#!/usr/bin/env python3
"""Build a portable metadata-only index (Python 3.10+, standard library).

This is NOT a router, permission system, installer, or full YAML parser.
Only the SkillForge single-line frontmatter profile is accepted. Nothing in
SKILL.md is executed. Default: stdout only. --check is read-only. --output is
an explicit write and must not be used before the workflow permits writes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any

SELF = "skillforge-orchestrator"
VERSION = "0.1.0"
MAX_BYTES = 1024 * 1024
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z", re.ASCII)
LABEL = re.compile(r"[a-z][a-z0-9-]*\Z", re.ASCII)
RESERVED = {"null", "true", "false", "yes", "no", "on", "off", "y", "n"}


class IndexErrorDetail(ValueError):
    """An actionable validation failure; the caller leaves old output intact."""


def is_link(path: Path) -> bool:
    """Reject symlinks and Windows reparse points without following them.

    Ownership boundary: the indexer reads only the caller's chosen roots.
    Junctions can escape that boundary just as POSIX symlinks can. This check
    is conservative; native host discovery remains available for symlinked
    installations. It is not an OS sandbox against concurrent adversaries.
    """
    try:
        st = path.lstat()
    except FileNotFoundError:
        return False
    return path.is_symlink() or bool(getattr(st, "st_file_attributes", 0) & 0x400)


def read_limited(path: Path) -> bytes:
    if is_link(path) or not path.is_file():
        raise IndexErrorDetail(f"not a regular, non-linked file: {path}")
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise IndexErrorDetail(f"file exceeds {MAX_BYTES} bytes: {path}")
    return data


def quoted(value: str, where: str) -> str:
    try:
        result = json.loads(value)
    except (ValueError, TypeError) as exc:
        raise IndexErrorDetail(f"unsupported frontmatter at {where}; expected a JSON-quoted string") from exc
    if not isinstance(result, str):
        raise IndexErrorDetail(f"frontmatter at {where} must be a string")
    return result


def parse_frontmatter(data: bytes, path: Path) -> dict[str, Any]:
    """Parse the same restricted scalar shape used by the existing collection.

    Do not silently reinterpret arbitrary YAML, block scalars, tags, aliases,
    or duplicate fields. Failing the whole build prevents a partial catalogue
    from looking complete. Future YAML support needs tests and explicit scope.
    """
    lines = data.decode("utf-8-sig").splitlines()
    if len(lines) < 4 or lines[0] != "---" or "---" not in lines[1:]:
        raise IndexErrorDetail(f"missing frontmatter: {path}")
    fields: dict[str, Any] = {}
    metadata: dict[str, str] | None = None
    for line in lines[1:lines.index("---", 1)]:
        if line == "metadata:":
            if "metadata" in fields:
                raise IndexErrorDetail(f"duplicate frontmatter metadata: {path}")
            metadata = {}
            fields["metadata"] = metadata
            continue
        if line.startswith("  ") and metadata is not None:
            match = re.fullmatch(r"  ([a-z][a-z0-9_-]*): (.*)", line)
            if not match or match[1] in metadata:
                raise IndexErrorDetail(f"invalid/duplicate frontmatter metadata: {path}")
            metadata[match[1]] = quoted(match[2], str(path))
            continue
        metadata = None
        match = re.fullmatch(r"(name|description|compatibility|license|allowed-tools): (.*)", line)
        if not match or match[1] in fields:
            raise IndexErrorDetail(f"unsupported/duplicate frontmatter: {path}")
        key, raw = match.groups()
        if key == "name" and not raw.startswith('"'):
            if not raw or raw[0].isdigit() or raw in RESERVED:
                raise IndexErrorDetail(f"ambiguous frontmatter name must be quoted: {path}")
            fields[key] = raw
        else:
            fields[key] = quoted(raw, str(path))
    name = fields.get("name", "")
    description = fields.get("description", "")
    if not 1 <= len(name) <= 64 or not NAME.fullmatch(name) or name != path.parent.name:
        raise IndexErrorDetail(f"invalid name or name/folder mismatch: {path}")
    if not description.strip() or len(description) > 1024:
        raise IndexErrorDetail(f"description must contain 1-1024 characters: {path}")
    if "compatibility" in fields and not 1 <= len(fields["compatibility"]) <= 500:
        raise IndexErrorDetail(f"compatibility must contain 1-500 characters: {path}")
    return fields


def parse_roots(values: list[str]) -> list[tuple[str, Path]]:
    roots: list[tuple[str, Path]] = []
    labels: set[str] = set()
    seen: set[Path] = set()
    for value in values:
        label, separator, raw_path = value.partition("=")
        if not separator or not LABEL.fullmatch(label) or not raw_path:
            raise IndexErrorDetail("--root requires label=directory; labels use lowercase letters, digits and hyphens")
        path = Path(raw_path).expanduser()
        if is_link(path) or not path.is_dir():
            raise IndexErrorDetail(f"root must be an existing non-linked directory: {path}")
        path = path.resolve()
        if label in labels or path in seen:
            raise IndexErrorDetail(f"duplicate root label or physical directory: {label}")
        labels.add(label)
        seen.add(path)
        roots.append((label, path))
    return sorted(roots)


def build_index(roots: list[tuple[str, Path]]) -> dict[str, Any]:
    skills: list[dict[str, Any]] = []
    names: dict[str, str] = {}
    for label, root in roots:
        # No rglob, no home scan, no imports: only immediate skill directories.
        for folder in sorted(root.iterdir()):
            if folder.name.startswith("."):
                continue
            if is_link(folder):
                raise IndexErrorDetail(f"linked entry in skill root is not supported: {folder}")
            if not folder.is_dir():
                continue
            entry = folder / "SKILL.md"
            if is_link(entry):
                raise IndexErrorDetail(f"linked SKILL.md is not supported: {entry}")
            if not entry.exists():
                continue
            if not entry.resolve().is_relative_to(root):
                raise IndexErrorDetail(f"entry escapes root: {entry}")
            data = read_limited(entry)
            meta = parse_frontmatter(data, entry)
            name = meta["name"]
            if name == SELF:
                continue
            if name in names:
                raise IndexErrorDetail(f"duplicate skill {name!r}: {names[name]} and {entry}; resolve host scope explicitly")
            names[name] = str(entry)
            skills.append({
                "name": name,
                "description": meta["description"],
                "root": label,
                "path": entry.relative_to(root).as_posix(),
                "revision": meta.get("metadata", {}).get("revision"),
                # Hash describes this entry file, not every reference/dependency.
                "sha256": hashlib.sha256(data).hexdigest(),
            })
    skills.sort(key=lambda item: (item["name"], item["root"], item["path"]))
    return {
        "schema_version": 1,
        "generator": f"skillforge-orchestrator/{VERSION}",
        "scope": "metadata-snapshot-not-installation-or-permission-proof",
        "root_labels": [label for label, _ in roots],
        "skill_count": len(skills),
        "skills": skills,
    }


def write_atomic(path: Path, text: str) -> None:
    """Publish a fully validated index, never truncate the previous one first.

    The caller owns the explicit output path. No directory is created. An
    interrupted write may leave a temporary file only if the OS kills the
    process before cleanup; the old destination remains intact until replace.
    """
    path = path.absolute()
    if path.suffix.lower() != ".json" or not path.parent.is_dir():
        raise IndexErrorDetail("--output must be a .json file in an existing directory")
    if any(is_link(part) for part in (path, *path.parents)):
        raise IndexErrorDetail("--output and its ancestors must not be symlinks/reparse points")
    if path.exists() and not path.is_file():
        raise IndexErrorDetail("--output must be a regular file")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", prefix=".skill-index-", suffix=".tmp", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    # Chinese Windows paths must not turn a successful write into a reported
    # failure when output is redirected through a legacy codepage. Configure
    # both JSON and diagnostics BEFORE any mode writes; this owns only these
    # process streams, never the user's terminal or persistent environment.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", metavar="LABEL=DIRECTORY", help="repeat for multiple roots; defaults to sibling skills")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--output", type=Path, help="explicit atomic write (requires workflow authorization)")
    mode.add_argument("--check", type=Path, help="read-only comparison; 0=current, 1=stale, 2=invalid")
    args = parser.parse_args(argv)
    try:
        roots = parse_roots(args.root or [f"skills={Path(__file__).resolve().parents[2]}"])
        index = build_index(roots)
        text = json.dumps(index, ensure_ascii=False, indent=2) + "\n"
        if args.check is not None:
            old = json.loads(read_limited(args.check).decode("utf-8-sig"))
            if not isinstance(old, dict) or old.get("schema_version") != 1 or not isinstance(old.get("skills"), list):
                raise IndexErrorDetail("--check file is not a schema_version=1 skill index")
            if old != index:
                print("STALE: inventory or entry contents changed; no files written.", file=sys.stderr)
                return 1
            print("CURRENT: index matches selected roots; no files written.")
        elif args.output is not None:
            write_atomic(args.output, text)
            print(f"WROTE: {index['skill_count']} skill entries to {args.output}")
        else:
            # Only metadata enters stdout; entry body is never emitted.
            sys.stdout.write(text)
        return 0
    except (IndexErrorDetail, OSError, UnicodeError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
