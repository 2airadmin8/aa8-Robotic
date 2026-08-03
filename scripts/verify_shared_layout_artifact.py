#!/usr/bin/env python3
"""Verify the final _site artifact uses one shared Header/Footer source.

This script checks build output, not editable source HTML.
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"
HEADER_SOURCE = ROOT / "includes/site-header.html"
FOOTER_SOURCE = ROOT / "includes/site-footer.html"

HEADER_RE = re.compile(
    r'<header\b(?=[^>]*class=["\'][^"\']*\bsite-header\b[^"\']*["\'])[^>]*>.*?</header>',
    re.I | re.S,
)
FOOTER_RE = re.compile(
    r'<footer\b(?=[^>]*class=["\'][^"\']*\bfooter\b[^"\']*["\'])[^>]*>.*?</footer>',
    re.I | re.S,
)
URL_ATTR_RE = re.compile(r'(?P<attr>(?:href|src|srcset)=["\'])(?P<url>[^"\']+)', re.I)
SPACE_RE = re.compile(r"\s+")


def canonicalize(markup: str) -> str:
    """Normalize relative/root URLs and insignificant whitespace for comparison."""
    def replace_url(match: re.Match[str]) -> str:
        url = match.group("url")
        clean = re.sub(r"^(?:\.\./)+", "/", url)
        if clean.startswith("index.html"):
            clean = "/"
        elif not clean.startswith(("/", "http://", "https://", "#", "mailto:", "tel:")):
            clean = "/" + clean
        clean = clean.replace("/index.html", "/")
        return match.group("attr") + clean

    normalized = URL_ATTR_RE.sub(replace_url, markup.strip())
    normalized = re.sub(r'\s+aria-current=["\']page["\']', "", normalized, flags=re.I)
    normalized = SPACE_RE.sub(" ", normalized)
    return normalized.strip()


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main() -> int:
    errors: list[str] = []
    if not OUTPUT.is_dir():
        print("ERROR: _site does not exist. Run build first.")
        return 1
    for source in (HEADER_SOURCE, FOOTER_SOURCE):
        if not source.is_file():
            errors.append(f"Missing single source: {source.relative_to(ROOT)}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    expected_header = canonicalize(HEADER_SOURCE.read_text(encoding="utf-8"))
    expected_footer = canonicalize(FOOTER_SOURCE.read_text(encoding="utf-8"))
    expected_header_hash = digest(expected_header)
    expected_footer_hash = digest(expected_footer)

    pages = sorted(
        path for path in OUTPUT.rglob("*.html")
        if "includes" not in path.relative_to(OUTPUT).parts
    )
    if not pages:
        errors.append("No publishable HTML pages found in _site")

    checked = 0
    for page in pages:
        relative = page.relative_to(OUTPUT)
        text = page.read_text(encoding="utf-8")
        headers = HEADER_RE.findall(text)
        footers = FOOTER_RE.findall(text)

        if len(headers) != 1:
            errors.append(f"Expected exactly one shared header: {relative} ({len(headers)})")
            continue
        if len(footers) != 1:
            errors.append(f"Expected exactly one shared footer: {relative} ({len(footers)})")
            continue

        header = canonicalize(headers[0])
        footer = canonicalize(footers[0])
        if digest(header) != expected_header_hash:
            errors.append(f"Header differs from includes/site-header.html: {relative}")
        if digest(footer) != expected_footer_hash:
            errors.append(f"Footer differs from includes/site-footer.html: {relative}")

        forbidden = {
            '<picture class="brand-picture">': "legacy brand-picture",
            'class="brand-mark"': "legacy text brand mark",
            "TOP Header Sync": "legacy TOP sync marker",
        }
        for marker, label in forbidden.items():
            if marker in text:
                errors.append(f"Forbidden {label} remains: {relative}")

        required = [
            'data-shared-layout="header"',
            'data-shared-layout="footer"',
            'class="brand-logo brand-logo-pc"',
            'class="brand-logo brand-logo-sp"',
            'assets/css/shared-layout.css',
        ]
        for marker in required:
            if marker not in text:
                errors.append(f"Required artifact marker missing ({marker}): {relative}")
        checked += 1

    required_assets = [
        OUTPUT / "assets/css/shared-layout.css",
        OUTPUT / "assets/img/logo-airadmin8-robotics-pc.svg",
        OUTPUT / "assets/img/logo-airadmin8-robotics-sp.svg",
    ]
    for asset in required_assets:
        if not asset.is_file() or asset.stat().st_size == 0:
            errors.append(f"Missing or empty artifact asset: {asset.relative_to(OUTPUT)}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Artifact verification FAILED: {len(errors)} error(s), {checked} page(s) inspected.")
        return 1

    print(
        "Artifact verification PASSED: "
        f"{checked} page(s), header={expected_header_hash[:12]}, footer={expected_footer_hash[:12]}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
