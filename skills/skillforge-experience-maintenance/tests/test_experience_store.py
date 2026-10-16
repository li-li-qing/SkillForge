"""Local file transaction tests. Semantic review and model behavior are out of scope."""
from pathlib import Path
import importlib.util
import json
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
        target=self.root/self.target;target.unlink();target.symlink_to(outside)
        with self.assertRaises(self.m.StoreError): self.proposal()
        self.assertEqual(outside.read_text(),'outside')

    def test_empty_evidence_rejected(self):
        with self.assertRaises(self.m.StoreError):
            self.m.propose(self.root,self.target,'new',actor='tester',kind='technical',evidence=[],conditions='x')

    def test_invalid_record_identifier_rejected(self):
        with self.assertRaises(self.m.StoreError): self.m.promote(self.root,'../escape',reviewed=True)

    def test_private_store_symlink_rejected(self):
        external=self.root/'external';external.mkdir()
        (self.root/'.skillforge-memory').symlink_to(external,target_is_directory=True)
        with self.assertRaises(self.m.StoreError): self.proposal()

    def test_oversized_base_is_rejected_before_recording(self):
        (self.root/self.target).write_text('x'*(self.m.MAX_CONTENT+1))
        with self.assertRaises(self.m.StoreError): self.proposal()

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
