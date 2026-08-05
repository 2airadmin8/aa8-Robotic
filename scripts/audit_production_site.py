#!/usr/bin/env python3
"""Audit the deployed production site using sitemap.xml as the source of truth."""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from html.parser import HTMLParser

DEFAULT_BASE_URL = "https://robotics.air-admin8.co.jp"
DEFAULT_TIMEOUT = 20
LEGACY_REDIRECTS = {
    "/aa8-Robotic/glossary/physical-ai.html": "/glossary/physical-ai.html",
}
CORE_PATHS = {"/", "/about.html", "/glossary.html", "/contact.html", "/privacy.html"}


@dataclass
class PageAudit:
    url: str
    status: int
    final_url: str
    title: str
    canonical: str
    h1_count: int
    has_header: bool
    has_footer: bool
    errors: list[str]
    warnings: list[str]


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title_parts: list[str] = []
        self.canonical = ""
        self.meta_refresh = ""
        self.h1_count = 0
        self.has_header = False
        self.has_footer = False
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag == "title":
            self._in_title = True
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "header":
            classes = set(values.get("class", "").split())
            self.has_header = self.has_header or values.get("data-shared-layout") == "header" or "site-header" in classes
        elif tag == "footer":
            classes = set(values.get("class", "").split())
            self.has_footer = self.has_footer or values.get("data-shared-layout") == "footer" or "footer" in classes
        elif tag == "link" and "canonical" in values.get("rel", "").lower().split():
            self.canonical = values.get("href", "").strip()
        elif tag == "meta" and values.get("http-equiv", "").lower() == "refresh":
            self.meta_refresh = values.get("content", "").strip()

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)

    @property
    def title(self) -> str:
        return "".join(self.title_parts).strip()


def fetch(url: str, timeout: int) -> tuple[int, str, bytes, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AirAdmin8-Production-Audit/1.0",
            "Cache-Control": "no-cache",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            return response.status, response.geturl(), response.read(), content_type
    except urllib.error.HTTPError as exc:
        return exc.code, exc.geturl(), exc.read(), exc.headers.get("Content-Type", "")


def sitemap_urls(base_url: str, timeout: int) -> list[str]:
    status, _, body, _ = fetch(f"{base_url}/sitemap.xml", timeout)
    if status != 200:
        raise RuntimeError(f"sitemap.xml returned HTTP {status}")
    root = ET.fromstring(body)
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [node.text.strip() for node in root.findall("sm:url/sm:loc", namespace) if node.text]
    if not urls:
        raise RuntimeError("sitemap.xml contains no URLs")
    return sorted(dict.fromkeys(urls))


def audit_page(url: str, timeout: int) -> PageAudit:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        status, final_url, body, content_type = fetch(url, timeout)
    except Exception as exc:  # noqa: BLE001
        return PageAudit(url, 0, "", "", "", 0, False, False, [f"request failed: {exc}"], [])

    parser = PageParser()
    if status == 200 and "html" in content_type.lower():
        parser.feed(body.decode("utf-8", errors="replace"))

    if status != 200:
        errors.append(f"HTTP {status}")
    if status == 200:
        if not parser.title:
            warnings.append("title missing")
        if not parser.canonical:
            warnings.append("canonical missing")
        elif parser.canonical != final_url:
            warnings.append(f"canonical mismatch: {parser.canonical}")
        if parser.h1_count != 1:
            warnings.append(f"h1 count is {parser.h1_count}")
        if not parser.has_header:
            warnings.append("header missing")
        if not parser.has_footer:
            warnings.append("footer missing")

    path = urllib.parse.urlparse(url).path or "/"
    if path in CORE_PATHS and errors:
        errors.append("core page unavailable")

    return PageAudit(url, status, final_url, parser.title, parser.canonical, parser.h1_count, parser.has_header, parser.has_footer, errors, warnings)


def normalize_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path or "/", parsed.query, ""))


def html_redirect_target(body: bytes, source_url: str) -> str:
    text = body.decode("utf-8", errors="replace")
    parser = PageParser()
    parser.feed(text)
    candidates: list[str] = []
    if parser.canonical:
        candidates.append(parser.canonical)
    if parser.meta_refresh:
        match = re.search(r"(?:^|;)\s*url\s*=\s*['\"]?([^'\";]+)", parser.meta_refresh, re.I)
        if match:
            candidates.append(match.group(1).strip())
    js_match = re.search(r"(?:window\.)?location\.replace\(\s*['\"]([^'\"]+)['\"]\s*\)", text, re.I)
    if js_match:
        candidates.append(js_match.group(1).strip())
    return urllib.parse.urljoin(source_url, candidates[0]) if candidates else ""


def audit_legacy_redirects(base_url: str, timeout: int) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for source_path, target_path in LEGACY_REDIRECTS.items():
        source_url = base_url + source_path
        expected_url = base_url + target_path
        try:
            status, final_url, body, content_type = fetch(source_url, timeout)
            effective_url = final_url
            method = "http"
            if normalize_url(final_url) == normalize_url(source_url) and status == 200 and "html" in content_type.lower():
                html_target = html_redirect_target(body, source_url)
                if html_target:
                    effective_url = html_target
                    method = "html"
            ok = status == 200 and normalize_url(effective_url) == normalize_url(expected_url)
            results.append({"source": source_url, "expected": expected_url, "status": status, "final_url": effective_url, "method": method, "ok": ok})
        except Exception as exc:  # noqa: BLE001
            results.append({"source": source_url, "expected": expected_url, "status": 0, "final_url": "", "method": "error", "ok": False, "error": str(exc)})
    return results


def markdown_report(audits: list[PageAudit], redirects: list[dict[str, object]]) -> str:
    failed = [item for item in audits if item.errors]
    warned = [item for item in audits if item.warnings]
    lines = ["## 本番サイト全URL監査", "", f"- Sitemap URL数: **{len(audits)}**", f"- 正常: **{len(audits) - len(failed)}**", f"- 失敗: **{len(failed)}**", f"- Warningあり: **{len(warned)}**", ""]
    if failed:
        lines.extend(["### 失敗", "", "| URL | 内容 |", "|---|---|"])
        lines.extend(f"| {item.url} | {'; '.join(item.errors)} |" for item in failed)
        lines.append("")
    if warned:
        lines.extend(["### Warning", "", "| URL | 内容 |", "|---|---|"])
        lines.extend(f"| {item.url} | {'; '.join(item.warnings)} |" for item in warned[:30])
        if len(warned) > 30:
            lines.append(f"| ... | 他 {len(warned) - 30}件 |")
        lines.append("")
    lines.extend(["### 旧URL移行", "", "| 旧URL | 最終URL | 方式 | 結果 |", "|---|---|---|---|"])
    for item in redirects:
        result = "✅ PASS" if item.get("ok") else "❌ FAIL"
        lines.append(f"| {item['source']} | {item.get('final_url', '')} | {item.get('method', '')} | {result} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--json", default="production-audit.json")
    parser.add_argument("--markdown", default="production-audit.md")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")
    try:
        urls = sitemap_urls(base_url, args.timeout)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}")
        return 1
    audits = [audit_page(url, args.timeout) for url in urls]
    redirects = audit_legacy_redirects(base_url, args.timeout)
    with open(args.json, "w", encoding="utf-8") as handle:
        json.dump({"base_url": base_url, "pages": [asdict(item) for item in audits], "legacy_redirects": redirects}, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    markdown = markdown_report(audits, redirects)
    with open(args.markdown, "w", encoding="utf-8") as handle:
        handle.write(markdown)
    print(markdown)
    return 1 if any(item.errors for item in audits) or any(not item.get("ok") for item in redirects) else 0


if __name__ == "__main__":
    sys.exit(main())
