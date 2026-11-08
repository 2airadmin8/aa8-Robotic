"""X2 series: isolated preview candidate uses existing factory and keeps release gates."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from product_factory import ContractError, catalog, render, validate_page_factory

PRODUCT_PATH=ROOT/'tests/fixtures/x2-pilot/product.json'
SOURCE_PATH=ROOT/'tests/fixtures/x2-pilot/source-contract.json'

class X2PilotContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.item=json.loads(PRODUCT_PATH.read_text(encoding='utf8'))
        cls.source=json.loads(SOURCE_PATH.read_text(encoding='utf8'))

    def test_existing_product_master_unchanged_and_no_id_collision(self):
        self.assertEqual(len(catalog(ROOT)),13)
        self.assertNotIn(self.item['id'],[x['id'] for x in catalog(ROOT)])
        self.assertNotEqual(self.item['id'],'agibot-x2-edu')

    def test_exact_35_parameters_and_9_groups(self):
        rows=self.source['source_parameter_entries']
        self.assertEqual(len(rows),35)
        self.assertEqual(len(self.source['parameter_groups']),9)
        self.assertEqual(sum(self.source['parameter_groups'].values()),35)
        self.assertEqual(len(self.item['pageFactory']['specifications']),35)
        for raw,mapped in zip(rows,self.item['pageFactory']['specifications']):
            self.assertIn(raw['youth_raw'],mapped['value'])
            self.assertIn(raw['flagship_raw'],mapped['value'])
            self.assertIn(raw['label_ja'],mapped['label'])
            self.assertEqual(mapped['sourceUrl'],self.source['official_source'])

    def test_generic_image_approval_only_for_preview(self):
        self.assertEqual(self.item['imageStatus'],'original')
        self.assertEqual(self.item['imageApproval'],'user_confirmed_x2_series_generic')
        preview=render(ROOT,self.item,'preview')
        self.assertIn('noindex,nofollow',preview)
        self.assertIn('x2-series-hero.png',preview)
        self.assertNotIn('src="/assets/js/site.js"',preview,
                         "isolated Preview must not send GA4 production page_view")
        with self.assertRaises(ContractError):
            render(ROOT,dict(self.item,pageFactory=dict(self.item['pageFactory'],releaseReady=True)),'candidate')

    def test_negative_approval_fails_closed(self):
        bad=copy.deepcopy(self.item)
        bad.pop('imageApproval')
        with self.assertRaises(ContractError):
            render(ROOT,bad,'preview')
        bad=copy.deepcopy(self.item)
        bad['pageFactory']['inheritSourcePage']="true"
        with self.assertRaises(ContractError):
            render(ROOT,bad,'preview')

    def test_cta_full_inheritance(self):
        content=render(ROOT,self.item,'preview')
        self.assertIn('maker=AGIBOT',content)
        self.assertIn('service=use-case-review',content)
        self.assertIn('source_page=https%3A%2F%2Frobotics.air-admin8.co.jp%2Fproducts%2Fagibot-x2-series.html',content)
        self.assertEqual(content.count('class="g1-cta-card"'),3)
        self.assertEqual(content.count('<tr><th scope="row">'),35)

    def test_cli_draft_preview_only_and_refuses_conflicting_master(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'x2-preview.html'
            cmd=[sys.executable,str(ROOT/'scripts/product_factory.py'),'generate','--draft-product',str(PRODUCT_PATH),'--mode','preview','--output',str(out),'--root',str(ROOT)]
            run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8')
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertTrue(out.is_file())
            self.assertIn('noindex,nofollow',out.read_text('utf8'))
            release=subprocess.run(cmd[:],capture_output=True,text=True,encoding='utf8')
            # repeated output must fail rather than overwrite approved evidence
            self.assertNotEqual(release.returncode,0)
            cmd[cmd.index('preview')]='candidate'
            cmd[-4:]=['--output',str(Path(temp)/'unsafe.html'),'--root',str(ROOT)]
            blocked=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8')
            self.assertNotEqual(blocked.returncode,0)
if __name__=='__main__':
    unittest.main()
