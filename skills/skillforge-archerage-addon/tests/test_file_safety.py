"""Offline filesystem fault injection; no game or Lua execution."""
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from test_tools import ROOT, SCRIPTS, module, frames

class FileSafety(unittest.TestCase):
    def setUp(self):
        self.report = module(self, 'verify_report')
        self.skill = module(self, 'verify_skill')

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'FIFO unavailable')
    def test_eval_fifo_rejected_without_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ROOT.name
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns('__pycache__'))
            p = root / 'evals/behavior-cases.json'
            p.unlink(); os.mkfifo(p)
            result = subprocess.run([sys.executable, str(root/'scripts/verify_skill.py'), str(root)], capture_output=True, timeout=2)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)['status'], 'failed')

    def test_output_faults_never_publish_partial(self):
        for fault in ('write', 'short_write', 'flush', 'close', 'fsync', 'publish'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                output = Path(tmp) / 'out'
                original = Path.open
                class Stream:
                    def __init__(self, stream): self.stream=stream
                    def __enter__(self): return self
                    def __exit__(self, *args):
                        self.stream.close()
                        if fault == 'close': raise OSError('close failure')
                    def write(self, data):
                        if fault in ('write', 'short_write'):
                            self.stream.write(data[:2])
                            if fault == 'write': raise OSError('write failure')
                            return 2
                        return self.stream.write(data)
                    def flush(self):
                        if fault == 'flush': raise OSError('flush failure')
                        self.stream.flush()
                    def fileno(self): return self.stream.fileno()
                def opened(path, *args, **kwargs):
                    stream=original(path,*args,**kwargs)
                    return Stream(stream) if args == ('xb',) else stream
                with contextlib.ExitStack() as stack:
                    stack.enter_context(mock.patch.object(Path, 'open', opened))
                    if fault == 'fsync': stack.enter_context(mock.patch.object(self.report.os, 'fsync', side_effect=OSError('sync failure')))
                    if fault == 'publish': stack.enter_context(mock.patch.object(self.report.os, 'link', side_effect=OSError('link failure')))
                    with self.assertRaises(OSError): self.report.publish_output(output, b'abcdef')
                self.assertFalse(output.exists())
                self.assertTrue(Path(str(output)+'.partial').exists())

    def test_no_overwrite_final_or_partial(self):
        for suffix in ('', '.partial'):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as tmp:
                output=Path(tmp)/'out'; existing=Path(str(output)+suffix); existing.write_bytes(b'keep')
                with self.assertRaises(FileExistsError): self.report.publish_output(output,b'new')
                self.assertEqual(existing.read_bytes(),b'keep')

    def test_publish_race_preserves_competitor(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'out'
            def race(source,target):
                Path(target).write_bytes(b'competitor')
                raise FileExistsError(target)
            with mock.patch.object(self.report.os,'link',side_effect=race):
                with self.assertRaises(FileExistsError): self.report.publish_output(output,b'new')
            self.assertEqual(output.read_bytes(),b'competitor')

    def test_cleanup_failure_is_published_even_with_warning_error(self):
        import warnings
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'out'
            with warnings.catch_warnings():
                warnings.simplefilter('error')
                with mock.patch.object(self.report.os,'unlink',side_effect=OSError('cleanup denied')):
                    state=self.report.publish_output(output,b'complete')
            self.assertTrue(state['published']); self.assertEqual(state['cleanup_error'],'cleanup denied')
            self.assertEqual(output.read_bytes(),b'complete')
            self.assertTrue(Path(state['partial_path']).exists())

    def test_regular_reader_rejects_symlink_and_oversize(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'source';p.write_bytes(b'x'*(2*1024*1024+1))
            with self.assertRaises(ValueError):self.skill.read_regular_text(p)
            p.write_bytes(b'line\r\n')
            self.assertEqual(self.skill.read_regular_text(p),'line\n')
            link=Path(tmp)/'link'
            try:link.symlink_to(p)
            except (OSError,NotImplementedError):self.skipTest('symlink unsupported')
            with self.assertRaises(ValueError):self.skill.read_regular_text(link)

    def test_cli_cleanup_state_and_broken_stdout(self):
        import warnings
        for broken in (False,True):
            with self.subTest(broken=broken), tempfile.TemporaryDirectory() as tmp:
                inp=Path(tmp)/'in';out=Path(tmp)/'out';inp.write_bytes(frames('private-fixture')[0])
                stdout=io.StringIO()
                with contextlib.ExitStack() as stack:
                    stack.enter_context(mock.patch.object(sys,'argv',['verify_report',str(inp),'--output',str(out)]))
                    stack.enter_context(contextlib.redirect_stdout(stdout))
                    stack.enter_context(warnings.catch_warnings());warnings.simplefilter('error')
                    stack.enter_context(mock.patch.object(self.report.os,'unlink',side_effect=OSError('cleanup denied')))
                    if broken:stack.enter_context(mock.patch('builtins.print',side_effect=BrokenPipeError('output closed')))
                    self.assertEqual(self.report.main(),1 if broken else 0)
                self.assertEqual(out.read_text(),'private-fixture')
                if not broken:
                    state=json.loads(stdout.getvalue())['output_state']
                    self.assertTrue(state['published']);self.assertEqual(state['cleanup_error'],'cleanup denied')

    def test_published_diagnostic_error_on_stderr_or_both_closed(self):
        class BrokenStream(io.StringIO):
            def write(self, text): raise BrokenPipeError('stream closed')
        for stderr_broken in (False, True):
            with self.subTest(stderr_broken=stderr_broken), tempfile.TemporaryDirectory() as tmp:
                inp=Path(tmp)/'in';out=Path(tmp)/'out';inp.write_bytes(frames('private-fixture')[0])
                stderr=BrokenStream() if stderr_broken else io.StringIO()
                with mock.patch.object(sys,'argv',['verify_report',str(inp),'--output',str(out)]),contextlib.redirect_stdout(BrokenStream()),contextlib.redirect_stderr(stderr):
                    self.assertEqual(self.report.main(),1)
                self.assertEqual(out.read_text(),'private-fixture')
                if not stderr_broken:
                    result=json.loads(stderr.getvalue())
                    self.assertEqual(result['status'],'published_diagnostic_error')
                    self.assertTrue(result['output_state']['published'])
                    self.assertEqual(result['output_state']['path'],str(out))
                    self.assertIn('stream closed',result['error'])
                    self.assertNotIn('private-fixture',stderr.getvalue())

    def test_cli_reports_output_state_without_raw(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp=Path(tmp)/'in'; out=Path(tmp)/'out'; inp.write_bytes(frames('secret-fixture')[0])
            stdout=io.StringIO()
            with mock.patch.object(sys,'argv',['verify_report',str(inp),'--output',str(out)]),contextlib.redirect_stdout(stdout):
                self.assertEqual(self.report.main(),0)
            result=json.loads(stdout.getvalue())
            self.assertEqual(result['status'],'verified_copy');self.assertTrue(result['output_state']['published'])
            self.assertIsNone(result['output_state']['cleanup_error'])
            self.assertNotIn('secret-fixture',stdout.getvalue());self.assertEqual(out.read_text(),'secret-fixture')

if __name__ == '__main__': unittest.main()
