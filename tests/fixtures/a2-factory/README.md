# Unitree A2｜真实メーカー资料→既有Factory Preview｜单次受控效率试点

**正式SKU：** Unitree A2 标准四足机器人（不是A2-PRO）
**状态：** PREVIEW_ONLY；所有网页、图片与规格不得自动进入正式产品目录、main或Production。
**厂家官网：** https://www.unitree.com/A2/
**厂家正式网页资料快照：** 2026-10-28，Drive ID `1reZR6ITCYq1n9Ct2T9pKYHWO8oR9uJp6`，SHA256参见`source-contract.json`。
**最新厂家网页复核：** 2026-11-14 HTTP200，标准版与PRO两版本区别；不使用第三方价格。
**厂家图片：** 本仓库既有官方A2产品图`24_a2.png`＋5张独立Unitree官网素材；源URL、字节SHA256均记入`source-contract.json`。
**首次源资料合格时间（JST）：** `2026-11-14T23:03:22+09:00`（文件为真实时间，不回填到2026-10-28旧快照时间）。
**Factory：** 使用主仓库现有`scripts/product_factory.py`及`--draft-product`入口。
**安全：** `releaseReady:false`、`visibility:hidden`、`noindex,nofollow`、不修改正式`data/products.json`（仍13条）且不生成正式`products/unitree-a2.html`。
**SDK与商业信息：** ROS 2具体版本／A2专用SDK／日本报价、交期、售后仍需厂家确认，禁止虚构。
**价格声明：** 只表示要询价，正式页面暂不发布。
**QA范围：** `tests/test_a2_factory_pilot.py`及`tests/a2-factory-preview.spec.js`、13款现有产品回归；禁止向正式咨询表单提交。

## 实际Developer返工记录

首版生成后，单元测试发现规格表未独立列出“连续行走载荷约25kg”。在相同隔离入口补充真实厂家规格、重新生成Preview，属于首次开发内技术返工，**不是CEO真实退回事件**。修复证据：`initial-rework-evidence.json`；当前开发返工次数1，CEO正式反馈次数0。

## 停止／成功规则

- 此PR为Factory真实新SKU首次Preview。只记录已核实资料时间与首次Preview、独立QA真实事件。
- 未取得CEO亲自通过2airadmin8发布的合格退回评论、且安全开关保持OFF时，禁止冒称已完成“CEO退回→AI修复”E2E。
- 每次返工最多3轮，唯一原Draft PR，新HEAD完整CI＋AA8-N-015独立QA；任何缺证据立即HOLD，不绕过门禁。
- 原2条历史Factory KPI记录均`HISTORICAL_INCOMPLETE`，即使A2第1条完整记录通过，也不能声称已经计算出效率下降百分比；需另一可比SKU。
