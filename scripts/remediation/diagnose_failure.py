#!/usr/bin/env python3
"""Classify known CI/production failures for deterministic remediation."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RULES = [
    ("HEADER_SYNC", 0.99, [r"brand-logo", r"shared header", r"header.*missing", r"logo.*missing"]),
    ("CANONICAL", 0.98, [r"canonical", r"aa8-Robotic"]),
    ("SITEMAP", 0.97, [r"sitemap"]),
    ("ROBOTS", 0.97, [r"robots\.txt", r"robots"]),
    ("ASSET_404", 0.95, [r"404", r"asset.*missing", r"logo.*200"]),
    ("DEPLOY_SHA", 0.99, [r"SHA mismatch", r"deploy-meta", r"Production commit"]),
    ("TRANSIENT", 0.92, [r"timeout", r"timed out", r"Could not resolve host", r"connection reset"]),
]


def classify(text: str) -> dict[str, object]:
    for category, confidence, patterns in RULES:
        if any(re.search(pattern, text, re.I) for pattern in patterns):
            return {"category": category, "confidence": confidence}
    return {"category": "UNKNOWN", "confidence": 0.0}


def main() -> int:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    text = source.read_text(encoding="utf-8", errors="replace") if source else sys.stdin.read()
    result = classify(text)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
