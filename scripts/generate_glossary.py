#!/usr/bin/env python3
"""Generate the glossary index and selected detail pages from data/glossary.json."""
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
<style>
.glossary-shell{{width:min(var(--max),calc(100% - 40px));margin-inline:auto}}
.glossary-main{{padding-bottom:72px;font-family:inherit}}
.glossary-hero{{padding:48px 0 34px;background:linear-gradient(180deg,#f3faff 0%,#fff 100%)}}
.glossary-kicker{{margin:0 0 12px;color:var(--blue);font-size:.8rem;font-weight:900;letter-spacing:.14em}}
.glossary-hero h1{{max-width:980px;margin:0;line-height:1.12;font-size:clamp(2.25rem,4.2vw,3.6rem);letter-spacing:-.035em;color:var(--ink)}}
.glossary-intro{{max-width:900px;margin:20px 0 0;color:var(--muted);font-size:1.06rem;line-height:1.85}}
.glossary-tools{{position:sticky;top:72px;z-index:10;padding:18px 0;background:rgba(255,255,255,.97);border-top:1px solid var(--line);border-bottom:1px solid var(--line);backdrop-filter:blur(10px)}}
.glossary-tools label{{display:block;margin-bottom:7px;color:var(--ink);font-size:.92rem;font-weight:800}}
.glossary-search{{box-sizing:border-box;width:100%;min-height:52px;padding:13px 16px;border:1px solid #bdd9e5;border-radius:14px;color:var(--ink);background:#fff;font:inherit}}
.glossary-search::placeholder{{color:#7d8f98}}
.glossary-search:focus{{outline:3px solid rgba(0,154,210,.16);border-color:var(--blue)}}
.glossary-index{{display:flex;flex-wrap:wrap;gap:8px;margin-top:13px}}
.glossary-index button{{min-height:42px;padding:8px 14px;border:1px solid #cde1e9;border-radius:999px;color:var(--blue-dark);background:#fff;font:inherit;font-size:.9rem;font-weight:800;cursor:pointer}}
.glossary-index button[aria-pressed="true"]{{color:#fff;border-color:var(--blue-dark);background:var(--blue-dark)}}
.glossary-category{{padding:48px 0 4px;scroll-margin-top:180px}}
.glossary-category>h2{{margin:0 0 20px;color:var(--navy);font-size:clamp(1.75rem,3vw,2.4rem);line-height:1.2;letter-spacing:-.025em}}
.term-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}
.term-card,.glossary-detail{{padding:24px;border:1px solid var(--line);border-radius:18px;background:#fff;box-shadow:var(--shadow)}}
.term-card{{display:flex;min-height:210px;flex-direction:column}}
.term-card h3{{margin:0 0 4px;color:var(--navy);font-size:1.18rem;line-height:1.45}}
.term-card p,.glossary-detail p,.glossary-detail li{{color:var(--muted);line-height:1.75}}
.term-en{{margin:0!important;color:var(--blue)!important;font-size:.76rem;font-weight:900;letter-spacing:.05em;text-transform:uppercase}}
.term-link{{display:inline-block;margin-top:auto;padding-top:14px;color:var(--blue-dark);font-weight:900;text-decoration:none}}
.glossary-detail{{margin-top:40px}}
.no-results{{display:none;padding:36px 0;color:#7a4a00;font-weight:800}}
@media(max-width:980px){{.glossary-tools{{top:60px}}}}
@media(max-width:760px){{.glossary-shell{{width:min(100% - 28px,var(--max))}}.glossary-main{{padding-bottom:56px}}.glossary-hero{{padding:36px 0 28px}}.glossary-hero h1{{font-size:clamp(2rem,10vw,2.75rem)}}.glossary-intro{{margin-top:16px;font-size:1rem}}.glossary-tools{{padding:14px 0}}.glossary-index{{flex-wrap:nowrap;overflow-x:auto;padding-bottom:4px;scrollbar-width:thin}}.glossary-index button{{flex:0 0 auto}}.term-grid{{grid-template-columns:1fr}}.term-card{{min-height:0}}.glossary-category{{padding-top:36px}}}}
</style>
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
    buttons = '<button type="button" data-category-filter="" aria-pressed="true">すべて</button>' + "".join(f'<button type="button" data-category-filter="{esc(category)}" aria-pressed="false">{esc(category)}</button>' for category in categories)
    schema = {"@context": "https://schema.org", "@type": "DefinedTermSet", "name": "ロボット・フィジカルAI用語集", "url": BASE + "glossary.html", "hasDefinedTerm": [{"@type": "DefinedTerm", "name": term[1], "alternateName": term[2], "description": term[3]} for term in terms]}
    script = '''<script>const input=document.querySelector('#glossary-search');const sections=[...document.querySelectorAll('.glossary-category')];const filterButtons=[...document.querySelectorAll('[data-category-filter]')];function filter(value=''){const q=value.trim().toLowerCase();let visible=0;sections.forEach(section=>{let count=0;section.querySelectorAll('.term-card').forEach(card=>{const show=!q||card.dataset.term.toLowerCase().includes(q)||card.textContent.toLowerCase().includes(q);card.hidden=!show;if(show)count++});section.hidden=count===0;visible+=count});document.querySelector('#no-results').style.display=visible?'none':'block';filterButtons.forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.categoryFilter.toLowerCase()===q)))}input.addEventListener('input',event=>filter(event.target.value));filterButtons.forEach(button=>button.addEventListener('click',()=>{input.value=button.dataset.categoryFilter;filter(input.value)}));</script>'''
    hero = '''<main class="glossary-main"><section class="glossary-hero"><div class="glossary-shell"><p class="glossary-kicker">ROBOT &amp; PHYSICAL AI GLOSSARY</p><h1>ロボット・フィジカルAI用語集</h1><p class="glossary-intro">製品選定、研究開発、データ収集、ROS 2、シミュレーション、安全・法規まで、AIロボットの研究と導入に必要な概念を体系的に整理しました。</p></div></section>'''
    tools = f'''<section class="glossary-tools"><div class="glossary-shell"><label for="glossary-search">用語を検索</label><input id="glossary-search" class="glossary-search" type="search" placeholder="例：VLA、ROS 2、RGB-D、技適"><div class="glossary-index">{buttons}</div></div></section><div class="glossary-shell"><p id="no-results" class="no-results">一致する用語がありません。</p>{''.join(cards)}</div></main>'''
    return head("ロボット・フィジカルAI用語集｜AirAdmin8 Robotics", "AIロボット、具身AI、VLA、ロボット学習、ROS 2、シミュレーション、安全・法規など、研究・選定・導入に役立つ専門用語を解説します。", BASE + "glossary.html", schema=schema) + layout(HEADER) + hero + tools + layout(FOOTER) + script + "</body></html>"


def make_detail(term: list[str | None], related: list[list[str | None]]) -> str:
    category, jp, en, description, slug = term
    links = "".join(f'<a href="{item[4]}.html">{esc(str(item[1]))}</a> ' for item in related)
    schema = {"@context": "https://schema.org", "@type": "DefinedTerm", "name": jp, "alternateName": en, "description": description, "url": BASE + f"glossary/{slug}.html", "inDefinedTermSet": BASE + "glossary.html"}
    hero = f'''<main class="glossary-main"><section class="glossary-hero"><div class="glossary-shell"><p class="glossary-kicker"><a href="../glossary.html">用語集</a> / {esc(str(category))}</p><h1>{esc(str(jp))}とは？</h1><p class="glossary-intro">{esc(str(en))}</p></div></section>'''
    body = f'''<section class="glossary-shell glossary-detail"><p><strong>{esc(str(description))}</strong></p><h2>導入・研究で確認するポイント</h2><ul><li>対象タスクと必要な性能を先に定義する</li><li>対応する機体、センサー、SDK、計算環境を確認する</li><li>評価指標、データ取得条件、安全条件を決める</li><li>PoC後の保守、更新、法規対応まで含めて判断する</li></ul><h2>関連用語</h2><p>{links}<a href="../glossary.html">用語集へ戻る</a></p></section></main>'''
    return head(f"{jp}とは？｜AirAdmin8 Robotics", f"{jp}（{en}）の意味と、AIロボットの研究・選定・導入で確認すべきポイントを解説します。", BASE + f"glossary/{slug}.html", depth=1, schema=schema) + layout(HEADER, 1) + hero + body + layout(FOOTER, 1) + "</body></html>"


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
