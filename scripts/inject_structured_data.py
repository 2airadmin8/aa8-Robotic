#!/usr/bin/env python3
"""Inject core JSON-LD into the built HTML artifact.

Search engines should receive Organization, page, breadcrumb and FAQ schemas
without having to execute JavaScript. The runtime SEO script keeps the same
IDs, so it becomes a fallback and does not create duplicates.
"""

from __future__ import annotations

import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"
PUBLIC_BASE = "https://2airadmin8.github.io/aa8-Robotic/"
SOCIAL_IMAGE = f"{PUBLIC_BASE}assets/img/robot-category-lineup.svg"

PAGE_MAP = {
    "index.html": {"name": "AirAdmin8 Robotics", "type": "WebSite"},
    "products.html": {"name": "研究用AIロボット製品比較", "type": "CollectionPage"},
    "use-cases.html": {"name": "研究テーマ・用途から探す", "type": "CollectionPage"},
    "support.html": {"name": "AIロボット導入支援", "type": "Service"},
    "cases.html": {"name": "AIロボット導入事例", "type": "CollectionPage"},
    "resources.html": {"name": "AIロボット開発資料・SDK", "type": "CollectionPage"},
    "manufacturers.html": {"name": "AIロボットメーカー比較", "type": "CollectionPage"},
    "contact.html": {"name": "AIロボット製品・導入相談", "type": "ContactPage"},
    "privacy.html": {"name": "プライバシーポリシー", "type": "WebPage"},
    "faq.html": {"name": "よくある質問", "type": "FAQPage"},
    "about.html": {"name": "会社情報", "type": "AboutPage"},
    "products/unitree-g1-d.html": {"name": "Unitree G1-D", "type": "Product", "brand": "Unitree"},
    "products/agibot-g2.html": {"name": "AgiBot G2", "type": "Product", "brand": "AgiBot"},
    "products/unitree-g1.html": {"name": "Unitree G1", "type": "Product", "brand": "Unitree"},
    "products/unitree-go2.html": {"name": "Unitree Go2 EDU", "type": "Product", "brand": "Unitree"},
    "products/agibot-x2-edu.html": {"name": "AgiBot X2 EDU", "type": "Product", "brand": "AgiBot"},
    "products/limx-oli.html": {"name": "LimX Oli", "type": "Product", "brand": "LimX Dynamics"},
    "products/tianji-marvin.html": {"name": "Tianji Marvin", "type": "Product", "brand": "Tianji"},
    "manufacturers/unitree.html": {"name": "Unitree Robotics", "type": "Brand"},
    "manufacturers/agibot.html": {"name": "AgiBot", "type": "Brand"},
    "use-cases/vla-data-collection.html": {"name": "VLA・模倣学習データ収集", "type": "Service"},
    "support/university-procurement.html": {"name": "大学研究用AIロボット導入・購買支援", "type": "Service"},
    "cases/keio-selection.html": {"name": "慶應義塾大学向け選定・見積支援", "type": "Article"},
}

TITLE_PATTERN = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
DESCRIPTION_PATTERN = re.compile(
    r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']\s*/?>',
    re.IGNORECASE | re.DOTALL,
)
CANONICAL_PATTERN = re.compile(
    r'<link\s+rel=["\']canonical["\']\s+href=["\'](.*?)["\']\s*/?>',
    re.IGNORECASE | re.DOTALL,
)
MANAGED_SCRIPT_PATTERN = re.compile(
    r'\s*<script\s+id=["\'](?:organization-schema|page-schema|breadcrumb-schema|faq-schema)["\']\s+type=["\']application/ld\+json["\']>.*?</script>',
    re.IGNORECASE | re.DOTALL,
)


class BreadcrumbParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_breadcrumb = False
        self.current_href = ""
        self.current_text: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "div" and "breadcrumb" in values.get("class", "").split():
            self.in_breadcrumb = True
        elif self.in_breadcrumb and tag == "a":
            self.current_href = values.get("href", "")
            self.current_text = []

    def handle_data(self, data: str) -> None:
        if self.in_breadcrumb and self.current_href:
            self.current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self.in_breadcrumb and tag == "a" and self.current_href:
            label = "".join(self.current_text).strip()
            if label:
                self.links.append((label, self.current_href))
            self.current_href = ""
            self.current_text = []
        elif self.in_breadcrumb and tag == "div":
            self.in_breadcrumb = False


class FaqParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_item = False
        self.in_summary = False
        self.answer_depth = 0
        self.question_parts: list[str] = []
        self.answer_parts: list[str] = []
        self.entries: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "details" and "data-faq-item" in values:
            self.in_item = True
            self.question_parts = []
            self.answer_parts = []
        elif self.in_item and tag == "summary":
            self.in_summary = True
        elif self.in_item and "faq-answer" in values.get("class", "").split():
            self.answer_depth = 1
        elif self.answer_depth:
            self.answer_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self.in_summary and tag == "summary":
            self.in_summary = False
        elif self.answer_depth:
            self.answer_depth -= 1
        if self.in_item and tag == "details":
            question = " ".join("".join(self.question_parts).split())
            answer = " ".join("".join(self.answer_parts).split())
            if question and answer:
                self.entries.append((question, answer))
            self.in_item = False
            self.in_summary = False
            self.answer_depth = 0

    def handle_data(self, data: str) -> None:
        if self.in_summary:
            self.question_parts.append(data)
        elif self.answer_depth:
            self.answer_parts.append(data)


def extract(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return html.unescape(match.group(1).strip()) if match else ""


def organization_schema() -> dict[str, object]:
    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        "@id": f"{PUBLIC_BASE}#organization",
        "name": "株式会社AirAdmin8",
        "alternateName": "AirAdmin8 Robotics",
        "url": PUBLIC_BASE,
        "email": "airobot@robotics.air-admin8.co.jp",
        "address": {
            "@type": "PostalAddress",
            "postalCode": "100-0004",
            "addressRegion": "東京都",
            "addressLocality": "千代田区",
            "streetAddress": "大手町一丁目9番2号 大手町フィナンシャルシティ グランキューブ18階",
            "addressCountry": "JP",
        },
    }


def page_schema(config: dict[str, str], canonical: str, description: str) -> dict[str, object]:
    result: dict[str, object] = {
        "@context": "https://schema.org",
        "@type": config["type"],
        "@id": f"{canonical}#page",
        "name": config["name"],
        "url": canonical,
        "description": description,
        "inLanguage": "ja-JP",
        "isPartOf": {
            "@type": "WebSite",
            "@id": f"{PUBLIC_BASE}#website",
            "name": "AirAdmin8 Robotics",
            "url": PUBLIC_BASE,
        },
        "provider": {"@id": f"{PUBLIC_BASE}#organization"},
    }

    if config["type"] == "Product":
        result.update({
            "brand": {"@type": "Brand", "name": config.get("brand", "")},
            "category": "AI Robot",
            "image": SOCIAL_IMAGE,
            "potentialAction": {
                "@type": "AskAction",
                "target": f"{PUBLIC_BASE}contact.html?product={config['name'].replace(' ', '%20')}",
                "name": "価格・納期・導入条件を問い合わせる",
            },
        })
    elif config["type"] == "Article":
        result.update({
            "headline": config["name"],
            "author": {"@id": f"{PUBLIC_BASE}#organization"},
            "publisher": {"@id": f"{PUBLIC_BASE}#organization"},
        })

    return result


def breadcrumb_schema(text: str, canonical: str, page_name: str) -> dict[str, object]:
    parser = BreadcrumbParser()
    parser.feed(text)
    items = [
        {
            "@type": "ListItem",
            "position": index,
            "name": label,
            "item": urljoin(canonical, href),
        }
        for index, (label, href) in enumerate(parser.links, start=1)
    ]
    if not items or items[-1]["item"] != canonical:
        items.append({
            "@type": "ListItem",
            "position": len(items) + 1,
            "name": page_name,
            "item": canonical,
        })
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items,
    }


def faq_schema(text: str) -> dict[str, object]:
    parser = FaqParser()
    parser.feed(text)
    if not parser.entries:
        raise ValueError("FAQ page contains no valid data-faq-item entries")
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": answer,
                },
            }
            for question, answer in parser.entries
        ],
    }


def script_tag(element_id: str, data: dict[str, object]) -> str:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f'<script id="{element_id}" type="application/ld+json">{payload}</script>'


def process_html(text: str, relative: Path) -> str:
    relative_name = relative.as_posix()
    title = extract(TITLE_PATTERN, text) or "AirAdmin8 Robotics"
    description = extract(DESCRIPTION_PATTERN, text)
    canonical = extract(CANONICAL_PATTERN, text)
    if not canonical:
        canonical = PUBLIC_BASE if relative_name == "index.html" else f"{PUBLIC_BASE}{relative_name}"

    config = PAGE_MAP.get(relative_name, {"name": title, "type": "WebPage"})
    text = MANAGED_SCRIPT_PATTERN.sub("", text)
    scripts = [
        script_tag("organization-schema", organization_schema()),
        script_tag("page-schema", page_schema(config, canonical, description)),
        script_tag("breadcrumb-schema", breadcrumb_schema(text, canonical, config["name"])),
    ]
    if relative_name == "faq.html":
        scripts.append(script_tag("faq-schema", faq_schema(text)))

    if "</head>" not in text:
        raise ValueError(f"Missing </head>: {relative_name}")
    return text.replace("</head>", "  " + "\n  ".join(scripts) + "\n</head>", 1)


def main() -> int:
    if not OUTPUT.is_dir():
        print("SCHEMA ERROR: _site directory does not exist")
        return 1

    errors: list[str] = []
    processed = 0
    for path in sorted(OUTPUT.rglob("*.html")):
        relative = path.relative_to(OUTPUT)
        try:
            source = path.read_text(encoding="utf-8")
            path.write_text(process_html(source, relative), encoding="utf-8")
            processed += 1
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            errors.append(str(exc))

    if errors:
        for error in errors:
            print(f"SCHEMA ERROR: {error}")
        return 1

    print(f"Static structured data injected into {processed} HTML page(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
