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
