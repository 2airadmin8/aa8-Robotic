#!/usr/bin/env python3
"""Release the glossary pages into the built site."""

from pathlib import Path

from generate_robot_ai_glossary import BASE, OUTPUT, TERMS, make_detail, make_index, update_sitemap

ORGANIZATION_SCHEMA = '''<script id="organization-schema" type="application/ld+json">{
  "@context":"https://schema.org",
  "@type":"Organization",
  "name":"株式会社AirAdmin8",
  "alternateName":"AirAdmin8 ロボティクス",
  "url":"https://www.air-admin8.co.jp/",
  "sameAs":["https://robotics.air-admin8.co.jp/"]
}</script>'''


def normalize_shell(markup: str, depth: int) -> str:
    markup = markup.replace('<footer class="site-footer">', '<footer class="footer">')
    company_link = '<p><a href="https://www.air-admin8.co.jp/company/">会社情報</a></p>'
    if "会社情報" not in markup:
        markup = markup.replace("</footer>", company_link + "</footer>", 1)
    if 'id="organization-schema"' not in markup:
        markup = markup.replace("</head>", ORGANIZATION_SCHEMA + "</head>", 1)
    return markup


def release_robot_ai_glossary(output: Path = OUTPUT) -> tuple[int, list[str]]:
    errors: list[str] = []
    glossary_dir = output / "glossary"
    glossary_dir.mkdir(parents=True, exist_ok=True)
    (output / "glossary.html").write_text(normalize_shell(make_index(), 0), encoding="utf-8")
    count = 1
    urls = [BASE + "glossary.html"]
    for term in TERMS:
        slug = term[4]
        if not slug:
            continue
        markup = normalize_shell(make_detail(term), 1)
        (glossary_dir / f"{slug}.html").write_text(markup, encoding="utf-8")
        urls.append(BASE + f"glossary/{slug}.html")
        count += 1
    update_sitemap(urls)
    if len(TERMS) != 65:
        errors.append(f"Glossary must contain 65 terms, found {len(TERMS)}")
    if count < 16:
        errors.append(f"Glossary must provide at least 15 priority detail pages, found {count - 1}")
    return count, errors
