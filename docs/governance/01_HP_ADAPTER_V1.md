# AirAdmin8 Robotics HP｜Governance Adapter V1.0

## Authorities
Visual: CEO-approved Figma Product Page Standard V3.2.
Semantic roles: Product Standard V3.1, not identical HTML block order.
Opt-in renderer: existing G1 Factory V1, NOT a new renderer.
HP SSOT: data/products.json (13 public entries). RobotFDE business Product Master is separate; IDs are not automatically interchangeable.
Shared Header/Footer: includes/site-header.html, includes/site-footer.html.
Shared layout owner: assets/css/shared-layout.css.
Production: existing main, manual-only pages.yml. CRM remains PAUSED.

## P1 Four content profiles
- Biped robot: research capability, motion safety, controller, verified SDK interface, use cases.
- Biped accessory: maker-approved host models/revisions, mounts, electrical interface, safety and warranty.
- Quadruped robot: terrain, mobility, verified payload, navigation, developer functions, safety.
- Quadruped accessory: exact host version, mounts, power, communication, safety.
- Existing mobile-manipulation is a distinct LEGACY category. Preserve it; not an accessory.
- Biped real baseline: Unitree H2 Plus. Quadruped real baseline: Unitree Go2 EDU. Two accessories: CONTRACT_ONLY until actual sourced product evidence exists.

Common semantic roles: identity/hero, capabilities, uses, official media provenance, specifications, resources/SDK, purchase/PoC flow, FAQ, related, product consultation. Optional comparison only when real model differences exist.
Maintain manufacturer claims and customer value separately from shared design assets.

## Change impact matrix
- Header/Footer/menu: one shared include change → recompile/test all 13 existing product pages.
- Shared contact form/CTA: test product prefill from each of 13 product pages at 1440px and 390px. DO NOT submit inquiry.
- Product-specific copy: only affected SKU plus shared regression; preserve approved specialized sections.
- Manufacturer facts/price/source: explicit manual fact gate; cannot auto-amend from GSC or generated copy.
- Full HTML redesign: out of scope; no mass migration of 13 existing pages.

## P2 Data-driven business signals
Read-only: AirAdmin8_Robotics_GSC_Master spreadsheet 1VTLnGjyld_pNWBad-gJcPNqGy0jUnrDKiiU18S6OgbM, tabs 99_Config/01_Daily/02_Query/03_Page; Inquiry Master 1dgoeLCBJVE0CXBGgizUwA-ozrRVvJw6Ng9gfGN0h8wI, tab 01_Inquiry.
Use successful synchronized last 7 complete days vs previous 7, JST; verify source freshness and page/query coverage. Google property-wide Daily differs from Page/Query totals due to reporting. Do not treat masked queries or omitted rows as zero.
Aggregate only: no names, emails, phone, messages or submission tokens. Separate genuine leads from tests/UNKNOWN; no CRM claims.
Output <=3 PROPOSAL_ONLY improvements each with URL, KPI, dates, expected testable effect, exclusions and hold rule.
Use existing AirAdmin8 Robotics V3 SEO/GEO recurring task; no new GSC pipeline or cron.

## P3 Factory KPI
source_ready_at, preview_ready_at, first_qa_at, manual_code_edits, rework_iterations, ceo_interventions, repeated_bug_count, exact evidence_url.
Unknown source ready dates for historic H2 Plus/A3 Ultra are UNKNOWN, so initial efficiency gain is unproven. Require >=2 genuinely comparable verified SKUs before any claim of improvement.
