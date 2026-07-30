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


def add_organization_schema(markup: str) -> str:
    if 'id="organization-schema"' in markup:
        return markup
    return markup.replace("</head>", ORGANIZATION_SCHEMA + "</head>", 1)


def release_robot_ai_glossary(output: Path = OUTPUT) -> tuple[int, list[str]]:
    errors: list[str] = []
    glossary_dir = output / "glossary"
    glossary_dir.mkdir(parents=True, exist_ok=True)
    (output / "glossary.html").write_text(add_organization_schema(make_index()), encoding="utf-8")
    count = 1
    urls = [BASE + "glossary.html"]
    for term in TERMS:
        slug = term[4]
        if not slug:
            continue
        markup = add_organization_schema(make_detail(term))
        (glossary_dir / f"{slug}.html").write_text(markup, encoding="utf-8")
        urls.append(BASE + f"glossary/{slug}.html")
        count += 1
    update_sitemap(urls)
    if len(TERMS) != 65:
        errors.append(f"Glossary must contain 65 terms, found {len(TERMS)}")
    if count < 16:
        errors.append(f"Glossary must provide at least 15 priority detail pages, found {count - 1}")
    return count, errors
