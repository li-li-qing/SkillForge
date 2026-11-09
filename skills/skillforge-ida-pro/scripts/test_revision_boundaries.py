"""Offline boundary regression tests, not IDA runtime validation."""
import json, os, tempfile, unittest, types
from pathlib import Path
from unittest.mock import patch
import ida_evidence as e
import ida_mutations as m
import mcp_function_query as rpc

class Boundaries(unittest.TestCase):
    def test_strings_offset_uses_one_parser(self):
        class Item:
            ea = 0x100
            length = 1
            strtype = 0
            def __str__(self): return 'fixture'
        with patch.object(e, 'ready'), patch.object(e, 'module', return_value=types.SimpleNamespace(Strings=lambda _: [Item(), Item(), Item()])):
            for offset in (1, '1', '01', '0x1', '0o1', '0b1'):
                with self.subTest(offset=offset):
                    result = e.strings_page(offset, 1)
                    self.assertEqual(result['offset'], 1)
                    self.assertEqual(result['rows'][0]['index'], 1)
                    self.assertEqual(result['next_index'], 2)
            for offset in (True, 1.0, '-1', '0xG'):
                with self.assertRaises(ValueError): e.strings_page(offset, 1)

    def test_export_cleanup_warning_cannot_hide_publication(self):
        import warnings
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'out.json'
            with warnings.catch_warnings():
                warnings.simplefilter('error')
                with patch.object(e.os, 'unlink', side_effect=OSError('cleanup denied')):
                    result = e.export({'ok': True}, p)
            self.assertIs(type(result), str)
            self.assertEqual(result, str(p))
            self.assertEqual(json.loads(p.read_text()), {'ok': True})
            self.assertTrue(Path(str(p) + '.partial').exists())

    def test_export_optional_status(self):
        import warnings
        for cleanup_error in (False, True):
            with self.subTest(cleanup_error=cleanup_error), tempfile.TemporaryDirectory() as tmp:
                p = Path(tmp) / 'out.json'
                real_unlink = e.os.unlink
                with warnings.catch_warnings():
                    warnings.simplefilter('error')
                    with patch.object(e.os, 'unlink', side_effect=OSError('cleanup denied') if cleanup_error else real_unlink):
                        status = e.export({}, p, return_status=True)
                self.assertTrue(status['published'])
                self.assertEqual(status['path'], str(p))
                self.assertEqual(status['partial_path'], str(p) + '.partial')
                self.assertEqual(status['cleanup_error'], 'cleanup denied' if cleanup_error else None)
                self.assertEqual(Path(status['partial_path']).exists(), cleanup_error)

    def test_batch_propagates_export_state_without_changing_analysis(self):
        import run_ida_batch as batch
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'out.json'
            analysis = {'ok': False, 'seconds': 0.1, 'error': 'analysis fixture failure'}
            with patch.object(batch, 'report', return_value=analysis.copy()), patch.object(e.os, 'unlink', side_effect=OSError('cleanup denied')), patch('builtins.print', side_effect=BrokenPipeError('closed output')):
                result = batch.run({'operation': 'fixture', 'output': str(p)})
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], analysis['error'])
            self.assertTrue(result['export_status']['published'])
            self.assertEqual(result['export_status']['cleanup_error'], 'cleanup denied')
            self.assertEqual(json.loads(p.read_text()), analysis)

    def test_batch_closed_stdout_preserves_published_result(self):
        import io
        from contextlib import redirect_stdout
        import run_ida_batch as batch
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'out.json'
            closed = io.StringIO()
            closed.close()
            analysis = {'ok': True, 'seconds': 0}
            with patch.object(batch, 'report', return_value=analysis.copy()), redirect_stdout(closed):
                result = batch.run({'operation': 'fixture', 'output': str(p)})
            self.assertTrue(result['export_status']['published'])
            self.assertIn('closed', result['export_status']['diagnostic_error'])
            self.assertEqual(json.loads(p.read_text()), analysis)

    def test_batch_does_not_swallow_interrupt(self):
        import run_ida_batch as batch
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'out.json'
            with patch.object(batch, 'report', return_value={'ok': True, 'seconds': 0}), patch('builtins.print', side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):
                    batch.run({'operation': 'fixture', 'output': str(p)})
            self.assertTrue(p.exists())

    def test_sha_special_files_refused(self):
        import subprocess, sys
        script_dir = str(Path(__file__).resolve().parent)
        code = "import sys;sys.path.insert(0,sys.argv[1]);import ida_evidence as e;e.sha256_file(sys.argv[2])"
        with tempfile.TemporaryDirectory() as tmp:
            paths=[]
            if hasattr(os,"mkfifo"):
                fifo=Path(tmp)/"fifo";os.mkfifo(fifo);paths.append(fifo)
            if Path("/dev/zero").exists():paths.append(Path("/dev/zero"))
            if not paths:self.skipTest("special-file fixtures unavailable")
            for path in paths:
                with self.subTest(path=path):
                    try: result=subprocess.run([sys.executable,"-B","-c",code,script_dir,str(path)],capture_output=True,text=True,timeout=2)
                    except subprocess.TimeoutExpired:self.fail("hash special file blocked")
                    self.assertNotEqual(result.returncode,0)
                    self.assertIn("regular file",result.stderr)

    def test_sha_growth_and_opened_descriptor(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"input";path.write_bytes(b"abc")
            real_sha=hashlib.sha256
            class GrowingDigest:
                def __init__(self):self.digest=real_sha()
                def update(self,block):
                    self.digest.update(block)
                    with path.open("ab") as output:output.write(b"growth")
            with patch.object(e.hashlib,"sha256",GrowingDigest):
                with self.assertRaisesRegex(OSError,"grew"):e.sha256_file(path)
            if Path("/dev/zero").exists():
                fd=os.open("/dev/zero",os.O_RDONLY)
                with patch.object(e.os,"open",return_value=fd):
                    with self.assertRaisesRegex(OSError,"Opened hash input"):e.sha256_file(path)
                with self.assertRaises(OSError):os.fstat(fd)

    def test_sha_large_regular_and_symlink(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"large";data=b"abc123"*(1024*1024);path.write_bytes(data)
            expected=hashlib.sha256(data).hexdigest()
            self.assertEqual(e.sha256_file(path),expected)
            link=Path(tmp)/"alias"
            try:link.symlink_to(path.name)
            except (OSError,NotImplementedError):self.skipTest("symlink unavailable")
            self.assertEqual(e.sha256_file(link),expected)

    def test_strict_numbers(self):
        for value in (True, False, 4096.9, 4096.0):
            with self.subTest(value=value), self.assertRaises(ValueError): e.ea(value)
        for value in (True, 2.9):
            with self.assertRaises(ValueError): e.bounded(value)
        self.assertEqual(e.ea('0x1000'),4096)

    def test_mutation_invalid_address_stops_before_prepare(self):
        for address in (True, 16.9):
            plan={'expected_input_sha256':'a','reason':'test','operations':[{'kind':'rename','ea':address,'new':'x'}]}
            with patch.object(m,'ready'),patch.object(m,'context',return_value={'input_sha256':'a'}),patch.object(m,'_prepare') as prepare:
                with self.assertRaises(ValueError):m.run_plan(plan,commit=True)
                prepare.assert_not_called()

    def test_export_fsync_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'out.json'
            with patch.object(e.os,'fsync',side_effect=OSError('fsync failure')):
                with self.assertRaises(OSError):e.export({},p)
            self.assertFalse(p.exists())
            self.assertTrue(Path(str(p)+'.partial').exists())

    def test_envelope(self):
        invalid=[{'id':1,'result':{}}, {'jsonrpc':'1.0','id':1,'result':{}},
                 {'jsonrpc':'2.0','id':True,'result':{}},
                 {'jsonrpc':'2.0','id':1},
                 {'jsonrpc':'2.0','id':1,'result':{},'error':{}},
                 {'jsonrpc':'2.0','id':1,'error':{'code':True,'message':'bad'}}]
        for obj in invalid:
            with self.subTest(obj=obj),self.assertRaises(RuntimeError): rpc.decode_response(json.dumps(obj).encode(),1)
        self.assertEqual(rpc.decode_response(b'{"jsonrpc":"2.0","id":1,"result":{}}',1),{})

    def test_failed_export_not_published(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'out.json'
            with self.assertRaises(TypeError): e.export({'data':object()},p)
            self.assertFalse(p.exists())
            self.assertTrue(Path(str(p)+'.partial').exists())

    def test_export_close_failure_not_published(self):
        import builtins
        real_open=builtins.open
        class Wrapper:
            def __init__(self,s): self.s=s
            def __getattr__(self,n): return getattr(self.s,n)
            def __enter__(self): return self
            def __exit__(self,*args): self.s.close();raise OSError('close failure')
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'out.json'
            with patch('builtins.open',side_effect=lambda *a,**k:Wrapper(real_open(*a,**k))):
                with self.assertRaises(OSError):e.export({},p)
            self.assertFalse(p.exists())

    def test_export_publish_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'out.json'
            def conflict(src,dst):
                Path(dst).write_text('existing')
                raise FileExistsError(dst)
            with patch.object(e.os,'link',side_effect=conflict):
                with self.assertRaises(FileExistsError):e.export({},p)
            self.assertEqual(p.read_text(),'existing')

    def test_backup_same_inode_and_unknown(self):
        real_samefile=os.path.samefile
        for unknown in (False,True):
            with self.subTest(unknown=unknown),tempfile.TemporaryDirectory() as tmp:
                current=Path(tmp)/'work.i64';current.write_bytes(b'fixture')
                backup=Path(tmp)/'backup.i64';os.link(current,backup)
                identity={'input_sha256':'a','idb_input_sha256':'a','idb_path':str(current),'image_base':'0x0'}
                plan={'expected_input_sha256':'a','expected_idb_path':str(current),'expected_image_base':'0x0','reason':'test','operations':[{'kind':'rename','ea':'0x10','new':'new'}]}
                loader=types.SimpleNamespace(get_path=lambda _:str(current),PATH_TYPE_IDB=1)
                with patch.object(m,'ready'),patch.object(m,'context',return_value=identity),patch.object(m,'_prepare',return_value=({'kind':'rename'},None)),patch.object(m,'module',return_value=loader),patch.object(m.os.path,'samefile',side_effect=OSError('unknown') if unknown else real_samefile):
                    with self.assertRaises(e.AnalysisError):m.run_plan(plan,commit=True,audit_path=Path(tmp)/'audit',backup_path=backup)
                    self.assertFalse((Path(tmp)/'audit').exists())

if __name__=='__main__':unittest.main(verbosity=2)
