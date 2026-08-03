#!/usr/bin/env python3
"""Apply small, deterministic fixes only. Never edits WordPress or external systems."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HEADER = ROOT / "includes/site-header.html"


def sync_header() -> list[Path]:
    header = HEADER.read_text(encoding="utf-8").strip()
    changed: list[Path] = []
    pattern = re.compile(r'<header\b(?=[^>]*class=["\'][^"\']*site-header)[^>]*>.*?</header>', re.I | re.S)
    for path in ROOT.rglob("*.html"):
        if any(part in {".git", "_site", "node_modules", "vendor"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        if not pattern.search(text):
            continue
        new = pattern.sub(header, text, count=1)
        if new != text:
            path.write_text(new, encoding="utf-8", newline="\n")
            changed.append(path)
    return changed


def repair_canonical() -> list[Path]:
    changed: list[Path] = []
    for path in ROOT.rglob("*.html"):
        if any(part in {".git", "_site", "node_modules", "vendor"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        new = text.replace("https://robotics.air-admin8.co.jp/aa8-Robotic/", "https://robotics.air-admin8.co.jp/")
        if new != text:
            path.write_text(new, encoding="utf-8", newline="\n")
            changed.append(path)
    return changed


def repair_sitemap() -> list[Path]:
    path = ROOT / "sitemap.xml"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    new = text.replace("https://robotics.air-admin8.co.jp/aa8-Robotic/", "https://robotics.air-admin8.co.jp/")
    if new == text:
        return []
    path.write_text(new, encoding="utf-8", newline="\n")
    return [path]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("category")
    args = parser.parse_args()
    handlers = {
        "HEADER_SYNC": sync_header,
        "CANONICAL": repair_canonical,
        "SITEMAP": repair_sitemap,
        "ROBOTS": lambda: [],
    }
    handler = handlers.get(args.category)
    if handler is None:
        print(f"UNSUPPORTED:{args.category}")
        return 2
    changed = handler()
    for path in changed:
        print(path.relative_to(ROOT))
    print(f"CHANGED={len(changed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
