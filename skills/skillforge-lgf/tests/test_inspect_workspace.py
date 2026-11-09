from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import subprocess
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "inspect_workspace.py"
SPEC = importlib.util.spec_from_file_location("inspect_workspace", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class InspectWorkspaceTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform.startswith("linux") and Path("/dev/full").exists(), "Linux /dev/full fixture")
    def test_real_stdout_failure_remains_nonzero_at_interpreter_shutdown(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_json(root / "Game.uproject", {})
            with open("/dev/full", "wb", buffering=0) as failed_output:
                result = subprocess.run([sys.executable, "-B", str(SCRIPT_PATH), str(root)],
                                        stdout=failed_output, stderr=subprocess.PIPE,
                                        text=True, timeout=5)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("JSON 输出失败", result.stderr)
            # CPython can replace main's 2 with 120 when shutdown flush also fails.
            # Exact process exit code is deliberately not part of the output-I/O contract.

    def make_project(self, root: Path, association: str = "5.7") -> None:
        write_json(
            root / "TestGame.uproject",
            {
                "EngineAssociation": association,
                "Modules": [{"Name": "TestGame"}],
                "Plugins": [
                    {"Name": "Mover", "Enabled": True},
                    {"Name": "IKRig", "Enabled": True},
                ],
            },
        )
        build_file = root / "Source" / "TestGame" / "TestGame.Build.cs"
        build_file.parent.mkdir(parents=True, exist_ok=True)
        build_file.write_text("// test", encoding="utf-8")

    def add_lgf(self, root: Path, folder: str = "LGameplayFramework", with_source: bool = True) -> None:
        plugin_root = root / "Plugins" / folder
        write_json(
            plugin_root / "LGameplayFramework.uplugin",
            {"VersionName": "test", "Modules": [{"Name": "LGameplayFrameworkCore"}]},
        )
        if with_source:
            module = plugin_root / "Source" / "LGameplayFrameworkCore"
            module.mkdir(parents=True, exist_ok=True)
            (module / "LGameplayFrameworkCore.Build.cs").write_text("// test", encoding="utf-8")
            (module / "Public").mkdir()
            (module / "Public" / "Test.h").write_text("// test", encoding="utf-8")

    def test_manifest_distinguishes_association_from_verified_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            self.make_project(root, association="{CUSTOM-ENGINE-GUID}")
            self.add_lgf(root)

            manifest = MODULE.collect_manifest(root, verbose=False)

            self.assertEqual(manifest["project"]["engine_association"], "{CUSTOM-ENGINE-GUID}")
            self.assertTrue(manifest["project"]["engine_association_is_not_verified_version"])
            self.assertFalse(manifest["engine"]["verified"])
            self.assertTrue(manifest["lgf"]["source_inspectable"])
            self.assertNotIn("content_candidates", manifest)

    def test_engine_root_reads_build_version_and_mover_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp).resolve()
            root = base / "Project"
            engine = base / "EngineRoot"
            root.mkdir()
            self.make_project(root)
            self.add_lgf(root)
            write_json(
                engine / "Engine" / "Build" / "Build.version",
                {"MajorVersion": 5, "MinorVersion": 7, "PatchVersion": 1, "Changelist": 123},
            )
            mover = engine / "Engine" / "Plugins" / "Experimental" / "Mover"
            write_json(mover / "Mover.uplugin", {})
            (mover / "README.md").write_text("test", encoding="utf-8")
            (mover / "Source" / "Mover").mkdir(parents=True)

            manifest = MODULE.collect_manifest(root, verbose=False, engine_root=engine)

            self.assertTrue(manifest["engine"]["verified"])
            self.assertEqual(manifest["engine"]["build_version"]["minor"], 7)
            self.assertTrue(manifest["engine"]["mover"]["source_found"])
            self.assertTrue(manifest["engine"]["mover"]["descriptor"].endswith("Mover.uplugin"))
            self.assertTrue(manifest["project"]["relevant_plugins"]["IKRig"])


    def test_mover_plugin_is_discovered_outside_experimental_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp).resolve()
            root = base / "Project"
            engine = base / "EngineRoot"
            root.mkdir()
            self.make_project(root)
            self.add_lgf(root)
            write_json(
                engine / "Engine" / "Build" / "Build.version",
                {"MajorVersion": 5, "MinorVersion": 8, "PatchVersion": 0},
            )
            mover = engine / "Engine" / "Plugins" / "Animation" / "Mover"
            write_json(mover / "Mover.uplugin", {})
            (mover / "Source" / "MoverRuntime").mkdir(parents=True)

            manifest = MODULE.collect_manifest(root, verbose=False, engine_root=engine)

            self.assertTrue(manifest["engine"]["mover"]["plugin_found"])
            self.assertEqual(Path(manifest["engine"]["mover"]["plugin_root"]), mover.resolve())
            self.assertTrue(manifest["engine"]["mover"]["source_found"])

    def test_multiple_mover_descriptors_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp).resolve()
            root = base / "Project"
            engine = base / "EngineRoot"
            root.mkdir()
            self.make_project(root)
            self.add_lgf(root)
            write_json(
                engine / "Engine" / "Build" / "Build.version",
                {"MajorVersion": 5, "MinorVersion": 7, "PatchVersion": 4},
            )
            write_json(engine / "Engine" / "Plugins" / "Experimental" / "Mover" / "Mover.uplugin", {})
            write_json(engine / "Engine" / "Plugins" / "Custom" / "Mover" / "Mover.uplugin", {})

            with self.assertRaisesRegex(ValueError, "多个 Mover.uplugin"):
                MODULE.collect_manifest(root, verbose=False, engine_root=engine)

    def test_multiple_lgf_copies_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            self.make_project(root)
            self.add_lgf(root, "LGF_A")
            self.add_lgf(root, "LGF_B")

            with self.assertRaisesRegex(ValueError, "多个 LGameplayFramework"):
                MODULE.collect_manifest(root, verbose=False)

    def test_cli_returns_two_for_ambiguous_lgf_copies(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            self.make_project(root)
            self.add_lgf(root, "LGF_A")
            self.add_lgf(root, "LGF_B")
            stderr = io.StringIO()

            with patch.object(sys, "argv", [str(SCRIPT_PATH), str(root)]), redirect_stderr(stderr):
                exit_code = MODULE.main()

            self.assertEqual(exit_code, 2)
            self.assertIn("多个 LGameplayFramework", stderr.getvalue())

    def test_descriptor_without_source_is_reported_not_inspectable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            self.make_project(root)
            self.add_lgf(root, with_source=False)

            manifest = MODULE.collect_manifest(root, verbose=False)

            self.assertTrue(manifest["lgf"]["found"])
            self.assertFalse(manifest["lgf"]["source_inspectable"])

    def test_multiple_projects_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            self.make_project(root)
            write_json(root / "Other.uproject", {})

            with self.assertRaisesRegex(ValueError, "恰好包含一个"):
                MODULE.collect_manifest(root, verbose=False)

    def test_malformed_project_json_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            (root / "Broken.uproject").write_text("{broken", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "无法读取 JSON"):
                MODULE.collect_manifest(root, verbose=False)

    def test_invalid_module_field_uses_cli_diagnostic(self) -> None:
        for descriptor in ('project','plugin'):
            for value in (None,'wrong',{},42):
                with self.subTest(descriptor=descriptor,value=value), tempfile.TemporaryDirectory() as temp:
                    root=Path(temp).resolve();self.make_project(root);self.add_lgf(root)
                    path=root/'TestGame.uproject' if descriptor=='project' else root/'Plugins/LGameplayFramework/LGameplayFramework.uplugin'
                    data=json.loads(path.read_text());data['Modules']=value;write_json(path,data)
                    stderr=io.StringIO()
                    with patch.object(sys,'argv',[str(SCRIPT_PATH),str(root)]),redirect_stderr(stderr):
                        result=MODULE.main()
                    self.assertEqual(result,2)
                    self.assertIn(path.name,stderr.getvalue())
                    self.assertIn('Modules',stderr.getvalue())
                    self.assertNotIn('Traceback',stderr.getvalue())

    def test_invalid_module_entries_report_exact_cli_location(self) -> None:
        invalid = [
            (None, "$.Modules[1]"),
            ([], "$.Modules[1]"),
            ("wrong", "$.Modules[1]"),
            ({}, "$.Modules[1].Name"),
            ({"Name": 7}, "$.Modules[1].Name"),
            ({"Name": None}, "$.Modules[1].Name"),
            ({"Name": ""}, "$.Modules[1].Name"),
            ({"Name": "  "}, "$.Modules[1].Name"),
            ({"Name": "First"}, "$.Modules[1].Name"),
        ]
        for descriptor in ("project", "plugin"):
            for entry, location in invalid:
                with self.subTest(descriptor=descriptor, entry=entry), tempfile.TemporaryDirectory() as temp:
                    root = Path(temp).resolve()
                    self.make_project(root)
                    self.add_lgf(root)
                    path = root / "TestGame.uproject" if descriptor == "project" else root / "Plugins/LGameplayFramework/LGameplayFramework.uplugin"
                    data = json.loads(path.read_text())
                    data["Modules"] = [{"Name": "First"}, entry]
                    write_json(path, data)
                    stderr, stdout = io.StringIO(), io.StringIO()
                    with patch.object(sys, "argv", [str(SCRIPT_PATH), str(root)]), redirect_stderr(stderr), redirect_stdout(stdout):
                        result = MODULE.main()
                    self.assertEqual(result, 2)
                    self.assertIn(str(path), stderr.getvalue())
                    self.assertIn(location, stderr.getvalue())
                    self.assertNotIn("Traceback", stderr.getvalue())
                    self.assertEqual(stdout.getvalue(), "")
                    if entry == {"Name": "First"}:
                        self.assertIn("$.Modules[0].Name", stderr.getvalue())

    def test_valid_module_names_preserve_order_and_optional_fields(self) -> None:
        data = {"Modules": [{"Name": "B", "Type": "Runtime"}, {"Name": "A", "Extra": 1}]}
        self.assertEqual(MODULE.descriptor_modules(data, Path("Example.uplugin")), ["B", "A"])

    def test_missing_and_empty_module_fields_are_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve();write_json(root/'TestGame.uproject',{})
            manifest=MODULE.collect_manifest(root,verbose=True)
            self.assertEqual(manifest['project']['modules'],[])
            self.add_lgf(root)
            write_json(root/'Plugins/LGameplayFramework/LGameplayFramework.uplugin',{'Modules':[]})
            self.assertEqual(MODULE.collect_manifest(root,verbose=True)['lgf']['modules'],[])

    def test_invalid_plugin_list_and_entries_fail_closed(self) -> None:
        for value in (None, "wrong", {}, 42, [None], [{}], [{"Name": 4}]):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "Plugins"):
                    MODULE.plugin_summary({"Plugins": value})

    def test_missing_enabled_is_unknown_not_disabled(self) -> None:
        self.assertEqual(MODULE.plugin_summary({"Plugins": [{"Name": "Mover"}]}), {"Mover": None})
        self.assertEqual(MODULE.plugin_summary({}), {})

    def test_duplicate_plugin_entries_are_conflicts(self) -> None:
        for name in ("Mover", "UnlistedPlugin"):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "重复|conflict"):
                MODULE.plugin_summary({"Plugins": [{"Name": name, "Enabled": True}, {"Name": name, "Enabled": False}]})

    def test_absence_is_scoped_to_project_plugin_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            self.make_project(root)
            manifest = MODULE.collect_manifest(root, verbose=False)
            self.assertFalse(manifest["lgf"]["found"])
            self.assertEqual(manifest["lgf"]["status"], "not_found_in_project")
            self.assertEqual(manifest["lgf"]["search_scope"], "project_plugins_only")
            self.assertFalse(manifest["lgf"]["runtime_enabled_verified"])

    def test_source_directory_names_are_not_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            self.make_project(root)
            self.add_lgf(root, with_source=False)
            source = root / "Plugins/LGameplayFramework/Source"
            for name in ("Fake.Build.cs", "Fake.h", "Fake.cpp"):
                (source / name).mkdir(parents=True)
            (root / "Source/Fake.Build.cs").mkdir()
            manifest = MODULE.collect_manifest(root, verbose=True)
            self.assertFalse(manifest["lgf"]["source_inspectable"])
            self.assertEqual(manifest["lgf"]["build_file_count"], 0)
            self.assertEqual(manifest["lgf"]["header_count"], 0)
            self.assertEqual(manifest["lgf"]["source_file_count"], 0)
            self.assertEqual(manifest["build_files"]["project"], ["Source/TestGame/TestGame.Build.cs"])
            (source / "Real.Build.cs").write_text("// fixture")
            (source / "Real.cpp").write_text("// fixture")
            manifest = MODULE.collect_manifest(root, verbose=True)
            self.assertTrue(manifest["lgf"]["source_inspectable"])
            self.assertEqual(manifest["lgf"]["source_file_count"], 1)
            self.assertEqual(manifest["lgf"]["build_file_count"], 1)

    def test_duplicate_keys_and_deep_json_return_cli_error(self) -> None:
        payloads = [
            ('{"Plugins": [], "Plugins": []}', "Plugins"),
            ('{"Plugins": [{"Name": "Mover", "Enabled": false, "Enabled": true}]}', "Enabled"),
            ('{"X":' + '[' * 10000 + '0' + ']' * 10000 + '}', "JSON"),
        ]
        for descriptor in ("project", "plugin", "engine"):
            for payload, clue in payloads:
                with self.subTest(descriptor=descriptor, clue=clue), tempfile.TemporaryDirectory() as temp:
                    root = Path(temp).resolve()
                    self.make_project(root)
                    self.add_lgf(root)
                    argv = [str(SCRIPT_PATH), str(root)]
                    path = root / "TestGame.uproject"
                    if descriptor == "plugin":
                        path = root / "Plugins/LGameplayFramework/LGameplayFramework.uplugin"
                    elif descriptor == "engine":
                        engine = root / "EngineRoot"
                        path = engine / "Engine/Build/Build.version"
                        path.parent.mkdir(parents=True)
                        argv += ["--engine-root", str(engine)]
                    path.write_text(payload)
                    stderr, stdout = io.StringIO(), io.StringIO()
                    with patch.object(sys, "argv", argv), redirect_stderr(stderr), redirect_stdout(stdout):
                        result = MODULE.main()
                    self.assertEqual(result, 2)
                    self.assertIn(str(path), stderr.getvalue())
                    self.assertIn(clue, stderr.getvalue())
                    self.assertNotIn("Traceback", stderr.getvalue())
                    self.assertEqual(stdout.getvalue(), "")

    def test_json_bom_and_repeated_names_in_separate_objects_are_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "Valid.json"
            path.write_text('{"a":{"Name":"A"},"b":{"Name":"B"}}', encoding="utf-8-sig")
            self.assertEqual(MODULE.load_json(path), {"a": {"Name": "A"}, "b": {"Name": "B"}})

    def test_external_descriptor_symlink_reports_real_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp).resolve()
            root = base / "Project"
            root.mkdir()
            self.make_project(root)
            external = base / "External/Descriptor.json"
            write_json(external, {"VersionName": "external"})
            link = root / "Plugins/LGF/LGameplayFramework.uplugin"
            link.parent.mkdir(parents=True)
            try:
                link.symlink_to(external)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink unavailable: {exc}")
            manifest = MODULE.collect_manifest(root, verbose=False)
            self.assertEqual(manifest["lgf"]["file"], "Plugins/LGF/LGameplayFramework.uplugin")
            self.assertEqual(manifest["lgf"]["resolved_file"], str(external))
            self.assertTrue(manifest["lgf"]["descriptor_outside_project"])
            self.assertEqual(manifest["lgf"]["version_name"], "external")
            self.assertFalse(manifest["lgf"]["source_inspectable"])

    def test_version_file_only_retains_narrow_verification_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp).resolve()
            root = base / "Project"
            root.mkdir()
            self.make_project(root)
            engine = base / "VersionFileOnly"
            write_json(engine / "Engine/Build/Build.version", {"MajorVersion": 5, "MinorVersion": 8, "PatchVersion": 0})
            manifest = MODULE.collect_manifest(root, verbose=False, engine_root=engine)
            self.assertTrue(manifest["engine"]["verified"])
            limitations = " ".join(manifest["limitations"])
            self.assertIn("Build.version", limitations)
            self.assertIn("EngineAssociation", limitations)
            self.assertIn("不证明", limitations)
            self.assertIsNone(manifest["lgf"]["resolved_file"])
            self.assertIsNone(manifest["lgf"]["descriptor_outside_project"])

    def test_json_resource_errors_are_narrowly_converted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "Input.json"
            path.write_text("{}")
            with patch.object(MODULE.json, "loads", side_effect=MemoryError):
                with self.assertRaisesRegex(ValueError, "MemoryError"):
                    MODULE.load_json(path)
            with patch.object(MODULE.json, "loads", side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):
                    MODULE.load_json(path)

    def test_engine_association_optional_string_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            path = root / "Game.uproject"
            for data in ({}, {"EngineAssociation": None}, {"EngineAssociation": ""}, {"EngineAssociation": "{CUSTOM-GUID}"}):
                write_json(path, data)
                self.assertEqual(MODULE.collect_manifest(root, False)["project"]["engine_association"], data.get("EngineAssociation"))
            for value in ([], {}, True, 5, [0]):
                with self.subTest(value=value):
                    write_json(path, {"EngineAssociation": value})
                    with self.assertRaisesRegex(ValueError, r"Game.uproject.*EngineAssociation"):
                        MODULE.collect_manifest(root, False)

    def test_real_json_decode_encode_depth_gap_is_controlled(self) -> None:
        # Separate CLI processes avoid unittest's own stack changing the boundary.
        for field in ("VersionName", "Changelist", "CompatibleChangelist", "BranchName"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                root = Path(temp).resolve()
                write_json(root / "Game.uproject", {})
                argv = [sys.executable, str(SCRIPT_PATH), str(root)]
                if field == "VersionName":
                    path = root / "Plugins/LGF/LGameplayFramework.uplugin"
                    prefix = '{"VersionName":'
                else:
                    engine = root / "EngineRoot"
                    path = engine / "Engine/Build/Build.version"
                    prefix = '{"MajorVersion":5,"MinorVersion":8,"PatchVersion":0,"' + field + '":'
                    argv += ["--engine-root", str(engine)]
                path.parent.mkdir(parents=True, exist_ok=True)
                saw_output_boundary = False
                for depth in range(980, 1001):
                    path.write_text(prefix + '[' * depth + '0' + ']' * depth + '}')
                    result = subprocess.run(argv, capture_output=True, text=True, timeout=5)
                    if "编码" in result.stderr or "_iterencode" in result.stderr:
                        saw_output_boundary = True
                        self.assertEqual(result.returncode, 2)
                        self.assertNotIn("Traceback", result.stderr)
                        self.assertEqual(result.stdout, "")
                        break
                self.assertTrue(saw_output_boundary, "No real decoder/encoder depth gap observed")

    def test_surrogate_output_roundtrips_as_ascii_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            write_json(root / "Game.uproject", {"EngineAssociation": "\ud800"})
            result = subprocess.run([sys.executable, str(SCRIPT_PATH), str(root)], capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["project"]["engine_association"], "\ud800")
            result.stdout.decode("ascii")

    def test_output_errors_do_not_swallow_interrupts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            write_json(root / "Game.uproject", {})
            for error in (MemoryError, RecursionError, ValueError):
                with self.subTest(error=error), patch.object(sys, "argv", [str(SCRIPT_PATH), str(root)]), patch.object(MODULE.json, "dumps", side_effect=error), redirect_stdout(io.StringIO()) as stdout, redirect_stderr(io.StringIO()) as stderr:
                    self.assertEqual(MODULE.main(), 2)
                    self.assertEqual(stdout.getvalue(), "")
                    self.assertIn("编码", stderr.getvalue())
            with patch.object(sys, "argv", [str(SCRIPT_PATH), str(root)]), patch.object(MODULE.json, "dumps", side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):
                    MODULE.main()

    def test_deep_engine_association_and_stdout_io_failure(self) -> None:
        class FailingOutput(io.StringIO):
            def write(self, text):
                raise OSError("fixture write failure")

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            path = root / "Game.uproject"
            path.write_text('{"EngineAssociation":' + '[' * 900 + '0' + ']' * 900 + '}')
            result = subprocess.run([sys.executable, str(SCRIPT_PATH), str(root)], capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 2)
            self.assertIn("$.EngineAssociation", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertEqual(result.stdout, "")
            path.write_text("{}")
            with patch.object(sys, "argv", [str(SCRIPT_PATH), str(root)]), redirect_stdout(FailingOutput()), redirect_stderr(io.StringIO()) as stderr:
                self.assertEqual(MODULE.main(), 2)
                self.assertIn("输出可能不完整", stderr.getvalue())

    def test_external_path_format_does_not_raise(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp).resolve()
            root = base / "Project"
            outside = base / "External" / "Module.Build.cs"
            root.mkdir()
            outside.parent.mkdir()
            outside.write_text("// test", encoding="utf-8")

            rendered = MODULE.display_path(root, outside)

            self.assertTrue(Path(rendered).is_absolute())


if __name__ == "__main__":
    unittest.main()
