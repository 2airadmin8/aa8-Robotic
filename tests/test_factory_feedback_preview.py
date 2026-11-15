"""Pure tests for SHA-bound, provider-verified CEO re-review Preview routing."""
import sys
import unittest
from unittest.mock import patch
import io
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from factory_feedback_preview import eligible_preview, reachable, preview_probe, deliver, preview_path_from_pr

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

    def test_preview_http200_login_or_wrong_html_never_passes(self):
        url = "https://x2-edu-make-review-test.vercel.app/a2-factory-preview.html"
        valid = (
            '<!doctype html><meta name="robots" content="noindex,nofollow">'
            '<header class="site-header" data-shared-layout="header"></header>'
            '<main data-product-id="unitree-a2" data-product-factory="g1-v1">'
            '<a data-factory-cta="hero" href="/contact.html?product=Unitree%20A2">CTA</a></main>'
            '<footer class="footer" data-shared-layout="footer">'
            '<img class="aa8-main-logo" src="/assets/img/logo.svg"></footer>'
            '<script data-aa8-menu-runtime="true"></script>'
        )

        class FakeResponse:
            status = 200

            def __init__(self, html, final_url=url, content_type="text/html"):
                self.response = io.BytesIO(html.encode("utf-8"))
                self.url = final_url
                self.headers = {"Content-Type": content_type}

            def read(self, size):
                return self.response.read(size)

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

        for label, html, dest, content_type, expected in (
            ("valid", valid, url, "text/html", True),
            ("login page", "<html><title>Vercel Authentication</title></html>", url, "text/html", False),
            ("fake login with markers", valid + "<div>Vercel Authentication</div>", url, "text/html", False),
            ("missing noindex", valid.replace("noindex,nofollow", "index,follow"), url, "text/html", False),
            ("missing product ID", valid.replace('data-product-id="unitree-a2"', ''), url, "text/html", False),
            ("missing CTA", valid.replace('data-factory-cta="hero"', ''), url, "text/html", False),
            ("redirect to SSO", valid, "https://vercel.com/sso-api", "text/html", False),
            ("redirect to other preview", valid, "https://other.vercel.app/a2-factory-preview.html", "text/html", False),
            ("non-html response", valid, url, "text/plain", False),
        ):
            with self.subTest(label=label):
                with patch("factory_feedback_preview.urllib.request.urlopen",
                           return_value=FakeResponse(html, dest, content_type)):
                    self.assertEqual(reachable(url), expected)

        for bad_url in ("https://x2-edu-make-review-test.vercel.app/a2-factory-preview.html?token=secret",
                        "https://x2-edu-make-review-test.vercel.app.evil.test/a2-factory-preview.html"):
            self.assertFalse(reachable(bad_url))

    def test_protected_ceo_preview_delivered_without_fabricated_html_pass(self):
        url = "https://x2-edu-make-review-test.vercel.app"
        with patch("factory_feedback_preview.verify_live"), \
             patch("factory_feedback_preview.github") as github, \
             patch("factory_feedback_preview.preview_probe", return_value="AUTH_REQUIRED"), \
             patch("factory_feedback_preview.time.sleep") as sleep:
            github.side_effect = [
                [],  # existing comments
                [{"id": 51, "sha": SHA, "environment": "Preview – x2-edu-make-review"}],
                [{"state": "success", "environment_url": url,
                  "creator": {"login": "vercel[bot]"}}],
                [{"filename": "tests/fixtures/a2-factory/preview.html", "status": "added"}],
                {"id": 1001},  # posted to the original PR only
            ]
            result = deliver(SHA, 180, 42, 9911)
            self.assertEqual(result["status"], "WAIT_CEO_SSO_REVIEW")
            self.assertFalse(result["html_verified"])
            self.assertEqual(result["release"], "HOLD")
            sleep.assert_not_called()
            self.assertEqual(github.call_count, 5)
            posted = github.call_args_list[-1]
            self.assertEqual(posted.args[0], "repos/2airadmin8/aa8-Robotic/issues/180/comments")
            self.assertEqual(posted.kwargs["method"], "POST")
            self.assertIn(url + "/a2-factory-preview.html", posted.kwargs["body"])
            self.assertIn("HTML仍待CEO登录确认", posted.kwargs["body"])
            self.assertNotIn("已验证在线Preview", posted.kwargs["body"])

    def test_untrusted_preview_status_never_delivered(self):
        url = "https://x2-edu-make-review-test.vercel.app"
        from factory_feedback_preview import trusted_review_previews
        deps = [{"id": 51, "sha": SHA, "environment": "Preview – x2-edu-make-review"}]
        for status in (
            {"state": "success", "environment_url": url, "creator": {"login": "evil-bot"}},
            {"state": "success", "environment_url": "https://hikari-abc.vercel.app",
             "creator": {"login": "vercel[bot]"}},
            {"state": "pending", "environment_url": url, "creator": {"login": "vercel[bot]"}},
        ):
            with self.subTest(status=status):
                self.assertEqual(trusted_review_previews(SHA, deps, {"51": [status]}), [])
        self.assertEqual(trusted_review_previews("b" * 40, deps, {
            "51": [{"state": "success", "environment_url": url,
                    "creator": {"login": "vercel[bot]"}}]
        }), [])

    def test_preview_path_is_derived_from_original_pr_diff(self):
        with patch("factory_feedback_preview.github") as api:
            api.return_value = [
                {"filename": "tests/fixtures/h2plus-pilot/preview.html"},
                {"filename": "tests/test_product_factory.py"},
            ]
            self.assertEqual(preview_path_from_pr(180), "h2plus-pilot-preview.html")
        for changed in (
            [],
            [{"filename": "tests/fixtures/../../secrets/preview.html"}],
            [{"filename": "tests/fixtures/a2-factory/preview.html"},
             {"filename": "tests/fixtures/h2plus-pilot/preview.html"}],
            [{"filename": "tests/fixtures/a2-factory/preview.html"}] * 100,
        ):
            with self.subTest(changed=changed), patch("factory_feedback_preview.github", return_value=changed):
                with self.assertRaisesRegex(ValueError, "exactly one|pagination"):
                    preview_path_from_pr(180)

    def test_duplicate_ceo_handoff_is_idempotent(self):
        from factory_feedback_preview import MARKER
        with patch("factory_feedback_preview.verify_live"), \
             patch("factory_feedback_preview.github") as github:
            github.return_value = [{"body": MARKER.format(sha=SHA, comment_id=42)}]
            result = deliver(SHA, 180, 42, 9911)
            self.assertEqual(result["status"], "ALREADY_DELIVERED")
            self.assertEqual(github.call_count, 1)

    def test_ssoprotection_probe_distinguishes_html(self):
        url = "https://x2-edu-make-review-test.vercel.app/a2-factory-preview.html"
        class FakeResponse:
            status = 200
            headers = {"Content-Type": "text/html"}
            def __init__(self, landing): self.url = landing
            def __enter__(self): return self
            def __exit__(self, *_): return False
            def read(self, size): return b"<html>Vercel Authentication</html>"
        with patch("factory_feedback_preview.urllib.request.urlopen",
                   return_value=FakeResponse("https://vercel.com/sso-api")):
            self.assertEqual(preview_probe(url), "AUTH_REQUIRED")
            self.assertFalse(reachable(url))
        with patch("factory_feedback_preview.urllib.request.urlopen",
                   return_value=FakeResponse(url)):
            self.assertEqual(preview_probe(url), "AUTH_REQUIRED")

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
