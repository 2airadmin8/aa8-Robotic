#!/usr/bin/env python3
"""AirAdmin8 Product Page V3.1: additive, idempotent cross-product contract.

No page design rewrite. Keep every existing original section. Adds product IDs,
normalizes maker attribution on product-specific CTAs, and adds a lightweight
Resources/Support bridge ONLY on pages explicitly opted in by Product Master.

Usage: python scripts/product_page_standard_v31.py --apply|--check
"""
from __future__ import annotations
import argparse
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, parse_qs, quote

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "data/products.json"
ORIGIN = "https://robotics.air-admin8.co.jp"
VERSION = "3.1"
TARGET = 'data-aa8-product-standard="3.1"'
BRIDGE_START = "<!-- AA8_PRODUCT_STANDARD_BRIDGE_START -->"
BRIDGE_END = "<!-- AA8_PRODUCT_STANDARD_BRIDGE_END -->"
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FAMILIES = {"humanoid", "quadruped", "mobile-manipulation"}
SUPPORT_IDS = {"university", "poc", "vla", "procurement", "setup", "maintenance"}
RESOURCE_MAKERS = {"unitree", "agibot"}
RESOURCE_TYPES = {"all", "sdk", "official", "ros", "vla", "teleoperation", "simulation", "dataset"}

class Structure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.h1 = 0
        self.contact_links = []
        self.main = 0
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "main":
            self.main += 1
        if tag == "h1":
            self.h1 += 1
        if d.get("id"):
            self.ids.add(d["id"])
        if tag == "a":
            href = html.unescape(d.get("href", ""))
            if "contact.html" in href:
                self.contact_links.append(href)

def catalog():
    root = json.loads(MASTER.read_text(encoding="utf-8"))
    ps = root.get("products", [])
    if len(ps) != 13:
        raise ValueError(f"Expected existing 13 products, got {len(ps)}; do not silently change scope")
    return ps

def check_master(product):
    p = product["id"]
    if not ID_RE.fullmatch(p): raise ValueError(f"Invalid product ID {p}")
    spec = product.get("pageStandard")
    if not isinstance(spec, dict) or spec.get("version") != VERSION:
        raise ValueError(f"{p}: missing pageStandard v{VERSION}")
    if spec.get("family") not in FAMILIES:
        raise ValueError(f"{p}: unknown family")
    if not spec.get("customerValue") or not isinstance(spec.get("customerValue"), str):
        raise ValueError(f"{p}: missing unique customerValue")
    preserved = spec.get("preserveSectionIds")
    if not isinstance(preserved, list) or len(set(preserved)) != len(preserved):
        raise ValueError(f"{p}: invalid preserveSectionIds")
    for key in ("resourcesHref", "supportHref"):
        value = spec.get(key)
        if not isinstance(value,str) or not value.startswith("/"):
            raise ValueError(f"{p}: bad {key}")
    if not re.fullmatch(r"/support.html(?:#(?:university|poc|vla|procurement|setup|maintenance))?",spec["supportHref"]):
        raise ValueError(f"{p}: invalid support target")
    r=spec["resourcesHref"]
    if not r.startswith("/resources.html") or not (r=="/resources.html" or r.startswith("/resources.html?")):
        raise ValueError(f"{p}: invalid resources target")
    if "maker=" in r and not any("maker="+m in r for m in RESOURCE_MAKERS):
        raise ValueError(f"{p}: unsupported maker filter")
    if type(spec.get("showBridge")) is not bool:
        raise ValueError(f"{p}: showBridge must be explicit")
    page=ROOT / product["detailPage"]
    if not page.is_file():
        raise ValueError(f"{p}: missing source HTML {page}")
    return page

def normalize_contact_links(source, product):
    maker = quote(product["manufacturerName"], safe="")
    def change(m):
        before, raw, end = m.group(1), m.group(2), m.group(3)
        decoded=html.unescape(raw)
        # Only annotate existing product-specific CTAs. Global header contact
        # is generic by intent. Never change theme/service, labels, or page.
        parts=urlsplit(decoded)
        if product.get("designContract"):
            # CEO-approved H2-X CTA links are frozen. Do not alter hrefs.
            return m.group(0)
        if not parts.path.endswith("/contact.html") or "product" not in parse_qs(parts.query):
            return m.group(0)
        if "maker" in parse_qs(parts.query):
            return m.group(0)
        # Do not imply SDK or University purchase unless it was already set.
        sep="&amp;" if "&amp;" in raw else "&"
        if "#" in raw:
            head,frag=raw.split("#",1)
            return before + head + sep + "maker="+maker+"#"+frag + end
        return before+raw+sep+"maker="+maker+end
    return re.sub(r"(\bhref\s*=\s*[\"'])([^\"']+)([\"'])",change,source,flags=re.I)

def bridge(product):
    spec=product["pageStandard"]
    if not spec["showBridge"]:
        return ""
    resource=html.escape(spec["resourcesHref"],quote=True)
    support=html.escape(spec["supportHref"],quote=True)
    focused=html.escape(spec["customerValue"])
    return (
        f"\n{BRIDGE_START}\n"
        '<section class="aa8-product-bridge" aria-label="この製品の技術資料・導入支援">'
        '<div class="aa8-product-bridge__inner">'
        '<h2>研究・導入の次に確認すること</h2>'
        f'<p>{focused}。機体構成・SDK対応・見積・納期・支援範囲は、用途に合わせて確認します。</p>'
        '<div class="aa8-product-bridge__links">'
        f'<a href="{resource}">技術資料・SDK情報を確認する →</a>'
        f'<a href="{support}">研究・PoC・導入支援を見る →</a>'
        '</div></div></section>\n'
        f'{BRIDGE_END}\n'
    )

def transform(source, product):
    spec=product["pageStandard"]
    def standardize_main(m):
        attrs=m.group(2)
        ids=re.findall(r'\sdata-product-id="([^"]+)"',attrs)
        if ids and any(x!=product["id"] for x in ids):
            raise ValueError(f'{product["id"]}: main contains a conflicting ProductID')
        attrs=re.sub(r'\sdata-aa8-product-standard="[^"]*"', "", attrs)
        attrs=re.sub(r'\sdata-product-family="[^"]*"', "", attrs)
        attrs=re.sub(r'\sdata-product-id="[^"]*"', "", attrs)
        return (m.group(1) + ' ' + TARGET +
                f' data-product-id="{html.escape(product["id"])}"' +
                f' data-product-family="{html.escape(spec["family"])}"' +
                attrs)
    out,n=re.subn(r"(<main\b)([^>]*>)",standardize_main,source,count=1,flags=re.I)
    if n!=1:raise ValueError(f"{product['id']}: exactly one main required")
    out=normalize_contact_links(out,product)
    if spec["showBridge"]:
        css='<link rel="stylesheet" href="/assets/css/product-standard-v31.css">'
        if css not in out:
            out,n=re.subn(r"</head\s*>",lambda m:css+"\n"+m.group(0),out,count=1,flags=re.I)
            if n!=1:raise ValueError(f"{product['id']}: missing close head")
    expected=bridge(product)
    if expected and BRIDGE_START not in out:
        out,n=re.subn(r"</main\s*>",lambda m:expected+m.group(0),out,count=1,flags=re.I)
        if n!=1:raise ValueError(f"{product['id']}: missing close main")
    if not expected and BRIDGE_START in out:
        raise ValueError(f"{product['id']}: unexpected bridge")
    return out

def validate_transformed(source,product):
    spec=product["pageStandard"]
    parser=Structure()
    parser.feed(source)
    p=product["id"]
    if parser.main!=1 or parser.h1!=1:
        raise ValueError(f"{p}: main={parser.main}, h1={parser.h1}")
    for x in spec["preserveSectionIds"]:
        if x not in parser.ids:raise ValueError(f"{p}: lost specialty section {x}")
    for url in parser.contact_links:
        parts=urlsplit(url)
        if parts.path.endswith("/contact.html") and "product" in parse_qs(parts.query) and not product.get("designContract"):
            if parse_qs(parts.query).get("maker")!=[product["manufacturerName"]]:
                raise ValueError(f"{p}: CTA maker missing or wrong {url}")
    if not parser.contact_links:
        raise ValueError(f"{p}: no CTA links")
    if spec["showBridge"]:
        if source.count(BRIDGE_START)!=1 or source.count(BRIDGE_END)!=1:
            raise ValueError(f"{p}: bridge count")
        for href in (spec["resourcesHref"],spec["supportHref"]):
            if html.escape(href,quote=True) not in source:
                raise ValueError(f"{p}: bridge link missing")
    op=re.search(r"<main\b([^>]*)>",source,re.I)
    assert op is not None
    if len(re.findall(r"\bdata-product-id=",op.group(1)))!=1:
        raise ValueError(f"{p}: duplicate ProductID attributes")
    if spec["showBridge"] and source.count('product-standard-v31.css')!=1:
        raise ValueError(f"{p}: missing/duplicate bridge stylesheet")
    if source.count(TARGET)!=1:
        raise ValueError(f"{p}: standard marker missing/duplicate")

def main():
    parser=argparse.ArgumentParser()
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--apply",action="store_true")
    group.add_argument("--check",action="store_true")
    args=parser.parse_args()
    products=catalog()
    all_changes=[]
    for product in products:
        path=check_master(product)
        original=path.read_text(encoding="utf-8")
        expected=transform(original,product)
        validate_transformed(expected,product)
        if args.apply:
            if expected!=original:
                path.write_text(expected,encoding="utf-8")
                all_changes.append(product["id"])
        else:
            if expected!=original:
                raise ValueError(f"{product['id']}: product standard out of sync")
        # Idempotency gate
        if transform(expected,product)!=expected:
            raise ValueError(f"{product['id']}: non-idempotent transform")
    print(json.dumps({"standard":VERSION,"products":len(products),"changed":all_changes,
                      "gatewayModules":sum(bool(p["pageStandard"]["showBridge"]) for p in products),
                      "status":"PASS"},ensure_ascii=False))
if __name__=="__main__":
    main()
