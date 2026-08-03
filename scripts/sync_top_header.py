#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'index.html'
HEADER = ROOT / 'includes' / 'site-header.html'

text = INDEX.read_text(encoding='utf-8')
header = HEADER.read_text(encoding='utf-8').strip()
pattern = re.compile(r'<header\b(?=[^>]*\bclass=["\'][^"\']*\bsite-header\b[^"\']*["\'])[^>]*>.*?</header>', re.I | re.S)
if not pattern.search(text):
    raise SystemExit('TOP header not found')
new_text = pattern.sub(header, text, count=1)
if 'brand-logo-pc' not in new_text or 'brand-logo-sp' not in new_text:
    raise SystemExit('TOP logo markup sync failed')
if new_text != text:
    INDEX.write_text(new_text, encoding='utf-8', newline='\n')
    print('TOP header synchronized from includes/site-header.html')
else:
    print('TOP header already synchronized')
