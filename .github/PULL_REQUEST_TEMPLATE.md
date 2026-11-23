## 设计正本 / Design SSOT
- Design / Figma / Drive：
- 业务目标与范围：
- **产品PR定义（新SKU必填）**：ProductID／产品家族（biped、biped_accessory、quadruped、quadruped_accessory）／客户购买场景／核心价值／唯一主要咨询CTA：
- 正本归属：正式网站data/products.json／隔离Fixture（尚未发布）；ERP Product Master为另一系统，不得自动混用ID：
- 禁止改动的文件、流程：
- 对应 Issue：

## 变更与根因 / Change & RCA
- 类型：BUG / Feature / Content / Infrastructure
- BUG-ID（非BUG填 N/A）：
- 原始复现（Expected / Actual）：
- 根因（不是现象）：
- 优先级 P0/P1/P2/P3：
- 设计→代码对应模块ID：
- 影响页面/组件/PC-SP：
- **改动归属**：SKU局部／共通Factory・Header・Footer・CTA／CI。凡有共通变更即按全部13款正式产品做回归，不得因为仅1个SKU就标为单品：
- 本次Bug List：每项ID／原图位置／实际原因／修复文件／状态OPEN・BLOCKED・PASS，不能用单纯截图Artifact代替关单：
- 本次修复范围：

## 防再发回归 / Regression
- 自动测试文件与测试名称：
- 修复前 RED（测试失败）的证据：
- 修复后 GREEN（测试通过）的 CI Run：
- PC/SP、关键业务边界检查：
- **逐项视觉对照**：原CEO红标／最新精确SHA截图PC1440・SP390・SP360／独立差异判定与P0/P1关闭记录URL；未完成填VISUAL_HOLD：
- **厂家数据双层签核**：原厂快照URL＋SHA＋来源日期／逐型号原文和日文对照／技术事实QA／独立真人语义签核。即使74/74技术一致也不能写真人APPROVED：
- 关键客户路径：Hero／用途／型号比较／SDK资源／相关产品／最终咨询CTA，以及手机滚动、无裁切、可读性：
- 与已有 PR 的冲突审查：

## 真实业务证据 / E2E
- 环境：MOCK / DEV / STAGE / PROD
- 真实操作与最终结果（不得用HTTP200冒充业务完成）：
- 证据：脱敏记录ID / 图片 / 日志 / Run URL：
- 未完成的真实业务 Gate：
- **产品发布状态四分离**：TECHNICAL_CI／VISUAL_INDEPENDENT_QA／MAKER_HUMAN_FACT_SIGNOFF／LEAD_CRM_E2E，每项PASS或HOLD及证据（不得共用一个PASS）：
- 失败 / 回滚时的应对：
- 终止条件与价值证明（安全/核心功能100%；视觉/文案达标即停；额外打磨需收益证据）：

## 独立 QA 与发布
- Dev 负责人：
- 独立QA审查者（不得与Dev相同）：
- QA结论：PASS / PARTIAL / BLOCKED / FAIL
- **精确SHA验收矩阵**：CI Run／独立设备／部署ID／现场截图Artifact／线上HTML・图片SHA／P0/P1残项：
- **独立审查人及事实证明**：技术QA可由独立设备执行，但CEO控制的第二GitHub账号不能冒充独立真人；未对照原图只能记EVIDENCE_PASS/VISUAL_HOLD：
- 生产发布：需单独审批；不因 PR CI PASS 自动合并或发布
- 业务完成判定：PASS / PARTIAL / BLOCKED / FAIL

> 不得填入真实客户个人信息、密码、密钥、邮箱正文、非公开报价资料。
