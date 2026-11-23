#!/usr/bin/env python3
"""P1: enforce existing design ownership and four type content contracts.

This is contract governance, NOT a new renderer and NOT SKU publication.
Existing mobile-manipulation is preserved as its own legacy family.
"""
from __future__ import annotations
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data/hp-page-family-contract-v1.json"


def require(test: bool, msg: str):
    if not test:
        raise ValueError("P1_CONTRACT_HOLD: " + msg)


def load_contract(root: Path = ROOT) -> dict:
    c = json.loads((root / "data/hp-page-family-contract-v1.json").read_text("utf-8"))
    require(c.get("schemaVersion") == "aa8-hp-page-family-contract-v1", "version")
    require(set(c["families"]) == {
        "biped", "biped_accessory", "quadruped", "quadruped_accessory",
    }, "four expected profiles")
    require(c["shared"]["catalogSize"] == 13, "catalog release scope")
    for field in ("header", "footer", "css", "productSSOT"):
        p = root / c["shared"][field]
        require(p.is_file() and p.resolve().is_relative_to(root.resolve()), field)
    require(len(c["shared"]["requiredRoles"]) >= 10, "semantic roles missing")
    for p in c["families"].values():
        require(len(p["candidateRequired"]) >= 5, "type has weak source contract")
    return c


def validate_catalog(root: Path = ROOT) -> dict:
    c = load_contract(root)
    master = json.loads((root / c["shared"]["productSSOT"]).read_text("utf-8"))
    products = master["products"]
    require(len(products) == c["shared"]["catalogSize"], "catalog mutated")
    require(len({p["id"] for p in products}) == len(products), "duplicate ProductID")
    known = {x["id"]: x for x in products}
    for product in products:
        key = product["id"]
        detail = product.get("detailPage", "")
        require(re.fullmatch(r"products/[a-z0-9-]+\.html", detail) is not None,
                key + ": unsafe detailPage")
        require((root / detail).is_file(), key + ": missing source product page")
        spec = product.get("pageStandard") or {}
        require(spec.get("version") == "3.1", key + ": ProductStandard drift")
        family = spec.get("family")
        require(family in {"humanoid", "quadruped", "mobile-manipulation"},
                key + ": unknown legacy family")
    real = {}
    for name, profile in c["families"].items():
        baseline = profile["baselineProduct"]
        if baseline is None:
            require(profile["verification"].startswith("CONTRACT_ONLY"),
                    name + ": cannot pretend real accessory QA")
            real[name] = None
            continue
        require(baseline in known, "missing real product " + baseline)
        require(known[baseline]["pageStandard"]["family"] ==
                profile["legacyPageStandard"], name + ": wrong real baseline")
        real[name] = baseline
    return {"products": len(products), "realBaselines": real,
            "contracts": list(c["families"]), "legacyMobileManipulation":
            sum(p["pageStandard"]["family"] == "mobile-manipulation" for p in products)}


def validate_new_candidate(family: str, candidate: dict, root: Path = ROOT) -> None:
    """Validate facts before an AI generates ANY new accessory preview."""
    c = load_contract(root)
    require(family in c["families"], "unsupported product type")
    for field in c["families"][family]["candidateRequired"]:
        value = candidate.get(field)
        require(value is not None and value != "" and value != [],
                family + " missing verified " + field)
    require(candidate.get("sourceVerified") is True,
            "official manufacturer evidence missing")
    if family.endswith("_accessory"):
        require(isinstance(candidate.get("hostModelIds"), list)
                and all(isinstance(x, str) and x.strip() for x in
                        candidate["hostModelIds"]), "no verified host model IDs")
    require(candidate.get("releaseReady") is not True,
            "contract check must not create Production SKU")


if __name__ == "__main__":
    print(json.dumps(validate_catalog(), ensure_ascii=False, indent=2))
