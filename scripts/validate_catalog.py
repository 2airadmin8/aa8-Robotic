#!/usr/bin/env python3
"""Validate product and resource catalog integrity before deployment."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS_PATH = ROOT / "data" / "products.json"
RESOURCES_PATH = ROOT / "data" / "resources.json"
CASES_PATH = ROOT / "data" / "case-evidence.json"
DATE_PATTERN = re.compile(r"^20\d{2}-\d{2}-\d{2}$")

ALLOWED_VISIBILITY = {"public", "hidden", "archived"}
ALLOWED_STATUS = {"active", "preparing", "researching", "discontinued", "archived"}
ALLOWED_SALES_STATUS = {
    "quote_available",
    "confirmation_required",
    "not_released",
    "discontinued",
    "not_for_sale",
}
ALLOWED_SUPPORT_STATUS = {
    "available",
    "preparing",
    "confirmation_required",
    "discontinued",
    "not_available",
}
ALLOWED_PRICE_STATUS = {
    "inquiry",
    "confirmation_required",
    "not_released",
    "discontinued",
    "not_for_sale",
}
ALLOWED_LEAD_TIME_STATUS = {
    "confirmation_required",
    "not_released",
    "discontinued",
    "not_applicable",
}
ALLOWED_IMAGE_STATUS = {"placeholder", "official", "licensed", "original"}
ALLOWED_RESOURCE_REVIEW = {"official", "reviewed", "unverified", "archived"}
ALLOWED_RESOURCE_TYPES = {
    "official",
    "sdk",
    "ros",
    "vla",
    "teleoperation",
    "simulation",
    "dataset",
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def add_required_text_errors(errors: list[str], item: dict, fields: list[str], label: str) -> None:
    for field in fields:
        if not str(item.get(field, "")).strip():
            errors.append(f"{label} is missing {field}")


def main() -> int:
    errors: list[str] = []

    try:
        products_data = read_json(PRODUCTS_PATH)
        resources_data = read_json(RESOURCES_PATH)
        cases_data = read_json(CASES_PATH)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"CATALOG ERROR: cannot read catalog JSON: {exc}")
        return 1

    products = products_data.get("products", [])
    resources = resources_data.get("resources", [])
    case_ids = {str(item.get("id", "")).strip() for item in cases_data.get("cases", [])}

    product_ids: list[str] = []
    product_pages: list[str] = []

    for item in products:
        product_id = str(item.get("id", "")).strip()
        label = f"Product {product_id or '<unknown>'}"
        product_ids.append(product_id)
        product_pages.append(str(item.get("detailPage", "")).strip())

        add_required_text_errors(
            errors,
            item,
            [
                "id",
                "name",
                "manufacturerId",
                "manufacturerName",
                "categoryId",
                "categoryLabel",
                "status",
                "statusLabel",
                "visibility",
                "summary",
                "detailPage",
                "image",
                "imageAlt",
                "imageStatus",
                "priceStatus",
                "priceLabel",
                "leadTimeStatus",
                "leadTimeLabel",
                "verifiedAt",
            ],
            label,
        )

        if product_id and not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", product_id):
            errors.append(f"Invalid product id: {product_id}")
        if item.get("visibility") not in ALLOWED_VISIBILITY:
            errors.append(f"Invalid visibility for {product_id}: {item.get('visibility')}")
        if item.get("status") not in ALLOWED_STATUS:
            errors.append(f"Invalid status for {product_id}: {item.get('status')}")
        if item.get("salesStatus") not in ALLOWED_SALES_STATUS:
            errors.append(f"Invalid salesStatus for {product_id}: {item.get('salesStatus')}")
        if item.get("supportStatus") not in ALLOWED_SUPPORT_STATUS:
            errors.append(f"Invalid supportStatus for {product_id}: {item.get('supportStatus')}")
        if item.get("priceStatus") not in ALLOWED_PRICE_STATUS:
            errors.append(f"Invalid priceStatus for {product_id}: {item.get('priceStatus')}")
        if item.get("leadTimeStatus") not in ALLOWED_LEAD_TIME_STATUS:
            errors.append(f"Invalid leadTimeStatus for {product_id}: {item.get('leadTimeStatus')}")
        if item.get("imageStatus") not in ALLOWED_IMAGE_STATUS:
            errors.append(f"Invalid imageStatus for {product_id}: {item.get('imageStatus')}")

        verified_at = str(item.get("verifiedAt", ""))
        if verified_at and not DATE_PATTERN.fullmatch(verified_at):
            errors.append(f"Invalid verifiedAt for {product_id}: {verified_at}")

        for field in ("filterGroups", "featureLabels", "useCaseIds", "useLabels"):
            values = item.get(field)
            if not isinstance(values, list) or not values or not all(isinstance(value, str) and value.strip() for value in values):
                errors.append(f"Invalid or empty {field} for {product_id}")

        detail_page = ROOT / str(item.get("detailPage", ""))
        if not detail_page.is_file():
            errors.append(f"Missing detail page for {product_id}: {item.get('detailPage')}")

        image = ROOT / str(item.get("image", ""))
        if not image.is_file():
            errors.append(f"Missing image for {product_id}: {item.get('image')}")
        if item.get("imageStatus") == "placeholder" and "参考イメージ" not in str(item.get("imageAlt", "")):
            errors.append(f"Placeholder image alt must state 参考イメージ: {product_id}")

        for replacement_id in item.get("replacementIds", []):
            if replacement_id == product_id:
                errors.append(f"Product cannot replace itself: {product_id}")

        for case_id in item.get("relatedCaseIds", []):
            if case_id not in case_ids:
                errors.append(f"Unknown related case for {product_id}: {case_id}")

        if item.get("status") == "preparing" and item.get("salesStatus") != "not_released":
            errors.append(f"Preparing product must use salesStatus not_released: {product_id}")
        if item.get("status") in {"discontinued", "archived"} and item.get("salesStatus") not in {"discontinued", "not_for_sale"}:
            errors.append(f"Inactive product has active salesStatus: {product_id}")

    duplicate_product_ids = sorted({value for value in product_ids if value and product_ids.count(value) > 1})
    if duplicate_product_ids:
        errors.append("Duplicate product ids: " + ", ".join(duplicate_product_ids))
    duplicate_pages = sorted({value for value in product_pages if value and product_pages.count(value) > 1})
    if duplicate_pages:
        errors.append("Duplicate product detail pages: " + ", ".join(duplicate_pages))

    known_product_ids = set(product_ids)
    for item in products:
        for replacement_id in item.get("replacementIds", []):
            if replacement_id not in known_product_ids:
                errors.append(f"Unknown replacement product for {item.get('id')}: {replacement_id}")

    resource_ids: list[str] = []
    resource_urls: list[str] = []

    for item in resources:
        resource_id = str(item.get("id", "")).strip()
        label = f"Resource {resource_id or '<unknown>'}"
        resource_ids.append(resource_id)

        add_required_text_errors(
            errors,
            item,
            [
                "id",
                "makerId",
                "makerName",
                "title",
                "description",
                "sourceLabel",
                "reviewStatus",
                "reviewLabel",
                "language",
            ],
            label,
        )

        if resource_id and not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", resource_id):
            errors.append(f"Invalid resource id: {resource_id}")
        if item.get("reviewStatus") not in ALLOWED_RESOURCE_REVIEW:
            errors.append(f"Invalid reviewStatus for {resource_id}: {item.get('reviewStatus')}")

        types = item.get("types")
        if not isinstance(types, list) or not types:
            errors.append(f"Missing resource types for {resource_id}")
        elif not set(types).issubset(ALLOWED_RESOURCE_TYPES):
            errors.append(f"Unknown resource types for {resource_id}: {sorted(set(types) - ALLOWED_RESOURCE_TYPES)}")

        for field in ("productGroups", "keywords"):
            values = item.get(field)
            if not isinstance(values, list) or not values or not all(isinstance(value, str) and value.strip() for value in values):
                errors.append(f"Invalid or empty {field} for {resource_id}")

        raw_url = item.get("url")
        url = str(raw_url or "").strip()
        if url:
            resource_urls.append(url)
            parsed = urlparse(url)
            if parsed.scheme != "https" or not parsed.netloc:
                errors.append(f"Resource URL must be absolute HTTPS for {resource_id}: {url}")
        else:
            review_status = str(item.get("reviewStatus", ""))
            review_label = str(item.get("reviewLabel", ""))
            if review_status != "unverified" or "確認中" not in review_label:
                errors.append(
                    f"Missing resource URL must be explicitly marked unverified/確認中: {resource_id}"
                )

    duplicate_resource_ids = sorted({value for value in resource_ids if value and resource_ids.count(value) > 1})
    if duplicate_resource_ids:
        errors.append("Duplicate resource ids: " + ", ".join(duplicate_resource_ids))
    duplicate_resource_urls = sorted({value for value in resource_urls if value and resource_urls.count(value) > 1})
    if duplicate_resource_urls:
        errors.append("Duplicate resource URLs: " + ", ".join(duplicate_resource_urls))

    if errors:
        for error in errors:
            print(f"CATALOG ERROR: {error}")
        print(f"Catalog validation failed with {len(errors)} error(s).")
        return 1

    print(f"Catalog validation passed: {len(products)} products and {len(resources)} resources checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
