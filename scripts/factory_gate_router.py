#!/usr/bin/env python3
"""General PR Factory gate router; reports only, never launches workers or releases."""
import argparse
from datetime import timedelta
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
STEPS = ("regression", "build", "browser", "release", "source_clean")
OUTCOMES = {"success", "failure", "cancelled", "skipped", "unknown"}

# Home/Corporate shared UI belongs to the EXISTING Factory gate, not a new
# product SKU or a parallel runner. Explicit paths only: unknown changes stay
# NO_PRODUCT_SCOPE, and Product Master changes remain INPUT_REQUIRED.
HOME_PAGE_PATHS = frozenset({
    "index.html",
    "assets/css/home-hero.css",
    "assets/css/hero-lineup.css",
    "assets/img/robot-category-lineup.svg",
    "tests/hub-pages-visual.spec.js",
})
SHARED_UI_PATHS = frozenset({
    "assets/css/product-cards-v2.css",
    "assets/js/product-cards-v2.js",
    "assets/css/main-site-experience.css",
    "assets/js/seo.js",
    "assets/css/corporate-header.css",
})


def check(expr, msg):
    if not expr:
        raise ValueError(msg)

def discover(root, paths):
    master = json.loads((root / "data/products.json").read_text(encoding="utf8"))
    official = {p["id"]: p for p in master["products"]}
    pilots = {}
    for file in (root / "tests/fixtures").glob("*/product.json"):
        obj = json.loads(file.read_text(encoding="utf8"))
        pid = obj.get("id")
        check(pid and pid not in official and pid not in pilots, "Pilot ProductID collision")
        check(obj.get("pageFactory", {}).get("releaseReady") is False, "Unsafe pilot releaseReady")
        pilots[pid] = (obj, file.relative_to(root).as_posix())
    found, ambiguous, global_change = set(), [], False
    home_change, shared_ui_change = False, False
    for filename in paths:
        check(not filename.startswith("/") and "\\" not in filename and ".." not in Path(filename).parts,
              "Invalid changed path")
        if filename == "data/products.json":
            ambiguous.append(filename)
        home_change = home_change or filename in HOME_PAGE_PATHS
        shared_ui_change = shared_ui_change or filename in SHARED_UI_PATHS
        if filename in {"scripts/factory_gate_router.py",
                        "scripts/factory_autofix_policy.py",
                        "scripts/deepseek_factory_autofix.py",
                        "scripts/product_factory.py", "scripts/product_page_standard_v31.py",
                        "scripts/templates/g1_factory_v1.html",
                        "assets/css/site.css", "assets/css/shared-layout.css",
                        "assets/css/g1-product.css", "assets/css/g1-factory-v1.css",
                        "assets/css/g1-factory-v3.css", "assets/css/product-standard-v31.css",
                        "assets/js/site.js"}:
            global_change = True
        for pid, obj in official.items():
            refs = [obj.get("detailPage"), obj.get("image")]
            refs += [im.get("src") for im in obj.get("pageFactory", {}).get("images", [])]
            if filename in refs:
                found.add(pid)
        for pid, (obj, fixture) in pilots.items():
            if filename == fixture or filename.startswith(fixture.rsplit("/", 1)[0] + "/"):
                found.add(pid)
    # Shared Factory/source/template changes are GLOBAL, even when the same
    # PR also carries one A2 fixture. The previous label falsely said PRODUCT.
    scope = ("INPUT_REQUIRED" if ambiguous else
             "GLOBAL_FACTORY" if global_change else
             "UI_SHARED" if shared_ui_change else
             "MULTI_PRODUCT" if len(found) > 1 else "PRODUCT" if found else
             "HOME_PAGE" if home_change else
             "NO_PRODUCT_SCOPE")
    facts = {}
    for pid, (obj, fixture) in pilots.items():
        if pid not in found:
            continue
        maker = root / Path(fixture).parent / "maker-live-contract.json"
        if not maker.is_file():
            facts[pid] = {"maker_contract": "NOT_PRESENT",
                          "human_semantic_signoff": "NOT_ATTESTED"}
            continue
        contract = json.loads(maker.read_text(encoding="utf8"))
        rows = [row for group in contract.get("categories", [])
                for row in group.get("rows", [])]
        check(rows and all(isinstance(row.get("models"),dict) for row in rows),
              "Maker data contract malformed: "+pid)
        fact_status = {row.get("review_status","UNKNOWN") for row in rows}
        tech_file = root / Path(fixture).parent / "independent-technical-fact-review-74.json"
        technical = json.loads(tech_file.read_text(encoding="utf8")) if tech_file.is_file() else {}
        facts[pid] = {
            "manufacturer_source": contract.get("source_url"),
            "maker_rows": len(rows),
            "model_cells": sum(len(row["models"]) for row in rows),
            "row_review_statuses": sorted(fact_status),
            "independent_technical_semantic_review":
                "PASS_REFERENCE_ONLY" if technical.get("status") == "TECH_SEMANTIC_QA_PASS"
                and technical.get("errors") == [] else "HOLD_OR_NOT_RECORDED",
            "human_semantic_signoff": "NOT_ATTESTED",
            "evidence_source_code_sha": technical.get("reviewed_source_code_commit","UNKNOWN"),
        }
    return {"ids": sorted(found), "global_factory_change": global_change,
            "ambiguous": ambiguous, "master_count": len(official), "fixture_count": len(pilots),
            "work_scope": scope, "pilot_fact_quality": facts,
            "home_ui_regression_required": home_change or shared_ui_change,
            "all_13_public_product_regression_required": global_change or shared_ui_change}

def route(pr, sha, outcomes, scope, at):
    check(isinstance(pr, int) and pr > 0, "Invalid PR number")
    check(re.fullmatch("[0-9a-f]{40}", sha) is not None, "Invalid HEAD SHA")
    check(set(outcomes) == set(STEPS) and all(v in OUTCOMES for v in outcomes.values()),
          "Incomplete CI evidence")
    fails = [k for k in STEPS if outcomes[k] in ("failure", "cancelled")]
    gaps = [k for k in STEPS if outcomes[k] in ("unknown", "skipped")]
    if scope["work_scope"] == "NO_PRODUCT_SCOPE":
        state, gate, owner, action = ("NOT_APPLICABLE", "NONE", "Existing PR owner",
                                     "Continue normal PR checks, no Factory task inferred")
    elif fails:
        state, gate, owner, action = ("RETURN_TO_DEV", "CI", "AA8-N-018 development workstation",
                                     "Fix failed CI: " + ", ".join(fails) + "; add regression; retry in same PR")
    elif gaps:
        state, gate, owner, action = ("HOLD_EVIDENCE", "CI", "AA8-N-018 development workstation",
                                     "Missing CI evidence: " + ", ".join(gaps) + "; SKIP is not PASS")
    elif scope["ambiguous"]:
        state, gate, owner, action = ("INPUT_REQUIRED", "G0", "Product Master owner",
                                     "Determine specific changed ProductIDs; cannot infer from Master diff alone")
    elif scope["work_scope"] in ("HOME_PAGE", "UI_SHARED"):
        state, gate, owner, action = (
            "WAIT_UI_INDEPENDENT_QA", "G2",
            "AA8-N-015 independent QA workstation",
            "Check real final-artifact home PC1440/1280 SP640/390/360, "
            "all card bounding boxes, screenshots and links at exact HEAD")
    elif scope["global_factory_change"]:
        state, gate, owner, action = ("WAIT_FACTORY_QA", "G4", "AA8-N-015 independent QA workstation",
                                     "Inspect all 13 Master products and cross-product regressions on exact HEAD")
    else:
        state, gate, owner, action = ("WAIT_DESIGN_QA", "G2", "Design / AA8-N-015 QA workstation",
                                     "Compare PC/SP with approved Figma and verify each product at exact HEAD")
    return {
        "schema_version": "factory-gate-handoff-v2", "timestamp": at, "pr": pr,
        "pr_url": "https://github.com/2airadmin8/aa8-Robotic/pull/" + str(pr),
        "head_sha": sha, "scope": scope, "ci_outcomes": outcomes,
        "state": state, "blocking_gate": gate, "next_owner": owner,
        "next_action": action, "resume_from": "same PR #" + str(pr) + ", exact HEAD",
        "product_gates": [{
            "product_id": pid, "design": "HOLD", "independent_qa": "HOLD",
            "manufacturer_human_semantic_signoff":
                scope.get("pilot_fact_quality", {}).get(pid, {}).get(
                    "human_semantic_signoff",
                    "EXISTING_PUBLIC_PRODUCT_NOT_REATTESTED_IN_THIS_PR"),
            "business_e2e": "HOLD", "ceo": "HOLD"
        } for pid in scope["ids"]],
        "executor": {"developer_machine": "AA8-N-018", "qa_machine": "AA8-N-015",
                     "auto_wakeup": "NOT_CONNECTED", "auto_commit": False,
                     "independent_qa_trigger": "NOT_CONNECTED"},
        "release": "HOLD", "authorized": {"merge": False, "pages": False, "crm_write": False}
    }

# READY claim runs ONLY from trusted main in the original ci.yml, once the
# explicit AA8_FACTORY_READY_ENABLED repo variable is turned on. This parser
# does not invoke DeepSeek, open write tokens or make GitHub changes.
READY_TAG_RE = re.compile(
    r"<!-- AA8-HP-READY-V1\n"
    r"pr=(?P<pr>[0-9]+)\n"
    r"head=(?P<head>[a-f0-9]{40})\n"
    r"owner=(?P<owner>AA8-N-018|SES-sLLM)\n"
    r"task=(?P<task>[A-Z0-9][A-Z0-9_-]{3,63})\n"
    r"paths=(?P<paths>[a-zA-Z0-9_./,-]+)\n-->",
    re.ASCII)
LEASE_RE = re.compile(
    r"<!-- AA8-HP-READY-LEASE issue=(?P<issue>[0-9]+) "
    r"task=(?P<task>[A-Z0-9_-]+) "
    r"head=(?P<head>[0-9a-f]{40}) run=(?P<run>[0-9]+) "
    r"expires=(?P<expiry>[0-9TZ:-]+) -->")
READY_SAFE_PREFIXES = ("assets/css/", "assets/js/", "tests/", "includes/")
READY_BLOCKED = (
    "assets/js/analytics-events.js", "assets/js/contact-v2.js",
    "tests/fixtures/", ".github/", "data/", "secrets/")
CEO_USER_ID = 211299962


def ready_preflight(event: dict, pr: dict, prior_comments: list[dict],
                    run_id: int, now: datetime, live_issue: dict) -> dict:
    """No writes: accept CEO-labelled, already-authorized exact-SHA task only.

    GitHub Actions must serialize all READY jobs with one global concurrency
    group and cancel-in-progress:false; a comment marker is not itself an
    atomic cross-run mutex. Refuse if any non-expired claim exists in the sole
    governance Issue #129. The execution writer is deliberately not enabled.
    """
    check(event.get("action")=="labeled"
          and event.get("repository",{}).get("full_name")=="2airadmin8/aa8-Robotic"
          and event.get("label",{}).get("name")=="READY",
          "READY event source is not the original repository/label")
    issue=event.get("issue") or {}
    actor=event.get("sender") or {}
    check(not issue.get("pull_request") and type(issue.get("number")) is int
          and issue["number"]!=129 and issue.get("state")=="open",
          "READY task must be an authorized standalone open issue, not #129")
    check(actor.get("id")==CEO_USER_ID and actor.get("login")=="2airadmin8"
          and issue.get("user",{}).get("id")==CEO_USER_ID,
          "READY task and label must originate from the verified CEO")
    check(isinstance(live_issue,dict)
          and live_issue.get("number")==issue["number"]
          and live_issue.get("state")=="open"
          and live_issue.get("user",{}).get("id")==CEO_USER_ID
          and live_issue.get("body")==issue.get("body")
          and "READY" in [
              label.get("name") for label in live_issue.get("labels",[])
              if isinstance(label,dict)],
          "READY issue live body/state/label changed after signed GitHub event")
    check(type(run_id) is int and run_id>0 and now.tzinfo is not None,
          "READY requires genuine run ID and timezone")
    matches=list(READY_TAG_RE.finditer(issue.get("body") or ""))
    check(len(matches)==1,"READY issue needs one exact structured CEO scope")
    scope=matches[0].groupdict()
    check(scope["pr"]=="198" and pr.get("number")==198
          and pr.get("state")=="open" and pr.get("draft") is True
          and pr.get("base",{}).get("ref")=="main"
          and pr.get("head",{}).get("repo",{}).get("full_name")
              =="2airadmin8/aa8-Robotic"
          and pr.get("head",{}).get("sha")==scope["head"],
          "READY scope stale or does not match original Draft PR #198")
    check(pr.get("head",{}).get("ref")==
          "feat/hp-factory-b2-r1-preview-20261121",
          "READY does not own the original protected draft branch")
    paths=scope["paths"].split(",")
    check(0<len(paths)<=5 and len(set(paths))==len(paths)
          and all(p and p.startswith(READY_SAFE_PREFIXES)
                  and not p.startswith(READY_BLOCKED)
                  and ".." not in Path(p).parts
                  and not p.endswith("/") and "\\" not in p
                  and Path(p).suffix in (".css",".js",".html",".py") for p in paths),
          "READY path list is unsafe or exceeds minimal allowed code scope")
    check(isinstance(prior_comments,list),"READY existing leases unreadable")
    for comment in prior_comments:
        for match in LEASE_RE.finditer(comment.get("body") or ""):
            expiry=datetime.fromisoformat(match.group("expiry").replace("Z","+00:00"))
            check(expiry<=now, "READY_LEASE_HELD: existing task has active owner/run lease")
    expires=(now+timedelta(minutes=45)).strftime("%Y-%m-%dT%H:%M:%SZ")
    marker=(f"<!-- AA8-HP-READY-LEASE issue={issue['number']} "
            f"task={scope['task']} head={scope['head']} run={run_id} "
            f"expires={expires} -->")
    return {"status":"READY_CLAIM_PREPARED_WRITER_HOLD",
            "source_issue":issue["number"],"pr":198,
            "task":scope["task"],"owner":scope["owner"],
            "head_sha":scope["head"],"allowed_paths":paths,
            "run_id":run_id,"lease_marker":marker,
            "lease_expiry_utc":expires,
            "deepseek":"NOT_RUN","auto_commit":False,
            "independent_qa":"NOT_RUN","release":"HOLD"}


def summary(data):
    return "\n".join([
        "## Factory Gate handoff v2",
        "",
        "PR: #" + str(data["pr"]) + " | exact SHA: " + data["head_sha"],
        "Scope: " + data["scope"]["work_scope"] + " | Products: " + ", ".join(data["scope"]["ids"]),
        "State: " + data["state"] + " | Blocking: " + data["blocking_gate"],
        "Next owner: " + data["next_owner"],
        "Next: " + data["next_action"],
        "Release: HOLD; no automatic AI worker or independent QA invoked.",
        "",
    ])

def ready_main(argv: list[str]) -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--event",type=Path,required=True)
    parser.add_argument("--pr-file",type=Path,required=True)
    parser.add_argument("--issue-file",type=Path,required=True)
    parser.add_argument("--lease-comments",type=Path,required=True)
    parser.add_argument("--run-id",type=int,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        event=json.loads(args.event.read_text("utf8"))
        pr=json.loads(args.pr_file.read_text("utf8"))
        issue=json.loads(args.issue_file.read_text("utf8"))
        comments=json.loads(args.lease_comments.read_text("utf8"))
        if comments and isinstance(comments[0],list):
            comments=[item for page in comments for item in page]
        result=ready_preflight(event,pr,comments,args.run_id,
                               datetime.now(timezone.utc),issue)
        args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\\n",
                            encoding="utf8")
        print(json.dumps({"state":result["status"],"pr":198,"release":"HOLD"}))
        return 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print("READY_HOLD "+str(exc),file=sys.stderr)
        return 2


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--pr", type=int, required=True)
    a.add_argument("--head-sha", required=True)
    a.add_argument("--changed-paths", type=Path, required=True)
    a.add_argument("--out", type=Path, required=True)
    a.add_argument("--root", type=Path, default=ROOT)
    for key in STEPS:
        a.add_argument("--" + key.replace("_", "-"), choices=sorted(OUTCOMES), required=True)
    opts = a.parse_args()
    changed = [x.strip() for x in opts.changed_paths.read_text(encoding="utf8").splitlines() if x.strip()]
    check(changed and len(changed) <= 1000, "Missing or excessive PR file list")
    scope = discover(opts.root.resolve(), changed)
    outcomes = {x: getattr(opts, x) for x in STEPS}
    result = route(opts.pr, opts.head_sha, outcomes, scope, datetime.now(timezone.utc).isoformat())
    opts.out.mkdir(parents=True, exist_ok=True)
    (opts.out / "gate-handoff.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    (opts.out / "gate-handoff.md").write_text(summary(result), encoding="utf8")
    print(json.dumps({"state": result["state"], "product_count": len(scope["ids"]), "release": "HOLD"}))

if __name__ == "__main__":
    if sys.argv[1:2] == ["ready-preflight"]:
        sys.exit(ready_main(sys.argv[2:]))
    try:
        main()
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print("FAIL_CLOSED " + str(exc), file=sys.stderr)
        sys.exit(2)
