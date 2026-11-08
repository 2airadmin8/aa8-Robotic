"""Gate-handoff transition tests: no green score or skipped evidence can release."""
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from factory_gate_handoff import read_fixture, evaluate, markdown, REQUIRED_STEPS
SHA="7f326a4100cad38f027ef14736ec3a6f2a27724c"

class HandoffTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=read_fixture(ROOT)
    def check(self, outcome="success", **overrides):
        states={x:outcome for x in REQUIRED_STEPS}
        states.update(overrides)
        return evaluate(head_sha=SHA,pr=173,outcomes=states,source=self.source,checked_at="2026-11-09T00:00:00+00:00")
    def test_success_still_holds_qa_and_release(self):
        d=self.check()
        self.assertEqual(d["state"],"WAIT_INDEPENDENT_QA")
        self.assertEqual(d["blocking_gate"],"INDEPENDENT_QA")
        self.assertTrue(all(x is False for x in d["authorization"].values()))
        self.assertEqual(d["strict_release_status"],"HOLD")
        self.assertFalse(d["automatic_worker_started"])
        self.assertEqual(d["pr_url"],"https://github.com/2airadmin8/aa8-Robotic/pull/173")
        self.assertEqual(d["head_sha"],SHA)
        self.assertEqual(d["gates"][3]["status"],"PASS")
        self.assertEqual(d["gates"][4]["status"],"HOLD")
    def test_fail_returns_same_pr(self):
        d=self.check(browser="failure")
        self.assertEqual(d["state"],"RETURN_TO_DEV")
        self.assertEqual(d["blocking_gate"],"CI")
        self.assertIn("browser",d["next_action"])
        self.assertIn("same PR #173",d["resume_from"])
        self.assertEqual(d["gates"][3]["status"],"FAIL")
    def test_cancelled_or_skipped_is_not_pass(self):
        self.assertEqual(self.check(release="cancelled")["state"],"RETURN_TO_DEV")
        d=self.check(browser="skipped")
        self.assertEqual(d["state"],"HOLD_EVIDENCE")
        self.assertEqual(d["gates"][3]["status"],"HOLD")
    def test_invalid_sha_and_missing_ci_outcome(self):
        states={x:"success" for x in REQUIRED_STEPS}
        with self.assertRaises(ValueError):
            evaluate(head_sha="abc",pr=173,outcomes=states,source=self.source,checked_at="")
        states.pop("browser")
        with self.assertRaises(ValueError):
            evaluate(head_sha=SHA,pr=173,outcomes=states,source=self.source,checked_at="")
    def test_source_gates_count_and_identity(self):
        self.assertEqual(self.source["parameter_count"],36)
        self.assertEqual(len(self.source["parameter_groups"]),9)
        self.assertFalse(self.source["image_is_version_specific"])
        self.assertTrue(self.source["source_reconciliation"]["legacy_cn_preserved"])
    def test_existing_ci_workflow_uses_valid_github_expression_syntax(self):
        workflow=(ROOT/".github/workflows/ci.yml").read_text("utf-8")
        open_tag="$"+"{{"
        self.assertIn("if: "+open_tag+" always()",workflow)
        self.assertIn("PR_HEAD: "+open_tag+" github.event.pull_request.head.sha }}",workflow)
        self.assertIn("RESULT_REGRESSION: "+open_tag+" steps.regression.outcome }}",workflow)
        self.assertIn("x2-gate-handoff-"+open_tag+" github.event.pull_request.head.sha }}",workflow)
        # Check specifically that no malformed single-brace expression is present.
        import re
        self.assertNotRegex(workflow,r"\$\{(?!\{)\s*(?:github|steps|always)")
        self.assertIn("actions/upload-artifact@v4",workflow)
        self.assertIn("GITHUB_STEP_SUMMARY",workflow)

    def test_summary_has_safe_handoff(self):
        m=markdown(self.check(browser="failure"))
        self.assertIn("RETURN_TO_DEV",m)
        self.assertIn("PR:** #173",m)
        self.assertIn("HOLD",m)

if __name__=="__main__":
    unittest.main()
