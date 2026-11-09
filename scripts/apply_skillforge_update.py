#!/usr/bin/env python3
"""Apply a hash-guarded SkillForge change package; default is a read-only check.

Use the shared lock for cooperating writers. --apply makes backups, checks again
while holding that lock, and applies only listed paths. This is not a
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


class LockCleanupError(PatchError):
    def __init__(self, cleanup, primary=None):
        self.cleanup_error = str(cleanup)
        self.primary_error = None if primary is None else str(primary)
        super().__init__(("Primary failure: " + str(primary) + "; " if primary else "") +
                         "Lock cleanup failed: " + str(cleanup))


class PatchIncompleteError(PatchError):
    """已进入更新阶段；即使审计盘失败仍向调用者返回内存中的实际证据。"""
    def __init__(self, details):
        self.details = details
        super().__init__(f"Update {details['status']}; backup={details['backup']}; "
                         f"state={details['state_path']}; mutation_attempted={details['mutation_attempted']}; "
                         f"journal_persisted={details['journal_persisted']}; {details['error']}")


RETIRABLE = {f"skills/skillforge-orchestrator/{x}" for x in ("agents", "generated", "evals", "scripts", "tests")}
ALLOWED = {"skills", "development", "adapters", "docs", "evals", "scripts", "tests"}


def digest(data: bytes | None) -> str | None:
    return None if data is None else hashlib.sha256(data).hexdigest()


def is_link(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def safe(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative or "\0" in relative:
        raise PatchError("Invalid relative path")
    p = PurePosixPath(relative)
    if not p.parts or p.is_absolute() or ".." in p.parts or str(p) != relative:
        raise PatchError("Non-canonical or escaping path")
    if any(part.endswith((".", " ")) for part in p.parts):
        raise PatchError("Trailing dot/space components are not portable Windows paths")
    for part in p.parts:
        stem = part.split(".", 1)[0].upper()
        devices = {"CON", "PRN", "AUX", "NUL"} | {prefix + n for prefix in ("COM", "LPT") for n in "123456789¹²³"}
        if stem in devices or any(ord(c) < 32 or c in '<>"|?*' for c in part):
            raise PatchError("Reserved Windows device name or invalid portable path character")
    root = root.resolve(strict=True)
    result = root
    for part in p.parts:
        result = result / part
        if is_link(result):
            raise PatchError(f"Link/junction not supported: {relative}")
    if not result.resolve().is_relative_to(root):
        raise PatchError(f"Path escapes root: {relative}")
    return result


def read(path: Path) -> bytes | None:
    if not path.exists():
        return None
    if not path.is_file() or is_link(path):
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
        safe(package, name)  # Validate before indexing parts ('.' has no parts).
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
    for entry in manifest["entries"]:
        name = os.path.normcase(entry["path"])
        for directory in retired:
            prefix = os.path.normcase(directory)
            if entry["after"] is not None and (name == prefix or name.startswith(prefix + os.sep)):
                raise PatchError(f"Retired directory would retain an added/modified file: {entry['path']}")
    return manifest


def check(root: Path, package: Path, manifest: dict) -> list[dict]:
    changes = []
    targets = set()
    for entry in manifest["entries"]:
        key = os.path.normcase(str(safe(root, entry["path"]).resolve()))
        if key in targets:
            raise PatchError(f"Aliased manifest targets: {entry['path']}")
        targets.add(key)
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
            if item.is_dir():
                continue
            if not item.is_file():
                raise PatchError(f"Non-regular entry in retired directory: {relative}; preserve and reconcile first")
            if relative not in deletes:
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
        primary = sys.exc_info()[1]
        try:
            if path.is_file() and not is_link(path) and path.read_text(encoding="utf-8") == token:
                path.unlink()
        except (OSError, ValueError) as cleanup:
            raise LockCleanupError(cleanup, primary) from (primary or cleanup)



def inspect_pending_updates(root: Path) -> list[dict]:
    """只读列出未完成日志；不能根据目标已是新内容就当审计完成。"""
    store = safe(root, ".skillforge-backups")
    if not store.exists():
        return []
    pending = []
    for directory in sorted(store.iterdir()):
        relative = directory.relative_to(root).as_posix()
        safe(root, relative)
        if not directory.is_dir():
            raise PatchError(f"Unexpected backup entry; inspect manually: {directory}")
        state_path = safe(root, relative + "/state.json")
        try:
            data = read(state_path)
            record = json.loads(data.decode("utf-8")) if data is not None else None
            if not isinstance(record, dict):
                raise ValueError("missing or invalid state")
            if record.get("status") == "applied":
                continue
            if record.get("status") == "reconciled" and isinstance(record.get("resolution"), str) and record["resolution"].strip():
                continue
            item = {"backup":str(directory),"state_path":str(state_path),
                    "status":record.get("status","unknown"),"recorded_completed":record.get("completed",[]),
                    "actual_targets":[]}
            for entry in record.get("planned", []):
                if not isinstance(entry,dict) or not isinstance(entry.get("path"),str):
                    raise ValueError("invalid planned entry")
                actual = digest(read(safe(root,entry["path"])))
                classification = ("after" if actual == entry.get("after") else
                                  "before" if actual == entry.get("before") else "conflict")
                item["actual_targets"].append({"path":entry["path"],"sha256":actual,"matches":classification})
            pending.append(item)
        except (OSError, ValueError, TypeError, KeyError, PatchError) as exc:
            pending.append({"backup":str(directory),"state_path":str(state_path),
                            "status":"unreadable_or_missing","error":str(exc)})
    return pending


def require_reconciled(root: Path) -> None:
    pending = inspect_pending_updates(root)
    if pending:
        raise PatchError("RECOVERY_REQUIRED: unfinished update evidence at " +
                         ", ".join(item["state_path"] for item in pending) +
                         "; use --inspect-pending; no automatic replay or journal dismissal")



def apply_update(root: Path, package: Path, *, apply: bool = False) -> dict:
    root = Path(root).resolve(strict=True)
    package = Path(package).resolve(strict=True)
    if not root.is_dir() or not package.is_dir():
        raise PatchError("Root and package must be existing directories")
    require_reconciled(root)  # 必须早于already_current快捷返回。
    manifest = read_manifest(package)
    changes = check(root, package, manifest)
    retirement_needed = any(safe(root, p).exists() for p in manifest.get("retire_dirs", []))
    if not apply:
        return dict(status="checked", changes=len(changes), retire_dirs=manifest.get("retire_dirs", []))
    if not changes and not retirement_needed:
        return dict(status="already_current", changes=0)
    state, backup, state_path, attempted = None, None, None, []
    applied_persisted = False
    try:
        with writer_lock(root):
            require_reconciled(root)
            changes = check(root, package, manifest)
            backup = safe(root, ".skillforge-backups/" + uuid.uuid4().hex)
            backup.mkdir(parents=True, exist_ok=False)
            state = dict(status="prepared", manifest_sha256=digest(read(package / "manifest.json")),
                         completed=[], planned=changes, retire_dirs=manifest.get("retire_dirs",[]))
            state_path = backup / "state.json"
            def save():
                atomic_write(state_path, (json.dumps(state, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
            save()
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
                # 先保存内存中的尝试记录；异常不能被解读成没有发生修改。
                attempted.append(entry["path"])
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
                    attempted.append(name + "/")
                    for child in sorted(directory.rglob("*"), key=lambda p: len(p.parts), reverse=True):
                        if child.is_dir():
                            child.rmdir()
                    directory.rmdir()
            if check(root, package, manifest):
                raise PatchError("Final content verification did not converge")
            state["status"] = "applied"
            save()
            applied_persisted = True
        # 只有锁释放也完成才报告整体成功。
        return dict(status="applied", changes=len(changes), backup=str(backup))
    except (OSError, ValueError, PatchError) as exc:
        if state is None:
            raise
        if applied_persisted and isinstance(exc, LockCleanupError):
            # Durable applied evidence must not be rewritten as an interrupted mutation.
            lock_path = root / ".skillforge-memory/write.lock"
            try:
                lock_status = "present" if lock_path.lstat() else "unknown"
            except FileNotFoundError:
                lock_status = "absent"
            except OSError:
                lock_status = "unknown"
            details = {"status":"cleanup_required", "transaction_status":"applied",
                       "backup":str(backup), "state_path":str(state_path),
                       "mutation_attempted":bool(attempted), "attempted_paths":attempted,
                       "verified_paths":list(state["completed"]), "uncertain_paths":[],
                       "journal_persisted":True, "journal_error":None,
                       "lock_path":str(lock_path), "lock_status":lock_status,
                       "cleanup_error":exc.cleanup_error, "error":str(exc),
                       "automatic_retry_allowed":False,
                       "next_action":"Update committed. Inspect lock ownership and clean up explicitly; do not recover or replay the transaction."}
            raise PatchIncompleteError(details) from exc
        state["status"] = "partial"
        state["error"] = str(exc)
        journal_error = None
        try:
            save()
        except (OSError, ValueError, PatchError) as failed_save:
            journal_error = str(failed_save)
        details = {"status":"incomplete", "backup":str(backup), "state_path":str(state_path),
                   "mutation_attempted":bool(attempted), "attempted_paths":attempted,
                   "verified_paths":list(state["completed"]),
                   "uncertain_paths":[x for x in attempted if x not in state["completed"]],
                   "journal_persisted":journal_error is None, "journal_error":journal_error,
                   "error":str(exc), "automatic_retry_allowed":False}
        raise PatchIncompleteError(details) from exc


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--package", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--apply", action="store_true", help="Apply only after reviewing the read-only check; uses the shared writer lock")
    parser.add_argument("--inspect-pending", action="store_true", help="Read unfinished update journals and current hashes; never modify or recover automatically")
    args = parser.parse_args(argv)
    try:
        if args.inspect_pending:
            if args.apply:
                raise PatchError("--inspect-pending cannot be combined with --apply")
            output = {"status":"inspection_only", "pending":inspect_pending_updates(args.root.resolve(strict=True))}
        else:
            output = apply_update(args.root, args.package, apply=args.apply)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except PatchIncompleteError as exc:
        print(json.dumps(exc.details, ensure_ascii=False, indent=2))
        print(f"{exc.details['status'].upper()}: {exc}", file=sys.stderr)
        return 3
    except (OSError, ValueError, KeyError, TypeError, PatchError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
