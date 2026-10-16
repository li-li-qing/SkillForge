"""The installer protects current files; it never assumes the upload is still current."""
from pathlib import Path
import hashlib
import importlib.util
import json
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
        target=self.root/'README.md';target.unlink();outside=self.base/'outside';outside.write_bytes(b'old');target.symlink_to(outside)
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

if __name__=='__main__':unittest.main()
