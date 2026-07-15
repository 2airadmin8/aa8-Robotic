#!/usr/bin/env python3
"""Validate page-level SEO keyword ownership.

This check prevents duplicate primary keywords and references to missing pages.
It is intentionally limited to structural governance; editorial quality remains
part of manual review.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEO_DATA = ROOT / "data" / "seo-keywords.json"


def main() -> int:
    errors: list[str] = []

    try:
        data = json.loads(SEO_DATA.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"SEO validation failed: {exc}")
        return 1

    pages = data.get("pages", [])
    if not isinstance(pages, list) or not pages:
        print("SEO validation failed: pages must be a non-empty list.")
        return 1

    primary_keywords: list[str] = []
    paths: list[str] = []

    for index, page in enumerate(pages, start=1):
        if not isinstance(page, dict):
            errors.append(f"Entry {index}: page must be an object.")
            continue

        path = str(page.get("path", "")).strip()
        keyword = str(page.get("primaryKeyword", "")).strip()
        intent = str(page.get("searchIntent", "")).strip()
        priority = str(page.get("priority", "")).strip()

        if not path:
            errors.append(f"Entry {index}: missing path.")
        else:
            paths.append(path)
            if not (ROOT / path).is_file():
                errors.append(f"Missing HTML target: {path}")

        if not keyword:
            errors.append(f"Entry {index}: missing primaryKeyword.")
        else:
            primary_keywords.append(keyword.casefold())

        if not intent:
            errors.append(f"Entry {index}: missing searchIntent.")
        if priority not in {"S", "A", "B", "C"}:
            errors.append(f"Entry {index}: invalid priority '{priority}'.")

    duplicate_paths = [item for item, count in Counter(paths).items() if count > 1]
    duplicate_keywords = [
        item for item, count in Counter(primary_keywords).items() if count > 1
    ]

    for path in duplicate_paths:
        errors.append(f"Duplicate SEO page path: {path}")
    for keyword in duplicate_keywords:
        errors.append(f"Duplicate primary keyword: {keyword}")

    if errors:
        for error in errors:
            print(f"SEO ERROR: {error}")
        return 1

    print(f"SEO validation passed for {len(pages)} pages.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
