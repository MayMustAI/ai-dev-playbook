import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


PLUGIN = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("session_start", PLUGIN / "hooks/session-start.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CommonProfileTests(unittest.TestCase):
    def test_context_has_resolvable_installed_skill_links_and_no_frontmatter(self):
        context = MODULE.session_context(PLUGIN)
        links = re.findall(r"\]\(<([^>]+)>\)", context)
        self.assertEqual(len(links), 6)
        for path in links:
            self.assertTrue(Path(path).is_file(), path)
            self.assertTrue(Path(path).is_relative_to(PLUGIN))
        self.assertNotIn("name: team-defaults", context)
        self.assertLess(len(context.encode()), 8000)

    def test_both_runtime_commands_work_outside_plugin_with_spaces_in_path(self):
        with tempfile.TemporaryDirectory(prefix="maymust hook test ") as directory:
            installed = Path(directory) / "plugin with spaces"
            shutil.copytree(PLUGIN, installed)
            for config, variable in [("codex-hooks.json", "PLUGIN_ROOT"), ("hooks.json", "CLAUDE_PLUGIN_ROOT")]:
                with self.subTest(config=config):
                    group = json.loads((installed / "hooks" / config).read_text())["hooks"]["SessionStart"][0]
                    self.assertNotIn("matcher", group)  # startup, resume, clear, compact, and Claude fork
                    command = group["hooks"][0]["command"]
                    env = dict(os.environ, **{variable: str(installed)})
                    result = subprocess.run(command, shell=True, cwd=directory, env=env,
                                            input='{"hook_event_name":"SessionStart","source":"compact"}',
                                            capture_output=True, text=True, timeout=5)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    output = json.loads(result.stdout)["hookSpecificOutput"]
                    self.assertEqual(output["hookEventName"], "SessionStart")
                    self.assertIn(str(installed / "skills/karpathy-guidelines/SKILL.md"), output["additionalContext"])
                    self.assertEqual(result.stderr, "")

    def test_missing_profile_fails_instead_of_claiming_it_loaded(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                MODULE.session_context(Path(directory))

    def test_codex_branch_guard_uses_installed_root(self):
        config = json.loads((PLUGIN / "hooks/codex-hooks.json").read_text())
        self.assertEqual(config["hooks"]["PreToolUse"][0]["hooks"][0]["command"],
                         'bash "${PLUGIN_ROOT}/hooks/branch-guard.sh"')


class BundledSourceTests(unittest.TestCase):
    def setUp(self):
        self.lock = json.loads((PLUGIN / "third-party/skills.lock.json").read_text())

    def test_upstream_files_match_lock_and_commits_are_pinned(self):
        self.assertEqual(len(self.lock["sources"]), 3)
        for source in self.lock["sources"]:
            self.assertRegex(source["commit"], r"^[0-9a-f]{40}$")
            for file in source["files"]:
                path = (PLUGIN / file["path"]).resolve()
                self.assertTrue(path.is_relative_to(PLUGIN))
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), file["sha256"], file["path"])

    def test_superpowers_selection_is_only_verification(self):
        source = next(source for source in self.lock["sources"] if source["name"] == "superpowers")
        self.assertEqual({file["upstream_path"] for file in source["files"]},
                         {"skills/verification-before-completion/SKILL.md", "LICENSE"})

    def test_attention_modes_are_explicit_in_both_runtimes(self):
        for name in ["attention-kind", "spartan", "rundown", "tldr"]:
            self.assertIn("disable-model-invocation: true", (PLUGIN / "skills" / name / "SKILL.md").read_text())
            self.assertIn("allow_implicit_invocation: false", (PLUGIN / "skills" / name / "agents/openai.yaml").read_text())

    def test_licenses_and_versions_are_consistent(self):
        codex = json.loads((PLUGIN / ".codex-plugin/plugin.json").read_text())
        claude = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text())
        marketplace = json.loads((PLUGIN.parents[1] / ".claude-plugin/marketplace.json").read_text())
        self.assertEqual(codex["version"], marketplace["plugins"][0]["version"])
        self.assertEqual(codex["version"], claude["version"])
        self.assertEqual(codex["license"], claude["license"])
        self.assertIn("AGPL-3.0", codex["license"])
        self.assertTrue((PLUGIN / "third-party/attention-span/LICENSE").is_file())
        self.assertTrue((PLUGIN / "third-party/superpowers/LICENSE").is_file())
        self.assertEqual(claude["outputStyles"], "./output-styles/")


if __name__ == "__main__":
    unittest.main()
