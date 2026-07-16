#!/usr/bin/env python3
"""Smoke-test the generated _site artifact before GitHub Pages deployment."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"
REPORT = OUTPUT / "qa-report.json"
REQUIRED_FILES = [
    "index.html",
    "products.html",
    "support.html",
    "cases.html",
    "contact.html",
    "sitemap.xml",
    "robots.txt",
    "llms.txt",
    "site.webmanifest",
    "assets/img/favicon.svg",
    "assets/img/robot-category-lineup.svg",
    "assets/js/site.js",
    "assets/js/seo.js",
    "assets/css/site.css",
    "data/products.json",
]

STATIC_META_MARKERS = [
    'name="theme-color"',
    'rel="icon"',
    'rel="manifest"',
    'property="og:title"',
    'property="og:description"',
    'property="og:url"',
    'property="og:image"',
    'name="twitter:card"',
]

STRUCTURED_DATA_IDS = [
    "organization-schema",
    "page-schema",
    "breadcrumb-schema",
]


def main() -> int:
    errors: list[str] = []

    if not OUTPUT.exists():
        print("ARTIFACT ERROR: _site directory does not exist")
        return 1

    for relative in REQUIRED_FILES:
        path = OUTPUT / relative
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"Missing or empty built file: {relative}")

    try:
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        status = str(report.get("status", ""))
        if status == "fallback_build":
            errors.append("Primary build failed and fallback files were generated")
        elif status not in {"passed", "passed_with_findings"}:
            errors.append(f"Unexpected QA report status: {status or '(empty)'}")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"Cannot read built qa-report.json: {exc}")

    html_files = sorted(OUTPUT.rglob("*.html"))
    if len(html_files) < 10:
        errors.append(f"Too few HTML pages in artifact: {len(html_files)}")

    invalid_gtm = "googletagmanager.com/gtm.js?id=GT-5NXF29HN"
    for path in html_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        relative = path.relative_to(OUTPUT)

        if invalid_gtm in text:
            errors.append(f"Invalid Google Tag Manager loader remains: {relative}")
        if "AirAdmin8 Robotics" not in text:
            errors.append(f"Brand text missing from built HTML: {relative}")
        if path.name != "404.html" and 'rel="canonical"' not in text:
            errors.append(f"Canonical missing from built HTML: {relative}")
        if "site-header" not in text or 'class="footer"' not in text:
            errors.append(f"Shared header/footer missing from built HTML: {relative}")
        if "会社情報" not in text:
            errors.append(f"Company information link missing from built HTML: {relative}")

        for marker in STATIC_META_MARKERS:
            if marker not in text:
                errors.append(f"Static metadata marker missing from {relative}: {marker}")

        for element_id in STRUCTURED_DATA_IDS:
            marker = f'id="{element_id}" type="application/ld+json"'
            count = text.count(marker)
            if count != 1:
                errors.append(
                    f"Structured data id must appear exactly once in {relative}: "
                    f"{element_id} ({count})"
                )

        json_ld_payloads = re.findall(
            r'<script\s+id="(?:organization-schema|page-schema|breadcrumb-schema)"\s+type="application/ld\+json">(.*?)</script>',
            text,
            flags=re.DOTALL,
        )
        for index, payload in enumerate(json_ld_payloads, start=1):
            try:
                json.loads(payload.replace("<\\/", "</"))
            except json.JSONDecodeError as exc:
                errors.append(f"Invalid JSON-LD in {relative} #{index}: {exc}")

    contact = OUTPUT / "contact.html"
    if contact.exists():
        contact_text = contact.read_text(encoding="utf-8", errors="replace")
        required_contact_markers = [
            "data-contact-form",
            "data-contact-confirm",
            "contact-v2.js",
            "airobot@robotics.air-admin8.co.jp",
        ]
        for marker in required_contact_markers:
            if marker not in contact_text:
                errors.append(f"Contact artifact missing marker: {marker}")

    products = OUTPUT / "products.html"
    if products.exists():
        products_text = products.read_text(encoding="utf-8", errors="replace")
        if "data-product-list" not in products_text:
            errors.append("Products artifact is missing dynamic product list root")

    sitemap = OUTPUT / "sitemap.xml"
    if sitemap.exists():
        sitemap_text = sitemap.read_text(encoding="utf-8", errors="replace")
        url_count = len(re.findall(r"<url>", sitemap_text))
        if url_count < 20:
            errors.append(f"Sitemap contains too few URLs: {url_count}")

    if errors:
        for error in errors:
            print(f"ARTIFACT ERROR: {error}")
        print(f"Built-site smoke test failed with {len(errors)} error(s).")
        return 1

    print(f"Built-site smoke test passed: {len(html_files)} HTML pages checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
