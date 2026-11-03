# Product CTA & SEO/LLMO V1 concentrated fix — 2026-11-04 JST

## Scope
Existing repository: `2airadmin8/aa8-Robotic`. Baseline main `f807932fcbcb06e4c6af1b5c1d36cb177beaf767` (Pages run `41634281263` succeeded before this change).

CEO's sequence: (1) correct customer-facing inquiry CTAs and model copy; (2) complete five legacy product JSON-LD; (3) do one concentrated PC1440/SP390/SP360 review, then request **one exact-SHA approval** for merge and a single manual Pages production release. No production change is approved by this document.

### Fix 1: General consultation is not an automatic university purchase
Generic "導入・研究相談" hero CTAs on Unitree G1, G1+, H2, H2-X and AGIBOT A3 Ultra now carry a correct `product` and `maker` but omit the `service=university-procurement` that had forced `見積・大学購買`. Existing `assets/js/contact-v2.js` safely defaults product-only consultations to `導入条件整理`; users may change category. G1+ EDU's intentionally procurement-specific link and G1's catalog link are unchanged.

H2-X: both hero and illustrated conversion CTA now carry `maker=Unitree`; old second-section headline `何を検証するかから、H2を選ぶ。` now correctly identifies `H2-X`. Its official design-contract CTA in the existing `data/products.json` Product Master is updated in the same change, avoiding Factory drift.

### Fix 2: Five older live product pages get factual Product JSON-LD
Extend the existing `scripts/inject_structured_data.py` publish-time injector to include G1, G1-D, Go2 EDU, X2 EDU and AgiBot G2, **in addition to** the six recent pages. Each detail page maps by `detailPage` from the sole approved Product Master; no new data store, no second factory. Official image path and `imageStatus=official` are mandatory. Emit one `Product` object with name/brand/manufacturer/image/description, correct product class and canonical mainEntityOfPage. Omit unverified prices, offers, ratings, availability, SKU, and review claims. Keep `WebPage`, breadcrumbs, and organization schema.

### QA and release safety
- Python regression: `tests/test_product_cta_schema_20261104.py` (legacy 5 plus original 6, CTA intent, original catalog/EDU controls).
- True-browser regression: `tests/product-cta-llmo-20261104.spec.js` (click five CTA links in PC1440/SP390/SP360, assert form source fields/category/referrer, verify all eleven pages have exactly one Product schema, verify no document horizontal overflow, H2-X headline).
- Both test suites are included in existing `.github/workflows/ci.yml`; existing independent and CI gates remain unchanged.
- Local factory audit, v3.1 standard, full build, structured-data injection and release verification must all PASS. Later AA8-N-015 independent QA and actual HTML Preview review are separate gates.
- **No live customer form POST, no external emails, no CRM/PAI data writes, no direct main merge, no automatic Pages deployment.**
- X2 EDU old Design Issue #109 requires actual approved Figma/visual comparison before whole-page Design PASS. H2 Plus Issue #160 must be checked against the current Production and closed only on verified evidence.
- Once CI/independent QA and interactive noindex preview are acceptable, submit exactly one candidate HEAD SHA for CEO approval. Changes to SHA void prior approval. Manual `pages.yml` only, once; post-release verify public SHA, PC/SP, CTA prefill, image and SEO facts.

### CI regression root-cause reconciliation
The initial PR run #41701300790 failed two **old contract** tests: (1) A3 Ultra Factory generated its default university-procurement URL even though the manually edited HTML used general consultation; (2) V3.1 expected the older H2-X URL to have no maker. Both were fixed at their roots by declaring "contactService": "" in A3's existing Product Master pageFactory configuration (the Factory already handles empty services) and updating the exact V3.1 expected H2-X maker provenance. Original 8 V3.1 and 20 Factory regression tests now pass; no CI gate was disabled.
