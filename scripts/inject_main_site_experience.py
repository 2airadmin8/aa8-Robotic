#!/usr/bin/env python3
"""Build成果物へ共通ヘッダー・フッター・UI資産・faviconを必須適用する。"""
from __future__ import annotations

import re
from pathlib import Path

from footer_cleanup_rules import NOTICE_TEXT, cleanup_footer

ROOT = Path(__file__).resolve().parents[1]
HEADER_SOURCE = ROOT / "includes/site-header.html"
FOOTER_SOURCE = ROOT / "includes/site-footer.html"

ASSETS = {
    "main_css": "assets/css/main-site-experience.css?v=20260801-4",
    "footer_css": "assets/css/footer-mobile-cleanup.css?v=20260801-4",
    "logo_css": "assets/css/main-logo.css?v=20260731-2",
    "shared_css": "assets/css/shared-layout.css?v=20260803-buildfix",
    "js": "assets/js/main-site-experience.js?v=20260801-15",
    "favicon": "assets/img/airadmin8-192x192.svg?v=20260803-brand-v2",
}


def shared_markup(path: Path, prefix: str) -> str:
    markup = path.read_text(encoding="utf-8").strip()
    # 共通部品内のルート相対URLを、出力ページ階層に合わせて変換する。
    return re.sub(r'(?P<attr>(?:href|src|srcset)=["\'])/', rf'\g<attr>{prefix}', markup)


def replace_block(markup: str, tag: str, class_name: str, replacement: str) -> str:
    pattern = re.compile(
        rf'<{tag}\b(?=[^>]*class=["\'][^"\']*\b{re.escape(class_name)}\b[^"\']*["\'])[^>]*>.*?</{tag}>',
        re.I | re.S,
    )
    if not pattern.search(markup):
        raise ValueError(f"{tag}.{class_name} not found")
    return pattern.sub(replacement, markup, count=1)


def add_footer_links(markup: str, prefix: str) -> str:
    match = re.search(r"(<footer\b[^>]*>)(.*?)(</footer>)", markup, re.I | re.S)
    if match and "aa8-footer-learning" not in match.group(2):
        block = (
            '<section class="aa8-footer-learning" aria-labelledby="aa8-footer-learning-title">'
            '<h2 class="aa8-footer-learning__title" id="aa8-footer-learning-title">学ぶ・調べる</h2>'
            '<nav class="aa8-footer-learning__links" aria-label="学ぶ・調べる">'
            f'<a href="{prefix}glossary.html">ロボット・フィジカルAI用語集</a>'
            f'<a href="{prefix}resources.html">資料・SDK</a>'
            f'<a href="{prefix}faq.html">よくある質問</a>'
            '</nav></section>'
        )
        replacement = match.group(1) + match.group(2) + block + match.group(3)
        markup = markup[:match.start()] + replacement + markup[match.end():]
    return cleanup_footer(markup)


def remove_existing_icons(markup: str) -> str:
    return re.sub(
        r'\s*<link\b[^>]*\brel=["\'][^"\']*(?:icon|shortcut icon)[^"\']*["\'][^>]*>',
        '', markup, flags=re.I,
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
    for source in (HEADER_SOURCE, FOOTER_SOURCE):
        if not source.is_file():
            errors.append(f"Missing shared layout source: {source.relative_to(ROOT)}")
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

        try:
            markup = replace_block(original, "header", "site-header", shared_markup(HEADER_SOURCE, prefix))
            markup = replace_block(markup, "footer", "footer", shared_markup(FOOTER_SOURCE, prefix))
        except ValueError as exc:
            errors.append(f"Shared layout replacement failed: {relative.as_posix()}: {exc}")
            continue

        markup = add_footer_links(markup, prefix)
        markup = remove_existing_icons(markup)

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

        checks = expected + [
            js_src, favicon, "brand-logo-pc", "brand-logo-sp",
            'data-shared-layout="header"', 'data-shared-layout="footer"',
            'data-aa8-brand-icon="true"',
        ]
        if any(value not in markup for value in checks):
            errors.append(f"Shared branding verification failed: {relative.as_posix()}")
        if relative.name != "404.html" and "aa8-footer-learning__links" not in markup:
            errors.append(f"Footer links missing: {relative.as_posix()}")
        if NOTICE_TEXT in markup:
            errors.append(f"Deprecated footer notice remains: {relative.as_posix()}")

    if not html_files:
        errors.append("No publishable HTML found")
    return updated, errors


def main() -> None:
    output = Path("_site")
    if not output.is_dir():
        raise SystemExit("Missing build output directory: _site")
    updated, errors = inject(output)
    print(f"Required shared layout applied to {updated} HTML page(s).")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
