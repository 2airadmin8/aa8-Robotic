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
        cls.product=json.loads((ROOT/'tests/fixtures/a2-factory/product.json').read_text(encoding='utf-8'))
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

    def test_yes_cell_with_official_heading_allows_stated_wireless_versions(self):
        # The manufacturer title contains both versions; YES model cells
        # confirm each model supports the named communications standards.
        maker.verify_display(self.product,self.contract,self.parsed)

    def test_yes_cell_rejects_version_absent_from_official_heading(self):
        contract=copy.deepcopy(self.contract)
        product=copy.deepcopy(self.product)
        rows=[r for g in contract["categories"] for r in g["rows"]]
        idx=next(i for i,r in enumerate(rows) if r["id"]=="無線通信")
        rows[idx]["approved_display"]["A2"]="Wi-Fi 7／Bluetooth 5.2 対応"
        product["pageFactory"]["specifications"][idx]["models"]["A2"]="Wi-Fi 7／Bluetooth 5.2 対応"
        with self.assertRaisesRegex(ValueError,"extra version"):
            maker.verify_display(product,contract,self.parsed)

    def test_yes_cell_rejects_version_when_heading_has_no_numbers(self):
        contract=copy.deepcopy(self.contract)
        product=copy.deepcopy(self.product)
        rows=[r for g in contract["categories"] for r in g["rows"]]
        idx=next(i for i,r in enumerate(rows) if r["id"]=="無線通信")
        rows[idx]["source_label"]="Wireless"
        with self.assertRaisesRegex(ValueError,"extra version"):
            maker.verify_display(product,contract,self.parsed)

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
            proposed=json.loads((output/'candidate-product.json').read_text(encoding='utf-8'))
            self.assertEqual(proposed['pageFactory']['specifications'][4]['models']['A2'],'About 43kg')
            self.assertEqual(self.product['pageFactory']['specifications'][4]['models']['A2'],'約42 kg')
            self.assertTrue((output/'diff.json').is_file())

    def test_new_public_catalog_factory_optin_cannot_bypass_maker_contract(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"data").mkdir()
            (root/"tests/fixtures").mkdir(parents=True)
            product={"id":"new-public-robot","pageFactory":{
                "officialSource":"https://www.unitree.com/A2/","releaseReady":True}}
            catalog={"products":[
                {"id":"unitree-h2-plus","pageFactory":{"releaseReady":True}},
                {"id":"agibot-a3-ultra","pageFactory":{"releaseReady":True}},
                product
            ]}
            (root/"data/products.json").write_text(json.dumps(catalog),"utf-8")
            with self.assertRaisesRegex(ValueError,"new public Factory SKU.*lacks"):
                maker.audit_new_intake(root)

    def test_new_public_release_blocks_unreviewed_translation(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            fixture=root/"tests/fixtures/unitree-a2"
            fixture.mkdir(parents=True)
            (root/"data").mkdir()
            (root/"data/products.json").write_text(json.dumps({"products":[{
                "id":"unitree-a2","pageFactory":{
                    "officialSource":"https://www.unitree.com/A2/","releaseReady":True}
            }]}),"utf-8")
            (fixture/"product.json").write_text(json.dumps(self.product),"utf-8")
            (fixture/"maker-live-contract.json").write_text(
                json.dumps(self.contract,ensure_ascii=False),"utf-8")
            with self.assertRaisesRegex(ValueError,"pending independent review"):
                maker.audit_new_intake(root)

    def test_untrusted_new_maker_is_denied_without_existing_registry_identity(self):
        good={'manufacturer_id':'agibot','adapter':'html-table-v1',
              'source_url':'https://www.agibot.com/products/example'}
        maker.safe_url(good['source_url'],contract=good)
        for d in [
            {**good,'manufacturer_id':'nonexistent'},
            {**good,'source_url':'https://www.agibot.com.evil.example/specs'},
            {**good,'source_url':'https://127.0.0.1/internal'},
            {**good,'source_url':'https://www.unitree.com/A2/'},
            {**good,'adapter':'auto-ai-guess-v1'},
        ]:
            with self.subTest(case=d):
                with self.assertRaisesRegex(ValueError,'SOURCE_HOLD'):
                    maker.safe_url(d['source_url'],contract=d)

    def test_monitor_all_stages_real_drift_but_returns_hold(self):
        source=self._synthetic_page().replace(b'About 42kg',b'About 43kg',1)
        with tempfile.TemporaryDirectory(dir=ROOT/'tests') as d:
            base=Path(d)
            stage=base/'isolated-candidates'
            calls=[]
            original=maker.fetch
            def fake_fetch(url,*,contract=None):
                calls.append(url)
                return source
            try:
                with patch.object(maker,'fetch',side_effect=fake_fetch):
                    with self.assertRaisesRegex(ValueError,'PENDING_INDEPENDENT_FACT_REVIEW'):
                        maker.monitor_all(ROOT,stage_dir=stage)
                self.assertEqual(len(calls),1,'one unchanged official source snapshot per cycle')
                p=stage/'a2-factory'
                self.assertTrue((p/'diff.json').is_file())
                diff=json.loads((p/'diff.json').read_text('utf-8'))
                self.assertEqual(diff['status'],'PENDING_INDEPENDENT_FACT_REVIEW')
                self.assertEqual(len(diff['changes']),1)
                self.assertEqual(diff['changes'][0]['after'],'About 43kg')
                self.assertEqual(json.loads((p/'candidate-product.json').read_text('utf-8'))['pageFactory']['specifications'][4]['models']['A2'],'About 43kg')
                self.assertEqual(self.product['pageFactory']['specifications'][4]['models']['A2'],'約42 kg')
            finally:
                maker.fetch=original

    def test_monitor_all_no_change_has_no_staged_candidate(self):
        from html import escape
        def source_for(url, *, contract=None):
            if url.endswith("/A2/"):
                return self._synthetic_page()
            data=maker.load_contract(
                ROOT/"tests"/"fixtures"/(
                    "unitree-b2-new-real-pilot" if url.endswith("/b2/")
                    else "unitree-r1-new-real-pilot")/"maker-live-contract.json")
            if url.endswith("/b2/"):
                return ('<ul class="parameter b2">' + "".join(
                    '<li><div class="name">' + escape(row["source_label"]) +
                    '</div><div class="value"><p>' +
                    escape(row["models"]["B2"]) + '</p></div></li>'
                    for row in data["categories"][0]["rows"]) + '</ul>').encode()
            self.assertTrue(url.endswith("/R1/"))
            models=data["models"]
            header='<ul class="versions">' + "".join(
                '<li><p>' + escape(m) + '</p></li>' for m in models) + '</ul>'
            parts=[]
            for group in data["categories"]:
                rows=[]
                for row in group["rows"]:
                    cells=[row["source_label"]]+[row["models"][m] for m in models]
                    rows.append('<li>' + ''.join(
                        '<div class="valPart"><p>' + escape(c) + '</p></div>'
                        for c in cells) + '</li>')
                parts.append('<div class="part"><div class="category">' +
                    escape(group["source_name"]) + '</div><ul class="value">' +
                    ''.join(rows) + '</ul></div>')
            return ('<div class="decompose">' + header + '<div class="params">' +
                    ''.join(parts) + '</div></div>').encode()
        with patch.object(maker,'fetch',side_effect=source_for):
            result=maker.monitor_all(ROOT)
        self.assertEqual(len(result),3)
        self.assertEqual([(x["parameter_rows"],x["cells_checked"]) for x in result],
                         [(37,74),(19,19),(31,93)])
        self.assertTrue(all(x["status"]=="SOURCE_MATCH_TRANSLATION_REVIEW_PENDING"
                            for x in result))

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
