#!/usr/bin/env python3
# Guard the compare-catalog exclusion in static pre-rendering, not just client JS.
from pathlib import Path
import importlib.util
import json
import re
import sys

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from prerender_product_cards import render_html

source=(root/'products.html').read_text(encoding='utf-8')
data=json.loads((root/'data/products.json').read_text(encoding='utf-8'))
products=data['products']
output,count=render_html(source,Path('products.html'),products)
assert count==1
assert 'id="limx-oli"' not in output
assert output.count('class="product-card research-product-card"')==12
assert 'id="unitree-g1-d"' in output and 'id="unitree-g1"' in output
assert next(p for p in products if p['id']=='limx-oli')['visibility']=='public'
home=(root/'index.html').read_text(encoding='utf-8')
home_output,count=render_html(home,Path('index.html'),products)
assert count==1 and home_output.count('class="product-card research-product-card"')==3
# The standard build will emit these cards before JavaScript. Manual rendering
# may still run afterwards, but it must not duplicate the initial HTML.
assert render_html(home_output,Path('index.html'),products)==(home_output,1)
featured_match=re.search(r'\bdata-featured-products="([^"]+)"', home)
assert featured_match
featured=featured_match[1].split()
actual=re.findall(r'<article id="([^"]+)" class="product-card research-product-card"',home_output)
assert actual==featured
for broken in (
    featured[:-1],
    featured[:-1]+[featured[0]],
    featured[:-1]+['missing-product-fixture'],
):
    broken_home=home[:featured_match.start(1)]+' '.join(broken)+home[featured_match.end(1):]
    try:
        render_html(broken_home,Path('index.html'),products)
    except ValueError as exc:
        assert 'unique public IDs matching data-limit' in str(exc)
    else:
        raise AssertionError('Invalid homepage featured configuration was accepted')
print('Product catalog exclusion SSOT PASS: 12 compare cards; LimX Oli data preserved; home 3 ordered and idempotent')
