# AirAdmin8 Robotics｜Corporate Brand V1 CANDIDATE

**State:** INTERNAL_PREVIEW_ONLY / NOT_APPROVED / PRODUCTION_HOLD.
**Owner:** existing PR #180 and existing QA Policy/CI. No new PR, Runner, Factory, scheduler, deployment or CRM write.

## Verified primary-source visual baseline
- Official parent website: https://www.air-admin8.co.jp/
- Theme CSS (inspected on 2026-11-18): https://www.air-admin8.co.jp/aa82022/wp-content/themes/AirAdmin8/style.css
- Brand palette: deep #0069B5; primary #009BD2; teal #00B2BC; ink #333333; light-footer #F4F8FA.
- Font: Noto Sans JP with Japanese fallbacks; corporate base body CSS PC16px/SP15px; letter spacing .05em.
- Header: corporate logo, white surface, restrained shadow.
- Corporate structure: whitespace hierarchy, simple product photography, square/low-radius CTA, light-footnote.
- Footer: light-gray background and white business-information container.
- Original main-site ISMS display is NOT to be copied as a current certification claim.

## CSS ownership mapping after design approval
1. Shared Header/Footer/Menu and corporate colors -> existing `assets/css/shared-layout.css` (single Shell owner).
2. General typography, buttons, spacing, card and background rules -> existing `assets/css/main-site-experience.css` (page expression owner).
3. Factory/product-specific layout only -> existing factory CSS; no global brand overrides.
4. Legacy X2 inline styles are historical; avoid new per-page patches. Remove only with 13-product regression evidence.

## Stage / constraints
- Internal prototype CSS: `ops/brand-preview/corporate-brand-v1.css`, scoped to `[data-aa8-brand-preview="corporate-v1"]`.
- This candidate has **not** been linked into published product pages and does not signify full corporate style rollout.
- After CEO design-direction review, activate in original PR with explicit PC1440/SP390/SP360 browser comparison and independent QA; block new unowned colors, fonts and shared component overrides.
- Manufacturer facts, Japanese legal claims, CTA/CRM business E2E, CEO precise-SHA merge and manual-only GitHub Pages release remain separate HOLD gates.
