#!/usr/bin/env python3
"""Apply final sitewide brand wording, contact, breadcrumb, and glossary layout rules."""

from __future__ import annotations

import re
from pathlib import Path

REMOVE_SENTENCE = "AIロボット・フィジカルAIの選定、比較、導入、PoCを支援します。"
CONTACT_LABEL = "ロボティクス窓口"
CONTACT_EMAIL = "airobot@robotics.air-admin8.co.jp"


def remove_company_breadcrumb(markup: str) -> str:
    """Remove only the visible ホーム / 会社情報 breadcrumb text without deleting containers."""
    markup = markup.replace("ホーム / 会社情報", "")
    markup = markup.replace("ホーム／会社情報", "")
    markup = re.sub(
        r'<a\b[^>]*>\s*ホーム\s*</a>\s*[/／›&gt;]+\s*(?:<a\b[^>]*>)?\s*会社情報\s*(?:</a>)?',
        "",
        markup,
        flags=re.IGNORECASE,
    )
    return markup


def add_robotics_contact(markup: str) -> str:
    """Add one clear Robotics contact block to the footer."""
    if CONTACT_EMAIL in markup:
        return markup
    footer = re.search(r'(<footer\b[^>]*>)(.*?)(</footer>)', markup, flags=re.IGNORECASE | re.DOTALL)
    if not footer:
        return markup
    contact = (
        '<div class="aa8-footer-contact">'
        f'<strong>{CONTACT_LABEL}</strong>'
        f'<a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>'
        '</div>'
    )
    replacement = footer.group(1) + footer.group(2) + contact + footer.group(3)
    return markup[:footer.start()] + replacement + markup[footer.end():]


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
        new = remove_company_breadcrumb(new)
        new = add_robotics_contact(new)

        if path.name == "glossary.html":
            hero = re.search(r'<section class="glossary-hero">.*?</section>', new, flags=re.DOTALL)
            tools = re.search(r'<section class="glossary-tools">.*?</section>', new, flags=re.DOTALL)
            if hero and tools and hero.start() < tools.start():
                new = new[:hero.start()] + tools.group(0) + hero.group(0) + new[tools.end():]

        if new != text:
            path.write_text(new, encoding="utf-8")
            updated += 1

        if "AIRADMIN8" in new:
            errors.append(f"Uppercase AIRADMIN8 remains: {path.relative_to(output)}")
        if REMOVE_SENTENCE in new:
            errors.append(f"Removed footer sentence remains: {path.relative_to(output)}")
        if "79用語" in new:
            errors.append(f"Visible glossary count remains: {path.relative_to(output)}")
        if CONTACT_EMAIL not in new:
            errors.append(f"Robotics contact missing: {path.relative_to(output)}")
        if "ホーム / 会社情報" in new or "ホーム／会社情報" in new:
            errors.append(f"Company breadcrumb remains: {path.relative_to(output)}")

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
        for marker in ("ページが見つかりません", "about.html", 'id="main-content"', CONTACT_EMAIL):
            if marker not in built_404:
                errors.append(f"Custom 404 marker missing: {marker}")

    return updated, errors
