#!/usr/bin/env python3
"""Validate local href/src targets in the built static site."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

PUBLIC_PATH = "/aa8-Robotic/"
PUBLIC_HOST = "robotics.air-admin8.co.jp"


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.targets: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag in {"a", "link"} and values.get("href"):
            self.targets.append(("href", values["href"]))
        if tag in {"img", "script", "source"} and values.get("src"):
            self.targets.append(("src", values["src"]))


def resolve_target(output: Path, page: Path, raw: str) -> Path | None:
    raw = raw.strip()
    if not raw or raw.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None

    parsed = urlsplit(raw)
    if parsed.scheme in {"http", "https"}:
        if parsed.netloc != PUBLIC_HOST:
            return None
        path_text = parsed.path
    elif parsed.scheme or parsed.netloc:
        return None
    else:
        path_text = parsed.path

    if not path_text:
        return None

    path_text = unquote(path_text)
    if path_text.startswith(PUBLIC_PATH):
        relative = path_text[len(PUBLIC_PATH):]
        candidate = output / relative
    elif path_text.startswith("/"):
        return None
    else:
        candidate = page.parent / path_text

    if path_text.endswith("/"):
        candidate = candidate / "index.html"

    return candidate.resolve()


def validate_internal_links(output: Path) -> list[str]:
    errors: list[str] = []
    output_resolved = output.resolve()

    for page in sorted(output.rglob("*.html")):
        parser = LinkParser()
        parser.feed(page.read_text(encoding="utf-8", errors="replace"))
        for attr, raw in parser.targets:
            target = resolve_target(output, page, raw)
            if target is None:
                continue
            try:
                target.relative_to(output_resolved)
            except ValueError:
                errors.append(f"Path escapes site root: {page.relative_to(output)} {attr}={raw}")
                continue
            if not target.is_file():
                errors.append(f"Broken local target: {page.relative_to(output)} {attr}={raw}")

    return errors


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    problems = validate_internal_links(root / "_site")
    for problem in problems:
        print(f"LINK ERROR: {problem}")
    print(f"Internal link validation completed with {len(problems)} error(s).")
    raise SystemExit(1 if problems else 0)
