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
