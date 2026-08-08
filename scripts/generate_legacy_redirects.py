#!/usr/bin/env python3
"""Generate legacy URL migration pages inside the deploy artifact.

Every publishable HTML page is mirrored under the historical `/aa8-Robotic/`
prefix as a lightweight redirect page. GitHub Pages cannot configure wildcard
server-side redirects, so the build artifact must contain each legacy path.
"""
from __future__ import annotations

import html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"
ORIGIN = "https://robotics.air-admin8.co.jp"
LEGACY_ROOT = OUTPUT / "aa8-Robotic"


def make_page(target_path: str) -> str:
    target_url = ORIGIN + target_path
    escaped_url = html.escape(target_url, quote=True)
    js_url = target_url.replace("\\", "\\\\").replace("'", "\\'")
    return f'''<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>ページを移動しました｜AirAdmin8 Robotics</title>
  <meta name="description" content="このページは新しいURLへ移動しました。">
  <meta name="robots" content="noindex,follow">
  <link rel="canonical" href="{escaped_url}">
  <meta property="og:url" content="{escaped_url}">
  <meta http-equiv="refresh" content="0;url={escaped_url}">
  <script>window.location.replace('{js_url}');</script>
</head>
<body>
  <main>
    <h1>ページを移動しました</h1>
    <p><a href="{escaped_url}">新しいページへ移動する</a></p>
  </main>
</body>
</html>
'''


def publishable_pages() -> list[Path]:
    pages: list[Path] = []
    for path in sorted(OUTPUT.rglob("*.html")):
        relative = path.relative_to(OUTPUT)
        if relative.parts and relative.parts[0] == "aa8-Robotic":
            continue
        if "includes" in relative.parts:
            continue
        pages.append(path)
    return pages


def main() -> None:
    if not OUTPUT.is_dir():
        raise SystemExit("_site does not exist; run build_site.py first")

    pages = publishable_pages()
    if not pages:
        raise SystemExit("No publishable HTML pages found")

    generated = 0
    for target_file in pages:
        relative = target_file.relative_to(OUTPUT)
        target_path = "/" + relative.as_posix()
        destination = LEGACY_ROOT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(make_page(target_path), encoding="utf-8")
        generated += 1

    print(f"Generated {generated} legacy-prefix redirect page(s) under /aa8-Robotic/.")


if __name__ == "__main__":
    main()
