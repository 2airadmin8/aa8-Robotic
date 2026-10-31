# Robotics 大学営業｜邮件・开封・产品点击・咨询归属闭环 V2

基线：2026-11-01 JST｜现有唯一站点仓库 2airadmin8/aa8-Robotic，当前 main 8e7fad7a0d99a763b313b0181bd82fd3c0f4b31b。
**此目录是受控改造候选代码，不代表 GAS/Vercel 或 GitHub Pages 已上线。**

## 原正本（不能新建第二套）
- 既有 GAS：airadmin8-haishin，Script ID 1_SCkBvYmNVF2w19ngJRmSzw3wSO-58Zr6B3XnQ-D7p0U0s37bdfAiGsG
- 原 Google Sheet：本番_大学営業メール自動化_自動調査シンプル版_v4.0，Spreadsheet ID 1zhmDOkQkBRmAiTV8uu4teptbN_hiZczg_7cdHY1_7yY
- 正本 Tabs：メール送信管理 / 送信履歴 / EmailOpenLog / Web行動ログ / メール行動分析
- 既存反响 Trigger：salesEngagementHourlyTrigger_ → syncWebEngagementFromLog_ → refreshEngagementDashboard_；不得创建新 Trigger/Runner
- Vercel已有项目 hikari-proxy-dev，项目ID prj_xJW0H0vKZ3hnHrUevcHBJQrnIGT6，GitHub与官网同一仓库
- 现有真邮件链接已包含 PDF 的 rid=DLV-... + UTM，官网根 URL 和产品页原来未必带 rid
- 之前 Web行動ログ 31 条记录均为 PDF，最后9月4日，没有已核验的产品点击行
- Vercel hobby runtime log retention约1小时，不是可依赖的长期业务账本

## 新业务流程
1. 原GAS把每封新的模板邮件生成同一送信管理ID（DLV/RSJ），原PDF链接保留 RID/UTM，新模板额外加入具有 RID/UTM 的机器人产品目录 URL，原发送授权和去重规则不变。
2. 官网 analytics-events.js 接收并严格校验 RID，30分钟同一浏览器Tab内沿站内 URL 传递；恶意ID、跨域URL和资料文件地址不继承。
3. 事件含 event_id(UUID)、event_at、delivery_id、page_path、page_type、product_id、target_product_id、target_path，仅记录最小业务属性；不上传客户姓名/邮箱/IP/查询全文。GA4/dataLayer不接收 RID 或完整RID URL。
4. 现有 Vercel /api/web-event 校验 Origin、事件类别、页面路径、时间窗口、ID与型号，使用 Google Web App URL + HMAC签名转交原GAS。GAS只在写入既有 Web行動ログ并确认后返回 persisted=true；重复event_id返回 duplicate=true。未配置签名、数据不合法、写失败则返回503或拒绝，绝不假报成功。
5. 原GAS doPost（新增同一个项目里的08_web_event_ingest.js）验证签名并检查唯一已发送配信ID，再对原Web行動ログ写入。新增仅「イベントID」「遷移元パス」两列；不建新 Sheet/数据库。
6. 原salesEngagementHourlyTrigger_继续调用 syncWebEngagementFromLog_，再调用 syncAa8WebMarketingSummary_ 写回原 メール送信管理 的派生列：Web閲覧数、製品閲覧数、製品リンククリック数、最終クリック製品ID、最終Webページ、最終Web反応日時、開封品質区分。
7. 原問い合わせGAS确实返回 persisted 的成功响应后，前端才发 aa8:inquiry-confirmed，产生 lead_inquiry_success 行为；原問い合わせSheet仍是正式咨询数据正本。source_page 保留 RID，可按RID追溯到配信管理。
8. EmailOpenLog继续是原来的开封正本。GoogleImageProxy / Apple Mail Privacy Protection / 扫描器只标「画像代理取得のみ・真人未确认」，其他UA也仅「開封観測・真人未确认」，任何开封不自动标记高意向。

## 触发方式与数据安全
- 不创建新Automation、Master、Timer、Runner、Webhook项目或监控系统；Vercel 使用既有项目，GAS 使用原脚本，表使用原5个正本。
- 单纯的 PDF landing 自动跳转只能确认「PDFリンクへのアクセス／リダイレクトを実行」，不能证明PDF被阅读或人类打开。
- 同一产品页面 lead_page_view + product_view 为两条不同含义事件，统计时分别计数避免重复计算同一次访问。
- GAS 收到未知ID / 非已送信 / 重复配信ID / 伪造签名 / 超时 / event_id 重复时拒绝或幂等处理。
- Vercel不可存放 GAS Script Property；两端凭据只存于各自秘密设置，绝不可加入 repo/GitHub logs/浏览器。
- 既有网站生产页面仅 GitHub Pages 一次手动发布，GAS版本/现有WebApp及Vercel生产环境需分别有明确审批。
- 日方公开隐私告知应在启用跟踪前确认，包含营销邮件行为测量、保存期限与退出渠道；严禁因开封自动推送邮件。

## 现有配置缺口（截至本轮只读查询）
Vercel hikari-proxy-dev 环境仅见 DIFY_API_KEY；不存在以下配置：
- AA8_SALES_WEB_EVENT_WEBHOOK_URL：经过正式验收的现有GAS Web App /exec URL
- AA8_SALES_WEB_EVENT_SIGNING_SECRET：独立且长度>=32的服务端密钥（与 GAS Script Property AA8_WEB_EVENT_SIGNING_SECRET 同一值）
因此**当前无法证明真实云端入库，不能将本PR的模拟 PASS 写成生产闭环 PASS**。

## 最小安全发布顺序
1. AA8-N-018 已只读克隆原正式GAS 8文件；使用 patch_existing_sales.py 对现有03_sales_import_dedup.js做最小3处补丁；原文件只读保全。GAS新增08/09/11三个文件；不变更04_email_open_tracking.js。
2. DEV/UAT先使用合成的 SENT 配信ID和Fake Google Sheet 运行所有正反例，检查14列及派生列；人为异常fail-closed、0外部发信。
3. CEO批准原GAS正确源码版本及WebApp受控更新后：只部署现有WebApp一次、不新建另一个脚本；核对原 doGet 开封不退化和正常 doPost 签名ACK。
4. 在既有Vercel项目设置签名URL/密钥，不把密钥泄露到GitHub；以仅一条合成/内部测试事件确认 GAS Web行動ログ真实入库及 event_id去重，并验证旧每小时trigger能读取。
5. CEO另行审查本PR精确GitHub HEAD、必需CI和AA8-N-015独立Chrome QA；合并后审核自动Vercel部署与Pages手动单次部署，失败停机不反复重试。
6. 正式发布后用真实配信的RID只读核对「Web行動ログ—メール送信管理」关联，记录点击哪个产品与时间；真实咨询另外核对原Inquiry SSOT，无发送客户测试邮件。
7. 失败时停在本轮，无第二WebApp、无重复Pages或重发邮件；回滚Vercel/GAS源码及版本，旧配信与开封保持原样。

## 必需自动测试（不得以模拟代替实链）
- 后端：未配置503、未知Origin403、无效RID/UUID/过期/伪造400、HMAC有效才转发、GAS明确ACK才202、重复event_id不重复写、任意sink错误不报成功。
- GAS：模拟真实已发送ID、原12列→增加两列、写入正确点击型号/URL/事件时间、PDF归类、签名拒绝、重复幂等、代理开封不认定真人、派生汇总使用同一管理表。
- 邮件模板：既有原01/03源不重建，PDF仍正常、加入含RID/UTM的目录URL，其他发送授权和Draft逻辑不变。
- 浏览器：PC1440/SP390/SP360邮件RID进站→产品点击→目标页访问→咨询预填；无RID不得构造销售行为；隐私GA4不携带RID；PDF landing完整路径。
- 真实生产：以上自动PASS后还需要Webhook与GAS ACK真实读写E2E、Gmail原发送不退化（仅原有已发送只读证据）、不发送新营销邮件。

**不可回补的历史空缺**：Vercel日志旧事件没有持久化时，不能假造产品点击或补齐真实客户轨迹。
