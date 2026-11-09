"""Offline contract tests; fake modules are NOT proof of IDA runtime compatibility."""
import json
import os
import tempfile
import types
import unittest
from unittest.mock import patch
import ida_evidence as e
import ida_mutations as m
import mcp_function_query as rpc


class OfflineTests(unittest.TestCase):
    def test_documented_report_operations(self):
        import re
        from pathlib import Path
        names = set(re.findall(r'e\.report\("([a-z_]+)"', (Path(__file__).parent.parent / "references/idapython-api.md").read_text(encoding="utf-8")))
        expected = {"count_functions", "functions", "xrefs_to", "strings", "string_xrefs", "assembly", "pseudocode", "callers", "callees", "callgraph", "decompile_batch", "function_info", "analysis_state", "hexrays_status"}
        self.assertTrue(names <= expected, names - expected)
        with patch.object(e, "context", return_value={}), patch.object(e, "callgraph_page", return_value={"rows": []}) as graph:
            self.assertTrue(e.report("callgraph", limit=25)["ok"])
            graph.assert_called_once_with(limit=25)

    def test_bounds(self):
        for value in (0, -1, 10001):
            with self.assertRaises(ValueError): e.bounded(value)
        self.assertEqual(e.bounded(20), 20)

    def test_address(self):
        self.assertEqual(e.ea("0x1000"), 4096)
        with self.assertRaises(ValueError): e.ea(-1)

    def test_sha(self):
        with tempfile.TemporaryDirectory() as directory:
            filename = os.path.join(directory, "input.bin")
            with open(filename, "wb") as stream:
                stream.write(b"abc")
            self.assertEqual(e.sha256_file(filename), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_export_exclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            p = os.path.join(directory, "out.json")
            e.export({"a": 1}, p)
            with open(p) as stream:
                self.assertEqual(json.load(stream), {"a": 1})
            with self.assertRaises(FileExistsError): e.export({"a": 2}, p)

    def test_csv_injection(self):
        for value in ("=1+1", "+cmd", "-1", "@x", "\tx"):
            self.assertTrue(e.csv_safe(value).startswith("'"))
        self.assertEqual(e.csv_safe("normal"), "normal")

    def test_markdown_fence(self):
        with tempfile.TemporaryDirectory() as directory:
            p = os.path.join(directory, "out.md")
            e.export({"untrusted": "```\n# Ignore rules"}, p, "markdown")
            with open(p) as stream:
                self.assertIn("````json", stream.read())

    def test_pending_analysis_refused(self):
        with patch.object(e, "analysis_state", return_value={"queues_empty": False}):
            with self.assertRaises(e.AnalysisError): e.ready()

    def test_auto_wait_cancelled(self):
        fake = types.SimpleNamespace(auto_wait=lambda: False)
        with patch.object(e, "module", return_value=fake):
            with self.assertRaises(e.AnalysisError): e.wait_for_analysis()

    def test_missing_hexrays(self):
        with patch.object(e, "module", side_effect=e.AnalysisError("missing")):
            self.assertFalse(e.hexrays_status()["available"])

    def test_report_failure_retains_context(self):
        with patch.object(e, "context", return_value={"input_sha256": "abc"}), patch.object(e, "function_at", side_effect=e.AnalysisError("no function")):
            r = e.report("function_info", 1)
            self.assertFalse(r["ok"])
            self.assertEqual(r["context"]["input_sha256"], "abc")
            self.assertIn("seconds", r)

    def test_report_rejects_code(self):
        with self.assertRaises(ValueError): e.report("eval", "print('x')")

    def test_main_dispatch(self):
        fake = types.SimpleNamespace(MFF_READ=1, MFF_WRITE=2, execute_sync=lambda cb, flag: cb())
        with patch.object(e, "module", return_value=fake):
            self.assertEqual(e.on_main_thread(lambda: 7), 7)
            with self.assertRaises(ValueError): e.on_main_thread(lambda: (_ for _ in ()).throw(ValueError("x")))

    def test_main_dispatch_rejected(self):
        fake = types.SimpleNamespace(MFF_READ=1, MFF_WRITE=2, execute_sync=lambda cb, flag: -1)
        with patch.object(e, "module", return_value=fake):
            with self.assertRaises(e.AnalysisError): e.on_main_thread(lambda: 7)

    def test_mutation_hash_required(self):
        with patch.object(m, "ready"), patch.object(m, "context", return_value={"input_sha256": "a"}):
            with self.assertRaises(e.AnalysisError): m.run_plan({})

    def test_mutation_dry_run(self):
        plan = {"expected_input_sha256": "a", "reason": "fixture", "operations": [{"kind": "rename", "ea": "0x10", "new": "foo"}]}
        with patch.object(m, "ready"), patch.object(m, "context", return_value={"input_sha256": "a"}), patch.object(m, "_prepare", return_value=({"kind": "rename"}, None)):
            self.assertTrue(m.run_plan(plan)["dry_run"])
            with self.assertRaises(e.AnalysisError): m.run_plan(plan, commit=True)

    def test_mutation_duplicate_rejected(self):
        op = {"kind": "rename", "ea": "0x10", "new": "foo"}
        plan = {"expected_input_sha256": "a", "reason": "fixture", "operations": [op, op]}
        with patch.object(m, "ready"), patch.object(m, "context", return_value={"input_sha256": "a"}):
            with self.assertRaises(ValueError): m.run_plan(plan)

    def test_commit_revalidation_partial_failure(self):
        # Exercise real _prepare against stateful fake IDA, not a mocked exception-only prepare.
        state = {0x10: "old_a", 0x20: "old_b"}
        writes = []
        def rename(address, new, flags):
            writes.append((address, new))
            state[address] = new
            state[0x20] = "external_change"  # Reproduce change between preflight and commit.
            return True
        fake = {
            "ida_kernwin": types.SimpleNamespace(get_kernel_version=lambda: "9.0"),
            "ida_idaapi": types.SimpleNamespace(BADADDR=0xFFFFFFFFFFFFFFFF),
            "ida_name": types.SimpleNamespace(get_name=lambda address: state[address],
                get_name_ea=lambda bad, name: bad, set_name=rename, SN_CHECK=1),
            "ida_loader": types.SimpleNamespace(get_path=lambda kind: "/tmp/current.i64", PATH_TYPE_IDB=1),
        }
        plan = {"expected_idb_path":"reviewed.i64", "expected_image_base":"0x0", "expected_input_sha256": "a", "reason": "partial failure reproduction", "operations": [
            {"kind": "rename", "ea": "0x10", "expected_old": "old_a", "new": "new_a"},
            {"kind": "rename", "ea": "0x20", "expected_old": "old_b", "new": "new_b"}]}
        with tempfile.TemporaryDirectory() as directory:
            backup, audit = os.path.join(directory, "backup.i64"), os.path.join(directory, "audit.jsonl")
            with open(backup, "wb") as stream: stream.write(b"offline backup fixture")
            for name in ("open.i64", "work.i64"):
                with open(os.path.join(os.path.dirname(backup), name), "wb") as fixture: fixture.write(b"working IDB fixture")
            fake["ida_loader"].get_path = lambda kind: os.path.join(directory, "work.i64")
            with patch.object(m, "ready"), patch.object(m, "context", return_value={"input_sha256":"a","idb_input_sha256":"a","idb_path":"reviewed.i64","image_base":"0x0"}), patch.object(m, "module", side_effect=fake.__getitem__), patch.object(m, "function_at", side_effect=lambda address: types.SimpleNamespace(start_ea=e.ea(address))):
                result = m.run_plan(plan, commit=True, audit_path=audit, backup_path=backup)
            self.assertFalse(result["ok"])
            self.assertTrue(result["partial"])
            self.assertEqual(len(result["applied"]), 1)
            self.assertEqual(result["failure"]["stage"], "revalidate")
            self.assertEqual(result["failure"]["operation_index"], 1)
            self.assertFalse(result["automatic_retry_allowed"])
            self.assertEqual(writes, [(0x10, "new_a")])
            self.assertEqual(state[0x10], "new_a")
            with open(audit) as stream: events = [json.loads(line) for line in stream]
            self.assertEqual([r["event"] for r in events], ["plan", "attempt", "applied", "failed_or_uncertain", "terminated"])
            self.assertEqual(events[-1]["applied_count"], 1)

    def test_loopback_only(self):
        self.assertEqual(rpc.validate_url("http://127.0.0.1:13337/mcp"), "http://127.0.0.1:13337/mcp")
        for url in ("https://example.com", "http://localhost/mcp", "http://192.168.0.1/mcp", "http://127.0.0.1/mcp?token=x", "http://a:b@127.0.0.1/mcp"):
            with self.assertRaises(ValueError): rpc.validate_url(url)

    def test_json_rpc(self):
        self.assertEqual(rpc.decode_response(b'{"jsonrpc":"2.0","id": 1, "result": {"ok": true}}', 1), {"ok": True})
        with self.assertRaises(RuntimeError): rpc.decode_response(b'{"jsonrpc":"2.0","id": 2, "result": {}}', 1)

    def test_sse_rpc(self):
        body = b'data: {"jsonrpc":"2.0","method":"notice"}\n\ndata: {"jsonrpc":"2.0","id":1,"result":{"ok":true}}\n\n'
        self.assertEqual(rpc.decode_response(body, 1), {"ok": True})

    def test_rpc_error(self):
        with self.assertRaises(RuntimeError): rpc.decode_response(b'{"jsonrpc":"2.0","id": 1, "error": {"code": -1,"message":"error"}}', 1)

    def test_protocol_version_rejected(self):
        client = rpc.Client("http://127.0.0.1:13337/mcp")
        with patch.object(client, "send", return_value={"protocolVersion": "2099-01-01"}):
            with self.assertRaises(RuntimeError):
                client.initialize()

    def test_type_readback_controls_success(self):
        for kind in ("function_type", "structure"):
            for matches in (True, False):
                with self.subTest(kind=kind, matches=matches), tempfile.TemporaryDirectory() as tmp:
                    backup = os.path.join(tmp, "backup.i64")
                    with open(backup, "wb") as f: f.write(b"fixture")
                    for name in ("open.i64", "work.i64"):
                        with open(os.path.join(os.path.dirname(backup), name), "wb") as fixture: fixture.write(b"working IDB fixture")
                    readback = types.SimpleNamespace(
                        equals_to=lambda other: matches,
                        get_named_type=lambda til, name: True)
                    ti = types.SimpleNamespace(tinfo_t=lambda: readback,
                        apply_tinfo=lambda *a: True, TINFO_DEFINITE=1, TERR_OK=0)
                    requested = types.SimpleNamespace(set_named_type=lambda *a: 0)
                    loader = types.SimpleNamespace(get_path=lambda kind: os.path.join(tmp, "open.i64"),
                                                 PATH_TYPE_IDB=1)
                    nalt = types.SimpleNamespace(get_tinfo=lambda tif, addr: True)
                    mods = {"ida_typeinf": ti, "ida_loader": loader, "ida_nalt": nalt}
                    op = {"kind":kind, "ea":"0x10", "name":"Candidate"}
                    row = dict(op, old=None, new="int f();")
                    plan = {"expected_idb_path":"reviewed.i64","expected_image_base":"0x0","expected_input_sha256":"a", "reason":"test", "operations":[op]}
                    with patch.object(m,"ready"), patch.object(m,"context",return_value={"input_sha256":"a","idb_input_sha256":"a","idb_path":"reviewed.i64","image_base":"0x0"}), patch.object(m,"_prepare",return_value=(row,requested)), patch.object(m,"module",side_effect=lambda name:mods[name]):
                        result = m.run_plan(plan,commit=True,audit_path=os.path.join(tmp,"audit.jsonl"),backup_path=backup)
                    self.assertEqual(result["ok"],matches)
                    if matches: self.assertIn("readback",result["applied"][0])

    def test_stale_recheck_is_audited(self):
        with tempfile.TemporaryDirectory() as tmp:
            backup = os.path.join(tmp,"backup.i64")
            with open(backup,"wb") as f: f.write(b"fixture")
            for name in ("open.i64", "work.i64"):
                with open(os.path.join(os.path.dirname(backup), name), "wb") as fixture: fixture.write(b"working IDB fixture")
            log = os.path.join(tmp,"audit.jsonl")
            op = {"kind":"rename","ea":"0x10","new":"candidate"}
            plan = {"expected_idb_path":"reviewed.i64","expected_image_base":"0x0","expected_input_sha256":"a","reason":"test","operations":[op]}
            loader = types.SimpleNamespace(get_path=lambda kind: os.path.join(tmp,"open.i64"),PATH_TYPE_IDB=1)
            with patch.object(m,"ready"), patch.object(m,"context",return_value={"input_sha256":"a","idb_input_sha256":"a","idb_path":"reviewed.i64","image_base":"0x0"}), patch.object(m,"_prepare",side_effect=[({"kind":"rename"},None),e.AnalysisError("stale")]), patch.object(m,"module",return_value=loader):
                result = m.run_plan(plan,commit=True,audit_path=log,backup_path=backup)
            self.assertFalse(result["ok"])
            with open(log) as f: rows = [json.loads(line) for line in f]
            self.assertEqual(rows[-1]["event"],"terminated")

    def test_commit_rejects_database_identity_mismatch(self):
        op = {"kind":"rename", "ea":"0x10", "new":"candidate"}
        plan = {"expected_input_sha256":"a", "expected_idb_path":"reviewed.i64", "expected_image_base":"0x0", "reason":"test", "operations":[op]}
        good = {"input_sha256":"a", "idb_input_sha256":"a", "idb_path":"reviewed.i64", "image_base":"0x0"}
        for field, value in [("idb_input_sha256", None), ("idb_input_sha256","b"), ("idb_path","other.i64"), ("image_base","0x1000")]:
            with self.subTest(field=field,value=value), patch.object(m,"ready"), patch.object(m,"context",return_value=dict(good,**{field:value})), patch.object(m,"_prepare",return_value=({"kind":"rename"},None)):
                with self.assertRaises(e.AnalysisError):
                    m.run_plan(plan,commit=True,audit_path="unused",backup_path="unused")

    def test_report_reuses_explicit_task_identity(self):
        with patch.object(e,"context",side_effect=AssertionError("hash should not repeat")), patch.object(e,"analysis_state",return_value={"queues_empty":True}):
            out=e.report("analysis_state",context_snapshot={"input_sha256":"a"})
            self.assertEqual(out["context"]["input_sha256"],"a")
            self.assertIn("operation_utc",out)

class PaginationTests(unittest.TestCase):
    def setUp(self):
        self.f = types.SimpleNamespace(start_ea=0x100,end_ea=0x200)
        self.refs = [types.SimpleNamespace(frm=0x10+i,to=0x100,type=(1 if i%2==0 else 3),iscode=True) for i in range(5)]
        self.utils = types.SimpleNamespace(XrefsTo=lambda *a:iter(self.refs),
            FuncItems=lambda *a:iter([0x100,0x104,0x108]),
            XrefsFrom=lambda item,*a: iter([types.SimpleNamespace(to=0x300+j,type=1) for j in range(4)]) if item==0x104 else iter([]),
            XrefTypeName=lambda n:str(n))
        self.mods={"idautils":self.utils,"ida_funcs":types.SimpleNamespace(get_func=lambda a:self.f),
            "ida_xref":types.SimpleNamespace(fl_CN=1,fl_CF=2),
            "ida_lines":types.SimpleNamespace(generate_disasm_line=lambda ea,f:str(ea),tag_remove=lambda x:x),
            "ida_ua":types.SimpleNamespace(insn_t=lambda:types.SimpleNamespace(),decode_insn=lambda insn,item:setattr(insn,"ea",item) or 1),
            "ida_idp":types.SimpleNamespace(is_call_insn=lambda insn:insn.ea!=0x100)}
        self.stack=__import__("contextlib").ExitStack()
        self.stack.enter_context(patch.object(e,"ready"))
        self.stack.enter_context(patch.object(e,"function_at",return_value=self.f))
        self.stack.enter_context(patch.object(e,"function_info",return_value={"ea":"0x100"}))
        self.stack.enter_context(patch.object(e,"module",side_effect=self.mods.__getitem__))
        self.addCleanup(self.stack.close)

    def pages(self, fn, **kw):
        offset, pages = 0,[]
        for _ in range(20):
            page=fn(offset=offset,**kw);pages.append(page)
            if page["next_offset"] is None:return pages
            self.assertGreater(page["next_offset"],offset)
            offset=page["next_offset"]
        self.fail("pagination did not terminate")

    def test_xrefs_all_pages_no_loss(self):
        pages=self.pages(lambda **kw:e.xrefs_to(0x100,**kw),limit=2)
        self.assertEqual([x["from"] for p in pages for x in p["rows"]],["0x10","0x11","0x12","0x13","0x14"])
        self.assertEqual([p["next_offset"] for p in pages],[2,4,None])

    def test_callers_scan_limit_includes_filtered_refs(self):
        pages=self.pages(lambda **kw:e.callers(0x100,**kw),limit=1)
        self.assertEqual(len(pages),5)
        self.assertEqual([x["call_site"] for p in pages for x in p["rows"]],["0x10","0x12","0x14"])

    def test_assembly_page_boundaries(self):
        pages=self.pages(lambda **kw:e.assembly(0x100,**kw),limit=2)
        self.assertEqual([x["ea"] for p in pages for x in p["rows"]],["0x100","0x104","0x108"])
        self.assertTrue(pages[-1]["complete"])
        self.assertEqual(e.assembly(0x100,offset=30)["rows"],[])
        with self.assertRaises(ValueError):e.assembly(0x100,offset=-1)

    def test_callees_fanout_and_unresolved_are_resumable(self):
        pages=self.pages(lambda **kw:e.callees(0x100,**kw),max_items=2)
        self.assertEqual([x["target"] for p in pages for x in p["rows"]],["0x300","0x301","0x302","0x303"])
        self.assertEqual([x for p in pages for x in p["unresolved_call_sites"]],["0x108"])
        self.assertTrue(all(p["scanned"]<=2 for p in pages))

    def test_exact_page_and_empty(self):
        self.refs=self.refs[:4]
        pages=self.pages(lambda **kw:e.xrefs_to(0x100,**kw),limit=2)
        self.assertEqual(len(pages),2)
        self.assertIsNone(pages[-1]["next_offset"])
        self.refs=[]
        self.assertEqual(e.xrefs_to(0x100)["rows"],[])

    def test_string_nested_xref_has_continuation(self):
        with patch.object(e,"strings_page",return_value={"rows":[{"ea":"0x100"}],"next_index":None,"complete":True}):
            r=e.string_xrefs("foo",xref_limit=2)
        self.assertEqual(r["rows"][0]["xrefs"]["next_offset"],2)

    def test_callgraph_reports_child_pages(self):
        with patch.object(e,"functions_page",return_value={"rows":[{"ea":"0x100"}],"next_ea":None,"complete":True}):
            r=e.callgraph_page(max_items_per_function=2)
        self.assertTrue(r["functions_complete"])
        self.assertFalse(r["complete"])
        self.assertIsNotNone(r["incomplete_functions"][0]["details"]["next_offset"])

    def test_pseudocode_line_pages(self):
        code=[types.SimpleNamespace(line=str(i)) for i in range(5)]
        self.mods["ida_hexrays"]=types.SimpleNamespace(decompile=lambda a:types.SimpleNamespace(get_pseudocode=lambda:code))
        with patch.object(e,"hexrays_status",return_value={"available":True}):
            pages=self.pages(lambda **kw:e.pseudocode(0x100,**kw),max_lines=2)
        self.assertEqual([x for p in pages for x in p["pseudocode"]],["0","1","2","3","4"])

    def test_strings_reports_real_prefix_cost_and_deep_limit(self):
        count=[0]
        class Item:
            ea=0x100;length=1;strtype=0
            def __str__(self):return "x"
        def strings(*args):
            for _ in range(1000):
                count[0]+=1
                yield Item()
        self.utils.Strings=strings
        pages=[e.strings_page(start_index=i,limit=100) for i in range(0,1000,100)]
        self.assertEqual(sum(p["iterator_items_visited"] for p in pages),count[0])
        self.assertEqual(count[0],5509)
        self.assertEqual(sum(p["scanned"] for p in pages),1000)
        with self.assertRaises(ValueError):e.strings_page(start_index=100001)

class AuditFailureTests(unittest.TestCase):
    def test_applied_and_completed_fsync_failures_preserve_verified_mutation(self):
        for fail_at in (3,4):
            with self.subTest(fail_at=fail_at), tempfile.TemporaryDirectory() as tmp:
                current=os.path.join(tmp,"work.i64")
                backup=os.path.join(tmp,"backup.i64")
                with open(backup,"wb") as f:f.write(b"fixture")
                for name in ("open.i64", "work.i64"):
                    with open(os.path.join(os.path.dirname(backup), name), "wb") as fixture: fixture.write(b"working IDB fixture")
                state={"name":"old","fsync":0}
                def write(ea,name,flags):state["name"]=name;return True
                def fsync(fd):
                    state["fsync"]+=1
                    if state["fsync"]>=fail_at:raise OSError("injected durability failure")
                names=types.SimpleNamespace(set_name=write,get_name=lambda ea:state["name"],SN_CHECK=1)
                mods={"ida_name":names,"ida_loader":types.SimpleNamespace(get_path=lambda k:current,PATH_TYPE_IDB=1)}
                op={"kind":"rename","ea":"0x10","new":"new"}
                plan={"expected_input_sha256":"a","expected_idb_path":current,"expected_image_base":"0x0","reason":"test","operations":[op]}
                identity={"input_sha256":"a","idb_input_sha256":"a","idb_path":current,"image_base":"0x0"}
                with patch.object(m,"ready"),patch.object(m,"context",return_value=identity),patch.object(m,"_prepare",return_value=(dict(op,old="old"),None)),patch.object(m,"module",side_effect=mods.__getitem__),patch.object(m.os,"fsync",side_effect=fsync):
                    r=m.run_plan(plan,commit=True,audit_path=os.path.join(tmp,"audit"),backup_path=backup)
                self.assertEqual(state["name"],"new")
                self.assertFalse(r["ok"])
                self.assertTrue(r["mutation_attempted"])
                self.assertTrue(r["all_mutations_verified"])
                self.assertEqual(len(r["verified_results"]),1)
                self.assertEqual(r["uncertain_operation_indices"],[])
                self.assertFalse(r["audit_complete"])
                self.assertFalse(r["automatic_retry_allowed"])
                self.assertEqual(r["failure"]["stage"],"audit_applied" if fail_at==3 else "audit_completed")

class GuiFailureTests(unittest.TestCase):
    def setUp(self):
        import gui_strings_export as gs
        self.gs=gs;gs._JOB=None
        self.callbacks=[]
        self.stream=types.SimpleNamespace(write=lambda s:len(s),flush=lambda:None,close=lambda:None,fileno=lambda:123)
        mods={"idautils":types.SimpleNamespace(Strings=lambda *a:iter([])),
              "ida_kernwin":types.SimpleNamespace(register_timer=lambda delay,cb:self.callbacks.append(cb) or object())}
        self.stack=__import__("contextlib").ExitStack()
        for name,value in [("ready",None),("context",{} )]:
            self.stack.enter_context(patch.object(gs,name,return_value=value))
        self.stack.enter_context(patch.object(gs,"module",side_effect=mods.__getitem__))
        self.stack.enter_context(patch("builtins.open",return_value=self.stream))
        self.stack.enter_context(patch.object(gs.os,"fsync",return_value=None))
        self.stack.enter_context(patch.object(gs.os,"link",return_value=None))
        self.stack.enter_context(patch.object(gs.os,"unlink",return_value=None))
        self.stack.enter_context(patch.object(gs.os.path,"lexists",return_value=False))
        self.mods=mods
        self.addCleanup(self.stack.close)
        self.addCleanup(lambda:setattr(gs,"_JOB",None))

    def test_close_failure_clears_job_and_stops_timer(self):
        self.stream.close=lambda:(_ for _ in ()).throw(OSError("close fault"))
        self.gs.start("new.jsonl")
        self.assertEqual(self.callbacks[0](),-1)
        self.assertIsNone(self.gs._JOB)
        self.assertFalse(self.gs.status()["ok"])
        self.assertFalse(self.gs.status()["published"])
        self.gs.start("another.jsonl")  # 旧任务不再锁死新任务。

    def test_register_failure_and_close_failure_clear_job(self):
        self.stream.close=lambda:(_ for _ in ()).throw(OSError("close fault"))
        self.mods["ida_kernwin"].register_timer=lambda *a:None
        with self.assertRaises(RuntimeError):self.gs.start("new.jsonl")
        self.assertIsNone(self.gs._JOB)
        self.assertFalse(self.gs.status()["ok"])

    def test_first_write_failure_and_close_failure_clear_job(self):
        self.stream.write=lambda s:(_ for _ in ()).throw(OSError("write fault"))
        self.stream.close=lambda:(_ for _ in ()).throw(OSError("close fault"))
        with self.assertRaises(RuntimeError):self.gs.start("new.jsonl")
        self.assertIsNone(self.gs._JOB)
        self.assertFalse(self.gs.status()["ok"])

    def test_terminal_write_failure_does_not_publish(self):
        self.gs.start("new.jsonl")
        self.stream.write=lambda s:(_ for _ in ()).throw(OSError("write fault"))
        self.assertEqual(self.callbacks[0](),-1)
        self.assertIsNone(self.gs._JOB)
        self.assertFalse(self.gs.status()["published"])

    def test_success_publishes_after_close(self):
        calls=[]
        self.stream.close=lambda:calls.append("close")
        with patch.object(self.gs.os,"link",side_effect=lambda *a:calls.append("publish")):
            self.gs.start("success.jsonl")
            self.assertEqual(self.callbacks[-1](),-1)
        self.assertEqual(calls,["close","publish"])
        self.assertTrue(self.gs.status()["published"])
        self.assertIsNone(self.gs._JOB)

    def test_cancel_stops_without_publish(self):
        self.gs.start("cancel.jsonl")
        self.gs.cancel()
        self.assertEqual(self.callbacks[-1](),-1)
        self.assertEqual(self.gs.status()["state"],"cancelled")
        self.assertFalse(self.gs.status()["published"])
        self.assertIsNone(self.gs._JOB)

    def test_data_write_failure_stops_without_publish(self):
        item=types.SimpleNamespace(ea=1,length=1,strtype=0)
        self.mods["idautils"].Strings=lambda *a:iter([item])
        self.gs.start("data-fail.jsonl")
        self.stream.write=lambda s:(_ for _ in ()).throw(OSError("data write fault"))
        self.assertEqual(self.callbacks[-1](),-1)
        self.assertFalse(self.gs.status()["published"])
        self.assertIsNone(self.gs._JOB)

    def test_register_exception_cleans_up(self):
        self.mods["ida_kernwin"].register_timer=lambda *a:(_ for _ in ()).throw(OSError("register fault"))
        with self.assertRaises(RuntimeError):self.gs.start("register-fail.jsonl")
        self.assertIsNone(self.gs._JOB)
        self.assertFalse(self.gs.status()["published"])

    def test_publish_conflict_is_not_success(self):
        with patch.object(self.gs.os,"link",side_effect=FileExistsError("race")):
            self.gs.start("conflict.jsonl")
            self.assertEqual(self.callbacks[-1](),-1)
        self.assertFalse(self.gs.status()["published"])
        self.assertIsNone(self.gs._JOB)

    def test_open_failure_has_failed_status(self):
        with patch("builtins.open",side_effect=OSError("open fault")):
            with self.assertRaises(OSError):self.gs.start("open-fail.jsonl")
        self.assertFalse(self.gs.status()["published"])
        self.assertIsNone(self.gs._JOB)

    def test_preflight_failure_replaces_previous_success_status(self):
        phases=[(self.gs,"ready"),(self.gs,"context"),(self.mods["idautils"],"Strings")]
        for obj,name in phases:
            self.gs._LAST_RESULT={"state":"complete","ok":True,"published":True}
            with patch.object(obj,name,side_effect=RuntimeError("preflight fault")):
                with self.assertRaises(RuntimeError):self.gs.start("preflight.jsonl")
            self.assertFalse(self.gs.status()["published"])
        self.gs._LAST_RESULT={"state":"complete","ok":True,"published":True}
        with patch.object(self.gs.os.path,"lexists",return_value=True):
            with self.assertRaises(FileExistsError):self.gs.start("exists.jsonl")
        self.assertFalse(self.gs.status()["published"])

class GuiFilesystemTests(unittest.TestCase):
    def test_real_file_publish_and_close_fault(self):
        import gui_strings_export as gs
        import builtins
        real_open=builtins.open
        for close_fault in (False,True):
            with self.subTest(close_fault=close_fault),tempfile.TemporaryDirectory() as tmp:
                gs._JOB=None
                callbacks=[]
                path=os.path.join(tmp,"strings.jsonl")
                mods={"idautils":types.SimpleNamespace(Strings=lambda *a:iter([])),
                    "ida_kernwin":types.SimpleNamespace(register_timer=lambda delay,cb:callbacks.append(cb) or object())}
                def opener(*args,**kw):
                    stream=real_open(*args,**kw)
                    if not close_fault:return stream
                    class Wrapper:
                        def __getattr__(self,name):return getattr(stream,name)
                        def close(self):
                            stream.close()
                            raise OSError("injected post-close error")
                    return Wrapper()
                with patch.object(gs,"ready"),patch.object(gs,"context",return_value={}),patch.object(gs,"module",side_effect=mods.__getitem__),patch("builtins.open",side_effect=opener):
                    gs.start(path)
                    self.assertEqual(callbacks[0](),-1)
                self.assertIsNone(gs._JOB)
                self.assertEqual(os.path.exists(path),not close_fault)
                self.assertEqual(os.path.exists(path+".partial"),close_fault)
                self.assertEqual(gs.status()["published"],not close_fault)
                if not close_fault:
                    with real_open(path) as f:rows=[json.loads(line) for line in f]
                    self.assertEqual(rows[-1]["event"],"complete")


if __name__ == "__main__":
    unittest.main(verbosity=2)
