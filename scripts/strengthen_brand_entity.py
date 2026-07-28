#!/usr/bin/env python3
"""Strengthen AirAdmin8 brand/entity signals in built JSON-LD.

This runs after static structured data injection. It keeps the existing
organization @id used by the site, while making the relationship between the
corporate brand (AirAdmin8) and the robotics business brand explicit.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"
CORPORATE_URL = "https://www.air-admin8.co.jp/"
ROBOTICS_URL = "https://robotics.air-admin8.co.jp/aa8-Robotic/"

ORG_PATTERN = re.compile(
    r'(<script\s+id=["\']organization-schema["\']\s+type=["\']application/ld\+json["\']>)(.*?)(</script>)',
    re.IGNORECASE | re.DOTALL,
)


def strengthen_brand_entity(output: Path = OUTPUT) -> tuple[int, list[str]]:
    if not output.is_dir():
        return 0, ["_site directory does not exist"]

    updated = 0
    errors: list[str] = []

    for path in sorted(output.rglob("*.html")):
        text = path.read_text(encoding="utf-8")
        match = ORG_PATTERN.search(text)
        if not match:
            errors.append(f"Missing organization-schema: {path.relative_to(output)}")
            continue

        try:
            data = json.loads(match.group(2))
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid organization-schema in {path.relative_to(output)}: {exc}")
            continue

        data["name"] = "株式会社AirAdmin8"
        data["alternateName"] = [
            "AirAdmin8",
            "Air Admin8",
            "AirAdmin8 ロボティクス",
            "AirAdmin8 Robotics",
        ]
        data["url"] = CORPORATE_URL
        data["brand"] = {
            "@type": "Brand",
            "name": "AirAdmin8 ロボティクス",
            "alternateName": ["AirAdmin8 Robotics", "AirAdmin8"],
            "url": ROBOTICS_URL,
        }
        data["knowsAbout"] = [
            "AIロボット",
            "ロボット",
            "フィジカルAI",
            "ヒューマノイドロボット",
            "ヒューマノイド",
            "四足ロボット",
            "Unitree",
            "ユニツリー",
            "AgiBot",
            "X2",
            "VLA",
            "ROS2",
        ]

        payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        replacement = f"{match.group(1)}{payload}{match.group(3)}"
        text = text[: match.start()] + replacement + text[match.end() :]
        path.write_text(text, encoding="utf-8")
        updated += 1

    return updated, errors


if __name__ == "__main__":
    count, problems = strengthen_brand_entity()
    for problem in problems:
        print(f"BRAND ENTITY ERROR: {problem}")
    print(f"AirAdmin8 brand entity strengthened in {count} HTML page(s).")
    raise SystemExit(1 if problems else 0)
