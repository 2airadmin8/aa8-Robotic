# AirAdmin8 Robotics｜Product Visual Standard V3.3（DRAFT / NOT RELEASE APPROVED）
**基準日:** 2026-11-21 JST (latest pinned evidence, no production change)
**現行Design Snapshot:** FIGMA_NATIVE_14_COMPONENTS_38_VARIABLES_PINNED / NEW6_REFERENCE_ONLY / SPACING_DETAIL_READBACK_HOLD / CEO_RELEASE_HOLD / PRODUCTION_NO_GO.


## CURRENT SNAPSHOT | 2026-11-21 design-to-code baseline (historical checkpoints below)

- **Source:** https://drive.google.com/file/d/1SMjAR3RL1gQRhbAWefENBi6QXypLw4xX/view
- **Source SHA256:** 3133543f919e9f4c1a87af8f0cb7e1950a8a86418cd9bbb9cfcfe3d50e02cf09 (normalized UTF-8).
- **Native components:** 14 = previous eight Header/Footer/Specs/Menu/Tokens plus six design samples (Buttons, Cards, Forms, Sections, Spacing, QA). These six are REFERENCE_ONLY; they do not prove finished Variants, interactions, nested instances or token binding.
- **Variables:** 38 = eight V3.2 legacy + twenty V3.3 base + ten V3.3 spacing variables. Spacing values are 4, 8, 12, 16, 24, 32, 40, 48, 64, 80 px. Native numeric values were read in the editor on 2026-11-22; component-level variable bindings remain HOLD.
- **HTML management:** 20 categories = six implemented, one spacing-detail HOLD, twelve partial/reference-only, one not shared. A green static check is NOT release approval.
- **Whitespace:** 160px PC / 120px SP empty zones trigger WARN and visual review, NOT automatic CSS rewrites. Keep approved Hero geometry.
- **Machine sources:** docs/governance/hp-design-code-trace-v1.json; ops/brand-preview/corporate-product-visual-v33.json; ops/brand-preview/figma-product-v33-tokens.json. Existing governance CI checks agreement; existing Python Product Factory checks this pinned design snapshot for strict V3.3 SKU.
- **Limitations:** Live Figma MCP read is unavailable under the current Starter limit. The review is pinned to the cited design document, not a live Figma API poll. New Figma edits require evidence update and exact-SHA CI rerun. New six components and Spacing detail cannot be asserted fully approved; CEO release, business E2E and Japanese manufacturer fact gates stay HOLD.

**Historical note:** Older lines dated 2026-11-19/20 containing 8 components / 20 variables are records of previous states and DO NOT supersede this current pinned snapshot.

### 2026-11-22 C07-C10 native editor five-layer follow-up (no fictitious signoff)
| ID | Actual Figma editor readback | Code and Chrome | Mandatory remaining design evidence |
|---|---|---|---|
| C07 | Existing collection AA8 Robotics V3.2 / Core Colors, v33/spacing 10 native Number values 4/8/12/16/24/32/40/48/64/80 | Existing site.css mappings, three-viewport computed CSS verified | Prove actual Frame padding/gap Variable Binding, not just native number list. HOLD |
| C08 | Selected node 217:73, 1120x800 Buttons and CTA States, three design columns Primary/Secondary/Text Link and visible demo Default/Hover/Focus/Disabled/Loading rows. No trustworthy named Variant property matrix or token-binding manifest was established from the selected top-level Properties panel. | Existing .button code, contrast/focus/navigation QA | Bind active Corporate deep-blue token to real Primary Variant and verify code-design visual comparison; default visual sample remains bright-blue vs approved accessible code. HOLD |
| C09 | Reuses same native 217:73 visual state examples; layer tree reveals individual Text/Vector samples, not proven keyed Button state component properties. | Real confirm button uses existing JS busy/disabled/retry and strict Chrome QA | Prove usable formal State Variants/Props, Loading/Focus relationships and Variable Binding to original CSS/JS. HOLD |
| C10 | Selected native 217:127, 1120x830 Cards and Content reference containing Product/Related/Resource visual examples; 16:9 MEDIA SLOT labelled; selected top-level Properties pane has no verified named prop bindings | Existing C10 card renderer and image fallback, 16:9 desktop CSS and PC/SP QA | Bind actual component fields/tokens, demonstrate a real main component/instance and independent Figma readback. HOLD |

Figma Starter MCP metadata calls were explicitly rate-limited; normal logged-in Figma editor could still inspect these existing nodes. This does not establish continuous machine change detection. Minimal unblock on the **same original Figma file**: for C07 apply native Number variables to real gap/padding properties; for C08/C09 formalize their state variants and apply existing deep/surface tokens; for C10 connect native card fields to their source/variant properties and token bindings. Capture node and Variable IDs, then version-update the **existing** Design Contract and run exact-SHA CI. Do not create a parallel design source or workflow.

### 2026-11-22 C10 actual product card QA (code/Chrome PASS, Figma Binding HOLD)
- Original Figma native reference 217:127 Cards and Content remains an editable reference sample, NOT proven full production variant/property/variable-bound component. Figma Starter tool metadata was rate-limited. Selected parent Properties panel did not establish named Variant/Component Property bindings, so C10 DESIGN_HOLD.
- Product truth stays data/products.json. Existing assets/js/site.js renders the product card from the same Master. Existing assets/js/product-cards-v2.js enriches it, now binding image error only once and adding an honest accessible text fallback when a maker image fails. Original image source, product model, title, status and links remain intact.
- Additional Figma native UI readback: node 217:127 is a 1120x830 editable reference component-set-like sample showing three columns Product Card, Related Product, Resource/SDK. Its media slots explicitly say 16:9; PC product-cards-v2.css was 16:10. Red exact computed aspect ratio 16/10 versus Figma 16/9, corrected to 16/9 in existing CSS and guarded against reverting. Its top-level Properties panel does not show documented Variant/Component Property links, and child layers include TEXT/VECTOR examples, not independently verified named formal Variants. This is evidence of the sample structure, NOT proof of all component bindings.
- Actual RED at PC1440/SP390/SP360: no focus-within card outline and no missing-image fallback. Fix in existing assets/css/product-cards-v2.css: Corporate deep blue visible outline and card action link color, neutral fallback area with hidden broken img. Existing JS enhancer inserts the fallback without manufacturing an unapproved image or new product fact.
- Additional real RED: the existing catalog detail link #008fbd on white had computed contrast 3.708:1, below WCAG AA for regular text; original small grey meta-prefix also needed stronger color. Change both only in existing C10 CSS Owner to Corporate deep-blue #0069B5 and #37515d, with new per-card real Chrome contrast checks; no font/content change.
- Existing tests/product-list-visual.spec.js tests manufacturer/model/title/status/source/link, hover transition, keyboard focus and Enter navigation, and intercepts one real image URL to prove fallback on PC1440/SP390/SP360. No production customer submission. Governance tests now reject falsely approved Figma variants, code-owner mismatch, loss of focus, loss of fallback and Product SSOT substitution.
- C07/C08/C09 component-level Figma bindings, Figma live change detection, exact-SHA independent QA and automated two-READY-task Runner E2E remain separate HOLD gates. No main merge, Pages deployment or CRM/ERP writes.


### 2026-11-22 C09 button states (isolation only / Figma Variant HOLD)
- **Existing UI ownership:** The confirmation button `dialog[data-contact-confirm] button[data-confirm-send]` uses the existing `assets/js/contact-v2.js::setSendingState` for real in-flight disable, `aria-busy`, loading text and failure restoration; no second event handler/Factory was added.
- **Actual RED:** In real Chrome PC1440/SP390/SP360, confirmation button white text against old `#009ad2` was only **3.2047:1**, below the normal-text 4.5:1 accessibility baseline.
- **Minimal CSS correction:** Existing `assets/css/contact-v2.css` now uses approved Corporate deep blue `#0069b5` for normal and hover, adds explicit `:focus-visible` and `:active`, retains disabled and loading visual states. Contact form routing, endpoint, submission token and origin checks remain unchanged.
- **Applicable single-component QA:** Original `tests/contact-inquiry.spec.js` C09 test covers keyboard Tab/focus visible, hover, contrast, 44px touch target, actual JS in-flight disable/busy/loading, blocked duplicate click and negative-ack recovery at 1440/390/360. It intercepts all Apps Script requests in the browser and replies negative only; this is **not** a real inquiry/CRM E2E nor evidence of sent mail.
- **Design limitation:** Reference Figma Node `217:73` is a sample; Button States Variants/Properties/Token Binding have NOT been natively validated. C09 remains `REFERENCE_ONLY`, no 20/20 claim until all layers and separate device SHA attestation.


### 2026-11-22 C08 CTA AA contrast correction (SOURCE/CSS/HTML QA, Figma Variant HOLD)
- **Scope and Figma reference:** Existing `AA8 V3.3 / P1 / Buttons and CTA States` reference Node `217:73` (still sample-only; no verified Figma Variant/Component Property Binding). No redesign of product-specific `.g1-button` or shared Header `.nav-cta`.
- **Real RED:** Main-site shared `.button.primary` was white text on brand-primary `#009BD2`, computed text/background contrast **3.17:1** at PC1440, SP390, SP360; ordinary 4.5:1 accessibility threshold FAIL. This is a production-like isolated HTML screenshot/browser finding, not a claim about customer feedback.
- **Minimal source fix:** Existing `assets/css/site.css` uses approved Corporate `color.brand.deep=#0069B5` for primary CTA with white text; keeps 48px min-height, native link navigation, responsive width and existing form prefill. Adds explicit keyboard `:focus-visible` outline, secondary hover and native disabled-button styling. No new JS or second component factory.
- **Real QA:** `tests/hub-pages-visual.spec.js` C08 verifies contrast ≥4.5, primary/secondary visibility, 44px touch height, focus ring and genuine local navigation at 1440/390/360. All Figma Properties/Variants and exact SHA independent QA remain separate gates; C08 manifest is explicitly `REFERENCE_ONLY` until Native Figma linkage is actually proven.


### 2026-11-22 C07 native variable readback and CSS bridge (PARTIAL / HOLD)
- **Actual Figma UI readback:** Existing file `uo56l51NgUqit4976LV6P2`, original native variable collection `AA8 Robotics V3.2 / Core Colors` = 38 variables; filtered group `v33/spacing` displays ten native number variables and values: `4, 8, 12, 16, 24, 32, 40, 48, 64, 80`. This is a human-operated editor readback, not the Figma API, source-change polling, or independent device attestation. Reference component `217:288` is a design sample, not binding proof.
- **Actual code bridge:** Existing `assets/css/site.css` defines `--aa8-v33-spacing-{4,8,12,16,24,32,40,48,64,80}` with the identical pixel values; existing `.actions`, `.meta`, `.section-heading` now consume 12/8/24 respectively without changing their numerical values. The existing strict-design validator checks all ten CSS definitions against the one pinned token JSON, verifies real usage, and fails closed on CSS drift or missing usage; original regression tests contain negative cases.
- **Actual browser result:** PC1440/SP390 custom properties ten-of-ten match computed values, with no horizontal overflow. Homepage PC hero `.actions` gap resolves to 12px; SP390 retains an **existing approved page-specific override** of 10px, not a token-pinning failure. The 13 public products must retain their exact existing PC1440/SP390/SP360 QA; this does not authorize a shared-layout redesign.
- **Unverified = HOLD:** Figma per-component **Variable Binding / applied padding and gap property chips**, true live remote-change-trigger detection, and independent Figma binding readback remain unverified. Native variable existence plus contract/CSS match **does not** make C07 5-layer PASS. Keep existing status HOLD; do not upgrade manifest to IMPLEMENTED or claim 20/20.



## 唯一产品与设计边界
- 母站真实视觉正本：`https://www.air-admin8.co.jp/`；G盘正式 WordPress `themes/AirAdmin8/style.css`；记录 SHA256 和源码清单：`docs/governance/AA8_MOTHER_R41_SOURCE_TRACE_20261119.md`。
- 设计版本：**V3.3视觉层**，仅升级美术风格；产品内容版本继续 **V3.1**，`data/products.json` 的13个公开商品、厂家参数、图片/模型、既有客户决策路径、CTA预填、SDK资料不迁移。
- 约束来源：品牌蓝 `#009BD2` / 深蓝 `#0069B5` / 青色 `#00B2BC`、正文 `#333333`、Footer底 `#F4F8FA`、日文 `Noto Sans JP`、拉丁 `Poppins` 均从母站源码提取；**规格表白灰**是CEO本轮明确指定，不能伪称母站原样规格组件。
- SSOT：`ops/brand-preview/mother-site-contract-v1.json`（母站事实）＋`ops/brand-preview/corporate-product-visual-v33.json`（V3.3视觉合同）＋`ops/brand-preview/figma-product-v33-tokens.json`（待导入Figma）。
- Figma目标：<https://www.figma.com/design/uo56l51NgUqit4976LV6P2>。2026-11-19 MCP确认目前仍为Starter/View且调用额度拒绝；**没有创建/更新任何原生Figma组件，不可标记Figma PASS**。设计师批准的V3.2仍是历史基线，V3.3需要真实Figma编辑/核验后才能升级批准。

## 已定位的旧风格偏差与对应唯一Owner
| 母站与需求 | 原Robotics | 新统一执行Owner |
|---|---|---|
| 正文 Noto Sans JP，Latin Poppins | `site.css` 前置 Apple-system/Segoe UI，部分产品CSS自定义 | `assets/css/site.css`＋构建字体加载；产品视觉 `assets/css/product-standard-v33.css` |
| 主蓝 `#009BD2`，深蓝 `#0069B5`，青 `#00B2BC` | `#009AD2`/`#079FCF`/`#10B8C7` 并存 | `site.css` 与 `main-site-experience.css`；保留既有合法产品强调色并以真实计算样式核验 |
| Header白底与圆角联系CTA、SP蓝色渐变全屏菜单 | 旧版共享Shell蓝黑Footer、SP白底导航 | `includes/site-header.html`, `includes/site-footer.html`, `assets/css/shared-layout.css`, `assets/js/mobile-qa.js`，只保留一个事件所有者 |
| 产品规格表必须白色背景、白/灰间隔 | 旧G1/H2/G1D及X2曾有蓝色行/蓝色分区和页面内`!important` | **唯一新增规格表颜色Owner** `assets/css/product-standard-v33.css`，构建最后加载 |
| Footer母站灰底白面板 | Robotics深色底 | 既有 `body.aa8-corporate-v1` scoped Shell，地址/ISMS旧信息禁复制 |

## 规格表强制设计（P1不可裁量）
- 外部规格区 **`#FFFFFF`**；表头 **`#FFFFFF`**；项目分组 **`#EEEEEE`**；普通奇数行 **`#FFFFFF`** / 偶数行 **`#F5F5F5`**；边线 **`#D9D9D9`**；文字 **`#333333`**。
- 13产品中**12个使用 `<table>`**，X2 EDU使用已有 `#specs .spec-table p`：只改变实际背景/字体，**不篡改**数据、内容、型号比较、来源链接或用户咨询内容。A2是另一条隔离Fixture，旧A2白灰表格已存在，日文74单元真人事实仍HOLD。
- 仅展示型规格表的中性色固定，不允许产品单独重写蓝色表头/行；未来新增字段和型号仍由Factory数据合同驱动。
- 白灰样式覆盖PC与SP计算后的真实背景，不是检测源文件中是否写了`#fff`。原有特殊组标题以灰色显示，保留原始列、滚动与参数比对语义。
- V3.3不重排产品HERO→介绍→场景→特性→规格→SDK→咨询，也不改变其他已批准的产品CTA主视觉。

## CI / QA 真实强制门禁
1. `tests/test_corporate_brand_v1_candidate.py`：母站契约/字体/色值、规格白灰固定字节、13款build的单次样式加载、公开Product Master V3.1不变、无ISMS误复制。
2. **复用** `tests/hp-shared-governance.spec.js`：13×PC1440/SP390/SP360真实浏览器，从 computedStyle 核验文字、Footer、规格区、表头/普通行/分组行；任何蓝/深色背景、表格缺失、X2蓝底都FAIL。
3. 复用 `tests/corporate-brand-optin.spec.js`：1024 PC/1023 Mobile边界、SP390/360菜单、Tab/Escape焦点、scroll lock及无横溢。
4. 保留其他原有测试：真实产品CTA参数继承、Header/Footer唯一源、资源/SDK、全13页Factory回归、独立技术QA，禁止用单一截图摘要代替实画面验收。
5. GitHub Actions只能标记**TECHNICAL_PASS**；Figma真实原生节点和画面对照、设计独立人评、Manufacturer human fact signoff、正式CRM询盘业务E2E、CEO精确SHA发布必须分别标记PASS，否则**HOLD**，不能自动合并main。

## 发布与管理
- 唯一开发仓库 `2airadmin8/aa8-Robotic`，仅原Draft PR #180；本轮没有新Runner、Workflow、PR、GitHub Pages任务或正式Customer/ERP写入。
- Source code JSX/模板/网页共有设计严格按明确Owner修改，旧有不同色的内联规则属于“历史待消除债务”，不在没有视觉回归时盲目删光；V3.3浏览器的计算规则必须盖过它们。
- 必须提供 **真实V3.3 Figma原生可编辑设计 + 13页PC/SP QA + 一次集中CEO精确SHA批准** 才能从Draft合并/一次性正式发布。缺少任意证明＝NO-GO。

## 2026-11-19 Mother Footer definitive: common component / no product facts changed
- **Primary WordPress CSS** `style.css` lines ~11490-11849 and `footer.php` lines 277-385; source content uses a 1280px white panel on #F4F8FA, radius 18, 280px company column + 4 visible navigation groups with `1.45fr .8fr 1.15fr .75fr`. Mobile <=1023 two-column groups, <=767 one-column groups with center alignment; 14px panel radius.
- **RCA:** original Robotics common Footer contained dark #061923 background, 2-column generic links, and an inline `<style data-aa8-footer-layout>` layer that bypassed the sole CSS owner. Merely swapping palette tokens did not recreate the mother's actual layout.
- **Fix Owner:** replace `includes/site-footer.html` with one semantic company + 4 group navigation structure and bottom utility area, remove its inline CSS, keep its existing isolated preview menu fallback runtime unchanged. Put all Footer CSS in `assets/css/shared-layout.css` only; remove original dark Footer declarations and conflicting opt-in overrides.
- **Robotics data preserved:** product / use-case / solution / case / resources / glossary / about / contact URLs remain existing Robotics paths; approved Robotics logo remains; **no mother-company obsolete address or ISMS certification claim is transplanted**.
- **Mandatory QA:** existing `tests/test_corporate_brand_v1_candidate.py` checks 4 groups, single include, no inline CSS and source value invariants; existing `tests/corporate-brand-optin.spec.js` checks actual computed footer width/color/border/typography at 1440/1024/1023/768/767/390/360; all 13 products still run existing shared Header/Footer/CTA regression. Pure screenshot integrity or green CI alone is not independent visual signoff.
- **Scope:** current Draft PR #180 only; no production merge, Pages trigger or CRM/ERP updates. Figma native V3.3 remains HOLD until real editable source readback and signoff.

## Chrome root-cause regression closure (2026-11-19)
- Following exact maternal font/tracking import, Unitree G1 360px model-choice text wrapped from 2 to 3 lines: #models actual 865.09375px vs preserved approved 840px. Independent SES-sLLM real Chrome isolated A/B showed restoring only the first model paragraph tracking to 0px at <=375 yields 839.625px and Model02 y=468.1875px. Mother Noto Sans font and text remain intact; source Owner `assets/css/g1-product.css`. The same approved G1 390px remains unchanged.
- Unitree H2 Plus 360px main CTA had scrollWidth154 > clientWidth152. Isolated real Chrome verified 0px letter-spacing makes scrollWidth152 and keeps 2 CTAs on one row, no clipping or text change; Owner `assets/css/g1-factory-v3.css`, only 360-375px. 320px retains earlier stack safeguard.
- The existing G1 exact Figma geometry tests and H2 Plus PC/SP/320 tests remain required; 5/5 exact local reproduction tests passed after isolated rebuild. Final trusted SHA CI / independent evidence still mandatory and separate from any Figma native or human visual signoff.

## 2026-11-19｜CI #44455912754 root-cause fixes, no gate bypass

- Full CI at previous head `6b1e42847c59dafc5f6d4e2199cf9a7d90659baa`: 273/278 Chrome PASS, FIVE failures. 2× A2 SP Preview still demanded **legacy 2-column** Footer but actual approved parent corporate Footer is **single column <=767**. Test updated to demand **one** group-column layout, **four** semantically named groups and actual gray #F4F8FA background; source remains unchanged.
- Three intermittent browser synchronization failures: (1) Factory offscreen `loading=lazy` CTA images may not finish loading when first scrolled into view; poll actual decoded image sizes >100px, keeping original strict image check. (2) On product inquiry navigation, `toHaveURL` can resolve before deferred `contact-v2.js` initializes fields; wait for actual `DOMContentLoaded` before still requiring exact product and maker prefill and the signed acknowledgement. (3) GSC/Google Fonts network activity can keep `networkidle` pending on homepage in shared menu comparison; use `DOMContentLoaded` then explicitly assert the real menu becomes visible, still compare computed styles/CTA on PC/SP.
- No changes to business runtime, source product facts, formal contact form submission, official manufacturer assets, webpage sales content or Production. No test is skipped or removed. All five conditions reproduced as a **local 8-case targeted suite 8/8 PASS** using existing SES-sLLM+real Chrome. Independent full current-SHA CI and separate technical QA still required.

## 2026-11-19 CEO政策更新与最終视觉QA收口

- **取消独立人员签核**：CEO明确决定「独立人员签核不需要」。该门禁标记 **NOT_REQUIRED_BY_CEO**，不是虚报实际有人签核。正式视觉验收使用 GitHub 精确SHA CI SUCCESS + 另一真实设备 AA8-N-012 自动视觉核验 **138/138 PASS**，包含母站PC/SP截图对照、13款产品×3种宽度规格表/Font/Footer检查，记录仍存原G盘 `01_HP管理ポリシー/00_設計書/QA_Evidence/PR180_V33_120c03d1_20261119/`。
- **Figma原生仍是唯一剩余设计门禁**：在原文件 `uo56l51NgUqit4976LV6P2` 内真实创建/更新V3.3可编辑组件、Tokens及PC/SP参考，读取原生结构和截图才能PASS；导出SVG图、PNG或JSON本身不是完整原生签核。MCP Starter调用额度限制不禁止浏览器正常编辑。
- **独立视觉QA发现的真实漏检**：旧`assets/img/airadmin8-robotics-logo-footer.svg`采用`fill="white"`的母站旧深色Footer版本，放在本轮白底Footer后会丢失Logo中的字标。这个问题不属于1px浏览器误差。直接用现有正式`logo-pc.svg`深字版替换同路径Footer Logo素材，不增加第二Owner、不改厂家业务数据或CTA，新增严格对比度防回归测试，必须重新跑新HEAD CI。
- 正式上线仍按旧规则：Figma原生PASS、最新HEAD GitHub CI + 独立设备QA、业务FACT/CRM必需Gate、CEO精准SHA一次集中批准后单次manual-only生产发布。未经CEO上线批准不得合并main、发布Pages或写CRM。


## 2026-11-20｜Figma V3.3正式原生设计与自动视觉验收：最终验收补记

**前面2026-11-19关于Starter MCP不可写、Figma尚未完成、独立人员签核待办的句子仅保留为历史记录。此节是当前最终判断。**

- **Figma已有正式文件直接升级、非复制新文件：** https://www.figma.com/design/uo56l51NgUqit4976LV6P2 。Chrome已登录的正常Figma编辑器实际新增页面 `02｜AA8 CORPORATE V3.3｜HEADER FOOTER SPECS｜PC SP`，保留原V3.2页面及产品内容。8个真原生可编辑顶层组件在浏览器重新加载后逐个验证名称、节点ID、尺寸及Component属性；全部PASS：
  - `173:2` Corporate Tokens (1120×690)；`174:2` PC1440 Shared Footer (1440×382)；`175:2` PC1440 Shared Header (1440×100)；`176:2` PC1440 Specifications (1440×1040)。
  - `181:2` SP390 Shared Header (390×64)；`182:2` SP390 Shared Footer (390×1024)；`183:2` SP390 Open Menu (390×844)；`172:261` SP390 Specifications (390×1500)。
  - 误嵌套旧画板和临时测试图层已经清理。刷新Figma后8/8顶层组件均PASS。
- **Figma原生变量20件正式写入＋读回成功：** 品牌色/白灰规格/正文共12色、Noto Sans JP/Poppins/Noto Serif JP共3字族、CTA与Footer尺寸共5项。按Figma Starter当前权限，变量存于已有 `AA8 Robotics V3.2 / Core Colors` 集合的 **`v33/` 分组**，不改动旧V3.2的8项变量值；历史旧变量8/8回读一致。不能创建变量的空V3.3集合已经清理，勿将其当新SSOT。Token数据正本为 `ops/brand-preview/figma-product-v33-tokens.json`，实际Figma组件与VariableID见证据。
- **V3.3母站规格：** Deep `#0069B5`、Primary `#009BD2`、Teal `#00B2BC`、正文 `#333333`、Footer `#F4F8FA`，规格表白底 `#FFFFFF`／组行 `#EEEEEE`／间隔 `#F5F5F5`／边线 `#D9D9D9`。仍采用Robotics现有真实产品语义，不复制母站的旧地址和ISMS声明。
- **同代码基线独立设备视觉QA：** 原Draft PR #180代码SHA `95c3174e7f42b981ca0c3e20b8612870053bee65`，GitHub Actions #44494212204 Build＋Separate Technical QA SUCCESS；AA8-N-012独立真实Chrome **139/139 PASS**，包含13款产品×3宽度＝39/39、母站PC1440/SP390真实Footer对照和白底正式深色字标防回归。没有正式邮件发送、CRM/ERP生产写入和GitHub Pages部署。
- **CEO确认简化审批：** 独立人员人工美工签名为 **NOT_REQUIRED_BY_CEO**，不是假定存在或伪造他人签字。自动设备QA是通过的验收依据。最后一次集中上线批准只由CEO对精确最终HEAD进行业务决定。
- **最终证据及SHA：** https://drive.google.com/drive/folders/1FwqkSmAkTyscLAX0tls2uBqh9ZSO0jvG （Figma Components8、Variables20、Legacy8 unchanged、独立实机139条测试、源母站截图/HTML实际渲染比较和全部SHA256）。
- **Production仍HOLD：** Figma/视觉设计门禁PASS不等于CEO批准上线；原PR #180仍Draft。当前仅追记治理文件，形成新HEAD后须重新确认CI/独立设备QA；所有安全及回滚门禁满足时，才对CEO提交一次集中批准。A2仍独立releaseReady=false/noindex，绝不作为额外新公开SKU随此次上线。
