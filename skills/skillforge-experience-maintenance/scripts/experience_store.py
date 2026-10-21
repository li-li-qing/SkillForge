#!/usr/bin/env python3
"""Local, cooperating-writer protection for reviewed SkillForge documentation.

Python 3.10+, standard library. No network, background work, automatic semantic
approval or stale-lock stealing. A root lock protects all cooperating writes;
non-cooperating writers and unverified network/sync filesystem semantics are
outside this contract. Proposals are independent records, not active rules.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile
import uuid


class StoreError(RuntimeError):
    """An operation was refused without overwriting a conflicting rule."""


MAX_CONTENT = 1024 * 1024
MAX_RECORD_BYTES = 4 * MAX_CONTENT
IDENTIFIER = re.compile(r"[0-9a-f]{32}\Z")


def _sha(data: bytes | None) -> str | None:
    return None if data is None else hashlib.sha256(data).hexdigest()


def _time() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _root(root: Path) -> Path:
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise StoreError("Shared root must be an existing directory")
    return root


def _is_link(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    # st_file_attributes works on supported Windows Python versions before 3.12.
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def _no_links(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative or "\0" in relative:
        raise StoreError("Invalid relative protected path")
    parsed = PurePosixPath(relative)
    if not parsed.parts or parsed.is_absolute() or ".." in parsed.parts or str(parsed) != relative:
        raise StoreError("Non-canonical or escaping protected path")
    if any(part.endswith((".", " ")) for part in parsed.parts):
        raise StoreError("Trailing dot/space components are not portable Windows paths")
    root = root.resolve(strict=True)
    p = root
    for component in parsed.parts:
        p = p / component
        if _is_link(p):
            raise StoreError("Links/reparse points are not supported in protected paths")
    if not p.resolve().is_relative_to(root):
        raise StoreError("Protected path escapes the shared root")
    return p


def _target(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise StoreError("Target must be a canonical relative POSIX path")
    p = PurePosixPath(relative)
    if p.is_absolute() or ".." in p.parts or str(p) != relative:
        raise StoreError("Non-canonical or escaping target")
    parts = p.parts
    if len(parts) < 3 or parts[0] != "skills" or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", parts[1]):
        raise StoreError("Target must belong to one named skill")
    direct = len(parts) == 3 and parts[2] in {"SKILL.md", "README.md", "VERSION"}
    resource = len(parts) >= 4 and parts[2] in {"references", "assets"} and p.suffix == ".md"
    if not (direct or resource):
        raise StoreError("Only skill documentation and VERSION are supported")
    target = _no_links(root, relative)
    if target.exists() and not target.is_file():
        raise StoreError("Target is not a regular file")
    return target


def _store(root: Path) -> Path:
    folder = _no_links(root, ".skillforge-memory")
    folder.mkdir(exist_ok=True)
    for sub in ("proposals", "transactions"):
        _no_links(root, f".skillforge-memory/{sub}").mkdir(exist_ok=True)
    return folder


def _read(path: Path) -> bytes | None:
    if not path.exists():
        return None
    if _is_link(path) or not path.is_file() or path.stat().st_size > MAX_RECORD_BYTES:
        raise StoreError("Unsafe or oversized input file")
    return path.read_bytes()


def _json_read(path: Path) -> dict:
    data = _read(path)
    if data is None:
        raise StoreError("Record not found")
    record = json.loads(data.decode("utf-8"))
    if not isinstance(record, dict):
        raise StoreError("Record must be an object")
    return record


def _atomic_write(path: Path, data: bytes, *, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".sf-", delete=False) as stream:
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


def _record_bytes(value: dict) -> bytes:
    data = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if len(data) > MAX_RECORD_BYTES:
        raise StoreError("Serialized record exceeds the 4 MiB read limit")
    return data


def _check_record_capacity(record: dict) -> None:
    # Include every timestamp/state field used by promote/rollback/recover so a
    # readable proposal cannot fail only after replacing the active document.
    _record_bytes(dict(record, status="rollback_prepared", reviewed=True,
        **{key: _time() for key in ("prepared_at", "completed_at", "rollback_started_at",
                                  "rollback_completed_at", "recovered_at")}))


def _json_write(path: Path, value: dict) -> None:
    _atomic_write(path, _record_bytes(value))


def _id(value: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise StoreError("Invalid record identifier")
    return value


@contextmanager
def _lock(root: Path):
    store = _store(root)
    lock = _no_links(root, ".skillforge-memory/write.lock")
    token = uuid.uuid4().hex
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise StoreError("Writer busy or recovery lock remains; candidate retained; do not steal the lock") from exc
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(token)
            stream.flush()
            os.fsync(stream.fileno())
        yield store
    finally:
        # Never unlink a lock replaced by an external actor.
        if lock.is_file() and not _is_link(lock) and lock.read_text(encoding="utf-8") == token:
            lock.unlink()


def _pending(store: Path, *, allowed: str | None = None) -> None:
    for path in (store / "transactions").glob("*.json"):
        transaction = _json_read(path)
        if transaction.get("status") in {"prepared", "rollback_prepared"} and path.stem != allowed:
            raise StoreError("An interrupted transaction needs explicit recovery before further rule writes")


def _validated(record: dict, identifier: str) -> dict:
    if record.get("schema_version") != 1 or record.get("id") != identifier:
        raise StoreError("Unsupported or mismatched record")
    after = record.get("after")
    before = record.get("before")
    if not isinstance(after, str) or (before is not None and not isinstance(before, str)):
        raise StoreError("Record content must be UTF-8 text")
    if len(after.encode("utf-8")) > MAX_CONTENT:
        raise StoreError("Record content is too large")
    if _sha(after.encode("utf-8")) != record.get("after_sha256"):
        raise StoreError("Candidate content hash mismatch")
    if _sha(None if before is None else before.encode("utf-8")) != record.get("before_sha256"):
        raise StoreError("Base content hash mismatch")
    return record


def propose(root: Path, target: str, content: str, *, actor: str, kind: str,
            evidence: list[str], conditions: str) -> str:
    """Store an independent candidate without changing any active rule."""
    root = _root(root)
    path = _target(root, target)
    if not isinstance(content, str) or len(content.encode("utf-8")) > MAX_CONTENT:
        raise StoreError("Content must be at most 1 MiB UTF-8 text")
    if kind not in {"preference", "technical"} or not actor.strip() or not conditions.strip():
        raise StoreError("Kind, actor and applicability conditions are required")
    if not evidence or not all(isinstance(x, str) and x.strip() for x in evidence):
        raise StoreError("At least one concrete evidence reference is required")
    before = _read(path)
    if before is not None and len(before) > MAX_CONTENT:
        raise StoreError("Base document exceeds 1 MiB; split the material before promotion")
    before_text = None if before is None else before.decode("utf-8")
    store = _store(root)
    identifier = uuid.uuid4().hex
    record = dict(schema_version=1, id=identifier, created_at=_time(), actor=actor,
                  kind=kind, conditions=conditions, evidence=evidence, target=target,
                  before=before_text, before_sha256=_sha(before), after=content,
                  after_sha256=_sha(content.encode("utf-8")), status="candidate")
    _check_record_capacity(record)
    data = _record_bytes(record)
    # O_EXCL ensures proposals cannot overwrite each other, even on an ID collision.
    with (store / "proposals" / f"{identifier}.json").open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return identifier


def promote(root: Path, identifier: str, *, reviewed: bool = False) -> dict:
    """Apply one semantically reviewed proposal if its exact base still matches."""
    if not reviewed:
        raise StoreError("Semantic review is required; the tool cannot provide it")
    root = _root(root)
    identifier = _id(identifier)
    with _lock(root) as store:
        _pending(store)
        journal = store / "transactions" / f"{identifier}.json"
        if journal.exists():
            existing = _validated(_json_read(journal), identifier)
            if existing.get("status") == "committed":
                # This reports the historical event, not that the rule remains current.
                target = _target(root, existing["target"])
                return dict(id=identifier, status="already_committed",
                            current_matches=_sha(_read(target)) == existing["after_sha256"])
            raise StoreError("Transaction already exists; inspect or recover it rather than replaying")
        record = _validated(_json_read(store / "proposals" / f"{identifier}.json"), identifier)
        _check_record_capacity(record)
        target = _target(root, record["target"])
        current = _read(target)
        if _sha(current) != record["before_sha256"]:
            raise StoreError("STALE: target changed; reread and semantically merge into a new candidate")
        mode = stat.S_IMODE(target.stat().st_mode) if target.exists() else 0o644
        transaction = dict(record, status="prepared", reviewed=True, prepared_at=_time())
        _json_write(journal, transaction)
        _atomic_write(target, record["after"].encode("utf-8"), mode=mode)
        if _sha(_read(target)) != record["after_sha256"]:
            raise StoreError("Post-write mismatch; preserve the prepared record for investigation")
        transaction.update(status="committed", completed_at=_time())
        _json_write(journal, transaction)
        return dict(id=identifier, status="committed", target=record["target"])


def rollback(root: Path, identifier: str, *, reviewed: bool = False) -> dict:
    """Undo only this version; refuse when a later writer changed the target."""
    if not reviewed:
        raise StoreError("Explicit reviewed rollback is required")
    root = _root(root)
    identifier = _id(identifier)
    with _lock(root) as store:
        _pending(store)
        journal = store / "transactions" / f"{identifier}.json"
        transaction = _validated(_json_read(journal), identifier)
        if transaction.get("status") != "committed":
            raise StoreError("Only a committed transaction can be rolled back")
        target = _target(root, transaction["target"])
        if _sha(_read(target)) != transaction["after_sha256"]:
            raise StoreError("STALE: a later revision exists; propose a reviewed inverse patch")
        _check_record_capacity(transaction)
        transaction.update(status="rollback_prepared", rollback_started_at=_time())
        _json_write(journal, transaction)
        if transaction["before"] is None:
            target.unlink()
        else:
            mode = stat.S_IMODE(target.stat().st_mode)
            _atomic_write(target, transaction["before"].encode("utf-8"), mode=mode)
        if _sha(_read(target)) != transaction["before_sha256"]:
            raise StoreError("Rollback post-write mismatch; investigation required")
        transaction.update(status="rolled_back", rollback_completed_at=_time())
        _json_write(journal, transaction)
        return dict(id=identifier, status="rolled_back")


def recover(root: Path, identifier: str) -> dict:
    """Reconcile journal state from hashes; never change the active rule."""
    root = _root(root)
    identifier = _id(identifier)
    with _lock(root) as store:
        _pending(store, allowed=identifier)
        journal = store / "transactions" / f"{identifier}.json"
        transaction = _validated(_json_read(journal), identifier)
        state = transaction.get("status")
        if state not in {"prepared", "rollback_prepared"}:
            raise StoreError("No interrupted transaction to recover")
        target = _target(root, transaction["target"])
        actual = _sha(_read(target))
        if state == "prepared":
            matches = [(transaction["after_sha256"], "committed"), (transaction["before_sha256"], "aborted")]
        else:
            matches = [(transaction["before_sha256"], "rolled_back"), (transaction["after_sha256"], "committed")]
        for expected, resolved in matches:
            if actual == expected:
                transaction.update(status=resolved, recovered_at=_time())
                _json_write(journal, transaction)
                return dict(id=identifier, status=resolved, rule_modified=False)
        raise StoreError("Neither recorded version matches; manual investigation required")


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="Explicit shared SkillForge root")
    sub = parser.add_subparsers(dest="action", required=True)
    proposal = sub.add_parser("propose")
    proposal.add_argument("--target", required=True)
    proposal.add_argument("--content", type=Path, required=True, help="UTF-8 candidate file")
    proposal.add_argument("--actor", required=True)
    proposal.add_argument("--kind", choices=["preference", "technical"], required=True)
    proposal.add_argument("--evidence", action="append", required=True)
    proposal.add_argument("--conditions", required=True)
    for action in ("promote", "rollback", "recover"):
        command = sub.add_parser(action)
        command.add_argument("id")
        if action != "recover":
            command.add_argument("--reviewed", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.action == "propose":
            content = _read(args.content)
            if content is None:
                raise StoreError("Candidate input file is missing")
            result = dict(status="candidate", id=propose(args.root, args.target, content.decode("utf-8"),
                          actor=args.actor, kind=args.kind, evidence=args.evidence, conditions=args.conditions))
        elif args.action == "promote":
            result = promote(args.root, args.id, reviewed=args.reviewed)
        elif args.action == "rollback":
            result = rollback(args.root, args.id, reviewed=args.reviewed)
        else:
            result = recover(args.root, args.id)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (StoreError, OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
