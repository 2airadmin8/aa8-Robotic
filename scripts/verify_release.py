#!/usr/bin/env python3
"""Read-only release gate for source hygiene and the generated _site artifact."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"

SOURCE_GUIDE_PDF = "assets/pdf/AirAdmin8_AI_Robotics_Support_for_University_Labs.pdf"
PUBLIC_GUIDE_PDF = "assets/pdf/AirAdmin8_AI_Robotics_Support_for_University_Labs.pdf"

REQUIRED_FILES = [
    "index.html",
    "about.html",
    "glossary.html",
    "privacy.html",
    "products.html",
    "products/unitree-g1-d.html",
    "contact.html",
    "resources/document.html",
    "assets/css/shared-layout.css",
    "assets/js/document-tracking.js",
    "assets/img/airadmin8-robotics-logo-pc.svg",
    "assets/img/airadmin8-robotics-logo-sp.svg",
    "assets/img/airadmin8-robotics-logo-footer.svg",
    "assets/img/airadmin8-wordmark.svg",
    "assets/img/airadmin8-robotics-badge.svg",
    "assets/img/favicon-airadmin8.svg",
    "assets/img/airadmin8-icon-192.png",
    "assets/img/airadmin8-icon-512.png",
    "assets/img/apple-touch-icon.png",
    SOURCE_GUIDE_PDF,
    PUBLIC_GUIDE_PDF,
    "sitemap.xml",
    "robots.txt",
    "CNAME",
]

ALLOWED_WORKFLOWS = {"ci.yml", "pages.yml", "production-check.yml"}
LEGACY_REDIRECT_ROOTS = {"aa8-Robotic"}
FORBIDDEN_SOURCE_PATHS = {
    ".github/workflows/auto-merge.yml",
    ".github/workflows/artifact-validation.yml",
    ".github/workflows/production-url-check.yml",
    ".github/workflows/publish-sp-logo.yml",
    ".github/workflows/refresh-header-css-cache.yml",
    ".github/workflows/sync-shared-header.yml",
    ".github/workflows/sync-shared-layout.yml",
    ".github/workflows/use-uploaded-logo-directly.yml",
    "scripts/inject_main_site_experience.py",
    "scripts/verify_shared_layout_artifact.py",
    "scripts/sync_top_header.py",
    "assets/css/main-logo.css",
    "assets/img/logo-airadmin8-robotics-pc.png",
    "assets/img/airadmin8-192x192.svg",
    "assets/img/airadmin8-official-logo.png",
    "assets/img/brand-airadmin8-robotics-pc-v4.svg",
    "assets/img/brand-airadmin8-robotics-sp-v4.svg",
    "assets/img/logo-airadmin8-robotics-pc.svg",
    "assets/img/logo-airadmin8-robotics-sp.svg",
    "assets/img/brand",
    "STEP5_ARTIFACT_VALIDATION.md",
}

LEGACY_PATTERNS = {
    "legacy GitHub Pages URL prefix": re.compile(r"https://robotics\.air-admin8\.co\.jp/aa8-Robotic/", re.I),
    "legacy logo stylesheet": re.compile(r"main-logo\.css", re.I),
    "legacy PNG logo": re.compile(r"logo-airadmin8-robotics-pc\.png", re.I),
    "legacy PC logo": re.compile(r"(?:brand-)?logo-airadmin8-robotics-pc(?:-v4)?\.svg", re.I),
    "legacy SP logo": re.compile(r"(?:brand-)?logo-airadmin8-robotics-sp(?:-v4)?\.svg", re.I),
    "legacy favicon": re.compile(r"airadmin8-192x192\.svg", re.I),
    "legacy brand directory": re.compile(r"assets/img/brand/", re.I),
    "legacy brand-picture markup": re.compile(r'class=["\']brand-picture["\']', re.I),
    "legacy logo hiding CSS": re.compile(r"\.brand\s*>\s*\*\s*\{[^{}]*display\s*:\s*none\s*!important", re.I | re.S),
}

SOURCE_SCAN_SUFFIXES = {".html", ".css", ".xml", ".js", ".json"}
SOURCE_SCAN_EXCLUDED_ROOTS = {".git", ".github", "_site", "scripts", "includes"}


def is_legacy_redirect(path: Path) -> bool:
    relative = path.relative_to(OUTPUT)
    return bool(relative.parts and relative.parts[0] in LEGACY_REDIRECT_ROOTS)


def count_shared_element(html: str, tag: str, layout: str) -> int:
    pattern = re.compile(
        rf'<{tag}\b(?=[^>]*\bdata-shared-layout=["\']{re.escape(layout)}["\'])[^>]*>',
        re.IGNORECASE,
    )
    return len(pattern.findall(html))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fail(errors: list[str]) -> int:
    for error in errors:
        print(f"ERROR: {error}")
    print(f"Release verification FAILED with {len(errors)} error(s).")
    return 1


def verify_source_hygiene(errors: list[str]) -> None:
    workflow_dir = ROOT / ".github" / "workflows"
    actual_workflows = {path.name for path in workflow_dir.glob("*.yml")}
    if actual_workflows != ALLOWED_WORKFLOWS:
        errors.append(f"workflow set mismatch: expected={sorted(ALLOWED_WORKFLOWS)} actual={sorted(actual_workflows)}")

    for relative in sorted(FORBIDDEN_SOURCE_PATHS):
        if (ROOT / relative).exists():
            errors.append(f"forbidden obsolete source remains: {relative}")

    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SOURCE_SCAN_SUFFIXES:
            continue
        relative = path.relative_to(ROOT)
        if any(part in SOURCE_SCAN_EXCLUDED_ROOTS for part in relative.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in LEGACY_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{label} remains in publishable source: {relative}")


def main() -> int:
    errors: list[str] = []
    verify_source_hygiene(errors)

    if not OUTPUT.is_dir():
        errors.append("_site does not exist")
        return fail(errors)

    for item in REQUIRED_FILES:
        path = OUTPUT / item
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"missing or empty required file: {item}")

    if errors:
        return fail(errors)

    source_pdf = OUTPUT / SOURCE_GUIDE_PDF
    public_pdf = OUTPUT / PUBLIC_GUIDE_PDF
    if source_pdf.stat().st_size != public_pdf.stat().st_size:
        errors.append("published PDF alias size does not match source PDF")
    elif sha256(source_pdf) != sha256(public_pdf):
        errors.append("published PDF alias hash does not match source PDF")

    tracking_page = (OUTPUT / "resources/document.html").read_text(encoding="utf-8", errors="replace")
    for marker in ("G-3DCV21L2RT", "noindex,nofollow", "document-tracking.js"):
        if marker not in tracking_page:
            errors.append(f"tracking page missing required marker: {marker}")

    tracking_script = (OUTPUT / "assets/js/document-tracking.js").read_text(encoding="utf-8", errors="replace")
    for marker in ("pdf_open", "delivery_id", "/assets/pdf/AirAdmin8_AI_Robotics_Support_for_University_Labs.pdf"):
        if marker not in tracking_script:
            errors.append(f"tracking script missing required marker: {marker}")

    if (OUTPUT / "CNAME").read_text(encoding="utf-8").strip() != "robotics.air-admin8.co.jp":
        errors.append("CNAME mismatch")

    robots = (OUTPUT / "robots.txt").read_text(encoding="utf-8")
    if "Sitemap: https://robotics.air-admin8.co.jp/sitemap.xml" not in robots:
        errors.append("robots.txt sitemap mismatch")

    html_files = sorted(
        path for path in OUTPUT.rglob("*.html")
        if "includes" not in path.relative_to(OUTPUT).parts and not is_legacy_redirect(path)
    )
    if not html_files:
        errors.append("no publishable HTML files")

    for path in html_files:
        relative = path.relative_to(OUTPUT)
        text = path.read_text(encoding="utf-8")
        required_markers = [
            'data-shared-layout="header"',
            'data-shared-layout="footer"',
            'class="brand-logo brand-logo-pc"',
            'class="brand-logo brand-logo-sp"',
            'airadmin8-robotics-logo-pc.svg',
            'airadmin8-robotics-logo-sp.svg',
            'airadmin8-robotics-logo-footer.svg',
            'shared-layout.css',
            'data-aa8-brand-icon="true"',
            'property="og:url"',
            '<link rel="canonical" href="https://robotics.air-admin8.co.jp/',
        ]
        for marker in required_markers:
            if marker not in text:
                errors.append(f"missing marker {marker}: {relative}")
        if count_shared_element(text, "header", "header") != 1:
            errors.append(f"shared header count is not 1: {relative}")
        if count_shared_element(text, "footer", "footer") != 1:
            errors.append(f"shared footer count is not 1: {relative}")

    inspect_files = [
        path for path in OUTPUT.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".html", ".css", ".xml", ".js"}
        and not is_legacy_redirect(path)
    ]
    for path in inspect_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        relative = path.relative_to(OUTPUT)
        for label, pattern in LEGACY_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{label} remains: {relative}")

    shared_css = (OUTPUT / "assets/css/shared-layout.css").read_text(encoding="utf-8")
    for marker in (".brand-logo-pc", ".brand-logo-sp", "@media (max-width:980px)"):
        if marker not in shared_css:
            errors.append(f"shared-layout.css missing: {marker}")

    for asset in (
        "assets/img/airadmin8-robotics-logo-pc.svg",
        "assets/img/airadmin8-robotics-logo-sp.svg",
        "assets/img/airadmin8-robotics-logo-footer.svg",
        "assets/img/airadmin8-wordmark.svg",
        "assets/img/airadmin8-robotics-badge.svg",
        "assets/img/favicon-airadmin8.svg",
    ):
        if "<svg" not in (OUTPUT / asset).read_text(encoding="utf-8", errors="replace"):
            errors.append(f"invalid SVG: {asset}")

    meta_path = OUTPUT / "deploy-meta.json"
    if meta_path.exists():
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
            if not data.get("commit_sha"):
                errors.append("deploy-meta.json missing commit_sha")
        except json.JSONDecodeError as exc:
            errors.append(f"invalid deploy-meta.json: {exc}")

    if errors:
        return fail(errors)

    print(f"Release verification PASSED: {len(html_files)} HTML page(s), {len(ALLOWED_WORKFLOWS)} workflow(s), clean publishable source tree.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
