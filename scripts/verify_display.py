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


def main() -> None:
    pages = ["index.html", "products.html", "glossary.html"]
    detail_pages = sorted((SITE / "glossary").glob("*.html"))
    require(detail_pages, "No glossary detail pages were generated")

    expected_pc_logo = "airadmin8-robotics-logo-pc.svg"
    expected_sp_logo = "airadmin8-robotics-logo-sp.svg"
    expected_footer_logo = "airadmin8-robotics-logo-footer.svg"
    expected_header_runtime = "assets/js/shared-header-runtime.js"
    forbidden_public_text = ["重点解説", "【80語】", "8分類×10語"]
    forbidden_brand_tokens = [
        "airadmin8-192x192.svg",
        "airadmin8-official-logo.png",
        "brand-airadmin8-robotics-pc-v4.svg",
        "brand-airadmin8-robotics-sp-v4.svg",
        "logo-airadmin8-robotics-pc.svg",
        "logo-airadmin8-robotics-sp.svg",
        "assets/img/brand/",
    ]
    legacy_link_pattern = re.compile(r'(?:href|src|srcset)=["\'][^"\']*/aa8-Robotic/', re.IGNORECASE)

    for relative in [*pages, detail_pages[0].relative_to(SITE).as_posix()]:
        html = read(relative)
        require('data-shared-layout="header"' in html, f"Shared header missing: {relative}")
        require('data-shared-layout="footer"' in html, f"Shared footer missing: {relative}")
        require(expected_pc_logo in html, f"PC brand logo missing: {relative}")
        require(expected_sp_logo in html, f"SP brand logo missing: {relative}")
        require(expected_footer_logo in html, f"Footer brand logo missing: {relative}")
        require('class="menu"' in html, f"SP menu button missing: {relative}")
        require(expected_header_runtime in html, f"SP menu runtime missing: {relative}")
        require(not legacy_link_pattern.search(html), f"Legacy repository path in link attribute: {relative}")
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
        "airadmin8-symbol.svg",
        "airadmin8-wordmark.svg",
        "airadmin8-robotics-badge.svg",
        "favicon-airadmin8.svg",
        "airadmin8-icon-192.png",
        "airadmin8-icon-512.png",
        "apple-touch-icon.png",
        "shared-header-runtime.js",
    ]
    for asset in required_assets:
        asset_path = SITE / ("assets/js" if asset.endswith(".js") else "assets/img") / asset
        require(asset_path.is_file(), f"Brand asset missing: {asset}")

    runtime = (SITE / expected_header_runtime).read_text(encoding="utf-8")
    require("airadmin8-robotics-logo-pc.svg" in runtime, "PC logo runtime restoration missing")
    require("airadmin8-robotics-logo-sp.svg" in runtime, "SP logo runtime restoration missing")
    require("menuReady" in runtime and "classList.toggle('open')" in runtime, "Mobile menu runtime binding missing")

    print("Display verification passed:")
    print("- shared header/footer")
    print("- official PC/SP/Footer brand assets")
    print("- favicon and app icons")
    print("- shared header runtime")
    print("- SP menu wiring")
    print("- glossary search/filter/detail links")
    print("- legacy logo paths absent")


if __name__ == "__main__":
    main()
