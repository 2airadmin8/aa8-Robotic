#!/usr/bin/env python3
"""Generate the glossary index and priority detail pages from data/glossary.json."""
from __future__ import annotations

import html
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"
DATA = ROOT / "data" / "glossary.json"
BASE = "https://robotics.air-admin8.co.jp/"
HEADER = ROOT / "includes" / "site-header.html"
FOOTER = ROOT / "includes" / "site-footer.html"


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def load_data() -> tuple[list[str], list[list[str | None]]]:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    categories = payload["categories"]
    terms = payload["terms"]
    if len(categories) != 8:
        raise ValueError(f"Glossary requires 8 categories, found {len(categories)}")
    if len(terms) != 80:
        raise ValueError(f"Glossary requires 80 terms, found {len(terms)}")
    counts = Counter(term[0] for term in terms)
    expected = {category: 10 for category in categories}
    if counts != expected:
        raise ValueError(f"Glossary category counts mismatch: expected={expected} actual={dict(counts)}")
    names = [str(term[1]) for term in terms]
    if len(names) != len(set(names)):
        raise ValueError("Glossary term names must be unique")
    slugs = [str(term[4]) for term in terms if term[4]]
    if len(slugs) != len(set(slugs)):
        raise ValueError("Glossary detail slugs must be unique")
    return categories, terms


def layout(source: Path, depth: int = 0) -> str:
    prefix = "../" * depth
    text = source.read_text(encoding="utf-8").strip()
    return re.sub(r'(?P<attr>(?:href|src|srcset)=["\'])/', rf'\g<attr>{prefix}', text)


def head(title: str, description: str, canonical: str, depth: int = 0, schema: dict | None = None) -> str:
    prefix = "../" * depth
    structured = ""
    if schema:
        structured = f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>'
    return f'''<!doctype html><html lang="ja"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(description)}">
<link rel="canonical" href="{canonical}"><meta property="og:url" content="{canonical}">
<link rel="stylesheet" href="{prefix}assets/css/site.css"><link rel="stylesheet" href="{prefix}assets/css/shared-layout.css">
<style>.glossary-shell{{width:min(1120px,calc(100% - 40px));margin:auto}}.glossary-hero{{padding:64px 0 32px;background:linear-gradient(135deg,#fff,#eef9fc)}}.glossary-hero h1{{font-size:clamp(2rem,5vw,3.4rem);margin:.3em 0}}.glossary-hero p{{max-width:820px;line-height:1.9;color:#536c78}}.glossary-tools{{position:sticky;top:72px;z-index:10;padding:16px 0;background:rgba(255,255,255,.96);border-bottom:1px solid #d8e7ed;backdrop-filter:blur(10px)}}.glossary-search{{box-sizing:border-box;width:100%;min-height:52px;padding:13px 15px;border:1px solid #bdd9e5;border-radius:12px;font:inherit}}.glossary-index{{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}}.glossary-index button,.glossary-index a{{padding:9px 12px;border:1px solid #cde1e9;border-radius:999px;color:#087cae;background:#fff;font-weight:700;text-decoration:none;cursor:pointer}}.glossary-category{{padding:48px 0 4px;scroll-margin-top:180px}}.glossary-category>h2{{font-size:1.8rem;margin:0 0 20px;color:#073e5a}}.term-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}.term-card,.glossary-detail{{padding:24px;border:1px solid #d8e7ed;border-radius:16px;background:#fff;box-shadow:0 8px 24px rgba(13,61,84,.05)}}.term-card h3{{margin:0 0 4px;font-size:1.2rem;color:#073e5a}}.term-card p,.glossary-detail p,.glossary-detail li{{line-height:1.75;color:#526c79}}.term-en{{margin:0!important;color:#0084c5!important;font-size:.78rem;font-weight:800;letter-spacing:.05em;text-transform:uppercase}}.term-link{{display:inline-block;margin-top:14px;color:#087cae;font-weight:700;text-decoration:none}}.glossary-main{{padding-bottom:80px}}.no-results{{display:none;padding:36px 0;font-weight:700;color:#7a4a00}}@media(max-width:760px){{.glossary-shell{{width:min(100% - 28px,1120px)}}.glossary-tools{{top:64px}}.term-grid{{grid-template-columns:1fr}}.glossary-category{{padding-top:36px}}}}</style>
{structured}</head><body>'''


def make_index(categories: list[str], terms: list[list[str | None]]) -> str:
    cards: list[str] = []
    for category in categories:
        rows: list[str] = []
        for term_category, jp, en, description, slug in terms:
            if term_category != category:
                continue
            detail = f'<a class="term-link" href="glossary/{slug}.html">詳しく見る →</a>' if slug else ""
            rows.append(f'<article class="term-card" data-term="{esc(str(jp))} {esc(str(en))} {esc(category)}"><h3>{esc(str(jp))}</h3><p class="term-en">{esc(str(en))}</p><p>{esc(str(description))}</p>{detail}</article>')
        cards.append(f'<section class="glossary-category" data-category="{esc(category)}"><h2>{esc(category)}</h2><div class="term-grid">{"".join(rows)}</div></section>')
    buttons = "".join(f'<button type="button" data-category-filter="{esc(category)}">{esc(category)}</button>' for category in categories)
    schema = {"@context": "https://schema.org", "@type": "DefinedTermSet", "name": "ロボット・フィジカルAI用語集80語", "url": BASE + "glossary.html", "hasDefinedTerm": [{"@type": "DefinedTerm", "name": term[1], "alternateName": term[2], "description": term[3]} for term in terms]}
    script = '''<script>const input=document.querySelector('#glossary-search');const sections=[...document.querySelectorAll('.glossary-category')];function filter(value=''){const q=value.trim().toLowerCase();let visible=0;sections.forEach(section=>{let count=0;section.querySelectorAll('.term-card').forEach(card=>{const show=!q||card.dataset.term.toLowerCase().includes(q)||card.textContent.toLowerCase().includes(q);card.hidden=!show;if(show)count++});section.hidden=count===0;visible+=count});document.querySelector('#no-results').style.display=visible?'none':'block'}input.addEventListener('input',event=>filter(event.target.value));document.querySelectorAll('[data-category-filter]').forEach(button=>button.addEventListener('click',()=>{input.value=button.dataset.categoryFilter;filter(input.value)}));</script>'''
    return head("ロボット・フィジカルAI用語集80語｜AirAdmin8 Robotics", "AIロボット、具身AI、VLA、ロボット学習、ROS 2、シミュレーション、安全・法規まで、導入判断に役立つ80用語を8分類で解説します。", BASE + "glossary.html", schema=schema) + layout(HEADER) + f'''<main class="glossary-main"><section class="glossary-hero"><div class="glossary-shell"><p>ROBOT &amp; PHYSICAL AI GLOSSARY</p><h1>ロボット・フィジカルAI用語集80語</h1><p>製品選定、研究開発、データ収集、ROS 2、シミュレーション、安全・法規まで、AIロボット導入で実際に判断材料になる用語を8分類で整理しました。</p></div></section><section class="glossary-tools"><div class="glossary-shell"><label for="glossary-search">用語を検索</label><input id="glossary-search" class="glossary-search" type="search" placeholder="例：具身AI、VLA、ROS 2、RGB-D、技適"><div class="glossary-index">{buttons}</div></div></section><div class="glossary-shell"><p id="no-results" class="no-results">一致する用語がありません。</p>{''.join(cards)}</div></main>''' + layout(FOOTER) + script + "</body></html>"


def make_detail(term: list[str | None], related: list[list[str | None]]) -> str:
    category, jp, en, description, slug = term
    links = "".join(f'<a href="{item[4]}.html">{esc(str(item[1]))}</a> ' for item in related)
    schema = {"@context": "https://schema.org", "@type": "DefinedTerm", "name": jp, "alternateName": en, "description": description, "url": BASE + f"glossary/{slug}.html", "inDefinedTermSet": BASE + "glossary.html"}
    return head(f"{jp}とは？｜AirAdmin8 Robotics", f"{jp}（{en}）の意味と、AIロボットの研究・選定・導入で確認すべきポイントを解説します。", BASE + f"glossary/{slug}.html", depth=1, schema=schema) + layout(HEADER, 1) + f'''<main class="glossary-main"><section class="glossary-hero"><div class="glossary-shell"><p><a href="../glossary.html">用語集80語</a> / {esc(str(category))}</p><h1>{esc(str(jp))}とは？</h1><p>{esc(str(en))}</p></div></section><section class="glossary-shell glossary-detail"><p><strong>{esc(str(description))}</strong></p><h2>導入・研究で確認するポイント</h2><ul><li>対象タスクと必要な性能を先に定義する</li><li>対応する機体、センサー、SDK、計算環境を確認する</li><li>評価指標、データ取得条件、安全条件を決める</li><li>PoC後の保守、更新、法規対応まで含めて判断する</li></ul><h2>関連用語</h2><p>{links}<a href="../glossary.html">80語の一覧へ</a></p></section></main>''' + layout(FOOTER, 1) + "</body></html>"


def update_sitemap(urls: list[str]) -> None:
    path = OUTPUT / "sitemap.xml"
    if not path.exists():
        raise FileNotFoundError("sitemap.xml not found in build output")
    text = path.read_text(encoding="utf-8")
    text = re.sub(r'\s*<url><loc>https://robotics\.air-admin8\.co\.jp/glossary(?:/[^<]+)?\.html</loc>.*?</url>', "", text, flags=re.S)
    additions = "".join(f"\n  <url><loc>{url}</loc></url>" for url in urls)
    text = text.replace("</urlset>", additions + "\n</urlset>")
    path.write_text(text, encoding="utf-8")


def generate() -> dict[str, int]:
    categories, terms = load_data()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "glossary.html").write_text(make_index(categories, terms), encoding="utf-8")
    detail_dir = OUTPUT / "glossary"
    if detail_dir.exists():
        for path in detail_dir.glob("*.html"):
            path.unlink()
    detail_dir.mkdir(exist_ok=True)
    detail_terms = [term for term in terms if term[4]]
    for term in detail_terms:
        related = [item for item in detail_terms if item[0] == term[0] and item[4] != term[4]][:5]
        (detail_dir / f"{term[4]}.html").write_text(make_detail(term, related), encoding="utf-8")
    urls = [BASE + "glossary.html", *[BASE + f"glossary/{term[4]}.html" for term in detail_terms]]
    update_sitemap(urls)
    return {"terms": len(terms), "categories": len(categories), "details": len(detail_terms)}


if __name__ == "__main__":
    result = generate()
    print(f"Generated glossary: {result}")
