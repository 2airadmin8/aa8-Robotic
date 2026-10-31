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


def validate_page_factory(root: Path, product: dict) -> dict:
    pid = product["id"]
    page_path(root, product.get("detailPage"), pid, generated=True)
    spec = product.get("pageFactory")
    if not isinstance(spec, dict) or spec.get("template") != "g1-v1":
        raise ContractError(f"{pid}: pageFactory.template must be g1-v1")
    if product.get("imageStatus") != "official":
        raise ContractError(f"{pid}: hero source image must be confirmed official")
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


def render(root: Path, product: dict, mode: str) -> str:
    spec = validate_page_factory(root, product)
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
    contact = "/contact.html?product=" + quote(product["name"], safe="") + "&service=university-procurement"
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
    mapping = {
        "related": related,
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
        "specifications": _item_html(spec["specifications"], "specifications"),
        "faq": _item_html(spec["faq"], "faq"),
        "images": media_images,
        "videos": videos,
        "video_section": (
            '<div class="g1-factory-videos">' + videos + '</div>'
            '<p class="g1-fine">メーカー映像と実際の納入仕様は異なる場合があります。動作保証ではありません。</p>'
            if spec["videos"] else
            '<p class="g1-fine">提供された公式製品素材には検証可能な動画がありません。'
            '最新の実演情報は <a href="' + source +
            '" target="_blank" rel="noopener noreferrer">メーカー公式ページ</a>をご確認ください。</p>'
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
    return Template(TEMPLATE.read_text(encoding="utf-8")).substitute(mapping)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("audit", "generate"))
    parser.add_argument("--id", help="Product ID from data/products.json")
    parser.add_argument("--mode", choices=("preview", "candidate"), default="preview")
    parser.add_argument("--output", type=Path, help="Output file; never overwrites")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.action == "audit":
        errors, warnings, stats = audit_catalog(root)
        print(json.dumps({"pass": not errors, "stats": stats, "errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2))
        return 1 if errors else 0
    if not args.id or not args.output:
        parser.error("generate requires --id and --output")
    try:
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
        print(f"GENERATED {args.mode}: {output} from Product Master {args.id}")
        return 0
    except (ContractError, StopIteration, FileExistsError, OSError) as exc:
        print(f"PRODUCT FACTORY STOP: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
