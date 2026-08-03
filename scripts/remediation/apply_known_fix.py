#!/usr/bin/env python3
"""Apply small deterministic fixes only. Never edits WordPress or external systems."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HEADER = ROOT / "includes/site-header.html"
BASE = "https://robotics.air-admin8.co.jp"
EXCLUDED = {".git", "_site", "node_modules", "vendor"}


def html_files():
    for path in ROOT.rglob("*.html"):
        if not any(part in EXCLUDED for part in path.parts):
            yield path


def sync_header() -> list[Path]:
    header = HEADER.read_text(encoding="utf-8").strip()
    pattern = re.compile(r'<header\b(?=[^>]*class=["\'][^"\']*site-header)[^>]*>.*?</header>', re.I | re.S)
    changed: list[Path] = []
    for path in html_files():
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
    for path in html_files():
        text = path.read_text(encoding="utf-8")
        new = text.replace(f"{BASE}/aa8-Robotic/", f"{BASE}/")
        if new != text:
            path.write_text(new, encoding="utf-8", newline="\n")
            changed.append(path)
    return changed


def repair_sitemap() -> list[Path]:
    path = ROOT / "sitemap.xml"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    new = text.replace(f"{BASE}/aa8-Robotic/", f"{BASE}/")
    if new == text:
        return []
    path.write_text(new, encoding="utf-8", newline="\n")
    return [path]


def repair_robots() -> list[Path]:
    path = ROOT / "robots.txt"
    expected = f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n"
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if current == expected:
        return []
    path.write_text(expected, encoding="utf-8", newline="\n")
    return [path]


def repair_asset_404() -> list[Path]:
    """Repair only registered header-logo asset references; never invent assets."""
    required = [
        ROOT / "assets/img/logo-airadmin8-robotics-pc.svg",
        ROOT / "assets/img/logo-airadmin8-robotics-sp.svg",
        ROOT / "assets/css/shared-layout.css",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise SystemExit("UNSAFE_MISSING_ASSET:" + ",".join(missing))
    changed = sync_header()
    index = ROOT / "index.html"
    if index.exists():
        text = index.read_text(encoding="utf-8")
        replacements = {
            r'/assets/img/logo-airadmin8-robotics-pc\.svg(?:\?v=[^"\']*)?': '/assets/img/logo-airadmin8-robotics-pc.svg?v=auto-remediation-v2',
            r'/assets/img/logo-airadmin8-robotics-sp\.svg(?:\?v=[^"\']*)?': '/assets/img/logo-airadmin8-robotics-sp.svg?v=auto-remediation-v2',
        }
        new = text
        for pattern, value in replacements.items():
            new = re.sub(pattern, value, new)
        if new != text:
            index.write_text(new, encoding="utf-8", newline="\n")
            if index not in changed:
                changed.append(index)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("category")
    args = parser.parse_args()
    handlers = {
        "HEADER_SYNC": sync_header,
        "CANONICAL": repair_canonical,
        "SITEMAP": repair_sitemap,
        "ROBOTS": repair_robots,
        "ASSET_404": repair_asset_404,
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
