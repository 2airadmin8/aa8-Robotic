#!/usr/bin/env python3
"""P3 Factory efficiency ledger: no fabricated cycle times or fake ROI."""
from __future__ import annotations
import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ("sku_id", "pr_number", "source_ready_at", "preview_ready_at",
          "first_qa_at", "manual_code_edits", "rework_iterations",
          "ceo_interventions", "repeated_bug_count", "evidence_url",
          "record_status")
ALLOWED_STATUS = {"HISTORICAL_INCOMPLETE", "VERIFIED"}


def require(ok: bool, msg: str):
    if not ok:
        raise ValueError("FACTORY_KPI_HOLD: " + msg)


def parse_dt(value: str | None):
    if not value:
        return None
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(result.tzinfo is not None and result.utcoffset() is not None,
            "timezone-aware date required")
    return result


def normalized(record: dict) -> dict:
    require(set(record) == set(FIELDS), "exact ledger schema required")
    require(re.fullmatch("[a-z0-9]+(?:-[a-z0-9]+)*", record["sku_id"]) is not None,
            "invalid product id")
    require(str(record["pr_number"]).isdigit() and int(record["pr_number"]) > 0,
            "invalid PR")
    require(record["record_status"] in ALLOWED_STATUS, "invalid status")
    require(re.fullmatch(
        r"https://github\.com/2airadmin8/aa8-Robotic/(?:pull|issues)/\d+(?:#.*)?",
        record["evidence_url"]) is not None, "evidence must be real GitHub PR/issue")
    times = {field: parse_dt(record[field]) for field in
             ("source_ready_at", "preview_ready_at", "first_qa_at")}
    if times["source_ready_at"] and times["preview_ready_at"]:
        require(times["preview_ready_at"] >= times["source_ready_at"],
                "Preview before materials ready")
    if times["preview_ready_at"] and times["first_qa_at"]:
        require(times["first_qa_at"] >= times["preview_ready_at"],
                "QA before preview")
    for field in ("manual_code_edits", "rework_iterations",
                  "ceo_interventions", "repeated_bug_count"):
        raw = record[field]
        if raw not in ("", None):
            require(str(raw).isdigit(), field + " must be nonnegative integer")
    if record["record_status"] == "VERIFIED":
        require(times["source_ready_at"] is not None
                and times["preview_ready_at"] is not None,
                "verified speed needs actual timestamp evidence")
        require(all(record[k] not in ("", None) for k in (
            "manual_code_edits", "rework_iterations",
            "ceo_interventions", "repeated_bug_count")), "verified counts missing")
    require(record["rework_iterations"] in ("", None) or
            int(record["rework_iterations"]) <= 3,
            "more than three reworks requires HOLD")
    return {k: str(record[k] if record[k] is not None else "")
            for k in FIELDS}


def load(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        require(tuple(reader.fieldnames or ()) == FIELDS,
                "ledger header drift")
        records = [normalized(x) for x in reader]
    keys = [(x["sku_id"], x["pr_number"]) for x in records]
    require(len(keys) == len(set(keys)), "duplicate SKU/PR history")
    return records


def report(records: list[dict]) -> dict:
    spans = []
    for x in records:
        if x["record_status"] != "VERIFIED":
            continue
        a, b = parse_dt(x["source_ready_at"]), parse_dt(x["preview_ready_at"])
        spans.append({
            "sku_id": x["sku_id"], "pr_number": x["pr_number"],
            "minutes_source_to_preview": round((b - a).total_seconds() / 60, 1),
            "manual_code_edits": int(x["manual_code_edits"]),
            "rework_iterations": int(x["rework_iterations"]),
            "ceo_interventions": int(x["ceo_interventions"]),
            "repeated_bug_count": int(x["repeated_bug_count"]),
            "evidence": x["evidence_url"],
        })
    return {
        "schema": "aa8-factory-efficiency-report-v1",
        "total": len(records), "comparable": len(spans),
        "measurements": spans,
        "insufficientEvidence": len(spans) < 2,
        "efficiencyImprovementProven": False if len(spans) < 2 else None,
        "note": "No % improvement without at least two traceable comparable SKU runs.",
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--ledger", type=Path, default=ROOT / "ops/hp-factory-efficiency.csv")
    p.add_argument("--append", type=Path, help="verified event JSON only; never overwrite")
    p.add_argument("--report", type=Path, help="optional JSON output (safe aggregate)")
    args = p.parse_args()
    path = args.ledger.resolve()
    require(path.parent == (ROOT / "ops").resolve(),
            "ledger must stay in repository ops, never Production")
    records = load(path)
    if args.append:
        event = normalized(json.loads(args.append.read_text("utf-8")))
        require(not any((x["sku_id"], x["pr_number"]) ==
                        (event["sku_id"], event["pr_number"]) for x in records),
                "duplicate event requires explicit review")
        with path.open("a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writerow(event)
        records.append(event)
    result = report(records)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) +
                               "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
