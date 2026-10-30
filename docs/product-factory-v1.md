# AirAdmin8 Robotics | Product Page Factory V1 (2026-10-31)

## 1. Existing single sources of truth
- Product facts / product catalog: data/products.json schemaVersion 5. Do not create another Product Master.
- Visual baseline: CEO-approved G1 HTML and assets/css/g1-product.css; new opt-in pages use scoped assets/css/g1-factory-v1.css.
- Shared header/footer: existing includes/ only. Never duplicate a new header system.
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
  Validates all 11 catalog products and frozen approved contracts. Reports old placeholder images without pretending they are official media.
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
- pageFactory.videos >= 1, each with src, poster, label, sourceUrl; browser decoding tested separately
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
