"""Synthetic QA-only product; never add this entry to the published Product Master."""
from __future__ import annotations


def sample_product() -> dict:
    official = "https://www.unitree.com/H2-X/"
    source_images = [
        ("image_005.webp", "QA image 1"),
        ("image_007.webp", "QA image 2"),
        ("image_013.jpg", "QA image 3"),
    ]
    images = [
        {
            "src": f"assets/img/products/unitree/h2x/drive/{name}",
            "alt": alt,
            "sourceUrl": official,
        }
        for name, alt in source_images
    ]
    return {
        "id": "factory-qa",
        "name": "QA Fixture Robot",
        "manufacturerName": "Unitree",
        "summary": "Internal QA fixture for verifying generated markup. Not a public product.",
        "detailPage": "products/factory-qa.html",
        "image": "assets/img/products/unitree/h2x/drive/image_007.webp",
        "imageAlt": "QA fixture model",
        "imageStatus": "official",
        "visibility": "hidden",
        "statusLabel": "QAのみ",
        "priceLabel": "見積要確認",
        "leadTimeLabel": "納期要確認",
        "verifiedAt": "2026-10-31",
        "pageFactory": {
            "template": "g1-v1",
            "officialSource": official,
            "title": "QA Fixture Robot | AirAdmin8 Robotics",
            "metaDescription": "QA-only product factory template fixture. Never publish this page.",
            "heroLead": "QA-only layout and asset test",
            "facts": [
                {"label": "QA fact A", "value": "A", "sourceUrl": official},
                {"label": "QA fact B", "value": "B", "sourceUrl": official},
                {"label": "QA fact C", "value": "C", "sourceUrl": official},
            ],
            "applications": [
                {"title": "QA scenario 1", "description": "A workflow test", "sourceUrl": official},
                {"title": "QA scenario 2", "description": "Another workflow test", "sourceUrl": official},
            ],
            "specifications": [
                {"label": "QA spec 1", "value": "Unknown", "sourceUrl": official},
                {"label": "QA spec 2", "value": "Check supplier", "sourceUrl": official},
                {"label": "QA spec 3", "value": "Quotation needed", "sourceUrl": official},
            ],
            "faq": [
                {"question": "QA question 1?", "answer": "QA answer 1."},
                {"question": "QA question 2?", "answer": "QA answer 2."},
                {"question": "QA question 3?", "answer": "QA answer 3."},
            ],
            "images": images,
            "videos": [{
                "src": "assets/img/products/unitree/h2x/drive/video_01.mp4",
                "poster": "assets/img/products/unitree/h2x/drive/image_005.webp",
                "label": "QA-only official video asset",
                "sourceUrl": official,
            }],
            "ctaImageIndexes": [0, 1, 2],
            "relatedProductIds": ["unitree-g1", "unitree-h2", "unitree-h2-x"],
            "releaseReady": False,
        },
    }
