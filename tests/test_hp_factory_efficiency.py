"""Factory efficiency: source-to-Preview clocks must never be invented."""
import csv
from datetime import datetime
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import hp_factory_efficiency as k


class FactoryKPIContract(unittest.TestCase):
    def valid(self):
        return {key: "" for key in k.FIELDS} | {
            "sku_id": "unitree-g1-edu-new", "pr_number": "201",
            "source_ready_at": "2026-11-15T01:00:00Z",
            "preview_ready_at": "2026-11-15T02:30:00Z",
            "first_qa_at": "2026-11-15T03:30:00Z",
            "manual_code_edits": "0", "rework_iterations": "1",
            "ceo_interventions": "1", "repeated_bug_count": "0",
            "evidence_url": "https://github.com/2airadmin8/aa8-Robotic/pull/201",
            "record_status": "VERIFIED",
        }

    def test_real_ledger_does_not_invent_sku_cycle_time(self):
        records = k.load(ROOT / "ops/hp-factory-efficiency.csv")
        result = k.report(records)
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["comparable"], 0)
        self.assertTrue(result["insufficientEvidence"])
        self.assertFalse(result["efficiencyImprovementProven"])
        self.assertEqual({x["sku_id"]: x["pr_number"] for x in records},
                         {"unitree-h2-plus": "158", "agibot-a3-ultra": "164"})

    def test_verified_example_calculates_duration(self):
        x = k.normalized(self.valid())
        report = k.report([x])
        self.assertEqual(report["measurements"][0]["minutes_source_to_preview"], 90.0)
        self.assertTrue(report["insufficientEvidence"])

    def test_missing_evidence_cannot_be_verified(self):
        x = self.valid()
        x["source_ready_at"] = ""
        with self.assertRaisesRegex(ValueError, "actual timestamp"):
            k.normalized(x)
        x = self.valid()
        x["first_qa_at"] = ""
        with self.assertRaisesRegex(ValueError, "first QA evidence"):
            k.normalized(x)
        x = self.valid()
        x["rework_iterations"] = "4"
        with self.assertRaisesRegex(ValueError, "three reworks"):
            k.normalized(x)

    def test_time_order_and_wrong_repo_denied(self):
        x = self.valid()
        x["preview_ready_at"] = "2026-11-14T01:00:00Z"
        with self.assertRaises(ValueError):
            k.normalized(x)
        x = self.valid()
        x["evidence_url"] = "https://github.com/unknown/evil/pull/201"
        with self.assertRaises(ValueError):
            k.normalized(x)


if __name__ == "__main__":
    unittest.main()
