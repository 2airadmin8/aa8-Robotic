#!/usr/bin/env python3
"""Inject browser identity and social metadata into the built HTML artifact.

The runtime SEO script remains as a safety net, but crawlers and link preview bots
should receive favicon, manifest, theme color, Open Graph and Twitter metadata in
the initial HTML response.
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"
PUBLIC_BASE = "https://2airadmin8.github.io/aa8-Robotic/"
SOCIAL_IMAGE = f"{PUBLIC_BASE}assets/img/robot-category-lineup.svg"

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


def build_static_meta(text: str, relative: Path) -> str:
    title = extract(TITLE_PATTERN, text) or "AirAdmin8 Robotics"
    description = extract(DESCRIPTION_PATTERN, text)
    canonical = extract(CANONICAL_PATTERN, text)
    if not canonical:
        canonical = PUBLIC_BASE if relative.as_posix() == "index.html" else f"{PUBLIC_BASE}{relative.as_posix()}"

    og_type = "product" if relative.parts and relative.parts[0] == "products" else "website"
    prefix = "../" * len(relative.parent.parts)

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

    # Remove only the tags managed by this script to keep reruns idempotent.
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

    errors: list[str] = []
    processed = 0
    for path in sorted(OUTPUT.rglob("*.html")):
        relative = path.relative_to(OUTPUT)
        try:
            source = path.read_text(encoding="utf-8")
            result = build_static_meta(source, relative)
            path.write_text(result, encoding="utf-8")
            processed += 1
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            errors.append(str(exc))

    if errors:
        for error in errors:
            print(f"META ERROR: {error}")
        return 1

    print(f"Static browser and social metadata injected into {processed} HTML page(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
