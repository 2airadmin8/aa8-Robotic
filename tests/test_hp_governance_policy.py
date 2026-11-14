"""Shared-drive-ready management modules are version pinned and testable."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/governance"


class PolicyV1(unittest.TestCase):
    def test_reusable_policy_modules_present(self):
        files = ("README.md", "00_CORE_CHANGE_CONTROL_V1.md",
                 "01_HP_ADAPTER_V1.md", "02_CHANGE_REQUEST_TEMPLATE.md",
                 "03_MEASUREMENT_BASELINE.md", "CHANGELOG.md")
        for name in files:
            with self.subTest(name=name):
                p = DOCS / name
                self.assertTrue(p.is_file())
                self.assertGreater(p.stat().st_size, 100)
        contents = (DOCS / "README.md").read_text("utf-8")
        self.assertIn("AA8-HP-GOV-v1.0", contents)

    def test_existing_canonical_owner_not_replaced(self):
        files = ("includes/site-header.html", "includes/site-footer.html",
                 "assets/css/shared-layout.css", "data/products.json",
                 ".github/workflows/pages.yml")
        for name in files:
            self.assertTrue((ROOT / name).is_file(), name)
        policy = (DOCS / "00_CORE_CHANGE_CONTROL_V1.md").read_text("utf-8")
        for condition in ("HOLD", "max 3", "rollback", "CEO", "regression"):
            self.assertIn(condition.lower(), policy.lower())

    def test_change_request_has_required_governance_fields(self):
        template = (ROOT / ".github/ISSUE_TEMPLATE/hp-factory-governance.yml"
                    ).read_text("utf-8")
        for key in ("id: priority", "id: evidence", "id: impact",
                    "id: constraints", "id: qa", "id: closeout"):
            self.assertIn(key, template)
        self.assertEqual(template.count("required: true"), 6)
        self.assertNotIn("workflow_dispatch", template)
        self.assertNotIn("pages.yml", template)
        security=(DOCS/"01_HP_ADAPTER_V1.md").read_text("utf-8")
        self.assertIn("data/hp-page-family-contract-v1.json",security)
        self.assertIn("public _site/",security)


if __name__ == "__main__":
    unittest.main()
