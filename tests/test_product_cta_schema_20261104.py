"""Regression: Product facts from original approved Master and correct general CTA."""
import json
import re
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import inject_structured_data as schema
from product_factory import catalog

LEGACY={
 "unitree-g1":"Unitree", "unitree-g1-d":"Unitree",
 "unitree-go2":"Unitree", "agibot-x2-edu":"AgiBot", "agibot-g2":"AgiBot",
}
RECENT=("unitree-g1-plus","unitree-h2-d","unitree-h2","unitree-h2-x","unitree-h2-plus","agibot-a3-ultra")
class Anchors(HTMLParser):
 def __init__(self): super().__init__();self.anchors=[]
 def handle_starttag(self,tag,attrs):
  if tag=="a": self.anchors.append(dict(attrs))

class ProductCtaSchema20261104(unittest.TestCase):
 def test_legacy_five_get_exactly_one_verified_product_schema(self):
  items=catalog(ROOT)
  for slug,brand in LEGACY.items():
   with self.subTest(slug=slug):
    rel=Path("products")/(slug+".html")
    source=(ROOT/rel).read_text(encoding="utf-8")
    built=schema.process_html(source,rel)
    matches=re.findall(r'<script id="product-facts-schema" type="application/ld\+json">(.*?)</script>',built)
    self.assertEqual(len(matches),1,slug)
    doc=json.loads(matches[0])
    original=[p for p in items if p.get("detailPage")==rel.as_posix()]
    self.assertEqual(len(original),1)
    product=original[0]
    self.assertEqual(doc["@type"],"Product")
    self.assertEqual(doc["name"],product["name"])
    self.assertEqual(doc["brand"]["name"],brand)
    self.assertEqual(doc["image"],["https://robotics.air-admin8.co.jp/"+product["image"]])
    self.assertEqual(product["imageStatus"],"official")
    self.assertTrue((ROOT/product["image"]).is_file())
    self.assertEqual(doc["url"],f"https://robotics.air-admin8.co.jp/{rel.as_posix()}")
    self.assertEqual(doc["mainEntityOfPage"]["@id"],doc["url"]+"#page")
    for prohibited in ["offers","aggregateRating","review","sku","availability"]:
     self.assertNotIn(prohibited,doc)
    self.assertTrue(doc["description"])
    self.assertEqual(doc["category"],
      "四足歩行ロボット" if slug=="unitree-go2" else
      "移動マニピュレーションロボット" if slug=="agibot-g2" else
      "ヒューマノイドロボット")

 def test_recent_six_keep_one_product_schema_after_build(self):
  for slug in RECENT:
   with self.subTest(slug=slug):
    rel=Path("products")/(slug+".html")
    result=schema.process_html((ROOT/rel).read_text(encoding="utf-8"),rel)
    self.assertEqual(result.count('id="product-facts-schema"'),1)
    self.assertEqual(result.count('"@type":"Product"'),1)

 def test_generic_research_ctas_preselect_conditions_not_procurement(self):
  targets={
    "unitree-g1":("Unitree G1","Unitree"),
    "unitree-g1-plus":("Unitree G1+","Unitree"),
    "unitree-h2":("Unitree H2","Unitree"),
    "unitree-h2-x":("Unitree H2-X","Unitree"),
    "agibot-a3-ultra":("AGIBOT A3 Ultra","AGIBOT"),
  }
  for slug,(name,maker) in targets.items():
   with self.subTest(slug=slug):
    data=(ROOT/"products"/(slug+".html")).read_text(encoding="utf-8")
    parser=Anchors();parser.feed(data)
    hero=[a for a in parser.anchors if "g1-button" in a.get("class","") and
       a.get("href","").startswith("/contact.html?product=")]
    self.assertEqual(len(hero),1,slug)
    params=parse_qs(urlsplit(hero[0]["href"]).query)
    self.assertEqual(params.get("product"),[name])
    self.assertEqual(params.get("maker"),[maker])
    self.assertNotEqual(params.get("service"),["university-procurement"])
    self.assertNotIn("source_page",params)
  h2x=(ROOT/"products/unitree-h2-x.html").read_text(encoding="utf-8")
  self.assertNotIn("何を検証するかから、H2を選ぶ。",h2x)
  self.assertIn("何を検証するかから、H2-Xを選ぶ。",h2x)
  x=Anchors();x.feed(h2x)
  all_h2x=[a["href"] for a in x.anchors if a.get("href","").startswith("/contact.html?product=Unitree%20H2-X")]
  self.assertEqual(len(all_h2x),2)
  self.assertTrue(all("maker=Unitree" in href for href in all_h2x))

 def test_intentional_procurement_and_catalog_are_unchanged(self):
  g1p=(ROOT/"products/unitree-g1-plus.html").read_text(encoding="utf-8")
  self.assertIn("product=Unitree%20G1%2B%20EDU&amp;service=university-procurement&amp;maker=Unitree",g1p)
  g1=(ROOT/"products/unitree-g1.html").read_text(encoding="utf-8")
  self.assertIn("service=catalog&amp;maker=Unitree",g1)

if __name__=="__main__":unittest.main()
