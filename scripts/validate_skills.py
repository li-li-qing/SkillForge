#!/usr/bin/env python3
"""Validate portable SkillForge v1 packages using Python 3.10+ standard library.

This intentionally validates a small YAML profile, not arbitrary YAML: exactly
two single-line fields between `---` delimiters, a `name` and a JSON-quoted
`description`. Names may be JSON-quoted or use a conservative plain subset:
plain names must begin with a letter and cannot be null, true, false, yes, no,
on, off, y, or n (including YAML 1.1 boolean spellings). Quote those names and
all digit-leading names, even ordinary strings such as 123-foo, to avoid YAML
scalar type ambiguity. Decoded names still obey the normal skill-name rules.
Optional metadata, comments, block scalars, aliases, and other YAML features
are unsupported in v1.

Markdown checks cover ordinary inline links and reference-link definitions,
not HTML or a complete CommonMark grammar. Relative links and recognizable
script paths resolve from the containing Markdown file. HTTPS links are not
fetched and fragment identifiers are not checked. Prose portability checks
recognize absolute filesystem paths and explicit host API syntax; they cannot
prove that all natural-language instructions are host-independent. Unreal
virtual object paths /Game/, /Engine/, and /Script/ are allowed in prose.

Eval files are structural test specifications; this tool does not execute an
agent or claim that a skill passes the behaviors those specifications describe.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
from pathlib import Path, PureWindowsPath
import re
import shutil
import tempfile
from urllib.parse import unquote, urlsplit


NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z", re.ASCII)
YAML_RESERVED_NAMES = {"null", "true", "false", "yes", "no", "on", "off", "y", "n"}
INLINE_LINK = re.compile(r"!?\[[^\]\n]*\]\(\s*(<[^>\n]*>|[^\s)]+)")
REFERENCE_LINK = re.compile(r"^ {0,3}\[[^\]\n]+\]:\s*(<[^>\n]*>|\S+)", re.MULTILINE)
WINDOWS_PATH = re.compile(r"(?<![\w])[A-Za-z]:[\\/]|\\\\[^\s\\]+\\[^\s\\]+")
UNIX_PATH = re.compile(r"(?<![\w:/.~-])/(?!/)[A-Za-z0-9_.~-]+(?:/[^\s`<>\"'()\[\]{},;]+)*/?")
HOST_API = re.compile(
    r"\b(?:functions\.[A-Za-z_]\w*|tools\.[A-Za-z_]\w*|mcp__[A-Za-z0-9_]+|"
    r"cua\.[A-Za-z_]\w*|nodeRepl\.[A-Za-z_]\w*)\b|codex://|\$(?:CODEX_HOME|CLAUDE_PROJECT_DIR)\b"
)
SCRIPT_PATH = re.compile(
    r"(?<![\w/\\])(?:\.{1,2}/)*scripts/[A-Za-z0-9_./-]+\.(?:py|sh|ps1|js|mjs|ts|bat|cmd)\b"
)
SCRIPT_COMMAND = re.compile(
    r"\b(?:python(?:3(?:\.\d+)?)?|node|bash|sh|pwsh|powershell)(?:\s+-File)?\s+"
    r"[\"']?((?:\.{1,2}/)*[A-Za-z0-9_./-]+\.(?:py|sh|ps1|js|mjs|ts|bat|cmd))\b"
)
TRIGGER_CATEGORIES = {"trigger", "no_trigger", "conditional"}


@dataclass
class Report:
    skills: int = 0
    standalone: int = 0
    errors: list[str] = field(default_factory=list)

    def error(self, source: Path, message: str) -> None:
        self.errors.append(f"{source}: {message}")


def read_text(path: Path, report: Report) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        report.error(path, f"cannot read UTF-8 file: {error}")
        return None


def validate_header(path: Path, text: str, report: Report) -> str | None:
    lines = text.splitlines()
    if len(lines) < 4 or lines[0] != "---" or lines[3] != "---":
        report.error(path, "v1 header must have exactly name and description on two single lines between --- delimiters")
        return None
    fields = {}
    for line in lines[1:3]:
        match = re.fullmatch(r"(name|description): (.*)", line)
        if not match or match[1] in fields:
            report.error(path, "v1 header requires one name and one JSON-quoted description; other YAML is unsupported")
            return None
        fields[match[1]] = match[2]
    if set(fields) != {"name", "description"}:
        report.error(path, "v1 header requires name and description")
        return None
    name = fields["name"]
    if name.startswith('"'):
        try:
            name = json.loads(name)
        except ValueError:
            report.error(path, "quoted name must be a valid JSON string")
            name = None
    elif name in YAML_RESERVED_NAMES or (name and name[0] in "0123456789"):
        report.error(path, "plain name may have a non-string YAML type; quote this name as a JSON string")
    if not isinstance(name, str) or not 1 <= len(name) <= 64 or not NAME.fullmatch(name):
        report.error(path, "name must be 1-64 lowercase ASCII letters/digits with single internal hyphens")
    if name != path.parent.name:
        report.error(path, "name must match the package directory name")
    try:
        description = json.loads(fields["description"])
    except (ValueError, TypeError):
        description = None
    if not isinstance(description, str) or not description.strip() or len(description) > 1024:
        report.error(path, "description must be a nonempty JSON-quoted string of at most 1024 characters")
    return name


def resolve_local(
    package: Path, source: Path, target: str, report: Report, *, file_only: bool = False,
) -> Path | None:
    """Resolve an explicitly local resource and enforce the package boundary."""
    target = unquote(target)
    windows = PureWindowsPath(target)
    if not target or windows.drive or target.startswith(("/", "\\")):
        report.error(source, f"resource must be a relative package path: {target!r}")
        return None
    try:
        destination = (source.parent / target.replace("\\", "/")).resolve()
        if not destination.is_relative_to(package):
            report.error(source, f"resource escapes package: {target!r}")
            return None
        if not destination.exists() or (file_only and not destination.is_file()):
            report.error(source, f"resource does not exist as {'a file' if file_only else 'a path'}: {target!r}")
            return None
        return destination
    except (OSError, ValueError, RuntimeError) as error:
        report.error(source, f"invalid resource {target!r}: {error}")
        return None


def validate_markdown(package: Path, path: Path, text: str, report: Report) -> None:
    for number, line in enumerate(text.splitlines(), 1):
        unix_paths = (match[0] for match in UNIX_PATH.finditer(line))
        if WINDOWS_PATH.search(line) or any(
            value.rstrip("/") not in {"/Game", "/Engine", "/Script"}
            and not value.startswith(("/Game/", "/Engine/", "/Script/"))
            for value in unix_paths
        ):
            report.error(path, f"line {number}: absolute local filesystem path is not portable")
        if HOST_API.search(line):
            report.error(path, f"line {number}: host-specific tool or environment syntax is not portable")

    targets = [match[1].strip("<>") for pattern in (INLINE_LINK, REFERENCE_LINK)
               for match in pattern.finditer(text)]
    for target in targets:
        if target.startswith("#"):
            continue
        try:
            url = urlsplit(target)
        except ValueError as error:
            report.error(path, f"invalid link {target!r}: {error}")
            continue
        if url.scheme == "https" and url.netloc:
            continue
        if url.scheme or url.netloc:
            report.error(path, f"link must be relative or HTTPS: {target!r}")
            continue
        resolve_local(package, path, url.path, report)

    scripts = {match[0] for match in SCRIPT_PATH.finditer(text)}
    scripts.update(match[1] for match in SCRIPT_COMMAND.finditer(text))
    for target in sorted(scripts):
        resolve_local(package, path, target, report, file_only=True)


def nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_evals(package: Path, kind: str, report: Report) -> None:
    path = package / "evals" / f"{kind}-cases.json"
    text = read_text(path, report)
    if text is None:
        return
    try:
        cases = json.loads(text)
    except ValueError as error:
        report.error(path, f"invalid JSON: {error}")
        return
    if not isinstance(cases, list) or not cases:
        report.error(path, "evals must be a nonempty array of case objects")
        return
    identifiers = set()
    categories = set()
    for number, case in enumerate(cases, 1):
        label = f"case {number}"
        if not isinstance(case, dict):
            report.error(path, f"{label}: must be an object")
            continue
        for key in ("id", "prompt") + (("reason",) if kind == "trigger" else ()):
            if not nonempty_string(case.get(key)):
                report.error(path, f"{label}: {key} must be a nonempty string")
        identifier = case.get("id")
        if isinstance(identifier, str):
            if identifier in identifiers:
                report.error(path, f"{label}: duplicate id {identifier!r}")
            identifiers.add(identifier)
        if kind == "trigger":
            context = case.get("context")
            if not (nonempty_string(context) or isinstance(context, dict)):
                report.error(path, f"{label}: context must be a nonempty string or an object")
            expected = case.get("expected")
            if not isinstance(expected, str) or expected not in TRIGGER_CATEGORIES:
                report.error(path, f"{label}: expected must be trigger, no_trigger, or conditional")
            else:
                categories.add(expected)
        else:
            expectations = case.get("expectations")
            if not isinstance(expectations, list) or not expectations or not all(
                nonempty_string(item) for item in expectations
            ):
                report.error(path, f"{label}: expectations must be a nonempty list of nonempty strings")
            fixtures = case.get("fixtures", [])
            if not isinstance(fixtures, list) or not all(nonempty_string(item) for item in fixtures):
                report.error(path, f"{label}: fixtures must be a list of relative file paths")
            else:
                for target in fixtures:
                    # Fixture paths are defined relative to the package, unlike Markdown links.
                    resolve_local(package, package / "SKILL.md", target, report, file_only=True)
    if kind == "trigger" and categories != TRIGGER_CATEGORIES:
        report.error(path, "trigger evals must cover all categories: trigger, no_trigger, conditional")


def validate_package(package: Path, report: Report) -> str | None:
    if not package.is_dir():
        report.error(package, "skill package directory does not exist")
        return None
    # Check real targets before reading or copying: a symlink/junction must not
    # silently borrow content from the repository or a host-specific location.
    boundary_errors = len(report.errors)
    try:
        for resource in package.rglob("*"):
            if not resource.resolve().is_relative_to(package):
                report.error(resource, "resource target escapes package")
    except (OSError, RuntimeError) as error:
        report.error(package, f"cannot inspect package resources: {error}")
    if len(report.errors) != boundary_errors:
        return None
    main = package / "SKILL.md"
    text = read_text(main, report)
    name = None
    if text is not None:
        name = validate_header(main, text, report)
        if len(text.splitlines()) > 500:
            report.error(main, "SKILL.md exceeds the 500-line limit")
        validate_markdown(package, main, text, report)
    for path in sorted((package / "references").rglob("*.md")):
        text = read_text(path, report)
        if text is not None:
            validate_markdown(package, path, text, report)
    for kind in ("trigger", "behavior"):
        validate_evals(package, kind, report)
    return name


def validate_packages(packages: list[Path], *, self_contained: bool = False) -> Report:
    report = Report(skills=len(packages))
    if not packages:
        report.errors.append("No skill packages found; supply directories or create packages under skills/.")
        return report
    names = {}
    for candidate in packages:
        package = candidate.resolve()
        before = len(report.errors)
        name = validate_package(package, report)
        if name is not None:
            if name in names:
                report.error(package, f"duplicate skill name {name!r}; also found in {names[name]}")
            names[name] = package
        if self_contained and len(report.errors) == before:
            try:
                with tempfile.TemporaryDirectory(prefix="skillforge-standalone-") as temporary:
                    copied = Path(temporary) / package.name
                    shutil.copytree(package, copied, symlinks=True)
                    validate_package(copied, report)
                    if len(report.errors) == before:
                        report.standalone += 1
            except (OSError, shutil.Error) as error:
                report.error(package, f"standalone copy failed: {error}")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("skill_dirs", nargs="*", type=Path, help="package directories; defaults to this repository's skills/*")
    parser.add_argument("--self-contained", action="store_true", help="copy each valid package to a temporary directory and revalidate")
    arguments = parser.parse_args(argv)
    packages = arguments.skill_dirs
    if not packages:
        root = Path(__file__).resolve().parents[1] / "skills"
        packages = sorted(path for path in root.iterdir() if path.is_dir()) if root.is_dir() else []
    report = validate_packages(packages, self_contained=arguments.self_contained)
    for error in report.errors:
        print(f"ERROR: {error}")
    suffix = f"; {report.standalone} standalone copies validated" if arguments.self_contained else ""
    print(f"Validated {report.skills} skill(s): {len(report.errors)} error(s){suffix}.")
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
