import importlib.util
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"ops"/"sales-engagement-gas"/"patch_existing_sales.py"
spec=importlib.util.spec_from_file_location("sales_sender_patch",PATCH)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

ORIGINAL=(
    "function buildSalesMailPlainText_(bodyPreview, deliveryId) {\n"
    "  return String(bodyPreview)\n"
    "    .replace('[[PDF_LINK]]', buildPdfUrl_(deliveryId))\n"
    "    .replace(\n"
    "      '[[BOOKING_LINK]]',\n"
    "      '日程調整へ ' + buildBookingUrl_(deliveryId)\n"
    "    );\n}\n"
    "function buildSalesMailHtml_(bodyPreview, deliveryId, signatureText) {\n"
    "    escapedBody + '<br><br>' + escapedSignature +\n"
    "    '</div>';\n}\n"
    "function salesEngagementHourlyTrigger_() {\n"
    "  try {\n"
    "    syncWebEngagementFromLog_();\n"
    "  } catch (webLogError) {\n"
    "    console.error(webLogError);\n"
    "  }\n"
    "  // Existing send safeguards and triggers remain untouched.\n"
    "}\n"
    "function syncWebEngagementFromLog_() {\n"
    "  validateHeaders_(wh, ['送信管理ID','イベント日時','ページ種別','ページパス'], 'Web行動ログ');\n"
    "    const pageType = clean_(value_(row, wh, 'ページ種別'));\n"
    "    const pagePath = clean_(value_(row, wh, 'ページパス'));\n"
    "    if (!byId[deliveryId]) byId[deliveryId] = {count:0};\n"
    "}\n"
)

class SalesSenderPatchTests(unittest.TestCase):
    def test_original_anchors_are_replaced_exactly_once(self):
        updated=module.patch(ORIGINAL)
        self.assertIn("buildTrackedCatalogUrl_(deliveryId)",updated)
        self.assertIn("syncAa8WebMarketingSummary_()",updated)
        self.assertIn("VERCEL_WEB_EVENT_TEST", updated)
        self.assertIn("pageType.startsWith('TEST_')", updated)
        self.assertEqual(updated.count("研究用ロボット製品一覧を見る"),1)
        self.assertEqual(updated.count("研究用ロボット製品一覧："),1)
        self.assertIn("Existing send safeguards and triggers remain untouched",updated)
        self.assertNotIn("newTrigger(",updated)

    def test_gate_default_off_and_explicit_on_with_exact_generated_code(self):
        patched = module.patch(ORIGINAL)
        start = patched.index("    syncWebEngagementFromLog_();")
        end = patched.index("  } catch (webLogError) {", start)
        gate = patched[start:end]
        self.assertIn("AA8_WEB_EVENT_SUMMARY_ENABLED", gate)
        self.assertEqual(gate.count("syncWebEngagementFromLog_();"), 1)
        self.assertEqual(gate.count("syncAa8WebMarketingSummary_();"), 1)
        self.assertLess(gate.index("syncWebEngagementFromLog_();"), gate.index("AA8_WEB_EVENT_SUMMARY_ENABLED"))
        js = """
const assert=require('node:assert/strict');
let originalSync=0,newSummary=0,customerStatsWrites=0;
function syncWebEngagementFromLog_(){originalSync++;}
function syncAa8WebMarketingSummary_(){newSummary++;customerStatsWrites+=7;return {ok:true};}
function execute(prop){
  const PropertiesService={getScriptProperties:()=>({getProperty:(key)=>{
    assert.equal(key,'AA8_WEB_EVENT_SUMMARY_ENABLED');
    return prop;
  }})};
  try{
""" + gate + """
  }catch(err){throw err;}
}
for(const setting of [undefined,null,'','0','FALSE','false','NO',' trueX ','TRUE','true']){
 const oldSync=originalSync,oldSummary=newSummary,oldWrites=customerStatsWrites;
 execute(setting);
 assert.equal(originalSync-oldSync,1,'original hourly web sync must always run');
 const enabled=typeof setting==='string'&&setting.trim().toUpperCase()==='TRUE';
 assert.equal(newSummary-oldSummary,enabled?1:0,'summary gate mismatch '+setting);
 assert.equal(customerStatsWrites-oldWrites,enabled?7:0,'new customer columns must not be written with gate OFF');
}
"""
        result = subprocess.run(["node", "-e", js], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_second_patch_rejected(self):
        with self.assertRaises(ValueError):
            module.patch(module.patch(ORIGINAL))

    def test_modified_original_code_refused_without_overwrite(self):
        with self.assertRaises(ValueError):
            module.patch(ORIGINAL.replace("syncWebEngagementFromLog_();","otherFunction();"))

    def test_missing_source_anchor_cannot_silently_succeed(self):
        with self.assertRaises(ValueError):
            module.patch("function normal() {}")

if __name__=="__main__":
    unittest.main()
