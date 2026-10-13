import { useState } from "react";

type Item = [string, string, string];
const challenges: Item[] = [
  ["01", "実機で学べる教材が少ない", "組立・配線・制御まで、実機に触れながら学べる環境が求められています。"],
  ["02", "実機教材の導入・運用負担", "機材の準備、部品管理、教材や実習環境の整備が課題です。"],
  ["03", "ソフトだけでは実践力が不足", "プログラムの実行結果をロボットの動きで確かめる機会が必要です。"],
  ["04", "導入後のサポートが不安", "運用・安全管理・保守の条件を、導入前に確認する必要があります。"],
];
const uses: Item[] = [
  ["EDUCATION", "教育・授業", "機体構造、組立、動作調整などを実機で学ぶ授業・実習に。"],
  ["RESEARCH", "研究・開発", "AI・制御・ロボティクスの研究テーマや実証に。"],
  ["COMPETITION", "ロボット競技", "競技・演習を通した動作制御とプログラミングの検証に。"],
  ["COLLABORATION", "産学連携", "企業と教育機関による共同研究・実証・人材育成に。"],
];
const steps: Item[] = [["01","構造を知る","部品とロボットの構造を確認"],["02","組み立てる","手順に沿って機体を組立"],["03","接続・設定する","開発環境と機体を準備"],["04","動かして学ぶ","制御と検証を繰り返す"]];
const checks: Item[] = [["01","利用目的","授業・演習・研究など、想定する用途と到達目標"],["02","利用者・体制","対象学年、習熟度、利用人数、指導・管理体制"],["03","設置・保管環境","作業スペース、電源、ネットワーク、安全な保管場所"],["04","開発環境","開発用PC、ソフトウェア、接続・セキュリティ条件"]];
const faqs = [
  ["組立にはどのくらい時間がかかりますか？", "参加人数、経験、作業環境により異なります。実習計画に合わせてご確認ください。"],
  ["プログラミング初心者でも使えますか？", "組立・構造理解から学習できます。ROS2開発にはLinuxやプログラミングの基礎知識が役立ちます。"],
  ["保証期間はどのくらいですか？", "保証期間・対象範囲はメーカーおよび販売条件を確認し、お見積り時にご案内します。"],
  ["研究用途でのカスタマイズは可能ですか？", "ソフトウェア二次開発や機能拡張を想定しています。具体的な対応範囲は事前確認が必要です。"],
];

function Placeholder({ name, label, className="" }: { name:string; label:string; className?:string }) {
  return <div className={`placeholder ${className}`} role="img" aria-label={`${label}、素材未提供`}><i/><b>{label}</b><small>{name}</small><em>素材未提供</em></div>;
}

const assetPaths: Record<string, {pc:string; sp?:string; alt:string}> = {
  "X2 EDU 製品画像": {pc:"/assets/x2-edu-body-clean.png",alt:"X2 EDU組立型ヒューマノイドロボットの本体"},
  "教育・研究画像 01": {pc:"/assets/assembly-training.webp",sp:"/assets/assembly-training.webp",alt:"メーカー資料に掲載された組立実習の参考画像"},
  "教育・研究画像 02": {pc:"/assets/robot-education.webp",sp:"/assets/robot-education.webp",alt:"メーカー資料に掲載されたロボット教育の様子"},
  "教育・研究画像 03": {pc:"/assets/robot-competition.webp",sp:"/assets/robot-competition.webp",alt:"メーカー資料に掲載されたロボット競技の参考画像"},
  "教育・研究画像 04": {pc:"/assets/robot-parts-business.webp",alt:"研究開発・産学連携の参考画像"},
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
    <section className="hero"><div className="hero-copy"><p className="product-label">HUMANOID ROBOT FOR EDUCATION <b>AGIBOT X2 EDU</b></p><h1>X2 EDU<br/><span className="hero-tagline">つくる・動かす・学ぶ</span></h1><p className="hero-lead">次世代のヒューマノイド教育プラットフォーム。<br/>組立・制御・ソフトウェア開発を、実機を通して学べます。</p><div className="actions"><a className="button primary" href="#contact">資料を請求する <Arrow/></a><a className="button secondary" href="#contact">導入について相談する</a></div><small className="note">教育機関・研究機関向け／仕様・提供条件はお問い合わせください</small></div><div className="hero-visual"><span>X2</span><ProductAsset name="X2 EDU 製品画像" label="製品メインビジュアル"/></div></section>

    <section className="section" id="overview"><div className="container overview-grid"><div><Heading n="01" en="ABOUT X2 EDU" title="組み立てて、動かして、開発できる。" lead="教育・研究向けの組立型ヒューマノイドロボット。ロボット工学・AI・制御を実機で学ぶプラットフォームです。"/><ProductAsset name="X2 EDU 製品画像" label="X2 EDU 機体"/></div><div className="overview-benefits">{[["実機で学ぶ実践性","組立から動作確認まで、実機を使って学べます。"],["自ら組み立てて理解する","関節・構造・配線の仕組みを理解できます。"],["ROS2で開発する","ROS2 SDKを用いた制御・ソフトウェア開発に。"],["研究・競技へ応用する","目的に応じた検証・拡張を検討できます。"]].map(([t,p])=><article key={t}><h3>{t}</h3><p>{p}</p></article>)}</div></div></section>
    <section className="section" id="issues"><div className="container"><Heading n="02" en="CHALLENGES" title="教育・研究の現場に、こんな課題はありませんか？" lead="実機を活用した学びを始めるには、教材・環境・運用をまとめて考える必要があります。"/><div className="cards four">{challenges.map(([n,t,p])=><article key={n}><small>{n}</small><h3>{t}</h3><p>{p}</p></article>)}</div><div className="solution"><b>AGIBOT X2 EDU</b><p>組立から開発まで、実機を中心にした学習・研究環境を検討できます。</p></div></div></section>

    <section className="section gray" id="use"><div className="container"><Heading n="03" en="USE CASES" title="教育から研究・開発まで、学びを実機につなげる" lead="目的に合わせて、授業・演習・研究テーマへの活用を検討できます。"/><div className="use-grid">{uses.map(([tag,t,p],i)=><article key={t}><ProductAsset name={`教育・研究画像 0${i+1}`} label={`${t}イメージ`}/><div><small>{tag}</small><h3>{t}</h3><p>{p}</p></div></article>)}</div></div></section>

    <section className="section" id="assembly"><div className="container split"><div><Heading n="04" en="LEARNING PROCESS" title="組み立てる工程そのものが、学びになる" lead="完成品を動かすだけでなく、部品・構造・接続を理解しながら組み上げることで、ロボットへの理解を深めます。"/><div className="steps">{steps.map(([n,t,p])=><article key={n}><small>{n}</small><div><h3>{t}</h3><p>{p}</p></div></article>)}</div></div><div className="assembly-img"><ProductAsset name="X2 EDU 組立画像" label="組立キット・学習工程"/><p><b>ASSEMBLY KIT</b><span>同梱内容・工具・所要時間は要確認</span></p></div></div></section>

    <section className="section navy" id="features"><div className="container"><Heading n="05" en="FEATURES" title="X2 EDUの主な特長" lead="教育・研究に必要な組立・制御・開発を、ひとつの機体で学ぶプラットフォーム。" light/><div className="features-five">{[["フルスタック開発","ハード・ソフト・制御、ROS2・DDSを学習。"],["X2シリーズの本体","29自由度の構造を使った組立・調整実習。"],["柔軟な拡張性","センサーや計算モジュールの追加を検討。"],["組立・開発資料","メーカー提供の資料を使って学習。"],["教育現場での運用","安全管理・保守・サポート条件を確認。"]].map(([t,p],i)=><article key={t}><span>{String(i+1).padStart(2,"0")}</span><h3>{t}</h3><p>{p}</p></article>)}</div></div></section>


    <section className="section specs" id="specs"><div className="container"><Heading n="06" en="HARDWARE & SPECIFICATIONS" title="ハードウェア・仕様" lead="下記項目は提供資料の確認後に確定します。未確認の数値や性能は掲載していません。" light/><div className="spec-grid"><ProductAsset name="X2 EDU 仕様図" label="製品仕様図・寸法図"/><div className="spec-table">{[["製品名","AGIBOT X2 EDU"],["外形寸法","提供資料を確認中"],["本体重量","提供資料を確認中"],["自由度・駆動方式","提供資料を確認中"],["電源・稼働条件","提供資料を確認中"],["通信・接続","提供資料を確認中"],["同梱物","構成により異なるため要確認"]].map(([k,v])=><p key={k}><span>{k}</span><b>{v}</b></p>)}<small>掲載内容は確認用です。正式な仕様は最新の製品資料をご確認ください。</small></div></div></div></section>

    <section className="section" id="development"><div className="container split"><div><Heading n="07" en="DEVELOPMENT" title="ROS2を中心とした開発環境" lead="開発用PCやソフトウェア、接続方法など、利用開始までに必要な環境を確認します。"/><div className="dev-list">{[["開発用PC","Linux等の環境を準備"],["ROS2 SDK","制御プログラムを開発"],["シミュレーション","MuJoCo等で事前検証"],["実機制御","X2 EDUで動作確認"],["応用開発","AI・認識・運動制御へ展開"]].map(([a,b])=><p key={a}><b>{a}</b><span>{b}</span></p>)}</div><a className="text-link" href="#contact">開発環境の詳細を問い合わせる <Arrow/></a></div><ProductAsset className="dev-img" name="X2 EDU PC/SP図解" label="開発環境・接続イメージ"/></div></section>

    <section className="section gray" id="check"><div className="container"><Heading n="08" en="BEFORE INTRODUCTION" title="導入前に、ご確認ください" lead="スムーズに活用を始めるため、用途と環境を事前に整理してください。"/><div className="cards four">{checks.map(([n,t,p])=><article key={n}><small>{n}</small><h3>{t}</h3><p>{p}</p></article>)}</div><div className="check-cta"><p><b>導入条件がまだ決まっていない場合もご相談ください。</b><span>用途を伺い、確認が必要な項目を一緒に整理します。</span></p><a className="button primary" href="#contact">導入相談を申し込む <Arrow/></a></div></div></section>

    <section className="section gray" id="purchase-flow"><div className="container"><Heading n="09" en="INTRODUCTION FLOW" title="購入後の流れ（学習・開発・運用まで）" lead="納品から授業・研究での活用まで、6つのステップで進めます。"/><div className="purchase-flow">{[["相談・見積","利用目的を確認し、構成をご提案。"],["ご発注","仕様・条件を確定してご契約。"],["納品","ご注文のキット一式をお届け。"],["組立・調整","組立・キャリブレーションを実施。"],["学習・開発","授業・実習・研究に活用。"],["運用・サポート","技術支援・保守条件を確認。"]].map(([t,p],i)=><article key={t}><span>{String(i+1).padStart(2,"0")}</span><h3>{t}</h3><p>{p}</p></article>)}</div><p className="purchase-note">※組立・調整・運用は原則お客様が実施。技術支援・トレーニングは提供可否と条件をご相談ください。</p></div></section>
    <section className="section" id="support"><div className="container support-grid"><div><Heading n="10" en="SUPPORT & FAQ" title="よくある質問・サポート" lead="購入後の提供内容・サポート範囲は、契約条件や導入構成によって異なるため、事前にご確認ください。"/><div className="support-box"><h3>サポートについて</h3><p>セットアップ、操作、保守など、必要な支援内容を導入前に確認します。</p><small>※提供可否・範囲・期間は要確認</small></div></div><div className="faq"><b>よくあるご質問</b>{faqs.map(([q,a],i)=><details key={q} open={i===0}><summary><span>Q</span>{q}</summary><p><span>A</span>{a}</p></details>)}</div></div></section>

    <section className="final-cta" id="contact"><div className="container"><p className="eyebrow">10 / CONTACT</p><h2>X2 EDUで、<br/>未来の人材を育てませんか？</h2><p>AGIBOT X2 EDUの仕様・導入条件・活用方法について、お気軽にご相談ください。</p><div className="cta-actions"><a href="https://robotics.air-admin8.co.jp/contact.html?product=X2%20EDU&theme=materials"><span><small>製品情報を詳しく知りたい方</small><b>資料を請求する</b></span><Arrow/></a><a href="https://robotics.air-admin8.co.jp/contact.html?product=X2%20EDU&service=university&theme=education"><span><small>用途や環境から相談したい方</small><b>導入について相談する</b></span><Arrow/></a></div><small className="contact-note">※価格・納期・提供条件は正式確認後にご案内します。</small></div></section>
  </main><footer><a className="brand" href="#top"><b>AGIBOT</b><span>X2 EDU</span></a><p>AGIBOT X2 EDU 日本語製品ページ</p><small>掲載内容は確認用です。製品仕様・提供条件は正式資料をご確認ください。</small></footer>
</>}
