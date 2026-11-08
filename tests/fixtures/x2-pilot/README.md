# AGIBOT 灵犀 X2｜正式Factory隔離パイロット

- **入力正本**: 智元公式X2商品ページの2026-10-28 SingleFile保存版（Google Drive / 02_カタログ / X2.html）。SHA256はsource-contract.jsonに保管。
- **ProductID候補**: `agibot-x2-series`（既存の`agibot-x2-edu`と別。既存13商品を書き換えない）
- **対象**: 青春版・旗舰版の2バリアント、元表日本語公式36項目／9分類。
- **写真**: x2-series-hero.pngはユーザーが2026-11-09に確認したX2シリーズ**共通宣伝画像**。単一SKU画像と表示しない。追加の公式X2ページ抽出写真はバリアント判別未承認。
- **設計**: Figma G1 V3.2のPC Hero 33:2714・SP Hero 29:1657を設計参照。これはX2固有のデザイン正式承認を意味しない。
- **生成**: 既存 `scripts/product_factory.py` に追加した `--draft-product` だけを利用。例：
  `python scripts/product_factory.py generate --draft-product tests/fixtures/x2-pilot/product.json --mode preview --output _site/x2-pilot-preview.html`
- **安全**: プレビューはnoindex、releaseReady=false、既存13件への追加なし。候補モードによる公開先HTML生成は禁止。ページ公開・CRM書込・メール送信なし。
- **検証**: 旧Factory20 tests + X2固有6 tests。CIの同一HEAD上でPlaywright 1440/390/320を必須チェック。特にproduct/maker/source_page/serviceと35表行を確認。
- **未完了Gate**: X2専用Figma正式承認、Previewの実オンラインURL、既存Customer/PAI実登録E2E、CEO精確SHA承認、手動Pagesリリース。CIのPASSはこれらを代替しない。
- **正式Product Masterへの登録**: 既存ProductIDとの衝突と日本向け販売要件を審査した後に別途承認。現時点では新規SKUとして公開しない。
\n## 2026-11-09 日本向けメーカー正本の優先\n- 現行公式日本語ページ https://agibot.com/jp/products/X2 を日本語ページ仕様の優先ソースに採用。2機種 X2 / X2 Ultra、36項目・9分類。\n- 旧中国語SingleFile 35項目は歴史証拠として同じsource-contract.jsonに保持。自由度25→27、首0→2、片腕リーチ558→437mm、最大速度1.8/2→1.5 m/s 等の差分を明示。\n- 現行日本語表の映像出力は追加1項目。未検証の表記差はメーカー確認まで公開をHOLD。\n- X2独自Figmaは追加作成せず、CEO承認済み共通Figma製品ページテンプレートを参照。実HTMLのPC/SP差分QAは別Gate。\n