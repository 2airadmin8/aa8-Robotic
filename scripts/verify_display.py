#!/usr/bin/env python3
"""Verify visible site structure and shared UI wiring in a built release."""
from __future__ import annotations

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

    expected_pc_logo = "brand-airadmin8-robotics-pc-v4.svg"
    expected_sp_logo = "brand-airadmin8-robotics-sp-v4.svg"
    forbidden = [
        "/aa8-Robotic/",
        "logo-airadmin8-robotics-pc.svg",
        "logo-airadmin8-robotics-sp.svg",
        "重点解説",
        "【80語】",
        "8分類×10語",
    ]

    for relative in [*pages, detail_pages[0].relative_to(SITE).as_posix()]:
        html = read(relative)
        require('data-shared-layout="header"' in html, f"Shared header missing: {relative}")
        require('data-shared-layout="footer"' in html, f"Shared footer missing: {relative}")
        require(expected_pc_logo in html, f"PC brand logo missing: {relative}")
        require(expected_sp_logo in html, f"SP brand logo missing: {relative}")
        require('class="menu"' in html, f"SP menu button missing: {relative}")
        require("data.menuReady" in html or "assets/js/site.js" in html, f"SP menu wiring missing: {relative}")
        for token in forbidden:
            require(token not in html, f"Forbidden public token {token!r}: {relative}")

    glossary = read("glossary.html")
    require("ロボット・フィジカルAI用語集" in glossary, "Glossary title missing")
    require('id="glossary-search"' in glossary, "Glossary search missing")
    require('data-category-filter=""' in glossary, "Glossary all-category filter missing")
    require("詳しく見る →" in glossary, "Glossary detail links missing")

    require((SITE / "assets/img" / expected_pc_logo).is_file(), "PC logo asset missing")
    require((SITE / "assets/img" / expected_sp_logo).is_file(), "SP logo asset missing")

    print("Display verification passed:")
    print("- shared header/footer")
    print("- PC/SP brand assets")
    print("- SP menu wiring")
    print("- glossary search/filter/detail links")
    print("- forbidden legacy paths and public labels absent")


if __name__ == "__main__":
    main()
