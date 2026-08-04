#!/usr/bin/env python3
"""Read-only release gate for the generated _site artifact."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

OUTPUT = Path("_site")
BASE_URL = "https://robotics.air-admin8.co.jp/"

REQUIRED_FILES = [
    "index.html",
    "products.html",
    "products/unitree-g1-d.html",
    "contact.html",
    "assets/css/shared-layout.css",
    "assets/img/logo-airadmin8-robotics-pc.svg",
    "assets/img/logo-airadmin8-robotics-sp.svg",
    "assets/img/airadmin8-192x192.svg",
    "sitemap.xml",
    "robots.txt",
    "CNAME",
]

LEGACY_PATTERNS = {
    "legacy GitHub Pages URL prefix": re.compile(r"https://robotics\.air-admin8\.co\.jp/aa8-Robotic/", re.I),
    "legacy logo stylesheet": re.compile(r"main-logo\.css", re.I),
    "legacy PNG logo": re.compile(r"logo-airadmin8-robotics-pc\.png", re.I),
    "legacy brand-picture markup": re.compile(r'class=["\']brand-picture["\']', re.I),
    "legacy logo hiding CSS": re.compile(r"\.brand\s*>\s*\*\s*\{[^{}]*display\s*:\s*none\s*!important", re.I | re.S),
}


def fail(errors: list[str]) -> int:
    for error in errors:
        print(f"ERROR: {error}")
    print(f"Release verification FAILED with {len(errors)} error(s).")
    return 1


def main() -> int:
    errors: list[str] = []
    if not OUTPUT.is_dir():
        return fail(["_site does not exist"])

    for item in REQUIRED_FILES:
        path = OUTPUT / item
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"missing or empty required file: {item}")

    if errors:
        return fail(errors)

    if (OUTPUT / "CNAME").read_text(encoding="utf-8").strip() != "robotics.air-admin8.co.jp":
        errors.append("CNAME mismatch")

    robots = (OUTPUT / "robots.txt").read_text(encoding="utf-8")
    if "Sitemap: https://robotics.air-admin8.co.jp/sitemap.xml" not in robots:
        errors.append("robots.txt sitemap mismatch")

    html_files = sorted(path for path in OUTPUT.rglob("*.html") if "includes" not in path.relative_to(OUTPUT).parts)
    if not html_files:
        errors.append("no publishable HTML files")

    for path in html_files:
        relative = path.relative_to(OUTPUT)
        text = path.read_text(encoding="utf-8")
        required_markers = [
            'data-shared-layout="header"',
            'data-shared-layout="footer"',
            'class="brand-logo brand-logo-pc"',
            'class="brand-logo brand-logo-sp"',
            'shared-layout.css',
            'data-aa8-brand-icon="true"',
            'property="og:url"',
            '<link rel="canonical" href="https://robotics.air-admin8.co.jp/',
        ]
        for marker in required_markers:
            if marker not in text:
                errors.append(f"missing marker {marker}: {relative}")
        if text.count('data-shared-layout="header"') != 1:
            errors.append(f"shared header count is not 1: {relative}")
        if text.count('data-shared-layout="footer"') != 1:
            errors.append(f"shared footer count is not 1: {relative}")

    inspect_files = [
        path for path in OUTPUT.rglob("*")
        if path.is_file() and path.suffix.lower() in {".html", ".css", ".xml", ".js"}
    ]
    for path in inspect_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        relative = path.relative_to(OUTPUT)
        for label, pattern in LEGACY_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{label} remains: {relative}")

    shared_css = (OUTPUT / "assets/css/shared-layout.css").read_text(encoding="utf-8")
    for marker in (".brand-logo-pc", ".brand-logo-sp", "@media (max-width:980px)"):
        if marker not in shared_css:
            errors.append(f"shared-layout.css missing: {marker}")

    for asset in (
        "assets/img/logo-airadmin8-robotics-pc.svg",
        "assets/img/logo-airadmin8-robotics-sp.svg",
        "assets/img/airadmin8-192x192.svg",
    ):
        if "<svg" not in (OUTPUT / asset).read_text(encoding="utf-8", errors="replace"):
            errors.append(f"invalid SVG: {asset}")

    meta_path = OUTPUT / "deploy-meta.json"
    if meta_path.exists():
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
            if not data.get("commit_sha"):
                errors.append("deploy-meta.json missing commit_sha")
        except json.JSONDecodeError as exc:
            errors.append(f"invalid deploy-meta.json: {exc}")

    if errors:
        return fail(errors)

    print(f"Release verification PASSED: {len(html_files)} HTML page(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
