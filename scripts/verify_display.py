#!/usr/bin/env python3
"""Verify visible site structure and shared UI wiring in a built release."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def read(relative: str) -> str:
    path = SITE / relative
    require(path.is_file(), f"Missing display target: {relative}")
    return path.read_text(encoding="utf-8")


def count_shared_element(html: str, tag: str, layout: str) -> int:
    pattern = re.compile(
        rf'<{tag}\b(?=[^>]*\bdata-shared-layout=["\']{re.escape(layout)}["\'])[^>]*>',
        re.IGNORECASE,
    )
    return len(pattern.findall(html))


def count_glossary_footer_links(html: str) -> int:
    pattern = re.compile(
        r'<a\b[^>]*\bhref=["\'](?:\.\./)*/?glossary\.html["\'][^>]*>\s*用語集\s*</a>',
        re.IGNORECASE,
    )
    return len(pattern.findall(html))


def main() -> None:
    pages = ["index.html", "products.html", "glossary.html"]
    detail_pages = sorted((SITE / "glossary").glob("*.html"))
    require(detail_pages, "No glossary detail pages were generated")

    expected_pc_logo = "airadmin8-robotics-logo-pc.svg"
    expected_sp_logo = "airadmin8-robotics-logo-sp.svg"
    expected_footer_logo = "airadmin8-robotics-logo-footer.svg"
    expected_favicon = "favicon-airadmin8.svg"
    forbidden_public_text = ["重点解説", "【80語】", "8分類×10語"]
    forbidden_brand_tokens = [
        "airadmin8-192x192.svg",
        "airadmin8-official-logo.png",
        "brand-airadmin8-robotics-pc-v4.svg",
        "brand-airadmin8-robotics-sp-v4.svg",
        "logo-airadmin8-robotics-pc.svg",
        "logo-airadmin8-robotics-sp.svg",
        "airadmin8-symbol-192.svg",
        "airadmin8-symbol.svg",
        "assets/img/brand/",
        "shared-header-runtime.js",
    ]
    legacy_link_pattern = re.compile(r'(?:href|src|srcset)=["\'][^"\']*/aa8-Robotic/', re.IGNORECASE)

    checked_pages = [*pages, detail_pages[0].relative_to(SITE).as_posix()]
    for relative in checked_pages:
        html = read(relative)
        require(count_shared_element(html, "header", "header") == 1, f"Shared header count is not 1: {relative}")
        require(count_shared_element(html, "footer", "footer") == 1, f"Shared footer count is not 1: {relative}")
        require(expected_pc_logo in html, f"PC brand logo missing: {relative}")
        require(expected_sp_logo in html, f"SP brand logo missing: {relative}")
        require(expected_footer_logo in html, f"Footer brand logo missing: {relative}")
        require(expected_favicon in html, f"SVG favicon missing: {relative}")
        require('class="native-nav"' in html, f"Native SP navigation missing: {relative}")
        require('<summary aria-label="メニューを開閉する">メニュー</summary>' in html, f"Native SP menu summary missing: {relative}")
        require('.native-nav[open] .nav' in html, f"Native SP menu open-state CSS missing: {relative}")
        require(not legacy_link_pattern.search(html), f"Legacy repository path in link attribute: {relative}")

        require(html.count('data-aa8-footer-layout="true"') == 1, f"Footer layout guard count is not 1: {relative}")
        require(count_glossary_footer_links(html) >= 2, f"Glossary links missing from footer navigation: {relative}")
        require('class="footer-brand-block"' in html, f"Footer brand block missing: {relative}")
        require('class="footer-links"' in html, f"Footer primary navigation missing: {relative}")
        require('class="footer-utility-links"' in html, f"Footer utility navigation missing: {relative}")
        for label in ["製品", "用途", "ソリューション", "導入事例", "資料・SDK", "用語集", "相談"]:
            require(label in html, f"Required footer label {label!r} missing: {relative}")

        for token in [*forbidden_public_text, *forbidden_brand_tokens]:
            require(token not in html, f"Forbidden token {token!r}: {relative}")

    glossary = read("glossary.html")
    require("ロボット・フィジカルAI用語集" in glossary, "Glossary title missing")
    require('id="glossary-search"' in glossary, "Glossary search missing")
    require('data-category-filter=""' in glossary, "Glossary all-category filter missing")
    require("詳しく見る →" in glossary, "Glossary detail links missing")

    required_assets = [
        expected_pc_logo,
        expected_sp_logo,
        expected_footer_logo,
        expected_favicon,
        "airadmin8-wordmark.svg",
        "airadmin8-robotics-badge.svg",
        "airadmin8-icon-192.png",
        "airadmin8-icon-512.png",
        "apple-touch-icon.png",
    ]
    for asset in required_assets:
        require((SITE / "assets/img" / asset).is_file(), f"Brand asset missing: {asset}")

    require(not (SITE / "assets/img/airadmin8-symbol-192.svg").exists(), "Incorrect SVG shortcut icon still published")
    require(not (SITE / "assets/img/airadmin8-symbol.svg").exists(), "Legacy symbol SVG still published")
    require(not (SITE / "assets/js/shared-header-runtime.js").exists(), "Obsolete shared header runtime still published")

    print("Display verification passed:")
    print("- one shared header and footer element")
    print("- uploaded PC/SP/Footer brand assets")
    print("- uploaded SVG favicon")
    print("- uploaded 192px and 512px PNG app icons")
    print("- incorrect legacy symbol SVGs absent")
    print("- native SP menu structure and open-state CSS")
    print("- obsolete header runtime absent")
    print("- glossary search/filter/detail links")
    print("- footer layout guard and required navigation")
    print("- legacy logo paths absent")


if __name__ == "__main__":
    main()
