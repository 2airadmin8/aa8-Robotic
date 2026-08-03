#!/usr/bin/env python3
"""Inject canonical, product SEO and social metadata into built HTML.

The public site is served through robotics.air-admin8.co.jp while GitHub Pages is
only the hosting origin. Crawlers should therefore always receive the production
host as the canonical URL. Product title/description overrides are kept in a
small data registry so the seven sales pages can be maintained consistently.
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"
PUBLIC_BASE = "https://robotics.air-admin8.co.jp/"
SOCIAL_IMAGE = f"{PUBLIC_BASE}assets/img/robot-category-lineup.svg"
PRODUCT_SEO_PATH = ROOT / "data" / "product-seo-v1.json"

TITLE_PATTERN = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
DESCRIPTION_PATTERN = re.compile(
    r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']\s*/?>',
    re.IGNORECASE | re.DOTALL,
)
CANONICAL_PATTERN = re.compile(
    r'<link\s+rel=["\']canonical["\']\s+href=["\'](.*?)["\']\s*/?>',
    re.IGNORECASE | re.DOTALL,
)


def extract(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return html.unescape(match.group(1).strip()) if match else ""


def meta_tag(attribute: str, key: str, value: str) -> str:
    return f'<meta {attribute}="{html.escape(key, quote=True)}" content="{html.escape(value, quote=True)}">'


def canonical_for(relative: Path) -> str:
    if relative.as_posix() == "index.html":
        return PUBLIC_BASE
    return f"{PUBLIC_BASE}{relative.as_posix()}"


def load_product_seo() -> dict[str, dict[str, str]]:
    try:
        payload = json.loads(PRODUCT_SEO_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read product SEO registry: {exc}") from exc
    pages = payload.get("pages", {})
    if not isinstance(pages, dict):
        raise ValueError("Product SEO registry pages must be an object")
    return pages


def replace_title(text: str, title: str) -> str:
    escaped = html.escape(title)
    if TITLE_PATTERN.search(text):
        return TITLE_PATTERN.sub(f"<title>{escaped}</title>", text, count=1)
    if "</head>" in text:
        return text.replace("</head>", f"  <title>{escaped}</title>\n</head>", 1)
    return text


def replace_description(text: str, description: str) -> str:
    tag = f'<meta name="description" content="{html.escape(description, quote=True)}">'
    if DESCRIPTION_PATTERN.search(text):
        return DESCRIPTION_PATTERN.sub(tag, text, count=1)
    if "</head>" in text:
        return text.replace("</head>", f"  {tag}\n</head>", 1)
    return text


def build_static_meta(text: str, relative: Path, product_seo: dict[str, dict[str, str]]) -> str:
    relative_name = relative.as_posix()
    override = product_seo.get(relative_name, {})

    title = str(override.get("title") or extract(TITLE_PATTERN, text) or "AirAdmin8 Robotics")
    description = str(override.get("description") or extract(DESCRIPTION_PATTERN, text))
    text = replace_title(text, title)
    text = replace_description(text, description)

    canonical = canonical_for(relative)
    og_type = "product" if relative.parts and relative.parts[0] == "products" else "website"
    prefix = "../" * len(relative.parent.parts)

    canonical_tag = f'<link rel="canonical" href="{html.escape(canonical, quote=True)}">'
    if CANONICAL_PATTERN.search(text):
        text = CANONICAL_PATTERN.sub(canonical_tag, text, count=1)
    elif "</head>" in text:
        text = text.replace("</head>", f"  {canonical_tag}\n</head>", 1)

    tags = [
        '<meta name="theme-color" content="#0b3143">',
        '<meta name="apple-mobile-web-app-capable" content="yes">',
        '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">',
        '<meta name="apple-mobile-web-app-title" content="A8 Robotics">',
        f'<link rel="icon" href="{prefix}assets/img/favicon.svg" type="image/svg+xml">',
        f'<link rel="mask-icon" href="{prefix}assets/img/favicon.svg" color="#009ad2">',
        f'<link rel="manifest" href="{prefix}site.webmanifest">',
        meta_tag("property", "og:type", og_type),
        meta_tag("property", "og:site_name", "AirAdmin8 Robotics"),
        meta_tag("property", "og:title", title),
        meta_tag("property", "og:description", description),
        meta_tag("property", "og:url", canonical),
        meta_tag("property", "og:image", SOCIAL_IMAGE),
        meta_tag("name", "twitter:card", "summary_large_image"),
        meta_tag("name", "twitter:title", title),
        meta_tag("name", "twitter:description", description),
        meta_tag("name", "twitter:image", SOCIAL_IMAGE),
    ]

    managed_patterns = [
        r'\s*<meta\s+name=["\'](?:theme-color|apple-mobile-web-app-capable|apple-mobile-web-app-status-bar-style|apple-mobile-web-app-title|twitter:card|twitter:title|twitter:description|twitter:image)["\'][^>]*>',
        r'\s*<meta\s+property=["\'](?:og:type|og:site_name|og:title|og:description|og:url|og:image)["\'][^>]*>',
        r'\s*<link\s+rel=["\'](?:icon|mask-icon|manifest)["\'][^>]*>',
    ]
    for pattern in managed_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    if "</head>" not in text:
        raise ValueError(f"Missing </head>: {relative}")
    return text.replace("</head>", "  " + "\n  ".join(tags) + "\n</head>", 1)


def main() -> int:
    if not OUTPUT.is_dir():
        print("META ERROR: _site directory does not exist")
        return 1

    try:
        product_seo = load_product_seo()
    except ValueError as exc:
        print(f"META ERROR: {exc}")
        return 1

    errors: list[str] = []
    processed = 0
    for path in sorted(OUTPUT.rglob("*.html")):
        relative = path.relative_to(OUTPUT)
        try:
            source = path.read_text(encoding="utf-8")
            result = build_static_meta(source, relative, product_seo)
            path.write_text(result, encoding="utf-8")
            processed += 1
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            errors.append(str(exc))

    if errors:
        for error in errors:
            print(f"META ERROR: {error}")
        return 1

    print(f"Static browser, product SEO and social metadata injected into {processed} HTML page(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
