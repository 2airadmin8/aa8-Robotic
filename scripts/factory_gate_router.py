#!/usr/bin/env python3
"""General PR Factory gate router; reports only, never launches workers or releases."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
STEPS = ("regression", "build", "browser", "release", "source_clean")
OUTCOMES = {"success", "failure", "cancelled", "skipped", "unknown"}

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
    for filename in paths:
        check(not filename.startswith("/") and "\\" not in filename and ".." not in Path(filename).parts,
              "Invalid changed path")
        if filename == "data/products.json":
            ambiguous.append(filename)
        if filename in {"scripts/product_factory.py", "scripts/product_page_standard_v31.py",
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
    scope = ("MULTI_PRODUCT" if len(found) > 1 else "PRODUCT" if found else
             "GLOBAL_FACTORY" if global_change else "INPUT_REQUIRED" if ambiguous else "NO_PRODUCT_SCOPE")
    return {"ids": sorted(found), "global_factory_change": global_change,
            "ambiguous": ambiguous, "master_count": len(official), "fixture_count": len(pilots),
            "work_scope": scope}

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
        "product_gates": [{"product_id": pid, "design": "HOLD", "independent_qa": "HOLD",
                           "business_e2e": "HOLD", "ceo": "HOLD"} for pid in scope["ids"]],
        "executor": {"developer_machine": "AA8-N-018", "qa_machine": "AA8-N-015",
                     "auto_wakeup": "NOT_CONNECTED", "auto_commit": False,
                     "independent_qa_trigger": "NOT_CONNECTED"},
        "release": "HOLD", "authorized": {"merge": False, "pages": False, "crm_write": False}
    }

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
    try:
        main()
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print("FAIL_CLOSED " + str(exc), file=sys.stderr)
        sys.exit(2)
