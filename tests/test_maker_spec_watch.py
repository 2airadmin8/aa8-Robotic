"""Offline deterministic maker source drift tests (network checked separately)."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import maker_spec_watch as maker
import json


class MakerSourceWatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=maker.load_contract(ROOT/'tests/fixtures/a2-factory/maker-live-contract.json')
        cls.product=json.loads((ROOT/'tests/fixtures/a2-factory/product.json').read_text())
        cls.parsed={
            'models':cls.contract['models'],
            'categories':[{'name':g['source_name'],
                'rows':[{'source_label':r['source_label'],'models':dict(r['models'])}
                        for r in g['rows']]} for g in cls.contract['categories']]
        }

    def test_two_models_4_groups_37_rows_74_individual_cells(self):
        parsed=copy.deepcopy(self.parsed)
        self.assertEqual(parsed['models'],['A2','A2-PRO'])
        self.assertEqual([len(g['rows']) for g in parsed['categories']],[10,15,9,3])
        self.assertEqual(len(maker.flatten(parsed)),74)
        self.assertEqual(maker.compare(parsed,self.contract),[])
        maker.verify_display(self.product,self.contract,parsed)

    def test_detect_real_value_delta_per_model_cell(self):
        parsed=copy.deepcopy(self.parsed)
        parsed['categories'][0]['rows'][4]['models']['A2']='About 43kg'
        drift=maker.compare(parsed,self.contract)
        self.assertEqual(len(drift),1)
        self.assertEqual(drift[0]['parameter_id'],'電池装着重量')
        self.assertEqual(drift[0]['model'],'A2')
        self.assertEqual(drift[0]['before'],'About 42kg')
        self.assertEqual(drift[0]['after'],'About 43kg')

    def test_silent_reordering_rejected(self):
        parsed=copy.deepcopy(self.parsed)
        rows=parsed['categories'][0]['rows']
        rows[0],rows[1]=rows[1],rows[0]
        with self.assertRaisesRegex(ValueError,'identity/order'):
            maker.compare(parsed,self.contract)

    def test_extra_missing_row_or_model_rejected(self):
        for kind in ['missing','extra','model']:
            with self.subTest(kind=kind):
                parsed=copy.deepcopy(self.parsed)
                if kind=='missing':
                    parsed['categories'][0]['rows'].pop()
                if kind=='extra':
                    parsed['categories'][0]['rows'].append(copy.deepcopy(parsed['categories'][0]['rows'][0]))
                if kind=='model':
                    parsed['models']=['A2','FAKE']
                with self.assertRaisesRegex(ValueError,'SOURCE_HOLD'):
                    maker.compare(parsed,self.contract)

    def test_japanese_display_cannot_disagree_with_saved_provenance(self):
        product=copy.deepcopy(self.product)
        product['pageFactory']['specifications'][4]['models']['A2']='約45 kg'
        with self.assertRaisesRegex(ValueError,'DISPLAY_HOLD'):
            maker.verify_display(product,self.contract,self.parsed)

    def test_source_host_must_not_be_unverified_mirror_or_internal(self):
        for url in ['https://unitree-robot.com/mobile/A2/index.html',
                    'http://www.unitree.com/A2/',
                    'https://www.unitree.com.evil.org/A2/',
                    'https://127.0.0.1/A2/',
                    'https://www.unitree.com/A2/?admin=1']:
            with self.subTest(url=url):
                with self.assertRaisesRegex(ValueError,'SOURCE_HOLD'):
                    maker.safe_url(url)
        maker.safe_url('https://www.unitree.com/A2/')

    def test_new_products_are_blocked_if_source_contract_missing(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            f=root/"tests/fixtures/brandnew-product"
            f.mkdir(parents=True)
            (f/"product.json").write_text(json.dumps({
                "id":"brandnew-product","pageFactory":{"officialSource":"https://www.unitree.com/A2/"}
            }))
            with self.assertRaisesRegex(ValueError,"lacks maker-live-contract"):
                maker.audit_new_intake(root)

    def test_generic_maker_html_table_adapter_requires_approved_structure(self):
        contract={'adapter':'html-table-v1','table_id':'model-specs',
                  'group_class':'maker-group','models':['Base','Pro']}
        raw=b'<table id="model-specs"><tr><th>X</th><th>Base</th><th>Pro</th></tr><tr class="maker-group"><th colspan="3">Mechanical</th></tr><tr><th>Weight</th><td>2kg</td><td>3kg</td></tr></table>'
        result=maker.parse_source(raw,contract)
        self.assertEqual(result['models'],['Base','Pro'])
        self.assertEqual(result['categories'][0]['rows'][0]['models']['Pro'],'3kg')
        with self.assertRaisesRegex(ValueError,'SOURCE_HOLD'):
            maker.parse_source(b'<html><p>Loading...</p></html>',contract)

    def test_stage_changed_raw_cell_into_isolated_proposal_never_production(self):
        raw=self._synthetic_page()
        changed=raw.replace(b'About 42kg',b'About 43kg',1)
        with tempfile.TemporaryDirectory(dir=ROOT/'tests') as temp:
            temp=Path(temp)
            src=temp/'source.html'
            src.write_bytes(changed)
            output=temp/'candidate'
            report=maker.run(ROOT/'tests/fixtures/a2-factory/maker-live-contract.json',
                ROOT/'tests/fixtures/a2-factory/product.json',
                source_file=src,output=output,stage=True)
            self.assertEqual(report['status'],'SOURCE_CHANGED_HOLD')
            self.assertEqual(len(report['drift']),1)
            self.assertEqual(report['isolated_recheck_rounds'],1)
            self.assertEqual(report['isolated_data_consistency'],'PASS_NOT_RELEASE_AUTHORIZATION')
            proposed=json.loads((output/'candidate-product.json').read_text())
            self.assertEqual(proposed['pageFactory']['specifications'][4]['models']['A2'],'About 43kg')
            self.assertEqual(self.product['pageFactory']['specifications'][4]['models']['A2'],'約42 kg')
            self.assertTrue((output/'diff.json').is_file())

    def _synthetic_page(self):
        v=['<div class="decompose"><ul class="versions"><li></li>',
           '<li><p>A2</p></li><li><p>A2-PRO</p></li></ul>',
           '<div class="params">']
        for g in self.parsed['categories']:
            v.extend(['<div class="part"><div class="category">',g['name'],
                      '</div><ul class="value">'])
            for r in g['rows']:
                v.append('<li>')
                for cell in [r['source_label'],r['models']['A2'],r['models']['A2-PRO']]:
                    v.extend(['<div class="valPart"><div><p>',cell,'</p></div></div>'])
                v.append('</li>')
            v.extend(['</ul></div>'])
        v.append('</div></div>')
        return ''.join(v).encode('utf-8')


if __name__=='__main__':
    unittest.main()
