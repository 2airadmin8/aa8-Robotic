# AirAdmin8 Robotics HP｜Governance Adapter V1.1

## Authorities
Visual: CEO-approved Figma Product Page Standard V3.2.
Semantic roles: Product Standard V3.1, not identical HTML block order.
Opt-in renderer: existing G1 Factory V1, NOT a new renderer.
HP SSOT: data/products.json (13 public entries). RobotFDE business Product Master is separate; IDs are not automatically interchangeable.
Shared Header/Footer: includes/site-header.html, includes/site-footer.html.
Shared layout owner: assets/css/shared-layout.css.
Production: existing main, manual-only pages.yml. CRM remains PAUSED.

## PM/CTO design-to-code traceability
- Visual reference: Figma Product Page Standard V3.2, reference https://www.figma.com/design/uo56l51NgUqit4976LV6P2. Repo-only audit cannot prove full Figma pixel parity; real PC/SP comparison remains separate.
- Semantic: docs/product-page-standard-v3.1.md. Existing opted-in renderer: docs/product-factory-v1.md, scripts/product_factory.py. Version numbers have distinct scopes; do not force them to match.
- Machine-readable map: docs/governance/hp-design-code-trace-v1.json. Six modules: SHELL, PRODUCT_FACTS, CTA, PRIVACY, GROWTH, GOVERNANCE. Each maps one design authority to actual implementation and CI-registered regression tests.
- New applicable PRs use the existing GitHub PR template: evidence/value, affected design/code IDs, 13-product PC/SP impact for shared shell, negative QA, safety exclusions, HOLD, exact-SHA rollback.
- scripts/hp_governance_quality_gate.py runs in the existing ci.yml. The read-only policy-independent-gate uses trusted base SHA on pull_request_target. Its status is not a required branch-protection check until separately verified and configured.
- Audit gate is structural traceability, not live CEO approval, Figma visual parity or proof of sales ROI.

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

## Public artifact boundary (P0 release gate)
Internal docs/ and ops/ contain governance and business reporting, not website assets. They must never be copied into public _site/. data/hp-page-family-contract-v1.json is an internal contract; data/products.json stays public because the existing catalog uses it. A real build must prove exclusion, and verify_release.py must reject any _site copy of these items before a manual release.

## P2 Data-driven business signals
Read-only: AirAdmin8_Robotics_GSC_Master spreadsheet 1VTLnGjyld_pNWBad-gJcPNqGy0jUnrDKiiU18S6OgbM, tabs 99_Config/01_Daily/02_Query/03_Page; Inquiry Master 1dgoeLCBJVE0CXBGgizUwA-ozrRVvJw6Ng9gfGN0h8wI, tab 01_Inquiry.
Use successful synchronized last 7 complete days vs previous 7, JST; verify source freshness and page/query coverage. Google property-wide Daily differs from Page/Query totals due to reporting. Do not treat masked queries or omitted rows as zero.
Aggregate only: no names, emails, phone, messages or submission tokens. Separate genuine leads from tests/UNKNOWN; no CRM claims.
Output <=3 PROPOSAL_ONLY improvements each with URL, KPI, dates, expected testable effect, exclusions and hold rule.
Use existing AirAdmin8 Robotics V3 SEO/GEO recurring task; no new GSC pipeline or cron.

## P3 Factory KPI
source_ready_at, preview_ready_at, first_qa_at, manual_code_edits, rework_iterations, ceo_interventions, repeated_bug_count, exact evidence_url.
Unknown source ready dates for historic H2 Plus/A3 Ultra are UNKNOWN, so initial efficiency gain is unproven. Require >=2 genuinely comparable verified SKUs before any claim of improvement.


## V1.1 implementation audit: shared CSS owner, strict on new rules only
- Canonical CSS owner remains `assets/css/shared-layout.css`. `scripts/verify_shared_css_ownership.py` audits the external CSS and publishable HTML `<style>` blocks, including old X2 EDU, G1 fallback and the canonical Footer include inline CSS. These are legacy declarations, not a second renderer.
- Historical non-owner declarations remain visible warnings, compared with the **exact PR base SHA**. New or modified declarations targeting Header/Footer/Menu in non-owner CSS/inline style sources **fail existing CI**. Changed responsive media or property declarations also fail. Missing/invalid base SHA fails closed.
- Against main base `c42f19c90f9165101369205d71931f4886ab75ae`, the known legacy baseline contains 32 declarations in three HTML files (X2 EDU 8, G1 12, site-footer include 12). This is not a zero-warning claim. X2 EDU's actual SP menu problem is separate P0.
- `tests/test_shared_css_owner_delta.py` covers negative new CSS/inline overrides, changed legacy rules, invalid base, plus positive canonical-owner edits. Existing `ci.yml` applies the delta gate to PR or scoped repair events without additional jobs, reviewers, runners, schedulers, or Production permissions.
- This gate does not establish GitHub Branch Protection Required Check configuration. Existing `pages.yml` stays manual-only and no historical CSS sweep is authorized.

## Preview bundle contract — all products, no separate Factory (2026-11-15)

- The existing Product Factory Preview and CI must enumerate EVERY
  `tests/fixtures/*/product.json` candidate, not a hard-coded A2/X2 list.
  The shared asset walker `scripts/verify_preview_bundle.py` collects local
  HTML src/srcset/poster/link refs plus CSS imports/url() and SVG references,
  then produces an exact SHA1 and byte size manifest for the combined bundle.
  Missing local referenced assets FAIL before CI browser tests.
- Vercel Preview deployment review **requires a second independently sourced
  file-tree check** after READY, using the exact deployment ID, source HEAD,
  `target=null`, and SHA1 of every manifest file. The checker has read-only
  `--verify-deployed` mode; any mismatch or absent file = PREVIEW_BUNDLE_HOLD.
  SSO login readiness alone does not prove CEO browser review or source files.
- The existing manual-only Pages release invokes `verify_release.py`, which
  now uses the same dependency resolver for ALL public products/*.html.
  The legacy G1-D dead CSS reference was removed after this gate caught it.
- This repo's GitHub CI cannot read authorized Vercel files without the
  connected Vercel deployment action. Until the authorized Review deployment
  operation always invokes this exact post-deploy check, it remains a required
  external Gate rather than a self-enforcing CI status. Do not call that
  remaining deployment connector orchestration E2E completed, do not grant
  Preview Ready/CEO acceptance on GitHub CI alone, and do not add new Runner,
  workflow, scheduler, Production credential or automatic Pages release.

## Git-linked Vercel runtime SHA readback (2026-11-16)

The existing Git-integrated Vercel Review project returns 404 for the source-file tree on a real source=git deployment. Reuse the same trusted-main event handler and independent CI asset manifest, but verify actual SSO-protected HTML/CSS/JS/images using strict immutable deployment-host SHA1 checks on Git source deployments. VERCEL_TOKEN and VERCEL_AUTOMATION_BYPASS_SECRET must be supplied as protected secrets in GitHub Actions and never exposed. Unknown source, missing HTML, redirect or SHA mismatch is HOLD, not CEO_REVIEW_READY. Full activation still requires main exact-SHA approval and a real post-deploy event run.

## Trusted-main minimal activation of Vercel postdeploy verification (2026-11-16)

- The original A2 Draft PR #180 is NOT merged to main and its 37×2 product
  facts / business release permissions remain isolated.
- To receive Vercel's native vercel.deployment.ready event, the existing
  CI workflow MUST contain the repository_dispatch listener on GitHub's
  protected default branch. This narrow activation carries only the trusted
  postdeploy verification code, the one existing workflow event job and the
  CEO-preview handoff status safeguard, not the A2 website.
- The event is valid only for the connected x2-edu-make-review project,
  a READY Preview, exact source SHA, a matching approved CI file manifest,
  and real deployed HTML/CSS/JS/SVG/media bytes. API(upload) source trees
  are verified with SHA1; Git(auto) deployments return 404 for the Files API,
  and are verified through SSO-protected HTTP runtime SHA1 using the existing
  automation-bypass credential. Missing evidence, token or source output HOLD.
- Configure GitHub Actions protected secrets VERCEL_TOKEN and
  VERCEL_AUTOMATION_BYPASS_SECRET without exposing them to Chat or
  repository source. A Git-linked Preview not serving the generated product
  HTML is HOLD, even if Vercel says READY.
- The only automated success effect is GitHub commit status
  aa8-preview-postdeploy=success for the exact authorized head; no Pages
  Production release, auto-merge or fabricated human CEO signoff.
- The default-branch merge of this narrow activation must still receive
  the CEO's exact-SHA approval and pass independent QA. An isolated Draft
  CI green alone is not proof of event-triggered postdeploy E2E.


## A2 CEO redline visual evidence gate (2026-11-17)

- The existing CI and separate-technical-qa runner must download and verify the same-run exact-HEAD screenshots for all V01-V15 on PC1440 / SP390 / SP360, plus clicked mobile CTA screenshots. Missing, damaged, or wrong-viewport PNG = CI FAIL.
- Existing scripts/hp_governance_quality_gate.py checks screenshot bytes, dimensions and SHA256, and writes an A2 matrix into the existing separate-QA artifact. No new workflow, job, runner, Factory, schedule or standalone approval process.
- The only automatic conclusion is screenshot_integrity=PASS and visual_approval=HOLD. Original CEO redline comparison, every P0/P1 closure and genuinely independent visual judgment remain NOT_ATTESTED until separately evidenced on the exact same SHA.
- Technical CI/Preview SHA may pass independently to keep the existing postdeployment hash check working. Such PASS must NEVER be presented as visual signoff; normal Factory handoff remains WAIT_DESIGN_QA/HOLD.
- CEO-controlled GitHub accounts do not count as separate people. If original reference or independent verdict is missing, Production NO-GO. The 80-point stop rule applies only to optional aesthetics, never to mandatory safety, facts, functionality or P0/P1 defects.
