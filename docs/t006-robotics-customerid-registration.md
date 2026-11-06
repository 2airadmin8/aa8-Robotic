# T006 × Robotics｜正式CustomerID自动登记的受控接续（2026-11-04）

## 真实当前状态
- 既有DEV WebApp @3：咨询接收、InquiryID、原27列入库与CEO内部4封通知验收已实测；新增两条均为内部合成数据，不是真实研究者。
- 既有T006代码：正式 ScriptID `1_SCkBvYmNVF2w19ngJRmSzw3wSO-58Zr6B3XnQ-D7p0U0s37bdfAiGsG`；`05_runtime_p1.js` 中 `p1AssignOfficialCustomerIdFromIntake` 对正式 `00_新規受付` 分配/继承 `L-xxxx`，实际目标是正式 `大学AIロボット営業_顧客Master_APP完成版`，不能在原Inquiry DEV的 `01_Inquiry` 上直接调用。
- 真实两笔内部Inquiry与正式大学Person Master核对：邮箱、姓名＋所属匹配各0，均应保持 `HOLD_EVIDENCE`；不得因为“客户咨询提交成功”就生成正式CustomerID。
- 正式T006既有Writer存在危险路径：当Primary邮件相同而姓名＋所属无法确认时，原函数可取 `uniqueEmailIds[0]` 并标记 `EXISTING_INHERITED`。这不是安全的正式身份继承条件；必须在接入官网自动消费前完成最小防护。

## 新增候选代码（不是第二Writer）
- `ops/inquiry-api/T006_Robotics_CustomerID_Gate.gs` 只计算准入：`NOT_APPLICABLE`、`HOLD`、`READY_REUSE_EXISTING` 或 `READY_REGISTER_NEW`；永不创建CustomerID、写Sheet、发送邮件或生成Case。
- 原真实大学 `00_新規受付` 的SourceID必须等于既有InquiryID且唯一。先比较原Inquiry和接收表，再比较正式Person Master的Email与姓名＋所属。邮件一致而身份不一致、一人多ID、SourceID重复都HOLD。
- `READY_` 还需由既有T006可信服务端取得官方邮箱来源与Identity/Dedup的完整Evidence。表单勾选隐私、官网source_page或网页传来的伪造Evidence不能使其通过。
- `READY_REUSE_EXISTING` 只把已核验现有CustomerID作为候选，最终由**原T006加锁Writer**写正式受付；`READY_REGISTER_NEW` 不自造ID，须使用原T006加锁Writer原来的L-xxxx分配、冲突处理、关联及回读。
- 自动营销许可仍为NO；普通咨询/开封/PDF不自动建PAI Case。企业不得写大学Person Master。

## 上线前还需要做的真实集成
1. **在既有T006的真实Source intake入口**，对正式 `Robotics_Web_Inquiry` 类型增加上述准入。T006自身生成可信Evidence结果（不能接受Public GAS、表单、调用参数自称verified）；只由授权T006主流程调用原 `p1AssignOfficialCustomerIdFromIntake`。
2. 查明现有T006版本/正在运行的trigger和其他Source兼容；修改原Writer仅必要入口，不替换其他营业数据，不改变正式27/17列，也不创建第二Master。
3. 由真实已核验大学Person进行：InquiryID→唯一SourceID→T006 Evidence确认→正式CustomerID复用/分配→原表回读→后续PAI Case仅明确Event。先用隔离真实Writer/正式批准的测试目标完成E2E，完整留存客户身份及回滚证据。
4. 当前没有受控隔离Customer Writer及合法可登记的真实测试身份；不能把此候选代码与通过的单测视为已完成正式CustomerID登记。正式Master写入需要独立精确SHA审批；Production立即写入仍禁止。

## 受控变更边界
- 原仓库：`2airadmin8/aa8-Robotic`；任务Issue #166；原Draft PR #127；设计SSOT V129第1～20章全保留。
- 本轮只增加纯Gate与6条关键回归并挂到原CI，正式T006在线脚本/Production/Customer Master未改，实际CustomerID创建数0。
