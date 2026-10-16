"""Static documentation contracts only; NOT model behavior evaluations."""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
O = ROOT / 'skills/skillforge-orchestrator'

class CollaborationContractTests(unittest.TestCase):
    def text(self, p):
        self.assertTrue(p.is_file(), f'Missing contract: {p.name}')
        return p.read_text(encoding='utf-8')

    def test_collaboration_levels_are_distinct_from_task_kind(self):
        t=self.text(O/'references/collaboration-policy.md')
        for word in ['A级', 'B级', 'task_kind', 'awaiting_mode', '同一任务', '未回复']:
            self.assertIn(word,t)

    def test_entry_does_not_retain_old_modes(self):
        t=self.text(O/'SKILL.md')
        for phrase in ['列计划推进', '分支 B（深入打磨需求）', '收敛后转入步骤 7', '默认一次确认']:
            self.assertNotIn(phrase,t)
        self.assertIn('collaboration-policy.md',t)

    def test_common_preparation_is_not_skipped(self):
        t=self.text(O/'SKILL.md')
        self.assertIn('共同准备',t)
        self.assertIn('task_kind',t)
        self.assertIn('个人习惯',t)

    def test_approval_not_a_second_prompt_gate(self):
        t=self.text(O/'references/approval-policy.md')
        self.assertIn('长提示词',t)
        self.assertIn('不是实施授权',t)
        self.assertNotIn('默认 `PREPARE`',t)

    def test_personal_habits_are_proactive_not_explicit_only(self):
        t=self.text(O/'references/user-workstyle.md')
        self.assertIn('主动提炼',t)
        self.assertIn('临时',t)
        self.assertIn('共同根因',t)
        self.assertNotIn('仅在用户授权“记入技能/更新习惯”后',t)

    def test_advisory_without_workspace_and_converges(self):
        t=self.text(O/'references/advisory-workflow.md')
        for phrase in ['没有工程', '一个', '共同准备', '不重复']:
            self.assertIn(phrase,t)
        self.assertNotIn('[B] 打磨需求',t)

    def test_checkpoint_retains_new_state(self):
        t=self.text(O/'assets/checkpoint.md')
        for word in ['collaboration_level', 'task_kind', '待决', '经验']:
            self.assertIn(word,t)

    def test_preflight_has_scale_and_exit_conditions(self):
        d=ROOT/'skills/skillforge-engineering-preflight'
        t=self.text(d/'SKILL.md')+self.text(d/'assets/probe-record.md')
        for word in ['规模', '退出', 'not_run', '可丢弃', '既定']:
            self.assertIn(word,t)

    def test_memory_has_conflict_and_noncooperating_limits(self):
        d=ROOT/'skills/skillforge-experience-maintenance'
        t=self.text(d/'references/concurrent-updates.md')
        for word in ['候选', '哈希', '锁', '非协作', '撤回', '未回复']:
            self.assertIn(word,t)

    def test_behavior_specs_exist_without_claiming_run(self):
        p=ROOT/'development/skillforge-orchestrator/evals/collaboration-cases.json'
        data=json.loads(self.text(p));self.assertGreaterEqual(len(data),16)
        self.assertEqual(len({x['id'] for x in data}),len(data))
        for x in data:
            self.assertTrue(x['prompt']);self.assertTrue(x['expectations'])
            self.assertEqual(x['execution_status'],'not_run')

if __name__=='__main__': unittest.main()
