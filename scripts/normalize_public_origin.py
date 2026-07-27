#!/usr/bin/env python3
"""Normalize legacy GitHub Pages URLs in the built public artifact.

The repository is hosted on GitHub Pages internally, but the public site is
served through robotics.air-admin8.co.jp. This post-build guard prevents old
GitHub Pages URLs from leaking into canonical metadata, JSON-LD, social tags,
runtime SEO JavaScript, sitemap-like text assets, or other public text files.
"""

from __future__ import annotations

from pathlib import Path

LEGACY_BASE = "https://2airadmin8.github.io/aa8-Robotic/"
PUBLIC_BASE = "https://robotics.air-admin8.co.jp/aa8-Robotic/"
TEXT_SUFFIXES = {".html", ".js", ".json", ".xml", ".txt", ".webmanifest", ".css"}


def normalize_public_origin(output: Path) -> tuple[int, list[str]]:
    changed = 0
    errors: list[str] = []

    if not output.is_dir():
        return 0, ["_site directory does not exist"]

    for path in sorted(output.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name != "site.webmanifest":
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        if LEGACY_BASE in text:
            path.write_text(text.replace(LEGACY_BASE, PUBLIC_BASE), encoding="utf-8")
            changed += 1

    for path in sorted(output.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name != "site.webmanifest":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if LEGACY_BASE in text:
            errors.append(f"Legacy public origin remains: {path.relative_to(output)}")

    return changed, errors


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    count, problems = normalize_public_origin(root / "_site")
    for problem in problems:
        print(f"PUBLIC ORIGIN ERROR: {problem}")
    print(f"Public origin normalized in {count} built file(s).")
    raise SystemExit(1 if problems else 0)
