# X2 EDU Figma Make原版の継承・画像配置記録

- ソース：ユーザー提出 `製品ページ制作依頼.make` 内のReact/Vite画面。見出し、セクション、CSSの大枠を維持。
- PC/SP素材：Drive `02_データ-素材...` および既存HPウェブ画像パックより取得。画像自体の権利確認とは別。
- Hero `product_official.jpg`：メーカー資料抽出、X2 EDU本体。著作権許諾と型番整合の確認待ち。
- 教育・組立・競技・研究画像：HPの参考WebP素材。実際の納入事例として表示しない。
- 組立・仕様：`kit_pc.png` / `kit_sp.png` / `spec_pc.png` / `spec_sp.png`。
- 問い合わせ：テスト用 `contact@example.com` を廃止し、`https://robotics.air-admin8.co.jp/contact.html` に統一。
- 旧Figma専用Viteプラグイン・プレースホルダーtitleを除去し、標準Vite設定へ置換。
- メーカー権利・BOM・正式提供条件・実画面QAが未承認のため、本番公開は不可。

## ローカルプレビュー
`npm install && npm run build && npm run preview`

## Make原版からの最小差分
`src/App.tsx` で既存の画像プレースホルダーを `ProductAsset` に置換。`src/index.css` の最後に画像専用CSSを追記。既存ページセクションや主要スタイルは保持。
