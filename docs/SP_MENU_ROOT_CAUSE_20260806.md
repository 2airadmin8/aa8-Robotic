# SPメニュー回帰の根因と恒久対策（2026-08-06）

## 根因

SPメニューのCSS自体は修正済みだったが、公開HTMLが固定された古いCSS URLを参照していたため、端末側で旧`shared-layout.css`が再利用された。

その結果、PR上のPlaywrightは最新ローカル成果物で成功しても、本番端末では旧CSSが残り、ボタン状態だけ変化してナビゲーションが表示されない状態が発生した。

## 恒久ルール

- 共通CSS、共通JS、faviconは手動日付ではなく内容ハッシュをURLへ付与する。
- Build成果物の全HTMLが現在のファイルハッシュを参照していることをCIで検証する。
- ハッシュ不一致、未付与、旧参照が1ページでもあればMerge／Pages Deployを停止する。
- SPメニューの完成判定は、実ブラウザ操作成功と本番SHA一致の両方を必須とする。

## 管理元

- HTML: `includes/site-header.html`
- CSS: `assets/css/shared-layout.css`
- JavaScript: `assets/js/site.js` / 公開用共通JS
- 実ブラウザテスト: `tests/header-navigation.spec.js`
- キャッシュ検証: `scripts/verify_asset_fingerprints.py`
