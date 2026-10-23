## 设计正本 / Design SSOT
- Design / Figma / Drive：
- 业务目标与范围：
- 禁止改动的文件、流程：
- 对应 Issue：

## 变更与根因 / Change & RCA
- 类型：BUG / Feature / Content / Infrastructure
- BUG-ID（非BUG填 N/A）：
- 原始复现（Expected / Actual）：
- 根因（不是现象）：
- 本次修复范围：

## 防再发回归 / Regression
- 自动测试文件与测试名称：
- 修复前 RED（测试失败）的证据：
- 修复后 GREEN（测试通过）的 CI Run：
- PC/SP、关键业务边界检查：
- 与已有 PR 的冲突审查：

## 真实业务证据 / E2E
- 环境：MOCK / DEV / STAGE / PROD
- 真实操作与最终结果（不得用HTTP200冒充业务完成）：
- 证据：脱敏记录ID / 图片 / 日志 / Run URL：
- 未完成的真实业务 Gate：
- 失败 / 回滚时的应对：

## 独立 QA 与发布
- Dev 负责人：
- 独立QA审查者（不得与Dev相同）：
- QA结论：PASS / PARTIAL / BLOCKED / FAIL
- 生产发布：需单独审批；不因 PR CI PASS 自动合并或发布
- 业务完成判定：PASS / PARTIAL / BLOCKED / FAIL

> 不得填入真实客户个人信息、密码、密钥、邮箱正文、非公开报价资料。
