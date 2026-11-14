import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from factory_gate_router import discover, route, STEPS
SHA="fdbe59ac855b738276dd8841027a68fa29be938e"
class UniversalGateTest(unittest.TestCase):
 def outcomes(self,**kwargs):
  r={k:"success" for k in STEPS};r.update(kwargs);return r
 def test_real_x2_fixture_maps_to_existing_pr(self):
  x=discover(ROOT,["tests/fixtures/x2-pilot/source-contract.json",".github/workflows/ci.yml"])
  self.assertEqual(x["ids"],["agibot-x2-series"])
  self.assertEqual(x["master_count"],13)
  self.assertEqual(x["work_scope"],"PRODUCT")
  g=route(173,SHA,self.outcomes(),x,"2026-11-09T00:00:00Z")
  self.assertEqual(g["state"],"WAIT_DESIGN_QA")
  self.assertEqual(g["release"],"HOLD")
  self.assertEqual(g["executor"]["auto_wakeup"],"NOT_CONNECTED")
 def test_existing_product_id_from_page(self):
  x=discover(ROOT,["products/unitree-g1.html"])
  self.assertIn("unitree-g1",x["ids"])
  self.assertEqual(x["work_scope"],"PRODUCT")
 def test_multiple_existing_products(self):
  x=discover(ROOT,["products/unitree-g1.html","products/agibot-g2.html"])
  self.assertEqual(x["ids"],["agibot-g2","unitree-g1"])
  self.assertEqual(x["work_scope"],"MULTI_PRODUCT")
 def test_global_change_routes_all_master_to_qa_scope(self):
  x=discover(ROOT,["scripts/product_factory.py"])
  self.assertEqual(x["work_scope"],"GLOBAL_FACTORY")
  g=route(31,SHA,self.outcomes(),x,"date")
  self.assertEqual(g["state"],"WAIT_FACTORY_QA")
  self.assertIn("13",g["next_action"])
 def test_product_and_shared_factory_change_route_to_global_regression(self):
  x=discover(ROOT,["tests/fixtures/x2-pilot/product.json","scripts/product_factory.py"])
  self.assertEqual(x["ids"],["agibot-x2-series"])
  self.assertTrue(x["global_factory_change"])
  self.assertEqual(route(173,SHA,self.outcomes(),x,"date")["state"],"WAIT_FACTORY_QA")
 def test_shared_css_and_site_js_require_full_factory_qa(self):
  for path in ("assets/css/g1-factory-v1.css","assets/css/shared-layout.css","assets/js/site.js"):
   with self.subTest(path=path):
    x=discover(ROOT,[path])
    self.assertTrue(x["global_factory_change"])
    self.assertEqual(route(173,SHA,self.outcomes(),x,"date")["state"],"WAIT_FACTORY_QA")
 def test_no_product_change_never_fabricates_agent(self):
  x=discover(ROOT,["README.md"])
  self.assertEqual(x["work_scope"],"NO_PRODUCT_SCOPE")
  self.assertEqual(route(5,SHA,self.outcomes(),x,"date")["state"],"NOT_APPLICABLE")
 def test_master_ambiguous_requires_input(self):
  x=discover(ROOT,["data/products.json"])
  g=route(7,SHA,self.outcomes(),x,"date")
  self.assertEqual(g["state"],"INPUT_REQUIRED")
  self.assertEqual(g["blocking_gate"],"G0")
 def test_failure_and_skip_fail_closed(self):
  x=discover(ROOT,["products/unitree-g1.html"])
  self.assertEqual(route(18,SHA,self.outcomes(browser="failure"),x,"date")["state"],"RETURN_TO_DEV")
  self.assertEqual(route(18,SHA,self.outcomes(browser="skipped"),x,"date")["state"],"HOLD_EVIDENCE")
 def test_pr_sha_and_paths_must_be_valid(self):
  x=discover(ROOT,["products/unitree-g1.html"])
  with self.assertRaises(ValueError): route(3,"not-sha",self.outcomes(),x,"date")
  with self.assertRaises(ValueError): discover(ROOT,["../secret"])
  with self.assertRaises(ValueError): route(3,SHA,{"regression":"success"},x,"date")
if __name__=="__main__":unittest.main()
