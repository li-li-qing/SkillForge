"""Structural checks for the Qt skill package; these do not evaluate agent behavior."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills' / 'skillforge-qt'

class QtPackageTests(unittest.TestCase):
    def require_file(self, name):
        path = SKILL / name
        self.assertTrue(path.is_file(), f'Missing Qt runtime resource: {name}')
        return path

    def test_entry_is_small_and_named(self):
        text = self.require_file('SKILL.md').read_text(encoding='utf-8')
        self.assertRegex(text, r'(?m)^name: skillforge-qt$')
        self.assertLess(len(text.encode('utf-8')), 11000)
        self.assertLess(len(text.splitlines()), 150)

    def test_runtime_topics_are_present(self):
        for name in ['project-profile', 'architecture-commands', 'widgets-layout-input-dpi',
                     'model-view-performance', 'qobject-threading-shutdown', 'windows-com-dmsoft',
                     'mfc-migration', 'testing-build-deployment', 'qml-quick-boundary', 'github-sources']:
            with self.subTest(topic=name):
                self.require_file(f'references/{name}.md')
        self.require_file('assets/project-profile.md')
        self.require_file('assets/review-handoff.md')

    def test_sources_have_immutable_revisions_and_review_ranges(self):
        data = json.loads(self.require_file('references/source-manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(data['schema_version'], 1)
        self.assertFalse(data['whole_repository_review'])
        projects = data['projects']
        self.assertEqual(len({p['repository'] for p in projects}), 6)
        for p in projects:
            with self.subTest(repository=p['repository']):
                self.assertRegex(p['commit'], r'^[0-9a-f]{40}$')
                self.assertIn(p['classification'], ['Current', 'Stable-but-old', 'Historical', 'Reject'])
                self.assertTrue(p['not_adopted'])
                self.assertTrue(p['files'])
                for f in p['files']:
                    self.assertRegex(f['blob_sha'], r'^[0-9a-f]{40}$')
                    self.assertTrue(f['url'].startswith('https://github.com/'+p['repository']+'/blob/'+p['commit']+'/'))
                    self.assertTrue(f['read_ranges'])
                    for start, end in f['read_ranges']:
                        self.assertGreaterEqual(start, 1)
                        self.assertGreaterEqual(end, start)

    def test_evaluation_cases_are_unique_and_have_rubrics(self):
        triggers = json.loads(self.require_file('evals/trigger-cases.json').read_text(encoding='utf-8'))
        behavior = json.loads(self.require_file('evals/behavior-cases.json').read_text(encoding='utf-8'))
        self.assertGreaterEqual(len(triggers), 12)
        self.assertGreaterEqual(len(behavior), 18)
        ids = [c['id'] for c in triggers + behavior]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual({c['expected'] for c in triggers}, {'trigger', 'no_trigger', 'conditional'})
        for c in behavior:
            self.assertTrue(c['prompt'])
            self.assertGreaterEqual(len(c['expectations']), 3)

    def test_templates_do_not_fill_unknown_project_facts(self):
        text = self.require_file('assets/project-profile.md').read_text(encoding='utf-8')
        for field in ['qt_version: unknown', 'architecture: unknown', 'compiler: unknown',
                      'ui_stack: unknown', 'cpp_standard: unknown']:
            self.assertIn(field, text)

    def test_runtime_has_no_parent_relative_links(self):
        self.require_file('SKILL.md')
        for path in SKILL.rglob('*.md'):
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
                if '://' in target or target.startswith('#'):
                    continue
                resolved = (path.parent / target.split('#', 1)[0]).resolve()
                self.assertTrue(resolved.is_relative_to(SKILL.resolve()), f'Runtime dependency escapes skill: {path}: {target}')

if __name__ == '__main__':
    unittest.main()
