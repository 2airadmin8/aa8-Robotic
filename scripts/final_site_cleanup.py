#!/usr/bin/env python3
"""Apply final sitewide brand wording and glossary layout rules."""

from __future__ import annotations

import re
from pathlib import Path

REMOVE_SENTENCE = "AIロボット・フィジカルAIの選定、比較、導入、PoCを支援します。"


def finalize_site(output: Path) -> tuple[int, list[str]]:
    errors: list[str] = []
    updated = 0

    for path in output.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        new = text.replace("AIRADMIN8", "AirAdmin8")
        new = new.replace(REMOVE_SENTENCE, "")
        new = new.replace("79用語の一覧へ", "用語の一覧へ")
        new = new.replace("79用語", "用語")
        new = new.replace("glossary.css?v=20260731-2", "glossary.css?v=20260731-3")
        new = new.replace("main-site-experience.js?v=20260731-2", "main-site-experience.js?v=20260731-3")

        if path.name == "glossary.html":
            hero = re.search(r'<section class="glossary-hero">.*?</section>', new, flags=re.DOTALL)
            tools = re.search(r'<section class="glossary-tools">.*?</section>', new, flags=re.DOTALL)
            if hero and tools and hero.start() < tools.start():
                new = new[:hero.start()] + tools.group(0) + hero.group(0) + new[tools.end():]

        if path.name == "404.html" and "company.html" not in new:
            company_link = '<a href="company.html">会社情報</a>'
            footer_links = re.search(r'(<div class="footer-links"[^>]*>)(.*?)(</div>)', new, flags=re.DOTALL)
            if footer_links:
                replacement = footer_links.group(1) + company_link + footer_links.group(2) + footer_links.group(3)
                new = new[:footer_links.start()] + replacement + new[footer_links.end():]
            elif "</footer>" in new:
                new = new.replace("</footer>", company_link + "</footer>", 1)

        if new != text:
            path.write_text(new, encoding="utf-8")
            updated += 1

        if "AIRADMIN8" in new:
            errors.append(f"Uppercase AIRADMIN8 remains: {path.relative_to(output)}")
        if REMOVE_SENTENCE in new:
            errors.append(f"Removed footer sentence remains: {path.relative_to(output)}")
        if "79用語" in new:
            errors.append(f"Visible glossary count remains: {path.relative_to(output)}")

    glossary = output / "glossary.html"
    if glossary.is_file():
        built = glossary.read_text(encoding="utf-8")
        if built.find('class="glossary-tools"') > built.find('class="glossary-hero"'):
            errors.append("Glossary search is not displayed before the hero")
    else:
        errors.append("Missing glossary.html")

    error_page = output / "404.html"
    if not error_page.is_file():
        errors.append("Custom 404 page was not generated")
    else:
        built_404 = error_page.read_text(encoding="utf-8")
        for marker in ("ページが見つかりません", "company.html", 'id="main-content"'):
            if marker not in built_404:
                errors.append(f"Custom 404 marker missing: {marker}")

    return updated, errors
