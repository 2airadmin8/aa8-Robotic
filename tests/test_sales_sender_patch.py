import importlib.util
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
)

class SalesSenderPatchTests(unittest.TestCase):
    def test_original_anchors_are_replaced_exactly_once(self):
        updated=module.patch(ORIGINAL)
        self.assertIn("buildTrackedCatalogUrl_(deliveryId)",updated)
        self.assertIn("syncAa8WebMarketingSummary_()",updated)
        self.assertEqual(updated.count("研究用ロボット製品一覧を見る"),1)
        self.assertEqual(updated.count("研究用ロボット製品一覧："),1)
        self.assertIn("Existing send safeguards and triggers remain untouched",updated)
        self.assertNotIn("newTrigger(",updated)

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
