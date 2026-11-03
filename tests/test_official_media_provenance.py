"""Manufacturer image release guard; source/sha/model must all match."""
from __future__ import annotations
import hashlib
import json
import struct
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
MODELS={'agibot-g2','agibot-x2-edu','limx-oli','unitree-go2-edu','tianji-marvin'}
VALID_SOURCE_HOSTS={
  'agibot-g2':{'store.agibot.com'},
  'agibot-x2-edu':{'store.agibot.com'},
  'limx-oli':{'www.limxdynamics.com','limx-video-oss.limxdynamics.com'},
  'unitree-go2-edu':{'www.unitree.com'},
  'tianji-marvin':{'en.tianjizn.com'},
}

class OfficialMediaTests(unittest.TestCase):
 def setUp(self):
  self.master={p['id']:p for p in json.loads((ROOT/'data/products.json').read_text(encoding='utf8'))['products']}
  self.items={p['id']:p for p in json.loads((ROOT/'data/official-media-provenance.json').read_text(encoding='utf8'))['products']}
 def test_exact_five_products_and_sources(self):
  self.assertEqual(set(self.items),MODELS)
  for pid,p in self.items.items():
   with self.subTest(pid=pid):
    m=self.master[pid]
    self.assertEqual(m['imageStatus'],'official')
    self.assertEqual(m['image'],p['localPath'])
    self.assertEqual(m['imageSourcePage'],p['sourcePage'])
    self.assertEqual(m['imageAssetSourceUrl'],p['sourceAssetUrl'])
    self.assertNotEqual(m['imageAlt'].find('参考イメージ'),0)
    self.assertIn(urlparse(p['sourcePage']).hostname,VALID_SOURCE_HOSTS[pid])
    self.assertIn(urlparse(p['sourceAssetUrl']).hostname,VALID_SOURCE_HOSTS[pid])
    self.assertNotIn('placeholder',m['imageStatus'])
    self.assertNotIn('/robot-',m['image'])
 def test_real_binary_magic_sizes_and_sha256(self):
  for pid,p in self.items.items():
   with self.subTest(pid=pid):
    file=ROOT / p['localPath']
    self.assertTrue(file.is_file(),str(file))
    raw=file.read_bytes()
    self.assertGreater(len(raw),15000)
    self.assertEqual(hashlib.sha256(raw).hexdigest(),p['sha256'])
    if file.suffix=='.jpg':self.assertTrue(raw.startswith(b'\xff\xd8\xff'))
    elif file.suffix=='.png':self.assertTrue(raw.startswith(b'\x89PNG\r\n\x1a\n'))
    elif file.suffix=='.webp':self.assertTrue(raw.startswith(b'RIFF') and raw[8:12]==b'WEBP')
    else:self.fail('Unsupported extension '+str(file))
 def test_sparse_product_heroes_are_replaced_and_cited(self):
  for pid in MODELS-{'agibot-x2-edu'}:
   with self.subTest(pid=pid):
    p=self.master[pid]
    content=(ROOT / p['detailPage']).read_text(encoding='utf8')
    self.assertIn('../'+p['image'],content)
    self.assertIn('alt="'+p['imageAlt']+'"',content)
    self.assertNotIn('の参考イメージ',content.split('../'+p['image'],1)[1].split('</figure>',1)[0])
    self.assertIn('メーカー公式写真',content)
    self.assertIn(p['imageSourcePage'],content)
    self.assertNotIn('src="../assets/img/robot-',content)
 def test_x2_edu_preserves_rich_assembly_design(self):
  m=self.master['agibot-x2-edu']
  html=(ROOT / m['detailPage']).read_text(encoding='utf8')
  self.assertIn('/assets/x2-edu-body-clean.png',html)
  self.assertIn('id="assembly"',html)
  self.assertNotIn('robot-humanoid.svg',html)

if __name__=='__main__': unittest.main()
