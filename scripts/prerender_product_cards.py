#!/usr/bin/env python3
"""Pre-render public product cards into built HTML.

Use the public product catalog to render cards directly into the initial HTML.
The main site build uses the renderer for the homepage; the standalone command
can also pre-render the product directory.
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"
PRODUCTS_PATH = ROOT / "data" / "products.json"
ROOT_PATTERN = re.compile(
    r'(<div\b(?=[^>]*\bdata-product-list\b)(?P<attrs>[^>]*)>)(?P<body>.*?)(</div>)',
    re.IGNORECASE | re.DOTALL,
)
LIMIT_PATTERN = re.compile(r'\bdata-limit=["\'](?P<limit>\d+)["\']', re.IGNORECASE)
EXCLUDE_PATTERN = re.compile(r'\bdata-exclude-products=["\'](?P<ids>[^"\']+)["\']', re.IGNORECASE)


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def card(product: dict[str, object], prefix: str, *, homepage: bool = False) -> str:
    groups = " ".join(product.get("filterGroups") or [product.get("categoryId", "")])
    feature_labels = list(product.get("featureLabels") or [])[:4]
    use_labels = list(product.get("useLabels") or [])[:4]
    placeholder = (
        '<span class="image-note">参考イメージ</span>'
        if product.get("imageStatus") == "placeholder"
        else ""
    )
    note = (
        f'<p class="product-note">{esc(product.get("note"))}</p>'
        if product.get("note")
        else ""
    )
    features = "".join(f"<span>{esc(label)}</span>" for label in feature_labels)
    detail_page = f"{prefix}{product.get('detailPage', '')}"
    image = f"{prefix}{product.get('image', '')}"
    contact = f"{prefix}contact.html?product={esc(product.get('name'))}"
    maker = esc(product.get("manufacturerName"))
    badge = f'<span class="home-product-maker">{maker}</span>' if homepage else ""
    detail_text = "製品詳細を見る →" if homepage else "詳細を見る →"

    return f'''<article id="{esc(product.get('id'))}" class="product-card research-product-card" data-product-groups="{esc(groups)}" data-product-maker="{esc(product.get('manufacturerId'))}">
  <a class="product-visual" href="{esc(detail_page)}" tabindex="-1" aria-label="{esc(product.get('name'))}の詳細を見る">
    <img src="{esc(image)}" alt="{esc(product.get('imageAlt'))}" loading="lazy">
    {placeholder}{badge}
  </a>
  <div class="product-body">
    <div class="product-topline">
      <p class="product-maker">{maker}</p>
      <span class="status status-{esc(product.get('status'))}">{esc(product.get('statusLabel'))}</span>
    </div>
    <h3><a href="{esc(detail_page)}" tabindex="-1">{esc(product.get('name'))}</a></h3>
    <p class="product-summary">{esc(product.get('summary'))}</p>
    <div class="feature-list">{features}</div>
    <div class="meta product-condition-meta">
      <span class="tag">{esc(product.get('priceLabel'))}</span>
      <span class="tag">{esc(product.get('leadTimeLabel'))}</span>
    </div>
    <p class="use-labels">{esc('・'.join(str(value) for value in use_labels))}</p>
    {note}
    <div class="product-card-actions">
      <a class="product-link" href="{esc(detail_page)}" aria-label="{esc(product.get('name'))}の製品詳細を見る">{detail_text}</a>
      <a class="product-consult-link" href="{contact}">研究用途を相談</a>
    </div>
  </div>
</article>'''


def render_html(source: str, relative: Path, products: list[dict[str, object]]) -> tuple[str, int]:
    prefix = "../" * len(relative.parent.parts)
    rendered_roots = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal rendered_roots
        attrs = match.group("attrs")
        rendered_roots += 1
        if re.search(r'\bdata-prerendered-products=["\']true["\']', attrs, re.IGNORECASE):
            return match.group(0)
        if match.group("body").strip() or "data-prerendered-products" in attrs.lower():
            raise ValueError("Product grid must be empty or already marked as pre-rendered")
        homepage = relative == Path("index.html")
        limit_match = LIMIT_PATTERN.search(attrs)
        limit = int(limit_match.group("limit")) if limit_match else 0
        exclude_match = EXCLUDE_PATTERN.search(attrs)
        excluded = set(exclude_match.group("ids").split()) if exclude_match else set()
        visible = [
            item for item in products
            if item.get("visibility") == "public" and item.get("id") not in excluded
        ]
        if homepage:
            featured_match = re.search(r'\bdata-featured-products=["\']([^"\']+)["\']', attrs, re.IGNORECASE)
            ids = featured_match[1].split() if featured_match else []
            public_by_id = {item["id"]: item for item in visible}
            if not ids or len(ids) != limit or len(ids) != len(set(ids)) or set(ids) - public_by_id.keys():
                raise ValueError("Homepage featured products must be unique public IDs matching data-limit")
            visible = [public_by_id[pid] for pid in ids]
        elif limit > 0:
            visible = visible[:limit]
        cards = "\n".join(card(item, prefix, homepage=homepage) for item in visible)
        start = match.group(1)[:-1] + ' data-prerendered-products="true">'
        return f"{start}\n{cards}\n{match.group(4)}"

    return ROOT_PATTERN.sub(replace, source), rendered_roots


def main() -> int:
    from release_robot_ai_glossary import release_robot_ai_glossary

    if not OUTPUT.is_dir():
        print("PRODUCT PRERENDER ERROR: _site directory does not exist")
        return 1

    glossary_count, glossary_errors = release_robot_ai_glossary(OUTPUT)
    if glossary_errors:
        for error in glossary_errors:
            print(f"GLOSSARY BUILD ERROR: {error}")
        return 1

    try:
        data = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))
        products = list(data.get("products", []))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"PRODUCT PRERENDER ERROR: cannot read products.json: {exc}")
        return 1

    errors: list[str] = []
    page_count = 0
    root_count = 0
    for path in sorted(OUTPUT.rglob("*.html")):
        relative = path.relative_to(OUTPUT)
        try:
            source = path.read_text(encoding="utf-8")
            result, rendered = render_html(source, relative, products)
            if rendered:
                if result != source:
                    path.write_text(result, encoding="utf-8")
                page_count += 1
                root_count += rendered
        except (OSError, ValueError) as exc:
            errors.append(f"{relative}: {exc}")

    if errors:
        for error in errors:
            print(f"PRODUCT PRERENDER ERROR: {error}")
        return 1
    if root_count == 0:
        print("PRODUCT PRERENDER ERROR: no data-product-list roots found")
        return 1

    print(f"Generated {glossary_count} glossary page(s).")
    print(f"Product cards pre-rendered into {root_count} root(s) across {page_count} page(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
