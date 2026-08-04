#!/usr/bin/env python3
"""Verify glossary source data and generated output."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"
DATA = ROOT / "data" / "glossary.json"
EXPECTED_CATEGORIES = ["ロボット種別", "AI・方策", "学習・データ", "制御・動作", "認識・センサー", "開発基盤", "仮想検証", "導入・安全"]
REQUIRED_TERMS = {"具身AI", "VLA", "ロボット基盤モデル", "Diffusion Policy", "ACT", "Cross-Embodiment", "ROS 2 QoS", "Isaac Lab", "E-stop", "技適", "UN38.3"}


def main() -> int:
    errors: list[str] = []
    try:
        payload = json.loads(DATA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: glossary data unreadable: {exc}")
        return 1

    categories = payload.get("categories", [])
    terms = payload.get("terms", [])
    if categories != EXPECTED_CATEGORIES:
        errors.append(f"category order mismatch: {categories}")
    if len(terms) != 80:
        errors.append(f"term count must be 80, found {len(terms)}")
    counts = Counter(term[0] for term in terms if isinstance(term, list) and len(term) == 5)
    expected_counts = {category: 10 for category in EXPECTED_CATEGORIES}
    if counts != expected_counts:
        errors.append(f"category counts mismatch: {dict(counts)}")

    names = [term[1] for term in terms if isinstance(term, list) and len(term) == 5]
    if len(names) != len(set(names)):
        errors.append("duplicate glossary term names")
    missing_terms = sorted(REQUIRED_TERMS - set(names))
    if missing_terms:
        errors.append(f"missing required modern terms: {missing_terms}")

    slugs = [term[4] for term in terms if isinstance(term, list) and len(term) == 5 and term[4]]
    if len(slugs) < 24:
        errors.append(f"at least 24 priority detail pages required, found {len(slugs)}")
    if len(slugs) != len(set(slugs)):
        errors.append("duplicate glossary detail slugs")

    index_path = OUTPUT / "glossary.html"
    if not index_path.is_file():
        errors.append("generated glossary.html missing")
    else:
        index = index_path.read_text(encoding="utf-8")
        if index.count('class="term-card"') != 80:
            errors.append(f"generated glossary must contain 80 term cards, found {index.count('class=\"term-card\"')}")
        if index.count('class="glossary-category"') != 8:
            errors.append("generated glossary must contain 8 category sections")
        for marker in ("glossary-search", "data-category-filter", "DefinedTermSet", "具身AI", "ROS 2 QoS"):
            if marker not in index:
                errors.append(f"generated glossary missing marker: {marker}")

    for slug in slugs:
        path = OUTPUT / "glossary" / f"{slug}.html"
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"missing glossary detail page: {slug}.html")

    sitemap_path = OUTPUT / "sitemap.xml"
    if not sitemap_path.is_file():
        errors.append("sitemap.xml missing")
    else:
        sitemap = sitemap_path.read_text(encoding="utf-8")
        required_urls = ["https://robotics.air-admin8.co.jp/glossary.html", *[f"https://robotics.air-admin8.co.jp/glossary/{slug}.html" for slug in slugs]]
        for url in required_urls:
            if url not in sitemap:
                errors.append(f"sitemap missing glossary URL: {url}")
        if len(re.findall(r"https://robotics\.air-admin8\.co\.jp/glossary(?:/[^<]+)?\.html", sitemap)) != len(required_urls):
            errors.append("sitemap contains duplicate or stale glossary URLs")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Glossary verification FAILED with {len(errors)} error(s).")
        return 1
    print(f"Glossary verification PASSED: 80 terms, 8 categories, {len(slugs)} detail pages.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
