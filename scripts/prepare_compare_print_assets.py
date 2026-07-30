#!/usr/bin/env python3
"""Prepare comparison print assets, prefer Japanese brand wording, strengthen entity signals, normalize origin, and validate links."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from fix_unconfirmed_product_schema import fix_unconfirmed_product_schema
from inject_typography_system import inject_typography_system
from japanese_brand_language import prefer_japanese_brand_language
from normalize_public_origin import normalize_public_origin
from strengthen_brand_entity import strengthen_brand_entity
from validate_internal_links import validate_internal_links

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"
PRODUCTS_HTML = OUTPUT / "products.html"
COMPARE_JS = OUTPUT / "assets" / "js" / "product-compare.js"
COMPARE_CSS = OUTPUT / "assets" / "css" / "product-compare.css"
BUILD_LOG = ROOT / "build.log"
CSS_VERSION = "20260716-5"
JS_VERSION = "20260716-4"


def persist_errors(errors: list[str]) -> None:
    if not errors:
        return
    with BUILD_LOG.open("a", encoding="utf-8") as handle:
        handle.write("\n--- FINAL BUILD VALIDATION ---\n")
        for error in errors:
            handle.write(f"BUILD FINALIZE ERROR: {error}\n")


def main() -> int:
    errors: list[str] = []

    for path in (PRODUCTS_HTML, COMPARE_JS, COMPARE_CSS):
        if not path.is_file():
            errors.append(f"Missing comparison print asset: {path.relative_to(OUTPUT)}")

    if errors:
        persist_errors(errors)
        for error in errors:
            print(f"COMPARE PRINT ERROR: {error}")
        return 1

    html = PRODUCTS_HTML.read_text(encoding="utf-8")
    html = re.sub(
        r'assets/css/product-compare\.css(?:\?v=[^"\']+)?',
        f'assets/css/product-compare.css?v={CSS_VERSION}',
        html,
    )
    html = re.sub(
        r'assets/js/product-compare\.js(?:\?v=[^"\']+)?',
        f'assets/js/product-compare.js?v={JS_VERSION}',
        html,
    )
    PRODUCTS_HTML.write_text(html, encoding="utf-8")

    js = COMPARE_JS.read_text(encoding="utf-8")
    css = COMPARE_CSS.read_text(encoding="utf-8")

    required_js_markers = [
        "compare-print-sheet",
        "afterprint",
        "requestAnimationFrame",
        "60000",
        "dialog.close()",
    ]
    required_css_markers = [
        "body.is-printing-comparison > *",
        "body.is-printing-comparison > .compare-print-sheet",
        "@page { size: A4 landscape",
        "display: table-header-group",
        "page-break-inside: avoid",
    ]

    for marker in required_js_markers:
        if marker not in js:
            errors.append(f"Missing iPhone print JavaScript marker: {marker}")
    for marker in required_css_markers:
        if marker not in css:
            errors.append(f"Missing comparison print CSS marker: {marker}")

    expected_css = f'assets/css/product-compare.css?v={CSS_VERSION}'
    expected_js = f'assets/js/product-compare.js?v={JS_VERSION}'
    if expected_css not in html:
        errors.append(f"Built products.html is missing cache-busted CSS: {expected_css}")
    if expected_js not in html:
        errors.append(f"Built products.html is missing cache-busted JS: {expected_js}")

    typography_count, typography_errors = inject_typography_system(OUTPUT)
    errors.extend(typography_errors)
    japanese_count, japanese_errors = prefer_japanese_brand_language(OUTPUT)
    errors.extend(japanese_errors)
    brand_count, brand_errors = strengthen_brand_entity(OUTPUT)
    errors.extend(brand_errors)
    product_schema_count, product_schema_errors = fix_unconfirmed_product_schema(OUTPUT)
    errors.extend(product_schema_errors)
    normalized_count, origin_errors = normalize_public_origin(OUTPUT)
    errors.extend(origin_errors)
    errors.extend(validate_internal_links(OUTPUT))

    if errors:
        persist_errors(errors)
        for error in errors:
            print(f"BUILD FINALIZE ERROR: {error}")
        print(f"Final build preparation failed with {len(errors)} error(s).")
        return 1

    print(
        "Comparison print assets prepared, shared typography applied, Japanese-first AirAdmin8 wording applied, "
        "brand entity strengthened, unconfirmed Product rich-result markup cleaned, public origin normalized, "
        "and internal links validated "
        f"({typography_count} typography-updated page(s), {japanese_count} Japanese-updated page(s), "
        f"{brand_count} brand-updated page(s), {product_schema_count} product-schema-cleaned page(s), "
        f"{normalized_count} origin-normalized file(s))."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
