# Unitree G1+ product page — Fact & media evidence
Date: 2026-10-30 JST / Status: Draft, pending manufacturer commercial asset permission and CEO production approval.

## Sources and version separation
- Manufacturer product specifications, images, feature comparison: https://www.unitree.com/G1plus/
- Internal G1+ standard source: https://docs.google.com/document/d/1nMqvPrTHnZRQlI_Rtt2muwWHbDjcbQd6FkB8kyL35KI/edit
- Internal G1+ EDU source: https://docs.google.com/document/d/18Vsp4U1EVaYcwrIs9pM1Fmd90lEjSCR7Q8Z1Pl29uTQ/edit
- Original G1 reference (different product!): https://robotics.air-admin8.co.jp/products/unitree-g1.html

## SKU-safe fact table
| Field | G1+ standard | G1+ EDU | Publication rule |
|---|---|---|---|
| Whole-body DOF | 25 | 25–45, per SKU | Separate variants |
| Secondary development | Not supported | Supported within specific SDK/API | Never claim on Standard |
| Arm load | Approximately 3kg | Up to approx. 4kg, configuration and pose dependent | State conditions |
| Head | 2 DOF | 2 DOF | Manufacturer value |
| Weight | Approx. 35kg | 35kg+, configuration-dependent | Avoid single SKU assertion |
| Basic compute | 8-core CPU | 8-core CPU plus optional compute | Never imply Orin included |
| Supplier/manufacturer warranty | Manufacturer web 8/18 months | Manufacturer web 18 months | NOT a Japanese AirAdmin8 guarantee |
| Japanese price/lead time | Not finalized | Not finalized | Inquiry only |

## Original manufacturer image provenance
Local files are original bytes downloaded on 2026-10-30 from the following manufacturer page. Images must not be presented as proof of delivery performance.
- Main hero and catalog: `assets/img/products/unitree/catalog/29_g1pl.png` — approved existing internal catalog asset; see `data/unitree-product-image-sources.json`; do not substitute G1 original.
- `assets/img/products/unitree/g1plus/g1plus-engineering-original.png`: https://www.unitree.com/images/1c07b00b22eb40448af5736919891c77_1454x1902.png
- `assets/img/products/unitree/g1plus/g1plus-hero-original.png`: https://www.unitree.com/images/0e5960107c1648a490cf11f869941269_2000x1346.png (official annotation is in Chinese; no modification)
- `assets/img/products/unitree/g1plus/g1plus-vision.png`: https://www.unitree.com/images/6feac9066863484b9f238b86d16d0fb5_3202x2146.png
- `assets/img/products/unitree/g1plus/g1plus-touch.png`: https://www.unitree.com/images/a7ee597e374e48d5a7c94ccbc3196ccf_1758x2160.png

## Publishing safety gates
- The site owner has asked to use manufacturer promotional assets on product pages, retain source credit. That decision does not constitute independently verified legal authorization.
- Internal catalogue notes commercial usage authorization for some high-res media remains unverified. Record status; CEO accepts disclosed exception before release per existing rules.
- No foreign currency price, distributor quote, fictional stock, delivery timeline, testimonial, certification or ratings is published.
- `products/unitree-g1-plus.html` is a candidate, not a production webpage. Draft PR + real noindex Preview + independent PC/SP QA required; no main merge or production deployment without separate CEO approval.
