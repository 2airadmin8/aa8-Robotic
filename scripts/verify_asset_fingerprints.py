#!/usr/bin/env python3
"""Verify generated HTML references shared assets with current content hashes."""
from __future__ import annotations

import hashlib
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
ASSETS = (
    "assets/css/main-site-experience.css",
    "assets/css/shared-layout.css",
    "assets/js/main-site-experience.js",
)


class StylesheetLinks(HTMLParser):
    """Collect real stylesheet links in the head, excluding inert markup."""

    INERT = {"template", "noscript", "textarea", "title", "xmp", "iframe"}

    def __init__(self) -> None:
        super().__init__()
        self.in_head = False
        self.inert: list[str] = []
        self.active: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.INERT:
            self.inert.append(tag)
            return
        if self.inert:
            return
        if tag == "head":
            self.in_head = True
        elif tag == "body":
            self.in_head = False
        elif tag == "link" and self.in_head:
            fields = dict(attrs)
            if len(fields) != len(attrs) or "disabled" in fields:
                return
            rel = set((fields.get("rel") or "").lower().split())
            media = (fields.get("media") or "").strip().lower()
            if rel == {"stylesheet"} and media in ("", "all") and fields.get("href"):
                self.active.append(fields["href"])

    def handle_endtag(self, tag: str) -> None:
        if self.inert:
            if tag == self.inert[-1]:
                self.inert.pop()
            return
        if tag == "head":
            self.in_head = False


def digest(relative: str) -> str:
    path = SITE / relative
    if not path.is_file():
        raise SystemExit(f"Missing fingerprint target: {relative}")
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def main() -> int:
    if not SITE.is_dir():
        raise SystemExit("_site does not exist")

    expected = {asset: digest(asset) for asset in ASSETS}
    html_files = sorted(path for path in SITE.rglob("*.html") if "includes" not in path.relative_to(SITE).parts)
    if not html_files:
        raise SystemExit("No publishable HTML files")

    errors: list[str] = []
    for path in html_files:
        relative = path.relative_to(SITE)
        text = path.read_text(encoding="utf-8")
        links = StylesheetLinks()
        links.feed(text)
        links.close()
        prefix = "../" * (len(relative.parents) - 1)
        for asset, version in expected.items():
            if asset.endswith(".css"):
                href = f"{prefix}{asset}?v={version}"
                count = links.active.count(href)
                if count != 1:
                    errors.append(
                        f"expected exactly one active stylesheet {href}, found {count}: {relative}"
                    )
                continue
            name = re.escape(Path(asset).name)
            pattern = re.compile(rf'{name}\?v={version}(?=["\'])')
            if not pattern.search(text):
                errors.append(f"stale or missing fingerprint for {asset}: {relative}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Asset fingerprint verification FAILED with {len(errors)} error(s).")
        return 1

    print(f"Asset fingerprint verification PASSED for {len(html_files)} page(s).")
    for asset, version in expected.items():
        print(f"- {asset}?v={version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
