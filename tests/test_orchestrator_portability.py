from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills' / 'skillforge-orchestrator'

class OrchestratorPortabilityTests(unittest.TestCase):
    def runtime_text(self):
        parts=[]
        for p in SKILL.rglob('*'):
            if p.is_file() and p.suffix.lower() in {'.md','.yaml','.yml','.json','.txt'}:
                parts.append(p.read_text(encoding='utf-8'))
        return '\n'.join(parts)

    def test_runtime_has_only_portable_surface(self):
        forbidden={'agents','generated','evals','tests','scripts','development','adapters'}
        found={p.name for p in SKILL.iterdir() if p.is_dir()}
        self.assertFalse(found & forbidden, f'non-runtime directories leaked into portable core: {sorted(found & forbidden)}')

    def test_frontmatter_is_minimal(self):
        text=(SKILL/'SKILL.md').read_text(encoding='utf-8')
        self.assertTrue(text.startswith('---\n'))
        header=text.split('---\n',2)[1]
        keys=[]
        for line in header.splitlines():
            m=re.match(r'^([A-Za-z0-9_-]+):',line)
            if m:
                keys.append(m.group(1))
        self.assertEqual(keys,['name','description'])

    def test_runtime_does_not_name_specific_hosts(self):
        text=self.runtime_text().lower()
        for token in ['codex','claude','openai','qoder','zcode','workbuddy']:
            self.assertNotIn(token,text)

    def test_runtime_has_no_fixed_leaf_skill_catalog(self):
        text=self.runtime_text().lower()
        for token in [
            'skillforge-mfc','skillforge-debugging','skillforge-ui-design',
            'skillforge-ue-cpp','skillforge-ue-blueprint','skillforge-lgf',
            'skillforge-archerage-addon'
        ]:
            self.assertNotIn(token,text)

    def test_capability_contract_exists(self):
        p=SKILL/'references'/'capability-contract.md'
        self.assertTrue(p.is_file())
        text=p.read_text(encoding='utf-8')
        for field in ['skill_discovery','skill_loading','context_meter','context_compaction','file_read','file_write','command_execution','artifact_delivery']:
            self.assertIn(field,text)

if __name__=='__main__':
    unittest.main()
