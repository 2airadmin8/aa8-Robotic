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
        self.assertIn("AA8-HP-GOV-v1.1", contents)

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


    def test_a2_15_redline_evidence_never_auto_approves(self):
        import json
        import struct
        import zlib
        import sys
        import tempfile
        sys.path.insert(0, str(ROOT / "scripts"))
        from hp_governance_quality_gate import (
            A2_REDLINE_SHOTS, A2_VISUAL_VIEWPORTS, a2_visual_evidence,
        )
        self.assertEqual(len(A2_REDLINE_SHOTS), 15)
        with tempfile.TemporaryDirectory() as tmp:
            images = Path(tmp) / "images"
            images.mkdir()
            output = Path(tmp) / "result.json"
            with self.assertRaisesRegex(ValueError, "screenshot missing"):
                a2_visual_evidence("a"*40, images, output)
            def png(view, height):
                def chunk(kind, data):
                    return (struct.pack(">I", len(data)) + kind + data
                            + struct.pack(">I", zlib.crc32(kind+data)&0xffffffff))
                ihdr = struct.pack(">IIBBBBB", view, height, 8, 2, 0, 0, 0)
                pixel = (b"\0" + b"\0"*(view*3)) * height
                return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
                        + chunk(b"tEXt", b"QA-evidence"+b"x"*1200)
                        + chunk(b"IDAT", zlib.compress(pixel))
                        + chunk(b"IEND", b""))
            for stem in set(A2_REDLINE_SHOTS.values()):
                for v in A2_VISUAL_VIEWPORTS:
                    (images / f"{stem}-{v}.png").write_bytes(png(v,350))
            with self.assertRaisesRegex(ValueError, "screenshot missing"):
                a2_visual_evidence("a"*40, images, output)
            for v in (390, 360):
                (images / f"a2-sp-cta-after-anchor-{v}.png").write_bytes(
                    png(v,500))
            result = a2_visual_evidence("a"*40, images, output)
            self.assertEqual(result["visual_approval"], "HOLD")
            self.assertEqual(result["p0_p1_closure"], "NOT_ATTESTED")
            self.assertEqual(len(result["bugs"]), 15)
            self.assertEqual(json.loads(output.read_text("utf-8"))["head_sha"], "a"*40)
            (images / "a2-sales-cta-390.png").write_bytes(b"garbage")
            with self.assertRaisesRegex(ValueError, "invalid/empty PNG"):
                a2_visual_evidence("a"*40, images, output)



if __name__ == "__main__":
    unittest.main()
