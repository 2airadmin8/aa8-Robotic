import { useState } from "react";

type Item = [string, string, string];
const challenges: Item[] = [
  ["01", "実機を使った学びが不足", "座学だけでなく、組立から制御までを一連の工程として学べる環境が求められています。"],
  ["02", "研究テーマへの接続が難しい", "ロボティクス、AI、制御など、複数分野を横断する教育・研究環境には多くの準備が必要です。"],
  ["03", "導入後の運用が不安", "利用人数、設置場所、開発環境、サポート範囲の事前整理が、継続的な活用につながります。"],
];
const uses: Item[] = [
  ["EDUCATION", "ロボット教育", "組立・構造理解・動作確認を通して、ハードウェアとソフトウェアを横断的に学ぶ授業へ。"],
  ["RESEARCH", "研究・実験", "人型ロボットを活用する研究テーマや実験計画に。適合性は導入前に個別確認します。"],
  ["DEVELOPMENT", "制御・開発演習", "プログラミングや制御の学習を、実機での動作確認につなげる実践的な演習へ。"],
];
const steps: Item[] = [["01","構造を知る","部品とロボットの構造を確認"],["02","組み立てる","手順に沿って機体を組立"],["03","接続・設定する","開発環境と機体を準備"],["04","動かして学ぶ","制御と検証を繰り返す"]];
const checks: Item[] = [["01","利用目的","授業・演習・研究など、想定する用途と到達目標"],["02","利用者・体制","対象学年、習熟度、利用人数、指導・管理体制"],["03","設置・保管環境","作業スペース、電源、ネットワーク、安全な保管場所"],["04","開発環境","開発用PC、ソフトウェア、接続・セキュリティ条件"]];
const faqs = [
  ["授業・研究のどちらにも利用できますか？","想定する学習内容や研究テーマによって必要な構成が異なります。用途を伺ったうえで、適合性と必要な準備をご案内します。"],
  ["導入前に何を確認すればよいですか？","利用目的、利用者の習熟度、設置・保管場所、開発用PCやネットワーク環境、運用体制などをご確認ください。"],
  ["価格・納期・保証について知りたいです。","価格、納期、保証条件は本ページでは未確認のため掲載していません。最新情報はお問い合わせ時にご確認ください。"],
  ["購入後のサポート内容は？","提供範囲や条件の確認が必要です。導入内容に応じたサポート可否を個別にご案内します。"],
];

function Placeholder({ name, label, className="" }: { name:string; label:string; className?:string }) {
  return <div className={`placeholder ${className}`} role="img" aria-label={`${label}、素材未提供`}><i/><b>{label}</b><small>{name}</small><em>素材未提供</em></div>;
}

const assetPaths: Record<string, {pc:string; sp?:string; alt:string}> = {
  "X2 EDU 製品画像": {pc:"/assets/x2-edu-product-official.jpg",alt:"メーカー資料に掲載されたX2 EDUの本体画像"},
  "教育・研究画像 01": {pc:"/assets/assembly-training.webp",sp:"/assets/assembly-training.webp",alt:"メーカー資料に掲載された組立実習の参考画像"},
  "教育・研究画像 02": {pc:"/assets/robot-education.webp",sp:"/assets/robot-education.webp",alt:"メーカー資料に掲載されたロボット教育の様子"},
  "教育・研究画像 03": {pc:"/assets/robot-competition.webp",sp:"/assets/robot-competition.webp",alt:"メーカー資料に掲載されたロボット競技の参考画像"},
  "X2 EDU 組立画像": {pc:"/assets/kit_pc.png",sp:"/assets/kit_sp.png",alt:"X2 EDU 部品キット構成の説明図。正式同梱内容は要確認"},
  "X2 EDU 仕様図": {pc:"/assets/spec-pc.png",sp:"/assets/spec_sp.png",alt:"メーカー資料に基づくX2 EDU主要仕様図。正式仕様は要確認"},
  "X2 EDU PC/SP図解": {pc:"/assets/robot-parts-business.webp",alt:"メーカー資料に掲載されたX2 EDU研究開発関連の参考画像"},
};
function ProductAsset({name,label,className=""}:{name:string;label:string;className?:string}) {
  const a=assetPaths[name];
  if (!a) return <Placeholder name={name} label={label} className={className}/>;
  return <picture className={`x2-asset ${className}`}>
    {a.sp && <source media="(max-width: 640px)" srcSet={a.sp}/>}
    <img src={a.pc} alt={a.alt} loading={name==="X2 EDU 製品画像"?"eager":"lazy"} decoding="async"/>
  </picture>;
}

function Heading({ n, en, title, lead, light=false }: { n:string; en:string; title:string; lead:string; light?:boolean }) {
  return <div className={`heading ${light?"light":""}`}><p className="eyebrow">{n} / {en}</p><h2>{title}</h2><p>{lead}</p></div>;
}
function Header(){const [open,setOpen]=useState(false);return <header><div className="header-in"><a className="brand" href="#top"><b>AGIBOT</b><span>X2 EDU</span></a><nav className={open?"open":""}><a href="#use">教育・研究用途</a><a href="#features">製品の特徴</a><a href="#specs">仕様</a><a href="#support">サポート・FAQ</a><a className="nav-cta" href="#contact">導入について相談</a></nav><button className="menu" onClick={()=>setOpen(!open)} aria-label="メニューを開閉"><i/><i/></button></div></header>}
const Arrow=()=> <span className="arrow">→</span>;

export default function App(){return <>
  <Header/><main id="top">
    <section className="hero"><div className="hero-copy"><p className="product-label">HUMANOID ROBOT FOR EDUCATION <b>AGIBOT X2 EDU</b></p><h1>組み立てる。<br/>動かす。考える。</h1><p className="hero-lead">人型ロボットを、教育・研究の現場へ。<br/>構造理解から制御・開発まで、実機を通して学ぶためのプラットフォーム。</p><div className="actions"><a className="button primary" href="#contact">資料を請求する <Arrow/></a><a className="button secondary" href="#contact">導入について相談する</a></div><small className="note">教育機関・研究機関向け／仕様・提供条件はお問い合わせください</small></div><div className="hero-visual"><span>X2</span><ProductAsset name="X2 EDU 製品画像" label="製品メインビジュアル"/></div></section>

    <section className="section" id="issues"><div className="container"><Heading n="02" en="CHALLENGES" title="教育・研究の現場に、こんな課題はありませんか？" lead="実機を活用した学びを始めるには、教材・環境・運用をまとめて考える必要があります。"/><div className="cards three">{challenges.map(([n,t,p])=><article key={n}><small>{n}</small><h3>{t}</h3><p>{p}</p></article>)}</div><div className="solution"><b>AGIBOT X2 EDU</b><p>組立から開発まで、実機を中心にした学習・研究環境を検討できます。</p></div></div></section>

    <section className="section gray" id="use"><div className="container"><Heading n="03" en="USE CASES" title="教育から研究・開発まで、学びを実機につなげる" lead="目的に合わせて、授業・演習・研究テーマへの活用を検討できます。"/><div className="use-grid">{uses.map(([tag,t,p],i)=><article key={t}><ProductAsset name={`教育・研究画像 0${i+1}`} label={`${t}イメージ`}/><div><small>{tag}</small><h3>{t}</h3><p>{p}</p></div></article>)}</div></div></section>

    <section className="section" id="assembly"><div className="container split"><div><Heading n="04" en="LEARNING PROCESS" title="組み立てる工程そのものが、学びになる" lead="完成品を動かすだけでなく、部品・構造・接続を理解しながら組み上げることで、ロボットへの理解を深めます。"/><div className="steps">{steps.map(([n,t,p])=><article key={n}><small>{n}</small><div><h3>{t}</h3><p>{p}</p></div></article>)}</div></div><div className="assembly-img"><ProductAsset name="X2 EDU 組立画像" label="組立キット・学習工程"/><p><b>ASSEMBLY KIT</b><span>同梱内容・工具・所要時間は要確認</span></p></div></div></section>

    <section className="section navy" id="features"><div className="container"><Heading n="05" en="FEATURES" title="教育・研究への適合性を、導入前に確認" lead="目的や環境に合うかを判断できるよう、確認すべきポイントを整理しています。" light/><div className="features"><article className="feature-main"><small>01 / HANDS-ON</small><h3>組立から学べる構成</h3><p>機体の構造を確認し、組立・接続・動作確認へと進む実践的な学習工程を想定しています。</p></article><div><article><small>02 / CONTROL</small><h3>制御学習への展開</h3><p>実機の動作を観察しながら、制御と検証のサイクルを学びます。</p></article><article><small>03 / RESEARCH</small><h3>研究テーマへの活用</h3><p>利用予定の研究内容に対する適合性は、事前の個別確認が必要です。</p></article></div></div><div className="feature-note"><b>導入検討時のポイント</b><p>対象者の習熟度、授業時間、研究目的、設備条件に応じてご相談ください。</p><a href="#check">導入前確認を見る <Arrow/></a></div></div></section>

    <section className="section specs" id="specs"><div className="container"><Heading n="06" en="HARDWARE & SPECIFICATIONS" title="ハードウェア・仕様" lead="下記項目は提供資料の確認後に確定します。未確認の数値や性能は掲載していません。" light/><div className="spec-grid"><ProductAsset name="X2 EDU 仕様図" label="製品仕様図・寸法図"/><div className="spec-table">{[["製品名","AGIBOT X2 EDU"],["外形寸法","提供資料を確認中"],["本体重量","提供資料を確認中"],["自由度・駆動方式","提供資料を確認中"],["電源・稼働条件","提供資料を確認中"],["通信・接続","提供資料を確認中"],["同梱物","構成により異なるため要確認"]].map(([k,v])=><p key={k}><span>{k}</span><b>{v}</b></p>)}<small>掲載内容は確認用です。正式な仕様は最新の製品資料をご確認ください。</small></div></div></div></section>

    <section className="section" id="development"><div className="container split"><div><Heading n="07" en="DEVELOPMENT" title="学びを深める、開発環境" lead="開発用PCやソフトウェア、接続方法など、利用開始までに必要な環境を確認します。"/><div className="dev-list">{[["プログラミング","対応言語・SDKは要確認"],["動作・制御","利用可能な制御範囲は要確認"],["実機検証","推奨環境・接続要件は要確認"]].map(([a,b])=><p key={a}><b>{a}</b><span>{b}</span></p>)}</div><a className="text-link" href="#contact">開発環境の詳細を問い合わせる <Arrow/></a></div><ProductAsset className="dev-img" name="X2 EDU PC/SP図解" label="開発環境・接続イメージ"/></div></section>

    <section className="section gray" id="check"><div className="container"><Heading n="08" en="BEFORE INTRODUCTION" title="導入前に、ご確認ください" lead="スムーズに活用を始めるため、用途と環境を事前に整理してください。"/><div className="cards four">{checks.map(([n,t,p])=><article key={n}><small>{n}</small><h3>{t}</h3><p>{p}</p></article>)}</div><div className="check-cta"><p><b>導入条件がまだ決まっていない場合もご相談ください。</b><span>用途を伺い、確認が必要な項目を一緒に整理します。</span></p><a className="button primary" href="#contact">導入相談を申し込む <Arrow/></a></div></div></section>

    <section className="section" id="support"><div className="container support-grid"><div><Heading n="09" en="SUPPORT & FAQ" title="導入後も、学びと研究を前へ" lead="購入後の提供内容・サポート範囲は、契約条件や導入構成によって異なるため、事前にご確認ください。"/><div className="support-box"><h3>サポートについて</h3><p>セットアップ、操作、保守など、必要な支援内容を導入前に確認します。</p><small>※提供可否・範囲・期間は要確認</small></div></div><div className="faq"><b>よくあるご質問</b>{faqs.map(([q,a],i)=><details key={q} open={i===0}><summary><span>Q</span>{q}</summary><p><span>A</span>{a}</p></details>)}</div></div></section>

    <section className="final-cta" id="contact"><div className="container"><p className="eyebrow">10 / CONTACT</p><h2>人型ロボットで、<br/>次の学びをはじめよう。</h2><p>AGIBOT X2 EDUの仕様・導入条件・活用方法について、お気軽にご相談ください。</p><div className="cta-actions"><a href="https://robotics.air-admin8.co.jp/contact.html?product=X2%20EDU&theme=materials"><span><small>製品情報を詳しく知りたい方</small><b>資料を請求する</b></span><Arrow/></a><a href="https://robotics.air-admin8.co.jp/contact.html?product=X2%20EDU&service=university&theme=education"><span><small>用途や環境から相談したい方</small><b>導入について相談する</b></span><Arrow/></a></div><small className="contact-note">※価格・納期・提供条件は正式確認後にご案内します。</small></div></section>
  </main><footer><a className="brand" href="#top"><b>AGIBOT</b><span>X2 EDU</span></a><p>AGIBOT X2 EDU 日本語製品ページ</p><small>掲載内容は確認用です。製品仕様・提供条件は正式資料をご確認ください。</small></footer>
</>}
