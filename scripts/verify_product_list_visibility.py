#!/usr/bin/env python3
# Guard the compare-catalog exclusion in static pre-rendering, not just client JS.
from pathlib import Path
import importlib.util
import json
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
assert output.count('class="product-card research-product-card"')==11
assert 'id="unitree-g1-d"' in output and 'id="unitree-g1"' in output
assert next(p for p in products if p['id']=='limx-oli')['visibility']=='public'
home=(root/'index.html').read_text(encoding='utf-8')
home_output,count=render_html(home,Path('index.html'),products)
assert count==1 and home_output.count('class="product-card research-product-card"')==3
print('Product catalog exclusion SSOT PASS: 11 compare cards; LimX Oli data preserved; home 3 unaffected')
