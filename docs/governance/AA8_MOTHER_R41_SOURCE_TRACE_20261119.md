# AA8 Corporate R4.1｜WordPress source-of-truth trace (2026-11-19)

**Status:** SOURCE_AUDITED / CORPORATE_COMPONENTS_STAGED / FIGMA_NATIVE_BLOCKED / PRODUCTION_NO_GO.

## Grounded parent-source location
- Original owner-maintained shared Google Drive:
  https://drive.google.com/drive/folders/1Dp53JswAH-7i_GS8qvNG9aYZoB3XVIlZ
- New read-only extraction under same R4.1:
  https://drive.google.com/drive/folders/1iOJ-6J-_lXWhLFcL_haRvQZEAcn2gXds
- Audit files: DEEP_REPORT.md, AUDIT.md, contracts/theme-source-contract.json, css/*.css, source/menu-version-diff.patch, original WordPress Header/Footer fragments; original source files are NOT mutated.
- Snapshot ZIP in sibling R4.1 folder: _Corporate_Theme_Extract_20261119.zip; SHA256 `86D4DB390A238E11DDB33591829E3D29A5D59DDB34B748906982DAACC36C41B4` (13 files, no font binaries).

## Verified original / online file identities
| Source path | SHA256 | Observed status |
| --- | --- | --- |
| style.css (and style.min.css) | `C2D5AAA83CC779B9EBCDE05B8C412A1D4029B89A390C43D866D6CFEE51D3064F` | Exactly equal to live November website CSS |
| assets/js/common.js | `7ABC81479A103C4AD191C0D96FD61ADCE2BE46C8DFEA7C5BD9E252E296C1E44E` | Drive snapshot, 6,940 bytes |
| LIVE assets/js/common.js | `BA8109F36EB6B1DA50AB7FAF47C45C0484BA187EB99C9CC14860F6D09C6FFD54` | 8,212 bytes. Main difference is appended Company profile popup code, not a wholesale rewrite of hamburger behavior |
| assets/scss/_header.scss | `F6D6225BA46DFDEEE225252EC00EAD88AAA63C91ECCE40F2607137357BCF01D9` | Historical Sass partial |
| assets/scss/_footer.scss | `91E38C434919F8A8744CDA0AC9B7F912B3B0A5D176F402960990B98AD3C0C7BD` | Missing compiled Footer Renewal code |

**Stop condition:** Theme `Gulpfile.js` uses `gulp-sass ^4.1.0` and declares `outputStyle:'compressed'`, while the published 11k-line `style.css` contains an appended Footer Renewal block starting near line 11485. Sass source parity is NOT established. **Never rebuild and overwrite canonical CSS from those partials until regenerated output has been compared and independently QA'd.** `style.min.css` is identical, not independently minimized.

## Accurate source-to-component implementation map
| Brand role | Original location/selector | Robotics single code owner |
| --- | --- | --- |
| Typography / body | `assets/scss/_variable.scss`, `_typography.scss`, `style.css:.body` near line124 | `assets/css/main-site-experience.css` after opt-in approval |
| PC/SP Header | `header.php:104-188`, `style.css:.header` | `includes/site-header.html` + `assets/css/shared-layout.css` |
| Header logo | `header.php:110-115` / original official PNG | existing approved logo asset; no faux copy |
| PC menu | `header.php:117-167`, `.header-nav__link` | shared Header include and CSS |
| Mobile menu | `header.php:179-185`, `style.css:.header-nav_open, .header-hum-btn`, original `common.js` | `assets/js/mobile-qa.js` is build-time event owner; `site.js` fallback only |
| Header Contact CTA | `style.css:.header-contact__link` near line1199; 130x40, radius21 gradient | Header variant (NOT all buttons) |
| Content CTA | `style.css:.common-btn__link` near line900; black 320x76 PC, 52 SP | Content button variant, not Header pill |
| Footer | `footer.php:277+`, `style.css:11485+` | `includes/site-footer.html` + `assets/css/shared-layout.css` |
| Footer visual | `#F4F8FA`, white panel max1280 radius18, 4-nav columns | Corporate CSS tokens scoped to `body.aa8-corporate-v1` |
| Product facts | Manufacturer evidence, **not WordPress page copy** | existing `data/products.json` / Factory |

## Four release-critical findings
1. **SOURCE_BUILD_HOLD:** Footer Renewal is compiled-only; do not overwrite from the stale SCSS. Need a source-to-built parity proof first.
2. **BRAND_RUNTIME_HOLD:** WordPress JS references jQuery, clone-on-scroll Header and popup plugins; adapt UI semantics in existing Robotics runtime, never transplant scripts wholesale.
3. **LEGAL_FACT_HOLD:** WordPress Footer has ISMS/ISO27001 claim and fixed office address; source presence is not authorization to republish these facts. Check current status and correct the mother site separately when appropriate.
4. **PERFORMANCE/ACCESSIBILITY:** `header.php:21` changes stylesheet cache-buster every minute; HTML disables zoom (`user-scalable=no`). Do not clone either pattern into Robotics.

## Management rules
- Website visual authority = verified live parent `style.css` and recorded source SHA, NOT guesswork or prompt-generated gradients.
- Figma remains the editable design representation after API quota access is restored; `ops/brand-preview/figma-corporate-tokens-v1.json` is the versioned token candidate. **No claim that native Figma components have been created yet.**
- Single code owner remains as above; no parallel component system, new PR, runner, scheduler, Factory or Production edits.
- New/reworked pages must reuse existing Header/Footer/CTA semantics, keep factory facts intact, and pass 13 product PC1440/SP390/SP360 plus 1023/1024 breakpoint navigation tests on exact HEAD.
- Until Figma native sync, independent full visual QA, manufacturer fact gates and CEO exact-SHA approval: **NO-GO**.
