"""Regression: H2-X social cards use the approved hero, not generic category art."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import inject_static_meta as meta


class SocialImageGate(unittest.TestCase):
    def test_h2x_approved_social_image_exists(self):
        image = "assets/img/products/unitree/h2x/drive/image_007.webp"
        self.assertTrue((ROOT / image).is_file())
        self.assertEqual(meta.social_image_for({"image": image}), meta.PUBLIC_BASE + image)

    def test_other_pages_retain_existing_fallback(self):
        self.assertEqual(meta.social_image_for({}), meta.SOCIAL_IMAGE)

    def test_disallow_escape_and_missing_files(self):
        for image in ("../secret.png", "assets/img/products/../../x.png",
                      "assets/img/products/missing.webp", "https://example.com/a.jpg"):
            with self.subTest(image=image):
                with self.assertRaises(ValueError):
                    meta.social_image_for({"image": image})

    def test_injected_og_and_twitter_are_product_specific(self):
        content = '<html><head><title>Unitree H2-X</title></head><body></body></html>'
        image = "assets/img/products/unitree/h2x/drive/image_007.webp"
        generated = meta.build_static_meta(
            content, Path("products/unitree-h2-x.html"),
            {"products/unitree-h2-x.html": {"image": image}}
        )
        expected = meta.PUBLIC_BASE + image
        self.assertIn('<meta property="og:image" content="' + expected + '">', generated)
        self.assertIn('<meta name="twitter:image" content="' + expected + '">', generated)
        self.assertNotIn("robot-category-lineup.svg", generated)


if __name__ == "__main__":
    unittest.main()
