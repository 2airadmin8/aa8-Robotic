"""Ensure customer-facing product status never advertises internal blockers."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BAD = ("取扱条件確認中", "構成確認中", "取扱準備中", "条件確認中", "候補整理中")

class CustomerFacingProductCopy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.products=json.loads((ROOT/"data/products.json").read_text(encoding="utf-8"))["products"]
        cls.manufacturers=json.loads((ROOT/"data/manufacturers.json").read_text(encoding="utf-8"))["manufacturers"]

    def test_all_public_labels_positive(self):
        for product in self.products:
            if product.get("visibility")!="public":continue
            with self.subTest(product=product["id"]):
                label=product["statusLabel"]
                self.assertTrue(label.strip())
                self.assertFalse(any(x in label for x in BAD))
                self.assertNotIn("在庫あり",label)
                self.assertNotIn("即納",label)

    def test_internal_availability_state_retained(self):
        for item in self.products:
            with self.subTest(product=item["id"]):
                if item.get("status")=="preparing":
                    self.assertEqual(item["salesStatus"],"not_released")
                if item.get("status")=="researching":
                    self.assertEqual(item["salesStatus"],"confirmation_required")

    def test_manufacturer_labels_and_public_html(self):
        for item in self.manufacturers:
            with self.subTest(manufacturer=item["id"]):
                self.assertFalse(any(x in item["statusLabel"] for x in BAD))
        for path in [ROOT/"products.html",ROOT/"manufacturers.html",ROOT/"faq.html",*sorted((ROOT/"products").glob("*.html"))]:
            with self.subTest(page=path.name):
                html=path.read_text(encoding="utf-8")
                self.assertFalse(any(x in html for x in BAD),path.name)

    def test_product_cards_and_comparison_use_customer_labels(self):
        site=(ROOT/"assets/js/site.js").read_text(encoding="utf-8")
        compare=(ROOT/"assets/js/product-compare.js").read_text(encoding="utf-8")
        self.assertIn("item.statusLabel",site)
        self.assertIn("item.statusLabel",compare)
        self.assertIn("製品情報・ご相談",compare)

    def test_no_unauthorized_pdfs_or_false_stock_claim(self):
        for p in ("products/unitree-h2-plus.html","products/agibot-a3-ultra.html"):
            content=(ROOT/p).read_text(encoding="utf-8")
            self.assertNotIn('data-document-type="product-catalog"',content)
            self.assertNotIn("在庫あり",content)
