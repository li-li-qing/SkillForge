"""Local file transaction tests. Semantic review and model behavior are out of scope."""
from pathlib import Path
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest

TOOL=Path(__file__).resolve().parents[1]/'scripts/experience_store.py'

class ExperienceStoreTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(TOOL.is_file(),'Experience store implementation missing')
        spec=importlib.util.spec_from_file_location('experience_store',TOOL)
        self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.target='skills/example/references/rule.md'
        p=self.root/self.target;p.parent.mkdir(parents=True);p.write_text('old',encoding='utf-8')

    def proposal(self, content='new', target=None):
        return self.m.propose(self.root,target or self.target,content,actor='tester',kind='technical',evidence=['test:evidence'],conditions='local fixture')

    def symlink(self, link, target, **kwargs):
        try: link.symlink_to(target, **kwargs)
        except OSError as exc:
            if getattr(exc,'winerror',None)==1314: self.skipTest('Windows symlink privilege unavailable; junction cases run separately')
            raise

    def test_proposal_does_not_change_rule(self):
        i=self.proposal();self.assertTrue(i)
        self.assertEqual((self.root/self.target).read_text(),'old')

    def test_promotion_requires_semantic_review(self):
        i=self.proposal()
        with self.assertRaises(self.m.StoreError): self.m.promote(self.root,i,reviewed=False)
        self.assertEqual((self.root/self.target).read_text(),'old')

    def test_reviewed_matching_base_can_promote(self):
        i=self.proposal();r=self.m.promote(self.root,i,reviewed=True)
        self.assertEqual(r['status'],'committed')
        self.assertEqual((self.root/self.target).read_text(),'new')

    def test_stale_proposal_cannot_overwrite_newer_content(self):
        a=self.proposal('first');b=self.proposal('second')
        self.m.promote(self.root,a,reviewed=True)
        with self.assertRaises(self.m.StoreError): self.m.promote(self.root,b,reviewed=True)
        self.assertEqual((self.root/self.target).read_text(),'first')

    def test_busy_lock_does_not_wait_or_steal(self):
        i=self.proposal();lock=self.root/'.skillforge-memory/write.lock';lock.write_text('other')
        with self.assertRaises(self.m.StoreError): self.m.promote(self.root,i,reviewed=True)
        self.assertEqual(lock.read_text(),'other')

    def test_idempotent_promotion_is_not_duplicate_write(self):
        i=self.proposal();self.m.promote(self.root,i,reviewed=True)
        r=self.m.promote(self.root,i,reviewed=True);self.assertEqual(r['status'],'already_committed')

    def test_rollback_checks_current_hash(self):
        i=self.proposal();self.m.promote(self.root,i,reviewed=True)
        (self.root/self.target).write_text('someone else')
        with self.assertRaises(self.m.StoreError): self.m.rollback(self.root,i,reviewed=True)
        self.assertEqual((self.root/self.target).read_text(),'someone else')

    def test_rollback_restores_only_own_revision(self):
        i=self.proposal();self.m.promote(self.root,i,reviewed=True)
        self.m.rollback(self.root,i,reviewed=True)
        self.assertEqual((self.root/self.target).read_text(),'old')

    def test_new_target_can_be_rolled_back(self):
        target='skills/example/references/new.md';i=self.proposal(target=target)
        self.m.promote(self.root,i,reviewed=True);self.assertTrue((self.root/target).exists())
        self.m.rollback(self.root,i,reviewed=True);self.assertFalse((self.root/target).exists())

    def test_traversal_and_non_rule_target_rejected(self):
        for target in ['../escape.md','/tmp/escape.md','skills/example/../../escape.md','skills/example/scripts/x.py','.git/config']:
            with self.subTest(target=target):
                with self.assertRaises(self.m.StoreError): self.proposal(target=target)

    def test_symlink_target_rejected(self):
        outside=self.root/'outside';outside.write_text('outside')
        target=self.root/self.target;target.unlink();self.symlink(target,outside)
        with self.assertRaises(self.m.StoreError): self.proposal()
        self.assertEqual(outside.read_text(),'outside')

    def test_empty_evidence_rejected(self):
        with self.assertRaises(self.m.StoreError):
            self.m.propose(self.root,self.target,'new',actor='tester',kind='technical',evidence=[],conditions='x')

    def test_invalid_record_identifier_rejected(self):
        with self.assertRaises(self.m.StoreError): self.m.promote(self.root,'../escape',reviewed=True)

    def test_private_store_symlink_rejected(self):
        external=self.root/'external';external.mkdir()
        self.symlink(self.root/'.skillforge-memory',external,target_is_directory=True)
        with self.assertRaises(self.m.StoreError): self.proposal()

    def test_embedded_drive_and_ads_are_refused_before_recording(self):
        for target in ('skills/example/references/D:escape.md',
                       'skills/example/references/rule.md:stream'):
            with self.subTest(target=target):
                with self.assertRaises(self.m.StoreError): self.proposal(target=target)
        self.assertFalse((self.root/'.skillforge-memory').exists())
        self.assertEqual((self.root/self.target).read_text(), 'old')

    def junction(self, link, target):
        if os.name != 'nt': self.skipTest('Windows junction fixture')
        for path in (link, target):
            self.assertTrue(path.resolve().is_relative_to(self.root.resolve()))
        script = "New-Item -ItemType Junction -Path '"+str(link)+"' -Target '"+str(target)+"' -ErrorAction Stop | Out-Null"
        subprocess.run(['powershell.exe','-NoProfile','-Command',script],check=True,capture_output=True)
        self.addCleanup(lambda: link.rmdir() if link.is_junction() else None)

    def test_junction_target_is_refused_without_external_write(self):
        outside=self.root/'outside';outside.mkdir();marker=outside/'rule.md';marker.write_text('outside')
        link=self.root/'skills/example/assets';self.junction(link,outside)
        with self.assertRaises(self.m.StoreError): self.proposal(target='skills/example/assets/rule.md')
        self.assertEqual(marker.read_text(),'outside')

    def test_junction_private_store_is_refused_before_recording(self):
        outside=self.root/'outside';outside.mkdir()
        self.junction(self.root/'.skillforge-memory',outside)
        with self.assertRaises(self.m.StoreError): self.proposal()
        self.assertEqual(list(outside.iterdir()),[])

    def test_junction_proposals_and_transactions_are_refused(self):
        for name in ('proposals','transactions'):
            with self.subTest(name=name):
                store=self.root/'.skillforge-memory';store.mkdir(exist_ok=True)
                outside=self.root/('outside-'+name);outside.mkdir()
                link=store/name;self.junction(link,outside)
                try:
                    with self.assertRaises(self.m.StoreError): self.proposal()
                    self.assertEqual(list(outside.iterdir()),[])
                finally:
                    link.rmdir()

    def test_oversized_base_is_rejected_before_recording(self):
        (self.root/self.target).write_text('x'*(self.m.MAX_CONTENT+1))
        with self.assertRaises(self.m.StoreError): self.proposal()

    def test_escaped_record_size_refused_before_proposal_write(self):
        text='"\\'*(self.m.MAX_CONTENT//2)
        (self.root/self.target).write_text(text,encoding='utf-8')
        with self.assertRaises(self.m.StoreError): self.proposal(text)
        self.assertEqual(list((self.root/'.skillforge-memory/proposals').glob('*.json')),[])
        self.assertEqual((self.root/self.target).read_text(encoding='utf-8'),text)

    def test_large_metadata_is_refused_before_proposal_write(self):
        with self.assertRaises(self.m.StoreError):
            self.m.propose(self.root,self.target,'small',actor='test',kind='technical',
                           evidence=['x'*(4*self.m.MAX_CONTENT)],conditions='fixture')
        self.assertEqual((self.root/self.target).read_text(),'old')
        self.assertEqual(list((self.root/'.skillforge-memory/proposals').glob('*.json')),[])

    def test_near_limit_escaped_record_can_promote_and_rollback(self):
        text='"\\'*(self.m.MAX_CONTENT//2-1024)
        (self.root/self.target).write_text(text,encoding='utf-8')
        identifier=self.proposal(text[:-2]+'ok')
        self.assertEqual(self.m.promote(self.root,identifier,reviewed=True)['status'],'committed')
        self.assertEqual(self.m.rollback(self.root,identifier,reviewed=True)['status'],'rolled_back')
        self.assertEqual((self.root/self.target).read_text(encoding='utf-8'),text)

    def test_legacy_record_capacity_refused_before_rollback_mutation(self):
        identifier=self.proposal('new');self.m.promote(self.root,identifier,reviewed=True)
        journal=self.root/'.skillforge-memory/transactions'/f'{identifier}.json'
        record=json.loads(journal.read_text(encoding='utf-8'))
        # The previous schema-v1 tool could generate readable committed records
        # this close to the limit. Preserve their evidence instead of truncating it.
        record['conditions']=''
        encode=lambda value:(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
        record['conditions']='x'*(self.m.MAX_RECORD_BYTES-80-len(encode(record)))
        before=encode(record);journal.write_bytes(before)
        self.assertLessEqual(len(before),self.m.MAX_RECORD_BYTES)
        with self.assertRaises(self.m.StoreError):self.m.rollback(self.root,identifier,reviewed=True)
        self.assertEqual((self.root/self.target).read_text(),'new')
        self.assertEqual(journal.read_bytes(),before)

    def test_windows_alias_component_refused_before_recording(self):
        for target in ('skills/example/references/group./rule.md','skills/example/assets/group /rule.md'):
            with self.subTest(target=target):
                with self.assertRaises(self.m.StoreError):self.proposal(target=target)
        self.assertFalse((self.root/'.skillforge-memory').exists())

    def rewrite_transaction(self, identifier, status):
        p=self.root/'.skillforge-memory/transactions'/f'{identifier}.json'
        d=json.loads(p.read_text());d['status']=status;p.write_text(json.dumps(d));return p

    def test_recover_after_write_finalizes_without_modifying_rule(self):
        i=self.proposal();self.m.promote(self.root,i,reviewed=True);self.rewrite_transaction(i,'prepared')
        r=self.m.recover(self.root,i);self.assertEqual(r['status'],'committed');self.assertFalse(r['rule_modified'])
        self.assertEqual((self.root/self.target).read_text(),'new')

    def test_recover_before_write_marks_aborted(self):
        i=self.proposal();self.m.promote(self.root,i,reviewed=True);self.rewrite_transaction(i,'prepared')
        (self.root/self.target).write_text('old')
        self.assertEqual(self.m.recover(self.root,i)['status'],'aborted')

    def test_recover_does_not_guess_after_unrelated_edit(self):
        i=self.proposal();self.m.promote(self.root,i,reviewed=True);self.rewrite_transaction(i,'prepared')
        (self.root/self.target).write_text('unrelated')
        with self.assertRaises(self.m.StoreError):self.m.recover(self.root,i)
        self.assertEqual((self.root/self.target).read_text(),'unrelated')

    def test_pending_transaction_blocks_new_promotion(self):
        i=self.proposal();self.m.promote(self.root,i,reviewed=True);self.rewrite_transaction(i,'prepared')
        b=self.proposal('next')
        with self.assertRaises(self.m.StoreError):self.m.promote(self.root,b,reviewed=True)
        self.assertEqual((self.root/self.target).read_text(),'new')

    def test_two_processes_cannot_both_commit_the_same_base(self):
        import subprocess
        import sys
        a=self.proposal('first');b=self.proposal('second')
        commands=[[sys.executable,'-B',str(TOOL),'--root',str(self.root),'promote',i,'--reviewed'] for i in (a,b)]
        children=[subprocess.Popen(c,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for c in commands]
        outputs=[c.communicate(timeout=10) for c in children]
        self.assertEqual(sorted(c.returncode for c in children),[0,2],outputs)
        self.assertIn((self.root/self.target).read_text(),['first','second'])

if __name__=='__main__': unittest.main()
