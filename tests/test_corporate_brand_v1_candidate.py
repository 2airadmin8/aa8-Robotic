"""Candidate brand facts must be source-grounded and isolated from production."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]

class CorporateBrandV1CandidateTests(unittest.TestCase):
    def test_corporate_palette_and_font(self):
        css=(ROOT/"ops/brand-preview/corporate-brand-v1.css").read_text(encoding="utf-8")
        for val in ("#0069b5","#009bd2","#00b2bc","#333333","#f4f8fa","Noto Sans JP"):
            self.assertIn(val,css)
        self.assertIn('[data-aa8-brand-preview="corporate-v1"]',css)
        self.assertNotIn("ISMS",css)
    def test_css_and_figma_tokens_match_mother_contract(self):
        import json
        mother=json.loads((ROOT/"ops/brand-preview/mother-site-contract-v1.json").read_text(encoding="utf-8"))
        figma=json.loads((ROOT/"ops/brand-preview/figma-corporate-tokens-v1.json").read_text(encoding="utf-8"))
        css=(ROOT/"assets/css/shared-layout.css").read_text(encoding="utf-8")
        fields={"deepBlue":"deep","primaryBlue":"primary","teal":"teal"}
        for mother_key, figma_key in fields.items():
            value=mother["tokens"][mother_key]
            self.assertEqual(figma["color"]["brand"][figma_key]["$value"].lower(),value.lower())
            self.assertIn(value.lower(),css.lower())
        self.assertEqual(figma["color"]["text"]["body"]["$value"].lower(),mother["tokens"]["bodyInk"].lower())
        self.assertIn("AA8_CORPORATE_BRAND_V1_OPT_IN",css)
        self.assertIn("body.aa8-corporate-v1",css)
        self.assertIn("(max-width:1023px)",css)
        self.assertIn(".menu::before",css)
        self.assertNotIn("aa8-corporate-v1", (ROOT/"index.html").read_text(encoding="utf-8"))
        self.assertNotIn("aa8-corporate-v1", (ROOT/"scripts/templates/g1_factory_v1.html").read_text(encoding="utf-8"))

    def test_one_shared_header_and_accessible_runtime(self):
        header=(ROOT/"includes/site-header.html").read_text(encoding="utf-8")
        script=(ROOT/"assets/js/site.js").read_text(encoding="utf-8")
        self.assertEqual(header.count('class="site-header"'),1)
        self.assertEqual(header.count('class="menu"'),1)
        self.assertIn("menu::before", (ROOT/"assets/css/shared-layout.css").read_text(encoding="utf-8"))
        self.assertIn("aria-controls=\"nav\"",header)
        self.assertIn("aa8-corporate-menu-open",script)
        # Public build injects mobile-qa.js as the capture-phase menu owner.
        deployed=(ROOT/"assets/js/mobile-qa.js").read_text(encoding="utf-8")
        self.assertIn("event.stopImmediatePropagation()",deployed)
        self.assertIn("aa8-corporate-menu-open",deployed)
        self.assertIn("const minDesktop = corporateShell ? 1024 : 981",deployed)
        self.assertIn("event.key !== 'Tab'",deployed)
        self.assertIn("event.key === 'Escape'",script)
        self.assertIn("last.focus()",script)
        self.assertIn("min-width:1024px",script)

    def test_public_build_has_only_external_menu_runtime(self):
        from scripts.build_site import build_html
        from pathlib import Path
        home=(ROOT/"index.html").read_text(encoding="utf-8")
        output=build_html(home,Path("index.html"))
        self.assertNotIn('data-aa8-menu-runtime="true"', output)
        self.assertIn("assets/js/mobile-qa.js",output)

    def test_isolated_factory_preview_keeps_own_runtime(self):
        from scripts.build_site import build_html
        from pathlib import Path
        original=(ROOT/"tests/fixtures/a2-factory/preview.html").read_text(encoding="utf-8")
        self.assertIn('data-product-factory="g1-v1"',original)
        output=build_html(original,Path("a2-factory-preview.html"))
        self.assertEqual(output.count('data-aa8-menu-runtime="true"'),1)
        self.assertNotIn('assets/js/mobile-qa.js',output)

    def test_verified_mother_site_contract_and_menu(self):
        import json
        item=json.loads((ROOT/"ops/brand-preview/mother-site-contract-v1.json").read_text(encoding="utf-8"))
        self.assertEqual(item["status"],"DESIGN_CANDIDATE_ONLY")
        self.assertEqual(item["tokens"]["breakpointMobileMaxPx"],1023)
        self.assertEqual(item["tokens"]["footerNavColumns"],"1.45fr .8fr 1.15fr .75fr")
        self.assertEqual(item["motherMenuLabels"][-1],"お問い合わせ")
        self.assertEqual(len(item["motherFooterSections"]),4)
        self.assertEqual(len(item["sources"]),5)
        self.assertTrue(all(len(s["sha256"])==64 for s in item["sources"]))
        self.assertTrue(item["copyGates"]["currentIsmsStatusMustBeVerified"])
        self.assertEqual(item["ownership"]["shell"],"assets/css/shared-layout.css")
        self.assertEqual(item["ownership"]["menuRuntime"],"assets/js/mobile-qa.js")

    def test_corporate_preview_not_loaded_by_factory_or_public_pages(self):
        tpl=(ROOT/"scripts/templates/g1_factory_v1.html").read_text(encoding="utf-8")
        homepage=(ROOT/"index.html").read_text(encoding="utf-8")
        self.assertNotIn("corporate-brand-v1.css",tpl)
        self.assertNotIn("corporate-brand-v1.css",homepage)
        policy=(ROOT/"docs/governance/AA8_CORPORATE_BRAND_V1_CANDIDATE.md").read_text(encoding="utf-8")
        self.assertIn("INTERNAL_PREVIEW_ONLY",policy)
        self.assertIn("PRODUCTION_HOLD",policy)
        self.assertIn("13-product regression",policy)

    def test_v33_corporate_footer_single_owner(self):
        from scripts.build_site import build_html
        footer=(ROOT/"includes/site-footer.html").read_text("utf-8")
        css=(ROOT/"assets/css/shared-layout.css").read_text("utf-8")
        self.assertEqual(footer.count('<footer class="footer" data-shared-layout="footer">'),1)
        self.assertEqual(footer.count('class="footer-shell"'),1)
        self.assertEqual(footer.count('class="footer-links__column"'),4)
        self.assertEqual(footer.count('class="footer-links__title"'),4)
        self.assertEqual(footer.count('class="footer-links__list"'),4)
        for label in ("製品・サービス","導入・事例","研究・サポート","会社情報"):
            self.assertIn(label,footer)
        for href in ("/products.html","/use-cases.html","/cases.html","/resources.html",
                     "/support.html","/glossary.html","/about.html","/contact.html"):
            self.assertIn('href="'+href+'"',footer)
        self.assertNotIn('<style',footer)
        self.assertNotIn("ISMS/ISO27001",footer)
        self.assertNotIn("千代田区大手町",footer)
        self.assertIn("AA8_MOTHER_R41_FOOTER_V33_SINGLE_OWNER",css)
        for token in ("background: #f4f8fa","width: min(1280px, 94%)","border-radius: 18px",
                      "grid-template-columns: 280px minmax(0,1fr)",
                      "grid-template-columns: 1.45fr .8fr 1.15fr .75fr",
                      "border-radius:14px","grid-template-columns:minmax(0,1fr)"):
            self.assertIn(token,css)
        self.assertNotIn("background: #061923",css)
        home=(ROOT/"index.html").read_text("utf-8")
        built=build_html(home,Path("index.html"))
        self.assertIn('class="footer-shell"',built)
        self.assertEqual(built.count('class="footer-links__title"'),4)
        self.assertEqual(built.count('data-shared-layout="footer"'),1)

    def test_v33_mother_brand_and_white_grey_spec_contract(self):
        import json
        from scripts.build_site import build_html
        mother=json.loads((ROOT/"ops/brand-preview/mother-site-contract-v1.json").read_text(encoding="utf-8"))
        v33=json.loads((ROOT/"ops/brand-preview/corporate-product-visual-v33.json").read_text(encoding="utf-8"))
        css=(ROOT/"assets/css/product-standard-v33.css").read_text(encoding="utf-8")
        foundation=(ROOT/"assets/css/site.css").read_text(encoding="utf-8")
        content=(ROOT/"assets/css/main-site-experience.css").read_text(encoding="utf-8")
        self.assertEqual(v33["schema"],"AA8_CORPORATE_PRODUCT_VISUAL_V3.3")
        self.assertEqual(v33["effectiveDesign"],"3.3")
        self.assertIn("V3.1",v33["contentAndBuyerJourney"])
        self.assertEqual(v33["release"],"NO_GO_UNTIL_ALL_REQUIRED_GATES")
        self.assertIn("FIGMA_NATIVE",v33["status"])
        for mother_key,code_key in (("deepBlue","deep"),("primaryBlue","primary"),("teal","teal"),("bodyInk","body"),("footerSurface","footer")):
            self.assertEqual(v33["brandColors"][code_key].lower(),mother["tokens"][mother_key].lower())
        self.assertEqual(v33["fontFamilies"]["japanese"],mother["tokens"]["fontFamily"])
        for code,color in (("white","#ffffff"),("group","#eeeeee"),("stripe","#f5f5f5"),("border","#d9d9d9"),("ink","#333333")):
            self.assertIn(f"--aa8-v33-spec-{code}: {color}",css)
        self.assertEqual(v33["specTable"]["section"],"#FFFFFF")
        self.assertEqual(v33["specTable"]["category"],"#EEEEEE")
        self.assertEqual(v33["specTable"]["even"],"#F5F5F5")
        self.assertIn('"Noto Sans JP","Montserrat"',foundation)
        self.assertIn("--blue:#009bd2",foundation)
        self.assertIn("--ink:#333333",foundation)
        self.assertIn("--aa8-blue: #009bd2",content)
        self.assertIn("--aa8-ink: #333333",content)
        self.assertIn("main[data-aa8-visual-version=\"3.3\"]",css)
        self.assertIn("#specs .spec-table p:nth-of-type(even)",css)
        self.assertNotIn("ISMS",css)
        product_master=json.loads((ROOT/"data/products.json").read_text(encoding="utf-8"))
        self.assertEqual(len(product_master["products"]),13)
        self.assertTrue(all(p["pageStandard"]["version"]=="3.1" for p in product_master["products"]))
        for product in product_master["products"]:
            relative=Path(product["detailPage"])
            source=(ROOT/relative).read_text(encoding="utf-8")
            built=build_html(source,relative)
            self.assertEqual(built.count('data-aa8-visual-version="3.3"'),1,relative)
            self.assertEqual(built.count("assets/css/product-standard-v33.css"),1,relative)
            self.assertEqual(built.count("fonts.googleapis.com/css2?family=Noto"),1,relative)
            self.assertIn('aa8-corporate-v1',built,relative)
        home=build_html((ROOT/"index.html").read_text(encoding="utf-8"),Path("index.html"))
        self.assertIn('aa8-corporate-v1',home)
        self.assertNotIn("assets/css/product-standard-v33.css",home)
        self.assertNotIn('data-aa8-visual-version="3.3"',home)

if __name__=="__main__":
    unittest.main()
