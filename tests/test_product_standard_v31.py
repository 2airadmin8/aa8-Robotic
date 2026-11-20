"""Additive V3.1 contract: 13 pages and original product-specific value."""
from __future__ import annotations
import html
import json
import sys
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from product_page_standard_v31 import (
    BRIDGE_START, TARGET, Structure, bridge, check_master, transform, validate_transformed
)


class ProductStandardV31Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.products = json.loads((ROOT / "data/products.json").read_text(encoding="utf-8"))["products"]
        cls.by_id = {p["id"]: p for p in cls.products}

    def test_13_distinct_master_ids_and_families(self):
        self.assertEqual(len(self.products), 13)
        self.assertEqual(len(self.by_id), 13)
        families = [p["pageStandard"]["family"] for p in self.products]
        self.assertEqual(families.count("quadruped"), 1)
        self.assertEqual(families.count("humanoid"), 8)
        self.assertEqual(families.count("mobile-manipulation"), 4)

    def test_shared_modules_match_source_and_are_idempotent(self):
        for product in self.products:
            with self.subTest(product=product["id"]):
                source = check_master(product).read_text(encoding="utf-8")
                validate_transformed(source, product)
                self.assertEqual(transform(source, product), source)
                self.assertEqual(source.count(TARGET), 1)
                self.assertEqual(source.count("data-product-family="), 1)
                self.assertIn('data-product-id="' + product["id"] + '"', source)

    def test_sparse_pages_share_resource_support_bridge_without_new_cta(self):
        wanted = {p["id"] for p in self.products if p["pageStandard"]["showBridge"]}
        self.assertEqual(wanted, {
            "agibot-g2", "unitree-g1-d", "unitree-h2-d",
            "limx-oli", "unitree-go2-edu", "tianji-marvin", "agibot-a3-ultra"
        })
        for product in self.products:
            text = check_master(product).read_text(encoding="utf-8")
            present = BRIDGE_START in text
            self.assertEqual(present, product["pageStandard"]["showBridge"])
            if present:
                self.assertIn('href="' + html.escape(product["pageStandard"]["resourcesHref"], quote=True) + '"', text)
                self.assertIn('href="' + html.escape(product["pageStandard"]["supportHref"], quote=True) + '"', text)
                self.assertNotIn('contact.html', bridge(product))  # Existing CTA remains sole consult CTA.

    def test_original_high_value_sections_preserved(self):
        expected = {
            "unitree-g1": ["capabilities", "research", "models", "architecture"],
            "agibot-x2-edu": ["assembly", "development", "purchase-flow"],
            "unitree-g1-d": ["workflow", "training"],
            "unitree-h2-d": ["models", "development"],
            "unitree-h2-plus": ["development", "solutions", "introduction"],
        }
        for pid, sections in expected.items():
            parser = Structure()
            parser.feed(check_master(self.by_id[pid]).read_text(encoding="utf-8"))
            for section in sections:
                self.assertIn(section, parser.ids, f"{pid}: {section}")

    def test_no_forced_model_comparison_or_model_homogenization(self):
        h2 = check_master(self.by_id["unitree-h2-plus"]).read_text(encoding="utf-8")
        x2 = check_master(self.by_id["agibot-x2-edu"]).read_text(encoding="utf-8")
        g1 = check_master(self.by_id["unitree-g1"]).read_text(encoding="utf-8")
        self.assertNotIn('id="model-selection"', h2)
        self.assertIn('id="assembly"', x2)
        self.assertIn('id="models"', g1)

    def test_normalized_product_cta_keeps_original_intent_and_approved_contract(self):
        for product in self.products:
            with self.subTest(product=product["id"]):
                parser=Structure()
                parser.feed(check_master(product).read_text(encoding="utf-8"))
                for url in parser.contact_links:
                    parts=urlsplit(url)
                    if not parts.path.endswith("/contact.html"):continue
                    query=parse_qs(parts.query)
                    if "product" not in query: continue
                    if not product.get("designContract"):
                        self.assertEqual(query.get("maker"), [product["manufacturerName"]])
                    else:
                        # CEO-approved H2-X generic CTA must retain its maker provenance.
                        self.assertEqual(query.get("maker"), [product["manufacturerName"]])

    def test_v3_sdk_copy_comes_from_product_master_not_hardcoded_vendor(self):
        factory_source=(ROOT / "scripts/product_factory.py").read_text(encoding="utf-8")
        self.assertIn('developerDocsLabel',factory_source)
        self.assertIn('developerDocsCaution',factory_source)
        self.assertIn('resourceLinkLabel',factory_source)
        self.assertNotIn('Unitree H2 Developer Documentation（公式）',factory_source)
        self.assertNotIn('この資料はH2向けです。',factory_source)
        h2=self.by_id["unitree-h2-plus"]["pageFactory"]["v3"]
        self.assertEqual(h2["developerDocsLabel"],"Unitree H2 Developer Documentation（公式）")

    def test_factory_products_generated_source_parity(self):
        import product_factory
        for product in self.products:
            if product.get("pageFactory"):
                with self.subTest(product=product["id"]):
                    actual=check_master(product).read_text(encoding="utf-8")
                    self.assertEqual(product_factory.render(ROOT,product,"candidate"),actual)


if __name__=="__main__":
    unittest.main()
