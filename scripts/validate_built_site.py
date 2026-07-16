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
PRODUCTS_DATA = OUTPUT / "data" / "products.json"
RESOURCES_DATA = OUTPUT / "data" / "resources.json"
REQUIRED_FILES = [
    "index.html",
    "products.html",
    "support.html",
    "cases.html",
    "contact.html",
    "faq.html",
    "resources.html",
    "sitemap.xml",
    "robots.txt",
    "llms.txt",
    "site.webmanifest",
    "assets/img/favicon.svg",
    "assets/img/robot-category-lineup.svg",
    "assets/js/site.js",
    "assets/js/seo.js",
    "assets/js/resource-static-filter.js",
    "assets/css/site.css",
    "assets/css/accessibility.css",
    "data/products.json",
    "data/resources.json",
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

ACCESSIBILITY_MARKERS = [
    'class="skip-link" href="#main-content"',
    'id="main-content"',
    'assets/css/accessibility.css',
]


def extract_json_ld(text: str, element_id: str) -> dict[str, object] | None:
    match = re.search(
        rf'<script\s+id="{re.escape(element_id)}"\s+type="application/ld\+json">(.*?)</script>',
        text,
        flags=re.DOTALL,
    )
    if not match:
        return None
    return json.loads(match.group(1).replace("<\\/", "</"))


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

        for marker in ACCESSIBILITY_MARKERS:
            count = text.count(marker)
            if count != 1:
                errors.append(
                    f"Accessibility marker must appear exactly once in {relative}: "
                    f"{marker} ({count})"
                )

        if not re.search(r'<main\b[^>]*\bid="main-content"[^>]*>', text, flags=re.IGNORECASE):
            errors.append(f"main-content id is not attached to <main>: {relative}")

        for element_id in STRUCTURED_DATA_IDS:
            marker = f'id="{element_id}" type="application/ld+json"'
            count = text.count(marker)
            if count != 1:
                errors.append(
                    f"Structured data id must appear exactly once in {relative}: "
                    f"{element_id} ({count})"
                )

        ids_to_parse = list(STRUCTURED_DATA_IDS)
        if relative.as_posix() == "faq.html":
            faq_marker = 'id="faq-schema" type="application/ld+json"'
            faq_count = text.count(faq_marker)
            if faq_count != 1:
                errors.append(f"FAQ schema must appear exactly once in faq.html ({faq_count})")
            ids_to_parse.append("faq-schema")
        elif 'id="faq-schema"' in text:
            errors.append(f"FAQ schema must not appear outside faq.html: {relative}")

        for element_id in ids_to_parse:
            try:
                payload = extract_json_ld(text, element_id)
                if payload is None:
                    continue
                if element_id == "faq-schema":
                    entries = payload.get("mainEntity", [])
                    if payload.get("@type") != "FAQPage":
                        errors.append("faq-schema @type must be FAQPage")
                    if not isinstance(entries, list) or len(entries) < 5:
                        errors.append(
                            f"faq-schema contains too few questions: "
                            f"{len(entries) if isinstance(entries, list) else 0}"
                        )
                    for index, entry in enumerate(entries, start=1):
                        question = str(entry.get("name", "")).strip()
                        answer = str(entry.get("acceptedAnswer", {}).get("text", "")).strip()
                        if not question or not answer:
                            errors.append(f"Incomplete FAQ entry #{index}")
            except json.JSONDecodeError as exc:
                errors.append(f"Invalid JSON-LD in {relative} ({element_id}): {exc}")

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
        if 'data-prerendered-products="true"' not in products_text:
            errors.append("Products artifact is missing pre-render marker")

        try:
            catalog = json.loads(PRODUCTS_DATA.read_text(encoding="utf-8"))
            public_products = [
                item for item in catalog.get("products", []) if item.get("visibility") == "public"
            ]
            card_count = products_text.count('class="product-card research-product-card"')
            if card_count != len(public_products):
                errors.append(
                    f"Pre-rendered product card count mismatch: {card_count} != {len(public_products)}"
                )
            for item in public_products:
                product_id = str(item.get("id", ""))
                if f'id="{product_id}" class="product-card research-product-card"' not in products_text:
                    errors.append(f"Pre-rendered product card missing: {product_id}")
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(f"Cannot validate pre-rendered product cards: {exc}")

    resources = OUTPUT / "resources.html"
    if resources.exists():
        resources_text = resources.read_text(encoding="utf-8", errors="replace")
        if "data-resource-list" not in resources_text:
            errors.append("Resources artifact is missing dynamic resource list root")
        if "assets/js/resource-static-filter.js" not in resources_text:
            errors.append("Resources artifact is missing static resource filter script")

        try:
            resource_catalog = json.loads(RESOURCES_DATA.read_text(encoding="utf-8"))
            resource_items = resource_catalog.get("resources", [])
            expected_count = len(resource_items)
            marker = f'data-prerendered-resources="{expected_count}"'
            if marker not in resources_text:
                errors.append(f"Resources artifact is missing pre-render marker: {marker}")

            card_count = resources_text.count('class="resource-card" data-resource-id=')
            if card_count != expected_count:
                errors.append(
                    f"Pre-rendered resource card count mismatch: {card_count} != {expected_count}"
                )
            for item in resource_items:
                resource_id = str(item.get("id", ""))
                if f'id="resource-{resource_id}" class="resource-card"' not in resources_text:
                    errors.append(f"Pre-rendered resource card missing: {resource_id}")
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(f"Cannot validate pre-rendered resource cards: {exc}")

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
