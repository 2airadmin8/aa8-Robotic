#!/usr/bin/env python3
"""Fail-closed exact preview bundle media/CSS manifest validator.

Used for any isolated product Preview. A browser can pass CI against _site
while a separate protected Preview deployment accidentally omits an asset.
Validate every local IMG/CSS/JS/VIDEO URL against the *deployment file list*
before treating Preview as READY; no login, deploy, or Production write.
"""
from __future__ import annotations
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import urlsplit, unquote


class LocalAssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = set()

    def handle_starttag(self, tag, attrs):
        vals=dict(attrs)
        keys=[]
        if tag in {"img","script","source","video"}:
            keys.append("src")
        if tag in {"img","video"}:
            keys.append("poster")
        if tag=="link" and "stylesheet" in vals.get("rel","").lower():
            keys.append("href")
        for key in keys:
            value=vals.get(key)
            if not value:
                continue
            parts=urlsplit(value)
            if parts.scheme or parts.netloc or not parts.path.startswith("/"):
                # Absolute remote references require separate source approval.
                continue
            path=unquote(parts.path).lstrip("/")
            if not path.startswith("assets/") or ".." in Path(path).parts or chr(92) in path:
                raise ValueError("PREVIEW_BUNDLE_HOLD: unexpected local asset path "+path)
            self.paths.add(path)


def check(html_text: str, files: set[str]) -> dict:
    parser=LocalAssetParser()
    parser.feed(html_text)
    required=parser.paths
    # The single shared Footer is mandatory. Checking only a PC/SP header
    # logo misses the real iPhone broken-image regression.
    if "assets/img/airadmin8-robotics-logo-footer.svg" not in required:
        raise ValueError("PREVIEW_BUNDLE_HOLD: official Footer logo not referenced")
    missing=sorted(required-files)
    if missing:
        raise ValueError("PREVIEW_BUNDLE_HOLD: deployment missing asset(s): "+", ".join(missing))
    return {"status":"PREVIEW_BUNDLE_ASSETS_PASS",
            "checked_assets":len(required),"footer_logo":True,
            "missing":[]}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--html",type=Path,required=True)
    ap.add_argument("--manifest",type=Path,required=True,
                    help="JSON list of literal file paths from exact deployment listing")
    args=ap.parse_args()
    listing=json.loads(args.manifest.read_text(encoding="utf-8"))
    if not isinstance(listing,list) or any(not isinstance(x,str) for x in listing):
        raise ValueError("PREVIEW_BUNDLE_HOLD: malformed file list")
    report=check(args.html.read_text(encoding="utf-8"),set(listing))
    print(json.dumps(report,ensure_ascii=False))


if __name__=="__main__":
    main()
