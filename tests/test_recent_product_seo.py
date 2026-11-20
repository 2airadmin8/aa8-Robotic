"""P0/P1 SEO and LLMO regression for publicly launched Oct 30-31 products.

Guard against missing sitemap/keyword ownership, duplicate or false Product
claims and stale organization address. No unverified prices or ratings.
"""
import json,re,sys,unittest
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import inject_structured_data as seo

RECENT=("unitree-g1-plus","unitree-h2-d","unitree-h2","unitree-h2-x","unitree-h2-plus","agibot-a3-ultra")

class RecentProductSeoTest(unittest.TestCase):
    def test_every_recent_published_product_in_sitemap(self):
        xml=ET.parse(ROOT/"sitemap.xml")
        locs=[node.text for node in xml.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        self.assertEqual(len(locs),len(set(locs)))
        for slug in RECENT:
            self.assertIn(f"https://robotics.air-admin8.co.jp/products/{slug}.html",locs)

    def test_each_recent_product_has_unique_keyword(self):
        pages=json.loads((ROOT/"data/seo-keywords.json").read_text(encoding="utf-8"))["pages"]
        paths={p["path"]:p for p in pages}
        for slug in RECENT:
            self.assertIn(f"products/{slug}.html",paths)
        keywords=[p["primaryKeyword"].casefold() for p in pages]
        self.assertEqual(len(keywords),len(set(keywords)))

    def test_recent_metadata_and_machine_readable_product(self):
        for slug in RECENT:
            with self.subTest(slug=slug):
                path=ROOT/"products"/f"{slug}.html"
                self.assertTrue(path.exists())
                source=path.read_text(encoding="utf-8")
                self.assertRegex(source,r"<h1\b")
                self.assertIn('rel="canonical"',source)
                self.assertNotIn('name="robots" content="noindex',source)
                result=seo.process_html(source,Path("products")/(slug+".html"))
                m=re.search(r'<script id="product-facts-schema" type="application/ld\+json">(.*?)</script>',result)
                self.assertIsNotNone(m,slug)
                graph=json.loads(m.group(1))
                self.assertEqual(graph["@type"],"Product")
                self.assertTrue(graph["image"][0].startswith("https://robotics.air-admin8.co.jp/assets/"))
                self.assertNotIn("offers",graph)
                self.assertNotIn("aggregateRating",graph)
                self.assertNotIn("review",graph)

    def test_company_address_not_historical(self):
        org=seo.organization_schema()
        address=org["address"]
        self.assertEqual(address["postalCode"],"164-0001")
        self.assertEqual(address["addressLocality"],"中野区")
        self.assertNotIn("大手町",str(address))

if __name__=="__main__":
    unittest.main()
