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
