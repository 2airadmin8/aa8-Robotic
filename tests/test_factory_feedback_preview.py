"""Pure tests for SHA-bound, provider-verified CEO re-review Preview routing."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from factory_feedback_preview import eligible_preview

SHA = "a" * 40


class VerifiedPreviewSources(unittest.TestCase):
    def test_same_sha_successful_vercel_preview_only(self):
        deployments = [
            {"sha": SHA, "id": 4, "environment": "Preview – x2-edu-make-review"},
            {"sha": "b"*40, "id": 7, "environment": "Preview – x2-edu-make-review"},
            {"sha": SHA, "id": 8, "environment": "Production"},
        ]
        statuses = {
            "4": [{"state": "success", "environment_url": "https://x2-review-abc.vercel.app"}],
            "7": [{"state": "success", "environment_url": "https://wrong-sha.vercel.app"}],
            "8": [{"state": "success", "environment_url": "https://production.vercel.app"}],
        }
        self.assertEqual(eligible_preview(SHA, deployments, statuses),
                         ["https://x2-review-abc.vercel.app"])

    def test_incomplete_or_external_deployments_denied(self):
        deployments = [{"sha": SHA, "id": 4, "environment": "Preview"}]
        for url, state in [
            ("http://preview.vercel.app", "success"),
            ("https://preview.vercel.app.evil.test", "success"),
            ("https://user@preview.vercel.app", "success"),
            ("https://preview.vercel.app", "pending"),
            ("https://preview.vercel.app?token=abc", "success"),
        ]:
            with self.subTest(url=url, state=state):
                self.assertEqual(eligible_preview(SHA, deployments, {
                    "4": [{"state": state, "environment_url": url}]
                }), [])

    def test_invalid_sha_denied(self):
        with self.assertRaisesRegex(ValueError, "invalid SHA"):
            eligible_preview("short", [], {})

    def test_prefer_existing_review_project(self):
        dep = [
            {"sha": SHA, "id": 1, "environment": "Preview – hikari-proxy-dev"},
            {"sha": SHA, "id": 2, "environment": "Preview – x2-edu-make-review"},
        ]
        status = {
            "1": [{"state": "success", "environment_url": "https://hikari-abc.vercel.app"}],
            "2": [{"state": "success", "environment_url": "https://x2-edu-make-review-abc.vercel.app"}],
        }
        self.assertEqual(eligible_preview(SHA, dep, status)[0],
                         "https://x2-edu-make-review-abc.vercel.app")


if __name__ == "__main__":
    unittest.main()
