"""CEO feedback-driven rework: exact author/SHA, safe patch, fail closed."""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
import subprocess

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import factory_feedback_rework as fb


SHA = "a" * 40


def comment(now=None, reason="Please correct pilot test label safely."):
    now = now or datetime.now(timezone.utc)
    stamp = now.isoformat().replace("+00:00", "Z")
    return {
        "id": 8675309,
        "user": {"id": 211299962, "login": "2airadmin8"},
        "issue_url": "https://api.github.com/repos/2airadmin8/aa8-Robotic/issues/173",
        "body": (
            "<!-- AA8-CEO-RETURNED sha=" + SHA + " -->\n"
            "### CEO revision request / 退回修改\n"
            "PR #173 HEAD " + SHA + "\n\n"
            + reason +
            "\n\nThis records a real scoped PR change request. "
            "Existing Factory repair is NOT automatically started by a comment."
        ),
        "created_at": stamp,
        "updated_at": stamp,
    }


class FeedbackVerification(unittest.TestCase):
    def verify(self, data):
        return fb.verify_comment(
            data, expected_sha=SHA, comment_id=8675309,
            now=datetime.now(timezone.utc)
        )

    def test_owner_current_sha_pass(self):
        res = self.verify(comment())
        self.assertEqual(res["pr"], 173)
        self.assertEqual(res["sha"], SHA)
        self.assertEqual(res["release"], "HOLD")

    def test_forbidden_other_actor(self):
        data = comment()
        data["user"] = {"id": 111, "login": "2airadmin8"}
        with self.assertRaisesRegex(ValueError, "author"):
            self.verify(data)

    def test_forbidden_other_login(self):
        data = comment()
        data["user"] = {"id": 211299962, "login": "attacker"}
        with self.assertRaisesRegex(ValueError, "author"):
            self.verify(data)

    def test_forbidden_wrong_issue(self):
        data = comment()
        data["issue_url"] = data["issue_url"].replace("/173", "/172")
        with self.assertRaisesRegex(ValueError, "Wrong PR"):
            self.verify(data)

    def test_forbidden_other_sha(self):
        data = comment()
        data["body"] = data["body"].replace(SHA, "b" * 40)
        with self.assertRaisesRegex(ValueError, "HEAD marker"):
            self.verify(data)

    def test_forbidden_comment_edited_after_authorization(self):
        data = comment()
        data["updated_at"] = (
            datetime.now(timezone.utc) + timedelta(seconds=1)
        ).isoformat().replace("+00:00", "Z")
        with self.assertRaisesRegex(ValueError, "Edited feedback"):
            self.verify(data)

    def test_forbidden_stale_comment(self):
        with self.assertRaisesRegex(ValueError, "Stale"):
            self.verify(comment(datetime.now(timezone.utc) - timedelta(hours=1)))

    def test_forbidden_embedded_credentials(self):
        with self.assertRaisesRegex(ValueError, "credential"):
            self.verify(comment(reason="Please use ghp_01234567890123456789 now."))

    def test_forbidden_short_reason(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            self.verify(comment(reason="fix"))

    def test_forbidden_nonmatching_comment_id(self):
        with self.assertRaisesRegex(ValueError, "ID mismatch"):
            fb.verify_comment(comment(), expected_sha=SHA, comment_id=9876)


class FeedbackPatch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "tests" / "fixtures" / "x2-pilot").mkdir(parents=True)
        self.one = self.root / "tests/fixtures/x2-pilot/product.json"
        self.two = self.root / "tests/test_x2_pilot_factory.py"
        self.one.write_text('{"demo_label":"OLD"}\n', "utf-8")
        self.two.write_text("def test_pilot():\n    assert True\n", "utf-8")
        def run(*args):
            subprocess.run(
                ["git", *args], cwd=self.root, check=True,
                capture_output=True, timeout=10
            )
        run("init", "-q")
        run("-c", "user.email=test@example.test", "-c",
            "user.name=QA", "commit", "--allow-empty", "-m", "base")
        self.base = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.root, text=True
        ).strip()
        run("add", ".")
        run("-c", "user.email=test@example.test", "-c",
            "user.name=QA", "commit", "-m", "PR-173")
        self.head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.root, text=True
        ).strip()
        self.verified = {"schema": "aa8-feedback-rework-v1", "pr": 173,
                         "sha": self.head, "comment_id": 8675309,
                         "reason": "Change demo label OLD to NEW",
                         "release": "HOLD"}

    def tearDown(self):
        self.tmp.cleanup()

    def test_minimal_patch_generated_and_validated(self):
        mock = '{"edits":[{"path":"tests/fixtures/x2-pilot/product.json",'
        mock += '"find":"OLD","replace":"NEW"}]}'
        with patch.object(fb, "request_deepseek", return_value=mock):
            result = fb.propose(
                self.root, self.base, self.verified, "test",
                self.root / "patch.diff", self.root / "report.json"
            )
        self.assertEqual(result["release"], "HOLD")
        self.assertEqual(result["files"], ["tests/fixtures/x2-pilot/product.json"])
        self.assertIn("NEW", self.one.read_text("utf-8"))
        self.assertGreater((self.root / "patch.diff").stat().st_size, 0)
        self.assertNotIn("OLD", self.one.read_text("utf-8"))

    def test_forged_path_forbidden(self):
        mock = '{"edits":[{"path":"data/products.json","find":"OLD","replace":"NEW"}]}'
        with patch.object(fb, "request_deepseek", return_value=mock):
            with self.assertRaises(ValueError):
                fb.propose(self.root, self.base, self.verified, "test",
                           self.root / "patch.diff", self.root / "report.json")

    def test_no_op_response_fails_closed(self):
        with patch.object(fb, "request_deepseek", return_value='{"edits":[]}'):
            with self.assertRaises(ValueError):
                fb.propose(self.root, self.base, self.verified, "test",
                           self.root / "patch.diff", self.root / "report.json")

    def test_wrong_head_rejected(self):
        self.verified["sha"] = SHA
        with self.assertRaisesRegex(ValueError, "SHA differs"):
            fb.propose(self.root, self.base, self.verified, "test",
                       self.root / "patch.diff", self.root / "report.json")


if __name__ == "__main__":
    unittest.main()
