"""P1: all 13 pages share build-time Header/Footer and exact data contracts."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_site as build
import hp_design_contract as gov


class P1CoreDesignContract(unittest.TestCase):
    def test_four_contracts_and_real_legacy_baselines(self):
        out = gov.validate_catalog()
        self.assertEqual(out["products"], 13)
        self.assertEqual(len(out["contracts"]), 4)
        self.assertEqual(out["realBaselines"]["biped"], "unitree-h2-plus")
        self.assertEqual(out["realBaselines"]["quadruped"], "unitree-go2-edu")
        self.assertIsNone(out["realBaselines"]["biped_accessory"])
        self.assertIsNone(out["realBaselines"]["quadruped_accessory"])

    def test_missing_accessory_manufacturer_compatibility_is_hold(self):
        fake = {"officialSource": "https://maker.example/products", "sourceVerified": True,
                "mounting": "?", "interface": "USB", "safety": "TBD",
                "warranty": "TBD", "revision": "R1", "releaseReady": False}
        with self.assertRaisesRegex(ValueError, "hostModelIds"):
            gov.validate_new_candidate("biped_accessory", fake)
        fake["hostModelIds"] = ["unknown"]
        # Still cannot satisfy all verified fields just by inventing a host.
        fake.pop("sourceVerified")
        with self.assertRaisesRegex(ValueError, "manufacturer evidence"):
            gov.validate_new_candidate("biped_accessory", fake)

    def test_same_shared_header_change_propagates_across_all_13_generated_pages(self):
        source = (ROOT / "includes/site-header.html").read_text("utf-8")
        self.assertIn('data-shared-layout="header"', source)
        token = "AA8_GOV_HEADER_SENTINEL_20261114"
        with TemporaryDirectory() as tmp:
            changed_header = Path(tmp) / "site-header.html"
            changed_header.write_text(source.replace(
                'data-shared-layout="header"',
                f'data-shared-layout="header" data-governance-probe="{token}"', 1),
                encoding="utf-8")
            catalog = json.loads((ROOT / "data/products.json").read_text("utf-8"))
            with patch.object(build, "HEADER_SOURCE", changed_header):
                for p in catalog["products"]:
                    with self.subTest(product=p["id"]):
                        src = Path(p["detailPage"])
                        output = build.build_html(
                            (ROOT / src).read_text("utf-8"), src)
                        self.assertEqual(output.count(token), 1)
                        self.assertEqual(output.count('<footer class="footer" data-shared-layout="footer">'), 1)
        # Source files are not overwritten by this test.
        self.assertNotIn(token, (ROOT / "includes/site-header.html").read_text("utf-8"))

    def test_product_cta_is_configured_not_generic_false_sales_claim(self):
        data = json.loads((ROOT / "data/products.json").read_text("utf-8"))
        for p in data["products"]:
            with self.subTest(product=p["id"]):
                source = (ROOT / p["detailPage"]).read_text("utf-8")
                self.assertIn("contact.html", source, p["id"])
                self.assertIn("data-aa8-product-standard", source, p["id"])


if __name__ == "__main__":
    unittest.main()
