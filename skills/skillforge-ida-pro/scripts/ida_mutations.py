"""Small, explicit IDB changes. Target IDA 9.x; dry-run by default.
No arbitrary Python, no patching original bytes, no implicit database save.
A backup and per-operation audit are required for commit; NOT atomic rollback.
"""
import json
import os
import re
from datetime import datetime, timezone
from ida_evidence import AnalysisError, context, ea, function_at, hex_ea, module, ready, require, sha256_file


def _identifier(name):
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", name):
        raise ValueError("Use a simple ASCII identifier in this conservative example")
    return name


def _prepare(op):
    kind = op.get("kind")
    if not str(module("ida_kernwin").get_kernel_version()).startswith("9."):
        raise AnalysisError("Mutation example targets IDA 9.x only; adapt against installed documentation")
    if kind == "rename":
        f, names = function_at(op["ea"]), module("ida_name")
        if f.start_ea != ea(op["ea"]):
            raise AnalysisError("Rename target must be the exact function start")
        old = names.get_name(f.start_ea)
        if old != op.get("expected_old"):
            raise AnalysisError("Name changed since review; regenerate plan")
        new = _identifier(op["new"])
        target = names.get_name_ea(module("ida_idaapi").BADADDR, new)
        if target not in (module("ida_idaapi").BADADDR, f.start_ea):
            raise AnalysisError("New name already belongs to another address")
        return {"kind": kind, "ea": hex_ea(f.start_ea), "old": old, "new": new}, None
    if kind == "function_type":
        f, ti, idc = function_at(op["ea"]), module("ida_typeinf"), module("idc")
        if f.start_ea != ea(op["ea"]):
            raise AnalysisError("Type target must be the exact function start")
        old = idc.get_type(f.start_ea)
        if old != op.get("expected_old"):
            raise AnalysisError("Function type changed since review")
        decl = op["declaration"]
        if not isinstance(decl, str) or len(decl) > 4096 or "#" in decl or "{" in decl:
            raise ValueError("Only one short function declaration; no directives or inline type bodies")
        tif = ti.tinfo_t()
        if ti.parse_decl(tif, None, decl, ti.PT_SIL) is None or not tif.is_func():
            raise AnalysisError("Not a valid function declaration in this target ABI")
        return {"kind": kind, "ea": hex_ea(f.start_ea), "old": old, "new": decl}, tif
    if kind == "structure":
        ti = module("ida_typeinf")
        name = _identifier(op["name"])
        existing = ti.tinfo_t()
        if existing.get_named_type(None, name):
            raise AnalysisError("Local type already exists; replacement is intentionally unsupported")
        # Build detached type from a bounded declaration. User-reviewed, no external includes.
        declaration = op["declaration"]
        if not isinstance(declaration, str) or len(declaration) > 4096 or "#" in declaration:
            raise ValueError("Short inline structure declaration only, no preprocessor")
        tif = ti.tinfo_t()
        parsed = ti.parse_decl(tif, None, declaration, ti.PT_SIL)
        if parsed is None or not tif.is_struct():
            raise AnalysisError("Declaration did not produce a structure")
        return {"kind": kind, "name": name, "old": None,
                "new": declaration, "parsed_size_bytes": tif.get_size()}, tif
    raise ValueError("Allowed changes: rename, function_type, structure")


def run_plan(plan, commit=False, audit_path=None, backup_path=None):
    """Review dry run before commit. Always run on IDA owner/main thread.
    plan = {expected_input_sha256: ..., reason: ..., operations: [...]}
    Mutation may trigger analysis; run ready() before a subsequent plan.
    """
    ready()
    evidence = context()
    expected = plan.get("expected_input_sha256")
    if not expected or expected != evidence.get("input_sha256"):
        raise AnalysisError("Original input hash unavailable or mismatched")
    if not plan.get("reason"):
        raise ValueError("A change reason is required")
    operations = plan.get("operations", [])
    if not 1 <= len(operations) <= 100:
        raise ValueError("Use 1..100 explicitly reviewed operations per plan")
    # Avoid duplicate target changes within a batch and name swapping.
    keys = [(op.get("kind"), op.get("name") if op.get("kind") == "structure" else ea(op["ea"])) for op in operations]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate operation targets")
    names = [op["new"] for op in operations if op.get("kind") == "rename"]
    if len(set(names)) != len(names):
        raise ValueError("Duplicate new function names")
    prepared = [_prepare(op) for op in operations]
    preview = {"context": evidence, "reason": plan["reason"], "dry_run": not commit,
               "changes": [row for row, _ in prepared],
               "warning": "Independent operations, not a transaction; rollback requires verified working IDB backup."}
    if not commit:
        return preview
    if not evidence.get("idb_input_sha256") or evidence["idb_input_sha256"] != expected:
        raise AnalysisError("IDB stored input SHA-256 missing or different from disk input")
    if not plan.get("expected_idb_path") or not evidence.get("idb_path") or os.path.realpath(plan["expected_idb_path"]) != os.path.realpath(evidence["idb_path"]):
        raise AnalysisError("Current IDB path differs from reviewed plan")
    if plan.get("expected_image_base") != evidence.get("image_base") or not plan.get("expected_image_base"):
        raise AnalysisError("Current IDB image base differs from reviewed plan")
    if not audit_path or not backup_path:
        raise AnalysisError("Commit requires audit_path and an operator-verified IDB backup_path")
    loader = module("ida_loader")
    require(loader, "get_path", "PATH_TYPE_IDB")
    current = loader.get_path(loader.PATH_TYPE_IDB)
    backup_path = os.path.abspath(backup_path)
    if not current or os.path.realpath(current) == os.path.realpath(backup_path):
        raise AnalysisError("Backup must be a distinct file from the open IDB")
    try:
        same = os.path.samefile(current, backup_path)
    except OSError as exc:
        raise AnalysisError("Cannot establish independent backup identity") from exc
    if same:
        raise AnalysisError("Backup aliases the open IDB (same file/inode)")
    if not os.path.isfile(backup_path) or os.path.getsize(backup_path) == 0:
        raise AnalysisError("Backup is missing or empty")
    preview["operator_supplied_backup"] = {"path": backup_path, "sha256": sha256_file(backup_path),
        "limitation": "Existence/hash checked; recoverability and currency must be verified by operator before commit"}

    outcomes, attempted, uncertain, audit_errors = [], [], [], []
    def result(ok, failure=None):
        return {"ok": ok, "partial": bool(attempted) and len(outcomes) < len(operations),
                "mutation_attempted": bool(attempted), "attempted_operation_indices": attempted,
                "applied": outcomes, "verified_results": outcomes,
                "uncertain_operation_indices": uncertain,
                "all_mutations_verified": len(outcomes) == len(operations),
                "audit_complete": not audit_errors, "audit_errors": audit_errors,
                "failure": failure, "saved_to_disk": False, "automatic_retry_allowed": False,
                "next_step": "Inspect returned evidence and actual IDB; audit persistence can be incomplete. Never automatically replay."}
    try:
        with open(audit_path, "x", encoding="utf-8") as log:
            def record(value):
                try:
                    log.write(json.dumps(value, ensure_ascii=False) + "\n")
                    log.flush()
                    os.fsync(log.fileno())
                    return True
                except Exception as exc:
                    audit_errors.append({"event": value.get("event"), "error": str(exc)})
                    return False
            if not record({"event": "plan", "utc": datetime.now(timezone.utc).isoformat(), "plan": preview}):
                return result(False, {"stage": "audit_plan"})
            for index, operation in enumerate(operations):
                row, stage = None, "revalidate"
                try:
                    row, tif = _prepare(operation)
                    if not record({"event":"attempt","operation_index":index,"change":row}):
                        return result(False, {"stage":"audit_attempt","operation_index":index})
                    stage = "apply"
                    attempted.append(index)
                    if row["kind"] == "rename":
                        names = module("ida_name")
                        ok = bool(names.set_name(ea(row["ea"]), row["new"], names.SN_CHECK))
                    elif row["kind"] == "function_type":
                        ti = module("ida_typeinf")
                        ok = bool(ti.apply_tinfo(ea(row["ea"]), tif, ti.TINFO_DEFINITE))
                    else:
                        ti = module("ida_typeinf")
                        ok = tif.set_named_type(None, row["name"], 0) == ti.TERR_OK
                    if not ok:
                        raise AnalysisError("IDA rejected change; inspect actual state")
                    stage = "readback"
                    outcome = {"event":"applied","operation_index":index,"change":row}
                    if row["kind"] == "rename":
                        outcome["readback"] = module("ida_name").get_name(ea(row["ea"]))
                        if outcome["readback"] != row["new"]:
                            raise AnalysisError("Rename readback did not match")
                    else:
                        ti = module("ida_typeinf")
                        readback = ti.tinfo_t()
                        found = (module("ida_nalt").get_tinfo(readback, ea(row["ea"]))
                                 if row["kind"] == "function_type"
                                 else readback.get_named_type(None, row["name"]))
                        if not found or not readback.equals_to(tif):
                            raise AnalysisError("Type readback differs from requested type")
                        outcome["readback"] = str(readback)
                    # 内存中的已验证结果必须先保留，日志失败不能抹掉已发生的修改。
                    outcomes.append(outcome)
                    if not record(outcome):
                        return result(False, {"stage":"audit_applied","operation_index":index})
                except Exception as exc:
                    if index in attempted and not any(x["operation_index"] == index for x in outcomes):
                        uncertain.append(index)
                    failure = {"event":"failed_or_uncertain","operation_index":index,
                               "stage":stage,"operation":operation,"change":row,"error":str(exc)}
                    record(failure)
                    record({"event":"terminated","ok":False,"applied_count":len(outcomes),
                            "operation_index":index,"stage":stage,"automatic_retry_allowed":False})
                    return result(False, failure)
            if not record({"event":"completed","ok":True,"applied_count":len(outcomes),"saved_to_disk":False}):
                return result(False, {"stage":"audit_completed"})
    except Exception as exc:
        # 包括打开/关闭日志失败；保留此前已尝试和已读回的真实状态。
        audit_errors.append({"event":"open_or_close","error":str(exc)})
        return result(False, {"stage":"audit_open_or_close","error":str(exc)})
    return result(True)
