"""Tracking loader is a build-level invariant, not only G1 pages."""
import unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from build_site import build_html

PAGES=[
 "index.html","products.html","resources/document.html","resources.html",
 "contact.html","products/unitree-h2-plus.html","products/unitree-h2-x.html",
 "support.html","use-cases.html",
]
class MarketingLoaderTest(unittest.TestCase):
    def test_every_landing_page_includes_exactly_one_direct_event_loader(self):
        for name in PAGES:
            with self.subTest(page=name):
                page=ROOT/name
                self.assertTrue(page.is_file(),name)
                output=build_html(page.read_text(encoding="utf-8"),Path(name))
                self.assertEqual(output.count('assets/js/analytics-events.js?v='),1,name)
    def test_retired_analytics_loader_not_present_in_seo_js(self):
        js=(ROOT/"assets/js/seo.js").read_text(encoding="utf-8")
        self.assertNotIn("ensureScript(",js.split("const pageMap",1)[0])
    def test_legacy_page_receives_direct_loader(self):
        source=(ROOT/"products.html").read_text(encoding="utf-8")
        built=build_html(source,Path("products.html"))
        self.assertIn('assets/js/analytics-events.js',built)
        self.assertIn('assets/js/seo.js',built)
    def test_site_wide_loader_is_idempotent(self):
        source=(ROOT/"products.html").read_text(encoding="utf-8")
        once=build_html(source,Path("products.html"))
        twice=build_html(once,Path("products.html"))
        self.assertEqual(twice.count('assets/js/analytics-events.js?v='),1)

if __name__=="__main__":unittest.main()
