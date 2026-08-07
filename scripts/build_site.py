#!/usr/bin/env python3
"""Validate and build the AirAdmin8 Robotics static site.

Header and footer have exactly one source of truth:
- includes/site-header.html
- includes/site-footer.html
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"
EXCLUDED_DIRS = {".git", ".github", "_site", "scripts", "includes"}
BUILD_VERSION = os.environ.get("GITHUB_SHA", "local-dev")[:12]
PRODUCTION_ORIGIN = "https://robotics.air-admin8.co.jp"
HEADER_SOURCE = ROOT / "includes" / "site-header.html"
FOOTER_SOURCE = ROOT / "includes" / "site-footer.html"
SOURCE_GUIDE_PDF = ROOT / "assets" / "pdf" / "AirAdmin8_AI_Robotics_Support_for_University_Labs.pdf"
PUBLIC_GUIDE_PDF = OUTPUT / "assets" / "pdf" / "AirAdmin8_AI_Robotics_Support_for_University_Labs.pdf"


@dataclass
class PageResult:
    path: str
    title: str
    description_length: int
    h1_count: int
    link_count: int
    image_count: int


class DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.ids: list[str] = []
        self.title_parts: list[str] = []
        self.description = ""
        self.canonical = ""
        self.h1_count = 0
        self.image_alts: list[str | None] = []
        self.html_lang = ""
        self.viewport = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "html":
            self.html_lang = values.get("lang", "").strip()
        if "id" in values:
            self.ids.append(values["id"])
        if tag in {"a", "link", "script", "img"}:
            attr = {"a": "href", "link": "href", "script": "src", "img": "src"}[tag]
            if values.get(attr):
                self.links.append(values[attr])
        if tag == "img":
            self.image_alts.append(values.get("alt") if "alt" in values else None)
        if tag == "meta" and values.get("name") == "description":
            self.description = values.get("content", "").strip()
        if tag == "meta" and values.get("name") == "viewport":
            self.viewport = values.get("content", "").strip()
        if tag == "link" and "canonical" in values.get("rel", "").split():
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


def parse_document(path: Path) -> DocumentParser:
    parser = DocumentParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def validate_json(fatal_errors: list[str]) -> None:
    for path in ROOT.rglob("*.json"):
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            fatal_errors.append(f"JSON error: {relative}: {exc}")


def validate_html(findings: list[str]) -> list[PageResult]:
    results: list[PageResult] = []
    for path in ROOT.rglob("*.html"):
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        try:
            parser = parse_document(path)
        except (UnicodeDecodeError, OSError) as exc:
            findings.append(f"Unreadable HTML: {relative}: {exc}")
            continue
        if path.name != "404.html":
            if not parser.title:
                findings.append(f"Missing title: {relative}")
            if not parser.description:
                findings.append(f"Missing meta description: {relative}")
            if not parser.canonical:
                findings.append(f"Missing canonical: {relative}")
            if parser.h1_count != 1:
                findings.append(f"Expected exactly one h1, found {parser.h1_count}: {relative}")
        results.append(PageResult(str(relative), parser.title, len(parser.description), parser.h1_count, len(parser.links), len(parser.image_alts)))
    return results


def page_prefix(relative: Path) -> str:
    return "../" * len(relative.parent.parts)


def canonical_url(relative: Path) -> str:
    if relative.as_posix() == "index.html":
        return f"{PRODUCTION_ORIGIN}/"
    return f"{PRODUCTION_ORIGIN}/{relative.as_posix()}"


def shared_markup(source: Path, prefix: str) -> str:
    markup = source.read_text(encoding="utf-8").strip()
    return re.sub(r'(?P<attr>(?:href|src|srcset)=["\'])/', rf'\g<attr>{prefix}', markup)


def replace_required_block(html: str, tag: str, class_name: str, replacement: str, relative: Path) -> str:
    pattern = re.compile(
        rf'<{tag}\b(?=[^>]*class=["\'][^"\']*\b{re.escape(class_name)}\b[^"\']*["\'])[^>]*>.*?</{tag}>',
        re.I | re.S,
    )
    if not pattern.search(html):
        raise ValueError(f"{relative}: {tag}.{class_name} not found")
    return pattern.sub(replacement, html, count=1)


def rewrite_canonical(html: str, relative: Path) -> str:
    expected = canonical_url(relative)
    pattern = re.compile(
        r'<link\b(?=[^>]*\brel=["\'][^"\']*\bcanonical\b[^"\']*["\'])[^>]*>',
        re.I,
    )
    replacement = f'<link rel="canonical" href="{expected}">'
    if pattern.search(html):
        return pattern.sub(replacement, html, count=1)
    if "</head>" in html:
        return html.replace("</head>", f"  {replacement}\n</head>", 1)
    raise ValueError(f"{relative}: </head> not found for canonical injection")


def build_html(html: str, relative: Path) -> str:
    prefix = page_prefix(relative)
    html = replace_required_block(html, "header", "site-header", shared_markup(HEADER_SOURCE, prefix), relative)
    html = replace_required_block(html, "footer", "footer", shared_markup(FOOTER_SOURCE, prefix), relative)
    html = rewrite_canonical(html, relative)

    html = re.sub(r'assets/css/site\.css(?:\?v=[^"\']+)?', f'assets/css/site.css?v={BUILD_VERSION}', html)
    html = re.sub(r'assets/js/site\.js(?:\?v=[^"\']+)?', f'assets/js/site.js?v={BUILD_VERSION}', html)

    mobile_css = f'<link rel="stylesheet" href="{prefix}assets/css/mobile-qa.css?v={BUILD_VERSION}">'
    if "assets/css/mobile-qa.css" not in html and "</head>" in html:
        html = html.replace("</head>", f"  {mobile_css}\n</head>", 1)

    scripts: list[str] = []
    if "assets/js/mobile-qa.js" not in html:
        scripts.append(f'<script src="{prefix}assets/js/mobile-qa.js?v={BUILD_VERSION}" defer></script>')
    if "assets/js/seo.js" not in html:
        scripts.append(f'<script src="{prefix}assets/js/seo.js?v={BUILD_VERSION}" defer></script>')
    if scripts and "</body>" in html:
        html = html.replace("</body>", "\n".join(scripts) + "\n</body>", 1)
    return html


def build_output(page_results: list[PageResult], findings: list[str]) -> None:
    for source in (HEADER_SOURCE, FOOTER_SOURCE, SOURCE_GUIDE_PDF):
        if not source.is_file():
            raise FileNotFoundError(f"Missing required source: {source.relative_to(ROOT)}")
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)

    for source in iter_source_files():
        relative = source.relative_to(ROOT)
        destination = OUTPUT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix.lower() == ".html":
            destination.write_text(build_html(source.read_text(encoding="utf-8"), relative), encoding="utf-8")
        else:
            shutil.copy2(source, destination)

    PUBLIC_GUIDE_PDF.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_GUIDE_PDF, PUBLIC_GUIDE_PDF)
    if PUBLIC_GUIDE_PDF.stat().st_size != SOURCE_GUIDE_PDF.stat().st_size:
        raise OSError("Published PDF alias size does not match source PDF")

    report = {
        "status": "passed_with_findings" if findings else "passed",
        "build_version": BUILD_VERSION,
        "html_pages": len(page_results),
        "findings": findings,
        "pages": [asdict(result) for result in page_results],
    }
    (OUTPUT / "qa-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    fatal_errors: list[str] = []
    findings: list[str] = []
    validate_json(fatal_errors)
    pages = validate_html(findings)
    for finding in findings:
        print(f"QA: {finding}")
    if fatal_errors:
        for error in fatal_errors:
            print(f"FATAL: {error}")
        return 1
    try:
        build_output(pages, findings)
    except Exception as exc:  # noqa: BLE001
        print(f"FATAL: Build failed: {exc}")
        return 1
    print(f"Build completed. {len(pages)} HTML pages were written to _site.")
    print(f"Published PDF alias: {PUBLIC_GUIDE_PDF.relative_to(OUTPUT)}")
    print(f"QA report: _site/qa-report.json ({len(findings)} finding(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
