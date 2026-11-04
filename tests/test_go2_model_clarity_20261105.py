import unittest
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,parse_qs
ROOT=Path(__file__).resolve().parents[1]
class H(HTMLParser):
 def __init__(self):super().__init__();self.anchors=[];self.ids=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if "id" in a:self.ids.append(a["id"])
  if tag=="a":self.anchors.append(a)
class Go2ResearchGuidance(unittest.TestCase):
 def setUp(self):
  self.html=(ROOT/"products/unitree-go2.html").read_text(encoding="utf-8")
  self.a=H();self.a.feed(self.html)
 def test_one_accessible_model_guidance_section(self):
  self.assertEqual(self.a.ids.count("go2-model-guidance"),1)
  self.assertIn('aria-labelledby="go2-model-heading"',self.html)
  self.assertIn('AIR／PRO／EDU',self.html)
  self.assertIn('R&amp;D／R&amp;D Plus',self.html)
 def test_sales_model_queries_distinct_and_encoded(self):
  links=[a["href"] for a in self.a.anchors if "href" in a and "theme=research" in a["href"]]
  self.assertEqual(len(links),2)
  self.assertEqual([parse_qs(urlsplit(x).query)["product"][0] for x in links],["Unitree Go2 R&D","Unitree Go2 R&D Plus"])
  self.assertTrue(all(parse_qs(urlsplit(x).query)["maker"]==["Unitree"] for x in links))
 def test_original_edu_contract_and_no_unapproved_pdf(self):
  self.assertIn('data-product-id="unitree-go2-edu"',self.html)
  self.assertIn('product=Unitree%20Go2%20EDU&theme=inspection&maker=Unitree',self.html)
  self.assertNotIn('download=',self.html)
  self.assertNotIn('data-document-type="product-catalog"',self.html)
