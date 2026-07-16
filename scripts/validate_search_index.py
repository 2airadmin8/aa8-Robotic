#!/usr/bin/env python3
"""Validate Search Console readiness for sitemap, canonical and robots files."""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://2airadmin8.github.io/aa8-Robotic/"
SITEMAP_PATH = ROOT / "sitemap.xml"
ROBOTS_PATH = ROOT / "robots.txt"
SEO_PATH = ROOT / "data" / "seo-keywords.json"
READINESS_PATH = ROOT / "data" / "search-console-readiness.json"


class CanonicalParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.canonical = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "link":
            return
        values = {key.lower(): value or "" for key, value in attrs}
        if values.get("rel", "").lower() == "canonical":
            self.canonical = values.get("href", "").strip()


def expected_file_for_url(url: str) -> Path | None:
    if not url.startswith(BASE_URL):
        return None
    relative = url[len(BASE_URL):]
    if not relative:
        return ROOT / "index.html"
    if relative.endswith("/"):
        return ROOT / relative / "index.html"
    return ROOT / relative


def read_canonical(path: Path) -> str:
    parser = CanonicalParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser.canonical


def main() -> int:
    errors: list[str] = []

    try:
        tree = ET.parse(SITEMAP_PATH)
        namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        sitemap_urls = [
            node.text.strip()
            for node in tree.findall("sm:url/sm:loc", namespace)
            if node.text and node.text.strip()
        ]
    except (OSError, ET.ParseError) as exc:
        print(f"SEARCH ERROR: cannot read sitemap.xml: {exc}")
        return 1

    if not sitemap_urls:
        errors.append("sitemap.xml contains no URLs")
    if len(sitemap_urls) != len(set(sitemap_urls)):
        errors.append("sitemap.xml contains duplicate URLs")

    for url in sitemap_urls:
        parsed = urlparse(url)
        if parsed.query or parsed.fragment:
            errors.append(f"Sitemap URL contains query or fragment: {url}")
        file_path = expected_file_for_url(url)
        if file_path is None:
            errors.append(f"Sitemap URL is outside the public base: {url}")
            continue
        if not file_path.exists():
            errors.append(f"Sitemap target file does not exist: {file_path.relative_to(ROOT)}")
            continue
        if file_path.suffix.lower() == ".html":
            canonical = read_canonical(file_path)
            if not canonical:
                errors.append(f"Missing canonical: {file_path.relative_to(ROOT)}")
            elif canonical != url:
                errors.append(
                    f"Canonical mismatch for {file_path.relative_to(ROOT)}: {canonical} != {url}"
                )

    try:
        robots = ROBOTS_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"Cannot read robots.txt: {exc}")
        robots = ""

    expected_sitemap_line = f"Sitemap: {BASE_URL}sitemap.xml"
    if "User-agent: *" not in robots:
        errors.append("robots.txt is missing User-agent: *")
    if "Allow: /" not in robots:
        errors.append("robots.txt is missing Allow: /")
    if expected_sitemap_line not in robots:
        errors.append(f"robots.txt is missing exact sitemap line: {expected_sitemap_line}")

    try:
        seo = json.loads(SEO_PATH.read_text(encoding="utf-8"))
        seo_urls = {
            BASE_URL if page.get("path") == "index.html" else f"{BASE_URL}{page.get('path', '')}"
            for page in seo.get("pages", [])
            if page.get("path")
        }
        missing_from_sitemap = sorted(seo_urls - set(sitemap_urls))
        if missing_from_sitemap:
            errors.append(
                "SEO-managed pages missing from sitemap: " + ", ".join(missing_from_sitemap)
            )
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Cannot read SEO registry: {exc}")

    try:
        readiness = json.loads(READINESS_PATH.read_text(encoding="utf-8"))
        current_base = readiness.get("property", {}).get("currentPublicBase")
        if current_base != BASE_URL:
            errors.append(f"Search Console currentPublicBase mismatch: {current_base}")
        for url in readiness.get("priorityInspectionPages", []):
            if url not in sitemap_urls:
                errors.append(f"Priority inspection page missing from sitemap: {url}")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Cannot read Search Console readiness data: {exc}")

    if errors:
        for error in errors:
            print(f"SEARCH ERROR: {error}")
        print(f"Search index validation failed with {len(errors)} error(s).")
        return 1

    print(
        f"Search index validation passed: {len(sitemap_urls)} sitemap URLs, "
        "canonical and robots are consistent."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
