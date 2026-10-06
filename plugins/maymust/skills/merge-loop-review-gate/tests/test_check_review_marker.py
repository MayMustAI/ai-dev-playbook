import importlib.util
from pathlib import Path
import unittest


SPEC = importlib.util.spec_from_file_location(
    "check_review_marker", Path(__file__).parents[1] / "scripts/check_review_marker.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
HEAD = "a" * 40
PASS = f"<!-- loop-review:pass head={HEAD} blockers=0 mustfix=0 nits=2 round=1 at=2026-10-06T01:00:00Z -->"


class ReviewMarkerTests(unittest.TestCase):
    def check(self, body, **metadata):
        return MODULE.has_pass_marker(
            {"headRefOid": HEAD, "comments": [{"body": body}], **metadata}, HEAD
        )

    def test_accepts_current_head_comment(self):
        self.assertTrue(self.check("review complete\n\n" + PASS))

    def test_rejects_stale_head(self):
        self.assertFalse(self.check(PASS.replace(HEAD, "b" * 40)))

    def test_rejects_changed_pr_snapshot(self):
        self.assertFalse(self.check(PASS, headRefOid="b" * 40))

    def test_pr_body_is_not_review_evidence(self):
        self.assertFalse(MODULE.has_pass_marker({"headRefOid": HEAD, "body": PASS}, HEAD))

    def test_rejects_remaining_findings_and_incomplete_markers(self):
        for marker in [PASS.replace("blockers=0", "blockers=1"),
                       PASS.replace("mustfix=0", "mustfix=1"),
                       PASS.replace(" nits=2", ""), PASS.replace("round=1", "round=0")]:
            with self.subTest(marker=marker):
                self.assertFalse(self.check(marker))

    def test_rejects_invalid_timestamp_and_quoted_marker(self):
        self.assertFalse(self.check(PASS.replace("2026-10-06T01:00:00Z", "invalid")))
        self.assertFalse(self.check("> " + PASS))


if __name__ == "__main__":
    unittest.main()
