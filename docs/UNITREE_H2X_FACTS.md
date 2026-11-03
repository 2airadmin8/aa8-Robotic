# Unitree H2-X｜产品页单一事实与素材基线（2026-10-31）

## 页面状态
- H2-X 正式线上基线：`a0f3556edf704745b837fcb3390333a9b05b1045`。
- 本轮：隔离 Draft PR，待 CEO 检查真实 HTML Preview 并按新 HEAD 授权。**本文件不是上线完成证明。**
- 产品：Unitree H2-X，独立于 H2、H2-D；官方资料 https://www.unitree.com/H2-X/ 。
- 产品规格：31 DoF、1725×455×245mm、65kg以上、腿最大300N·m、臂最大150N·m、20Ah双电池（总1.152kWh）；H2-X标准版二次开发非对应，EDU支持但具体SDK依SKU。
- 日本价格、库存、交期、保修与SDK仍需正式商谈确认；不虚构授权与业务保证。

## 正确素材正本
G:\共有ドライブ\002_PAI_ID009_[PhyicalAI]_AIロボット\03_販売製品資料_カタログ_パンフレット\Unitree\素材\ヒューマノイドRobot\ヒューマノイドロボットー3種５品\H2-X_assets

- 当前 G: 文件夹共25件，为 H2-X 正本。早期提供的 Google Drive H2_assets **不是** 本产品素材正本，不应再引用为 H2-X。
- **新指定主产品图** `image_007.webp`：原文件 88,124 bytes，1290×1930，含 alpha；SHA256 `4D08C159B66D85C66E5212208B757060B97817A4125FE00ADFB695AC3459F0E5`。复制原字节至 `assets/img/products/unitree/h2x/drive/image_007.webp`，不编辑 G: 原始素材。
- Hero、产品列表目录、Open Graph 分享图使用**同一张** `image_007.webp`；CSS 仅控制图像在白色背景中完整显示，不改变原始图。
- 实景图仍用 `image_005.webp`、`image_012.jpg`、`image_013.jpg`、`image_014.jpg`。其他源图保留在G:，无需重复堆砌。
- 视频仍用 `video_01.mp4`（14.46s）、`video_02.mp4`（14.94s）、`video_03.mp4`（11.40s），H.264/AAC，已有真实 Chrome 播放证据。修改主图时不得破坏这3段视频。
- 官网旧 `h2x-hero.png` 是此前官方技术标注图，保留在仓库作为历史/可回滚素材，但**不用于主产品图**。

## G1 母版必须继承的规则
- 共用 Header/Footer `data-shared-layout`、`g1-product.css` 布局骨架、`g1-shell`、锚点导航、主CTA、规格表、FAQ、相关产品模块。
- 所有已批准的 G1 派生产品页规格表首列：**モデル**，不可为 `項目` 或 `比較項目`。三列表头必须为 `th scope="col"`。
- H2-X 页面目录里必须有「写真・動画」入口，并与 `#media-h2x` 对应；章节番号无重复：01/02/03/04/05/06。
- H2-X 型号、ALT、页内导航、FAQ 不允许混成 H2；只有「H2-X 和 H2 的产品比较」可使用独立的 H2 字样。
- 主图必须匹配 `1290×1930` intrinsic 尺寸，PC1440/SP390/360 保持完整主体、无横向溢出、无图片404、无白底白字。
- 素材商业使用遵守既有 CEO 方针，标注厂商来源，不声称无条件版权授权。

## 验收与发布门禁
同一 PR 与精确 SHA → GitHub CI、另一环境独立 QA（PC/SP、目录、分享图、3段视频、CTA）→ 可交互 noindex HTML Preview → CEO 单次明确批准 → 受控合并/手动发布/线上SHA及真浏览器回归。

## 2026-10-31｜CEO指出的背景/CTA视觉不一致：独立修复候选
- 生产基线 main: `c21c1dbd57038225512c5191ad337150147c2c3d`。用户指出此前「PC/SP25/25 PASS」不能代表实际G1 Figma视觉一致。
- 实测 G1 的首屏及非CTA正文都是纯白，G1最终CTA使用 `assets/img/products/unitree/g1/g1-cta-figma-pc.png` 背景及海军蓝遮罩，3张带图片的G1 CTA卡片；H2-X此前仍有白蓝渐变首屏、浅蓝正文、深蓝无图文字CTA。
- 本候选只调整 H2-X: 首屏及各大正文区恢复纯白；末尾复用真正G1 `g1-final-cta`/`g1-cta-grid`/`g1-cta-card` 结构和同一个几何背景图。H2-X 官方图片分别作为视频/型号对照/咨询卡片，现有 H2-X 视频、`image_007.webp`、SKU、SEO、G1原页及其它产品保持不变。
- 新增 `tests/h2x-g1-fidelity.spec.js` PC1440/SP390/360 **同时读取G1/H2-X的实际computed CSS**，验证背景URL一致、白色主体和三张有实图的CTA卡片，而不再仅测试“蓝色就算通过”。
- 本阶段 Draft PR / 未授权生产上线；需精确SHA的独立QA、GitHub CI和真实noindex HTML Preview，CEO再次批准才合并/发布。
