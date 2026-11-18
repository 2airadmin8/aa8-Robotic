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
