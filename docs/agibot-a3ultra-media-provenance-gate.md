# AGIBOT A3 Ultra｜G1页面候选 / 厂家素材溯源阻断（2026-10-31）

## 关键产品图片冲突（P0｜未经修正不可上线）
- CEO指定的 G:\... \ AGIBOT \ A3Ultra_assets \ image_023.png 完整 SHA256 是 d7a18459cb87c25f145602ab4c65b31329bc5af3f33bf5fb464e327e18a41512。
- AA8-N-024 实际反查旧 A3Ultra.html（2026-10-28，SingleFile 误保存）中第22个嵌入图片，SHA256 完全一致，源 HTML 区块为 A2Ultra_Seven / Product Specifications。
- 该图属于 A2 Ultra 产品图，不能以 A3 Ultra 官方主图出现在正式页面。
- G盘所谓 A3_assets 文件夹不存在，现有 A3_assets-cn 和 A3.html 是另一 SKU AGIBOT A3（55kg、10小时等规格不得复制）。
- 本候选使用经验证的 A3Ultra_EN/01_公式图片/A3Ultra_One-bg.jpg 作为准确的 A3 Ultra 主视觉，并将指定旧图保留为质量审查证据而非产品展示。
- **该候选不满足 CEO 指定原主图文件的字节级要求。未经明确认可换图，不允许合并或上线。**

## 真实官方产品来源
- 厂家官方 A3 Ultra：https://www.agibot.com/products/A3Ultra
- 厂家官方使用手册：https://www.agibot.com/filepage/319.html（2026-10-23）
- 素材：G:\... \ AGIBOT \ 素材 \ ヒューマノイドロボット \ ヒューマノイド製品 \ A3Ultra_EN
- 正式图 8张，经过来源 URL / SHA256 验证，不使用 A3 的产品图片。
- 3个厂家原本 MP4：1.mp4、2.mp4、A3Ultra-2.mp4。主宣传片 A3Ultra.mp4 共154MB，本候选未复制避免 Pages 膨胀。视频真实解码已在 AA8-N-024 对完整8本验证通过。

## 设计和业务
- 完全继承 G1 版本，Hero 和各正文段落纯白；Figma G1 统一图片 CTA 背景与3张素材卡。
- 图库用厂家真实 8 张场景图及规格图。
- 底部四个关联产品与真实产品目录相连。
- 中文 A3 页面功能描述只作同系列参考，不作为A3 Ultra的证据正本。
- 厂家确认值：174cm、约60kg，700 TOPS、8小时综合电源运行（按使用条件），51基础 DOF，手部最高选配20自由度，360度传感、UWB和RTK等。
- 售价、日方SDK支持、保修、纳期、导入规格保持未知状态；不得做保证。

## 测试与生产 Gate
- 原有 G1 factory 单元与安全门禁；浏览器 1440 / 390 / 360 真实 computed CSS、主图和8图、3视频、三图CTA、4相关产品、咨询预填。
- 实际生产发布需要新的 exact HEAD CEO 明确批准，包括图片更正决定。
- 此 PR 基于 H2 Plus候选分支，是 stacked Draft PR，不得合并到主站前覆盖 H2 Plus的受控 PR。
- PR CI / 独立AA8-N-015 验收和审批仍需执行；任何失败停止。
