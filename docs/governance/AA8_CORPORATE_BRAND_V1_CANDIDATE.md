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

## Verified original mother-site extraction (2026-11-18)
The original homepage HTML, WordPress theme CSS, menu runtime JS, and header/footer official logo assets were each read directly and fingerprinted. SSOT of observed facts: `ops/brand-preview/mother-site-contract-v1.json` (source URLs and SHA256).
- Original corporate menu labels: HOME / 製品一覧 / 導入事例 / 会社情報 / サポート / コラム / 採用情報 / お問い合わせ.
- At <=1023px WordPress uses a full-screen blue/teal gradient navigation, three blue hamburger bars that become white on open, and scroll lock. The original JS relies on jQuery; Robotics should reuse existing menu runtime via the existing shared shell owner, not copy jQuery.
- The original Footer has 4 information groups (サービス / 導入・事例 / サポート・セキュリティ / 会社情報), light-gray #F4F8FA background and a white 1280px / radius18 panel. Do not transplant unverified ISMS or outdated address statements.
- Original CSS has two distinct CTAs: header contact is a 130x40px gradient pill; general `common-btn__link` is a black rectangular 320x76px action (52px SP). Choose semantic components intentionally rather than enforcing one global CTA shape.
- Separate original WordPress styling from Robotics semantic navigation labels; the target must preserve Robotics product discovery + consultation and use the same corporate visual system.
- An independently generated offline component extraction and PC1440/PC1024/SP1023/SP390/SP360 preview is available as review artifact outside published product paths. It does not amend the existing `site-header`/`site-footer` until approval and full regression.

**Gate boundary:** corporate extraction/preview is source-grounded, not approval of 13 live pages; legacy CSS collisions and active certifications remain distinct HOLDs.

## Figma native component handoff and code freeze (2026-11-18)

**Existing target:** https://www.figma.com/design/uo56l51NgUqit4976LV6P2
**Actual Figma write status:** BLOCKED_STARTER_API_QUOTA. The connected Figma API explicitly refused the write. No native Figma nodes, variables, component keys or sign-off can be claimed. SVG preview and importable token JSON are staged; they are NOT native reusable Figma components yet.

### Unique design-token code contract
- SSOT primary-source capture: `ops/brand-preview/mother-site-contract-v1.json`.
- Figma-ready variables: `ops/brand-preview/figma-corporate-tokens-v1.json`.
- Code implementation: **existing owner** `assets/css/shared-layout.css` (AA8_CORPORATE_BRAND_V1_OPT_IN), **existing runtime** `assets/js/site.js`, **existing HTML include** `includes/site-header.html`.
- Owner of public product facts remains `data/products.json`; no Figma layer may alter a numeric manufacturer fact.
- Key colors: #0069B5 / #009BD2 / #00B2BC, body text #333333, Footer #F4F8FA; Noto Sans JP 16px PC / 15px SP; body tracking .05em.
- Corporate shell must be *opt-in* via `body.aa8-corporate-v1`; public 13 products and Production remain unchanged until authorized rollout.

### Target Figma reusable components (native nodes PENDING)
| Target component | Required properties/variants | Code owner |
| --- | --- | --- |
| AA8/Corporate/Header | Desktop / Mobile, logo using approved official asset | includes/site-header.html + shared-layout.css |
| AA8/Corporate/MobileMenu | Open / Closed; 1023px; full-screen gradient; keyboard access | assets/js/site.js + shared-layout.css |
| AA8/Corporate/Footer | Desktop / Mobile, four grouped semantic nav sections, legal facts verified | includes/site-footer.html + shared-layout.css |
| AA8/Corporate/CTA | Main Header 130×40 radius21 / rectangular content CTA | shared design tokens, page action CSS |
| AA8/Corporate/Typography | Desktop / Mobile text hierarchy, token-bound | existing main-site-experience.css after approval |

### Mandatory release contract
1. Figma token/variant IDs and independently reviewed native component screenshots; design **NOT_APPROVED** until actually written and read back.
2. Same token values in CSS and Figma; existing Python contract gate must PASS.
3. PC1440/SP390/SP360, plus mother mobile breakpoint 1023/1024, actual Chrome menu/CTA/keyboard/scroll checks must PASS.
4. Explicit product catalogue 13/13 visual and functionality regression when opt-in is applied to actual pages.
5. Safety: no ISMS-certification or address text is imported from mother site without current verification. All manufacturer facts and CRM E2E are separate release HOLDs.
6. CEO one-shot exact-SHA approval required before main merge and manual-only Pages deployment.

Stop when required quality passes; do not invent a second Factory, a separate HTML renderer, extra PRs, or a new persistent runner.
