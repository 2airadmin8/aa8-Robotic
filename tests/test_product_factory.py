"""Product Page Factory: catalog, CEO design contract, generator and safety negatives."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from product_factory import (  # noqa: E402
    ContractError, audit_catalog, catalog, local_asset, official_url,
    render, validate_approved_contract, validate_page_factory,
    IMAGE_EXT,
)
from product_factory_fixture import sample_product  # noqa: E402


class ProductFactoryContractTests(unittest.TestCase):
    def setUp(self):
        self.item = sample_product()

    def test_current_master_all_11_products_audit(self):
        errors, warnings, stats = audit_catalog(ROOT)
        self.assertEqual(errors, [])
        self.assertGreaterEqual(stats["products"], 11)
        self.assertTrue(any("placeholder image" in warning for warning in warnings))

    def test_h2x_ceo_design_contract_approved_assets(self):
        h2x = next(p for p in catalog(ROOT) if p["id"] == "unitree-h2-x")
        self.assertEqual(h2x["designContract"]["template"], "g1-approved-v1")
        validate_approved_contract(ROOT, h2x)

    def test_h2x_contract_rejects_wrong_image(self):
        h2x = copy.deepcopy(next(p for p in catalog(ROOT) if p["id"] == "unitree-h2-x"))
        h2x["designContract"]["ctaImages"][1] = "assets/img/products/unitree/catalog/28_g1.png"
        with self.assertRaises(ContractError):
            validate_approved_contract(ROOT, h2x)

    def test_h2x_contract_rejects_missing_video(self):
        h2x = copy.deepcopy(next(p for p in catalog(ROOT) if p["id"] == "unitree-h2-x"))
        h2x["designContract"]["videos"][0] = "assets/img/products/unitree/h2x/drive/not-real.mp4"
        with self.assertRaises(ContractError):
            validate_approved_contract(ROOT, h2x)

    def test_generate_preview_noindex_and_sanitized_links(self):
        text = render(ROOT, self.item, "preview")
        self.assertIn('name="robots" content="noindex,nofollow"', text)
        self.assertIn('data-product-factory="g1-v1"', text)
        self.assertIn('g1-cta-grid', text)
        self.assertEqual(text.count('class="g1-cta-card"'), 3)
        self.assertIn('name="description"', text)
        self.assertIn('property="og:image"', text)
        self.assertIn('href="/contact.html?product=QA%20Fixture%20Robot&amp;service=university-procurement"', text)
        self.assertIn('g1-factory-v1.css', text)
        self.assertNotIn("¥", text)

    def test_release_candidate_requires_explicit_ready(self):
        with self.assertRaises(ContractError):
            render(ROOT, self.item, "candidate")
        self.item["pageFactory"]["releaseReady"] = True
        text = render(ROOT, self.item, "candidate")
        self.assertNotIn('name="robots" content="noindex', text)
        self.assertIn("QA Fixture Robot", text)

    def test_unsupported_external_or_missing_asset_rejected(self):
        with self.assertRaises(ContractError):
            official_url("javascript:alert(1)", "bad")
        with self.assertRaises(ContractError):
            local_asset(ROOT, "assets/../../etc/passwd", "bad", IMAGE_EXT)
        with self.assertRaises(ContractError):
            local_asset(ROOT, "assets/img/does-not-exist.jpg", "missing", IMAGE_EXT)

    def test_missing_fact_evidence_blocks(self):
        del self.item["pageFactory"]["facts"][0]["sourceUrl"]
        with self.assertRaises(ContractError):
            validate_page_factory(ROOT, self.item)

    def test_placeholder_cannot_be_generated_as_official(self):
        self.item["imageStatus"] = "placeholder"
        with self.assertRaises(ContractError):
            render(ROOT, self.item, "preview")

    def test_malicious_copy_escaped(self):
        self.item["summary"] = "<script>alert(1)</script>"
        text = render(ROOT, self.item, "preview")
        self.assertNotIn("<script>alert(1)</script>", text)
        self.assertIn("&lt;script&gt;", text)

    def test_cta_indexes_reject_duplicates_or_bad(self):
        self.item["pageFactory"]["ctaImageIndexes"] = [0, 2, 88]
        with self.assertRaises(ContractError):
            validate_page_factory(ROOT, self.item)

    def test_legacy_go2_canonical_alias_preserved(self):
        go2 = next(p for p in catalog(ROOT) if p["id"] == "unitree-go2-edu")
        self.assertEqual(go2["detailPage"], "products/unitree-go2.html")


    def test_generated_page_inherits_master_seo(self):
        from unittest.mock import patch
        import inject_static_meta
        with patch("product_factory.catalog", return_value=[self.item, *catalog(ROOT)]):
            seo = inject_static_meta.load_product_seo()
        item = seo["products/factory-qa.html"]
        self.assertEqual(item["image"], self.item["image"])
        self.assertEqual(item["title"], self.item["pageFactory"]["title"])
        self.assertIn("QA-only", item["description"])

    def test_generated_page_uses_existing_analytics_not_legacy_seo(self):
        from build_site import build_html
        generated = render(ROOT, self.item, "preview")
        rebuilt = build_html(generated, Path("products/factory-qa.html"))
        self.assertIn("analytics-events.js", rebuilt)
        self.assertNotIn('src="../assets/js/seo.js', rebuilt)
        self.assertIn('content="noindex,nofollow"', rebuilt)
        self.assertIn('data-shared-layout="footer"', rebuilt)

    def test_structured_page_name_from_existing_master(self):
        from unittest.mock import patch
        import inject_structured_data
        source = render(ROOT, self.item, "preview")
        with patch("product_factory.catalog", return_value=[self.item, *catalog(ROOT)]):
            result = inject_structured_data.process_html(source, Path("products/factory-qa.html"))
        self.assertIn('"name":"QA Fixture Robot"', result)
        self.assertIn('id="page-schema"', result)

    def test_explicit_boolean_release_required(self):
        self.item["pageFactory"]["releaseReady"] = 1
        with self.assertRaises(ContractError):
            render(ROOT, self.item, "candidate")

    def test_each_claim_source_is_rendered(self):
        source = render(ROOT, self.item, "preview")
        self.assertGreaterEqual(source.count("仕様出典 ↗"), 3)
        self.assertGreaterEqual(source.count("出典 ↗"), 5)


    def test_no_video_product_copy_is_consistent(self):
        from copy import deepcopy
        item = deepcopy(self.item)
        item["pageFactory"]["videos"] = []
        item["pageFactory"]["videoAvailability"] = "not_provided_by_manufacturer"
        source = render(ROOT, item, "preview")
        for label in ("公式写真を見る", "公式写真</a>", "公式写真</h2>",
                      "製品写真と公式仕様を確認し", "画像出典"):
            self.assertIn(label, source)
        for wrong in ("公式写真・動画を見る", "写真・動画</a>", "画像・動画出典",
                      "動きを見て、仕様を比べ"):
            self.assertNotIn(wrong, source)
        self.assertNotIn("<video ", source)
        self.assertIn("検証可能な動画がありません", source)
        self.assertIn('href="https://www.unitree.com/H2-X/"', source)

    def test_real_h2plus_has_no_fake_video_claims(self):
        item = next(p for p in catalog(ROOT) if p["id"] == "unitree-h2-plus")
        source = (ROOT / item["detailPage"]).read_text(encoding="utf-8")
        self.assertEqual(item["pageFactory"]["videos"], [])
        self.assertIn("検証可能な動画がありません", source)
        # Previously shipped HTML still has old misleading CTA copy:
        # check the new renderer output rather than rewriting production here.
        generated = render(ROOT, item, "candidate")
        self.assertIn("公式写真を見る", generated)
        self.assertNotIn("公式写真・動画を見る", generated)

    def test_video_product_retains_media_labels(self):
        source = render(ROOT, self.item, "preview")
        self.assertIn("公式写真・動画を見る", source)
        self.assertIn("写真・動画</a>", source)
        self.assertIn("画像・動画出典", source)
        self.assertIn("動きを見て、仕様を比べ", source)

if __name__ == "__main__":
    unittest.main()
