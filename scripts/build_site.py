#!/usr/bin/env python3
"""Validate the static site, inject shared SEO script, and build _site."""

from __future__ import annotations

import json
import re
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"
EXCLUDED_DIRS = {".git", ".github", "_site", "scripts"}


class DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.ids: list[str] = []
        self.title_parts: list[str] = []
        self.description = ""
        self.canonical = ""
        self.h1_count = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if "id" in values:
            self.ids.append(values["id"])
        if tag in {"a", "link", "script", "img"}:
            attribute = {"a": "href", "link": "href", "script": "src", "img": "src"}[tag]
            if values.get(attribute):
                self.links.append(values[attribute])
        if tag == "meta" and values.get("name") == "description":
            self.description = values.get("content", "").strip()
        if tag == "link" and values.get("rel") == "canonical":
            self.canonical = values.get("href", "").strip()
        if tag == "title":
            self._in_title = True
        if tag == "h1":
            self.h1_count += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)

    @property
    def title(self) -> str:
        return "".join(self.title_parts).strip()


def iter_source_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        files.append(path)
    return files


def resolve_local_target(document: Path, raw_link: str) -> Path | None:
    link = raw_link.strip()
    if not link or link.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None
    parsed = urlparse(link)
    if parsed.scheme in {"http", "https"} or parsed.netloc:
        return None
    clean = parsed.path
    if not clean:
        return None
    if clean.startswith("/"):
        prefix = "/aa8-Robotic/"
        clean = clean[len(prefix):] if clean.startswith(prefix) else clean.lstrip("/")
        return ROOT / clean
    return (document.parent / clean).resolve()


def validate_json(errors: list[str]) -> None:
    for path in ROOT.rglob("*.json"):
        if any(part in EXCLUDED_DIRS for part in path.relative_to(ROOT).parts):
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            errors.append(f"JSON error: {path.relative_to(ROOT)}: {exc}")


def validate_html(errors: list[str], warnings: list[str]) -> None:
    for path in ROOT.rglob("*.html"):
        if any(part in EXCLUDED_DIRS for part in path.relative_to(ROOT).parts):
            continue
        text = path.read_text(encoding="utf-8")
        parser = DocumentParser()
        parser.feed(text)
        relative = path.relative_to(ROOT)

        if path.name != "404.html":
            if not parser.title:
                errors.append(f"Missing title: {relative}")
            if not parser.description:
                errors.append(f"Missing meta description: {relative}")
            if not parser.canonical:
                errors.append(f"Missing canonical: {relative}")
            if parser.h1_count != 1:
                errors.append(f"Expected exactly one h1, found {parser.h1_count}: {relative}")

        duplicate_ids = sorted({item for item in parser.ids if parser.ids.count(item) > 1})
        if duplicate_ids:
            errors.append(f"Duplicate IDs {duplicate_ids}: {relative}")

        for raw_link in parser.links:
            target = resolve_local_target(path, raw_link)
            if target is None:
                continue
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                errors.append(f"Broken local link: {relative} -> {raw_link}")

        if "href=\"#\"" in text or "href='#'" in text:
            warnings.append(f"Placeholder href found: {relative}")


def inject_seo_script(html: str, relative: Path) -> str:
    if "assets/js/seo.js" in html:
        return html
    depth = len(relative.parent.parts)
    prefix = "../" * depth
    script = f'<script src="{prefix}assets/js/seo.js?v=20260716-1" defer></script>'
    if "</body>" not in html:
        return html
    return html.replace("</body>", f"{script}\n</body>", 1)


def build_output() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)

    for source in iter_source_files():
        relative = source.relative_to(ROOT)
        destination = OUTPUT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix.lower() == ".html":
            html = source.read_text(encoding="utf-8")
            destination.write_text(inject_seo_script(html, relative), encoding="utf-8")
        else:
            shutil.copy2(source, destination)


if __name__ == "__main__":
    errors: list[str] = []
    warnings: list[str] = []
    validate_json(errors)
    validate_html(errors, warnings)

    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Validation failed with {len(errors)} error(s).")
        sys.exit(1)

    build_output()
    html_count = len(list(OUTPUT.rglob("*.html")))
    print(f"Validation passed. Built {html_count} HTML pages into _site.")
