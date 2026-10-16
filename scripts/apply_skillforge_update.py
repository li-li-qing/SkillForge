#!/usr/bin/env python3
"""Apply a hash-guarded SkillForge change package; default is a read-only check.

Pause all other writers first. --apply makes backups, checks again while holding
our shared cooperative rule lock, and applies only listed paths. This is not a
security sandbox or an all-files atomic transaction. A conflict never authorizes
force-overwriting local changes. Interrupted work leaves backups and state.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile
import uuid


class PatchError(RuntimeError):
    pass


RETIRABLE = {f"skills/skillforge-orchestrator/{x}" for x in ("agents", "generated", "evals", "scripts", "tests")}
ALLOWED = {"skills", "development", "adapters", "docs", "evals", "scripts", "tests"}


def digest(data: bytes | None) -> str | None:
    return None if data is None else hashlib.sha256(data).hexdigest()


def safe(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise PatchError("Invalid relative path")
    p = PurePosixPath(relative)
    if p.is_absolute() or ".." in p.parts or str(p) != relative:
        raise PatchError("Non-canonical or escaping path")
    result = root
    for part in p.parts:
        result = result / part
        if result.is_symlink() or (hasattr(result, "is_junction") and result.is_junction()):
            raise PatchError(f"Link/junction not supported: {relative}")
    return result


def read(path: Path) -> bytes | None:
    if not path.exists():
        return None
    if not path.is_file() or path.is_symlink():
        raise PatchError(f"Not a regular file: {path}")
    return path.read_bytes()


def atomic_write(path: Path, data: bytes, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".sf-update-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if mode is not None:
            os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def read_manifest(package: Path) -> dict:
    path = safe(package, "manifest.json")
    contents = read(path)
    if contents is None:
        raise PatchError("manifest.json not found next to the package payload")
    manifest = json.loads(contents.decode("utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1 or not isinstance(manifest.get("entries"), list):
        raise PatchError("Unsupported manifest")
    seen = set()
    for entry in manifest["entries"]:
        if not isinstance(entry, dict):
            raise PatchError("Invalid manifest entry")
        name = entry.get("path")
        if not isinstance(name, str) or not name:
            raise PatchError("Entry has no path")
        path = PurePosixPath(name)
        if name in seen or (name not in {"README.md", ".gitignore"} and path.parts[0] not in ALLOWED):
            raise PatchError(f"Duplicate or forbidden manifest path: {name}")
        safe(package, name)  # Validate path spelling and reject traversal.
        seen.add(name)
        before, after, action = entry.get("before"), entry.get("after"), entry.get("operation")
        for value in (before, after):
            if value is not None and (not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)):
                raise PatchError("Invalid content hash")
        valid = ((action == "add" and before is None and after is not None) or
                 (action == "modify" and before is not None and after is not None) or
                 (action == "delete" and before is not None and after is None))
        if not valid:
            raise PatchError("Inconsistent action and hashes")
    retired = manifest.get("retire_dirs", [])
    if not isinstance(retired, list) or any(x not in RETIRABLE for x in retired) or len(retired) != len(set(retired)):
        raise PatchError("Unsupported retired directory")
    return manifest


def check(root: Path, package: Path, manifest: dict) -> list[dict]:
    changes = []
    deletes = {e["path"] for e in manifest["entries"] if e["operation"] == "delete"}
    for entry in manifest["entries"]:
        name = entry["path"]
        target = safe(root, name)
        if entry["after"] is not None:
            payload = read(safe(package, "payload/" + name))
            if digest(payload) != entry["after"]:
                raise PatchError(f"Missing/corrupt payload: {name}")
        actual = digest(read(target))
        if actual == entry["after"]:
            continue  # Already installed, or a deleted file is already absent.
        if actual != entry["before"]:
            raise PatchError(f"CONFLICT: {name}; current content differs from both base and update; nothing forced")
        changes.append(entry)
    for name in manifest.get("retire_dirs", []):
        directory = safe(root, name)
        if not directory.exists():
            continue
        if not directory.is_dir():
            raise PatchError(f"Retired path is not a directory: {name}")
        for item in directory.rglob("*"):
            relative = item.relative_to(root).as_posix()
            safe(root, relative)
            if item.is_file() and relative not in deletes:
                raise PatchError(f"Unlisted local file in retired directory: {relative}; preserve and reconcile first")
    return changes


@contextmanager
def writer_lock(root: Path):
    store = safe(root, ".skillforge-memory")
    store.mkdir(exist_ok=True)
    path = safe(root, ".skillforge-memory/write.lock")
    token = uuid.uuid4().hex
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise PatchError("Shared rule writer lock exists; do not steal it") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(token)
            stream.flush()
            os.fsync(stream.fileno())
        transactions = safe(root, ".skillforge-memory/transactions")
        if transactions.exists():
            for item in transactions.glob("*.json"):
                safe(root, item.relative_to(root).as_posix())
                record = json.loads(read(item).decode("utf-8"))
                if record.get("status") in {"prepared", "rollback_prepared"}:
                    raise PatchError("Interrupted experience transaction exists; recover it first")
        yield
    finally:
        if path.is_file() and not path.is_symlink() and path.read_text(encoding="utf-8") == token:
            path.unlink()


def apply_update(root: Path, package: Path, *, apply: bool = False) -> dict:
    root = Path(root).resolve(strict=True)
    package = Path(package).resolve(strict=True)
    if not root.is_dir() or not package.is_dir():
        raise PatchError("Root and package must be existing directories")
    manifest = read_manifest(package)
    changes = check(root, package, manifest)
    retirement_needed = any(safe(root, p).exists() for p in manifest.get("retire_dirs", []))
    if not apply:
        return dict(status="checked", changes=len(changes), retire_dirs=manifest.get("retire_dirs", []))
    if not changes and not retirement_needed:
        return dict(status="already_current", changes=0)
    with writer_lock(root):
        changes = check(root, package, manifest)  # Another cooperative writer may have completed since the initial check.
        backup = safe(root, ".skillforge-backups/" + uuid.uuid4().hex)
        backup.mkdir(parents=True, exist_ok=False)
        state = dict(status="prepared", manifest_sha256=digest(read(package / "manifest.json")), completed=[], planned=changes)
        state_path = backup / "state.json"
        def save():
            atomic_write(state_path, (json.dumps(state, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        save()
        try:
            for entry in changes:
                current = read(safe(root, entry["path"]))
                if digest(current) != entry["before"]:
                    raise PatchError(f"Concurrent change before backup: {entry['path']}")
                if current is not None:
                    atomic_write(backup / "files" / entry["path"], current)
            for entry in changes:
                target = safe(root, entry["path"])
                if digest(read(target)) != entry["before"]:
                    raise PatchError(f"Concurrent change before write: {entry['path']}")
                if entry["after"] is None:
                    target.unlink()
                else:
                    contents = read(safe(package, "payload/" + entry["path"]))
                    if digest(contents) != entry["after"]:
                        raise PatchError(f"Payload changed during update: {entry['path']}")
                    mode = stat.S_IMODE(target.stat().st_mode) if target.exists() else 0o644
                    atomic_write(target, contents, mode)
                if digest(read(target)) != entry["after"]:
                    raise PatchError(f"Post-write mismatch: {entry['path']}")
                state["completed"].append(entry["path"])
                save()
            for name in manifest.get("retire_dirs", []):
                directory = safe(root, name)
                if directory.exists():
                    for child in sorted(directory.rglob("*"), key=lambda p: len(p.parts), reverse=True):
                        if child.is_dir():
                            child.rmdir()  # Nonempty or newly added content causes a refusal, never recursive deletion.
                    directory.rmdir()
            if check(root, package, manifest):
                raise PatchError("Final content verification did not converge")
            state["status"] = "applied"
            save()
            return dict(status="applied", changes=len(changes), backup=str(backup))
        except (OSError, ValueError, PatchError) as exc:
            state["status"] = "partial"
            state["error"] = str(exc)
            save()
            raise PatchError(f"Update incomplete; no automatic rollback over others' edits. Review {state_path}: {exc}") from exc


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--package", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--apply", action="store_true", help="Apply only after reviewing the read-only check; pause other writers")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(apply_update(args.root, args.package, apply=args.apply), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, PatchError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
