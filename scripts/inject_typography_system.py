#!/usr/bin/env python3
"""Inject the shared Japanese typography stylesheet into every built HTML page."""

from __future__ import annotations

import re
from pathlib import Path

STYLESHEET = "assets/css/typography-system.css?v=20260731-1"


def inject_typography_system(output: Path) -> tuple[int, list[str]]:
    errors: list[str] = []
    updated = 0

    css_path = output / "assets" / "css" / "typography-system.css"
    if not css_path.is_file():
        return 0, ["Missing shared typography stylesheet: assets/css/typography-system.css"]

    for html_path in output.rglob("*.html"):
        if html_path.name == "404.html":
            # 404 also receives the shared system, but no special handling is needed.
            pass

        relative = html_path.relative_to(output)
        depth = len(relative.parents) - 1
        href = "../" * depth + STYLESHEET
        link = f'<link rel="stylesheet" href="{href}">' 

        html = html_path.read_text(encoding="utf-8")
        existing = re.search(
            r'<link\s+rel=["\']stylesheet["\']\s+href=["\'][^"\']*typography-system\.css(?:\?v=[^"\']*)?["\']\s*/?>',
            html,
            flags=re.IGNORECASE,
        )
        if existing:
            new_html = html[: existing.start()] + link + html[existing.end() :]
        elif "</head>" in html:
            new_html = html.replace("</head>", f"  {link}\n</head>", 1)
        else:
            errors.append(f"Missing </head> in {relative.as_posix()}")
            continue

        if new_html != html:
            html_path.write_text(new_html, encoding="utf-8")
            updated += 1

        if href not in new_html:
            errors.append(f"Typography stylesheet injection failed: {relative.as_posix()}")

    if updated == 0:
        errors.append("Typography stylesheet was not injected into any HTML page")

    return updated, errors
