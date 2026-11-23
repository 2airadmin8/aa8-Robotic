"""New shared CSS overrides fail; existing historical site debt stays visible."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_shared_css_ownership import (  # noqa: E402
    css_rules, inventory, new_conflicts,
)


class SharedCSSOwnerDeltaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "assets/css").mkdir(parents=True)
        (self.root / "products").mkdir()
        self.owner = self.root / "assets/css/shared-layout.css"
        self.owner.write_text(".site-header{position:sticky}", encoding="utf-8")
        self.x2 = self.root / "products/x2.html"
        self.x2.write_text(
            '<style id="legacy">@media(max-width:900px){'
            'header.site-header nav.nav.open{position:absolute;top:100%}'
            '}</style>', encoding="utf-8",
        )
        self._git("init", "-q")
        self._git("config", "user.email", "qa@air-admin8.co.jp")
        self._git("config", "user.name", "QA fixture")
        self._git("add", ".")
        self._git("commit", "-qm", "historical baseline")
        self.base = self._git("rev-parse", "HEAD").strip()

    def _git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, text=True)

    def test_historical_inline_override_is_visible_not_new(self):
        found = inventory(self.root)
        self.assertIn("products/x2.html", found)
        self.assertGreater(sum(found["products/x2.html"].values()), 0)
        self.assertEqual(new_conflicts(self.root, self.base), [])

    def test_new_css_file_with_shared_selector_is_blocked(self):
        (self.root / "assets/css/new-product.css").write_text(
            ".site-header .menu { display:none !important; }", encoding="utf-8",
        )
        got = new_conflicts(self.root, self.base)
        self.assertEqual(len(got), 1)
        self.assertIn("new-product.css", got[0])

    def test_changed_historical_inline_rule_is_blocked(self):
        self.x2.write_text(
            '<style>@media(max-width:900px){'
            'header.site-header nav.nav.open{position:fixed;top:60px}'
            '}</style>', encoding="utf-8",
        )
        got = new_conflicts(self.root, self.base)
        self.assertEqual(len(got), 1)
        self.assertIn("products/x2.html", got[0])

    def test_new_html_inline_rule_is_blocked(self):
        (self.root / "products/new.html").write_text(
            "<style>.footer .footer-grid{width:100vw!important}</style>",
            encoding="utf-8",
        )
        got = new_conflicts(self.root, self.base)
        self.assertEqual(len(got), 1)
        self.assertIn("products/new.html", got[0])

    def test_new_css_in_footer_include_is_blocked(self):
        (self.root / "includes").mkdir()
        (self.root / "includes/site-footer.html").write_text(
            '<footer><style>.footer .footer-grid{margin-left:30px!important}'
            '</style></footer>', encoding="utf-8",
        )
        got = new_conflicts(self.root, self.base)
        self.assertEqual(len(got), 1)
        self.assertIn("includes/site-footer.html", got[0])

    def test_canonical_owner_changes_are_allowed(self):
        self.owner.write_text(
            ".site-header{position:sticky}.footer{padding:40px}",
            encoding="utf-8",
        )
        self.assertEqual(new_conflicts(self.root, self.base), [])

    def test_unrelated_style_and_print_only_rule_do_not_block(self):
        (self.root / "assets/css/more.css").write_text(
            "@media print{.site-header{display:none}} body{color:black}",
            encoding="utf-8",
        )
        self.assertEqual(new_conflicts(self.root, self.base), [])

    def test_whitespace_only_legacy_reformat_does_not_block(self):
        self.x2.write_text(
            '<style>@media (max-width:900px) {'
            ' header.site-header  nav.nav.open { position: absolute ; top: 100% ; }'
            '}</style>', encoding="utf-8",
        )
        self.assertEqual(new_conflicts(self.root, self.base), [])

    def test_invalid_or_unavailable_base_fails_closed(self):
        with self.assertRaises(ValueError):
            new_conflicts(self.root, "main")
        with self.assertRaises(ValueError):
            new_conflicts(self.root, "a" * 40)

    def test_nested_selectors_are_audited(self):
        rules = css_rules(
            "@media(max-width:900px){header.site-header nav.nav.open"
            "{position:absolute}}"
        )
        self.assertEqual(len(rules), 1)
        self.assertIn("nav.nav.open", rules[0][1])


if __name__ == "__main__":
    unittest.main()
