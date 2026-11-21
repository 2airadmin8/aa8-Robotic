"""Regression: only indexed website sources may enter the public HTML build."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_site as build


class BuildExclusionRegression(unittest.TestCase):
    def test_dependency_and_browser_artifacts_cannot_be_published(self):
        for directory in ("node_modules", "test-results", "playwright-report", "tests", "docs", "ops"):
            with self.subTest(directory=directory):
                self.assertIn(directory, build.EXCLUDED_DIRS)


class GitTrackedOnlyBuildRegression(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        subprocess.run(["git", "init", "--quiet"], cwd=self.root, check=True, capture_output=True)
        self._write("index.html", '''<!doctype html><html lang="ja"><head><title>Official</title>
<meta name="description" content="test"><link rel="canonical" href="https://example.com/"></head>
<body><header class="site-header">BASE</header><main><h1>Official</h1></main>
<footer class="footer">BASE</footer></body></html>''')
        self._write("data/products.json", "{}")
        self._write("includes/site-header.html", '<header class="site-header">TRUSTED HEADER</header>')
        self._write("includes/site-footer.html", '<footer class="footer">TRUSTED FOOTER</footer>')
        self._write("assets/pdf/AirAdmin8_AI_Robotics_Support_for_University_Labs.pdf", "SAFE PDF")
        subprocess.run(["git", "add", "--", "index.html", "data/products.json",
                        "includes/site-header.html", "includes/site-footer.html",
                        "assets/pdf/AirAdmin8_AI_Robotics_Support_for_University_Labs.pdf"],
                       cwd=self.root, check=True, capture_output=True)
        # Test input intentionally mimics source-dir leakage reproductions.
        self._write("products/unreviewed.html", "<html>UNREVIEWED PAGE</html>")
        self._write("data/unreviewed.json", "{BROKEN_JSON")
        self._write("_run1121/demo.html", "<html>UNTRACKED PAGE</html>")
        self._write("assets/img/unreviewed.jpg", "UNREVIEWED ASSET")

    def _write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
        return path

    def test_untracked_public_files_not_in_any_scan(self):
        with patch.object(build, "ROOT", self.root):
            listed = {p.relative_to(self.root).as_posix() for p in build.iter_source_files()}
            self.assertIn("index.html", listed)
            for unreviewed in ("products/unreviewed.html", "data/unreviewed.json",
                               "_run1121/demo.html", "assets/img/unreviewed.jpg",
                               "includes/site-header.html"):
                with self.subTest(path=unreviewed):
                    self.assertNotIn(unreviewed, listed)
            errors = []
            build.validate_json(errors)
            self.assertEqual(errors, [], "Invalid untracked JSON must never be scanned")
            pages = build.validate_html([])
            self.assertEqual([x.path for x in pages], ["index.html"])

    def test_untracked_files_not_copied_to_site(self):
        output = self.root / "_site"
        with patch.multiple(build, ROOT=self.root, OUTPUT=output,
                            HEADER_SOURCE=self.root / "includes/site-header.html",
                            FOOTER_SOURCE=self.root / "includes/site-footer.html",
                            SOURCE_GUIDE_PDF=self.root / "assets/pdf/AirAdmin8_AI_Robotics_Support_for_University_Labs.pdf",
                            PUBLIC_GUIDE_PDF=output / "assets/pdf/AirAdmin8_AI_Robotics_Support_for_University_Labs.pdf"):
            source_files = build.iter_source_files()
            build.build_output([], [], source_files)
        self.assertTrue((output / "index.html").exists())
        self.assertTrue((output / "assets/pdf/AirAdmin8_AI_Robotics_Support_for_University_Labs.pdf").exists())
        for rel in ("products/unreviewed.html", "data/unreviewed.json",
                    "_run1121/demo.html", "assets/img/unreviewed.jpg"):
            self.assertFalse((output / rel).exists(), rel)

    def test_missing_git_index_fails_closed(self):
        with TemporaryDirectory() as location:
            with patch.object(build, "ROOT", Path(location)):
                with self.assertRaisesRegex(RuntimeError, "BUILD_SOURCE_HOLD"):
                    build.iter_source_files()

    def test_indexed_but_missing_file_fails_closed(self):
        missing = self._write("products/missing-after-git-add.html", "<html>temp</html>")
        subprocess.run(["git", "add", "--", "products/missing-after-git-add.html"],
                       cwd=self.root, check=True, capture_output=True)
        missing.unlink()
        with patch.object(build, "ROOT", self.root):
            with self.assertRaisesRegex(RuntimeError, "indexed source missing"):
                build.iter_source_files()

    def test_staged_public_file_allowed_without_broad_scanning(self):
        staged = self._write("products/new-approved.html", "<html>STAGED CANDIDATE</html>")
        subprocess.run(["git", "add", "--", "products/new-approved.html"],
                       cwd=self.root, check=True, capture_output=True)
        with patch.object(build, "ROOT", self.root):
            listed = build.iter_source_files()
            self.assertIn(staged, listed)
            self.assertNotIn(self.root / "products/unreviewed.html", listed)


if __name__ == "__main__":
    unittest.main()
