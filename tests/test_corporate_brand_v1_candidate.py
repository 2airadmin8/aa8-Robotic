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

if __name__=="__main__":
    unittest.main()
