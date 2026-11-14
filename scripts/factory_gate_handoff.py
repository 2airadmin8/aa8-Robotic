#!/usr/bin/env python3
"""Existing PR CI -> auditable gate handoff. NEVER modifies Issues, PRs, CRM, or production.

Technical failures return to the original PR. Technical successes wait for
independent design/QA/business evidence, without self-approval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
from html import escape

ROOT = Path(__file__).resolve().parents[1]
VALID_OUTCOMES = {"success", "failure", "cancelled", "skipped", "unknown"}
REQUIRED_STEPS = ("regression", "build", "browser", "release", "source_clean")
HEX = set("0123456789abcdef")

def ensure(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)

def read_fixture(root: Path) -> dict:
    file = root / "tests/fixtures/x2-pilot/source-contract.json"
    data = json.loads(file.read_text(encoding="utf-8"))
    ensure(data["product_id"] == "agibot-x2-series", "Pilot ProductID mismatch")
    ensure(data["parameter_count"] == 36, "Official Japanese specs no longer 36")
    ensure(sum(data["parameter_groups"].values()) == 36, "Parameter group total mismatch")
    ensure(len(data["source_parameter_entries"]) == 36, "Source detail count mismatch")
    ensure(data["official_source"] == "https://agibot.com/jp/products/X2", "Official Japanese URL mismatch")
    ensure(data["image_approval"].startswith("CEO: X2 series general promotional image"), "Image approval missing")
    ensure(data["image_is_version_specific"] is False, "Generic hero must not be SKU-specific")
    ensure(data["source_reconciliation"]["legacy_cn_preserved"] is True, "Old manufacturer evidence lost")
    product = json.loads((root / "tests/fixtures/x2-pilot/product.json").read_text(encoding="utf-8"))
    ensure(product["id"] == data["product_id"], "Product fixture ID mismatch")
    ensure(product["pageFactory"]["releaseReady"] is False, "Isolated pilot cannot release")
    ensure(product.get("visibility") == "hidden", "Isolated pilot must stay hidden")
    ensure(len(product["pageFactory"]["specifications"]) == 36, "Candidate spec count mismatch")
    return data

def evaluate(*, head_sha: str, pr: int, outcomes: dict, source: dict, checked_at: str) -> dict:
    ensure(len(head_sha) == 40 and all(c in HEX for c in head_sha.lower()), "Invalid exact HEAD SHA")
    ensure(pr > 0, "PR number required for handoff")
    ensure(set(outcomes) == set(REQUIRED_STEPS), "Incomplete CI steps")
    ensure(all(v in VALID_OUTCOMES for v in outcomes.values()), "Invalid CI result")
    failed = [k for k in REQUIRED_STEPS if outcomes[k] in ("failure", "cancelled")]
    pending = [k for k in REQUIRED_STEPS if outcomes[k] in ("unknown", "skipped")]
    if failed:
        state, gate, owner = "RETURN_TO_DEV", "CI", "Original PR developer"
        next_action = "Fix CI: " + ", ".join(failed) + "; add regression; rerun on the same PR and exact new SHA"
    elif pending:
        state, gate, owner = "HOLD_EVIDENCE", "CI", "Original PR developer"
        next_action = "Provide missing CI evidence for: " + ", ".join(pending) + "; do not treat SKIP as PASS"
    else:
        state, gate, owner = "WAIT_DESIGN_QA", "G2", "Design / Independent QA owner"
        next_action = ("Validate actual X2 PC/SP against CEO-approved existing Figma template "
                       "on this exact SHA; record the design diff, then independent QA")
    gates = [
        {"id": "G0", "label": "X2 identity / series generic image", "status": "PASS", "evidence": "tests/fixtures/x2-pilot/source-contract.json"},
        {"id": "G1", "label": "36 Japanese specs / 9 categories", "status": "PASS", "evidence": "tests/fixtures/x2-pilot/source-contract.json"},
        {"id": "G2", "label": "Existing Figma design reuse / X2 visual comparison", "status": "HOLD", "evidence": None},
        {"id": "G3", "label": "Factory generation & CI regression", "status": "FAIL" if failed else "HOLD" if pending else "PASS", "evidence": "Actions CI"},
        {"id": "G4", "label": "Separate machine QA for exact HEAD", "status": "HOLD", "evidence": None},
        {"id": "G5", "label": "CTA real DEV business E2E / CRM", "status": "HOLD", "evidence": None},
        {"id": "G6", "label": "CEO interactive online Preview approval", "status": "HOLD", "evidence": None},
        {"id": "G7", "label": "Manual merge / Pages release approval", "status": "HOLD", "evidence": None},
    ]
    return {
        "schema_version": "gate-handoff-v1",
        "checked_at": checked_at,
        "issue": 129,
        "pr": pr,
        "pr_url": f"https://github.com/2airadmin8/aa8-Robotic/pull/{pr}",
        "product_id": source["product_id"],
        "head_sha": head_sha.lower(),
        "source": {"official": source["official_source"], "parameter_count": 36, "category_count": 9},
        "ci_outcomes": outcomes,
        "state": state,
        "blocking_gate": gate,
        "next_owner": owner,
        "next_action": next_action,
        "resume_from": f"same PR #{pr} (no duplicate branch/PR), HEAD {head_sha.lower()}",
        "gates": gates,
        "strict_release_status": "HOLD",
        "authorization": {"merge": False, "pages": False, "production_crm_write": False},
        "automatic_worker_started": False,
        "note": "CI event creates an auditable handoff; it does not autonomously launch or authorize an AI coding worker.",
    }

def markdown(record: dict) -> str:
    state = record["state"]
    rows = [
        f"## Product Factory Gate handoff · {escape(record['product_id'])}",
        "",
        f"**PR:** #{record['pr']} · **Exact HEAD:** `{record['head_sha']}`",
        f"**State:** `{state}` · **Release:** `HOLD`",
        f"**Blocking gate:** {record['blocking_gate']}",
        f"**Next owner:** {record['next_owner']}",
        f"**Next action:** {record['next_action']}",
        "",
        "| Gate | Status |",
        "|---|---|",
    ]
    rows.extend(f"| {g['id']} {g['label']} | {g['status']} |" for g in record["gates"])
    rows += ["", "No automatic merge, deploy, production CRM write, or AI worker execution.", ""]
    return "\n".join(rows)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    for step in REQUIRED_STEPS:
        parser.add_argument("--" + step.replace("_", "-"), required=True, choices=sorted(VALID_OUTCOMES))
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    data = read_fixture(args.root.resolve())
    outcomes = {key: getattr(args, key) for key in REQUIRED_STEPS}
    report = evaluate(head_sha=args.head_sha, pr=args.pr, outcomes=outcomes, source=data,
                      checked_at=datetime.now(timezone.utc).isoformat())
    dest = args.out.resolve()
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "gate-handoff.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", "utf-8")
    (dest / "gate-handoff.md").write_text(markdown(report), "utf-8")
    print(json.dumps({"state": report["state"], "pr": args.pr, "sha": args.head_sha,
                      "next_owner": report["next_owner"], "release": "HOLD"}))
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print("GATE HANDOFF CONTRACT FAIL: " + str(error), file=__import__("sys").stderr)
        raise SystemExit(2)
