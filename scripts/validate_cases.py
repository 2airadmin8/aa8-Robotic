#!/usr/bin/env python3
"""Validate public case evidence and disclosure rules."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "case-evidence.json"


def main() -> int:
    errors: list[str] = []

    try:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"CASE ERROR: cannot read {DATA_PATH.relative_to(ROOT)}: {exc}")
        return 1

    rules = data.get("disclosureRules", {})
    allowed_levels = set(rules.get("allowedEvidenceLevels", []))
    allowed_statuses = set(rules.get("allowedCaseStatuses", []))
    seen_ids: set[str] = set()
    seen_pages: set[str] = set()

    for case in data.get("cases", []):
        case_id = str(case.get("id", "")).strip()
        title = str(case.get("title", "")).strip()
        page = str(case.get("detailPage", "")).strip()
        status = str(case.get("status", "")).strip()
        disclaimer = str(case.get("publicDisclaimer", "")).strip()

        if not case_id:
            errors.append("Case is missing id")
        elif case_id in seen_ids:
            errors.append(f"Duplicate case id: {case_id}")
        seen_ids.add(case_id)

        if not title:
            errors.append(f"Case {case_id or '<unknown>'} is missing title")
        if not page:
            errors.append(f"Case {case_id or '<unknown>'} is missing detailPage")
        elif page in seen_pages:
            errors.append(f"Duplicate case detailPage: {page}")
        else:
            seen_pages.add(page)
            if not (ROOT / page).exists():
                errors.append(f"Missing case detail page: {page}")

        if status not in allowed_statuses:
            errors.append(f"Invalid status for {case_id}: {status}")
        if rules.get("requirePublicDisclaimer") and not disclaimer:
            errors.append(f"Missing public disclaimer for {case_id}")
        if status != "completed" and any(word in title for word in ("導入完了", "納品完了", "稼働実績")):
            errors.append(f"Unverified completion wording for {case_id}: {title}")

        evidence = case.get("evidence", [])
        if not evidence:
            errors.append(f"Case {case_id} has no evidence entries")
        for index, item in enumerate(evidence, start=1):
            level = str(item.get("level", "")).strip()
            label = str(item.get("label", "")).strip()
            description = str(item.get("description", "")).strip()
            if level not in allowed_levels:
                errors.append(f"Invalid evidence level for {case_id} #{index}: {level}")
            if not label or not description:
                errors.append(f"Incomplete evidence entry for {case_id} #{index}")

        progress = case.get("progress", [])
        current_count = sum(1 for item in progress if item.get("state") == "current")
        if status == "in_progress" and current_count != 1:
            errors.append(f"In-progress case {case_id} must have exactly one current step")
        orders = [item.get("order") for item in progress]
        if orders != sorted(orders) or len(orders) != len(set(orders)):
            errors.append(f"Invalid progress order for {case_id}")

    if errors:
        for error in errors:
            print(f"CASE ERROR: {error}")
        print(f"Case validation failed with {len(errors)} error(s).")
        return 1

    print(f"Case validation passed for {len(data.get('cases', []))} case(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
