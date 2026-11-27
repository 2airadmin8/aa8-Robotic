"""QG-V1: validate the sole machine-checkable UI contract and its safety boundary."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from factory_gate_router import discover
from factory_autofix_policy import UI_AUTOFIX_FILES, UI_SCOPES, validate_patch

CONTRACT = ROOT / "docs/governance/hp-ui-quality-contract-v1.json"
class QualityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text("utf-8"))

    def test_references_existing_Figma_and_Corporate_without_claiming_pixel_approval(self):
        c=self.contract
        self.assertEqual(c["schemaVersion"], "aa8-ui-quality-contract-v1")
        self.assertEqual(c["type"], "CI_MACHINE_CHECKABLE_CONTRACT_NOT_FIGMA_PIXEL_APPROVAL")
        for key in ("designTrace","corporateTokens","motherSite"):
            self.assertTrue((ROOT/c["authorities"][key]).is_file(),key)
        self.assertTrue(c["authorities"]["referenceFigma"].startswith("https://www.figma.com/"))
        token=json.loads((ROOT/c["authorities"]["corporateTokens"]).read_text("utf-8"))
        self.assertEqual(token["color"]["surface"]["page"]["$value"],"#FFFFFF")
        self.assertEqual(c["protectedApprovals"]["manualVisualFigma"],"HOLD_UNLESS_SEPARATELY_APPROVED")
        self.assertEqual(c["protectedApprovals"]["writing"],"CEO_APPROVED_ITEM_IDS_REQUIRED")

    def test_five_viewports_unique_pages_and_all_rules_traced(self):
        c=self.contract
        self.assertEqual(c["mandatoryViewports"],[1440,1280,640,390,360])
        pages=c["pageMatrix"]
        self.assertGreaterEqual(len(pages),10)
        self.assertEqual(len({p["path"] for p in pages}),len(pages))
        self.assertEqual(pages[0]["path"],"index.html")
        self.assertEqual(pages[0]["category"],"home")
        self.assertTrue(pages[0]["requireHomeCards"])
        for item in pages:
            with self.subTest(path=item["path"]):
                self.assertFalse(item["path"].startswith("/"))
                self.assertNotIn("..",Path(item["path"]).parts)
                self.assertTrue((ROOT/item["path"]).is_file())
                self.assertIn(item["category"],{"home","product","hub"})
        rules=c["rules"]
        self.assertEqual([r["id"] for r in rules],["QG-%02d"%i for i in range(1,9)])
        self.assertEqual(c["maxAutoRepair"],3)
        self.assertEqual(c["mobileHeroMinCtaHeightPx"],44)
        self.assertGreaterEqual(c["caseCtaMinContrast"],4.5)
        self.assertEqual(c["maxHorizontalOverflowPx"],1)

    def test_home_model_names_match_the_real_master(self):
        c=self.contract
        names=c["makerBadges"]["cardIds"]
        actual=c["makerBadges"]["expectedMakers"]
        self.assertEqual(len(names),3)
        self.assertEqual(len(set(names)),3)
        master=json.loads((ROOT/"data/products.json").read_text("utf-8"))
        found={p["id"]:p for p in master["products"]}
        self.assertTrue(set(names)<=set(found))
        self.assertEqual(actual,["Unitree","AgiBot","Unitree"])

    def test_shared_ui_changes_cannot_silently_skip_independent_qa(self):
        tests=["assets/css/product-cards-v2.css","assets/js/product-cards-v2.js",
               "index.html","tests/hub-pages-visual.spec.js"]
        for item in tests:
            result=discover(ROOT,[item])
            self.assertIn(result["work_scope"],UI_SCOPES)
            self.assertTrue(result["home_ui_regression_required"])
        for item in ("includes/site-header.html","includes/site-footer.html","assets/css/shared-layout.css"):
            result=discover(ROOT,[item])
            self.assertEqual(result["work_scope"],"GLOBAL_FACTORY")

    def test_ai_cannot_modify_tests_fact_sources_or_release_policy_to_hide_failures(self):
        for source in ("tests/hub-pages-visual.spec.js","tests/ui-quality-contract.spec.js",
                       "assets/js/product-cards-v2.js","assets/js/seo.js",
                       "data/products.json","data/case-evidence.json",
                       ".github/workflows/ci.yml","scripts/factory_autofix_policy.py"):
            with self.subTest(source=source):
                self.assertNotIn(source,UI_AUTOFIX_FILES)
                content=(f"diff --git a/{source} b/{source}\n"
                         f"--- a/{source}\n+++ b/{source}\n"
                         "@@ -1 +1 @@\n-x\n+y\n").encode()
                with self.assertRaises(ValueError):
                    validate_patch(content,scope="UI_SHARED")
        self.assertTrue({"assets/css/home-hero.css","assets/css/product-cards-v2.css"}<=set(UI_AUTOFIX_FILES))

    def test_same_ci_runs_quality_browser_and_preserves_exact_sha_evidence(self):
        c=(ROOT/".github/workflows/ci.yml").read_text("utf-8")
        self.assertIn("tests/ui-quality-contract.spec.js",c)
        self.assertIn("ui-quality-evidence-",c)
        independent=c.split("- name: Independent UI final-artifact browser QA",1)[1].split("- name: Download exact-HEAD A2",1)[0]
        self.assertIn("factory_scope == 'GLOBAL_FACTORY'",independent)
        self.assertIn("tests/ui-quality-contract.spec.js",independent)
        self.assertIn("QG_HOLD: missing exact HEAD viewport report",c)
        self.assertIn("ui-quality-evidence/summary.json",c) if "ui-quality-evidence/summary.json" in c else self.assertIn('out/"summary.json"',c)
        self.assertIn("PR_HEAD_SHA",c)
        self.assertIn("ai-autofix-propose:",c)
        self.assertIn("AA8_FACTORY_AUTOFIX_ENABLED",c)
        self.assertIn("AA8_UI_AUTOFIX_ENABLED",c)
        self.assertIn("workflow_dispatch:",(ROOT/".github/workflows/pages.yml").read_text("utf-8"))
        self.assertNotIn("production: AUTO_APPROVED",c)

if __name__=="__main__":
    unittest.main()
