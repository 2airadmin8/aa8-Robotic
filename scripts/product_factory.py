#!/usr/bin/env python3
"""Robotics Product Page Factory V1.

Existing data/products.json remains the ONLY product catalog SSOT.
Legacy pages stay as-is; opt-in pageFactory records can render a G1-family draft.
Never publishes, calls external services, or modifies a protected branch.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import date
from pathlib import Path, PurePosixPath
from string import Template
from urllib.parse import quote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ORIGIN = "https://robotics.air-admin8.co.jp"
TEMPLATE = Path(__file__).parent / "templates" / "g1_factory_v1.html"
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".svg"}
VIDEO_EXT = {".mp4", ".webm"}
CANONICAL_RE = re.compile(r'<link\s+rel=["\x27]canonical["\x27]\s+href=["\x27]([^"\x27]+)', re.I)
PLACEHOLDER_STATUSES = {"placeholder", "unverified"}


class ContractError(ValueError):
    pass


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def required(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label}: nonempty string required")
    return value.strip()


def local_asset(root: Path, value: str, label: str, extensions: set[str]) -> str:
    raw = required(value, label)
    parts = PurePosixPath(raw)
    if (
        "\\" in raw or "%" in raw or "#" in raw or "?" in raw
        or parts.is_absolute() or parts.parts[:1] != ("assets",)
        or ".." in parts.parts or not parts.suffix.lower() in extensions
    ):
        raise ContractError(f"{label}: unsafe local asset path {raw!r}")
    target = (root / Path(*parts.parts)).resolve()
    if not target.is_relative_to(root.resolve()) or not target.is_file() or target.stat().st_size == 0:
        raise ContractError(f"{label}: missing/empty asset {raw}")
    return "/" + raw


def official_url(value: object, label: str) -> str:
    raw = required(value, label)
    u = urlsplit(raw)
    if u.scheme != "https" or not u.hostname or u.username or u.password or "\\" in raw:
        raise ContractError(f"{label}: HTTPS official source URL required")
    if u.hostname.endswith(".invalid") or u.hostname in {"localhost", "127.0.0.1"}:
        raise ContractError(f"{label}: unsupported source hostname")
    return raw


def page_path(root: Path, value: object, product_id: str, *, generated: bool = False) -> Path:
    path = required(value, "detailPage")
    if not re.fullmatch(r"products/[a-z0-9]+(?:-[a-z0-9]+)*\.html", path):
        raise ContractError(f"{product_id}: unsafe detailPage path {path!r}")
    expected = f"products/{product_id}.html"
    if generated and path != expected:
        raise ContractError(f"{product_id}: generated detailPage must equal {expected}")
    return root / path


def catalog(root: Path) -> list[dict]:
    content = json.loads((root / "data" / "products.json").read_text(encoding="utf-8"))
    if content.get("schemaVersion") != 5 or not isinstance(content.get("products"), list):
        raise ContractError("data/products.json: expected schemaVersion 5 and products list")
    return content["products"]


def _strings(value: object, label: str, min_count: int) -> list:
    if not isinstance(value, list) or len(value) < min_count:
        raise ContractError(f"{label}: requires >= {min_count} items")
    return value


def validate_page_factory(root: Path, product: dict, *, allow_original_preview: bool = False) -> dict:
    pid = product["id"]
    page_path(root, product.get("detailPage"), pid, generated=True)
    spec = product.get("pageFactory")
    if not isinstance(spec, dict) or spec.get("template") != "g1-v1":
        raise ContractError(f"{pid}: pageFactory.template must be g1-v1")
    if product.get("imageStatus") != "official":
        # An owner-confirmed series-generic derived hero may be previewed, never released,
        # and must not be mistaken for a manufacturer-approved SKU photograph.
        allowed = (
            allow_original_preview
            and product.get("imageStatus") == "original"
            and product.get("imageApproval") == "user_confirmed_x2_series_generic"
            and spec.get("releaseReady") is False
        )
        if not allowed:
            raise ContractError(f"{pid}: hero source image must be confirmed official for release")
    local_asset(root, product.get("image", ""), f"{pid}.image", IMAGE_EXT)
    official_url(spec.get("officialSource"), f"{pid}.officialSource")
    for field in ("title", "metaDescription", "heroLead"):
        required(spec.get(field), f"{pid}.{field}")
    if len(spec["metaDescription"]) > 300:
        raise ContractError(f"{pid}: metaDescription is unusually long")
    for field, minimum in (("facts", 3), ("applications", 2), ("specifications", 3), ("faq", 3)):
        _strings(spec.get(field), f"{pid}.{field}", minimum)
    images = _strings(spec.get("images"), f"{pid}.images", 3)
    for i, item in enumerate(images):
        if not isinstance(item, dict):
            raise ContractError(f"{pid}.images[{i}]: expected object")
        local_asset(root, item.get("src", ""), f"{pid}.images[{i}].src", IMAGE_EXT)
        required(item.get("alt"), f"{pid}.images[{i}].alt")
        official_url(item.get("sourceUrl"), f"{pid}.images[{i}].sourceUrl")
    if "inheritSourcePage" in spec and type(spec["inheritSourcePage"]) is not bool:
        raise ContractError(f"{pid}: inheritSourcePage must be boolean")
    vids = _strings(spec.get("videos"), f"{pid}.videos", 0)
    if not vids and spec.get("videoAvailability") != "not_provided_by_manufacturer":
        raise ContractError(f"{pid}: no verified videos; mark manufacturer media absence explicitly")
    for i, v in enumerate(vids):
        if not isinstance(v, dict):
            raise ContractError(f"{pid}.videos[{i}]: expected object")
        local_asset(root, v.get("src", ""), f"{pid}.videos[{i}].src", VIDEO_EXT)
        local_asset(root, v.get("poster", ""), f"{pid}.videos[{i}].poster", IMAGE_EXT)
        required(v.get("label"), f"{pid}.videos[{i}].label")
        official_url(v.get("sourceUrl"), f"{pid}.videos[{i}].sourceUrl")
    choices = _strings(spec.get("ctaImageIndexes"), f"{pid}.ctaImageIndexes", 3)
    if len(choices) != 3 or len(set(choices)) != 3 or not all(type(n) is int and 0 <= n < len(images) for n in choices):
        raise ContractError(f"{pid}: exactly three valid ctaImageIndexes required")
    for field in ("facts", "applications", "specifications", "faq"):
        for i, fact in enumerate(spec[field]):
            if not isinstance(fact, dict):
                raise ContractError(f"{pid}.{field}[{i}]: expected object")
            keys = ("label", "value") if field in {"facts", "specifications"} else (
                ("title", "description") if field == "applications" else ("question", "answer")
            )
            for key in keys:
                required(fact.get(key), f"{pid}.{field}[{i}].{key}")
            if field != "faq":
                official_url(fact.get("sourceUrl"), f"{pid}.{field}[{i}].sourceUrl")
    v3 = spec.get("v3")
    if v3 is not None:
        if not isinstance(v3, dict):
            raise ContractError(f"{pid}.v3: expected object")
        for field, minimum in (("models", 3), ("sdk", 3), ("solutions", 3), ("process", 5)):
            if field == "models" and field not in v3:
                continue
            items = _strings(v3.get(field), f"{pid}.v3.{field}", minimum)
            for i, item in enumerate(items):
                if not isinstance(item, dict):
                    raise ContractError(f"{pid}.v3.{field}[{i}]: expected object")
                required(item.get("title"), f"{pid}.v3.{field}[{i}].title")
                required(item.get("description"), f"{pid}.v3.{field}[{i}].description")
                if field == "models":
                    href = required(item.get("href"), f"{pid}.v3.models[{i}].href")
                    if not (href == "#specifications" or re.fullmatch(r"/products/[a-z0-9-]+\.html", href)):
                        raise ContractError(f"{pid}.v3.models[{i}]: unsafe href")
                if field == "solutions" and item.get("supportSectionId") is not None:
                    if item.get("supportSectionId") not in {"university", "poc", "vla", "procurement", "setup", "maintenance"}:
                        raise ContractError(f"{pid}.v3.solutions[{i}]: unsafe supportSectionId")
    related = _strings(spec.get("relatedProductIds"), f"{pid}.relatedProductIds", 3)
    related_ids = {p.get("id") for p in catalog(root)}
    if (len(related) != len(set(related)) or len(related)>6 or pid in related
        or any(not isinstance(x,str) or x not in related_ids for x in related)):
        raise ContractError(f"{pid}: invalid relatedProductIds or self-reference")
    if type(spec.get("releaseReady")) is not bool:
        raise ContractError(f"{pid}: explicit releaseReady boolean required")
    try:
        date.fromisoformat(required(product.get("verifiedAt"), f"{pid}.verifiedAt"))
    except ValueError as exc:
        raise ContractError(f"{pid}: invalid verifiedAt date") from exc
    return spec


def validate_approved_contract(root: Path, product: dict) -> None:
    """Freeze the original CEO-approved H2-X assets and CTA structure."""
    contract = product["designContract"]
    if contract.get("template") != "g1-approved-v1":
        raise ContractError(f"{product['id']}: unknown designContract")
    markup = page_path(root, product["detailPage"], product["id"]).read_text(encoding="utf-8")
    hero = local_asset(root, product.get("image", ""), "approved hero", IMAGE_EXT)
    if f'src="{hero}"' not in markup:
        raise ContractError(f"{product['id']}: master hero not present in HTML")
    background = local_asset(root, contract.get("ctaBackground", ""), "CTA background", IMAGE_EXT)
    css_files = [root / path for path in ("assets/css/g1-product.css", "assets/css/h2x-product.css")]
    if not any(background.rsplit("/", 1)[-1] in p.read_text(encoding="utf-8") for p in css_files):
        raise ContractError(f"{product['id']}: G1 CTA background not declared in CSS")
    if 'class="g1-section h2-next g1-final-cta h2x-final-cta"' not in markup:
        raise ContractError(f"{product['id']}: approved illustrated CTA structure missing")
    pos = markup.index('class="g1-section h2-next g1-final-cta h2x-final-cta"')
    cta = markup[pos:].split("</section>", 1)[0]
    images = _strings(contract.get("ctaImages"), "approved ctaImages", 3)
    videos = _strings(contract.get("videos"), "approved videos", 3)
    expected_links = _strings(contract.get("ctaLinks"), "approved ctaLinks", 3)
    for i, asset in enumerate(images):
        path = local_asset(root, asset, f"approved CTA[{i}]", IMAGE_EXT)
        if f'src="{path}"' not in cta:
            raise ContractError(f"{product['id']}: approved CTA image absent: {asset}")
    for i, asset in enumerate(videos):
        path = local_asset(root, asset, f"approved video[{i}]", VIDEO_EXT)
        if f'src="{path}"' not in markup:
            raise ContractError(f"{product['id']}: video absent: {asset}")
    if cta.count('class="g1-cta-card"') != 3:
        raise ContractError(f"{product['id']}: must retain 3 illustrated CTA cards")
    for link in expected_links:
        if f'href="{esc(link)}"' not in cta:
            raise ContractError(f"{product['id']}: approved CTA link missing: {link}")


def audit_catalog(root: Path) -> tuple[list[str], list[str], dict]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        products = catalog(root)
    except (OSError, ValueError, TypeError) as exc:
        return [str(exc)], [], {"products": 0}
    seen: set[str] = set()
    pages: set[str] = set()
    factory_count = 0
    for entry in products:
        try:
            pid = required(entry.get("id"), "product.id")
            if not SLUG.fullmatch(pid) or pid in seen:
                raise ContractError(f"invalid/duplicate product id {pid!r}")
            seen.add(pid)
            target = page_path(root, entry.get("detailPage"), pid)
            if entry["detailPage"] in pages:
                raise ContractError(f"{pid}: duplicate detailPage")
            pages.add(entry["detailPage"])
            if not target.is_file():
                raise ContractError(f"{pid}: detailPage missing")
            required(entry.get("name"), f"{pid}.name")
            required(entry.get("manufacturerName"), f"{pid}.manufacturerName")
            required(entry.get("summary"), f"{pid}.summary")
            if entry.get("visibility") not in ("public", "hidden"):
                raise ContractError(f"{pid}: invalid visibility")
            local_asset(root, entry.get("image", ""), f"{pid}.image", IMAGE_EXT)
            text = target.read_text(encoding="utf-8")
            expected = f'{PUBLIC_ORIGIN}/{entry["detailPage"]}'
            m = CANONICAL_RE.search(text)
            if not m:
                raise ContractError(f"{pid}: missing canonical")
            if html.unescape(m.group(1)) != expected:
                warnings.append(f"{pid}: source canonical differs; build rewrites it")
            if not re.search(r"<h1\b", text, re.I) or not re.search(r"<title\b", text, re.I):
                raise ContractError(f"{pid}: missing title/H1")
            if entry.get("imageStatus") in PLACEHOLDER_STATUSES:
                warnings.append(f"{pid}: placeholder image; no official-photo release claim")
            if "designContract" in entry:
                validate_approved_contract(root, entry)
            if "pageFactory" in entry:
                spec = validate_page_factory(root, entry)
                if not spec["releaseReady"]:
                    raise ContractError(f"{pid}: committed generated page is not releaseReady")
                if 'data-product-factory="g1-v1"' not in text:
                    raise ContractError(f"{pid}: generated source template marker missing")
                if re.search(r'<meta\s+name=["\x27]robots["\x27][^>]*noindex', text, re.I):
                    raise ContractError(f"{pid}: noindex preview cannot enter public products/")
                factory_count += 1
        except (ContractError, KeyError, OSError, ValueError, TypeError) as exc:
            errors.append(str(exc))
    return errors, warnings, {"products": len(products), "ids": len(seen), "factoryEnabled": factory_count}


def _item_html(items: list[dict], kind: str) -> str:
    if kind == "facts":
        return "\n".join(f'<article><strong>{esc(x["value"])}</strong><p>{esc(x["label"])}</p><small><a href="{esc(x["sourceUrl"])}" target="_blank" rel="noopener noreferrer">仕様出典 ↗</a></small></article>' for x in items)
    if kind == "applications":
        return "\n".join(f'<article><h3>{esc(x["title"])}</h3><p>{esc(x["description"])}</p><small><a href="{esc(x["sourceUrl"])}" target="_blank" rel="noopener noreferrer">出典 ↗</a></small></article>' for x in items)
    if kind == "specifications":
        return "\n".join(f'<tr><th scope="row">{esc(x["label"])}</th><td>{esc(x["value"])} <small><a href="{esc(x["sourceUrl"])}" target="_blank" rel="noopener noreferrer">出典 ↗</a></small></td></tr>' for x in items)
    if kind == "faq":
        return "\n".join(f'<details><summary>{esc(x["question"])}</summary><p>{esc(x["answer"])}</p></details>' for x in items)
    raise AssertionError(kind)



def render_variant_compare_specs(product: dict, spec: dict) -> str:
    """X2 series: readable native comparison from the same 36 manufacturer facts."""
    rows = spec["specifications"]
    if product["id"] != "agibot-x2-series":
        return _item_html(rows, "specifications")
    if len(rows) != 36:
        raise ContractError("X2 JP current source must have exactly 36 compared specs")
    categories = set()
    group = None
    html_rows = [
        '<tr class="x2-compare-head"><th scope="col">比較項目</th>'
        '<th scope="col">X2</th><th scope="col">X2 Ultra</th></tr>'
    ]
    for item in rows:
        category = required(item.get("category"), "X2 comparison category")
        label = required(item.get("parameter"), "X2 comparison parameter")
        models = item.get("models")
        if not isinstance(models, dict) or set(models) != {"X2", "X2 Ultra"}:
            raise ContractError("X2 comparison must preserve two official model values")
        if category != group:
            if category in categories:
                raise ContractError("X2 categories must stay contiguous")
            categories.add(category)
            group = category
            html_rows.append(
                '<tr class="x2-category-row"><th scope="colgroup" colspan="3">'
                + esc(category) + '</th></tr>'
            )
        x2 = required(models["X2"], "X2 model spec")
        ultra = required(models["X2 Ultra"], "X2 Ultra model spec")
        html_rows.append(
            '<tr class="x2-spec-row" data-spec-row="true">'
            '<th scope="row">' + esc(label) +
            ' <small><a href="' + esc(item["sourceUrl"]) +
            '" target="_blank" rel="noopener noreferrer">出典 ↗</a></small></th>'
            '<td data-model="X2">' + esc(x2) + '</td>'
            '<td data-model="X2 Ultra">' + esc(ultra) + '</td></tr>'
        )
    if len(categories) != 9:
        raise ContractError("X2 JP comparison must preserve 9 categories")
    return "\n".join(html_rows)


def render_v3_sections(spec: dict, product: dict) -> dict[str, str]:
    """Optional, validated V3 content from Product Master, without changing legacy pages."""
    empty = {"v3_navigation": "", "v3_model_section": "", "v3_sdk_section": "",
             "v3_solutions_section": "", "v3_process_section": ""}
    v3 = spec.get("v3")
    if not v3:
        return empty

    def section(anchor: str, kicker: str, title: str, inner: str, foot: str) -> str:
        return (f'<section class="g1-section g1-factory-section g1-factory-v3" id="{anchor}"><div class="g1-shell">\n'
                f'<p class="g1-kicker">{kicker}</p><h2>{title}</h2>\n'
                + inner + '\n<p class="g1-fine">' + foot + '</p>\n</div></section>')

    models = v3.get("models", [])
    model_rows = '\n'.join(
        '<tr><th scope="row"><a href="' + esc(item["href"]) + '">' + esc(item["title"]) +
        '</a></th><td>' + esc(item["description"]) + '</td></tr>' for item in models
    )
    model_table = ('<table class="g1-factory-spec-table"><caption>関連モデルの選定目安</caption>'
                   '<tbody>' + model_rows + '</tbody></table>') if models else ""
    model_section = section("model-selection", "MODEL SELECTION",
        esc(product["name"]) + "と関連モデルの選び方", model_table,
        "用途・本体構成・開発権限・ハンド・国内見積を比較。別型番の仕様・SDK条件を混同せず個別に確認してください。") if models else ""

    def cards(field: str) -> str:
        rendered = []
        for item in v3[field]:
            support_link = ""
            support_id = item.get("supportSectionId") if field == "solutions" else None
            if support_id in {"university", "poc", "vla", "procurement", "setup", "maintenance"}:
                support_link = '<a class="g1-factory-support-link" href="/support.html#' + support_id + '">導入支援の詳細を見る →</a>'
            rendered.append('<article><h3>' + esc(item["title"]) + '</h3><p>' +
                            esc(item["description"]) + '</p>' + support_link + '</article>')
        return '<div class="g1-factory-applications">' + '\n'.join(rendered) + '</div>'

    source = esc(official_url(spec["officialSource"], "officialSource"))
    resource_href = str(v3.get("resourceSearchUrl") or "/resources.html")
    if not resource_href.startswith("/resources.html"):
        raise ContractError(f"{product['id']}.v3.resourceSearchUrl: unsafe local path")
    developer_url = v3.get("developerDocsUrl")
    resource_label = esc(str(v3.get("resourceLinkLabel") or "SDK・開発資料一覧"))
    developer_label = esc(str(v3.get("developerDocsLabel") or "メーカー公式開発資料"))
    developer_caution = esc(str(v3.get("developerDocsCaution") or
                               "対応SKU・OS・SDK配布条件は購入前にメーカーへ確認してください。"))
    sdk_download_note = esc(str(v3.get("sdkDownloadNote") or ""))
    developer_link = (
        '<a href="' + esc(official_url(developer_url, "developerDocsUrl")) +
        '" target="_blank" rel="noopener noreferrer">' + developer_label + '</a>。'
        if developer_url else
        '<a href="' + source + '" target="_blank" rel="noopener noreferrer">メーカー公式情報</a>。'
    )
    sdk_foot = (
        '技術資料：<a href="' + esc(resource_href) + '">' + resource_label + '</a>／'
        + developer_link + developer_caution + sdk_download_note
    )
    return {
        "v3_navigation": "",
        "v3_model_section": model_section,
        "v3_sdk_section": section("development", "SDK / DEVELOPMENT",
            "SDK・開発環境", cards("sdk"), sdk_foot),
        "v3_solutions_section": section("solutions", "SOLUTION / CONFIGURATION",
            "研究目的別の推奨構成例", cards("solutions"),
            '研究目的別の参考構成です。周辺機器・SDK・サービスの標準付属や動作保証を意味しません。'
            + '<a class="g1-factory-support-link" href="/support.html">導入支援メニュー・責任分界を見る →</a>'),
        "v3_process_section": section("introduction", "INTRODUCTION / SUPPORT",
            "導入・研究開始までの流れ", cards("process"), "AirAdmin8・メーカー・お客様の担当範囲、保証と有償支援は正式見積・契約時に明確化します。"),
    }


def render(root: Path, product: dict, mode: str) -> str:
    spec = validate_page_factory(root, product, allow_original_preview=(mode == "preview"))
    if mode == "candidate" and not spec["releaseReady"]:
        raise ContractError("release candidate blocked: pageFactory.releaseReady must be true")
    slug = product["id"]
    name = esc(product["name"])
    source = esc(official_url(spec["officialSource"], "officialSource"))
    media_images = "\n".join(
        f'<figure><img loading="lazy" src="{esc(local_asset(root,x["src"],"image",IMAGE_EXT))}" alt="{esc(x["alt"])}"><figcaption>{esc(x["alt"])}</figcaption></figure>'
        for x in spec["images"]
    )
    videos = "\n".join(
        f'<figure><video controls preload="metadata" playsinline poster="{esc(local_asset(root,v["poster"],"poster",IMAGE_EXT))}" aria-label="{esc(v["label"])}">'
        f'<source src="{esc(local_asset(root,v["src"],"video",VIDEO_EXT))}" type="video/mp4"></video>'
        f'<figcaption>{esc(v["label"])}</figcaption></figure>' for v in spec["videos"]
    )
    contact_service = spec.get("contactService", "university-procurement")
    contact = ("/contact.html?product=" + quote(product["name"], safe="")
               + ("&maker=" + quote(product["manufacturerName"], safe="") if spec.get("v3") else "")
               + ("&service=" + quote(contact_service, safe="") if contact_service else "")
               + ("&maker=" + quote(product["manufacturerName"], safe="")
                  if product.get("pageStandard") and not spec.get("v3") else ""))
    if spec.get("inheritSourcePage"):
        contact += "&source_page=" + quote(
            f'{PUBLIC_ORIGIN}/{product["detailPage"]}', safe=""
        )
    cta_img = [
        esc(local_asset(root, spec["images"][i]["src"], "ctaImage", IMAGE_EXT))
        for i in spec["ctaImageIndexes"]
    ]
    if spec["videos"]:
        primary_action = ("01 / SEE THE MOTION", f"/{spec['videos'][0]['src']}",
                          "公式デモを見る", "メーカーの実演映像を確認します。")
    else:
        primary_action = ("01 / OFFICIAL SOURCE", spec["officialSource"],
                          "メーカー公式情報を見る", "動画がないため公式仕様へ案内します。")
    card_data = [
        primary_action,
        ("02 / COMPARE THE HARDWARE", "#specifications", "仕様を比較する", "メーカー公開仕様と導入条件を整理します。"),
        ("03 / PLAN YOUR NEXT STEP", contact, "研究・導入を相談する", "用途、SDK、見積、納期を個別に確認します。"),
    ]
    cards = "\n".join(
        f'<a class="g1-cta-card" href="{esc(url)}" data-factory-cta="{i+1}">'
        f'<span class="g1-cta-photo"><img loading="lazy" src="{cta_img[i]}" alt="{esc(title)}"></span>'
        f'<span class="g1-cta-number">{esc(kicker)}</span><strong>{esc(title)}</strong>'
        f'<small>{esc(description)}</small><em>詳細を見る →</em></a>'
        for i, (kicker, url, title, description) in enumerate(card_data)
    )
    by_id = {p["id"]: p for p in catalog(root)}
    related = "\n".join(
        f'<a class="g1-factory-related-card" href="/{esc(by_id[rid]["detailPage"])}">'
        f'<span class="g1-factory-related-photo"><img loading="lazy" decoding="async" '
        f'src="{esc(local_asset(root,by_id[rid]["image"],"related",IMAGE_EXT))}" '
        f'alt="{esc(by_id[rid]["imageAlt"])}"></span>'
        f'<strong>{esc(by_id[rid]["name"])}</strong><small>{esc(by_id[rid]["summary"])}</small>'
        f'<em>製品詳細へ →</em></a>' for rid in spec["relatedProductIds"]
    )
    hero_actions = (
        '<a class="g1-button primary" href="' + esc(contact) +
        '" data-factory-cta="hero">研究・導入を相談する ↗</a>\n'
        '<a class="g1-button secondary" href="#media">' +
        esc("公式写真・動画を見る" if spec["videos"] else "公式写真を見る") + ' ↓</a>'
        if spec.get("v3") else
        '<a class="g1-button primary" href="#media">' +
        esc("公式写真・動画を見る" if spec["videos"] else "公式写真を見る") + ' ↓</a>\n'
        '<a class="g1-button secondary" href="' + esc(contact) +
        '" data-factory-cta="hero">研究・導入を相談する ↗</a>'
    )
    anchor_navigation = (
        "<a href=\"#capabilities\">特長</a><a href=\"#applications\">用途</a><a href=\"#media\">写真</a>"
        + ("<a href=\"#model-selection\">モデル</a>" if spec.get("v3", {}).get("models") else "")
        + "<a href=\"#specifications\">仕様</a><a href=\"#development\">SDK</a><a href=\"#solutions\">研究構成</a><a href=\"#introduction\">導入</a><a href=\"#contact-product\">相談</a>"
        if spec.get("v3") else
        ('<a href="#capabilities">製品特徴</a><a href="#applications">用途</a>\n'
         '<a href="#media">' + esc("写真・動画" if spec["videos"] else "公式写真") + '</a>'
         '<a href="#specifications">仕様</a>\n'
         '<a href="#faq">FAQ</a><a href="#related">関連製品</a><a href="#contact-product">導入相談</a>')
    )
    mapping = {
        "anchor_navigation": anchor_navigation,
        "hero_actions": hero_actions,
        "related": related,
        "media_button_label": "公式写真・動画を見る" if spec["videos"] else "公式写真を見る",
        "media_nav_label": "写真・動画" if spec["videos"] else "公式写真",
        "media_title": (
            "製品画像・構造" if spec.get("v3") else
            ("公式写真・動画" if spec["videos"] else "公式写真")
        ),
        "spec_heading": "製品スペック" if spec.get("v3") else "メーカー公開仕様",
        "spec_origin": (
            '<details class="g1-factory-source"><summary>仕様の出典・確認情報</summary>'
            '<p>' + esc(product["manufacturerName"]) + '公式の公表値を参照。確認日：' + esc(product["verifiedAt"]) +
            '。掲載値は購入するSKU・オプション構成で異なる場合があります。 '
            '<a href="' + source + '" target="_blank" rel="noopener noreferrer">'
            'メーカー公式仕様を見る ↗</a></p></details>'
            if spec.get("v3") else ""
        ),
        "cta_lead": ("動きを見て、仕様を比べ、研究・PoCの導入条件を整理します。"
                     if spec["videos"] else
                     "製品写真と公式仕様を確認し、研究・PoCの導入条件を整理します。"),
        "media_attribution": "画像・動画出典" if spec["videos"] else "画像出典",
        "title": esc(spec["title"]),
        "description": esc(spec["metaDescription"]),
        "canonical": esc(f'{PUBLIC_ORIGIN}/{product["detailPage"]}'),
        "og_image": esc(PUBLIC_ORIGIN + local_asset(root, product["image"], "hero", IMAGE_EXT)),
        "name": name,
        "manufacturer": esc(product["manufacturerName"]),
        "hero_lead": esc(spec["heroLead"]),
        "summary": esc(product["summary"]),
        "hero_image": esc(local_asset(root, product["image"], "hero", IMAGE_EXT)),
        "hero_alt": esc(product["imageAlt"]),
        "contact": esc(contact),
        "facts": _item_html(spec["facts"], "facts"),
        "applications": _item_html(spec["applications"], "applications"),
        "specifications": render_variant_compare_specs(product, spec),
        "faq": _item_html(spec["faq"], "faq"),
        "images": media_images,
        "videos": videos,
        "video_section": (
            '<div class="g1-factory-videos">' + videos + '</div>'
            '<p class="g1-fine">メーカー映像と実際の納入仕様は異なる場合があります。動作保証ではありません。</p>'
            if spec["videos"] else
            ('<p class="g1-fine g1-v3-video-note">提供された公式製品素材には検証可能な動画がありません。'
             '最新の実演情報は <a href="' + source +
             '" target="_blank" rel="noopener noreferrer">メーカー公式ページ</a>をご確認ください。</p>')
        ),
        "cards": cards,
        "official_source": source,
        "status": esc(product.get("statusLabel", "条件確認中")),
        "price_label": esc(product.get("priceLabel", "見積要確認")),
        "lead_time": esc(product.get("leadTimeLabel", "納期要確認")),
        "robots": '<meta name="robots" content="noindex,nofollow">' if mode == "preview" else "",
        "product_id": esc(slug),
        "verified_at": esc(product["verifiedAt"]),
    }
    from product_page_standard_v31 import bridge as render_standard_bridge
    standard = product.get("pageStandard", {})
    mapping["product_family"] = esc(standard.get("family", "humanoid"))
    mapping["standard_bridge"] = render_standard_bridge(product) if standard else ""
    mapping["standard_css"] = ('<link rel="stylesheet" href="/assets/css/product-standard-v31.css">'
        if standard.get("showBridge") else "")
    mapping.update(render_v3_sections(spec, product))
    mapping["v3_styles"] = (
        '<link rel="stylesheet" href="/assets/css/g1-factory-v3.css">'
        if spec.get("v3") else ""
    )
    # One exact shared header SSOT; do not invent a second logo/menu system.
    header_file = root / "includes/site-header.html"
    if not header_file.is_file():
        raise ContractError("Official shared header template is missing")
    mapping["shared_header"] = header_file.read_text(encoding="utf-8")
    # The normal site.js initializes GA4, so preview uses a strictly local
    # nav toggle without analytics, network calls or production writers.
    mapping["factory_nav_script"] = (
        '<script>(function(){var b=document.querySelector(".site-header .menu"),'
        'n=document.querySelector(".site-header .nav");'
        'if(!b||!n)return;'
        'function close(){n.classList.remove("open");b.setAttribute("aria-expanded","false")}'
        'b.addEventListener("click",function(){var o=n.classList.toggle("open");'
        'b.setAttribute("aria-expanded",String(o))});'
        'n.querySelectorAll("a").forEach(function(x){x.addEventListener("click",close)})'
        '})();</script>'
        if mode == "preview" else ""
    )
    page = Template(TEMPLATE.read_text(encoding="utf-8")).substitute(mapping)
    if mode == "preview":
        # CI/local preview is not a public page: never emit production
        # analytics page_view from site.js (GA4) or other site bootstrap.
        page = page.replace('<script src="/assets/js/site.js" defer></script>', '')
    return page


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("audit", "generate"))
    parser.add_argument("--id", help="Product ID from data/products.json")
    parser.add_argument("--draft-product", type=Path,
                        help="isolated preview-only single product JSON under tests/fixtures; never updates Product Master")
    parser.add_argument("--mode", choices=("preview", "candidate"), default="preview")
    parser.add_argument("--output", type=Path, help="Output file; never overwrites")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.action == "audit":
        errors, warnings, stats = audit_catalog(root)
        print(json.dumps({"pass": not errors, "stats": stats, "errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2))
        return 1 if errors else 0
    if not args.output or (not args.id and not args.draft_product):
        parser.error("generate requires --output and either --id or --draft-product")
    if args.draft_product and (args.id or args.mode != "preview"):
        parser.error("--draft-product is preview-only and cannot be combined with --id")
    try:
        if args.draft_product:
            draft_path = args.draft_product.resolve()
            if not draft_path.is_relative_to((root / "tests" / "fixtures").resolve()):
                raise ContractError("draft-product must reside under tests/fixtures")
            product = json.loads(draft_path.read_text(encoding="utf-8"))
            if product.get("id") in {p["id"] for p in catalog(root)}:
                raise ContractError("draft-product ID conflicts with existing Product Master")
            if product.get("pageFactory", {}).get("releaseReady") is not False:
                raise ContractError("draft-product releaseReady must be false")
        else:
            product = next(p for p in catalog(root) if p["id"] == args.id)
        result = render(root, product, args.mode)
        output = args.output.resolve()
        if output.suffix.lower() != ".html":
            raise ContractError("output must end in .html")
        if args.mode == "candidate" and output != page_path(root, product["detailPage"], product["id"]).resolve():
            raise ContractError("candidate must target its declared product detailPage")
        if args.mode == "preview" and output.is_relative_to(root / "products"):
            raise ContractError("preview cannot be written into public products/")
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8", newline="\n") as f:
            f.write(result)
        print(f"GENERATED {args.mode}: {output} from "+("isolated pilot fixture" if args.draft_product else f"Product Master {args.id}"))
        return 0
    except (ContractError, StopIteration, FileExistsError, OSError) as exc:
        print(f"PRODUCT FACTORY STOP: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
