#!/usr/bin/env python3
"""Attach required shared assets to the generated site.

This script never edits CSS rules, header/footer markup, canonical URLs, or content.
It only normalizes references to approved CSS, JavaScript, and favicon assets.
"""
from __future__ import annotations

import re
from pathlib import Path

OUTPUT = Path("_site")
ASSETS = {
    "main_css": "assets/css/main-site-experience.css",
    "footer_css": "assets/css/footer-mobile-cleanup.css",
    "shared_css": "assets/css/shared-layout.css",
    "js": "assets/js/main-site-experience.js",
    "favicon": "assets/img/airadmin8-192x192.svg",
}


def replace_or_insert(markup: str, pattern: re.Pattern[str], replacement: str, closing_tag: str) -> str:
    match = pattern.search(markup)
    if match:
        return markup[: match.start()] + replacement + markup[match.end() :]
    if closing_tag not in markup:
        raise ValueError(f"Missing {closing_tag}")
    return markup.replace(closing_tag, f"  {replacement}\n{closing_tag}", 1)


def main() -> int:
    if not OUTPUT.is_dir():
        print("ERROR: _site does not exist")
        return 1

    required = [*ASSETS.values(), "assets/img/logo-airadmin8-robotics-pc.svg", "assets/img/logo-airadmin8-robotics-sp.svg"]
    missing = [item for item in required if not (OUTPUT / item).is_file()]
    if missing:
        for item in missing:
            print(f"ERROR: missing asset: {item}")
        return 1

    html_files = sorted(path for path in OUTPUT.rglob("*.html") if "includes" not in path.relative_to(OUTPUT).parts)
    if not html_files:
        print("ERROR: no publishable HTML files")
        return 1

    changed = 0
    for path in html_files:
        relative = path.relative_to(OUTPUT)
        prefix = "../" * (len(relative.parents) - 1)
        original = path.read_text(encoding="utf-8")
        markup = original

        for asset in (ASSETS["main_css"], ASSETS["footer_css"], ASSETS["shared_css"]):
            name = Path(asset).name
            pattern = re.compile(
                rf'<link\b(?=[^>]*rel=["\'][^"\']*stylesheet[^"\']*["\'])(?=[^>]*href=["\'][^"\']*{re.escape(name)}(?:\?[^"\']*)?["\'])[^>]*>',
                re.I,
            )
            markup = replace_or_insert(markup, pattern, f'<link rel="stylesheet" href="{prefix}{asset}">', "</head>")

        icon_pattern = re.compile(
            r'\s*<link\b(?=[^>]*rel=["\'][^"\']*(?:icon|shortcut icon)[^"\']*["\'])[^>]*>',
            re.I,
        )
        markup = icon_pattern.sub("", markup)
        icon = prefix + ASSETS["favicon"]
        icon_block = (
            f'<link rel="icon" type="image/svg+xml" sizes="any" href="{icon}" data-aa8-brand-icon="true">\n'
            f'  <link rel="shortcut icon" href="{icon}" data-aa8-brand-icon="true">'
        )
        markup = replace_or_insert(markup, re.compile(r'(?!x)x'), icon_block, "</head>")

        js_pattern = re.compile(
            r'<script\b(?=[^>]*src=["\'][^"\']*main-site-experience\.js(?:\?[^"\']*)?["\'])[^>]*></script>',
            re.I,
        )
        markup = replace_or_insert(markup, js_pattern, f'<script src="{prefix}{ASSETS["js"]}" defer></script>', "</body>")

        if markup != original:
            path.write_text(markup, encoding="utf-8")
            changed += 1

    print(f"Applied approved site assets to {len(html_files)} page(s); changed {changed}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
