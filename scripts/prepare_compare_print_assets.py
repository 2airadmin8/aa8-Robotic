#!/usr/bin/env python3
"""Prepare comparison print assets, normalize public origin, and validate links."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from normalize_public_origin import normalize_public_origin
from validate_internal_links import validate_internal_links

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"
PRODUCTS_HTML = OUTPUT / "products.html"
COMPARE_JS = OUTPUT / "assets" / "js" / "product-compare.js"
COMPARE_CSS = OUTPUT / "assets" / "css" / "product-compare.css"
CSS_VERSION = "20260716-5"
JS_VERSION = "20260716-4"


def main() -> int:
    errors: list[str] = []

    for path in (PRODUCTS_HTML, COMPARE_JS, COMPARE_CSS):
        if not path.is_file():
            errors.append(f"Missing comparison print asset: {path.relative_to(OUTPUT)}")

    if errors:
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

    normalized_count, origin_errors = normalize_public_origin(OUTPUT)
    errors.extend(origin_errors)
    errors.extend(validate_internal_links(OUTPUT))

    if errors:
        for error in errors:
            print(f"BUILD FINALIZE ERROR: {error}")
        print(f"Final build preparation failed with {len(errors)} error(s).")
        return 1

    print(
        "Comparison print assets prepared, public origin normalized, and internal links validated "
        f"({normalized_count} origin-normalized file(s))."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
