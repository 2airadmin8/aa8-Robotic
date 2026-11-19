# AirAdmin8 Robotics｜Product Visual Standard V3.3（DRAFT / NOT RELEASE APPROVED）
**基準日:** 2026-11-19 JST  
**状态:** SOURCE_RECONCILED / DRAFT_CODE_STAGED / FIGMA_NATIVE_BLOCKED / INDEPENDENT_VISUAL_HOLD / PRODUCTION_NO_GO.

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
