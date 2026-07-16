#!/usr/bin/env python3
"""Inject shared accessibility helpers into the built HTML artifact."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"
BUILD_VERSION = "20260716-13"

SKIP_LINK = '<a class="skip-link" href="#main-content">本文へ移動</a>'
MAIN_PATTERN = re.compile(r"<main\b([^>]*)>", re.IGNORECASE)
ACCESSIBILITY_LINK_PATTERN = re.compile(
    r'\s*<link\s+rel=["\']stylesheet["\']\s+href=["\'][^"\']*assets/css/accessibility\.css(?:\?v=[^"\']+)?["\']\s*/?>',
    re.IGNORECASE,
)


def process_html(text: str, relative: Path) -> str:
    prefix = "../" * len(relative.parent.parts)
    stylesheet = (
        f'<link rel="stylesheet" href="{prefix}assets/css/accessibility.css?v={BUILD_VERSION}">'
    )

    text = ACCESSIBILITY_LINK_PATTERN.sub("", text)
    if "</head>" not in text:
        raise ValueError(f"Missing </head>: {relative}")
    text = text.replace("</head>", f"  {stylesheet}\n</head>", 1)

    text = text.replace(SKIP_LINK, "")
    body_match = re.search(r"<body\b[^>]*>", text, flags=re.IGNORECASE)
    if not body_match:
        raise ValueError(f"Missing <body>: {relative}")
    insert_at = body_match.end()
    text = text[:insert_at] + "\n" + SKIP_LINK + text[insert_at:]

    main_match = MAIN_PATTERN.search(text)
    if not main_match:
        raise ValueError(f"Missing <main>: {relative}")

    attrs = main_match.group(1)
    if re.search(r'\bid=["\']main-content["\']', attrs, flags=re.IGNORECASE):
        return text

    if re.search(r"\bid=", attrs, flags=re.IGNORECASE):
        attrs = re.sub(r'\bid=["\'][^"\']*["\']', 'id="main-content"', attrs, count=1, flags=re.IGNORECASE)
    else:
        attrs = f'{attrs} id="main-content"'

    return text[:main_match.start()] + f"<main{attrs}>" + text[main_match.end():]


def main() -> int:
    if not OUTPUT.is_dir():
        print("A11Y ERROR: _site directory does not exist")
        return 1

    errors: list[str] = []
    processed = 0
    for path in sorted(OUTPUT.rglob("*.html")):
        relative = path.relative_to(OUTPUT)
        try:
            source = path.read_text(encoding="utf-8")
            path.write_text(process_html(source, relative), encoding="utf-8")
            processed += 1
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            errors.append(str(exc))

    if errors:
        for error in errors:
            print(f"A11Y ERROR: {error}")
        return 1

    print(f"Accessibility helpers injected into {processed} HTML page(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
