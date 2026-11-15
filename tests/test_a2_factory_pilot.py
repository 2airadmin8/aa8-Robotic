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
# Existing CI already explicitly loads this A2 test module; reuse it to run
# source-watch regression without modifying the protected workflow YAML.
from test_maker_spec_watch import MakerSourceWatchTests
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

    def test_official_37_parameter_rows_four_categories_two_models(self):
        from collections import Counter
        rows=self.product["pageFactory"]["specifications"]
        contract=self.evidence["official_parameter_table"]
        self.assertEqual(contract["source"],"https://www.unitree.com/A2/")
        self.assertEqual(contract["models"],["A2","A2-PRO"])
        self.assertEqual(len(rows),37)
        groups=[(item["category"],item["count"]) for item in contract["group_counts"]]
        self.assertEqual(groups,[
            ("機械パラメータ",10),("電気特性",15),("性能パラメータ",9),("その他",3)
        ])
        self.assertEqual([(r["category"],r["parameter"]) for r in rows],[
            (group,label) for (group,n),start in zip(groups,[0,10,25,34])
            for label in contract["parameter_labels"][start:start+n]
        ])
        self.assertEqual(len(set(r["parameter"] for r in rows)),37)
        self.assertEqual([Counter(r["category"] for r in rows)[group] for group,n in groups],[10,15,9,3])
        for row in rows:
            self.assertEqual(set(row["models"]),{"A2","A2-PRO"})
            self.assertEqual(row["sourceUrl"],"https://www.unitree.com/A2/")
        official={r["parameter"]:r["models"] for r in rows}
        for field,models in contract["important_model_differences"].items():
            self.assertEqual(official[field],models,field)
        self.assertIn("約25 kg",official["連続歩行積載"]["A2"])
        self.assertIn("約100 kg",official["最大立位静荷重"]["A2"])
        self.assertNotEqual(official["センサー構成"]["A2"],official["センサー構成"]["A2-PRO"])
        self.assertEqual(len(self.product["pageFactory"]["v3"]["models"]),2)

    def test_html_exposes_real_two_model_comparison_all_37_rows(self):
        self.assertEqual(self.preview.count('class="a2-spec-row" data-spec-row="true"'),37)
        self.assertEqual(self.preview.count('class="a2-category-row"'),4)
        self.assertEqual(self.preview.count('data-model="A2"'),37)
        self.assertEqual(self.preview.count('data-model="A2-PRO"'),37)
        self.assertEqual(self.preview.count('id="model-selection"'),1)
        self.assertIn('href="#model-selection"',self.preview)
        self.assertIn("LiDAR ×1＋HDカメラ ×1",self.preview)
        self.assertIn("LiDAR ×2＋HDカメラ ×1",self.preview)
        self.assertIn("IP56～IP67",self.preview)
        self.assertEqual(self.preview.count('data-model-inquiry="A2"'),1)
        self.assertEqual(self.preview.count('data-model-inquiry="A2-PRO"'),1)
        self.assertIn('product=Unitree%20A2&amp;maker=Unitree&amp;service=industrial-poc',self.preview)
        self.assertIn('product=Unitree%20A2-PRO&amp;maker=Unitree&amp;service=industrial-poc',self.preview)

    def test_missing_duplicate_wrong_group_wrong_models_fail_closed(self):
        from copy import deepcopy
        variants=[]
        missing=deepcopy(self.product);missing["pageFactory"]["specifications"].pop()
        variants.append(missing)
        duplicate=deepcopy(self.product);duplicate["pageFactory"]["specifications"][1]["parameter"]=duplicate["pageFactory"]["specifications"][0]["parameter"]
        variants.append(duplicate)
        order=deepcopy(self.product);order["pageFactory"]["specifications"][0]["category"]="その他"
        variants.append(order)
        model=deepcopy(self.product);model["pageFactory"]["specifications"][0]["models"].pop("A2-PRO")
        variants.append(model)
        for candidate in variants:
            with self.subTest(candidate=candidate["pageFactory"]["specifications"][0].get("parameter")):
                with self.assertRaisesRegex(factory.ContractError,"A2 maker|A2 comparison"):
                    factory.render(ROOT,candidate,"preview")

    def test_release_candidate_refused_even_with_valid_source(self):
        with self.assertRaisesRegex(factory.ContractError,"releaseReady"):
            factory.render(ROOT,self.product,"candidate")

    def test_source_evidence_missing_is_hold(self):
        broken=dict(self.evidence["qualification"]["candidate"])
        broken.pop("safety")
        with self.assertRaisesRegex(ValueError,"safety"):
            validate_new_candidate("quadruped",broken,ROOT)

"""Factual A2 Japanese audit tests: separate fixed bilingual reference + official cells."""
import copy
import json
import sys
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import a2_semantic_fact_review as reviewer
import maker_spec_watch as maker

class IndependentA2SemanticFacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=maker.load_contract(ROOT/"tests/fixtures/a2-factory/maker-live-contract.json")
        cls.product=json.loads((ROOT/"tests/fixtures/a2-factory/product.json").read_text("utf-8"))
        cls.parsed={
            "models":cls.contract["models"],
            "categories":[{"name":group["source_name"],
             "rows":[{"source_label":row["source_label"],"models":dict(row["models"])}
                     for row in group["rows"]]}
                    for group in cls.contract["categories"]]
        }

    def test_74_model_cells_match_independently_authored_bilingual_reference(self):
        report=reviewer.evaluate(self.contract,self.product,self.parsed,"synthetic-test-source")
        self.assertEqual(report["status"],"TECH_SEMANTIC_QA_PASS")
        self.assertEqual(report["cells_checked"],74)
        self.assertEqual(len({x["parameter_id"] for x in report["evidence"]}),37)
        self.assertEqual(len(report["errors"]),0)
        self.assertEqual(report["independent_human_review"],"NOT_ATTESTED")
        self.assertEqual(report["production_release"],"HOLD")

    def test_unverified_japanese_semantic_drift_fails_independent_reference(self):
        for i, text in [(5,"12 DoF（各脚3関節）"),
                        (6,"産業用クロスローラーベアリング"),
                        (15,"Wi-Fi 7／Bluetooth 5.2 対応"),
                        (32,"0～3.7 m/s（限界値 約5 m/s）")]:
            with self.subTest(row=i):
                product=copy.deepcopy(self.product)
                product["pageFactory"]["specifications"][i]["models"]["A2"]=text
                report=reviewer.evaluate(self.contract,product,self.parsed,"test")
                self.assertEqual(report["status"],"TECH_SEMANTIC_QA_HOLD")
                self.assertTrue(any("Japanese semantic mismatch" in x for x in report["errors"]))

    def test_independent_live_fact_signoff_requires_exact_manufacturer_snapshot_hash(self):
        report=reviewer.evaluate(self.contract,self.product,self.parsed,
            "different-maker-snapshot",enforce_live_hash=True)
        self.assertEqual(report["status"],"TECH_SEMANTIC_QA_HOLD")
        self.assertTrue(any("source snapshot changed" in e for e in report["errors"]))

    def test_changed_manufacturer_heading_or_raw_cell_refuses_facts_signoff(self):
        for field in ("title","raw"):
            with self.subTest(field=field):
                parsed=copy.deepcopy(self.parsed)
                if field=="title":
                    parsed["categories"][1]["rows"][5]["source_label"]="Wireless unknown"
                else:
                    parsed["categories"][2]["rows"][4]["models"]["A2"]="About 55°"
                report=reviewer.evaluate(self.contract,self.product,parsed,"test")
                self.assertEqual(report["status"],"TECH_SEMANTIC_QA_HOLD")
                self.assertTrue(report["errors"])


if __name__=="__main__":
    unittest.main()
