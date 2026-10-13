import importlib.util
import json
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
    def sync_dev_into_release(self, resolve=None):
        self.git("switch", "-q", "-c", "release/v0.1")
        if resolve:
            self.commit("app.txt", "release\n", "release edit")
        self.git("switch", "-q", "-c", "dev", "main")
        dev = self.commit("app.txt", "dev\n", "dev edit") if resolve else self.commit(
            "y.txt", "y\n", "dev work")
        self.git("switch", "-q", "-c", "chore/sync", "release/v0.1")
        return dev, self.merge("dev", resolve)

    def test_clean_sync_of_reviewed_commits_is_eligible(self):
        dev, _sync = self.sync_dev_into_release()
        result = MODULE.evaluate_waiver(self.repo, "release/v0.1", "chore/sync", {dev})
        self.assertEqual(result["status"], "eligible")
        self.assertEqual(result["commit_count"], 2)

    def test_commits_outside_merged_prs_need_acknowledgement(self):
        dev, _sync = self.sync_dev_into_release()
        result = MODULE.evaluate_waiver(self.repo, "release/v0.1", "chore/sync", set())
        self.assertEqual(result["status"], "needs-ack")
        self.assertEqual([c["sha"] for c in result["unreviewed_commits"]], [dev])

    def test_manual_conflict_resolution_blocks_waiver(self):
        dev, sync = self.sync_dev_into_release(resolve="release + dev\n")
        result = MODULE.evaluate_waiver(self.repo, "release/v0.1", "chore/sync", {dev})
        self.assertEqual(result["status"], "blocked")
        self.assertEqual([c["sha"] for c in result["conflict_merges"]], [sync])

    def test_edit_hidden_in_clean_merge_blocks_waiver(self):
        self.git("branch", "release/v0.1")
        self.git("switch", "-q", "-c", "dev")
        dev = self.commit("y.txt", "y\n", "dev work")
        self.git("switch", "-q", "-c", "chore/sync", "release/v0.1")
        self.git("merge", "--no-ff", "--no-commit", "-q", "dev")
        Path(self.repo, "z.txt").write_text("unreviewed\n")
        self.git("add", "z.txt")
        self.git("commit", "-q", "-m", "merge dev")
        result = MODULE.evaluate_waiver(self.repo, "release/v0.1", "chore/sync", {dev})
        self.assertEqual(result["status"], "blocked")

    def test_merge_already_gated_by_merged_pr_is_not_rechecked(self):
        dev, sync = self.sync_dev_into_release(resolve="release + dev\n")
        result = MODULE.evaluate_waiver(self.repo, "release/v0.1", "chore/sync", {dev, sync})
        self.assertEqual(result["status"], "eligible")


class MergedPrCommitsTests(unittest.TestCase):
    def test_batches_queries_and_keeps_only_merged_associations(self):
        shas = [f"{i:040x}" for i in range(MODULE.GRAPHQL_BATCH + 1)]
        calls = []

        def runner(args):
            calls.append(args)
            query = args[args.index("-f") + 1]
            count = query.count("object(oid:")
            repo = {f"c{i}": {"associatedPullRequests": {"nodes": [{"merged": i == 0}]}}
                    for i in range(count)}
            return mock.Mock(stdout=json.dumps({"data": {"repository": repo}}))

        merged = MODULE.merged_pr_commits("org/repo", shas, runner=runner)
        self.assertEqual(len(calls), 2)
        self.assertEqual(merged, {shas[0], shas[MODULE.GRAPHQL_BATCH]})
        self.assertIn("owner=org", calls[0])
        self.assertIn("name=repo", calls[0])


if __name__ == "__main__":
    unittest.main()
