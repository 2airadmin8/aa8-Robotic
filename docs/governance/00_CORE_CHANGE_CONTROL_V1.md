# AA8 Common AI Development Change Control V1.1

## Why
Reduce repeat defects, per-product rework, CEO interruptions and marginal development cost. Technical QA alone is not product or business success.

## Highest operational principle: minimal cost, quality first, then STOP
- "**80 points and close**" is a management shorthand for **approved optional visual/content quality**, not a numerical software safety score.
- **100% of applicable mandatory gates**: security, privacy, manufacturer facts, functional acceptance, independent QA and release safety must pass. Missing evidence = HOLD regardless of aesthetic score.
- Once the approved baseline is met, close the scoped task; P2/P3 polishing needs actual customer/business evidence, a measurable baseline, time budget and observable success metric.
- Max 3 bounded AI repairs; overrun = HOLD, not additional CEO prompts.
- The CEO decides product/business exceptions and controlled Production release, not repeated unit-test/CSS review.
- We do NOT claim efficiency gains until ≥2 comparable real product runs have evidenced source-ready/Preview times and human interventions.

## Independent enforcement versus documents
- Policy source is the shared-drive AA8 Common Governance Core; version-pinned repository adapter includes docs/governance, docs/governance/hp-design-code-trace-v1.json and scripts/hp_governance_quality_gate.py.
- **Trusted-main pull_request_target check** reads PR metadata and changed-file list using read-only permissions; it never checks out untrusted PR HEAD, never uses secrets/writes, and never approves or deploys.
- Required PR inputs use the **existing** .github/PULL_REQUEST_TEMPLATE.md. No second approval form, Factory, scheduler or Runner.
- This is a technical status, NOT a separate human reviewer. Independent AA8-N-015 source/browser QA remains a distinct real QA process.
- On adoption, GitHub branch protection must require the trusted policy-independent-gate status **after the first verified live run**; until then, its result is advisory rather than an enforced merge block. Never claim this status required if not configured.
- Prior open PRs are exempt from new intake fields only. CI, privacy/security, actual QA and precise-SHA merge gates always remain mandatory.

## Intake gate (required before implementation)
Every new Issue/PR records: why/evidence, P0-P3 class, business value, source, accountable owner, impacted products/components and excluded files, objective acceptance, negative tests, rollback, max time/repairs and stop condition.
- P0: confirmed critical failure/safety. Repair root cause and add regression.
- P1: approved new capability or fact-verified product. Standard input and independent QA.
- P2: measured content/UX optimization with an observable expected result. Batch.
- P3: aesthetic preference. Backlog by default; only CEO-approved exception.

Absent evidence, impact matrix or acceptance => INPUT_REQUIRED/HOLD. Do not turn every visual suggestion into a new priority.

## Design ownership and frozen standards
- Lock approved PC/SP design and semantics BEFORE implementing a SKU.
- One authoritative Header/Footer/Menu/CTA behavior, page-level product content separate.
- Shared code modification must run cross-product regression, not a per-SKU workaround.
- Figma reference, semantic Product Standard and Factory renderer may carry DIFFERENT versions. Explicitly record compatibility; never assume equal version numbers.
- Unknown or contested official specs/prices/warranty/SDK/photo permissions stay unknown, not fabricated.

## Existing Factory flow
Evidence → scoped Draft PR → CI → independent machine/browser QA → bounded AI repair (max 3) → consolidated CEO exception/Production decision → manual-only single release → production SHA recheck.
Development and independent QA must use genuinely distinct checks. A second GitHub account owned by the same person is NOT independent human review.
CEO does not manually recheck every CSS patch; technical QA returns verifiable exact-SHA evidence.
Once approved scope is PASS, close. Later ideas are separate tasks. Fail = HOLD, never infinite retry.

## Learning
Every genuine BUG: original reproduction, root cause, minimal patch, repeat-prevention regression and affected-component coverage. A recurring BUG proves governance failed.
Every new SKU: source-ready and Preview timestamps, intervention/repair counts and traceable exact-SHA evidence. Unknown is blank, never zero.
Every weekly business improvement: authoritative data, date window, max 3 proposals, hypothesis, success metric and no-go facts. No auto production edit.

## No internal-data publication
The static site artifact is public. Governance documents, Factory efficiency and inquiry/GSC aggregates, and internal product-type contracts are non-publishable even when version-controlled. The build must exclude docs/, ops/, and data/hp-page-family-contract-v1.json while preserving public data/products.json. Both PR CI and existing manual-only Pages verification must FAIL CLOSED if an internal artifact reappears in _site.

## No bypass
No duplicate Factory/Runner/SSOT, autonomous main merge, unapproved Production deploy, CRM writes while paused, invented maker facts, false CEO approval or new scheduler if existing authorized task can be extended.
Changing this common policy requires semantic version change, a GitHub PR and auditable review.
