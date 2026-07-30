#!/usr/bin/env python3
"""Inject the shared AirAdmin8 main-site-inspired UI CSS and JS into every built HTML page."""

from __future__ import annotations

import re
from pathlib import Path

CSS_ASSET = "assets/css/main-site-experience.css?v=20260731-1"
JS_ASSET = "assets/js/main-site-experience.js?v=20260731-1"


def inject_main_site_experience(output: Path) -> tuple[int, list[str]]:
    errors: list[str] = []
    updated = 0

    required = [
        output / "assets" / "css" / "main-site-experience.css",
        output / "assets" / "js" / "main-site-experience.js",
    ]
    for path in required:
        if not path.is_file():
            errors.append(f"Missing shared UI asset: {path.relative_to(output).as_posix()}")
    if errors:
        return 0, errors

    css_pattern = re.compile(
        r'<link\s+rel=["\']stylesheet["\']\s+href=["\'][^"\']*main-site-experience\.css(?:\?v=[^"\']*)?["\']\s*/?>',
        flags=re.IGNORECASE,
    )
    js_pattern = re.compile(
        r'<script\s+src=["\'][^"\']*main-site-experience\.js(?:\?v=[^"\']*)?["\']\s*(?:defer)?\s*></script>',
        flags=re.IGNORECASE,
    )

    for html_path in output.rglob("*.html"):
        relative = html_path.relative_to(output)
        depth = len(relative.parents) - 1
        prefix = "../" * depth
        css_href = prefix + CSS_ASSET
        js_src = prefix + JS_ASSET
        css_link = f'<link rel="stylesheet" href="{css_href}">'
        js_tag = f'<script src="{js_src}" defer></script>'

        html = html_path.read_text(encoding="utf-8")
        new_html = html

        css_match = css_pattern.search(new_html)
        if css_match:
            new_html = new_html[:css_match.start()] + css_link + new_html[css_match.end():]
        elif "</head>" in new_html:
            new_html = new_html.replace("</head>", f"  {css_link}\n</head>", 1)
        else:
            errors.append(f"Missing </head> in {relative.as_posix()}")
            continue

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

        if css_href not in new_html or js_src not in new_html:
            errors.append(f"Shared UI injection failed: {relative.as_posix()}")

    if updated == 0:
        errors.append("Shared UI assets were not injected into any HTML page")

    return updated, errors
