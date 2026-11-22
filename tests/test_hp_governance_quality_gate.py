"""PM/CTO independent checks of existing PR intake and trusted-main governance."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import hp_governance_quality_gate as gate

GOOD_BODY = """## 设计正本 / Design SSOT
- Design / Figma / Drive：https://www.figma.com/design/uo56l51NgUqit4976LV6P2
- 业务目标与范围：P1 approved design/code traceability means less manual review work.
- 禁止改动的文件、流程：No CRM production writes, new Runner or invented facts.
- 对应 Issue：#176

## 变更与根因 / Change & RCA
- 类型：Feature, existing core governance quality enforcement.
- BUG-ID（非BUG填 N/A）：N/A
- 原始复现（Expected / Actual）：Previously the candidate PR could skip governance intake.
- 根因（不是现象）：No trusted-main design code traceability gate.
- 优先级 P0/P1/P2/P3：P1 approved governance capability.
- 设计→代码对应模块ID：SHELL, CTA, PRIVACY, GROWTH, GOVERNANCE, PRODUCT_FACTS
- 影响页面/组件/PC-SP：All 13 products PC1440/SP390, shared Header/Footer and CTA.
- 本次修复范围：Read-only existing CI and reusable governance validation only.

## 防再发回归 / Regression
- 自动测试文件与测试名称：tests/test_hp_governance_quality_gate.py; 11 security tests.
- 修复前 RED（测试失败）の证据：Existing CI not gated against unscoped changes.
- 修复后 GREEN（测试通过）的 CI Run：Exact candidate SHA GitHub actions required.
- PC/SP、关键业务边界检查：13 existing pages at PC1440 and SP390; no inquiry submit.
- 与已有 PR 的冲突审查：Current main and latest PR diff verified.

## 真实业务证据 / E2E
- 环境：DEV; no claim of verified live CEO rework E2E.
- 真实操作与最终结果（不得用HTTP200冒充业务完成）：Code and isolated QA only.
- 证据：脱敏记录ID / 图片 / 日志 / Run URL：https://github.com/2airadmin8/aa8-Robotic/pull/176
- 未完成的真实业务 Gate：Next new SKU measured cost and real CEO reject are pending.
- 失败 / 回滚时的应对：Failure = HOLD, restore to exact approved main SHA, no retries.
- 终止条件与价值证明（安全/核心功能100%；视觉/文案达标即停；额外打磨需收益证据）：Mandatory quality 100%, stop after approved baseline, no ROI-free polish.

## 独立 QA 与发布
- Dev 负责人：Existing AirAdmin8 Factory developer.
- 独立QA审查者（不得与Dev相同）：AA8-N-015 separate source/browser QA.
- QA结论：PASS only after exact SHA results.
- 生产发布：CEO-controlled separate authorization only.
- 业务完成判定：NOT_EXERCISED until verified.
"""


def event(*, created="2026-11-14T12:00:00Z", body=GOOD_BODY,
          action="opened"):
    return {"action": action, "repository": {"full_name": gate.REPO},
            "pull_request": {"number": 180, "created_at": created,
                             "base": {"ref": "main"},
                             "head": {"repo": {"full_name": gate.REPO}},
                             "body": body}}


class GovernanceQualityGateTests(unittest.TestCase):
    def test_design_docs_code_tests_exist_and_ci_is_wired(self):
        c = gate.load(ROOT)
        self.assertEqual(len(c["traceability"]), 6)
        self.assertEqual(c["qualityRule"]["maxAutoRepair"], 3)
        self.assertTrue(c["qualityRule"]["scoreIsNotReleaseAuthorization"])
        self.assertTrue(c["changeGate"]["reuseExistingPrTemplate"])
        self.assertIn("NOT_AUTOMATIC_FIGMA_PIXEL_PARITY",
                      c["designSources"]["visual"]["verification"])

    def test_v33_20261121_native_and_html_inventory_is_pinned_not_fully_approved(self):
        result = gate.validate_v33_design_snapshot(ROOT)
        self.assertEqual(result["status"], "PINNED_DESIGN_CONSISTENT_NOT_FIGMA_LIVE")
        self.assertEqual(result["figmaComponents"], 14)
        self.assertEqual(result["figmaVariables"], 38)
        self.assertEqual(result["htmlComponents"], 20)
        self.assertEqual(result["referenceOnly"], 12)
        self.assertEqual(result["release"], "HOLD")

    def test_v33_stale_figma_tokens_reference_components_fail_closed(self):
        import shutil
        file_names = (
            "docs/governance/hp-design-code-trace-v1.json",
            "ops/brand-preview/corporate-product-visual-v33.json",
            "ops/brand-preview/figma-product-v33-tokens.json",
            "docs/governance/AA8_PRODUCT_VISUAL_STANDARD_V33.md",
            "assets/css/site.css",
        )
        for mutation in (
            "old-8-20", "missing-component", "spacing-number", "falsely-approved",
            "cross-file-drift", "missing-src-proof", "stale-policy-doc",
            "spacing-css-drift", "spacing-css-no-usage"
        ):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as td:
                t = Path(td)
                for name in file_names:
                    dest = t / name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(ROOT/name, dest)
                visual_file=t/"ops/brand-preview/corporate-product-visual-v33.json"
                trace_file=t/"docs/governance/hp-design-code-trace-v1.json"
                tok_file=t/"ops/brand-preview/figma-product-v33-tokens.json"
                visual=json.loads(visual_file.read_text("utf-8"))
                trace=json.loads(trace_file.read_text("utf-8"))
                tokens=json.loads(tok_file.read_text("utf-8"))
                for entry in visual["htmlComponentManagement"]:
                    f=t/entry["codeOwner"]
                    f.parent.mkdir(parents=True, exist_ok=True)
                    f.touch(exist_ok=True)
                if mutation=="old-8-20":
                    trace["designSources"]["visualCandidateV33"]["figmaVariables"]["count"]=20
                elif mutation=="missing-component":
                    visual["htmlComponentManagement"].pop()
                elif mutation=="spacing-number":
                    tokens["dimension"]["spacing"]["24"]["$value"]="25px"
                elif mutation=="falsely-approved":
                    visual["htmlComponentManagement"][7]["status"]="IMPLEMENTED"
                elif mutation=="cross-file-drift":
                    visual["latestDesignEvidence"]["nativeComponentsTotal"]=8
                elif mutation=="missing-src-proof":
                    tokens["$sourceEvidence"]["normalizedUtf8Sha256"]="unverified"
                elif mutation=="spacing-css-drift":
                    f=t/"assets/css/site.css"
                    f.write_text(f.read_text("utf-8").replace(
                        "--aa8-v33-spacing-24:24px;",
                        "--aa8-v33-spacing-24:25px;"),encoding="utf-8")
                elif mutation=="spacing-css-no-usage":
                    f=t/"assets/css/site.css"
                    f.write_text(f.read_text("utf-8").replace(
                        "var(--aa8-v33-spacing-24)","24px"),encoding="utf-8")
                elif mutation=="stale-policy-doc":
                    f=t/"docs/governance/AA8_PRODUCT_VISUAL_STANDARD_V33.md"
                    f.write_text(f.read_text("utf-8").replace(
                        "14 = previous eight","8 = old"),encoding="utf-8")
                visual_file.write_text(json.dumps(visual,ensure_ascii=False),encoding="utf-8")
                trace_file.write_text(json.dumps(trace,ensure_ascii=False),encoding="utf-8")
                tok_file.write_text(json.dumps(tokens,ensure_ascii=False),encoding="utf-8")
                with self.assertRaisesRegex(ValueError,"AA8_GOVERNANCE_HOLD"):
                    gate.validate_v33_design_snapshot(t)

    def test_new_pr_uses_existing_template_and_impact_matrix(self):
        files = [{"filename": "includes/site-header.html"},
                 {"filename": "docs/governance/01_HP_ADAPTER_V1.md"},
                 {"filename": ".github/workflows/ci.yml"}]
        result = gate.check_pr(event(), files)
        self.assertEqual(result["status"], "SCOPED_INTAKE_READY_NOT_RELEASE_APPROVED")
        self.assertIn("SHELL", result["mappedModules"])
        self.assertIn("GOVERNANCE", result["mappedModules"])

    def test_missing_sections_or_empty_template_answers_hold(self):
        cases = ("", "Just fix CSS ASAP",
                 GOOD_BODY.replace("## 变更与根因 / Change & RCA", "## Later"),
                 GOOD_BODY.replace(
                     "- 优先级 P0/P1/P2/P3：P1 approved governance capability.",
                     "- 优先级 P0/P1/P2/P3："))
        for body in cases:
            with self.subTest(body=body[:40]), self.assertRaises(ValueError):
                gate.check_pr(event(body=body),
                              [{"filename": "includes/site-header.html"}])

    def test_shared_change_without_all_13_and_pc_sp_holds(self):
        body = GOOD_BODY.replace("All 13 products PC1440/SP390",
                                 "This single page only")
        with self.assertRaisesRegex(ValueError, "13 product"):
            gate.check_pr(event(body=body),
                          [{"filename": "includes/site-header.html"}])

    def test_p2_p3_need_measured_business_value_p0_does_not(self):
        base = GOOD_BODY.replace("P1 approved governance capability.",
                                 "P2 additional cosmetic polish.")
        with self.assertRaisesRegex(ValueError, "baseline"):
            gate.check_pr(event(body=base),
                          [{"filename": "scripts/hp_governance_quality_gate.py"}])
        measured = base.replace("P1 approved design/code traceability",
                                "GSC baseline 219 impressions and 8 clicks in 7 days")
        self.assertEqual(
            gate.check_pr(event(body=measured),
                          [{"filename": "scripts/hp_governance_quality_gate.py"}])["category"], "P2")
        security = GOOD_BODY.replace("P1 approved governance capability.",
                                     "P0 critical safety fix.")
        self.assertEqual(
            gate.check_pr(event(body=security),
                          [{"filename": "scripts/hp_governance_quality_gate.py"}])["category"], "P0")

    def test_fork_path_traversal_duplicate_files_denied(self):
        e = event()
        e["pull_request"]["head"]["repo"]["full_name"] = "malicious/fork"
        with self.assertRaises(ValueError):
            gate.check_pr(e, [{"filename": "includes/site-header.html"}])
        with self.assertRaises(ValueError):
            gate.check_pr(event(), [{"filename": "../secret.txt"}])
        arr = [{"filename": "scripts/hp_governance_quality_gate.py"}]
        with self.assertRaises(ValueError):
            gate.check_pr(event(), arr + arr)

    def test_old_pr_exempt_only_new_intake_not_safety(self):
        result = gate.check_pr(
            event(created="2026-11-01T01:00:00Z", body=""),
            [{"filename": "products/unitree-g1.html"}])
        self.assertEqual(result["status"], "LEGACY_INTAKE_EXEMPT_NOT_SAFETY_EXEMPT")
        with self.assertRaises((OSError, ValueError)):
            gate.load(Path("/nonexistent/governance"))

    def test_gh_pagination_and_unrelated_change(self):
        arr = [[{"filename": "products/unitree-g1.html"}],
               [{"filename": "tests/test_hp_governance_quality_gate.py"}]]
        self.assertEqual(len(gate.normalized_files(arr)), 2)
        self.assertEqual(
            gate.check_pr(event(body=""), [{"filename": "LICENSE"}])["status"],
            "OUT_OF_SCOPE")

    def test_untraced_code_change_holds(self):
        body = GOOD_BODY.replace(
            "SHELL, CTA, PRIVACY, GROWTH, GOVERNANCE, PRODUCT_FACTS",
            "SHELL, CTA, PRIVACY, GROWTH, PRODUCT_FACTS")
        with self.assertRaisesRegex(ValueError, "module IDs"):
            gate.check_pr(event(body=body),
                          [{"filename": "docs/governance/hp-design-code-trace-v1.json"}])

    def test_independent_job_never_runs_untrusted_pr_or_writer_secrets(self):
        wf = (ROOT / ".github/workflows/ci.yml").read_text("utf-8")
        self.assertIn("pull_request_target:", wf)
        part = wf.split("  policy-independent-gate:", 1)[1].split(
            "  # Trusted default-branch router", 1)[0]
        self.assertIn("ref: " + chr(36) + "{{ github.event.pull_request.base.sha }}", part)
        self.assertIn("persist-credentials: false", part)
        self.assertIn("pull-requests: read", part)
        self.assertIn("contents: read", part)
        self.assertNotIn("contents: write", part)
        self.assertNotIn("secrets.", part)
        self.assertNotIn("github.event.pull_request.head.sha", part)
        self.assertIn("scripts/hp_governance_quality_gate.py pr", part)

    def test_real_cli_bom_json_compatibility(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path_event = root / "event.json"
            path_files = root / "files.json"
            path_event.write_text(json.dumps(event()), encoding="utf-8-sig")
            path_files.write_text(json.dumps([[
                {"filename": "scripts/hp_governance_quality_gate.py"},
            ]]), encoding="utf-8-sig")
            run = subprocess.run([
                sys.executable, "-B",
                str(ROOT / "scripts/hp_governance_quality_gate.py"),
                "pr", "--event", str(path_event), "--files", str(path_files),
            ], cwd=ROOT, capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn("SCOPED_INTAKE_READY", run.stdout)

    def test_one_existing_ci_and_manual_only_pages(self):
        wf = (ROOT / ".github/workflows/ci.yml").read_text("utf-8")
        self.assertIn("build-and-verify:", wf)
        self.assertIn("hp_governance_quality_gate.py audit", wf)
        pages = (ROOT / ".github/workflows/pages.yml").read_text("utf-8")
        self.assertIn("workflow_dispatch:", pages)
        self.assertNotIn("\n  push:", pages)


if __name__ == "__main__":
    unittest.main()
