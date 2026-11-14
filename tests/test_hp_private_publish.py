"""P0 regression: internal governance and operating metrics never reach Pages."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_site as build
import verify_release as release


class InternalArtifactSafety(unittest.TestCase):
    def test_internal_files_are_not_build_sources(self):
        files = {path.relative_to(ROOT).as_posix()
                 for path in build.iter_source_files()}
        self.assertIn("data/products.json", files)
        self.assertIn("products/unitree-g1.html", files)
        self.assertNotIn("data/hp-page-family-contract-v1.json", files)
        self.assertFalse(any(path.startswith(("docs/", "ops/")) for path in files))

    def test_output_gate_rejects_private_data_and_accepts_public_catalog(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog = root / "data/products.json"
            catalog.parent.mkdir()
            catalog.write_text("{}", encoding="utf-8")
            with patch.object(release, "OUTPUT", root):
                errors = []
                release.verify_private_artifacts_absent(errors)
                self.assertEqual(errors, [])
                for path in ("docs/governance/internal.md",
                             "ops/hp-factory-efficiency.csv",
                             "data/hp-page-family-contract-v1.json"):
                    node = root / path
                    node.parent.mkdir(exist_ok=True, parents=True)
                    node.write_text("INTERNAL", encoding="utf-8")
                errors = []
                release.verify_private_artifacts_absent(errors)
                self.assertEqual(len(errors), 3)

    def test_real_build_excludes_private_directories(self):
        site = ROOT / "_site"
        if not site.is_dir():
            self.skipTest("build artifact not generated yet")
        for path in ("docs", "ops", "data/hp-page-family-contract-v1.json"):
            with self.subTest(path=path):
                self.assertFalse((site / path).exists())
        self.assertTrue((site / "data/products.json").exists())


if __name__ == "__main__":
    unittest.main()
