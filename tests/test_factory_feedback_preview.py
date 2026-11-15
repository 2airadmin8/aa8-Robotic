"""Pure tests for SHA-bound, provider-verified CEO re-review Preview routing."""
import sys
import unittest
from unittest.mock import patch
import io
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from factory_feedback_preview import eligible_preview, reachable

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
