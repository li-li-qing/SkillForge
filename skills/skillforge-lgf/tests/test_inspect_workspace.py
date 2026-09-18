from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
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
