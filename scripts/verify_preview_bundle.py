#!/usr/bin/env python3
"""Single fail-closed PREVIEW asset dependency contract.

Preparation: discover all required local assets from rendered HTML/CSS (and
referenced SVG files) and materialize SHA1+size of exact built bytes.
Verification: compare the preflight manifest to Vercel's real deployed *file
tree*, using the Vercel SHA1 source-file uid. No build, network or production
writes happen in this script. Existing CLI --html/--manifest stays compatible.

The two distinct stages are necessary: a CI PASS on _site cannot prove a
separately assembled SSO-protected Vercel bundle is complete.
"""
from __future__ import annotations
import argparse
from hashlib import sha1
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import re
from urllib.parse import unquote, urlsplit

SCHEMA = "aa8-preview-bundle-v1"
SKIP_SCHEMES = ("data:", "#")
CSS_REFS = re.compile(r"""url\(\s*(?:["']([^"']+)["']|([^)'"]+))\s*\)|@import\s+(?:url\()?\s*["']([^"']+)["']""", re.I)
SVG_REFS = re.compile(r"""(?:href|xlink:href)\s*=\s*["']([^"']+)["']""", re.I)


def local_path(url: str, base: str = "") -> str | None:
    url = url.strip()
    if not url or url.startswith(SKIP_SCHEMES):
        return None
    parts = urlsplit(url)
    if parts.scheme or parts.netloc:
        # Remote assets are not imported or implicitly trusted by this builder;
        # they require separately controlled references if the page needs them.
        if parts.scheme in ("https", "http"):
            return None
        raise ValueError("PREVIEW_BUNDLE_HOLD: unsafe resource URL " + url)
    raw = unquote(parts.path)
    if not raw:
        return None
    if chr(92) in raw or "\x00" in raw:
        raise ValueError("PREVIEW_BUNDLE_HOLD: unsafe resource path " + url)
    if raw.startswith("/"):
        segments = raw.lstrip("/").split("/")
    else:
        segments = (base.split("/")[:-1] if base else []) + raw.split("/")
    stack: list[str] = []
    for piece in segments:
        if not piece or piece == ".":
            continue
        if piece == "..":
            if not stack:
                raise ValueError("PREVIEW_BUNDLE_HOLD: path escapes web root " + url)
            stack.pop()
        else:
            stack.append(piece)
    output = "/".join(stack)
    if not output:
        return None
    # Every local resource URL is a dependency, including future root-level
    # favicon, font, wasm, media and JS assets (not just /assets/*).
    return output


class LocalAssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths: set[str] = set()
        self.urls: list[str] = []
        self._inline_css = False

    def handle_starttag(self, tag, attrs):
        vals = dict(attrs)
        if tag == "style":
            self._inline_css = True
        for name in ("src", "poster"):
            if tag in ("img", "script", "source", "video", "audio", "iframe") and vals.get(name):
                self.urls.append(vals[name])
        if tag in ("img", "source") and vals.get("srcset"):
            # Commas in data URIs are skipped by local_path; srcset with
            # actual local URLs is split by candidate separators.
            self.urls.extend(item.strip().split()[0] for item in vals["srcset"].split(",") if item.strip())
        if tag == "link" and vals.get("href"):
            rel = (vals.get("rel") or "").lower()
            if any(x in rel for x in ("stylesheet", "icon", "preload", "modulepreload", "apple-touch-icon")):
                self.urls.append(vals["href"])
        if vals.get("style"):
            self.urls.extend(css_urls(vals["style"]))

        # Backward-compatible direct-path view for existing source QA.
        # Recursive walker separately resolves paths relative to each actual
        # HTML/CSS file, so only root-relative URLs enter this legacy set.
        for url in self.urls:
            if url.startswith("/"):
                path=local_path(url)
                if path is not None:
                    self.paths.add(path)

    def handle_endtag(self, tag):
        if tag == "style":
            self._inline_css = False

    def handle_data(self, data):
        if self._inline_css:
            self.urls.extend(css_urls(data))


def css_urls(style: str) -> list[str]:
    return [next((v.strip() for v in match if v), "") for match in CSS_REFS.findall(style)]


def referenced_assets(html_text: str, web_root: Path, html_base: str = "") -> list[str]:
    html = LocalAssetParser()
    html.feed(html_text)
    todo = [(url, html_base) for url in html.urls]
    required: set[str] = set()
    while todo:
        url, base = todo.pop()
        relative = local_path(url, base)
        if relative is None or relative in required:
            continue
        file = web_root / relative
        if not file.is_file() or not file.resolve().is_relative_to(web_root.resolve()):
            raise ValueError("PREVIEW_BUNDLE_HOLD: referenced asset not present in build: " + relative)
        required.add(relative)
        if file.suffix.lower() == ".css":
            todo.extend((url, relative) for url in css_urls(file.read_text("utf-8")))
        if file.suffix.lower() == ".svg":
            # External SVG references are not implicitly bundled.
            todo.extend((url, relative) for url in SVG_REFS.findall(file.read_text("utf-8")))
    # Shared Footer is ALWAYS used for every product preview, not merely A2.
    if "assets/img/airadmin8-robotics-logo-footer.svg" not in required:
        raise ValueError("PREVIEW_BUNDLE_HOLD: official Footer logo not referenced")
    return sorted(required)


def prepare(web_root: Path, html_files: list[Path], revision: str) -> dict:
    """Build one exact SHA manifest for any number of product previews."""
    if not html_files:
        raise ValueError("PREVIEW_BUNDLE_HOLD: no product previews to audit")
    entries: dict[str, dict] = {}
    pages: dict[str, str] = {}
    page_sizes: dict[str, int] = {}
    for html_file in html_files:
        if not html_file.is_file() or not html_file.resolve().is_relative_to(web_root.resolve()):
            raise ValueError("PREVIEW_BUNDLE_HOLD: preview HTML missing or outside build")
        relative = html_file.relative_to(web_root).as_posix()
        if relative in pages:
            raise ValueError("PREVIEW_BUNDLE_HOLD: duplicate product preview path")
        blob = html_file.read_bytes()
        text = blob.decode("utf-8")
        if 'data-product-factory="g1-v1"' not in text or 'content="noindex,nofollow"' not in text:
            raise ValueError("PREVIEW_BUNDLE_HOLD: cannot bundle non-isolated public HTML")
        pages[relative] = sha1(blob).hexdigest()
        page_sizes[relative] = len(blob)
        for path in referenced_assets(text, web_root, relative):
            data = (web_root / path).read_bytes()
            entries[path] = {"sha1": sha1(data).hexdigest(), "size": len(data)}
    source_files = [
        {"file": name, "sha": pages[name], "size": page_sizes[name]}
        for name in sorted(pages)
    ] + [
        {"file": name, "sha": info["sha1"], "size": info["size"]}
        for name, info in sorted(entries.items())
    ]
    return {"schema": SCHEMA, "revision": revision, "previews": pages,
            "assets": dict(sorted(entries.items())),
            "files": source_files,
            "asset_count": len(entries), "preview_count": len(pages)}


def deployed_source_tree(tree: object) -> dict[str, str]:
    """Normalize exact Vercel Files tree (uid = source-file SHA1)."""
    if not isinstance(tree, list):
        raise ValueError("PREVIEW_BUNDLE_HOLD: deployment file tree must be a list")
    output: dict[str, str] = {}
    def visit(items, prefix=""):
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("PREVIEW_BUNDLE_HOLD: malformed deployment item")
            name = item.get("name")
            if not isinstance(name, str) or not name or "/" in name or name in (".", ".."):
                raise ValueError("PREVIEW_BUNDLE_HOLD: malformed deployment path")
            path = prefix + name
            if item.get("type") == "directory":
                kids = item.get("children")
                if not isinstance(kids, list):
                    raise ValueError("PREVIEW_BUNDLE_HOLD: missing deployed directory children")
                visit(kids, path + "/")
            else:
                sha = item.get("uid")
                if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
                    raise ValueError("PREVIEW_BUNDLE_HOLD: missing deployed file SHA1")
                if path in output:
                    raise ValueError("PREVIEW_BUNDLE_HOLD: duplicate deployed path")
                output[path] = sha
    visit(tree)
    return output


def verify_deployment(expected: dict, tree: object, *, deployed_revision: str,
                      state: str, target: object) -> dict:
    if expected.get("schema") != SCHEMA:
        raise ValueError("PREVIEW_BUNDLE_HOLD: unsupported manifest contract")
    if not isinstance(deployed_revision, str) or deployed_revision != expected.get("revision"):
        raise ValueError("PREVIEW_BUNDLE_HOLD: deployment SHA does not match reviewed HEAD")
    if state != "READY" or target is not None:
        raise ValueError("PREVIEW_BUNDLE_HOLD: preview not READY or targets Production")
    files = deployed_source_tree(tree)
    missing, changed = [], []
    # Vercel's source manifest can place files at root or under src/.
    if "src" in files and len(files) == 1:
        raise ValueError("PREVIEW_BUNDLE_HOLD: invalid collapsed source tree")
    declared=expected.get("files")
    if (not isinstance(declared,list) or len(declared)!=len(expected["previews"])+len(expected["assets"])
            or any(not isinstance(x,dict) or not isinstance(x.get("file"),str)
                   for x in declared)):
        raise ValueError("PREVIEW_BUNDLE_HOLD: bundle files are incomplete or unbound")
    for page, sha in expected["previews"].items():
        if page not in files:
            missing.append(page)
        elif files[page] != sha:
            changed.append(page)
    for path, info in expected["assets"].items():
        if path not in files:
            missing.append(path)
        elif files[path] != info["sha1"]:
            changed.append(path)
    if missing or changed:
        raise ValueError("PREVIEW_BUNDLE_HOLD: missing=" + repr(sorted(missing))
                         + " sha_mismatch=" + repr(sorted(changed)))
    return {"status": "PREVIEW_POST_DEPLOY_PASS",
            "revision": deployed_revision,
            "previews":len(expected["previews"]),
            "assets":len(expected["assets"]),
            "files_checked":len(expected["previews"])+len(expected["assets"]),
            "missing":[],"sha_mismatch":[],"production":False}


def check(html_text: str, files: set[str]) -> dict:
    """Compatibility for existing A2 tests; final gate uses SHA1 manifest."""
    parser = LocalAssetParser()
    parser.feed(html_text)
    required=set(filter(None,(local_path(url) for url in parser.urls)))
    if "assets/img/airadmin8-robotics-logo-footer.svg" not in required:
        raise ValueError("PREVIEW_BUNDLE_HOLD: official Footer logo not referenced")
    missing=sorted(required-files)
    if missing:
        raise ValueError("PREVIEW_BUNDLE_HOLD: deployment missing asset(s): "+", ".join(missing))
    return {"status":"PREVIEW_BUNDLE_ASSETS_PASS",
            "checked_assets":len(required),"footer_logo":True,"missing":[]}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--html",type=Path)
    ap.add_argument("--manifest",type=Path)
    ap.add_argument("--site",type=Path,help="read-only generated _site root")
    ap.add_argument("--previews",nargs="*",help="exact preview HTML paths relative to --site")
    ap.add_argument("--revision",default="local-dev")
    ap.add_argument("--emit",type=Path,help="create exact per-file SHA1 manifest outside _site")
    ap.add_argument("--verify-deployed",type=Path,help="read actual Vercel file tree JSON")
    ap.add_argument("--expected",type=Path)
    ap.add_argument("--deployed-sha")
    ap.add_argument("--deployed-state")
    ap.add_argument("--deployed-target",default="null")
    args=ap.parse_args()
    if args.site:
        discovered = sorted(p.relative_to(args.site).as_posix()
            for p in args.site.rglob("*-preview.html"))
        if (args.site/"products/factory-qa.html").is_file():
            discovered.append("products/factory-qa.html")
        paths=[args.site / x for x in (args.previews or discovered)]
        report=prepare(args.site,paths,args.revision)
        if args.emit:
            args.emit.parent.mkdir(parents=True,exist_ok=True)
            args.emit.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n","utf-8")
        print(json.dumps({k:v for k,v in report.items() if k!="assets"},ensure_ascii=False))
    elif args.verify_deployed:
        if not args.expected or not args.deployed_sha or not args.deployed_state:
            ap.error("--verify-deployed requires --expected, --deployed-sha and --deployed-state")
        expected=json.loads(args.expected.read_text("utf-8"))
        actual=json.loads(args.verify_deployed.read_text("utf-8"))
        # Accept Vercel {result:tree} wrapper or raw provider file tree.
        tree=actual.get("result") if isinstance(actual,dict) else actual
        target=None if args.deployed_target=="null" else args.deployed_target
        print(json.dumps(verify_deployment(expected,tree,
                 deployed_revision=args.deployed_sha,state=args.deployed_state,target=target),
                 ensure_ascii=False))
    elif args.html and args.manifest:
        files=json.loads(args.manifest.read_text("utf-8"))
        print(json.dumps(check(args.html.read_text("utf-8"),set(files)),ensure_ascii=False))
    else:
        ap.error("use --site [--previews ...] or --verify-deployed or --html/--manifest")


if __name__=="__main__":
    main()
