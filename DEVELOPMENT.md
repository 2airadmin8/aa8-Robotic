# AirAdmin8 Robotics Development Standard

## 1. Simple first
- 解决问题优先采用最简单方案。
- 不为“看起来完整”增加无必要的框架、脚本或流程。

## 2. Single source of truth
- Header：`includes/site-header.html`
- Footer：`includes/site-footer.html`
- Header / Footer / Logo / Navigation CSS：`assets/css/shared-layout.css`
- 图片：`assets/img/`
- Workflow：仅保留 `ci.yml`、`pages.yml`、`production-check.yml`

## 3. Modify before adding
新增文件前，必须先确认现有文件无法完成需求。

新增以下内容时，必须说明原因：
- CSS
- JavaScript
- Python脚本
- Workflow
- 目录

## 4. Delete replaced code
每次开发完成时，必须检查并删除：
- 已被替代的旧代码
- 旧Logo、旧路径、旧CSS补丁
- 0引用且确认无构建用途的文件

不为整理而盲删。

## 5. Done definition
只有以下全部通过，才算完成：

1. Build PASS
2. Link / asset verification PASS
3. Header / Footer regression PASS
4. GitHub Pages deploy PASS
5. Production SHA matches main
6. Production page manually confirmed

Commit或Merge不等于完成。

## 6. Keep CI small
CI只负责防止重大事故：
- Build失败
- Broken links / missing assets
- Header / Footer回归
- 旧Logo / 旧URL回归
- Production SHA不一致

禁止无必要增加大量健康检查。

## 7. Change report
每次修改结束时，报告以下内容：

- 新增文件
- 修改文件
- 删除文件
- Build状态
- Pages状态
- Production状态

## Final rule
功能可以持续增加，但维护入口必须保持少、清晰、可追踪。
