# Unitree H2 Plus | G1 template / product delivery / QA (2026-10-31)

## Product source of truth
- Official manufacturer: https://www.unitree.com/H2plus
- Source folder on G Drive: Unitree / 素材 / ヒューマノイドRobot / ヒューマノイドロボットー3種５品 / H2plus_assets
- Original SingleFile H2plus.html is in the parent folder, not inside H2plus_assets.
- Unitree H2 Plus, H2 and H2-X are different products and must never exchange specifications.
- Single Master: data/products.json, entry id=unitree-h2-plus.
- Product page is generated from scripts/product_factory.py + G1 approved fixed template.

## G1 design contract
- Hero and every non-CTA section calculated background rgb(255,255,255).
- Hero source: assets/img/products/unitree/h2plus/drive/h2plus.png (source SHA verified against G Drive).
- Main sections: key strengths, applications, 9 official media images, official specs, FAQ, four related products.
- CTA: same G1 illustrated image cards / g1-cta-figma-pc.png geometric visual; cards 1 official manufacturer page, 2 specifications, 3 consultation with product prefill.
- Related: Unitree H2 / H2-X / G1+ / G1.
- Manufacturer material does NOT supply a verifiable MP4, so do not fabricate a demo video or use video from another SKU.
- Header/Footer keep the existing includes SSOT.

## Manufacturer-grounded facts
- 31 basic body-joint motors and 75 combined with optional dexterous hands must not be conflated.
- Jetson Thor T5000 2,070 TFLOPS is manufacturer theoretical FP4 sparse compute, not real-world task performance guaranteed.
- Arm load 7kg rated / approximately 15kg peak depends on use and posture.
- Japanese sale terms, price, stock, warranty/SI coverage and SDK availability remain to be confirmed.

## Test scenario groups
1. Master schema and evidence field, SHA/media copying.
2. Real browser PC1440/SP390/SP360: hero, pure white sections, three CTA images loaded, nine media images, four related cards, no horizontal overflow.
3. Contact link real prefill and URL exact product, with NO customer sending.
4. Catalogue (11 visible compare cards, legacy LimX exclusion), OG/canonical/schema source.
5. PR CI plus independent AA8-N-015 browser QA and exact HEAD SHA.
6. Production: separate strict CEO approval, main/CI/QA/pages/no concurrency, single manual dispatch, failure immediate STOP, then public SHA/browser acceptance.

## Scope/permissions
- No edit of existing G1/H2/H2-X product HTML or approved CSS.
- No new automation, Master, runner, or external email/CRM write.
- Code merge and production deploy require existing CEO SHA approval gates.

## V3.0 strict review / additive modules (2026-11-03)
- H2 Plus only: model selection, SDK/developer resources, research solution examples, procurement/implementation steps.
- V3 factory code must be product-agnostic: model heading, manufacturer source and Hero CTA generated from Product Master, never hard-coded to Unitree or H2 Plus.
- The first Hero CTA is consultation; official image gallery remains accessible by secondary CTA.
- Resource link points to existing /resources.html and verified manufacturer source; do NOT claim a downloadable H2 Plus SDK or guaranteed ROS 2 compatibility.
- Five-step process uses scoped V3 layout; retain original white background, 9 official images, three G1 illustrated CTA cards and four related products.
- Product/Maker must prefill existing contact form; full Inquiry ID, persistent receipt and CRM routing are separate end-to-end projects and are NOT claimed as passed here.
- CI must assert candidate generated from data/products.json equals committed H2 Plus HTML. Independent AA8-N-015 PC1440/SP390/SP360 must still inspect screenshots and actual interaction.
- The exact PR HEAD, CI and independent QA must be reverified before a separate CEO merge/deploy approval.

- V3 long anchor navigation on 390/360px must scroll horizontally without colliding labels; test neighboring DOM bounding boxes and source CSS. Header is validated against built `_site` artifact, not just source placeholders.

- Strict design fix: the V3 header anchor navigation is reduced to 9 key sections. Desktop width 1440 must fit without horizontal scrolling; SP390/SP360 must scroll horizontally with non-overlapping labels. FAQ and related modules stay on the page.

## CEO screenshot redline / 2026-11-03
- H2 Plus V3 only: remove visible Hero repeated status line and tiny manufacturer caption; original manufacturer source retained at specification disclosure and illustrated CTA.
- Four feature cards and four application cards: 4 in one row on >=1120px, 2 columns on intermediate tablet, one column on SP. No 3+1 orphan layout.
- Keep all nine verified manufacturer images; equal 16:10 containment frame with caption alignment, never crop or substitute another SKU.
- Rename heading to 製品スペック and group source/date in expandable detail; machine-readable/SSOT per-fact source links remain in generation data.
- Suppress long zero-video fine print and duplicate final CTA kicker/lead/fine text on V3 only; preserve factual notes in Product Master and manufacturer source.
- Do not touch approved legacy pages, shared G1 CSS, QA Factory, contact/CRM or manual-only deployment.
