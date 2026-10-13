import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock


SPEC = importlib.util.spec_from_file_location(
    "check_integration_pr", Path(__file__).parents[1] / "scripts/check_integration_pr.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
PATTERNS = ["main", "dev", "release/*"]
GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com",
}


class GitRepoTestCase(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.dict(os.environ, GIT_ENV)
        patcher.start()
        self.addCleanup(patcher.stop)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = tmp.name
        self.git("init", "-q", "-b", "main")
        self.commit("app.txt", "base\n", "base")

    def git(self, *args):
        return subprocess.run(["git", "-C", self.repo, *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def commit(self, path, text, message):
        Path(self.repo, path).write_text(text)
        self.git("add", path)
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def merge(self, branch, resolve=None):
        """Merge branch into HEAD; on conflict write resolve into app.txt."""
        result = subprocess.run(["git", "-C", self.repo, "merge", "--no-ff", "-q",
                                 "-m", f"merge {branch}", branch],
                                capture_output=True, text=True)
        if result.returncode != 0:
            Path(self.repo, "app.txt").write_text(resolve)
            self.git("add", "app.txt")
            self.git("commit", "-q", "--no-edit")
        return self.git("rev-parse", "HEAD")

    def classify(self, base, head):
        others = [b for b in self.git("branch", "--format=%(refname:short)").split()
                  if b != base and MODULE.is_long_lived(b, PATTERNS)]
        return MODULE.classify(self.repo, base, head, base, head, others, PATTERNS)


class ClassifyTests(GitRepoTestCase):
    def test_long_lived_head_uses_merge_commit(self):
        self.git("switch", "-q", "-c", "release/v0.1")
        self.commit("app.txt", "hardening\n", "hardening")
        self.assertEqual(self.classify("main", "release/v0.1"), ("merge", "head-long-lived"))

    def test_work_branch_uses_squash(self):
        self.git("switch", "-q", "-c", "dev")
        self.git("switch", "-q", "-c", "feature/x")
        self.commit("x.txt", "x\n", "feature")
        self.assertEqual(self.classify("dev", "feature/x"), ("squash", "work-branch"))

    def test_work_branch_that_merged_its_base_still_squashes(self):
        self.git("switch", "-q", "-c", "dev")
        self.git("switch", "-q", "-c", "feature/x")
        self.commit("x.txt", "x\n", "feature")
        self.git("switch", "-q", "dev")
        self.commit("y.txt", "y\n", "dev moves")
        self.git("switch", "-q", "feature/x")
        self.merge("dev")
        self.assertEqual(self.classify("dev", "feature/x"), ("squash", "work-branch"))

    def test_sync_branch_bringing_another_long_lived_branch_uses_merge_commit(self):
        self.git("branch", "release/v0.1")
        self.git("switch", "-q", "-c", "dev")
        self.commit("y.txt", "y\n", "dev work")
        self.git("switch", "-q", "-c", "chore/sync", "release/v0.1")
        sync = self.merge("dev")
        mode, reason = self.classify("release/v0.1", "chore/sync")
        self.assertEqual(mode, "merge")
        self.assertEqual(reason, f"sync-merge {sync[:12]} from dev")

    def test_short_lived_base_uses_squash(self):
        self.git("switch", "-q", "-c", "feature/base")
        self.git("switch", "-q", "-c", "feature/child")
        self.commit("x.txt", "x\n", "child")
        self.assertEqual(self.classify("feature/base", "feature/child"),
                         ("squash", "base-not-long-lived"))


class WaiverTests(GitRepoTestCase):
    def long_refs(self):
        return [b for b in self.git("branch", "--format=%(refname:short)").split()
                if MODULE.is_long_lived(b, PATTERNS)]

    def waiver(self, base, head):
        return MODULE.evaluate_waiver(self.repo, base, head, self.long_refs())

    def sync_dev_into_release(self, resolve=None):
        self.git("switch", "-q", "-c", "release/v0.1")
        if resolve:
            self.commit("app.txt", "release\n", "release edit")
        self.git("switch", "-q", "-c", "dev", "main")
        if resolve:
            self.commit("app.txt", "dev\n", "dev edit")
        else:
            self.commit("y.txt", "y\n", "dev work")
        self.git("switch", "-q", "-c", "chore/sync", "release/v0.1")
        return self.merge("dev", resolve)

    def test_clean_sync_is_eligible(self):
        self.sync_dev_into_release()
        self.assertEqual(self.waiver("release/v0.1", "chore/sync"),
                         {"status": "eligible", "blocking_commits": []})

    def test_manual_conflict_resolution_blocks_waiver(self):
        sync = self.sync_dev_into_release(resolve="release + dev\n")
        result = self.waiver("release/v0.1", "chore/sync")
        self.assertEqual(result["status"], "blocked")
        self.assertEqual([(c["sha"], c["kind"]) for c in result["blocking_commits"]],
                         [(sync, "merge-differs-from-auto-merge")])

    def test_edit_hidden_in_clean_merge_blocks_waiver(self):
        self.git("branch", "release/v0.1")
        self.git("switch", "-q", "-c", "dev")
        self.commit("y.txt", "y\n", "dev work")
        self.git("switch", "-q", "-c", "chore/sync", "release/v0.1")
        self.git("merge", "--no-ff", "--no-commit", "-q", "dev")
        Path(self.repo, "z.txt").write_text("unreviewed\n")
        self.git("add", "z.txt")
        self.git("commit", "-q", "-m", "merge dev")
        self.assertEqual(self.waiver("release/v0.1", "chore/sync")["status"], "blocked")

    def test_new_commit_on_sync_branch_blocks_waiver(self):
        self.sync_dev_into_release()
        extra = self.commit("z.txt", "fix\n", "fix after sync")
        result = self.waiver("release/v0.1", "chore/sync")
        self.assertEqual([(c["sha"], c["kind"]) for c in result["blocking_commits"]],
                         [(extra, "new-commit")])

    def test_commits_already_on_long_lived_head_are_not_rechecked(self):
        self.sync_dev_into_release(resolve="release + dev\n")
        self.git("switch", "-q", "release/v0.1")
        self.git("merge", "-q", "--ff-only", "chore/sync")
        self.assertEqual(self.waiver("main", "release/v0.1")["status"], "eligible")


if __name__ == "__main__":
    unittest.main()
