# AA8 HP Governance Version History

2026-11-14 — Candidate V1.0:
- Extract common change-control rules into reusable module.
- HP adapter covers 4 product types; 2 real robot baseline and 2 accessory contract-only.
- Shared Header/Footer 13 product build propagation test, contact product-prefill QA.
- GSC/Inquiry read-only aggregate proof and no more than 3 proposals.
- Factory efficiency baseline with UNKNOWN dates instead of fabricated gains.
- No second Factory, no new Runner, no mass HTML rewrite, no CRM write, no Production release.
- Activation follows exact-SHA GitHub CI, independent QA, and separate merge authorization.

2026-11-14 — V1.0 publication-hardening patch:
- Block public publishing of docs/governance, ops KPI and inquiry aggregates, and internal product family contract.
- Enforce a negative gate at CI and manual Pages release, preserving public data/products.json.
- Validate actual JST run date to reject stale GSC snapshots; require first QA evidence for verified Factory speed.
- Correct initial H2 Plus / A3 Ultra provenance to PR #158 / #164, not X2 pilot PR #173.

2026-11-14 — PM/CTO governed quality V1.1 candidate (not activated on main):
- Clarify approved optional-quality stop vs mandatory safety/functional/data/QA 100% gates.
- Bind design standards to code and existing automated regression through a machine-readable six-module trace.
- Reuse the existing PR template, adding minimal scope/impact/stop fields rather than introducing a second process.
- Add candidate CI intake check and trusted-base read-only pull_request_target check, with no untrusted PR checkout, writer token, new Runner or Production deployment.
- Preserve prior open PRs; branch-protection independent check must not be falsely claimed required until real live evidence and authorized configuration.


## 2026-11-17 | PR #180 deep product-delivery governance audit (Draft only)

- A2 product candidate plus shared Factory/CI/CSS changes must have
  GLOBAL_FACTORY scope, with all 13 public products regressed in addition
  to A2. Original PR #180 involved 39 changed paths, including one
  existing G1-D stylesheet reference removal.
- Existing Product PR template now requires buyer value, four-family
  content, public vs isolated SSOT, per-redline design evidence, 4
  independent QA states and one precise-SHA release decision.
- A2 has independent-device TECH_SEMANTIC_QA_PASS for 37 rows/74 cells,
  but ALL manufacturer contract rows are TRANSLATION_REVIEW_PENDING and
  human_fact_review=NOT_ATTESTED. The misleading historical field label
  approved_display does not itself mean any legal or human approval.
- Visual screenshot artifacts and byte hashes are not independent
  reference-to-implementation approval; full visual P0/P1 verdict remains
  NOT_ATTESTED/HOLD until independently evaluated.
- Eliminated only one duplicate build-step invocation of the
  preview-postdeploy bridge test; separate technical QA still runs it.
- No new PR, Factory, runner, workflow, scheduler, source number edits,
  production merge, CRM/ERP write or Pages publish.
