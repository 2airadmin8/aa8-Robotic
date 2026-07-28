#!/usr/bin/env python3
"""Remove invalid Google Product rich-result markup from unconfirmed products.

These pages describe products whose price / offer conditions are not yet confirmed.
Publishing Product JSON-LD without offers, review, or aggregateRating makes Google
Search Console report an invalid product snippet. We therefore keep the pages as
normal WebPage structured data until a real, verifiable offer exists.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"

TARGETS = {
    "products/tianji-marvin.html",
    "products/agibot-x2-edu.html",
}

PAGE_SCHEMA_PATTERN = re.compile(
    r'(<script\s+id=["\']page-schema["\']\s+type=["\']application/ld\+json["\']>)(.*?)(</script>)',
    re.IGNORECASE | re.DOTALL,
)

PRODUCT_ONLY_KEYS = {"brand", "category", "image"}


def fix_unconfirmed_product_schema(output: Path = OUTPUT) -> tuple[int, list[str]]:
    updated = 0
    errors: list[str] = []

    for relative in sorted(TARGETS):
        path = output / relative
        if not path.is_file():
            errors.append(f"Missing target page: {relative}")
            continue

        text = path.read_text(encoding="utf-8")
        match = PAGE_SCHEMA_PATTERN.search(text)
        if not match:
            errors.append(f"Missing page-schema: {relative}")
            continue

        try:
            data = json.loads(match.group(2))
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid page-schema in {relative}: {exc}")
            continue

        if data.get("@type") != "Product":
            errors.append(f"Expected Product page-schema before cleanup: {relative}")
            continue

        data["@type"] = "WebPage"
        for key in PRODUCT_ONLY_KEYS:
            data.pop(key, None)

        action = data.get("potentialAction")
        if isinstance(action, dict) and action.get("@type") == "AskAction":
            # Keep a useful inquiry action on the WebPage; it is not Product offer markup.
            pass

        payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        replacement = f"{match.group(1)}{payload}{match.group(3)}"
        text = text[: match.start()] + replacement + text[match.end() :]
        path.write_text(text, encoding="utf-8")
        updated += 1

        # Regression guard: these pages must not advertise Product rich-result markup
        # until verified offer/review data is intentionally added.
        verify = PAGE_SCHEMA_PATTERN.search(text)
        if not verify:
            errors.append(f"page-schema disappeared after cleanup: {relative}")
            continue
        verify_data = json.loads(verify.group(2))
        if verify_data.get("@type") == "Product":
            errors.append(f"Product markup still present after cleanup: {relative}")

    return updated, errors


if __name__ == "__main__":
    count, problems = fix_unconfirmed_product_schema()
    for problem in problems:
        print(f"PRODUCT SNIPPET ERROR: {problem}")
    print(f"Unconfirmed product schema cleaned on {count} page(s).")
    raise SystemExit(1 if problems else 0)
