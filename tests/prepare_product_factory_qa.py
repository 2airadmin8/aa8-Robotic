#!/usr/bin/env python3
"""CI-only preview in ephemeral _site; NEVER writes to a public source page."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from build_site import build_html
from product_factory import render
from product_factory_fixture import sample_product

destination = ROOT / "_site" / "products" / "factory-qa.html"
if not (ROOT / "_site" / "index.html").exists():
    raise SystemExit("Factory QA preview requires CI build output")
if destination.exists():
    raise SystemExit("Factory QA output already exists; refuse overwrite")
text = build_html(render(ROOT, sample_product(), "preview"), Path("products/factory-qa.html"))
if 'content="noindex,nofollow"' not in text or 'data-product-factory="g1-v1"' not in text:
    raise SystemExit("FAIL: generated QA preview lost its safety markers")
destination.write_text(text, encoding="utf-8")
print(f"CI-ONLY isolated product factory QA page generated at {destination}")
