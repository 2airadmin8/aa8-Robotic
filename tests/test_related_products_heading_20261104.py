"""All existing related-product blocks share the approved factory heading."""
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PAGES=(
 'unitree-g1','unitree-g1-plus','unitree-h2','unitree-h2-d',
 'unitree-h2-x','unitree-h2-plus','agibot-a3-ultra',
)
class BlockParser(HTMLParser):
 def __init__(self):
  super().__init__();self.tag_count=0;self.links=[]
 def handle_starttag(self,tag,attrs):
  if tag=='a':
   x=dict(attrs)
   if x.get('href','').startswith('/products'):
    self.links.append(x['href'])

class RelatedHeadingContract(unittest.TestCase):
 def test_related_title_exactly_once_on_each_existing_related_section(self):
  for slug in PAGES:
   with self.subTest(page=slug):
    raw=(ROOT/'products'/f'{slug}.html').read_text(encoding='utf-8')
    self.assertEqual(raw.count('RELATED PRODUCTS'),1,slug)
    self.assertIn('あわせて比較したい製品',raw)
    if slug=='unitree-g1':
     self.assertEqual(raw.count('あわせて比較したい製品'),2,
      'Preserve the original separate PC/SP visual spans')
    else:
     self.assertEqual(raw.count('あわせて比較したい製品'),1)
    self.assertRegex(raw,r'class="[^"]*(?:related|g1-factory-related)[^"]*"')
 def test_factory_template_is_ssot_and_existing_pages_match(self):
  markup=(ROOT/'scripts/templates/g1_factory_v1.html').read_text(encoding='utf-8')
  heading='<p class="g1-kicker">RELATED PRODUCTS</p><h2>あわせて比較したい製品</h2>'
  self.assertEqual(markup.count(heading),1)
  for slug in ('agibot-a3-ultra','unitree-h2-plus'):
   self.assertEqual((ROOT/'products'/f'{slug}.html').read_text(encoding='utf-8').count(heading),1)
 def test_related_links_and_media_remain_present(self):
  for slug in PAGES:
   with self.subTest(page=slug):
    raw=(ROOT/'products'/f'{slug}.html').read_text(encoding='utf-8')
    parser=BlockParser();parser.feed(raw)
    self.assertGreaterEqual(len(parser.links),3,slug)
    for href in parser.links:
     self.assertFalse(href.startswith('/products//'))
 def test_no_title_duplication_for_other_pages(self):
  for slug in ('unitree-go2','agibot-g2','unitree-g1-d','agibot-x2-edu'):
   raw=(ROOT/'products'/f'{slug}.html').read_text(encoding='utf-8')
   self.assertEqual(raw.count('RELATED PRODUCTS'),0)

if __name__=='__main__':unittest.main()
