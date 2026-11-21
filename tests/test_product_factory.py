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

    def test_current_master_all_13_products_audit(self):
        errors, warnings, stats = audit_catalog(ROOT)
        self.assertEqual(errors, [])
        self.assertEqual(stats["products"], 13)
        self.assertFalse(any("placeholder image" in warning for warning in warnings),
                         "all five manufacturer-image replacements must be verified")
        for pid in ("agibot-g2", "agibot-x2-edu", "limx-oli", "unitree-go2-edu", "tianji-marvin"):
            product = next(p for p in catalog(ROOT) if p["id"] == pid)
            self.assertEqual(product["imageStatus"], "official", pid)
            self.assertTrue((ROOT / product["image"]).is_file(), pid)
            self.assertTrue(product.get("imageSourcePage"), pid)

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
        self.assertIn('class="brand-logo brand-logo-pc"', text)
        self.assertIn('class="brand-logo brand-logo-sp"', text)
        self.assertIn('aria-label="グローバルナビゲーション"', text)
        self.assertIn('class="menu" type="button"', text)
        self.assertEqual(text.count('data-shared-layout="header"'), 1)
        self.assertNotIn('<script src="/assets/js/site.js" defer></script>', text)
        self.assertIn('aria-expanded', text)
        self.assertNotIn("¥", text)

    def test_shared_footer_raw_and_build_parity_no_tracking(self):
        from build_site import build_html
        from pathlib import Path
        preview = render(ROOT, self.item, "preview")
        built = build_html(preview, Path("products/qa-factory-preview.html"))
        for html in (preview, built):
            self.assertEqual(html.count('data-shared-layout="header"'), 1)
            self.assertEqual(html.count('<footer class="footer" data-shared-layout="footer">'), 1)
            self.assertEqual(html.count('data-aa8-menu-runtime="true"'), 1)
            # V3.3 fixes the actual bug: one Footer shell, four reusable columns,
            # and zero inline style overrides that bypass the common CSS owner.
            self.assertEqual(html.count('data-aa8-footer-layout="true"'), 0)
            self.assertEqual(html.count('class="footer-shell"'), 1)
            self.assertEqual(html.count('class="footer-links__column"'), 4)
            self.assertEqual(html.count('class="footer-links__title"'), 4)
            self.assertIn('class="aa8-main-logo"', html)
            self.assertIn('class="footer-links"', html)
            self.assertIn('class="footer-utility-links"', html)
            self.assertIn('aria-label="フッターナビゲーション"', html)
            self.assertIn('© AirAdmin8 Inc. All rights reserved.', html)
            self.assertIn('name="robots" content="noindex,nofollow"', html)
            self.assertNotIn('assets/js/site.js', html)
            self.assertNotIn('analytics-events.js', html)
            self.assertNotIn('seo.js', html)
        self.assertIn('href="/contact.html"', preview)
        self.assertIn('href="../contact.html"', built)

    def test_preview_fails_closed_on_unexpected_template_analytics(self):
        from unittest.mock import patch
        import tempfile
        import product_factory

        original = product_factory.TEMPLATE.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            altered = Path(tmp) / "factory-template.html"
            for bad in (
                '<script async src="/assets/js/site.js"></script>',
                '<script src="/assets/js/analytics-events.js"></script>',
                '<script src="https://www.googletagmanager.com/gtag/js"></script>',
                '<script>gtag("config","G-TEST");</script>',
            ):
                with self.subTest(bad=bad):
                    altered.write_text(
                        original.replace("</body>", bad + "</body>"),
                        encoding="utf-8",
                    )
                    with patch.object(product_factory, "TEMPLATE", altered):
                        with self.assertRaisesRegex(
                            ContractError, "production tracking|production analytics"
                        ):
                            render(ROOT, self.item, "preview")

    def test_preview_shared_menu_and_footer_cannot_be_duplicated(self):
        from unittest.mock import patch
        import tempfile
        import product_factory

        original = product_factory.TEMPLATE.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            altered = Path(tmp) / "factory-template.html"
            for bad in (
                '<script data-aa8-menu-runtime="true"></script>',
                '<footer class="footer" data-shared-layout="footer"></footer>',
            ):
                with self.subTest(bad=bad):
                    altered.write_text(
                        original.replace("</body>", bad + "</body>"),
                        encoding="utf-8",
                    )
                    with patch.object(product_factory, "TEMPLATE", altered):
                        with self.assertRaisesRegex(
                            ContractError, "exactly one"
                        ):
                            render(ROOT, self.item, "preview")

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
        preview = build_html(render(ROOT, self.item, "preview"), Path("products/factory-qa.html"))
        self.assertNotIn("analytics-events.js", preview)
        self.assertNotIn("seo.js", preview)
        self.assertIn('content="noindex,nofollow"', preview)
        self.assertIn('data-shared-layout="footer"', preview)
        self.item["pageFactory"]["releaseReady"] = True
        candidate = build_html(render(ROOT, self.item, "candidate"), Path("products/factory-qa.html"))
        self.assertIn("analytics-events.js", candidate)
        self.assertNotIn('src="../assets/js/seo.js', candidate)
        self.assertNotIn('content="noindex,nofollow"', candidate)

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
        # Sales cards must stay clean; verified maker URLs remain in source data
        # and the official manufacturer resources link stays visible.
        self.assertNotIn("仕様出典 ↗", source)
        self.assertGreaterEqual(source.count("出典 ↗"), 3)
        self.assertIn(self.item["pageFactory"]["officialSource"], source)


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


class TwoNewRealSkuMakerSourceRegression(unittest.TestCase):
    """Only actual official B2/R1 raw model cells may enter a preview candidate."""

    def setUp(self):
        import json
        import maker_spec_watch as maker
        self.maker = maker
        self.contracts = {}
        self.products = {}
        for pid in ("unitree-b2",):
            directory = ROOT / "tests" / "fixtures" / (pid + "-new-real-pilot")
            self.contracts[pid] = json.loads(
                (directory / "maker-live-contract.json").read_text("utf-8"))
            self.products[pid] = json.loads((directory / "product.json").read_text("utf-8"))

    @staticmethod
    def offline_source_html(contract):
        from html import escape
        name = contract["models"]
        if name == ["B2"]:
            entries = []
            for row in contract["categories"][0]["rows"]:
                entries.append('<li><div class="name">' +
                    escape(row["source_label"]) + '</div><div class="value"><p>' +
                    escape(row["models"]["B2"]) + '</p></div></li>')
            return ('<ul class="parameter b2">' + "".join(entries) + '</ul>').encode()
        raise AssertionError("Unsupported family under this B2-only pilot")

    def test_full_real_model_grid_round_trip_offline(self):
        for pid, size, cells in (("unitree-b2", 19, 19),):
            with self.subTest(pid=pid):
                contract = self.contracts[pid]
                actual = self.maker.parse_source(self.offline_source_html(contract), contract)
                self.assertEqual(sum(len(g["rows"]) for g in actual["categories"]), size)
                self.assertEqual(len(self.maker.flatten(actual)), cells)
                self.assertEqual(self.maker.compare(actual, contract), [])
                self.maker.verify_display(self.products[pid], contract, actual)
                self.assertFalse(self.products[pid]["pageFactory"]["releaseReady"])
                html = render(ROOT, self.products[pid], "preview")
                self.assertIn('content="noindex,nofollow"', html)
                self.assertIn('data-product-factory="g1-v1"', html)

    def test_missing_row_and_wrong_model_cell_fail_closed(self):
        for pid in ("unitree-b2",):
            contract = self.contracts[pid]
            original = self.offline_source_html(contract)
            parsed = self.maker.parse_source(original, contract)
            import copy
            changed = copy.deepcopy(parsed)
            model = contract["models"][0]
            changed["categories"][0]["rows"][0]["models"][model] = "UNVERIFIED 999"
            self.assertEqual(len(self.maker.compare(changed, contract)), 1, pid)
            changed = copy.deepcopy(parsed)
            changed["categories"][0]["rows"].pop()
            with self.assertRaisesRegex(ValueError, "SOURCE_HOLD"):
                self.maker.compare(changed, contract)

    def test_wrong_maker_url_or_unrecognized_adapter_is_rejected(self):
        import copy
        for pid in ("unitree-b2",):
            original = self.contracts[pid]
            contract = copy.deepcopy(original)
            contract["source_url"] = "https://www.unitree.com/A2/"
            with self.assertRaisesRegex(ValueError, "SOURCE_HOLD"):
                self.maker.enforce_source_trust(contract)
            contract = copy.deepcopy(original)
            contract["adapter"] = "unregistered-maker-parser-v1"
            with self.assertRaisesRegex(ValueError, "SOURCE_HOLD"):
                self.maker.enforce_source_trust(contract)



class StrictV33QuadrupedDesignContractQA(unittest.TestCase):
    """Genuine new SKU must meet its buyer, family, visual and source contracts."""

    @classmethod
    def setUpClass(cls):
        import json
        cls.product=json.loads((ROOT/"tests/fixtures/unitree-b2-new-real-pilot/product.json").read_text("utf-8"))

    def test_all_modules_have_buyer_content_and_correct_render_order(self):
        item=copy.deepcopy(self.product)
        validate_page_factory(ROOT,item)
        page=render(ROOT,item,"preview")
        required_ids=["capabilities","applications","decision-checks","media",
                      "specifications","development","solutions","introduction",
                      "faq","related","contact-product"]
        positions=[page.index('id="'+s+'"') for s in required_ids]
        self.assertEqual(positions,sorted(positions),"V3.3 buyer reading order cannot drift")
        self.assertIn('data-page-design-v33="strict"',page)
        self.assertIn('data-aa8-visual-version="3.3"',page)
        self.assertIn('class="aa8-corporate-v1"',page)
        self.assertIn('product-standard-v33.css',page)
        self.assertIn('fonts.googleapis.com',page)
        self.assertEqual(page.count('class="g1-factory-decision-grid"'),1)
        self.assertIn("積載・機体構成",page)
        self.assertIn("通信・取得データ",page)
        self.assertIn("安全・運用責任",page)
        self.assertEqual(page.count('class="g1-cta-card"'),3)
        self.assertIn('scope="col">仕様項目',page)
        self.assertIn("メーカー公表値",page)
        self.assertNotIn("非公開プレビュー",page)
        self.assertNotIn("メーカー製品画像。",page)
        self.assertNotIn("仕様出典 ↗",page)
        self.assertIn('name="robots" content="noindex,nofollow"',page)
        self.assertNotIn('data-gtm',page)
        self.assertTrue(item["pageFactory"]["releaseReady"] is False)

    def test_missing_required_v33_content_is_rejected(self):
        for mutation in ("missing-v3","missing-autonomy","missing-safety",
                         "missing-sdk","missing-process","wrong-family",
                         "redundant-bridge","dev-only-hero","unrelated-product"):
            item=copy.deepcopy(self.product)
            spec=item["pageFactory"]
            if mutation=="missing-v3": spec.pop("v3")
            elif mutation=="missing-autonomy": spec["familyEvidence"].pop("autonomy")
            elif mutation=="missing-safety": spec["familyEvidence"].pop("safety")
            elif mutation=="missing-sdk": spec["v3"]["sdk"]=[]
            elif mutation=="missing-process": spec["v3"]["process"]=[]
            elif mutation=="wrong-family": item["pageStandard"]["family"]="humanoid"
            elif mutation=="redundant-bridge": item["pageStandard"]["showBridge"]=True
            elif mutation=="dev-only-hero": spec["heroLead"]="メーカー公開資料に基づき、非公開プレビュー"
            elif mutation=="unrelated-product": spec["relatedProductIds"]=["unitree-g1"]
            with self.subTest(mutation=mutation):
                with self.assertRaisesRegex(ContractError, "V3.3|quadruped|family|hero|unrelated"):
                    validate_page_factory(ROOT,item)

    def test_one_relevant_related_model_no_fabricated_three(self):
        item=copy.deepcopy(self.product)
        self.assertEqual(item["pageFactory"]["relatedProductIds"],["unitree-go2-edu"])
        page=render(ROOT,item,"preview")
        self.assertEqual(page.count('class="g1-factory-related-card"'),1)
        self.assertIn("Unitree Go2 EDU",page)
        self.assertNotIn("Unitree H2-D",page)


if __name__ == "__main__":
    unittest.main()
