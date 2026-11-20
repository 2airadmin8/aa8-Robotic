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

## Product PR single contract | architecture/data/QA/release (2026-11-17)

**One Product PR = one verifiable business delivery contract.** It is NOT a
stack of successful CI runs. Keep the existing Factory, Product Master,
Figma V3.2 authority, Product Standard V3.1 and GitHub manual-only release.

1. **Architecture owner** — website public SSOT remains data/products.json
   (currently 13). New candidate stays in tests/fixtures/*/product.json
   with releaseReady=false and no public HTML. ERP/PAI Product Master is a
   separate business system; never infer matching IDs or CRM writes.
   Header/Footer/menu and template/CSS/CI are cross-product shared code.
   Any PR touching shared Factory + one SKU is **GLOBAL_FACTORY**, must run
   regression of all 13 public products as well as the candidate.
2. **Business owner** — start with the buyer's question: what problem can
   this SKU address, what are verified product differentiators, and what is
   the next action? Keep ONE clear consultation CTA (with product/maker/
   source_page prefill). Put manufacturer documents in a consistent
   Specs/Resources region rather than repeating source links on every card.
   Technical cautions must be accurate and discoverable, not hidden as
   falsely guaranteed specifications nor repeated as sales-negative boilerplate.
3. **Data owner** — keep four distinct states:
   (a) raw manufacturer URL/snapshot hash/date and model/option/units;
   (b) machine bilingual/technical semantic correspondence;
   (c) independently signed human Japanese semantic/fact review;
   (d) authorized Production release. They may never collapse into a
   single PASS. The legacy field name approved_display in
   maker-live-contract.json is a DISPLAY CANDIDATE while its
   review_status=TRANSLATION_REVIEW_PENDING; the field name alone grants
   NO approval. A2 had 37 rows/74 cells technical verification evidence
   but still no attested human signoff. Differences with reseller data
   (model variant, battery count, payload modes) remain unresolved, not
   silently replaced by marketing copy.
4. **PM/CTO gate owner** — freeze versioned customer requirement, 4 family
   roles (biped, biped_accessory, quadruped, quadruped_accessory) and mapped
   semantic modules before development. Each redline BUG gets
   ID→original reference→Expected/Actual→RCA→patch SHA→PC/SP screens→
   independent verdict→P0/P1 closure. A screenshot checksum validates
   evidence integrity, not the independent visual conclusion.
5. **Independent QA owner** — technical QA, visual comparison, manufacturer
   human facts, CTA/lead E2E are FOUR independently labeled gates.
   DEV/authored screenshot tests cannot self-certify visual design.
   The existing AA8-N-015 can check code and browser, but a genuine
   independent design verdict requires actual reference-to-result
   comparison. Two CEO-controlled GitHub identities do not create an
   independent human reviewer.
6. **Delivery owner** — first finish Draft's CI and exact-SHA Vercel
   runtime readback, then separately clear factual/visual/business HOLD.
   Draft or Vercel Preview SUCCESS never permits main merge, Pages
   Production or CRM/ERP writes. Release remains one CEO-approved precise
   SHA with manual-only deploy and online SHA verification.

**Stop discipline:** mandatory safety, facts, functionality and P0/P1 must
be 100% resolved; approved optional visual quality can stop at 80 points.
At most three targeted repair iterations; recurrence after three is a
root-cause/policy issue, not another CEO screenshot task. No new
Factory/Runner/Workflow/Cron from this standard.

**Product PR handoff**: use ONLY .github/PULL_REQUEST_TEMPLATE.md. A single
exact-SHA report identifies TECHNICAL_PASS, VISUAL_HOLD/PASS,
HUMAN_FACT_HOLD/PASS, BUSINESS_E2E_HOLD/PASS and RELEASE_HOLD/READY,
with original source links and no fabricated approvals.


### 15 CEO redlines must have 15 DISTINCT screenshot captures
Previous A2 QA mapped several bug IDs to the same generic full-page PNG.
That is valid evidence the page rendered but INVALID as independent proof
of bug-by-bug coverage. Each V01-V15 now requires a distinct screenshot
from its relevant DOM section at PC1440/SP390/SP360, plus screenshot byte
uniqueness across bug IDs and the existing CRC/size/SHA integrity checks.
Original reference-to-current visual comparison still remains human/QA
HOLD until actually attested; no automated approval is invented.

## Corporate Product Visual Standard V3.3 — source + executable FAIL gate (2026-11-19)

**Visual candidate ONLY; V3.2 approved visual baseline and Product Standard V3.1
content remain untouched until V3.3 is independently certified.**
Exact contract: `docs/governance/AA8_PRODUCT_VISUAL_STANDARD_V33.md`;
mother verified source: `ops/brand-preview/mother-site-contract-v1.json`;
v33 contract: `ops/brand-preview/corporate-product-visual-v33.json`.

- CEO non-negotiable rule: every product specification surface WHITE #FFFFFF.
  All source comparison tables must use header WHITE, category #EEEEEE,
  odd #FFFFFF, even #F5F5F5, border #D9D9D9 and text #333333.
  Twelve products render a real table; X2 EDU retains its existing
  paragraph-based specs while following identical neutral visual rows.
- Fonts/color from parent theme must be tested at COMPUTED STYLE level:
  Noto Sans JP, brand #009BD2 / #0069B5 / #00B2BC, body text #333333,
  footer #F4F8FA. Do not count a CSS declaration as a visual pass.
- Existing build_site.py installs ONE V3.3 visual owner stylesheet on all 13
  public product *build artifacts*, not on manufacturer facts or Product Master.
  Original A2 isolated fixture stays independently controlled.
- MANDATORY CI: existing Python corporate-source contract test AND existing
  hp-shared-governance Playwright 13x PC1440/SP390/SP360 CSS computations,
  real CTA prefill, one shared shell, no overflow; 1023/1024 mother menu edge.
  Missing one product, wrong neutral color, wrong font or bad hyperlink = FAIL.
  No duplicate PR/job/Runner/Factory/scheduled monitor.
- Independent visual source-to-render verdict, native Figma V3.3 editable
  components/variables and genuine design review remain HOLD. Figma current
  Starter/View + MCP quota rejection means this round cannot invent Figma PASS.
  Technical CI green DOES NOT authorize release; CEO exact-SHA approval
  and manual-only Pages are still required.
