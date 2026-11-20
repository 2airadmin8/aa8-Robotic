# AirAdmin8 Robotics｜製品ページ共通標準 V3.1

Date: 2026-11-03  
Repository: `2airadmin8/aa8-Robotic`  
Change set: existing Draft PR #165 / no production deploy authorization.

## 1. Design philosophy

**One contract, not one identical page.** Preserve the approved G1 visual narrative,
X2 EDU assembly/ROS2 curriculum, H2-D model selection, G1-D data lifecycle,
Go2 EDU field mobility, and Marvin VLA/teleoperation.

Never replace a page with generic product cards, invent SDK compatibility,
use unverified data, create a second Product Master, or infer commercial terms.

## 2. Common modules and optional modules

Every product has a common *semantic role*; exact HTML structure/order and visual
composition can legitimately differ by product:

| Order | Standard role | Contract |
|---|---|---|
| 00 | Shared Header / Footer | Existing includes; do not duplicate |
| 01 | Hero | H1, product identity, manufacturer, strongest relevant image and action |
| 02 | Core capabilities | Verified product benefits, no generic marketing filler |
| 03 | Use cases / research | Buyer-facing tasks, not hypothetical guarantees |
| 04 | Media / structure | Original verified images/videos; alt and provenance |
| 05 | Model comparison | **Optional**. Only when a real, meaningful SKU choice is documented |
| 06 | Specifications | Official claims and exact model/option/date boundaries |
| 07 | SDK / technical material | Existing Resources, manufacturer docs; compatibility separately verified |
| 08 | Solution / PoC | Existing support.html sections, avoid second service page |
| 09 | Purchase / implementation | Consult → configuration → estimate → deliver → start; category-tailored |
| 10 | FAQ / cautions | Buyer objections and safety/legal/compatibility uncertainties |
| 11 | Related / alternatives | Relevant models; no automatically generated false comparisons |
| 12 | CTA / inquiry | Product-specific consultation, source attribution, no default false intent |

**Not all semantic roles require a dedicated full-width section.**
For existing rich pages, original hero/story/technical blocks satisfy the roles.
For sparse pages only, a small static Resources/Support gateway is inserted;
it does **not** add a redundant third consultation CTA.

## 3. Data SSOT

The existing `data/products.json` is the single Product Master.

- `id`: immutable machine identity, not inferred from user-facing display name.
- `name`: canonical display name, manufacturer/source-controlled.
- `manufacturerName`: maker attribution.
- `categoryId`: existing search/category ID; NOT replaced by family.
- `detailPage`: canonical product-page route.
- `pageStandard.version`: `3.1`.
- `pageStandard.family`: `humanoid`, `quadruped`, or `mobile-manipulation`.
- `pageStandard.customerValue`: one unique product-specific research/use-case summary.
- `pageStandard.preserveSectionIds`: approved product-specific content sections.
- `pageStandard.resourcesHref`: existing Resources URL, no fabricated SDK download.
- `pageStandard.supportHref`: existing support.html / verified section IDs.
- `pageStandard.showBridge`: explicit opt-in for only sparse detail pages.

**No new database, no new product facts, no fake videos, no new CRM fields.**

Consultation links preserve their existing `product`, `service`, `theme`,
`case` fields and only append `maker` when missing. A source with an approved
frozen CTA contract (H2-X) retains its exact href; the in-page product ID is
still recorded in the page element. Product aliases such as X2 EDU and G1+ EDU
remain intentional original configurations rather than silently rewritten.

The form may already persist `source_product`, `source_maker`, `source_page`
in Inquiry Master. `data-product-id` is **not** equivalent to a persisted CRM
ProductID; a later authenticated CRM gate must resolve and verify the mapping.

## 4. Existing page classification

| Product | Family | Specialty to preserve | New gateway? |
|---|---|---|---|
| Unitree G1 | humanoid | Six technical figures, RL, force hand, G1 EDU comparison | No |
| AgiBot X2 EDU | humanoid | Assembly curriculum, ROS2, purchase flow, academic cases | No |
| Unitree H2-X | humanoid | Approved hero/video/3 image CTA, EDU selection | No |
| Unitree H2 | humanoid | Bipedal/HRI and EDU distinction | No |
| Unitree G1+ | humanoid | Vision, neck, external power, EDU | No |
| Unitree H2 Plus | humanoid | VLA/Thor, verified SDK entry, solution, 5 steps | No (V3 modules already present) |
| AGIBOT A3 Ultra | humanoid | Official A3 Ultra gallery/videos, reception, patrol | Yes |
| LimX Oli | humanoid | Bipedal motion and research comparisons | Yes |
| Unitree Go2 EDU | quadruped | Mobility, navigation, inspection and gait research | Yes |
| Unitree G1-D | mobile-manipulation | Teleoperation/data capture/training chain | Yes |
| Unitree H2-D | mobile-manipulation | Moving grasp, Standard/Flagship choice | Yes |
| AgiBot G2 | mobile-manipulation | Two-arm PoC and force control | Yes |
| Tianji Marvin | mobile-manipulation | Teleoperation, recording, HDF5/RLDS context | Yes |

## 5. Implementation and release gates

1. Generate from the existing master: `python scripts/product_page_standard_v31.py --apply`. Never execute this on Production.
2. Read-only audit: `python scripts/product_page_standard_v31.py --check`.
3. Python tests assert 13/13, unique IDs, original section preservation, CTA attribution and Product Factory parity for H2 Plus/A3 Ultra.
4. Browser tests inspect every product at PC 1440 and SP 390/360; bridge scope, links, white background, no horizontal overflow.
5. Independent QA (AA8-N-015) rechecks images, broken links, source of manufacturer facts, meaningful original features, CTA prefill.
6. CEO centralized approval of precise PR HEAD, updated main SHA and CI. Deploy remains **manual-only**, single controlled dispatch after separate release authorization.
7. After release verify `/deploy-meta.json` SHA and all 13 URLs; CRM/Inquiry E2E has a separate permission gate (Issue #166).

A successful static/visual test does **not** mean current production is updated,
nor does it certify SDK compatibility or actual CRM customer creation.

## 6. Existing data-quality debt (not silently declared complete)

- Five existing Product Master entries are marked with placeholder-image status;
  leave these warnings visible until manufacturer-proven material replaces them.
- Exact Unitree/H2 SDK compatibility is still a version/SKU question.
- Inquiry Master → Customer Master/PAI Case end-to-end real write is separate
  and must never be assumed from query-prefill tests.
- Existing manufacturer CTA links are not all category-neutral by design;
  preserve explicit buyer-intent links unless product-level review says otherwise.
