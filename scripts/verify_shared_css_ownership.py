#!/usr/bin/env python3
"""Report shared Header/Footer CSS ownership issues without blocking deploy.

Only assets/css/shared-layout.css should define shared Header, Footer,
brand, navigation, and menu selectors. Print-only hiding is allowed.
Missing shared-layout.css remains a fatal release error.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS_ROOT = ROOT / "assets" / "css"
OWNER = CSS_ROOT / "shared-layout.css"

FORBIDDEN_SELECTOR_PATTERNS = {
    "site header": re.compile(r"(^|[,{\s])\.site-header(?=[\s\[:.#>{,+~]|$)", re.M),
    "header inner": re.compile(r"(^|[,{\s])\.header-inner(?=[\s\[:.#>{,+~]|$)", re.M),
    "header brand link": re.compile(r"(^|[,{\s])\.brand(?=[\s\[:.#>{,+~]|$)", re.M),
    "header brand mark": re.compile(r"(^|[,{\s])\.brand-mark(?=[\s\[:.#>{,+~]|$)", re.M),
    "header brand logo": re.compile(r"(^|[,{\s])\.brand-logo(?:-pc|-sp)?(?=[\s\[:.#>{,+~]|$)", re.M),
    "legacy brand picture": re.compile(r"(^|[,{\s])\.brand-picture(?=[\s\[:.#>{,+~]|$)", re.M),
    "shared navigation": re.compile(r"(^|[,{\s])\.nav(?=[\s\[:.#>{,+~]|$)", re.M),
    "shared navigation CTA": re.compile(r"(^|[,{\s])\.nav-cta(?=[\s\[:.#>{,+~]|$)", re.M),
    "shared menu button": re.compile(r"(^|[,{\s])\.menu(?=[\s\[:.#>{,+~]|$)", re.M),
    "footer root": re.compile(r"(^|[,{\s])\.footer(?=[\s\[:.#>{,+~]|$)", re.M),
    "footer grid": re.compile(r"(^|[,{\s])\.footer-grid(?=[\s\[:.#>{,+~]|$)", re.M),
    "footer links": re.compile(r"(^|[,{\s])\.footer-links(?=[\s\[:.#>{,+~]|$)", re.M),
    "footer brand block": re.compile(r"(^|[,{\s])\.footer-brand-block(?=[\s\[:.#>{,+~]|$)", re.M),
    "footer bottom": re.compile(r"(^|[,{\s])\.footer-bottom(?=[\s\[:.#>{,+~]|$)", re.M),
    "footer utility links": re.compile(r"(^|[,{\s])\.footer-utility-links(?=[\s\[:.#>{,+~]|$)", re.M),
    "footer brand link": re.compile(r"(^|[,{\s])\.aa8-footer-brand(?=[\s\[:.#>{,+~]|$)", re.M),
    "footer logo": re.compile(r"(^|[,{\s])\.aa8-main-logo(?=[\s\[:.#>{,+~]|$)", re.M),
}


def strip_comments(text: str) -> str:
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def strip_media_block(text: str, media_name: str) -> str:
    pattern = re.compile(rf"@media\s+{re.escape(media_name)}\s*\{{", re.I)
    while True:
        match = pattern.search(text)
        if not match:
            return text
        depth = 1
        index = match.end()
        while index < len(text) and depth:
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
            index += 1
        if depth:
            return text
        text = text[: match.start()] + "\n" + text[index:]


def main() -> int:
    if not OWNER.is_file():
        print("ERROR: assets/css/shared-layout.css is missing")
        return 1

    warnings: list[str] = []
    for path in sorted(CSS_ROOT.rglob("*.css")):
        if path == OWNER:
            continue
        text = strip_comments(path.read_text(encoding="utf-8", errors="replace"))
        text = strip_media_block(text, "print")
        relative = path.relative_to(ROOT)
        for label, pattern in FORBIDDEN_SELECTOR_PATTERNS.items():
            match = pattern.search(text)
            if match:
                line = text.count("\n", 0, match.start()) + 1
                warnings.append(
                    f"{relative}:{line}: shared CSS ownership warning ({label}); "
                    "prefer assets/css/shared-layout.css"
                )

    if warnings:
        for warning in warnings:
            print(f"WARNING: {warning}")
        print(f"Shared CSS ownership completed with {len(warnings)} warning(s); deploy continues.")
        return 0

    print("Shared CSS ownership PASSED:")
    print("- shared-layout.css is the only screen Header/Footer CSS owner")
    print("- print-only hiding is allowed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
