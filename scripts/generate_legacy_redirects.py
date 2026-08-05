#!/usr/bin/env python3
"""Generate legacy URL migration pages inside the deploy artifact.

GitHub Pages cannot configure server-side 301 redirects. These pages provide:
- noindex,follow
- canonical to the current URL
- immediate meta refresh
- JavaScript location.replace fallback
- visible manual link fallback

They are generated in _site so the source tree stays clean and the normal
metadata/structured-data/brand injection pipeline can process them.
"""
from __future__ import annotations

import html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"
ORIGIN = "https://robotics.air-admin8.co.jp"

LEGACY_REDIRECTS = {
    "aa8-Robotic/glossary/physical-ai.html": "/glossary/physical-ai.html",
}


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
  <link rel="stylesheet" href="../../assets/css/site.css">
  <link rel="stylesheet" href="../../assets/css/shared-layout.css">
  <script>window.location.replace('{js_url}');</script>
</head>
<body>
<header class="site-header"><div class="wrap"><a href="../../index.html">AirAdmin8 Robotics</a></div></header>
<main><div class="wrap"><h1>ページを移動しました</h1><p><a href="{escaped_url}">新しいページへ移動する</a></p></div></main>
<footer class="footer"><div class="wrap"><p>© AirAdmin8 Inc.</p></div></footer>
</body>
</html>
'''


def main() -> None:
    if not OUTPUT.is_dir():
        raise SystemExit("_site does not exist; run build_site.py first")

    for legacy_path, target_path in LEGACY_REDIRECTS.items():
        target_file = OUTPUT / target_path.lstrip("/")
        if not target_file.is_file():
            raise SystemExit(f"Redirect target does not exist: {target_path}")

        destination = OUTPUT / legacy_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(make_page(target_path), encoding="utf-8")
        print(f"Generated legacy redirect: /{legacy_path} -> {target_path}")


if __name__ == "__main__":
    main()
