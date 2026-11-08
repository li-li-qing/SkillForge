"""Real updater interruption must not be compounded by experience promotion."""
from pathlib import Path
import hashlib
import importlib.util
import json
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

class TransactionInteropTests(unittest.TestCase):
    def test_partial_updater_blocks_same_rule_but_not_unrelated_rule(self):
        updater=load('interop_updater',ROOT/'scripts/apply_skillforge_update.py')
        memory=load('interop_memory',ROOT/'skills/skillforge-experience-maintenance/scripts/experience_store.py')
        with tempfile.TemporaryDirectory() as temporary:
            base=Path(temporary);root=base/'root';package=base/'package'
            target='skills/example/references/rule.md'
            path=root/target;path.parent.mkdir(parents=True);path.write_bytes(b'old')
            payload=package/'payload'/target;payload.parent.mkdir(parents=True);payload.write_bytes(b'new')
            sha=lambda value:hashlib.sha256(value).hexdigest()
            (package/'manifest.json').write_text(json.dumps(dict(schema_version=1,entries=[
                dict(path=target,before=sha(b'old'),after=sha(b'new'),operation='modify')],retire_dirs=[])))
            original=updater.atomic_write
            def fault(path,data,*args,**kwargs):
                if path.name=='state.json' and json.loads(data).get('status')=='applied':
                    raise OSError('injected final journal error')
                return original(path,data,*args,**kwargs)
            with patch.object(updater,'atomic_write',side_effect=fault):
                with self.assertRaises(updater.PatchError):
                    updater.apply_update(root,package,apply=True)
            self.assertEqual(path.read_bytes(),b'new')
            proposal=memory.propose(root,target,'newer',actor='test',kind='technical',evidence=['test'],conditions='fixture')
            with self.assertRaisesRegex(memory.StoreError,'overlaps'):
                memory.promote(root,proposal,reviewed=True)
            self.assertEqual(path.read_bytes(),b'new')
            self.assertEqual(updater.inspect_pending_updates(root)[0]['actual_targets'][0]['matches'],'after')
            other=memory.propose(root,'skills/other/SKILL.md','other',actor='test',kind='technical',evidence=['test'],conditions='fixture')
            self.assertEqual(memory.promote(root,other,reviewed=True)['status'],'committed')
