"""Regression: non-site dependency and test artifacts are not product HTML."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_site import EXCLUDED_DIRS

class BuildExclusionRegression(unittest.TestCase):
    def test_dependency_and_browser_artifacts_cannot_be_published(self):
        for directory in ('node_modules','test-results','playwright-report','tests'):
            with self.subTest(directory=directory):
                self.assertIn(directory,EXCLUDED_DIRS)

if __name__ == '__main__':
    unittest.main()
