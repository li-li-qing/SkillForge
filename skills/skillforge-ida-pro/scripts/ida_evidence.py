"""SkillForge IDAPython evidence examples. Target: IDA 9.x, Python 3.
Run on the IDA main thread; no IDB save, network, debugger or process execution.
API references and validation limits: ../references/idapython-api.md.
"""
import csv
import hashlib
import importlib
import json
import os
import re
import stat
import time
from datetime import datetime, timezone


class AnalysisError(RuntimeError):
    pass


def module(name):
    try:
        return importlib.import_module(name)
    except ImportError as exc:
        raise AnalysisError("Required IDA module unavailable: " + name) from exc


def require(mod, *names):
    missing = [name for name in names if not hasattr(mod, name)]
    if missing:
        raise AnalysisError("Unsupported API capability: %s.%s" % (mod.__name__, ",".join(missing)))


def bounded(value, maximum=10000):
    value = ea(value)
    if not 1 <= value <= maximum:
        raise ValueError("limit must be 1..%d" % maximum)
    return value


def ea(value):
    if type(value) is int:
        result = value
    elif isinstance(value, str) and re.fullmatch(r"(?:[0-9]+|0[xX][0-9a-fA-F]+|0[bB][01]+|0[oO][0-7]+)", value):
        result = int(value, 10) if value.isdecimal() else int(value, 0)
    else:
        raise ValueError("address/count must be an integer or unsigned integer string; bool/float refused")
    if result < 0:
        raise ValueError("address must be nonnegative")
    return result


def hex_ea(value):
    return "0x%X" % int(value)


def sha256_file(path):
    """Hash a stable regular file (following file symlinks); lowercase hex.
    No arbitrary size cap. Initial-size budget is not an atomic snapshot.
    """
    if not stat.S_ISREG(os.stat(path).st_mode):
        raise OSError("Hash input must be a regular file")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise OSError("Opened hash input must be a regular file")
        stream = os.fdopen(descriptor, "rb")
        descriptor = None
        with stream:
            digest = hashlib.sha256()
            remaining = before.st_size
            while remaining:
                block = stream.read(min(1024 * 1024, remaining))
                if not block:
                    raise OSError("Hash input shrank; use a stable copy")
                digest.update(block)
                remaining -= len(block)
            if stream.read(1):
                raise OSError("Hash input grew; use a stable copy")
            after = os.fstat(stream.fileno())
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise OSError("Hash input changed; use a stable copy")
            return digest.hexdigest()
    finally:
        if descriptor is not None:
            os.close(descriptor)


def analysis_state():
    auto = module("ida_auto")
    require(auto, "auto_is_ok", "get_auto_state")
    return {"queues_empty": bool(auto.auto_is_ok()), "state": int(auto.get_auto_state()),
            "meaning": "Empty queues, not proof that all code/types were recovered."}


def wait_for_analysis():
    """Explicit opt-in: processes analysis queues and may modify the IDB."""
    auto = module("ida_auto")
    require(auto, "auto_wait")
    if not auto.auto_wait():
        raise AnalysisError("Automatic analysis cancelled or failed")
    return analysis_state()


def ready():
    if not analysis_state()["queues_empty"]:
        raise AnalysisError("Analysis is pending. Wait in IDA, or explicitly run wait_for_analysis on a working copy.")


def context():
    nalt, ida, kw = module("ida_nalt"), module("ida_ida"), module("ida_kernwin")
    require(ida, "inf_get_procname", "inf_is_64bit", "inf_is_32bit_exactly", "inf_is_be")
    path = nalt.get_input_file_path()
    result = {"target_file": path, "ida_version": kw.get_kernel_version(),
              "processor": ida.inf_get_procname(),
              "bitness": 64 if ida.inf_is_64bit() else 32 if ida.inf_is_32bit_exactly() else 16,
              "big_endian": bool(ida.inf_is_be()), "image_base": hex_ea(nalt.get_imagebase()),
              "analysis_utc": datetime.now(timezone.utc).isoformat(),
              "analysis_state": analysis_state(), "input_sha256": None,
              "hash_scope": "Original input file on disk, not patched IDB bytes"}
    try:
        result["input_sha256"] = sha256_file(path)
    except (OSError, TypeError) as exc:
        result["hash_error"] = str(exc)
    result["idb_input_sha256"] = None
    result["idb_path"] = None
    try:
        stored = nalt.retrieve_input_file_sha256()
        if stored and len(stored) == 32:
            result["idb_input_sha256"] = bytes(stored).hex()
        loader = module("ida_loader")
        result["idb_path"] = loader.get_path(loader.PATH_TYPE_IDB)
    except (AttributeError, AnalysisError, TypeError) as exc:
        result["idb_identity_error"] = str(exc)
    result["input_matches_idb"] = bool(result["input_sha256"] and result["input_sha256"] == result["idb_input_sha256"])
    return result


def function_at(address):
    funcs = module("ida_funcs")
    f = funcs.get_func(ea(address))
    if f is None:
        raise AnalysisError("No recognized function contains " + hex_ea(ea(address)))
    return f


def function_info(address):
    f, utils, funcs = function_at(address), module("idautils"), module("ida_funcs")
    return {"ea": hex_ea(f.start_ea), "end_ea": hex_ea(f.end_ea),
            "name": funcs.get_func_name(f.start_ea), "flags": int(f.flags),
            "chunks": [[hex_ea(a), hex_ea(b)] for a, b in utils.Chunks(f.start_ea)]}


def count_functions():
    ready()
    funcs = module("ida_funcs")
    return {"recognized_function_count": funcs.get_func_qty(),
            "scope": "IDA function table, not proof of every original source function"}


def functions_page(start=0, limit=100):
    ready()
    start, limit = ea(start), bounded(limit)
    utils, funcs = module("idautils"), module("ida_funcs")
    rows, next_ea = [], None
    for address in utils.Functions(start):
        # Functions() can repeat a function whose chunks span segments. Deduplicate.
        if rows and address <= int(rows[-1]["ea"], 16):
            continue
        if len(rows) == limit:
            next_ea = hex_ea(address)
            break
        f = funcs.get_func(address)
        rows.append({"ea": hex_ea(address), "name": funcs.get_func_name(address),
                     "end_ea": hex_ea(f.end_ea)})
    return {"rows": rows, "next_ea": next_ea, "complete": next_ea is None}



def _window(items, offset, limit):
    """按当前原生枚举顺序分页；不是数据库快照。深页会重放前缀。"""
    offset = ea(offset)
    if not 0 <= offset <= 100000:
        raise ValueError("offset must be 0..100000; use a persistent iterator for deeper exports")
    limit = bounded(limit)
    rows, visited, more = [], 0, False
    for index, item in enumerate(items):
        visited += 1
        if index < offset:
            continue
        if len(rows) == limit:
            more = True
            break
        rows.append(item)
    return rows, {"offset": offset, "scanned": len(rows),
        "iterator_items_visited": visited, "next_offset": offset + len(rows) if more else None,
        "truncated": more, "complete": not more,
        "order": "native iterator order of unchanged IDB; no sort or dedup",
        "consistency": "Not a snapshot. Freeze IDB and analysis; discard cursors after changes."}


def strings_page(start_index=0, limit=100, contains=None):
    ready()
    strings = module("idautils").Strings(False)
    items, meta = _window(iter(strings), start_index, limit)
    rows = []
    for index, item in enumerate(items, meta["offset"]):
        value = str(item)
        if contains is None or contains in value:
            rows.append({"index": index, "ea": hex_ea(item.ea), "length": int(item.length),
                         "string_type": int(item.strtype), "text": value})
    return dict(meta, rows=rows, next_index=meta["next_offset"],
                scope="Existing IDA string list only; prefix replay cost is iterator_items_visited")


def xrefs_to(address, limit=100, offset=0):
    ready()
    funcs, utils = module("ida_funcs"), module("idautils")
    items, meta = _window(utils.XrefsTo(ea(address), 0), offset, limit)
    rows = []
    for x in items:
        f = funcs.get_func(x.frm)
        rows.append({"from": hex_ea(x.frm), "to": hex_ea(x.to), "xref_type": int(x.type),
                     "type_name": utils.XrefTypeName(x.type), "is_code": bool(x.iscode),
                     "source_function": hex_ea(f.start_ea) if f else None})
    return dict(meta, rows=rows)


def string_xrefs(text, start_index=0, limit=100, xref_limit=100):
    result = strings_page(start_index, limit, contains=text)
    for row in result["rows"]:
        row["xrefs"] = xrefs_to(row["ea"], xref_limit)
    result["strings_complete"] = result["complete"]
    result["complete"] = result["strings_complete"] and all(row["xrefs"]["complete"] for row in result["rows"])
    return result


def assembly(address, limit=500, offset=0):
    ready()
    f, utils, lines = function_at(address), module("idautils"), module("ida_lines")
    items, meta = _window(utils.FuncItems(f.start_ea), offset, limit)
    rows = [{"ea": hex_ea(item), "assembly": lines.tag_remove(lines.generate_disasm_line(item, 0) or "")} for item in items]
    return dict(meta, function=function_info(f.start_ea), rows=rows)

def hexrays_status():
    try:
        hr = module("ida_hexrays")
        require(hr, "init_hexrays_plugin", "decompile")
        available = bool(hr.init_hexrays_plugin())
        return {"available": available,
                "meaning": "Plugin initialization only; target architecture/license and individual function may still fail."}
    except AnalysisError as exc:
        return {"available": False, "reason": str(exc)}


def pseudocode(address, max_lines=2000, offset=0):
    ready()
    max_lines = bounded(max_lines)
    f = function_at(address)
    if not hexrays_status()["available"]:
        raise AnalysisError("Hex-Rays unavailable for this session")
    hr, lines = module("ida_hexrays"), module("ida_lines")
    try:
        cf = hr.decompile(f.start_ea)
        if cf is None:
            raise AnalysisError("Decompiler returned no result")
        code = cf.get_pseudocode()
        selected, meta = _window((code[i] for i in range(len(code))), offset, max_lines)
        result = [lines.tag_remove(line.line) for line in selected]
        return {**meta, "function": function_info(f.start_ea), "pseudocode": result,
                "warning": "Reconstructed pseudocode, not recovered original C++ source"}
    except Exception as exc:
        raise AnalysisError("Decompilation failed at %s: %s" % (hex_ea(f.start_ea), exc)) from exc



def callers(address, limit=100, offset=0):
    """分页单位为原始XrefsTo条目，过滤后可能为空页；仍需沿游标继续。"""
    ready()
    f, xref, utils, funcs = function_at(address), module("ida_xref"), module("idautils"), module("ida_funcs")
    items, meta = _window(utils.XrefsTo(f.start_ea, 0), offset, limit)
    rows = []
    for x in items:
        if x.type not in (xref.fl_CN, xref.fl_CF):
            continue
        source = funcs.get_func(x.frm)
        rows.append({"call_site": hex_ea(x.frm), "target": hex_ea(x.to),
                     "caller": hex_ea(source.start_ea) if source else None, "xref_type": int(x.type)})
    return dict(meta, rows=rows, scope="Direct entry call xrefs; indirect/tail calls remain unknown")


def callees(address, max_items=1000, offset=0):
    ready()
    f, utils, xref = function_at(address), module("idautils"), module("ida_xref")
    ua, idp = module("ida_ua"), module("ida_idp")
    def events():
        for item in utils.FuncItems(f.start_ea):
            insn = ua.insn_t()
            if not ua.decode_insn(insn, item) or not idp.is_call_insn(insn):
                yield ("skip", None)
                continue
            found = False
            for x in utils.XrefsFrom(item, 0):
                if x.type in (xref.fl_CN, xref.fl_CF):
                    found = True
                    yield ("edge", {"caller": hex_ea(f.start_ea), "call_site": hex_ea(item),
                                   "target": hex_ea(x.to), "xref_type": int(x.type)})
                else:
                    yield ("skip", None)
            if not found:
                yield ("unresolved", hex_ea(item))
    items, meta = _window(events(), offset, max_items)
    return dict(meta, rows=[v for k,v in items if k=="edge"],
                unresolved_call_sites=[v for k,v in items if k=="unresolved"],
                pagination_unit="events: non-call item, each outgoing xref, unresolved call marker",
                scope="Recognized calls only; tail jumps and runtime targets not resolved")

def callgraph_page(start=0, limit=25, max_items_per_function=1000):
    result = functions_page(start, bounded(limit, 100))
    result["functions_complete"] = result["complete"]
    result["functions"] = result.pop("rows")
    result["rows"], result["incomplete_functions"] = [], []
    for f in result["functions"]:
        calls = callees(f["ea"], max_items_per_function)
        result["rows"].extend(calls["rows"])
        if calls["truncated"] or calls["unresolved_call_sites"]:
            result["incomplete_functions"].append({"ea": f["ea"], "details": calls})
    result["complete"] = result["functions_complete"] and not any(x["details"]["truncated"] for x in result["incomplete_functions"])
    result["fully_resolved"] = not result["incomplete_functions"]
    return result


def decompile_batch(addresses):
    """At most 20 explicit functions; no whole-program decompilation default."""
    addresses = list(addresses)
    if not 1 <= len(addresses) <= 20:
        raise ValueError("Supply 1..20 explicit function addresses")
    result, seen = [], set()
    for address in addresses:
        started = time.monotonic()
        try:
            canonical = function_at(address).start_ea
            if canonical in seen:
                continue
            seen.add(canonical)
            row = {"ok": True, "data": pseudocode(canonical)}
        except Exception as exc:
            row = {"ok": False, "address": str(address), "error": str(exc)}
        row["seconds"] = time.monotonic() - started
        result.append(row)
        print("SkillForge decompile: %d/%d" % (len(result), len(addresses)))
    return result


def report(operation, *args, context_snapshot=None, **kwargs):
    """Known read-only command dispatcher; never eval arbitrary remote input."""
    allowed = {"count_functions": count_functions, "functions": functions_page,
               "strings": strings_page, "string_xrefs": string_xrefs, "xrefs_to": xrefs_to, "assembly": assembly,
               "pseudocode": pseudocode, "callers": callers, "callees": callees,
               "callgraph": callgraph_page, "decompile_batch": decompile_batch,
               "function_info": function_info, "analysis_state": analysis_state,
               "hexrays_status": hexrays_status}
    if operation not in allowed:
        raise ValueError("Unsupported read operation")
    started = time.monotonic()
    result = {"schema": "skillforge.ida.evidence.v1", "context": context() if context_snapshot is None else dict(context_snapshot), "operation": operation,
              "operation_utc": datetime.now(timezone.utc).isoformat(),
              "arguments": {"args": args, "kwargs": kwargs}, "confidence": "observed-idb-state",
              "limitations": ["IDA runtime not validated by SkillForge packaging tests",
                              "IDA names/types/xrefs can be inferred, stale, user-defined or incomplete"]}
    try:
        result["data"] = allowed[operation](*args, **kwargs)
        result["ok"] = True
    except Exception as exc:
        result["ok"], result["error"] = False, str(exc)
    result["seconds"] = time.monotonic() - started
    return result


def csv_safe(value):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    # Binary-provided names/strings are untrusted spreadsheet input.
    if text.startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
        text = "'" + text
    return text


def export(result, path, fmt="json", *, return_status=False):
    """独占发布；默认返回路径，return_status=True另报告发布后清理状态。
    发布前失败仍抛异常；发布后清理失败不借warnings/输出通道改变结果。
    """
    if fmt not in ("json", "csv", "markdown"):
        raise ValueError("fmt must be json, csv or markdown")
    path = os.path.abspath(os.fspath(path))
    if os.path.lexists(path):
        raise FileExistsError(path)
    partial = path + ".partial"
    with open(partial, "x", encoding="utf-8", newline="") as stream:
        if fmt == "json":
            json.dump(result, stream, ensure_ascii=False, indent=2)
        elif fmt == "markdown":
            # JSON in code blocks prevents binary text from becoming report instructions/links.
            payload = json.dumps(result, ensure_ascii=False, indent=2)
            fence = "`" * max(3, max((len(m.group()) + 1 for m in re.finditer(r"`+", payload)), default=3))
            stream.write("# IDA evidence export\n\n" + fence + "json\n" + payload + "\n" + fence + "\n")
        else:
            # Envelope preserves provenance even when the CSV is distributed alone.
            writer = csv.writer(stream)
            writer.writerow(["record_kind", "record_json"])
            writer.writerow(["context", csv_safe(result.get("context", {}))])
            writer.writerow(["result", csv_safe(result)])
        stream.flush()
        os.fsync(stream.fileno())
    # Close must succeed before no-overwrite publication. Unsupported hard links fail closed.
    os.link(partial, path)
    status = {"path": path, "published": True, "partial_path": partial, "cleanup_error": None}
    try:
        os.unlink(partial)
    except OSError as exc:
        status["cleanup_error"] = str(exc)
    return status if return_status else path


def on_main_thread(callable_, write=False):
    """GUI RPC worker bridge. Do not call while holding a lock the UI needs.
    Headless callers must already be on the owner thread; use direct calls there.
    """
    kw = module("ida_kernwin")
    require(kw, "execute_sync", "MFF_READ", "MFF_WRITE")
    box = {}
    def callback():
        try:
            box["value"] = callable_()
        except Exception as exc:
            box["error"] = exc
        return 1
    rc = kw.execute_sync(callback, kw.MFF_WRITE if write else kw.MFF_READ)
    if rc == -1 or not box:
        raise AnalysisError("Main-thread dispatch was rejected")
    if "error" in box:
        raise box["error"]
    return box["value"]
