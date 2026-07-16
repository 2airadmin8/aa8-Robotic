# AirAdmin8 Robotics 運用手順

## 1. 役割

- 事業責任者: 掲載方針、優先順位、公開可否の最終判断
- 商品担当: 仕様、価格、納期、SDK、保証、規制情報の確認
- 営業担当: 用途、案件進捗、事例公開範囲、問い合わせ対応
- 制作・開発: HTML、CSS、JavaScript、JSON、QA、公開

## 2. 製品を追加する

1. メーカー公式URLと正式製品名を確認
2. `data/products.json` に製品を追加
3. `products/<slug>.html` を作成
4. 製品ページに確認日、未確認項目、相談導線を記載
5. `data/seo-keywords.json` に独立した主キーワードを追加
6. `sitemap.xml` にCanonicalと同じURLを追加
7. メーカー、用途、資料、比較機能とのリンクを確認
8. GitHub Actionsがすべて成功した後に公開確認

### 製品情報で断定してはいけない項目

- 個別見積前の販売価格
- 在庫・最終納期
- SDKで制御可能な全範囲
- 保証・修理・交換条件
- 日本での独占販売権・正式代理権
- 技適、PSE、電池輸送など案件ごとに変わる条件

## 3. 価格・納期・仕様を更新する

- 情報源と確認日を記録
- 古い情報を削除せず、必要に応じて「確認中」「旧情報」と区別
- Web上の参考価格を正式見積価格として表示しない
- メーカー資料間で矛盾がある場合は、断定せず差異を記載
- 製品JSONと詳細ページの内容を同時に更新

## 4. 事例を追加・更新する

1. 顧客名、写真、ロゴ、見積書、コメントの公開許可を確認
2. `data/case-evidence.json` に案件を登録
3. 状態を `planning` / `in_progress` / `completed` / `archived` から選択
4. 証拠を次の4区分で登録
   - `confirmed`: 案件内で確認済み
   - `organized`: AirAdmin8が整理済み
   - `pending`: 正式確認中
   - `not_public`: 非掲載
5. 詳細ページを作成し、進行中案件には完了表現を使わない
6. 大学・企業による推奨表明ではないことを明記
7. SitemapとSEO管理を更新

## 5. SEOを更新する

- 主キーワードは1ページ1つ
- 同じ検索意図のページを量産しない
- Title、Description、H1、本文、FAQ、内部リンクを同じ目的に揃える
- `data/seo-keywords.json` を先に更新してから原稿を修正
- 新規ページは `sitemap.xml` とCanonicalを一致させる
- 公開後はSearch Consoleで表示回数、クリック、CTR、順位を確認

## 6. GA4を更新する

- イベント追加時は `assets/js/analytics-events.js` と `data/analytics-events.json` を同時更新
- 氏名、メール、電話、会社名、自由記述本文を送信しない
- 重要イベント候補
  - 比較表PDF保存
  - 比較結果から相談
  - チェックリストから相談
  - 問い合わせ確認画面
  - メールアプリ起動
  - メール本文コピー

## 7. 問い合わせ対応

- 現在のGitHub Pages版はメールアプリ起動方式
- 顧客の入力内容は現在の端末にのみ下書き保存
- GmailやCRMへ自動保存されない
- 受信後は顧客マスターへ次を登録
  - 流入ページ
  - 製品・メーカー
  - 用途
  - 相談区分
  - 予算・希望時期
  - 次回対応期限

## 8. 公開前確認

- GitHub Actionsがすべて成功
- スマートフォンで横スクロールがない
- メニュー、比較、Dialog、Footerが崩れていない
- リンク切れがない
- 問い合わせURLのパラメータが正しく引き継がれる
- 未確認情報を断定していない
- Sitemap、Canonical、robotsが一致
- GA4に個人情報を送信していない

## 9. 障害対応

### Workflowが赤い場合

1. 失敗した最初の検査名を確認
2. その検査より後の失敗は二次的な可能性が高い
3. ログに表示された `ERROR` / `SEARCH ERROR` / `CASE ERROR` を確認
4. 検査を無効化して通すのではなく、データと実装の不一致を修正
5. 修正後の最新コミットが緑になるまで公開完了と判断しない

### 画面が崩れた場合

1. iPhone Safariで再現URLを確認
2. キャッシュを疑う前にHTML構造を確認
3. 共通Header/Footer置換がDialog内部要素を誤認していないか確認
4. CSSの固定幅、`min-width`、長い英数字、表を確認
5. 修正後は該当ページだけでなくトップ・製品・支援・事例・問い合わせを確認

## 10. 正式ドメイン移行

`robotics.air-admin8.co.jp` へ移行する場合は一括で対応します。

- DNS・GitHub Pages Custom Domain設定
- `CNAME`追加
- 全Canonical更新
- Sitemap URL更新
- robots.txtのSitemap更新
- `llms.txt`更新
- Search Consoleで新プロパティ確認
- GA4のデータストリーム確認
- 旧GitHub Pages URLからの重複評価確認

部分的にドメインを変更するとCanonical不一致が発生するため、同一リリースで更新します。
