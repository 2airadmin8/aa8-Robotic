#!/usr/bin/env python3
"""Build成果物へUI資産とfaviconのみを必須適用する。

Header/Footerはbuild_site.pyがincludesから生成するため、この工程では変更しない。
"""
from __future__ import annotations

import re
from pathlib import Path

ASSETS = {
    "main_css": "assets/css/main-site-experience.css?v=20260801-4",
    "footer_css": "assets/css/footer-mobile-cleanup.css?v=20260801-4",
    "logo_css": "assets/css/main-logo.css?v=20260731-2",
    "shared_css": "assets/css/shared-layout.css?v=20260803-buildfix",
    "js": "assets/js/main-site-experience.js?v=20260801-15",
    "favicon": "assets/img/airadmin8-192x192.svg?v=20260803-brand-v2",
}


def remove_existing_icons(markup: str) -> str:
    return re.sub(
        r'\s*<link\b[^>]*\brel=["\'][^"\']*(?:icon|shortcut icon)[^"\']*["\'][^>]*>',
        "",
        markup,
        flags=re.I,
    )


def upsert_head_link(markup: str, pattern: str, link: str) -> str:
    compiled = re.compile(pattern, re.I)
    match = compiled.search(markup)
    if match:
        return markup[:match.start()] + link + markup[match.end():]
    return markup.replace("</head>", f"  {link}\n</head>", 1)


def inject(output: Path) -> tuple[int, list[str]]:
    errors: list[str] = []
    updated = 0
    required = [
        "assets/css/main-site-experience.css",
        "assets/css/footer-mobile-cleanup.css",
        "assets/css/main-logo.css",
        "assets/css/shared-layout.css",
        "assets/js/main-site-experience.js",
        "assets/img/logo-airadmin8-robotics-pc.svg",
        "assets/img/logo-airadmin8-robotics-sp.svg",
        "assets/img/airadmin8-192x192.svg",
    ]
    for item in required:
        if not (output / item).is_file():
            errors.append(f"Missing required asset: {item}")
    if errors:
        return 0, errors

    html_files = [p for p in output.rglob("*.html") if "includes" not in p.relative_to(output).parts]
    for path in html_files:
        relative = path.relative_to(output)
        relative_posix = relative.as_posix()
        prefix = "../" * (len(relative.parents) - 1)
        original = path.read_text(encoding="utf-8")
        if "</head>" not in original or "</body>" not in original:
            errors.append(f"Invalid publishable HTML: {relative_posix}")
            continue

        markup = remove_existing_icons(original)
        css_items = [
            (r'<link\s+rel=["\']stylesheet["\']\s+href=["\'][^"\']*main-site-experience\.css[^"\']*["\']\s*/?>', ASSETS["main_css"]),
            (r'<link\s+rel=["\']stylesheet["\']\s+href=["\'][^"\']*footer-mobile-cleanup\.css[^"\']*["\']\s*/?>', ASSETS["footer_css"]),
            (r'<link\s+rel=["\']stylesheet["\']\s+href=["\'][^"\']*main-logo\.css[^"\']*["\']\s*/?>', ASSETS["logo_css"]),
            (r'<link\s+rel=["\']stylesheet["\']\s+href=["\'][^"\']*shared-layout\.css[^"\']*["\']\s*/?>', ASSETS["shared_css"]),
        ]
        expected: list[str] = []
        for pattern, asset in css_items:
            href = prefix + asset
            expected.append(href)
            markup = upsert_head_link(markup, pattern, f'<link rel="stylesheet" href="{href}">')

        favicon = prefix + ASSETS["favicon"]
        icon_block = (
            f'<link rel="icon" type="image/svg+xml" sizes="any" href="{favicon}" data-aa8-brand-icon="true">\n'
            f'<link rel="shortcut icon" href="{favicon}" data-aa8-brand-icon="true">'
        )
        markup = markup.replace("</head>", f"  {icon_block}\n</head>", 1)

        js_src = prefix + ASSETS["js"]
        js_tag = f'<script src="{js_src}" defer></script>'
        js_pattern = re.compile(r'<script\s+src=["\'][^"\']*main-site-experience\.js[^"\']*["\']\s*(?:defer)?\s*></script>', re.I)
        match = js_pattern.search(markup)
        if match:
            markup = markup[:match.start()] + js_tag + markup[match.end():]
        else:
            markup = markup.replace("</body>", f"  {js_tag}\n</body>", 1)

        if markup != original:
            path.write_text(markup, encoding="utf-8")
            updated += 1

        checks = expected + [js_src, favicon, 'data-aa8-brand-icon="true"']
        if any(value not in markup for value in checks):
            errors.append(f"UI asset verification failed: {relative_posix}")

        # glossaryページは別テンプレート系のため、共通Header/Footerの厳格検証対象外。
        # UI資産・faviconの検証は継続する。
        is_glossary = relative_posix == "glossary.html" or relative_posix.startswith("glossary/")
        if not is_glossary:
            if markup.count('data-shared-layout="header"') != 1:
                errors.append(f"Shared header missing or duplicated: {relative_posix}")
            if markup.count('data-shared-layout="footer"') != 1:
                errors.append(f"Shared footer missing or duplicated: {relative_posix}")

    if not html_files:
        errors.append("No publishable HTML found")
    return updated, errors


def main() -> None:
    output = Path("_site")
    if not output.is_dir():
        raise SystemExit("Missing build output directory: _site")
    updated, errors = inject(output)
    print(f"Required UI assets applied to {updated} HTML page(s); shared layout untouched.")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
