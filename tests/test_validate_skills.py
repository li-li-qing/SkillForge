"""Exercise the public CLI with real temporary skill packages, not prose checks."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


VALIDATOR = Path(__file__).resolve().parents[1] / "scripts" / "validate_skills.py"


class ValidateSkillsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.skill = self.make_skill(self.root)

    def make_skill(self, parent, name="skillforge-example"):
        package = parent / name
        (package / "references").mkdir(parents=True)
        (package / "evals").mkdir()
        (package / "scripts").mkdir()
        (package / "fixtures").mkdir()
        (package / "SKILL.md").write_text(
            "---\nname: " + name + '\ndescription: "Use for an example task."\n---\n'
            "# Portable example\n\n"
            "Read [details](references/details.md#workflow).\n"
            "See [external](https://example.com/docs).\n"
            "Run `python scripts/check.py` if Python is available.\n",
            encoding="utf-8",
        )
        (package / "references" / "details.md").write_text(
            "# Workflow\n[fixture](../fixtures/sample.txt)\n"
            "[main][entry]\n\n[entry]: ../SKILL.md\n"
            "[fragment](#workflow)\n"
            "Unreal object paths such as `/Game/Examples/Map` are virtual assets.\n",
            encoding="utf-8",
        )
        (package / "scripts" / "check.py").write_text("print('ok')\n", encoding="utf-8")
        (package / "fixtures" / "sample.txt").write_text("sample\n", encoding="utf-8")
        self.write_json(package / "evals" / "trigger-cases.json", [
            {"id": "positive", "prompt": "Perform the example task.",
             "context": "A project is available.", "expected": "trigger",
             "reason": "The request is in scope."},
            {"id": "negative", "prompt": "Translate a sentence.",
             "context": {"project": "unrelated"}, "expected": "no_trigger",
             "reason": "The request is outside this skill."},
            {"id": "conditional", "prompt": "Help improve this.",
             "context": "The artifact type is unknown.", "expected": "conditional",
             "reason": "Need project evidence to select this skill."},
        ])
        self.write_json(package / "evals" / "behavior-cases.json", [
            {"id": "basic", "prompt": "Inspect the sample.",
             "expectations": ["Inspect the supplied fixture before proposing changes."],
             "fixtures": ["fixtures/sample.txt"]},
        ])
        return package

    @staticmethod
    def write_json(path, value):
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    def run_validator(self, *paths, flags=(), script=VALIDATOR, cwd=None):
        return subprocess.run(
            [sys.executable, str(script), *flags, *(str(path) for path in paths)],
            capture_output=True, text=True, encoding="utf-8", cwd=cwd or self.root,
            check=False,
        )

    def assert_invalid(self, *paths, flags=()):
        result = self.run_validator(*(paths or (self.skill,)), flags=flags)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("error", result.stdout.lower(), result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        return result

    def append(self, text, relative="SKILL.md"):
        path = self.skill / relative
        path.write_text(path.read_text(encoding="utf-8") + text + "\n", encoding="utf-8")

    def test_valid_portable_package_runs_from_unrelated_directory(self):
        result = self.run_validator(self.skill)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertRegex(result.stdout, r"1 skill.*0 error")

    def test_optional_quoted_metadata_is_portable(self):
        p = self.skill / "SKILL.md"
        text = p.read_text(encoding="utf-8")
        p.write_text(text.replace('\n---\n#', '\ncompatibility: "Python 3.10+"\nmetadata:\n  revision: "2026.09"\n---\n#'), encoding="utf-8")
        result = self.run_validator(self.skill, flags=("--self-contained",))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_bad_metadata_is_rejected(self):
        for extra in ('metadata:\n  revision: 123', 'metadata:\n  revision: "a"\n  revision: "b"', 'compatibility: 42', 'compatibility: ""'):
            with self.subTest(extra=extra):
                p = self.skill / "SKILL.md"
                p.write_text('---\nname: skillforge-example\ndescription: "Example."\n' + extra + '\n---\n# Body\n', encoding="utf-8")
                self.assert_invalid()

    def test_tools_suffix_in_filename_is_not_host_api(self):
        (self.skill / "references" / "verification-tools.md").write_text('# Tools\n', encoding="utf-8")
        self.append('[tools](references/verification-tools.md)')
        result = self.run_validator(self.skill)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_self_contained_copy_keeps_all_relative_resources_valid(self):
        result = self.run_validator(self.skill, flags=("--self-contained",))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertRegex(result.stdout, r"1.*standalone")

    def test_boundary_values_and_reordered_header_are_valid(self):
        package = self.make_skill(self.root / "boundary", name="a" * 64)
        header = '---\ndescription: ' + json.dumps("x" * 1024) + '\nname: ' + package.name + '\n---\n'
        (package / "SKILL.md").write_text(header + "body\n" * 496, encoding="utf-8")
        result = self.run_validator(package)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_default_scan_is_relative_to_script_not_working_directory(self):
        repository = self.root / "isolated-repository"
        script_directory = repository / "scripts"
        script_directory.mkdir(parents=True)
        self.assertTrue(VALIDATOR.is_file(), "The public validator CLI must exist")
        shutil.copy2(VALIDATOR, script_directory / VALIDATOR.name)
        self.make_skill(repository / "skills")
        result = self.run_validator(script=script_directory / VALIDATOR.name)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertRegex(result.stdout, r"1 skill.*0 error")

    def test_empty_default_scan_fails(self):
        repository = self.root / "empty-repository"
        scripts = repository / "scripts"
        scripts.mkdir(parents=True)
        self.assertTrue(VALIDATOR.is_file(), "The public validator CLI must exist")
        shutil.copy2(VALIDATOR, scripts / VALIDATOR.name)
        result = self.run_validator(script=scripts / VALIDATOR.name)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_missing_skill_directory_fails_without_traceback(self):
        self.assert_invalid(self.root / "missing")

    def test_rejects_malformed_or_unsupported_header(self):
        path = self.skill / "SKILL.md"
        bodies = [
            "# Missing header\n",
            '---\nname: skillforge-example\ndescription: "broken\n---\n',
            '---\nname: skillforge-example\ndescription: unquoted text\n---\n',
            '---\nname: skillforge-example\ndescription: |\n  multiline\n---\n',
            '---\nname: skillforge-example\nname: duplicate\ndescription: "x"\n---\n',
            '---\nname: skillforge-example\ndescription: "x"\nmetadata: {}\n---\n',
            '---\nname: "skillforge-example\ndescription: "x"\n---\n',
            '---\nname: skillforge-example\ndescription: "x"\n',
        ]
        for body in bodies:
            with self.subTest(body=body):
                path.write_text(body, encoding="utf-8")
                self.assert_invalid()

    def test_name_constraints_and_directory_match(self):
        path = self.skill / "SKILL.md"
        for name in ("BadName", "bad_name", "-bad", "bad-", "bad--name", "技能", "a" * 65,
                     "different-name", ""):
            with self.subTest(name=name):
                path.write_text('---\nname: ' + name + '\ndescription: "Task."\n---\n',
                                encoding="utf-8")
                self.assert_invalid()

    def test_yaml_ambiguous_names_require_quotes(self):
        for name in ("123", "null", "true", "false", "yes", "no", "on", "off", "y", "n",
                     "0xabc", "1e-3", "2001-01-01", "123-foo"):
            with self.subTest(name=name):
                package = self.make_skill(self.root / "plain", name=name)
                result = self.assert_invalid(package)
                self.assertIn("quote", result.stdout.lower())

    def test_json_quoted_names_allow_yaml_ambiguous_but_valid_skill_names(self):
        for name in ("123", "null", "true", "false", "yes", "no", "on", "off", "y", "n",
                     "0xabc", "1e-3", "2001-01-01", "123-foo", "skillforge-normal"):
            with self.subTest(name=name):
                package = self.make_skill(self.root / "quoted", name=name)
                (package / "SKILL.md").write_text(
                    '---\nname: ' + json.dumps(name) + '\ndescription: "Task."\n---\n',
                    encoding="utf-8",
                )
                result = self.run_validator(package, flags=("--self-contained",))
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_quoted_names_still_obey_name_constraints_and_directory_match(self):
        path = self.skill / "SKILL.md"
        for name in ("BadName", "bad_name", "-bad", "bad-", "bad--name", "技能", "a" * 65,
                     "different-name", ""):
            with self.subTest(name=name):
                path.write_text('---\nname: ' + json.dumps(name) + '\ndescription: "Task."\n---\n',
                                encoding="utf-8")
                self.assert_invalid()

    def test_quoted_name_json_escapes_are_decoded_before_validation(self):
        (self.skill / "SKILL.md").write_text(
            '---\nname: "\\u0073killforge-example"\ndescription: "Task."\n---\n',
            encoding="utf-8",
        )
        result = self.run_validator(self.skill)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_description_is_nonempty_and_bounded(self):
        path = self.skill / "SKILL.md"
        for description in ("", "   ", "a" * 1025):
            with self.subTest(length=len(description)):
                path.write_text('---\nname: skillforge-example\ndescription: '
                                + json.dumps(description) + '\n---\n', encoding="utf-8")
                self.assert_invalid()

    def test_duplicate_skill_names_fail_across_distinct_roots(self):
        duplicate = self.make_skill(self.root / "second")
        self.assert_invalid(self.skill, duplicate)

    def test_main_file_line_budget(self):
        self.append("\n" * 500)
        self.assert_invalid()

    def test_broken_inline_and_reference_links(self):
        for text in ("[missing](references/missing.md)", "[missing][ref]\n[ref]: missing.md"):
            with self.subTest(text=text):
                original = (self.skill / "SKILL.md").read_text(encoding="utf-8")
                self.append(text)
                self.assert_invalid()
                (self.skill / "SKILL.md").write_text(original, encoding="utf-8")

    def test_link_cannot_escape_to_existing_repository_file(self):
        (self.root / "outside.md").write_text("outside", encoding="utf-8")
        self.append("[outside](../outside.md)")
        self.assert_invalid()
        self.assert_invalid(flags=("--self-contained",))

    def test_url_encoded_link_escape_is_rejected(self):
        (self.root / "outside.md").write_text("outside", encoding="utf-8")
        self.append("[outside](%2e%2e/outside.md)")
        self.assert_invalid()

    def test_symlinked_external_content_cannot_pass_standalone_validation(self):
        outside = self.root / "outside.md"
        outside.write_text("# External content\n", encoding="utf-8")
        link = self.skill / "references" / "external.md"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("Creating symlinks is unavailable on this host")
        self.assert_invalid()
        self.assert_invalid(flags=("--self-contained",))

    def test_scheme_urls_cannot_be_used_as_fixtures(self):
        # Colons are legal POSIX filename characters; URL-shaped fixture paths still are not portable.
        path = self.skill / "evals" / "behavior-cases.json"
        case = json.loads(path.read_text(encoding="utf-8"))
        case[0]["fixtures"] = ["https://example.com/fixture.txt"]
        self.write_json(path, case)
        self.assert_invalid()

    def test_absolute_local_paths_in_main_or_references_are_rejected(self):
        for relative in ("SKILL.md", "references/details.md"):
            for text in (r"Read `C:\Users\Alice\project\input.txt`.",
                         "Read `D:/Project/input.txt`.", "Read `/home/alice/input.txt`.",
                         "Read `/etc/config.json`.", r"Read `\\server\share\input.txt`."):
                with self.subTest(relative=relative, text=text):
                    path = self.skill / relative
                    original = path.read_text(encoding="utf-8")
                    self.append(text, relative)
                    self.assert_invalid()
                    path.write_text(original, encoding="utf-8")

    def test_host_specific_tool_syntax_is_rejected(self):
        for text in ("Run `functions.exec` to continue.", "Must call `mcp__provider__tool`.",
                     "Use `tools.exec_command` for every command.", "Run `cua.getState()`."):
            with self.subTest(text=text):
                path = self.skill / "SKILL.md"
                original = path.read_text(encoding="utf-8")
                self.append(text)
                self.assert_invalid()
                path.write_text(original, encoding="utf-8")

    def test_single_segment_absolute_posix_paths_are_rejected(self):
        for relative in ("SKILL.md", "references/details.md"):
            path = self.skill / relative
            original = path.read_text(encoding="utf-8")
            for target in ("/tmp", "/config.json", "/opt/"):
                for flags in ((), ("--self-contained",)):
                    with self.subTest(relative=relative, target=target, flags=flags):
                        path.write_text(original + f"Use `{target}` for this task.\n", encoding="utf-8")
                        self.assert_invalid(flags=flags)
            path.write_text(original, encoding="utf-8")

    def test_unreal_virtual_roots_and_paths_remain_portable(self):
        self.append("Virtual roots `/Game`, `/Engine/`, `/Script` and `/Game/UI/WBP_Test`.")
        result = self.run_validator(self.skill, flags=("--self-contained",))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_discernible_script_reference_must_exist(self):
        (self.skill / "scripts" / "check.py").unlink()
        self.assert_invalid()

    def test_evals_are_optional_for_portable_runtime(self):
        shutil.rmtree(self.skill / "evals")
        result = self.run_validator(self.skill, flags=("--self-contained",))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertRegex(result.stdout, r"1 skill.*0 error")

    def test_eval_files_must_exist_and_be_json_arrays(self):
        for name in ("trigger-cases.json", "behavior-cases.json"):
            path = self.skill / "evals" / name
            original = path.read_text(encoding="utf-8")
            with self.subTest(name=name, case="missing"):
                path.unlink()
                self.assert_invalid()
            for value in ("{broken", "{}", "[]"):
                with self.subTest(name=name, value=value):
                    path.write_text(value, encoding="utf-8")
                    self.assert_invalid()
            path.write_text(original, encoding="utf-8")

    def test_trigger_schema_and_three_categories_are_required(self):
        path = self.skill / "evals" / "trigger-cases.json"
        original = json.loads(path.read_text(encoding="utf-8"))
        mutations = [original[:2], [{**original[0], "expected": "maybe"}, *original[1:]],
                     [{**original[0], "reason": ""}, *original[1:]],
                     [{key: value for key, value in original[0].items() if key != "context"},
                      *original[1:]], [original[0], {**original[1], "id": "positive"}, original[2]],
                     [42, *original[1:]]]
        for cases in mutations:
            with self.subTest(cases=cases):
                self.write_json(path, cases)
                self.assert_invalid()

    def test_behavior_expectations_and_fixture_paths_are_validated(self):
        path = self.skill / "evals" / "behavior-cases.json"
        original = json.loads(path.read_text(encoding="utf-8"))[0]
        (self.root / "outside.txt").write_text("outside", encoding="utf-8")
        for replacement in ({"expectations": []}, {"expectations": [""]},
                            {"expectations": [12]}, {"prompt": ""},
                            {"fixtures": ["fixtures/missing.txt"]},
                            {"fixtures": ["../outside.txt"]},
                            {"fixtures": ["/etc/config.json"]}, {"fixtures": "file.txt"}):
            with self.subTest(replacement=replacement):
                self.write_json(path, [{**original, **replacement}])
                self.assert_invalid()


if __name__ == "__main__":
    unittest.main()
