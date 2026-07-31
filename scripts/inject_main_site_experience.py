#!/usr/bin/env python3
"""Inject the shared AirAdmin8 main-site-inspired UI CSS, JS, menu, footer links, and logo."""

from __future__ import annotations

import re
from pathlib import Path

from footer_cleanup_rules import NOTICE_TEXT, cleanup_footer

CSS_ASSET = "assets/css/main-site-experience.css?v=20260731-4"
FOOTER_CSS_ASSET = "assets/css/footer-mobile-cleanup.css?v=20260731-1"
LOGO_CSS_ASSET = "assets/css/main-logo.css?v=20260731-2"
JS_ASSET = "assets/js/main-site-experience.js?v=20260731-6"


def add_glossary_navigation(markup: str, prefix: str) -> str:
    glossary_href = f"{prefix}glossary.html"

    header_match = re.search(r"(<header\b[^>]*>.*?<nav\b[^>]*>)(.*?)(</nav>)", markup, flags=re.IGNORECASE | re.DOTALL)
    if header_match and "glossary.html" not in header_match.group(2):
        link = f'<a href="{glossary_href}">用語集</a>'
        replacement = header_match.group(1) + header_match.group(2) + link + header_match.group(3)
        markup = markup[:header_match.start()] + replacement + markup[header_match.end():]

    footer_match = re.search(r"(<footer\b[^>]*>)(.*?)(</footer>)", markup, flags=re.IGNORECASE | re.DOTALL)
    if footer_match and "aa8-footer-learning" not in footer_match.group(2):
        learning = (
            '<section class="aa8-footer-learning" aria-labelledby="aa8-footer-learning-title">'
            '<h2 class="aa8-footer-learning__title" id="aa8-footer-learning-title">学ぶ・調べる</h2>'
            '<nav class="aa8-footer-learning__links" aria-label="学ぶ・調べる">'
            f'<a href="{glossary_href}">ロボット・フィジカルAI用語集</a>'
            f'<a href="{prefix}resources.html">資料・SDK</a>'
            f'<a href="{prefix}faq.html">よくある質問</a>'
            '</nav>'
            '</section>'
        )
        replacement = footer_match.group(1) + footer_match.group(2) + learning + footer_match.group(3)
        markup = markup[:footer_match.start()] + replacement + markup[footer_match.end():]

    return cleanup_footer(markup)


def inject_main_site_experience(output: Path) -> tuple[int, list[str]]:
    errors: list[str] = []
    updated = 0

    required = [
        output / "assets" / "css" / "main-site-experience.css",
        output / "assets" / "css" / "footer-mobile-cleanup.css",
        output / "assets" / "css" / "main-logo.css",
        output / "assets" / "img" / "airadmin8-official-logo.png",
        output / "assets" / "js" / "main-site-experience.js",
    ]
    for path in required:
        if not path.is_file():
            errors.append(f"Missing shared UI asset: {path.relative_to(output).as_posix()}")
    if errors:
        return 0, errors

    css_pattern = re.compile(r'<link\s+rel=["\']stylesheet["\']\s+href=["\'][^"\']*main-site-experience\.css(?:\?v=[^"\']*)?["\']\s*/?>', flags=re.IGNORECASE)
    footer_css_pattern = re.compile(r'<link\s+rel=["\']stylesheet["\']\s+href=["\'][^"\']*footer-mobile-cleanup\.css(?:\?v=[^"\']*)?["\']\s*/?>', flags=re.IGNORECASE)
    logo_css_pattern = re.compile(r'<link\s+rel=["\']stylesheet["\']\s+href=["\'][^"\']*main-logo\.css(?:\?v=[^"\']*)?["\']\s*/?>', flags=re.IGNORECASE)
    js_pattern = re.compile(r'<script\s+src=["\'][^"\']*main-site-experience\.js(?:\?v=[^"\']*)?["\']\s*(?:defer)?\s*></script>', flags=re.IGNORECASE)

    for html_path in output.rglob("*.html"):
        relative = html_path.relative_to(output)
        depth = len(relative.parents) - 1
        prefix = "../" * depth
        css_href = prefix + CSS_ASSET
        footer_css_href = prefix + FOOTER_CSS_ASSET
        logo_css_href = prefix + LOGO_CSS_ASSET
        js_src = prefix + JS_ASSET
        css_link = f'<link rel="stylesheet" href="{css_href}">'
        footer_css_link = f'<link rel="stylesheet" href="{footer_css_href}">'
        logo_css_link = f'<link rel="stylesheet" href="{logo_css_href}">'
        js_tag = f'<script src="{js_src}" defer></script>'

        html = html_path.read_text(encoding="utf-8")
        new_html = add_glossary_navigation(html, prefix)

        for pattern, link in ((css_pattern, css_link), (footer_css_pattern, footer_css_link), (logo_css_pattern, logo_css_link)):
            match = pattern.search(new_html)
            if match:
                new_html = new_html[:match.start()] + link + new_html[match.end():]
            elif "</head>" in new_html:
                new_html = new_html.replace("</head>", f"  {link}\n</head>", 1)
            else:
                errors.append(f"Missing </head> in {relative.as_posix()}")
                break
        else:
            js_match = js_pattern.search(new_html)
            if js_match:
                new_html = new_html[:js_match.start()] + js_tag + new_html[js_match.end():]
            elif "</body>" in new_html:
                new_html = new_html.replace("</body>", f"  {js_tag}\n</body>", 1)
            else:
                errors.append(f"Missing </body> in {relative.as_posix()}")
                continue

            if new_html != html:
                html_path.write_text(new_html, encoding="utf-8")
                updated += 1

            if css_href not in new_html or footer_css_href not in new_html or logo_css_href not in new_html or js_src not in new_html:
                errors.append(f"Shared UI injection failed: {relative.as_posix()}")
            if relative.name != "404.html" and "glossary.html" not in new_html:
                errors.append(f"Glossary navigation missing: {relative.as_posix()}")
            if relative.name != "404.html" and "aa8-footer-learning__links" not in new_html:
                errors.append(f"Footer learning links missing: {relative.as_posix()}")
            if NOTICE_TEXT in new_html:
                errors.append(f"Footer notice was not removed: {relative.as_posix()}")

    if updated == 0:
        errors.append("Shared UI assets were not injected into any HTML page")

    return updated, errors
