"""The installer protects current files; it never assumes the upload is still current."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest

TOOL=Path(__file__).resolve().parents[1]/'scripts/apply_skillforge_update.py'
def sha(data): return hashlib.sha256(data).hexdigest()

class PatchInstallerTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(TOOL.is_file(),'Guarded patch installer missing')
        spec=importlib.util.spec_from_file_location('patch_installer',TOOL)
        self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.root=self.base/'root';self.package=self.base/'package'
        self.root.mkdir();(self.package/'payload').mkdir(parents=True)
        (self.root/'README.md').write_bytes(b'old')
        (self.package/'payload/README.md').write_bytes(b'new')
        self.entries=[dict(path='README.md',before=sha(b'old'),after=sha(b'new'),operation='modify')]
        self.manifest()
    def manifest(self,retire=None):
        (self.package/'manifest.json').write_text(json.dumps(dict(schema_version=1,entries=self.entries,retire_dirs=retire or [])))
    def run_update(self,apply=False):return self.m.apply_update(self.root,self.package,apply=apply)
    def test_dry_run_does_not_change_any_root_files(self):
        result=self.run_update();self.assertEqual(result['status'],'checked')
        self.assertEqual((self.root/'README.md').read_bytes(),b'old')
        self.assertEqual([p.name for p in self.root.iterdir()],['README.md'])
    def test_apply_and_backup(self):
        result=self.run_update(True);self.assertEqual(result['status'],'applied')
        self.assertEqual((self.root/'README.md').read_bytes(),b'new')
        self.assertEqual((Path(result['backup'])/'files/README.md').read_bytes(),b'old')
    def test_current_file_conflict_stops_all_writes(self):
        (self.root/'README.md').write_bytes(b'other agent')
        with self.assertRaises(self.m.PatchError):self.run_update(True)
        self.assertEqual((self.root/'README.md').read_bytes(),b'other agent')
    def test_corrupt_payload_rejected(self):
        (self.package/'payload/README.md').write_bytes(b'corrupt')
        with self.assertRaises(self.m.PatchError):self.run_update(True)
        self.assertEqual((self.root/'README.md').read_bytes(),b'old')
    def test_repeat_apply_is_idempotent(self):
        self.run_update(True);result=self.run_update(True)
        self.assertEqual(result['status'],'already_current')
    def test_path_escape_rejected(self):
        self.entries[0]['path']='../escape.md';self.manifest()
        with self.assertRaises(self.m.PatchError):self.run_update()
    def test_target_symlink_rejected(self):
        target=self.root/'README.md';target.unlink();outside=self.base/'outside';outside.write_bytes(b'old')
        try: target.symlink_to(outside)
        except OSError as exc:
            if getattr(exc,'winerror',None)==1314: self.skipTest('Windows symlink privilege unavailable; junction case runs separately')
            raise
        with self.assertRaises(self.m.PatchError):self.run_update(True)
        self.assertEqual(outside.read_bytes(),b'old')
    def test_new_file_conflict_rejected(self):
        self.entries[0].update(operation='add',before=None);self.manifest()
        with self.assertRaises(self.m.PatchError):self.run_update(True)
    def test_delete_and_retire_only_known_empty_dirs(self):
        p=self.root/'skills/skillforge-orchestrator/generated/a.json';p.parent.mkdir(parents=True);p.write_bytes(b'old-index')
        self.entries.append(dict(path=p.relative_to(self.root).as_posix(),before=sha(b'old-index'),after=None,operation='delete'))
        self.manifest(['skills/skillforge-orchestrator/generated']);self.run_update(True)
        self.assertFalse(p.parent.exists())
    def test_unknown_file_in_retired_directory_is_preserved(self):
        p=self.root/'skills/skillforge-orchestrator/generated/new.json';p.parent.mkdir(parents=True);p.write_bytes(b'other')
        self.manifest(['skills/skillforge-orchestrator/generated'])
        with self.assertRaises(self.m.PatchError):self.run_update(True)
        self.assertEqual(p.read_bytes(),b'other');self.assertEqual((self.root/'README.md').read_bytes(),b'old')
    def test_busy_shared_rule_lock_does_not_overwrite(self):
        d=self.root/'.skillforge-memory';d.mkdir();(d/'write.lock').write_text('other writer')
        with self.assertRaises(self.m.PatchError):self.run_update(True)
        self.assertEqual((d/'write.lock').read_text(),'other writer')
        self.assertEqual((self.root/'README.md').read_bytes(),b'old')
    def test_git_is_never_a_manifest_target(self):
        self.entries[0]['path']='.git/config';self.manifest()
        with self.assertRaises(self.m.PatchError):self.run_update()

    def test_empty_manifest_path_refused_cleanly(self):
        self.entries[0]['path']='';self.manifest()
        with self.assertRaises(self.m.PatchError):self.run_update()

    def test_embedded_drive_and_ads_refused_by_safe(self):
        for name in ('skills/example/references/D:escape.md','README.md:stream'):
            with self.subTest(name=name):
                with self.assertRaises(self.m.PatchError):self.m.safe(self.root,name)

    def test_dot_manifest_path_refused_without_traceback(self):
        import contextlib
        import io
        self.entries[0]['path']='.';self.manifest()
        error=io.StringIO()
        with contextlib.redirect_stderr(error):
            result=self.m.main(['--root',str(self.root),'--package',str(self.package),'--apply'])
        self.assertEqual(result,2)
        self.assertIn('REFUSED:',error.getvalue())
        self.assertNotIn('Traceback',error.getvalue())
        self.assertEqual((self.root/'README.md').read_bytes(),b'old')

    def test_retire_add_conflict_refused_before_any_write(self):
        name='skills/skillforge-orchestrator/agents/new.md'
        payload=self.package/'payload'/name;payload.parent.mkdir(parents=True);payload.write_bytes(b'new')
        self.entries.append(dict(path=name,before=None,after=sha(b'new'),operation='add'))
        self.manifest(['skills/skillforge-orchestrator/agents'])
        for apply in (False,True):
            with self.assertRaises(self.m.PatchError):self.run_update(apply)
        self.assertFalse((self.root/name).exists())
        self.assertEqual((self.root/'README.md').read_bytes(),b'old')
        self.assertFalse((self.root/'.skillforge-backups').exists())

    def test_case_alias_refused_before_any_write(self):
        upper=self.root/'skills/example/references/A.md';upper.parent.mkdir(parents=True);upper.write_bytes(b'alias')
        lower=upper.with_name('a.md')
        if not lower.exists() or not upper.samefile(lower):self.skipTest('case-sensitive filesystem')
        self.entries.extend(dict(path=p.relative_to(self.root).as_posix(),before=sha(b'alias'),after=None,operation='delete') for p in (upper,lower))
        self.manifest()
        for apply in (False,True):
            with self.assertRaises(self.m.PatchError):self.run_update(apply)
        self.assertEqual(upper.read_bytes(),b'alias')
        self.assertEqual((self.root/'README.md').read_bytes(),b'old')

    def test_win32_alias_spelling_refused_before_any_write(self):
        for name in ('scripts/new.py.','scripts/new.py ',
                     'skills/skillforge-orchestrator/agents./new.md'):
            with self.subTest(name=name):
                payload=self.package/'payload'/name;payload.parent.mkdir(parents=True,exist_ok=True);payload.write_bytes(b'new')
                self.entries=self.entries[:1]+[dict(path=name,before=None,after=sha(b'new'),operation='add')]
                self.manifest(['skills/skillforge-orchestrator/agents'] if 'agents.' in name else [])
                for apply in (False,True):
                    with self.assertRaises(self.m.PatchError):self.run_update(apply)
                self.assertEqual((self.root/'README.md').read_bytes(),b'old')
                self.assertFalse((self.root/'.skillforge-backups').exists())

    def test_junction_in_protected_paths_refused(self):
        if os.name != 'nt': self.skipTest('Windows junction fixture')
        for name in ('skills','.skillforge-memory','.skillforge-backups'):
            with self.subTest(name=name):
                outside=self.base/('outside-'+name);outside.mkdir()
                marker=outside/'marker';marker.write_bytes(b'unchanged')
                link=self.root/name
                for path in (link,outside):
                    self.assertTrue(path.resolve().is_relative_to(self.base.resolve()))
                script="New-Item -ItemType Junction -Path '"+str(link)+"' -Target '"+str(outside)+"' -ErrorAction Stop | Out-Null"
                subprocess.run(['powershell.exe','-NoProfile','-Command',script],check=True,capture_output=True)
                try:
                    with self.assertRaises(self.m.PatchError):self.m.safe(self.root,name+'/marker')
                    self.assertEqual(marker.read_bytes(),b'unchanged')
                finally:link.rmdir()

    def test_windows_device_names_rejected_on_every_host(self):
        for name in ("scripts/CON.txt", "scripts/nul.py", "docs/COM1.md",
                     "docs/LPT9.txt", "docs/COM¹.txt", "docs/bad?.md", "docs/a\x01.md"):
            with self.subTest(name=name):
                with self.assertRaises(self.m.PatchError):self.m.safe(self.root,name)

    def test_journal_failure_reports_changed_target_and_blocks_retry(self):
        from unittest.mock import patch
        original=self.m.atomic_write
        state_writes=[0]
        def faulty(path,data,mode=None):
            if path.name=="state.json":
                state_writes[0]+=1
                if state_writes[0]>=2:raise OSError("injected state disk failure")
            return original(path,data,mode)
        with patch.object(self.m,"atomic_write",side_effect=faulty):
            with self.assertRaises(self.m.PatchError) as caught:self.run_update(True)
        self.assertEqual((self.root/"README.md").read_bytes(),b"new")
        self.assertIn("backup",str(caught.exception).lower())
        self.assertTrue(caught.exception.details["mutation_attempted"])
        self.assertEqual(caught.exception.details["verified_paths"],["README.md"])
        self.assertFalse(caught.exception.details["journal_persisted"])
        with self.assertRaises(self.m.PatchError):self.run_update(True)

    def test_pending_journal_checked_before_already_current(self):
        self.run_update(True)
        state=next((self.root/".skillforge-backups").glob("*/state.json"))
        data=json.loads(state.read_text());data["status"]="prepared";state.write_text(json.dumps(data))
        with self.assertRaises(self.m.PatchError):self.run_update(True)

    def test_initial_journal_failure_has_no_target_mutation(self):
        from unittest.mock import patch
        original=self.m.atomic_write
        def faulty(path,data,mode=None):
            if path.name=="state.json":raise OSError("initial state failure")
            return original(path,data,mode)
        with patch.object(self.m,"atomic_write",side_effect=faulty):
            with self.assertRaises(self.m.PatchError) as caught:self.run_update(True)
        self.assertEqual((self.root/"README.md").read_bytes(),b"old")
        self.assertFalse(caught.exception.details["mutation_attempted"])
        with self.assertRaises(self.m.PatchError):self.run_update(True)

    def test_committed_lock_cleanup_failure_preserves_applied(self):
        from unittest.mock import patch
        unlink = Path.unlink
        def faulty(path,*args,**kwargs):
            if path.name == "write.lock": raise OSError("lock cleanup failed")
            return unlink(path,*args,**kwargs)
        with patch.object(Path,"unlink",faulty):
            with self.assertRaises(self.m.PatchIncompleteError) as caught:self.run_update(True)
        details=caught.exception.details
        self.assertEqual(details["status"],"cleanup_required")
        self.assertEqual(details["transaction_status"],"applied")
        state=next((self.root/".skillforge-backups").glob("*/state.json"))
        self.assertEqual(json.loads(state.read_text())["status"],"applied")
        self.assertEqual((self.root/"README.md").read_bytes(),b"new")
        self.assertTrue((self.root/".skillforge-memory/write.lock").exists())
        self.assertEqual(self.m.inspect_pending_updates(self.root),[])

    def test_primary_failure_survives_lock_cleanup_failure(self):
        from unittest.mock import patch
        unlink=Path.unlink;write=self.m.atomic_write
        def failed_write(path,data,mode=None):
            if path == self.root/"README.md":raise OSError("primary target failure")
            return write(path,data,mode)
        def failed_cleanup(path,*args,**kwargs):
            if path.name=="write.lock":raise OSError("secondary cleanup failure")
            return unlink(path,*args,**kwargs)
        with patch.object(Path,"unlink",failed_cleanup),patch.object(self.m,"atomic_write",side_effect=failed_write):
            with self.assertRaises(self.m.PatchIncompleteError) as caught:self.run_update(True)
        self.assertIn("primary target failure",caught.exception.details["error"])
        self.assertIn("secondary cleanup failure",caught.exception.details["error"])
        self.assertEqual((self.root/"README.md").read_bytes(),b"old")

if __name__=='__main__':unittest.main()
