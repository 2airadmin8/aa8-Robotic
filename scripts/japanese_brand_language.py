#!/usr/bin/env python3
"""Prefer natural Japanese brand language in built HTML.

The formal English brand name remains available in structured data, while
search-facing titles, descriptions and visible labels use Japanese wording
that is more natural for the Japan market.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"

COMMON_REPLACEMENTS = {
    '<span>AirAdmin8 Robotics</span>': '<span>AirAdmin8 ロボティクス</span>',
    '<strong>AirAdmin8 Robotics</strong>': '<strong>AirAdmin8 ロボティクス</strong>',
    'aria-label="AirAdmin8 Robotics ホーム"': 'aria-label="AirAdmin8 ロボティクス ホーム"',
    '｜AirAdmin8 Robotics</title>': '｜AirAdmin8 ロボティクス</title>',
    'AIRADMIN8 ROBOTICS / PHYSICAL AI': 'AIRADMIN8 ロボティクス / フィジカルAI',
    'AIRADMIN8 ROBOTICS ×': 'AIRADMIN8 ロボティクス ×',
    'AirAdmin8 Roboticsは': 'AirAdmin8 ロボティクスは',
    'AirAdmin8 Roboticsが': 'AirAdmin8 ロボティクスが',
    'AirAdmin8 Roboticsでは': 'AirAdmin8 ロボティクスでは',
    'AirAdmin8 Roboticsの': 'AirAdmin8 ロボティクスの',
}

HOME_REPLACEMENTS = {
    '<title>AirAdmin8 Robotics｜AIロボット・Physical AI導入支援｜Unitree・AgiBot</title>':
        '<title>AirAdmin8 ロボティクス｜AIロボット・フィジカルAI導入支援｜Unitree・AgiBot</title>',
    '<meta name="description" content="株式会社AirAdmin8が運営するAirAdmin8 Robotics。Unitree・AgiBotなどのAIロボットをメーカー横断で比較し、研究用途、正式見積、大学購買、PoC、SDK確認、初期設定まで支援します。">':
        '<meta name="description" content="株式会社AirAdmin8のロボティクス事業。AIロボット、ヒューマノイドロボット、四足ロボットをメーカー横断で比較し、Unitree・AgiBotの選定、見積、大学購買、PoC、SDK確認、初期導入まで支援します。">',
    'AirAdmin8 ロボティクスは、人型ロボット、四足ロボット、ロボットアームをメーカー横断で比較。':
        'AirAdmin8 ロボティクスは、AIロボット、ヒューマノイドロボット（人型ロボット）、四足ロボット、ロボットアームをメーカー横断で比較。',
}

ABOUT_REPLACEMENTS = {
    '<title>AirAdmin8 Robotics 会社情報｜株式会社AirAdmin8のAIロボット事業</title>':
        '<title>AirAdmin8 ロボティクス 会社情報｜株式会社AirAdmin8のAIロボット事業</title>',
    '<h1>AirAdmin8 Robotics。<br>AIロボットを、日本で使える状態へ。</h1>':
        '<h1>AirAdmin8 ロボティクス。<br>AIロボットを、日本で使える状態へ。</h1>',
}

UNITREE_REPLACEMENTS = {
    '<title>Unitree（宇樹科技）｜G1・G1-D・Go2 EDU・価格・日本導入・SDK｜AirAdmin8 ロボティクス</title>':
        '<title>Unitree（ユニツリー／宇樹科技）｜G1・G1-D・Go2 EDU・価格・日本導入｜AirAdmin8 ロボティクス</title>',
    '<h1>Unitree / 宇樹科技</h1>': '<h1>Unitree / ユニツリー / 宇樹科技</h1>',
}


def apply_replacements(text: str, replacements: dict[str, str]) -> str:
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def prefer_japanese_brand_language(output: Path = OUTPUT) -> tuple[int, list[str]]:
    if not output.is_dir():
        return 0, ["_site directory does not exist"]

    updated = 0
    for path in sorted(output.rglob("*.html")):
        text = path.read_text(encoding="utf-8")
        original = text
        text = apply_replacements(text, COMMON_REPLACEMENTS)

        rel = path.relative_to(output).as_posix()
        if rel == "index.html":
            text = apply_replacements(text, HOME_REPLACEMENTS)
        elif rel == "about.html":
            text = apply_replacements(text, ABOUT_REPLACEMENTS)
        elif rel == "manufacturers/unitree.html":
            text = apply_replacements(text, UNITREE_REPLACEMENTS)

        if text != original:
            path.write_text(text, encoding="utf-8")
            updated += 1

    return updated, []


if __name__ == "__main__":
    count, problems = prefer_japanese_brand_language()
    for problem in problems:
        print(f"JAPANESE BRAND ERROR: {problem}")
    print(f"Japanese-first brand wording applied to {count} HTML page(s).")
    raise SystemExit(1 if problems else 0)
