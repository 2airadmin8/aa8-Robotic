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
  self.assertEqual(x["work_scope"],"GLOBAL_FACTORY")
  self.assertTrue(x["all_13_public_product_regression_required"])
  self.assertEqual(route(173,SHA,self.outcomes(),x,"date")["state"],"WAIT_FACTORY_QA")
 def test_shared_css_and_site_js_require_full_factory_qa(self):
  for path in ("assets/css/g1-factory-v1.css","assets/css/shared-layout.css","assets/js/site.js"):
   with self.subTest(path=path):
    x=discover(ROOT,[path])
    self.assertTrue(x["global_factory_change"])
    self.assertEqual(route(173,SHA,self.outcomes(),x,"date")["state"],"WAIT_FACTORY_QA")
 def test_a2_real_source_evidence_has_separate_human_hold(self):
  a=discover(ROOT,["tests/fixtures/a2-factory/product.json",
                   "scripts/product_factory.py"])
  self.assertEqual(a["work_scope"],"GLOBAL_FACTORY")
  self.assertEqual(a["master_count"],13)
  facts=a["pilot_fact_quality"]["unitree-a2"]
  self.assertEqual(facts["maker_rows"],37)
  self.assertEqual(facts["model_cells"],74)
  self.assertEqual(facts["independent_technical_semantic_review"],"PASS_REFERENCE_ONLY")
  self.assertEqual(facts["row_review_statuses"],["TRANSLATION_REVIEW_PENDING"])
  self.assertEqual(facts["human_semantic_signoff"],"NOT_ATTESTED")
  out=route(180,SHA,self.outcomes(),a,"date")
  self.assertEqual(out["state"],"WAIT_FACTORY_QA")
  self.assertEqual(out["product_gates"][0]["manufacturer_human_semantic_signoff"],"NOT_ATTESTED")
  self.assertEqual(out["release"],"HOLD")
  mixed=discover(ROOT,["tests/fixtures/a2-factory/product.json",
                       "products/unitree-g1-d.html","scripts/product_factory.py"])
  status={x["product_id"]:x["manufacturer_human_semantic_signoff"]
          for x in route(180,SHA,self.outcomes(),mixed,"date")["product_gates"]}
  self.assertEqual(status["unitree-a2"],"NOT_ATTESTED")
  self.assertEqual(status["unitree-g1-d"],"EXISTING_PUBLIC_PRODUCT_NOT_REATTESTED_IN_THIS_PR")
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



class TrustedReadyLeaseTests(unittest.TestCase):
 """Synthetic negative/positive parser fixtures; NEVER a live task or worker."""
 def setUp(self):
  from datetime import datetime,timezone
  self.now=datetime(2026,11,22,12,0,tzinfo=timezone.utc)
  self.sha="7e270dc6b4b9d922ccee7e561535b1e83b65d071"
  self.pr={"number":198,"draft":True,"state":"open","base":{"ref":"main","sha":"a"*40},
    "head":{"sha":self.sha,"ref":"feat/hp-factory-b2-r1-preview-20261121",
            "repo":{"full_name":"2airadmin8/aa8-Robotic"}}}
  self.event={"action":"labeled","repository":{"full_name":"2airadmin8/aa8-Robotic"},
    "label":{"name":"READY"},"sender":{"login":"2airadmin8","id":211299962},
    "issue":{"number":400,"state":"open",
      "user":{"login":"2airadmin8","id":211299962},
      "body":("Authorized isolated task\n"
              "<!-- AA8-HP-READY-V1\n"
              "pr=198\nhead="+self.sha+"\nowner=AA8-N-018\n"
              "task=HP-C11-SAFE\npaths=assets/css/site.css,tests/hp-shared-governance.spec.js\n"
              "-->")}}
 def claim(self,comments=None):
  from factory_gate_router import ready_preflight
  return ready_preflight(self.event,self.pr,comments or [],1212001,self.now,
                         {**self.event["issue"],"labels":[{"name":"READY"}]})
 def test_eligible_ceo_only_prepares_read_only_claim(self):
  result=self.claim()
  self.assertEqual(result["status"],"READY_CLAIM_PREPARED_WRITER_HOLD")
  self.assertEqual(result["owner"],"AA8-N-018")
  self.assertFalse(result["auto_commit"])
  self.assertEqual(result["deepseek"],"NOT_RUN")
  self.assertIn("run=1212001",result["lease_marker"])
  self.assertEqual(len(result["allowed_paths"]),2)
 def test_parallel_runner_rejected_against_active_governance_lease(self):
  marker=self.claim()["lease_marker"]
  with self.assertRaisesRegex(ValueError,"READY_LEASE_HELD"):
   self.claim([{"body":marker,"user":{"login":"github-actions[bot]"}}])
 def test_stale_sha_ceo_identity_unsafe_paths_duplicate_or_wrong_issue_rejected(self):
  import copy
  from factory_gate_router import ready_preflight
  actions=[
   lambda e,p:e["label"].update({"name":"READY_IGNORED"}),
   lambda e,p:e["sender"].update({"id":25}),
   lambda e,p:e["issue"]["user"].update({"id":25}),
   lambda e,p:e["issue"].update({"number":129}),
   lambda e,p:p["head"].update({"sha":"f"*40}),
   lambda e,p:e["issue"].update({"body":e["issue"]["body"].replace("assets/css/site.css","data/products.json")}),
   lambda e,p:e["issue"].update({"body":e["issue"]["body"].replace("assets/css/site.css","scripts/deepseek_factory_autofix.py")}),
   lambda e,p:e["issue"].update({"body":e["issue"]["body"]+"\n"+e["issue"]["body"]}),
  ]
  for mutate in actions:
   with self.subTest(mutate=mutate.__code__.co_firstlineno):
    event,pr=copy.deepcopy(self.event),copy.deepcopy(self.pr)
    mutate(event,pr)
    with self.assertRaises(ValueError):
     ready_preflight(event,pr,[],1212001,self.now,
                     {**event["issue"],"labels":[{"name":"READY"}]})
 def test_expired_claim_can_be_reviewed_only_after_lease_expiry(self):
  from datetime import timedelta
  from factory_gate_router import ready_preflight
  old=self.claim()["lease_marker"]
  past=old.replace("expires=2026-11-22T12:45:00Z","expires=2026-11-22T11:00:00Z")
  result=ready_preflight(self.event,self.pr,[{"body":past}],1212002,self.now,
    {**self.event["issue"],"labels":[{"name":"READY"}]})
  self.assertEqual(result["run_id"],1212002)
 def test_live_issue_changed_or_unlabeled_refuses_claim(self):
  from factory_gate_router import ready_preflight
  for changes in ({"body":"mutated by non-CEO"},
                  {"labels":[]},{"state":"closed"}):
   with self.subTest(changes=changes):
    live={**self.event["issue"],"labels":[{"name":"READY"}],**changes}
    with self.assertRaisesRegex(ValueError,"live body/state/label"):
     ready_preflight(self.event,self.pr,[],1212001,self.now,live)
 def test_signed_ready_claim_to_model_bridge_and_negative_cases(self):
  import copy
  from factory_gate_router import ready_preflight,ready_verify
  event=copy.deepcopy(self.event)
  event["issue"]["body"]=event["issue"]["body"].replace(
   "Authorized isolated task",
   "### Acceptance\nThe main site menu should preserve keyboard navigation and focus. "
   "Update only shared CSS and its scoped regression test; no production writes.")
  issue={**event["issue"],"labels":[{"name":"READY"}]}
  claim=ready_preflight(event,self.pr,[],1212001,self.now,issue)
  signed={"body":claim["lease_marker"],
          "user":{"id":41898282,"login":"github-actions[bot]"}}
  verified=ready_verify(issue,self.pr,[signed],1212001,self.now)
  self.assertEqual(verified["status"],"READY_TASK_VERIFIED")
  self.assertEqual(verified["claim_run"],1212001)
  self.assertEqual(verified["allowed_paths"],
                   ["assets/css/site.css","tests/hp-shared-governance.spec.js"])
  with self.assertRaisesRegex(ValueError,"body changed"):
   ready_verify({**issue,"body":issue["body"]+" changed"},self.pr,
                [signed],1212001,self.now)
  with self.assertRaisesRegex(ValueError,"not made by"):
   ready_verify(issue,self.pr,[{**signed,"user":{"id":211299962,
                 "login":"2airadmin8"}}],1212001,self.now)
  with self.assertRaisesRegex(ValueError,"Missing or duplicate"):
   ready_verify(issue,self.pr,[],1212001,self.now)
  with self.assertRaisesRegex(ValueError,"exact SHA changed"):
   ready_verify(issue,{**self.pr,"head":{**self.pr["head"],
                "sha":"f"*40}},[signed],1212001,self.now)
  with self.assertRaisesRegex(ValueError,"lease expired"):
   from datetime import timedelta
   ready_verify(issue,self.pr,[signed],1212001,self.now+timedelta(minutes=46))
  wrong=copy.deepcopy(issue)
  wrong["body"]=wrong["body"].replace("assets/css/site.css","data/products.json")
  with self.assertRaisesRegex(ValueError,"unauthorized path"):
   ready_verify(wrong,self.pr,[signed],1212001,self.now)

 def test_workflow_bootstrap_is_separate_and_default_off(self):
  text=(ROOT/".github/workflows/ci.yml").read_text("utf8")
  if "factory-ready-wakeup:" not in text:
   # Original protected main must remain unchanged until exact bootstrap.
   self.assertNotIn("  issues:\n    types: [labeled]",text)
   return
  self.assertIn("issues:",text)
  self.assertIn("types: [labeled]",text)
  self.assertIn("AA8_FACTORY_READY_ENABLED == 'true'",text)
  self.assertIn("factory-ready-wakeup:",text)
  self.assertIn("cancel-in-progress: false",text)
  wakeup=text.split("  factory-ready-wakeup:",1)[1].split("  # POLICY-TRUSTED",1)[0]
  self.assertIn("vars.AA8_FACTORY_AUTOFIX_ENABLED == 'true'",wakeup)
  self.assertIn("gh workflow run ci.yml",wakeup)
  self.assertNotIn("DEEPSEEK_API_KEY:",wakeup)
  self.assertNotIn("git push",wakeup)

if __name__=="__main__":unittest.main()
