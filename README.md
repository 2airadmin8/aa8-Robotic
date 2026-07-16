# AirAdmin8 Robotics

株式会社AirAdmin8のロボティクス事業向け公式サイトです。
旧サイトとは完全に分離し、GitHub Pagesで静的配信します。

## 公開サイト

- 現在: https://2airadmin8.github.io/aa8-Robotic/
- 将来候補: https://robotics.air-admin8.co.jp/

## サイトの目的

- 大学・研究機関、製造、物流向けAIロボットの比較・選定
- 正式見積、大学購買、二社見積、PoC、初期導入の支援
- SDK、ROS、OSS、VLA・模倣学習資料の整理
- 製品、用途、支援、事例、問い合わせを一つの導線で接続

## 技術構成

- 静的HTML / CSS / JavaScript
- 製品データ: `data/products.json`
- SEO管理: `data/seo-keywords.json`
- GA4イベント管理: `data/analytics-events.json`
- 事例証拠管理: `data/case-evidence.json`
- Search Console準備: `data/search-console-readiness.json`
- ビルド: `scripts/build_site.py`
- 公開: GitHub Actions + GitHub Pages

## 主要ページ

- `index.html` — トップ
- `products.html` — 製品比較
- `use-cases.html` — 用途から探す
- `support.html` — 導入支援
- `cases.html` — 事例・支援実績
- `resources.html` — SDK・資料
- `checklist.html` — 導入前チェック
- `contact.html` — 製品・導入相談
- `about.html` — 会社情報

## 公開前の自動検査

GitHub Actionsで次を確認します。

1. JavaScript構文
2. SEO主キーワードの重複・対象ページ
3. GA4イベント定義と実装の一致
4. 事例の進捗・証拠区分・公開注意
5. Sitemap・Canonical・robotsの一致
6. サイトビルドとQAレポート生成

## 更新時の原則

- 未確認の仕様、価格、納期、保証、販売権を断定しない
- メーカー公式情報とAirAdmin8の整理内容を分ける
- 進行中案件を納品・導入完了事例として掲載しない
- 個人情報、非公開価格、大学内部資料をGitHubへ保存しない
- 1ページにつき主キーワードは原則1つ
- 製品追加時は詳細ページ、製品JSON、Sitemap、SEO管理を同時更新する

詳細な手順は [`docs/OPERATIONS.md`](docs/OPERATIONS.md) を参照してください。
