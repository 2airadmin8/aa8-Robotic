# AirAdmin8 Robotics | Product Page Factory V1 (2026-10-31)

## 1. Existing single sources of truth
- Product facts / product catalog: data/products.json schemaVersion 5. Do not create another Product Master.
- Visual baseline: CEO-approved G1 HTML and assets/css/g1-product.css; new opt-in pages use scoped assets/css/g1-factory-v1.css.
- Shared header/footer: existing includes/ only. Isolated Factory Preview must use both canonical includes; existing approved candidate-mode output remains frozen; build_site.py replaces both in release artifacts. No duplicate menu listeners or second renderer.
- Legacy SEO overrides: data/product-seo-v1.json remains for legacy pages. New opt-in pages obtain metadata directly from Product Master.
- Deployment: same main, existing PR CI, original manual-only pages.yml with one deploy attempt and no retry.
- No second crawler, automation, runner, factory or publishing route.

## 2. Mandatory eight gates
1. Official manufacturer facts: SKU, product names, sources, source dates, undefined sales terms.
2. Product Master: approved image, 3 gallery/CTA photos, official video and sources, validated paths.
3. G1 fixed layout: white Hero/body, geometry CTA background, three illustrated cards, responsive PC/SP.
4. AI isolated generation: draft noindex HTML preview; never write main.
5. CI + independent QA: source facts, negative tests, real Chrome PC1440/SP390/SP360, image and video, contact CTA.
6. CEO: real HTML Preview and exact HEAD SHA, one decision per stable product candidate.
7. Controlled merge and production: latest main, branch protection, CI, independent QA, Pages operational, no concurrent deploys, one manual dispatch, failure-safe stop.
8. Production acceptance: exact deploy-meta SHA, PC/SP, cards/media/forms, index and GEO visibility. Close issue only on production evidence.

## 3. CLI operations
- python scripts/product_factory.py audit
  Validates all 13 catalog products and frozen approved contracts. Reports old placeholder images without pretending they are official media.
- python -m unittest discover -s tests -p test_product_factory.py -v
  Contract, XSS, asset paths, missing source, unknown price, duplicate image, CEO G1-design regression.
- python scripts/product_factory.py generate --id PRODUCT-ID --mode preview --output PATH/preview.html
  Isolated noindex,nofollow Preview. Refuses source products/ folder, refuses overwrite.
- python scripts/product_factory.py generate --id PRODUCT-ID --mode candidate --output products/PRODUCT-ID.html
  Requires explicit pageFactory.releaseReady=true in the same Product Master row; still only a PR candidate, not a merge or deployment permission.
- Scripts never send inquiry email, change production content, commit, merge or deploy automatically.

## 4. Opt-in schema inside an EXISTING data/products.json row
- pageFactory.template = g1-v1
- pageFactory.officialSource = https URL for manufacturer primary source
- pageFactory.title, metaDescription, heroLead
- pageFactory.facts >= 3, each with label, value, sourceUrl
- pageFactory.applications >= 2, each with title, description, sourceUrl
- pageFactory.specifications >= 3, each with label, value, sourceUrl
- pageFactory.faq >= 3, each with question, answer
- pageFactory.images >= 3, each with src, alt, sourceUrl; src must exist in local assets/
- pageFactory.videos: verified entries each with src, poster, label, sourceUrl; 0 is permitted ONLY when pageFactory.videoAvailability=not_provided_by_manufacturer; no fictional video or video CTA, browser decoding checked when provided
- pageFactory.ctaImageIndexes is three distinct gallery image indexes
- pageFactory.releaseReady=false by default; no indexable page until contents validated and approved
- Existing parent row supplies id, name, manufacturerName, summary, image, imageAlt, verifiedAt, statusLabel, priceLabel, leadTimeLabel, detailPage.
- Unverified price, lead time, SDK scope or availability must remain confirmation required.

## 5. Implementation & safeguards
- H2-X now has a designContract in existing Product Master freezing hero image_007.webp, approved geometric CTA, three CTA image files, three real MP4 assets and links.
- Existing H2-X HTML, CSS, sales copy and production site are NOT changed by this factory PR.
- Existing CI runs source validation and an ephemeral noindex synthetic product in Chrome; the fixture is generated only into local _site by CI, not committed or production deployed.
- Existing scripts/verify_release.py runs the factory contract check during the manual Pages publish.
- Existing build_site.py selects analytics-events.js rather than legacy seo.js for generated pages.
- Existing static meta injector derives generated-page OG image/title/description from the Product Master; legacy manual pages stay unchanged.
- Existing build and shared-header owner rules are preserved.

## 6. KPI and next acceptance
Delivery target: three different consecutive real product pages with <= 1 normal CEO Preview approval each; zero repeated G1 layout regressions; 100% CI/independent QA/production SHA evidence.
Business success is separate: Search Console impressions/clicks/CTR, product CTA clicks, actual inquiry delivery, meetings, quotation and orders. Page QA green does not prove sales.
Known media backlog: AgiBot G2, AgiBot X2 EDU, LimX Oli, Unitree Go2 EDU, Tianji Marvin are still explicitly labeled placeholder in existing Product Master. Do not silently substitute unverified photos.
Next true trial: select a fact-verified REAL new product with manufacturer sources, execute Master -> noindex Preview -> CI + QA -> exact HEAD CEO approval -> single release -> real production verification. Do not claim factory mass-production proven until 3 consecutive releases pass.


## メーカー仕様表の行数・モデル数と自動検査（A2実装ルール）

- メーカーが複数モデルの正式仕様表を公開している場合、先に一次出典のモデル名、カテゴリー順、各カテゴリーの項目行数を凍結する。2モデル列を「2倍の行数」と数えない。
- A2公式表は2モデル（A2／A2-PRO）、4区分、37項目行（機械10／電気15／性能9／その他3）。A2標準版を主商品とし、PROを同ページの比較対象とする。メーカーにない追加SKU／価格／SDK互換を捏造しない。
- 正式モデル差（LiDAR、GPS、4G、追従モジュール、IP等）は別々のセルに記述。25kg歩行時積載と100kg最大静止荷重を混同しない。メーカー条件下の参考値は達成保証としない。
- メーカー出典・区分別行数・2モデル差の正本を tests/fixtures/a2-factory/source-contract.json、生成入力を同階層 product.json に固定。scripts/product_factory.py は37行、4区分順、2モデルの欠損・重複をFail-Closedにする。
- 既存 tests/test_a2_factory_pilot.py と tests/a2-factory-preview.spec.js をGitHub ci.yml から必ず実行し、実HTMLの37行、4組、モデル別相談CTAの引継ぎ、PC1440／SP390／SP360を検査する。
- 今後の別メーカー・別型番でも同じ「一次出典の行数×モデル×カテゴリー＋モデル別CTA」の証拠契約を必須チェック項目とし、正本に確定した行数のない製品は全パラメータ掲載と称さずHOLD。既存製品を一括で作り直すことはしない。

## Live Maker Parameter Watch V1 (current implementation and limits)

- Every NEW Factory draft added under tests/fixtures/*/product.json must include maker-live-contract.json with source URL, a manufacturer-approved parser, model names, category/row IDs, all per-model raw official cells and approved displayed translations. The pre-existing X2 experimental fixture is grandfathered, explicitly NOT live maker verified.
- Existing GitHub ci.yml already calls product_factory.py audit; that SAME command now calls maker_spec_watch.monitor_all on every existing CI run, with no workflow YAML change. The watch re-fetches the official host only. No redirects, mirrors, private hosts, arbitrary URLs, unsupported table formats or unreviewed model/row changes are allowed.
- Supported extractors: unitree-a2-html-v1 (A2 official 37 rows x 2 models = 74 raw values) and html-table-v1 for a uniquely identified source table with a trusted group row class. Each new maker outside the exact host allowlist must be reviewed before activation. PDF, scripted and image-only tables are not silently inferred.
- A raw cell delta creates an auditable per-model difference and a FAIL/HOLD. The existing isolated --stage command produces candidate-product.json, candidate-source-contract.json and diff.json containing the latest untouched official raw text; performs bounded max-three data-consistency rounds; does NOT directly overwrite source Product Master, approve Japanese translation, merge, notify, release, or enable AutoFix.
- Current A2 original-source check: 37 rows and 74 values examined, no source raw changes as of 2026-11-15. Independent English-to-Japanese semantic review of each of the existing displayed translations has NOT been completed: TRANSLATION_REVIEW_PENDING remains a release HOLD even if --monitor can pass source drift detection.
- This automatically checks manufacturer drift when an existing CI workflow runs or someone explicitly runs the script. Continuous time-based polling and notification are NOT currently connected. A future existing approved orchestration may call the same read-only CLI; adding another Cron/Runner is prohibited.
- Gate order: approved maker-source contract and model-cell evidence -> existing intake -> existing DEV/CI source monitor -> independent technical/factual QA -> CEO one consolidated review. On a changed source, stage isolated candidate, revalidate at most three rounds, and hold for independent verification. Unknown field/configuration or uncertain translation must HOLD and cannot become an invented published fact.

### Maker Watch V1.1 — Continuous source monitoring within existing Factory

- An approved manufacturer must already be active in data/manufacturers.json. A new product has a frozen maker-live-contract.json identifying its manufacturer_id, exact HTTPS source, approved adapter, categories, models, raw source cells and independently reviewed displayed values. Unknown or unsafe sites and unsupported source layouts are HOLD.
- The existing CI product_factory.py audit invokes the same live maker monitor. python scripts/maker_spec_watch.py --monitor-all checks all onboarded maker source contracts against one live-source snapshot per manufacturer product. It detects model, row/category and per-cell changes, not only the 37-row A2 shape.
- On any real source drift, python scripts/maker_spec_watch.py --monitor-all --stage --output <new isolated directory> generates candidate-product.json, candidate-source-contract.json and diff.json with source-original cells. It rechecks internal consistency for up to three bounded rounds and fails closed with PENDING_INDEPENDENT_FACT_REVIEW. It never silently approves Japanese translations, writes Production Product Master, merges, or deploys.
- For new manufacturers, the approved html-table-v1 adapter requires a real unique table identifier and verified group structure. Unrecognized PDF/JS/image/spec layouts require an independently verified adapter BEFORE automated source checking can become active. Do not apply A2 37-row count to other product families.
- IMPORTANT: Source changes are checked when existing CI is invoked. Continuous timed polling and notification have not been connected yet; no new Cron, Runner, or second workflow is created. No claim that the translation of all 74 A2 maker cells has been independently signed off. Vendor-original raw cells and Japanese text must receive distinct evidence and review states before release.


### A2 74-cell technical bilingual verification evidence (2026-11-15)

- The original A2/A2-PRO English official HTML row titles and all model cells are captured by MakerWatch. A separate 37-parameter Japanese bilingual acceptance map in scripts/a2_semantic_fact_review.py independently checks the actual Japanese product.json model values, source row identities, per-model values, cross-model differences, and legacy combined display text; expected source HTML SHA256 is frozen.
- Any source hash change, unexpected official parameter title/number, differing Japanese value, or wrong count fails closed. Tests of hallucinated Wi-Fi version, unsupported inferred 3 joints per leg, incomplete motor/bearing details, and stronger speed maximum are part of existing tests/test_a2_factory_pilot.py and .github/workflows/ci.yml.
- Run a real official-source fetch and this semantic QA independently on AA8-N-015. Generate a 74-row evidence report for the exact technical SHA. This is technical evidence matching a manually curated bilingual reference, **not** proof of a distinct human reviewer or unconditional authorization to change review_status to INDEPENDENTLY_VERIFIED. The original status stays TRANSLATION_REVIEW_PENDING until the formal independent fact owner approves.
- Do not waive CEO exact-SHA review or manual-only production Pages; no new scheduler, agent, Runner or product Master edits.

### Protected Preview bundling — Footer Logo regression (2026-11-15)

A source repository preview may pass Chrome CI while a separate external Vercel
review deployment omits a referenced asset. The A2 preview footer logo actually
uses /assets/img/airadmin8-robotics-logo-footer.svg?v=20260805-3.
Deploying only the header PC/SP logos caused iPhone missing-image fallback.

Use scripts/verify_preview_bundle.py --html <exact-preview-html>
--manifest <vercel-file-list.json> before marking a review deployment READY.
The check fails closed if ANY locally referenced image, stylesheet, or script
is missing. It includes the exact shared official Footer SVG; never replace
it with text, a screenshot, unrelated header logo or a second Footer. Confirm
the remote Vercel file tree and the loaded image naturalWidth, PC1440/SP390/SP360,
and do not infer a successful authenticated CEO review from SSO readiness.
This does not modify the 74 signed-off technical Japanese spec cells.


### All-product preview bundle and post-deploy hash Gate (2026-11-15)

- The existing Factory + `.github/workflows/ci.yml` generates a Preview for **every registered draft product fixture**, automatically scanning `tests/fixtures/*/product.json`; it does not only handle A2/X2 by name. The CI source preflight **must** parse each rendered noindex Preview and recursively collect each local image, video poster, CSS, CSS @import/url(), SVG external dependency, icon, source/srcset and script. Missing local files are Fail-Closed before Playwright.
- `python scripts/verify_preview_bundle.py --site _site --revision <checked-out-code-sha> --emit <isolated-manifest.json>` produces one exact Vercel-ready per-file `files[{file,sha,size}]` list. The file list, not a hand-made fixed set of 19 assets, must be used for any new Preview deployment. Do not include `_site` itself or internal governance/CRM documents in the Preview.
- Vercel deployment is **not fully accepted** by `READY` or HTTP200 alone. After uploading, read the **real Vercel deployment source file tree** by ID, require `target=null` (not Production), exact source revision, and compare SHA1 of all required HTML and recursively collected assets. Use `--verify-deployed <Vercel-tree-json> --expected <manifest.json> --deployed-sha <exact-SHA> --deployed-state READY`; any missing/mismatched file = HOLD. Also require real SP360/390 and PC1440 Chrome load checks and authorized CEO SSO page review separately.
- The existing manual-only Pages release gate `scripts/verify_release.py` now applies the identical recursive **source asset existence** check to all public `products/*.html`. This caught and removed the obsolete, already missing `footer-mobile-cleanup.css` link from G1-D. Main and Pages remain unchanged until a separate exact-SHA CEO approval.
- The existing CI and independent AA8-N-015 QA can verify code, generated manifests, and negative drift behavior. The GitHub workflow itself cannot read authenticated Vercel Files without a connected Vercel action. Do **not** call the post-deploy Gate fully enforced until the authorized deployment path always calls the real file-tree readback before promoting Preview to `CEO_REVIEW_READY`. No new Runner, Cron, Factory, or automatic main/Production deployment is authorized.

### Native Vercel deploy-ready → existing GitHub CI readback bridge (2026-11-16)

- No new workflow/runner/scheduler. The existing ci.yml has a trusted-main
  `repository_dispatch` entry for the official
  `vercel.deployment.ready` event from the **existing Git-linked**
  `x2-edu-make-review` Vercel project (projectId
  `prj_vH6kcA1vFU6FPCm3skNdpudINkEh`). Product Factory PR CI attaches
  `aa8-preview-bundle-<exact-head-sha>` and never executes PR code alongside
  provider credentials in the post-deploy job.
- The post-deploy job reads the existing exact-SHA CI artifact, then executes
  `scripts/preview_postdeploy_bridge.py`. This requires a **separately
  configured GitHub Actions protected VERCEL_TOKEN secret** with read-only
  deployment and source-files scope, verifies team/project, deployment ID,
  Preview-only target, READY, the exact source Git SHA, and all linked
  per-product local asset SHAs from the real Vercel files tree.
- When all checks pass it emits only the exact-head GitHub status
  `aa8-preview-postdeploy=success`. Missing secret/trigger, missing CI
  artifact, SSO/URL without underlying source evidence, mismatched HEAD,
  stale CSS, missing image, wrong project or production target must HOLD.
  The status is a **technical artifact** only: neither real CEO SSO review
  nor production merge/deploy authorization.
- **Activation blockers to verify, not assume:** repository_dispatch routes
  only to a workflow present on the default branch; this change remains
  in original Draft #180 until explicit CEO approved main integration.
  The Vercel project is Git-linked but webhook administration returned 403,
  so actual `vercel.deployment.ready` delivery to the repo is unverified.
  No VERCEL_TOKEN secret presence/read permission has been proven.
  Do not claim an unattended E2E until a real new deployment triggers
  the trusted-main job and exact-source SHA check PASS.

### Vercel Git Auto Preview post-deploy compatibility (2026-11-16)

- Native Vercel Git deployments send vercel.deployment.ready events, but their /v6/deployments/{id}/files source-tree API can return 404. This is observed with real Vercel deployment dpl_EKRa1xGcRVajRfLLKE7LTTY1M3fH on project x2-edu-make-review. READY and matching Git SHA alone are insufficient.
- Reuse the existing trusted-main scripts/preview_postdeploy_bridge.py: attempt API-uploaded file-tree SHA verification first. For a Git source-tree 404 only, read ALL immutable deployment HTML and recursively linked local CSS/JS/SVG/media over the exact deployed .vercel.app host, and match every SHA1 to the original CI artifact.
- Protected Git runtime reads require VERCEL_TOKEN for authoritative Vercel project metadata and VERCEL_AUTOMATION_BYPASS_SECRET for actual SSO-protected response bytes, scoped only to trusted-main Actions. Missing secrets, redirects, bad SHA, partial file list or missing Preview = HOLD. Never disable SSO or print tokens.
- A Git deployment which does not actually publish CI-generated Preview HTML must fail closed. Do not pretend the source Git repository or Vercel READY response proves actual delivered bytes. CEO authenticated review and manual-only Pages Production remain separate.
- This feature is code-only until approved exact-SHA main integration and repository secrets are present. No separate Runner, Workflow, webhook or Cron.

### One-time A2 native Git Preview E2E acceptance evidence (2026-11-16)

- Existing original Draft PR #180 only; after trusted-main PR #195 activation,
  this documentation-only nonempty commit initiates exactly one native Git
  Preview and the corresponding same-HEAD pull_request CI. No new Factory,
  workflow, runner, manufacturer facts, or Production product is introduced.
- Acceptance is explicitly **PENDING** until GitHub PR CI SUCCESS contains
  the new HEAD's exact manifest, Vercel reports source=git and target=Preview,
  and trusted-main readback proves every required deployed HTML/CSS/Logo/image
  byte digest. The older HEAD's manifest cannot be reused.
- If the CI run is absent, fails, or the deployed byte hashes do not match,
  aa8-preview-postdeploy must remain FAILURE/HOLD. No automatic retries,
  PR merge, GitHub Pages Production release, or CRM/ERP changes.

### Preview deploy event activation scope

The existing GitHub CI's main-branch listener verifies external Vercel events
using scripts/preview_postdeploy_bridge.py and the approved source manifest
from the exact PR HEAD CI run. It does not create a second Factory or deploy
an unapproved product. For Git-origin Vercel deployments, the source-file-list
API can return 404 and is replaced by actual authenticated runtime SHA1
verification of all registered generated Preview HTML and their linked assets.
Do not promote a candidate with unauthenticated HTML or missing runtime files.
The first active event remains a separate live E2E acceptance condition.

## Product PR factory: single SKU versus shared impact (2026-11-17)

- Draft fixture is a safe candidate input, not a second public Product Master.
  All official 13 products continue to be read from data/products.json;
  adding a new SKU requires an independently authorized product record
  and separate controlled publishing.
- Any change to scripts/product_factory.py, its template, shared header/
  footer/menu, relevant shared CSS/JS, or CI changes the **Factory contract**
  even when PR's only new fixture is A2. Thus assign GLOBAL_FACTORY scope
  and require cross-product regression, then separate candidate QA.
- Cross-SKU facts/metadata/CTA/data rendering must not be modified to
  solve one draft's CSS or copy complaint. Use explicit product-scoped
  presentation where necessary; preserve existing JSON source references,
  maker facts and approved public product output.
- Factory stages: G0 evidence + real manufacturer snapshot; G1 business
  customer value + 4-family module map; G2 source/preview generation and
  noindex/CTA checks; G3 cross-product and device QA with before/after
  screenshot evidence; G4 independent visual and human semantic facts;
  G5 exact-SHA CEO release/rollback. No stage can borrow a PASS from another.
- A real Bug recurrence means the generator's source/template or
  QA requirement is wrong; adding CSS on top of another override is not a
  root-cause fix. Once all mandatory gates pass, close within the
  80-point optional design standard and stop speculative polish.
