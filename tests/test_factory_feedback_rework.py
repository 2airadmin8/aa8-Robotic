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


def comment(now=None, reason="Please correct pilot test label safely.", pr=173, sha=SHA):
    now = now or datetime.now(timezone.utc)
    stamp = now.isoformat().replace("+00:00", "Z")
    return {
        "id": 8675309,
        "user": {"id": 211299962, "login": "2airadmin8"},
        "issue_url": f"https://api.github.com/repos/2airadmin8/aa8-Robotic/issues/{pr}",
        "body": (
            "<!-- AA8-CEO-RETURNED sha=" + sha + " -->\n"
            "### CEO revision request / 退回修改\n"
            f"PR #{pr} HEAD " + sha + "\n\n"
            + reason +
            "\n\nThis records a real scoped PR change request. "
            "Only authenticated, bounded Draft PR repairs are eligible."
        ),
        "created_at": stamp,
        "updated_at": stamp,
    }


class FeedbackVerification(unittest.TestCase):
    def verify(self, data):
        return fb.verify_comment(
            data, expected_sha=SHA, expected_pr=173, comment_id=8675309,
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
            fb.verify_comment(comment(), expected_sha=SHA, expected_pr=173, comment_id=9876)


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
        self.verified = {"schema": "aa8-feedback-rework-v2", "pr": 173,
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


class GenericDraftFeedbackRouting(unittest.TestCase):
    """Contract tests use synthetic events only, never a fabricated CEO action."""
    PR = 201

    def fixture(self):
        c = comment(pr=self.PR)
        event = {
            "action": "created", "repository": {"full_name": fb.EXPECTED_REPOSITORY},
            "issue": {"number": self.PR, "pull_request": {"url": "https://api.github.com/pr/201"}},
            "comment": {"id": c["id"], "body": c["body"]},
        }
        pr = {
            "number": self.PR, "state": "open", "draft": True,
            "head": {"sha": SHA, "ref": "feat/unitree-new-model",
                     "repo": {"full_name": fb.EXPECTED_REPOSITORY}},
            "base": {"ref": "main", "sha": "b" * 40,
                     "repo": {"full_name": fb.EXPECTED_REPOSITORY}},
        }
        return event, pr, c

    def test_generic_draft_201_routes_exact_sha_to_trusted_main(self):
        event, pr, c = self.fixture()
        result = fb.route_event(event, pr, c)
        self.assertEqual(result["pr"], 201)
        self.assertEqual(result["sha"], SHA)
        self.assertEqual(result["branch"], "feat/unitree-new-model")
        self.assertEqual(result["dispatch_ref"], "main")
        self.assertEqual(result["release"], "HOLD")

    def test_closed_or_ready_pr_denied(self):
        for key, value in (("state", "closed"), ("draft", False)):
            event, pr, c = self.fixture()
            pr[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                fb.route_event(event, pr, c)

    def test_fork_or_wrong_base_denied(self):
        for field in ("head", "base"):
            event, pr, c = self.fixture()
            pr[field]["repo"]["full_name"] = "someone-else/evil"
            with self.subTest(field=field), self.assertRaises(ValueError):
                fb.route_event(event, pr, c)
        event, pr, c = self.fixture()
        pr["base"]["ref"] = "release"
        with self.assertRaises(ValueError):
            fb.route_event(event, pr, c)

    def test_stale_sha_and_replay_edit_denied(self):
        event, pr, c = self.fixture()
        pr["head"]["sha"] = "c" * 40
        with self.assertRaises(ValueError):
            fb.route_event(event, pr, c)
        event, pr, c = self.fixture()
        c["updated_at"] = (datetime.now(timezone.utc) + timedelta(seconds=2)).isoformat()
        with self.assertRaises(ValueError):
            fb.route_event(event, pr, c)

    def test_untrusted_issue_or_mismatched_comment_denied(self):
        event, pr, c = self.fixture()
        event["issue"]["pull_request"] = None
        with self.assertRaises(ValueError):
            fb.route_event(event, pr, c)
        event, pr, c = self.fixture()
        event["comment"]["id"] += 1
        with self.assertRaises(ValueError):
            fb.route_event(event, pr, c)
        event, pr, c = self.fixture()
        event["action"] = "edited"
        with self.assertRaises(ValueError):
            fb.route_event(event, pr, c)

    def test_no_master_or_workflow_auto_edits(self):
        self.assertFalse(fb.is_feedback_source("data/products.json"))
        self.assertFalse(fb.is_feedback_source(".github/workflows/ci.yml"))
        self.assertFalse(fb.is_feedback_source("scripts/factory_autofix_policy.py"))
        self.assertTrue(fb.is_feedback_source("products/unitree-g1-plus.html"))
        self.assertTrue(fb.is_feedback_source("tests/fixtures/x2-pilot/product.json"))


if __name__ == "__main__":
    unittest.main()
