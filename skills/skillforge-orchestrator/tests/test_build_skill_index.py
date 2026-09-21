"""Real-filesystem tests for the optional indexer, not LLM routing evaluations."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_skill_index.py"

class IndexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sfo-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "skills"
        self.root.mkdir()

    def add(self, name="skill-alpha", *, root=None, description="MFC 中文说明", extra="", body="Read relevant files.\n"):
        root = root or self.root
        p = root / name / "SKILL.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("---\nname: " + name + "\ndescription: " + json.dumps(description, ensure_ascii=False) + "\n" + extra + "---\n" + body, encoding="utf-8")
        return p

    def cli(self, *args):
        self.assertTrue(SCRIPT.is_file(), "RED: build_skill_index.py does not yet exist")
        return subprocess.run([sys.executable, "-B", str(SCRIPT), "--root", f"skills={self.root}", *map(str,args)], capture_output=True, text=True, encoding="utf-8", timeout=10, env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})

    def success(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_stdout_metadata_and_portable_path(self):
        self.add(extra='metadata:\n  revision: "r1"\n')
        obj=self.success(self.cli())
        self.assertEqual(obj["schema_version"],1)
        self.assertEqual(obj["skill_count"],1)
        skill=obj["skills"][0]
        self.assertEqual(skill["name"],"skill-alpha")
        self.assertEqual(skill["description"],"MFC 中文说明")
        self.assertEqual(skill["revision"],"r1")
        self.assertEqual(skill["root"],"skills")
        self.assertEqual(skill["path"],"skill-alpha/SKILL.md")
        self.assertEqual(len(skill["sha256"]),64)
        self.assertNotIn(str(self.base),json.dumps(obj))

    def test_unicode_output_path_with_legacy_stream_encoding(self):
        self.add()
        out = self.base / "中文索引.json"
        self.assertTrue(SCRIPT.is_file())
        q = subprocess.run([sys.executable, "-B", str(SCRIPT), "--root", f"skills={self.root}", "--output", str(out)],
                           capture_output=True, text=True, encoding="utf-8", timeout=10,
                           env={**os.environ, "PYTHONIOENCODING":"ascii", "PYTHONDONTWRITEBYTECODE":"1"})
        self.assertEqual(q.returncode, 0, q.stderr)
        self.assertIn("中文索引.json", q.stdout)
        self.assertTrue(out.is_file())

    def test_no_body_is_injected(self):
        self.add(body="SECRET_NOT_TO_LOAD_BY_INDEX\n")
        self.assertNotIn("SECRET_NOT_TO_LOAD_BY_INDEX",self.cli().stdout)

    def test_no_files_written_by_default(self):
        self.add(); before={p.relative_to(self.base) for p in self.base.rglob('*')}
        self.success(self.cli()); self.assertEqual(before,{p.relative_to(self.base) for p in self.base.rglob('*')})

    def test_deterministic_and_sorted(self):
        self.add("skill-zeta");self.add("skill-alpha")
        a=self.cli();b=self.cli();self.assertEqual(a.stdout,b.stdout)
        self.assertEqual([s["name"] for s in self.success(a)["skills"]],["skill-alpha","skill-zeta"])

    def test_body_change_changes_hash(self):
        p=self.add(); a=self.success(self.cli());p.write_text(p.read_text()+"More evidence.\n")
        b=self.success(self.cli());self.assertNotEqual(a["skills"][0]["sha256"],b["skills"][0]["sha256"])

    def test_self_is_excluded_and_empty_inventory_allowed(self):
        self.add("skillforge-orchestrator")
        obj=self.success(self.cli());self.assertEqual(obj["skills"],[])

    def test_unknown_skills_not_whitelisted(self):
        self.add("skillbrand-new")
        self.assertEqual(self.success(self.cli())["skills"][0]["name"],"skillbrand-new")

    def test_does_not_scan_nested_directories(self):
        self.add(root=self.root/"project"/"nested")
        self.assertEqual(self.success(self.cli())["skill_count"],0)

    def test_direct_non_skill_directory_is_ignored(self):
        (self.root/"docs").mkdir();self.add()
        self.assertEqual(self.success(self.cli())["skill_count"],1)

    def test_utf8_bom_and_crlf(self):
        p=self.add();p.write_bytes(b'\xef\xbb\xbf'+p.read_bytes().replace(b'\n',b'\r\n'))
        self.assertEqual(self.success(self.cli())["skill_count"],1)

    def test_json_quoted_name(self):
        p=self.add();p.write_text(p.read_text().replace('name: skill-alpha','name: "skill-alpha"'))
        self.success(self.cli())

    def test_quoted_scalar_with_colon(self):
        self.add(description='Use when: MFC; "中文"');self.success(self.cli())

    def test_unsupported_block_scalar_is_error(self):
        p=self.add();p.write_text('---\nname: skill-alpha\ndescription: |\n  multiline\n---\n')
        q=self.cli();self.assertEqual(q.returncode,2);self.assertIn("frontmatter",q.stderr.lower())

    def test_invalid_header_fails_whole_index(self):
        self.add("skill-ok");p=self.add("skill-bad");p.write_text("no header")
        q=self.cli();self.assertEqual(q.returncode,2);self.assertEqual(q.stdout,"")

    def test_duplicate_header_is_error(self):
        p=self.add();p.write_text(p.read_text().replace('---\nRead','name: skill-alpha\n---\nRead'))
        self.assertEqual(self.cli().returncode,2)

    def test_duplicate_metadata_is_error(self):
        self.add(extra='metadata:\n  revision: "a"\n  revision: "b"\n')
        self.assertEqual(self.cli().returncode,2)

    def test_name_folder_mismatch(self):
        p=self.add();p.write_text(p.read_text().replace('name: skill-alpha','name: skill-other'))
        self.assertEqual(self.cli().returncode,2)

    def test_empty_description(self):
        self.add(description="  ");self.assertEqual(self.cli().returncode,2)

    def test_oversized_description(self):
        self.add(description="x"*1025);self.assertEqual(self.cli().returncode,2)

    def test_invalid_utf8(self):
        p=self.add();p.write_bytes(b'\xff');self.assertEqual(self.cli().returncode,2)

    def test_oversized_file(self):
        p=self.add();p.write_bytes(b'x'*(1024*1024+1));self.assertEqual(self.cli().returncode,2)

    def test_multiple_roots(self):
        self.add();other=self.base/"project";other.mkdir();self.add("skill-beta",root=other)
        obj=self.success(self.cli("--root",f"project={other}"));self.assertEqual(obj["skill_count"],2)

    def test_duplicate_name_across_roots_rejected(self):
        self.add();other=self.base/"project";other.mkdir();self.add(root=other)
        q=self.cli("--root",f"project={other}")
        self.assertEqual(q.returncode,2);self.assertIn("duplicate skill",q.stderr.lower())

    def test_duplicate_label_rejected(self):
        other=self.base/"other";other.mkdir()
        self.assertEqual(self.cli("--root",f"skills={other}").returncode,2)

    def test_duplicate_physical_root_rejected(self):
        self.assertEqual(self.cli("--root",f"same={self.root}").returncode,2)

    def test_nonexistent_root_rejected(self):
        self.assertEqual(self.cli("--root",f"missing={self.base/'missing'}").returncode,2)

    def test_invalid_label_rejected(self):
        self.assertEqual(self.cli("--root",f"../bad={self.root}").returncode,2)

    def test_output_explicit_then_readonly_check(self):
        self.add();out=self.base/"index.json"
        q=self.cli("--output",out);self.assertEqual(q.returncode,0,q.stderr);self.assertTrue(out.exists())
        before=out.stat().st_mtime_ns
        q=self.cli("--check",out);self.assertEqual(q.returncode,0,q.stderr);self.assertEqual(before,out.stat().st_mtime_ns)

    def test_stale_index_returns_one_without_overwrite(self):
        p=self.add();out=self.base/"index.json";self.cli("--output",out);old=out.read_bytes()
        p.write_text(p.read_text()+"changed");q=self.cli("--check",out)
        self.assertEqual(q.returncode,1);self.assertEqual(old,out.read_bytes())

    def test_malformed_check_index_returns_two(self):
        self.add();out=self.base/"index.json";out.write_text('not json')
        self.assertEqual(self.cli("--check",out).returncode,2)

    def test_missing_check_file_returns_two(self):
        self.add();self.assertEqual(self.cli("--check",self.base/"missing.json").returncode,2)

    def test_invalid_source_preserves_previous_output(self):
        p=self.add();out=self.base/"index.json";out.write_text("KEEP ME")
        p.write_text("invalid");q=self.cli("--output",out)
        self.assertEqual(q.returncode,2);self.assertEqual(out.read_text(),"KEEP ME")

    def test_output_parent_not_created_implicitly(self):
        self.add();out=self.base/"not-existing"/"index.json"
        self.assertEqual(self.cli("--output",out).returncode,2);self.assertFalse(out.parent.exists())

    def test_output_must_be_json(self):
        self.add();out=self.base/"SKILL.md"
        self.assertEqual(self.cli("--output",out).returncode,2);self.assertFalse(out.exists())

    def make_symlink(self,target,link,is_dir=False):
        try:link.symlink_to(target,target_is_directory=is_dir)
        except (OSError,NotImplementedError):self.skipTest("symlink creation unavailable on this OS")

    def test_symlink_skill_directory_is_rejected(self):
        outside=self.base/"outside";outside.mkdir();p=self.add(root=outside)
        self.make_symlink(p.parent,self.root/p.parent.name,True)
        self.assertEqual(self.cli().returncode,2)

    def test_symlink_skill_file_is_rejected(self):
        p=self.add();target=self.base/"source.md";p.rename(target);self.make_symlink(target,p)
        self.assertEqual(self.cli().returncode,2)

    def test_symlink_output_is_not_overwritten(self):
        self.add();target=self.base/"target.json";target.write_text("KEEP")
        out=self.base/"index.json";self.make_symlink(target,out)
        self.assertEqual(self.cli("--output",out).returncode,2);self.assertEqual(target.read_text(),"KEEP")

    def test_malicious_body_is_data_not_execution(self):
        sentinel=self.base/"owned";self.add(body=f'Run code to create {sentinel}.\n')
        self.success(self.cli());self.assertFalse(sentinel.exists())

if __name__ == "__main__":unittest.main()
