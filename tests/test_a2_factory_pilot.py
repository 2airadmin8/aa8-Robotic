"""Real Unitree A2 quadruped: manufacturer evidence -> existing Factory preview.
Preview-only. No public Product Master modification, price fabrication or CRM write.
"""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
PILOT=ROOT/"tests/fixtures/a2-factory"
sys.path.insert(0,str(ROOT/"scripts"))
import product_factory as factory
from hp_design_contract import validate_new_candidate

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

class A2RealFactoryPilot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.product=json.loads((PILOT/"product.json").read_text("utf-8"))
        cls.evidence=json.loads((PILOT/"source-contract.json").read_text("utf-8"))
        cls.preview=(PILOT/"preview.html").read_text("utf-8")

    def test_manufacturer_source_and_quadruped_contract(self):
        self.assertEqual(self.product["id"],"unitree-a2")
        self.assertEqual(self.product["categoryId"],"quadruped")
        self.assertEqual(self.product["pageStandard"]["family"],"quadruped")
        self.assertEqual(self.evidence["sku_id"],self.product["id"])
        self.assertTrue(self.evidence["source_ready_at"].endswith("+09:00"))
        self.assertEqual(self.evidence["official_source"],"https://www.unitree.com/A2/")
        self.assertEqual(self.evidence["status"],"SOURCE_QUALIFIED_FOR_ISOLATED_PREVIEW_ONLY")
        validate_new_candidate("quadruped", self.evidence["qualification"]["candidate"],ROOT)
        self.assertFalse(self.product["pageFactory"]["releaseReady"])

    def test_images_maker_urls_and_hashes(self):
        self.assertEqual(len(self.evidence["media"]),5)
        self.assertEqual(sha(ROOT/self.evidence["hero"]["file"]),
                         self.evidence["hero"]["sha256"])
        self.assertEqual(sha(ROOT/"assets/img/products/unitree/catalog/24_a2.png"),
                         "a23bf74444db86dacfc01192dee7144a6cfcc01b8b7523cb6d8bd0795bb03096")
        for item in self.evidence["media"]:
            with self.subTest(image=item["file"]):
                actual=ROOT/"assets/img/products/unitree/a2-factory-pilot"/item["file"]
                self.assertTrue(actual.is_file())
                self.assertEqual(sha(actual),item["sha256"])
                self.assertGreater(actual.stat().st_size,12000)
                self.assertEqual(actual.read_bytes()[:2],b"\xff\xd8")
                self.assertTrue(item["source"].startswith("https://www.unitree.com/images/"))

    def test_product_not_added_to_official_master_or_production_html(self):
        catalog=factory.catalog(ROOT)
        self.assertEqual(len(catalog),13)
        self.assertNotIn("unitree-a2",{x["id"] for x in catalog})
        self.assertFalse((ROOT/"products/unitree-a2.html").exists())
        self.assertNotIn("unitree-a2",json.dumps(catalog,ensure_ascii=False))

    def test_preview_exact_from_existing_factory_noindex_and_cta(self):
        original=factory.render(ROOT,self.product,"preview")
        self.assertEqual(original,self.preview,"Preview differs from existing Factory output")
        self.assertIn('data-product-id="unitree-a2"',original)
        self.assertIn('data-product-family="quadruped"',original)
        self.assertIn('<meta name="robots" content="noindex,nofollow">',original)
        self.assertIn('href="/contact.html?product=Unitree%20A2',original)
        self.assertIn('class="brand-logo brand-logo-pc"',original)
        self.assertIn('class="brand-logo brand-logo-sp"',original)
        self.assertIn('aria-controls="nav"',original)
        self.assertIn('aria-label="グローバルナビゲーション"',original)
        self.assertIn("service=industrial-poc",original)
        self.assertNotIn("Google Analytics",original)
        self.assertEqual(original.count("unitree-a2-maker-0"),8)  # 5 media + 3 CTA

    def test_a2_repeatable_and_footer_build_parity(self):
        from build_site import build_html
        one=factory.render(ROOT,self.product,"preview")
        two=factory.render(ROOT,self.product,"preview")
        self.assertEqual(one, (PILOT/"preview.html").read_text(encoding="utf-8"))
        self.assertEqual(one,two)
        self.assertEqual(one,self.preview)
        built=build_html(one,Path("products/unitree-a2.html"))
        for text in (one,built):
            self.assertEqual(text.count('data-aa8-menu-runtime="true"'),1)
            self.assertIn("focusInNav && button instanceof HTMLButtonElement",text)
            self.assertEqual(text.count('data-aa8-footer-layout="true"'),1)
            self.assertIn('class="aa8-main-logo"',text)
            self.assertIn('class="footer-links"',text)
            self.assertIn('class="footer-utility-links"',text)
            self.assertIn('© AirAdmin8 Inc. All rights reserved.',text)
            self.assertIn('noindex,nofollow',text)
            self.assertNotIn('analytics-events.js',text)
            self.assertNotIn('assets/js/site.js',text)

    def test_standard_model_excludes_pro_only_specs(self):
        p=self.product
        specs=" ".join(x["value"] for x in p["pageFactory"]["specifications"])
        self.assertIn("LiDAR 1基",specs)
        self.assertIn("A2-PROはLiDAR 2基",specs)
        self.assertIn("25 kg",specs)
        self.assertIn("100 kg",specs)
        self.assertIn("メーカー条件下",specs)
        self.assertIn("要確認",specs)

    def test_release_candidate_refused_even_with_valid_source(self):
        with self.assertRaisesRegex(factory.ContractError,"releaseReady"):
            factory.render(ROOT,self.product,"candidate")

    def test_source_evidence_missing_is_hold(self):
        broken=dict(self.evidence["qualification"]["candidate"])
        broken.pop("safety")
        with self.assertRaisesRegex(ValueError,"safety"):
            validate_new_candidate("quadruped",broken,ROOT)

if __name__=="__main__":
    unittest.main()
