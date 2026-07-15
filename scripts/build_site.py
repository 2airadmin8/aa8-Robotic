#!/usr/bin/env python3
"""Validate the static site, inject shared assets, and build _site.

The production build must not be blocked by content-quality warnings.
Only unreadable JSON or a build-time exception is fatal. HTML, link,
anchor and accessibility findings are recorded in qa-report.json.
"""

from __future__ import annotations

import json
import shutil
import sys
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"
EXCLUDED_DIRS = {".git", ".github", "_site", "scripts"}
SITE_PREFIX = "/aa8-Robotic/"


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
        self.buttons: list[dict[str, str]] = []
        self._in_title = False
        self._button_depth = 0
        self._button_text: list[str] = []
        self._button_attrs: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}

        if tag == "html":
            self.html_lang = values.get("lang", "").strip()
        if "id" in values:
            self.ids.append(values["id"])
        if tag in {"a", "link", "script", "img"}:
            attribute = {"a": "href", "link": "href", "script": "src", "img": "src"}[tag]
            if values.get(attribute):
                self.links.append(values[attribute])
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
        if tag == "button":
            self._button_depth = 1
            self._button_text = []
            self._button_attrs = values
        elif self._button_depth:
            self._button_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        if self._button_depth:
            self._button_depth -= 1
            if tag == "button" and self._button_depth == 0:
                self.buttons.append({
                    "text": "".join(self._button_text).strip(),
                    "aria_label": self._button_attrs.get("aria-label", "").strip(),
                })

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)
        if self._button_depth:
            self._button_text.append(data)

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


def resolve_local_target(document: Path, raw_link: str) -> tuple[Path, str] | None:
    link = raw_link.strip()
    if not link or link.startswith(("mailto:", "tel:", "javascript:", "data:")):
        return None

    parsed = urlparse(link)
    if parsed.scheme in {"http", "https"} or parsed.netloc:
        return None

    clean = parsed.path
    fragment = unquote(parsed.fragment)
    if not clean:
        return document, fragment
    if clean.startswith("/"):
        clean = clean[len(SITE_PREFIX):] if clean.startswith(SITE_PREFIX) else clean.lstrip("/")
        return ROOT / clean, fragment
    return (document.parent / clean).resolve(), fragment


def load_dynamic_ids() -> set[str]:
    path = ROOT / "data" / "products.json"
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return set()
    return {str(item.get("id", "")) for item in data.get("products", []) if item.get("id")}


def validate_json(fatal_errors: list[str]) -> None:
    for path in ROOT.rglob("*.json"):
        if any(part in EXCLUDED_DIRS for part in path.relative_to(ROOT).parts):
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            fatal_errors.append(f"JSON error: {path.relative_to(ROOT)}: {exc}")


def validate_html(findings: list[str]) -> list[PageResult]:
    page_results: list[PageResult] = []
    parser_cache: dict[Path, DocumentParser] = {}
    dynamic_ids = load_dynamic_ids()

    for path in ROOT.rglob("*.html"):
        if any(part in EXCLUDED_DIRS for part in path.relative_to(ROOT).parts):
            continue

        try:
            parser = parse_document(path)
        except (UnicodeDecodeError, OSError) as exc:
            findings.append(f"Unreadable HTML: {path.relative_to(ROOT)}: {exc}")
            continue

        parser_cache[path.resolve()] = parser
        relative = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")

        if path.name != "404.html":
            if not parser.title:
                findings.append(f"Missing title: {relative}")
            if not parser.description:
                findings.append(f"Missing meta description: {relative}")
            if not parser.canonical:
                findings.append(f"Missing canonical: {relative}")
            if parser.h1_count != 1:
                findings.append(f"Expected exactly one h1, found {parser.h1_count}: {relative}")

        if parser.html_lang != "ja":
            findings.append(f"Unexpected or missing html lang: {relative}")
        if "width=device-width" not in parser.viewport:
            findings.append(f"Missing responsive viewport: {relative}")
        if parser.description and not 40 <= len(parser.description) <= 180:
            findings.append(f"Meta description length {len(parser.description)}: {relative}")

        duplicate_ids = sorted({item for item in parser.ids if parser.ids.count(item) > 1})
        if duplicate_ids:
            findings.append(f"Duplicate IDs {duplicate_ids}: {relative}")

        for index, alt in enumerate(parser.image_alts, start=1):
            if alt is None:
                findings.append(f"Missing alt on image {index}: {relative}")

        for index, button in enumerate(parser.buttons, start=1):
            if not button["text"] and not button["aria_label"]:
                findings.append(f"Unnamed button {index}: {relative}")

        for raw_link in parser.links:
            resolved = resolve_local_target(path, raw_link)
            if resolved is None:
                continue
            target, fragment = resolved
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                findings.append(f"Broken local link: {relative} -> {raw_link}")
                continue

            if fragment and target.suffix.lower() == ".html":
                try:
                    target_parser = parser_cache.get(target.resolve()) or parse_document(target)
                    parser_cache[target.resolve()] = target_parser
                    if fragment not in target_parser.ids and fragment not in dynamic_ids:
                        findings.append(f"Missing anchor target: {relative} -> {raw_link}")
                except (UnicodeDecodeError, OSError):
                    findings.append(f"Could not inspect anchor target: {relative} -> {raw_link}")

        if "href=\"#\"" in text or "href='#'" in text:
            findings.append(f"Placeholder href found: {relative}")

        page_results.append(PageResult(
            path=str(relative),
            title=parser.title,
            description_length=len(parser.description),
            h1_count=parser.h1_count,
            link_count=len(parser.links),
            image_count=len(parser.image_alts),
        ))

    return page_results


def inject_shared_assets(html: str, relative: Path) -> str:
    depth = len(relative.parent.parts)
    prefix = "../" * depth

    mobile_css = f'<link rel="stylesheet" href="{prefix}assets/css/mobile-qa.css?v=20260716-2">'
    if "assets/css/mobile-qa.css" not in html and "</head>" in html:
        html = html.replace("</head>", f"  {mobile_css}\n</head>", 1)

    # GT- is a Google tag ID, not a GTM container ID. Prevent the legacy
    # JavaScript from requesting gtm.js with an incompatible identifier.
    analytics_guard = '<script data-google-tag-loader aria-hidden="true"></script>'
    if "data-google-tag-loader" not in html and "</head>" in html:
        html = html.replace("</head>", f"  {analytics_guard}\n</head>", 1)

    scripts: list[str] = []
    if "assets/js/mobile-qa.js" not in html:
        scripts.append(f'<script src="{prefix}assets/js/mobile-qa.js?v=20260716-2" defer></script>')
    if "assets/js/seo.js" not in html:
        scripts.append(f'<script src="{prefix}assets/js/seo.js?v=20260716-1" defer></script>')
    if scripts and "</body>" in html:
        html = html.replace("</body>", "\n".join(scripts) + "\n</body>", 1)

    return html


def build_output(page_results: list[PageResult], findings: list[str]) -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)

    for source in iter_source_files():
        relative = source.relative_to(ROOT)
        destination = OUTPUT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix.lower() == ".html":
            html = source.read_text(encoding="utf-8")
            destination.write_text(inject_shared_assets(html, relative), encoding="utf-8")
        else:
            shutil.copy2(source, destination)

    report = {
        "status": "passed_with_findings" if findings else "passed",
        "html_pages": len(page_results),
        "findings": findings,
        "pages": [asdict(result) for result in page_results],
    }
    (OUTPUT / "qa-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    fatal_errors: list[str] = []
    findings: list[str] = []

    validate_json(fatal_errors)
    pages = validate_html(findings)

    for finding in findings:
        print(f"QA: {finding}")

    if fatal_errors:
        for error in fatal_errors:
            print(f"FATAL: {error}")
        print(f"Build stopped with {len(fatal_errors)} fatal error(s).")
        sys.exit(1)

    try:
        build_output(pages, findings)
    except Exception as exc:  # noqa: BLE001 - CI must report any build exception.
        print(f"FATAL: Build failed: {exc}")
        sys.exit(1)

    print(f"Build completed. {len(pages)} HTML pages were written to _site.")
    print(f"QA report: _site/qa-report.json ({len(findings)} finding(s)).")