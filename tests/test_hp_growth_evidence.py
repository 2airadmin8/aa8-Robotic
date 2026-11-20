"""P2: genuine weekly aggregate evidence, not fabricated leads or writes."""
import copy
from datetime import date
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import hp_growth_evidence as growth


class GrowthEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(
            (ROOT / "ops/hp-growth-aggregate-example.json").read_text("utf-8"))

    def test_readonly_real_aggregate_produces_at_most_three(self):
        result = growth.propose(copy.deepcopy(self.snapshot), as_of=date(2026, 11, 14))
        self.assertEqual(len(result["candidates"]), 3)
        self.assertEqual(result["siteKPI"]["current"]["clicks"], 8)
        self.assertEqual(result["siteKPI"]["current"]["impressions"], 219)
        self.assertEqual(result["siteKPI"]["previous"]["clicks"], 4)
        self.assertEqual(result["inquiryCoverage"]["total"], 17)
        self.assertEqual(result["inquiryCoverage"]["withSourceProduct"], 2)
        self.assertTrue(result["sourceIsReadOnly"])
        self.assertFalse(result["productionWriteAuthorized"])
        self.assertFalse(result["businessRevenueProven"])
        self.assertTrue(all(c["status"] == "PROPOSAL_ONLY_NO_PRODUCTION_WRITE"
                            for c in result["candidates"]))
        self.assertTrue(all(c["evidence"] and c["success_measure"] and
                            c["prohibited"] for c in result["candidates"]))

    def test_unknown_source_or_failed_sync_holds(self):
        for field, value in (("gscId", "fake"), ("inquiryId", "wrong"),
                             ("gscSyncStatus", "FAILED")):
            item = copy.deepcopy(self.snapshot)
            item["sources"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                growth.inspect(item, as_of=date(2026, 11, 14))

    def test_7_day_completeness_and_freshness_required(self):
        item = copy.deepcopy(self.snapshot)
        item["weekly"]["current"]["days"] = 6
        with self.assertRaises(ValueError):
            growth.inspect(item, as_of=date(2026, 11, 14))
        item = copy.deepcopy(self.snapshot)
        item["collectedAt"] = "2026-12-15"
        with self.assertRaises(ValueError):
            growth.inspect(item, as_of=date(2026, 11, 14))

    def test_future_or_forged_metrics_rejected(self):
        item = copy.deepcopy(self.snapshot)
        item["weekly"]["previous"]["clicks"] = -1
        with self.assertRaises(ValueError):
            growth.inspect(item, as_of=date(2026, 11, 14))
        item = copy.deepcopy(self.snapshot)
        item["pages"][0]["url"] = "https://evil.test/phish"
        with self.assertRaises(ValueError):
            growth.inspect(item, as_of=date(2026, 11, 14))

    def test_old_snapshot_cannot_be_reused_as_latest_week(self):
        with self.assertRaisesRegex(ValueError, "not fresh"):
            growth.inspect(copy.deepcopy(self.snapshot), as_of=date(2026, 11, 24))

    def test_unapproved_customer_field_rejected(self):
        item = copy.deepcopy(self.snapshot)
        item["inquiry"]["name"] = "PERSON_NAME_NOT_ALLOWED"
        with self.assertRaises(ValueError):
            growth.inspect(item, as_of=date(2026, 11, 14))

    def test_pii_key_in_aggregate_holds(self):
        item = copy.deepcopy(self.snapshot)
        item["inquiry"]["email"] = "sensitive@example.test"
        with self.assertRaisesRegex(ValueError, "PII"):
            growth.inspect(item, as_of=date(2026, 11, 14))


if __name__ == "__main__":
    unittest.main()
