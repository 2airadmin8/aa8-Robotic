#!/usr/bin/env python3
"""Enforce single ownership of shared Header/Footer CSS.

Only assets/css/shared-layout.css may define selectors for the shared
Header, Footer, brand logos, or shared navigation containers.
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


def main() -> int:
    if not OWNER.is_file():
        print("ERROR: assets/css/shared-layout.css is missing")
        return 1

    errors: list[str] = []
    for path in sorted(CSS_ROOT.rglob("*.css")):
        if path == OWNER:
            continue
        text = strip_comments(path.read_text(encoding="utf-8", errors="replace"))
        relative = path.relative_to(ROOT)
        for label, pattern in FORBIDDEN_SELECTOR_PATTERNS.items():
            match = pattern.search(text)
            if match:
                line = text.count("\n", 0, match.start()) + 1
                errors.append(
                    f"{relative}:{line}: shared CSS ownership violation ({label}); "
                    "move this rule to assets/css/shared-layout.css"
                )

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Shared CSS ownership FAILED with {len(errors)} violation(s).")
        return 1

    print("Shared CSS ownership PASSED:")
    print("- shared-layout.css is the only Header/Footer CSS owner")
    print("- page-specific CSS cannot override shared brand/navigation/layout selectors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
