# X2 EDU｜60分納品スプリント／自動開発RUNBOOK
Version: 2026-10-13 / CR-20261013-01
## 目的
X2 EDUの日本語製品詳細ページを、G2未公開新版の判断＋Evidence型に沿って完成候補にする。対象は製品詳細1ページのみ。代理店・他製品・本番環境に触れない。
## SSOT
- 画面定義: https://docs.google.com/document/d/1LtaMuz3cS2kiplMyT6XFeu36GVMzXLv6w5CQE237_T4/edit
- 進捗: https://docs.google.com/spreadsheets/d/1dhuSy4kkPMo9fKN7KUj27aBdIrwtQBcTOdxxqs6iU88/edit
- 素材: https://docs.google.com/spreadsheets/d/1Mq_nGum8uJ6dOCflLOSiOe-uaZWjm-6GOTG-qVi3x7A/edit
- Code: GitHub 2airadmin8/aa8-Robotic / PR #108
## 自動開発プロセス（並列作業禁止の依存順）
0-10分 現状固定: 対象HTML、CSS、画像パス、SEO、最新CI SHA、画面定義の差分記録。
10-25分 実装: G2の10 SectionをX2 EDU教育購買ストーリーへ適応。既存共通Header/FooterとCSSを維持。製品名X2 EDU、代理店文言無し。Heroメーカー資料画像。仕様は2026/06原典に限定。
25-40分 QA: GitHub Actions build+Playwright PC1440/SP390、画像naturalWidth、object-fit:contain、水平溢れ無し、JS Error無し、CTA/404、SEO、製品名、重複、未確認事項をチェック。実画像のスクリーンショットをArtifactに保存。
40-50分 修正: NGはIssue化して同じPRブランチへ最小パッチ、CI再実行。テスト無効化は不可。
50-60分 Handoff: 最新SHA、PR、CI実行URL、PC/SPスクリーンショット、未完了／ブロッカーをDriveに記録。
## 役割
PM=作業順序・Drive進捗、Design=G2視覚基準/Figma、Developer=GitHub実装、QA=独立観点の検査、技術=メーカー事実、CEO=本番公開承認。
## 公開ゲート（Fail-closed）
A: Design Master PC/SP承認
B: 素材と権利、機種一致・仕様整合
C: CI成功、実ブラウザPC/SP、フォーム実受信、SEO/リンク、Figma差分審査
D: CEO承認、Production SHAとRollback SHA確保
いずれか未合格なら本番マージ・公開はしない。Vercel管理画面/認証画面のHTTP 200をページ描画成功とみなさない。
## 設計の10セクション
01 Hero／02 教育課題／03 教育用途／04 組立キットと実習／05 他方式との棲み分け／06 Hardware Capability・仕様／07 ROS2・DDS・MuJoCo開発／08 導入チェック／09 購入後・サポート／10 最終CTA。
## 技術の表現統制
約1.3m、約35kg、29DoF、RK3588、48V 10Ah（資料では500Wh）、最高1.8m/sは原典記載値として扱う。標準ダミーハンドと選択グリッパを区別。組立時間、保証、日本販売条件、同梱物、SDKアクセスは未確認を明示。実物でない図を公式写真と表示しない。中国語の焼込み文字がある動画をそのまま公開しない。
## Done 定義
「実装済み」「CI合格」「Design承認」「権利確認」「公開承認」の5状態を分ける。残タスク0と証跡リンクがない限り『納品完了・公開済み』としない。
