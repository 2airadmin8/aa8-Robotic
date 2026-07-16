#!/usr/bin/env python3
"""Pre-render resource cards into the built HTML artifact.

The client-side filter remains active, but crawlers and no-JavaScript users should
receive the full resource catalogue in the initial HTML response.
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"
DATA_PATH = ROOT / "data" / "resources.json"
ROOT_PATTERN = re.compile(
    r'(<div\b(?=[^>]*\bdata-resource-list\b)(?P<attrs>[^>]*)>)(?P<body>.*?)(</div>)',
    re.IGNORECASE | re.DOTALL,
)

TYPE_LABELS = {
    "official": "公式入口",
    "sdk": "SDK",
    "ros": "ROS・ROS2",
    "vla": "VLA・学習",
    "teleoperation": "テレオペ",
    "simulation": "シミュレーション",
    "dataset": "データセット",
}


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def render_card(item: dict[str, object]) -> str:
    type_labels = "".join(
        f"<span>{esc(TYPE_LABELS.get(str(resource_type), resource_type))}</span>"
        for resource_type in item.get("types", [])
    )
    url = str(item.get("url", "")).strip()
    if url:
        action = (
            f'<a class="resource-open-link" href="{esc(url)}" '
            'target="_blank" rel="noopener noreferrer">公式ページを開く ↗</a>'
        )
    else:
        action = '<span class="resource-link-pending">公式URL確認中</span>'

    return (
        f'<article id="resource-{esc(item.get("id"))}" class="resource-card" '
        f'data-resource-id="{esc(item.get("id"))}" '
        f'data-resource-maker="{esc(item.get("makerId"))}" '
        f'data-resource-products="{esc(" ".join(item.get("productGroups", [])))}" '
        f'data-resource-types="{esc(" ".join(item.get("types", [])))}">'
        '<div class="resource-card-topline">'
        f'<p class="resource-maker">{esc(item.get("makerName"))}</p>'
        f'<span class="resource-status {esc(item.get("reviewStatus"))}">{esc(item.get("reviewLabel"))}</span>'
        '</div>'
        f'<h3>{esc(item.get("title"))}</h3>'
        f'<p class="resource-description">{esc(item.get("description"))}</p>'
        f'<div class="resource-type-list">{type_labels}</div>'
        '<dl class="resource-meta-list">'
        f'<div><dt>出典</dt><dd>{esc(item.get("sourceLabel"))}</dd></div>'
        f'<div><dt>言語</dt><dd>{esc(item.get("language"))}</dd></div>'
        '</dl>'
        f'<div class="resource-card-footer">{action}</div>'
        '</article>'
    )


def process_html(text: str, resources: list[dict[str, object]]) -> tuple[str, int]:
    rendered = "".join(render_card(item) for item in resources)

    def replace(match: re.Match[str]) -> str:
        opening = match.group(1)
        if "data-prerendered-resources" not in opening:
            opening = opening[:-1] + f' data-prerendered-resources="{len(resources)}">'
        return f"{opening}{rendered}{match.group(4)}"

    result, count = ROOT_PATTERN.subn(replace, text)
    return result, count


def main() -> int:
    try:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"RESOURCE PRERENDER ERROR: cannot read resources.json: {exc}")
        return 1

    resources = data.get("resources", [])
    if not isinstance(resources, list) or not resources:
        print("RESOURCE PRERENDER ERROR: resources.json contains no resources")
        return 1

    if not OUTPUT.is_dir():
        print("RESOURCE PRERENDER ERROR: _site directory does not exist")
        return 1

    processed_roots = 0
    errors: list[str] = []
    for path in sorted(OUTPUT.rglob("*.html")):
        try:
            source = path.read_text(encoding="utf-8")
            result, count = process_html(source, resources)
            if count:
                path.write_text(result, encoding="utf-8")
                processed_roots += count
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"{path.relative_to(OUTPUT)}: {exc}")

    if errors:
        for error in errors:
            print(f"RESOURCE PRERENDER ERROR: {error}")
        return 1
    if processed_roots == 0:
        print("RESOURCE PRERENDER ERROR: no data-resource-list root was found")
        return 1

    print(f"Resource cards pre-rendered into {processed_roots} list root(s): {len(resources)} resources.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
