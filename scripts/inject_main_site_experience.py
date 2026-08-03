#!/usr/bin/env python3
"""Build成果物へ共通UI資産とfaviconのみを適用する。

Header/Footer/Logoはincludes + shared-layout.css、canonicalはbuild_site.py、
SEO/SNS metadataはinject_static_meta.pyが唯一の管理元。
"""
from __future__ import annotations

import re
from pathlib import Path

ASSETS = {
    "main_css": "assets/css/main-site-experience.css",
    "footer_css": "assets/css/footer-mobile-cleanup.css",
    "shared_css": "assets/css/shared-layout.css",
    "js": "assets/js/main-site-experience.js",
    "favicon": "assets/img/airadmin8-192x192.svg",
}


def remove_existing_icons(markup: str) -> str:
    return re.sub(
        r'\s*<link\b[^>]*\brel=["\'][^"\']*(?:icon|shortcut icon)[^"\']*["\'][^>]*>',
        "",
        markup,
        flags=re.I,
    )


def upsert_head_link(markup: str, asset_name: str, link: str) -> str:
    pattern = re.compile(
        rf'<link\b(?=[^>]*\brel=["\'][^"\']*\bstylesheet\b[^"\']*["\'])(?=[^>]*\bhref=["\'][^"\']*{re.escape(asset_name)}(?:\?[^"\']*)?["\'])[^>]*>',
        re.I,
    )
    match = pattern.search(markup)
    if match:
        return markup[:match.start()] + link + markup[match.end():]
    return markup.replace("</head>", f"  {link}\n</head>", 1)


def remove_legacy_logo_links(markup: str) -> str:
    return re.sub(
        r'\s*<link\b(?=[^>]*\brel=["\'][^"\']*\bstylesheet\b[^"\']*["\'])(?=[^>]*\bhref=["\'][^"\']*main-logo\.css(?:\?[^"\']*)?["\'])[^>]*>',
        "",
        markup,
        flags=re.I,
    )


def inject(output: Path) -> tuple[int, list[str]]:
    errors: list[str] = []
    updated = 0
    required = [
        ASSETS["main_css"],
        ASSETS["footer_css"],
        ASSETS["shared_css"],
        ASSETS["js"],
        "assets/img/logo-airadmin8-robotics-pc.svg",
        "assets/img/logo-airadmin8-robotics-sp.svg",
        ASSETS["favicon"],
    ]
    for item in required:
        if not (output / item).is_file():
            errors.append(f"Missing required asset: {item}")
    if errors:
        return 0, errors

    html_files = [p for p in output.rglob("*.html") if "includes" not in p.relative_to(output).parts]
    for path in html_files:
        relative = path.relative_to(output)
        prefix = "../" * (len(relative.parents) - 1)
        original = path.read_text(encoding="utf-8")
        if "</head>" not in original or "</body>" not in original:
            errors.append(f"Invalid publishable HTML: {relative.as_posix()}")
            continue

        markup = remove_existing_icons(original)
        markup = remove_legacy_logo_links(markup)

        css_items = [
            ("main-site-experience.css", ASSETS["main_css"]),
            ("footer-mobile-cleanup.css", ASSETS["footer_css"]),
            ("shared-layout.css", ASSETS["shared_css"]),
        ]
        expected: list[str] = []
        for asset_name, asset in css_items:
            href = prefix + asset
            expected.append(href)
            markup = upsert_head_link(markup, asset_name, f'<link rel="stylesheet" href="{href}">')

        favicon = prefix + ASSETS["favicon"]
        icon_block = (
            f'<link rel="icon" type="image/svg+xml" sizes="any" href="{favicon}" data-aa8-brand-icon="true">\n'
            f'<link rel="shortcut icon" href="{favicon}" data-aa8-brand-icon="true">'
        )
        markup = markup.replace("</head>", f"  {icon_block}\n</head>", 1)

        js_src = prefix + ASSETS["js"]
        js_tag = f'<script src="{js_src}" defer></script>'
        js_pattern = re.compile(
            r'<script\b(?=[^>]*\bsrc=["\'][^"\']*main-site-experience\.js(?:\?[^"\']*)?["\'])[^>]*></script>',
            re.I,
        )
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
            errors.append(f"UI asset verification failed: {relative.as_posix()}")
        if "main-logo.css" in markup:
            errors.append(f"Legacy logo stylesheet remains: {relative.as_posix()}")

    if not html_files:
        errors.append("No publishable HTML found")
    return updated, errors


def main() -> None:
    output = Path("_site")
    if not output.is_dir():
        raise SystemExit("Missing build output directory: _site")
    updated, errors = inject(output)
    print(f"Required UI assets applied to {updated} HTML page(s).")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
