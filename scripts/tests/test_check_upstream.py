import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "check_upstream.py"
SPEC = importlib.util.spec_from_file_location("check_upstream", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def git(cwd, *args):
    return subprocess.run(["git", "-c", "user.email=t@example.com", "-c", "user.name=t", *args],
                          cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class CheckUpstreamTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.upstream = root / "upstream"
        (self.upstream / "skills/x").mkdir(parents=True)
        git(self.upstream, "init", "-q", "-b", "main")
        (self.upstream / "skills/x/SKILL.md").write_text("v1\n")
        (self.upstream / "LICENSE").write_text("MIT\n")
        (self.upstream / "notes.md").write_text("method v1\n")
        git(self.upstream, "add", ".")
        git(self.upstream, "commit", "-q", "-m", "v1")
        self.first_commit = git(self.upstream, "rev-parse", "HEAD")

        self.plugin = root / "plugin"
        (self.plugin / "skills/x").mkdir(parents=True)
        (self.plugin / "third-party/up").mkdir(parents=True)
        (self.plugin / "skills/x/SKILL.md").write_text("v1\n")
        (self.plugin / "third-party/up/LICENSE").write_text("MIT\n")
        self.lock_path = self.plugin / "third-party/skills.lock.json"
        self.lock_path.write_text(json.dumps({"schema_version": 1, "sources": [{
            "name": "up",
            "repository": self.upstream.as_uri(),
            "commit": self.first_commit,
            "license": "MIT",
            "files": [
                {"upstream_path": "skills/x/SKILL.md", "path": "skills/x/SKILL.md",
                 "sha256": digest(self.plugin / "skills/x/SKILL.md")},
                {"upstream_path": "LICENSE", "path": "third-party/up/LICENSE",
                 "sha256": digest(self.plugin / "third-party/up/LICENSE")},
            ],
            "adapted": [
                {"upstream_path": "notes.md", "upstream_sha256": digest(self.upstream / "notes.md"),
                 "used_in": ["skills/x/SKILL.md"]},
            ],
        }]}, indent=2) + "\n")

    def tearDown(self):
        self.tmp.cleanup()

    def commit_upstream(self, message, writes=(), moves=()):
        for path, text in writes:
            (self.upstream / path).write_text(text)
        for source, target in moves:
            (self.upstream / target).parent.mkdir(parents=True, exist_ok=True)
            git(self.upstream, "mv", source, target)
        git(self.upstream, "add", "-A")
        git(self.upstream, "commit", "-q", "-m", message)
        return git(self.upstream, "rev-parse", "HEAD")

    def run_check(self, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(MODULE.main(["--plugin-root", str(self.plugin), *args]), 0)
        return json.loads(output.getvalue())

    def statuses(self, report):
        source = report["sources"][0]
        return {item["upstream_path"]: item["status"] for item in source["files"] + source["adapted"]}

    def test_unchanged_upstream_reports_no_change(self):
        report = self.run_check()
        self.assertFalse(report["changed"])
        self.assertEqual(set(self.statuses(report).values()), {"same"})
        self.assertEqual(report["sources"][0]["latest_commit"], self.first_commit)

    def test_apply_copies_changed_file_and_pins_new_commit(self):
        latest = self.commit_upstream("v2", writes=[("skills/x/SKILL.md", "v2\n")])
        self.assertEqual(self.statuses(self.run_check())["skills/x/SKILL.md"], "changed")
        self.assertEqual((self.plugin / "skills/x/SKILL.md").read_text(), "v1\n")

        report = self.run_check("--apply")
        self.assertTrue(report["sources"][0]["applied"])
        self.assertEqual((self.plugin / "skills/x/SKILL.md").read_text(), "v2\n")
        lock = json.loads(self.lock_path.read_text())["sources"][0]
        self.assertEqual(lock["commit"], latest)
        self.assertEqual(lock["files"][0]["sha256"], digest(self.plugin / "skills/x/SKILL.md"))
        self.assertFalse(self.run_check()["changed"])

    def test_missing_upstream_path_blocks_apply(self):
        self.commit_upstream("move", writes=[("skills/x/SKILL.md", "v2\n")],
                             moves=[("skills/x/SKILL.md", "plugins/up/skills/x/SKILL.md")])
        before = self.lock_path.read_text()
        report = self.run_check("--apply")
        self.assertEqual(self.statuses(report)["skills/x/SKILL.md"], "missing")
        self.assertIn("missing", report["sources"][0]["blocked"])
        self.assertFalse(report["sources"][0]["applied"])
        self.assertEqual(self.lock_path.read_text(), before)

    def test_license_change_blocks_apply(self):
        self.commit_upstream("relicense", writes=[("skills/x/SKILL.md", "v2\n"), ("LICENSE", "AGPL\n")])
        report = self.run_check("--apply")
        self.assertIn("license", report["sources"][0]["blocked"])
        self.assertFalse(report["sources"][0]["applied"])
        self.assertEqual((self.plugin / "skills/x/SKILL.md").read_text(), "v1\n")

    def test_adapted_change_blocks_apply_for_its_source(self):
        self.commit_upstream("method v2", writes=[("skills/x/SKILL.md", "v2\n"), ("notes.md", "method v2\n")])
        before = self.lock_path.read_text()
        report = self.run_check("--apply")
        self.assertTrue(report["changed"])
        self.assertEqual(self.statuses(report)["notes.md"], "changed")
        self.assertIn("adapted", report["sources"][0]["blocked"])
        self.assertFalse(report["sources"][0]["applied"])
        self.assertEqual((self.plugin / "skills/x/SKILL.md").read_text(), "v1\n")
        self.assertEqual(self.lock_path.read_text(), before)


if __name__ == "__main__":
    unittest.main()
