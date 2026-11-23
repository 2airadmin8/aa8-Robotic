#!/usr/bin/env python3
"""Audit shared CSS ownership; reject *new* conflicts without breaking legacy pages.

Canonical CSS owner: assets/css/shared-layout.css. Existing source HTML includes
some historical inline overrides (notably X2 EDU), so the mandatory PR gate
compares normalized CSS rules against a trusted exact base commit. It neither
suppresses those warnings nor turns unchanged legacy debt into a release block.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OWNER = "assets/css/shared-layout.css"
EXCLUDED = {
    ".git", ".github", "_site", "tests", "docs", "ops",
    "node_modules", "test-results", "playwright-report", "vendor",
}
SHARED = re.compile(
    r"\.(?:site-header|header-inner|brand|brand-mark|brand-logo"
    r"(?:-pc|-sp)?|brand-picture|nav|nav-cta|menu|footer|footer-grid|"
    r"footer-links|footer-brand-block|footer-bottom|footer-utility-links|"
    r"aa8-footer-brand|aa8-main-logo)(?=[\s.#\[:>,+~]|$)"
)
STYLE = re.compile(r"<style\b[^>]*>(.*?)</style\s*>", re.I | re.S)
HEX_SHA = re.compile(r"[0-9a-f]{40}\Z")


def normalize(value: str) -> str:
    value = re.sub(r"/\*.*?\*/", "", value, flags=re.S)
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"\s*([:;{}(),])\s*", r"\1", value)
    value = re.sub(r"@(media|supports|container)\s+\(", r"@\1(", value)
    return value.rstrip(";")


def css_rules(text: str, context: str = "") -> list[tuple[str, str, str]]:
    """Extract normalized shared selector declarations, respecting nested media."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    records: list[tuple[str, str, str]] = []
    pos = 0
    while True:
        start = text.find("{", pos)
        if start < 0:
            break
        preamble = text[pos:start].strip()
        depth, end = 1, start + 1
        quote = ""
        while end < len(text) and depth:
            c = text[end]
            if quote:
                if c == quote and text[end - 1] != "\\":
                    quote = ""
            elif c in ("'", '"'):
                quote = c
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            end += 1
        if depth:
            break
        body = text[start + 1:end - 1]
        head = preamble.rsplit(";", 1)[-1].strip()
        label = normalize(head)
        if head.startswith(("@media", "@supports", "@container", "@layer")):
            if not re.match(r"@media\s*\(?print\b", head, re.I):
                records.extend(css_rules(body, context + "|" + label))
        elif head and not head.startswith("@"):
            for selector in head.split(","):
                selector = normalize(selector)
                if SHARED.search(selector):
                    record = (context, selector, normalize(body))
                    records.append(record)
        pos = end
    return records


def inventory(root: Path) -> dict[str, Counter]:
    """Only existing publishable sources; never fixtures, generated _site or includes."""
    result: dict[str, Counter] = {}
    css = root / "assets" / "css"
    for file in sorted(css.rglob("*.css")):
        rel = file.relative_to(root).as_posix()
        if rel == OWNER:
            continue
        rules = css_rules(file.read_text(encoding="utf-8", errors="replace"))
        if rules:
            result[rel] = Counter(("css", *r) for r in rules)
    for file in sorted(root.rglob("*.html")):
        rel = file.relative_to(root)
        if any(p in EXCLUDED for p in rel.parts):
            continue
        if "includes" in rel.parts and rel.as_posix() not in {
            "includes/site-header.html", "includes/site-footer.html"
        }:
            continue
        rules = []
        for match in STYLE.finditer(file.read_text(encoding="utf-8", errors="replace")):
            rules.extend(css_rules(match.group(1)))
        if rules:
            result[rel.as_posix()] = Counter(("inline", *r) for r in rules)
    return result


def base_file(root: Path, sha: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{sha}:{path}"], cwd=root,
        capture_output=True, timeout=15,
    )
    if result.returncode:
        return ""  # new source path: no historical exception
    return result.stdout.decode("utf-8", errors="replace")


def baseline_rules(root: Path, sha: str, path: str) -> Counter:
    blob = base_file(root, sha, path)
    if not blob:
        return Counter()
    if path.endswith(".css"):
        return Counter(("css", *r) for r in css_rules(blob))
    results = []
    for match in STYLE.finditer(blob):
        results.extend(css_rules(match.group(1)))
    return Counter(("inline", *r) for r in results)


def new_conflicts(root: Path, sha: str, entries: dict[str, Counter] | None = None) -> list[str]:
    if not HEX_SHA.fullmatch(sha):
        raise ValueError("HOLD: invalid exact base SHA")
    check = subprocess.run(
        ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
        cwd=root, capture_output=True, timeout=15,
    )
    if check.returncode:
        raise ValueError("HOLD: trusted base commit unavailable")
    entries = inventory(root) if entries is None else entries
    fresh: list[str] = []
    for path, current in sorted(entries.items()):
        prev = baseline_rules(root, sha, path)
        for rule, count in (current - prev).items():
            origin, media, selector, declaration = rule
            digest = hashlib.sha256(repr(rule).encode()).hexdigest()[:12]
            fresh.append(
                f"{path}: NEW shared CSS owner conflict [{origin}] "
                f"{media} {selector} fingerprint={digest} count={count}"
            )
    return fresh


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict-new", action="store_true")
    parser.add_argument("--base-sha")
    args = parser.parse_args()
    root = ROOT
    if not (root / OWNER).is_file():
        print("ERROR: canonical shared-layout.css missing")
        return 2
    findings = inventory(root)
    count = sum(sum(c.values()) for c in findings.values())
    if count:
        print(f"WARNING: {count} legacy-or-new shared CSS declarations in "
              f"{len(findings)} non-owner files; not claiming zero warnings")
        for path, counter in findings.items():
            print(f"WARNING: {path}: {sum(counter.values())} shared owner declaration(s)")
    else:
        print("Shared CSS owner audit: no non-owner selector collisions")
    if args.strict_new:
        if not args.base_sha:
            print("HOLD: strict-new requires exact trusted base SHA")
            return 2
        try:
            conflicts = new_conflicts(root, args.base_sha, findings)
        except (ValueError, subprocess.TimeoutExpired) as exc:
            print(str(exc))
            return 2
        for violation in conflicts:
            print("ERROR: " + violation)
        if conflicts:
            print(f"HOLD: {len(conflicts)} new/changed shared CSS ownership rule(s)")
            return 1
        print(f"PASS: zero new shared CSS conflicts vs base {args.base_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
