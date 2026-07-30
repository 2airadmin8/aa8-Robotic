#!/usr/bin/env python3
"""Generate AirAdmin8's original robot / Physical AI glossary and priority detail pages."""

from __future__ import annotations

import html
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"
BASE = "https://robotics.air-admin8.co.jp/"

# Original AirAdmin8 explanations. Terms overlap common industry vocabulary, but wording and structure are independent.
TERMS = [
    ("AIロボット", "AI Robot", "認識・判断・行動の一部にAIを使い、環境や対象物に応じて動作を変えられるロボット。", "基礎", "ai-robot"),
    ("フィジカルAI", "Physical AI", "現実世界の身体、センサー、環境との相互作用を前提に学習・推論するAIの考え方。", "基礎", "physical-ai"),
    ("ヒューマノイドロボット", "Humanoid Robot", "人に近い身体構造を持ち、人向けに設計された空間や道具を扱うことを目指すロボット。", "ロボット", "humanoid-robot"),
    ("四足ロボット", "Quadruped Robot", "4本脚で移動し、段差や不整地での巡検・計測・研究に使われるロボット。", "ロボット", None),
    ("ロボットアーム", "Robot Arm", "複数の関節を制御し、把持、組立、計測、実験操作などを行う機構。", "ロボット", None),
    ("協働ロボット", "Collaborative Robot", "人と同じ作業空間での利用を想定し、安全機能や操作性を重視したロボット。", "ロボット", None),
    ("AMR", "Autonomous Mobile Robot", "地図やセンサーを使い、固定レールなしで自律移動する搬送ロボット。", "ロボット", None),
    ("AGV", "Automated Guided Vehicle", "磁気テープやマーカーなど、あらかじめ定めた経路に沿って移動する搬送車。", "ロボット", None),
    ("サービスロボット", "Service Robot", "製造以外の分野で、人や設備を支援する目的で使われるロボット。", "ロボット", None),
    ("テレオペレーション", "Teleoperation", "離れた場所から人がロボットを操作し、作業やデータ収集を行う方式。", "操作", None),
    ("自律制御", "Autonomous Control", "センサー入力と内部判断に基づき、人の逐次操作なしで動作を決める制御。", "制御", None),
    ("モーションプランニング", "Motion Planning", "障害物や関節制約を考慮し、目的姿勢までの安全な動作経路を計算する技術。", "制御", None),
    ("逆運動学", "Inverse Kinematics", "手先などの目標位置から、必要な各関節角度を求める計算。", "制御", None),
    ("順運動学", "Forward Kinematics", "関節角度から手先や各部位の位置・姿勢を求める計算。", "制御", None),
    ("インピーダンス制御", "Impedance Control", "接触時の力と位置の関係を調整し、柔らかく安全な動作を実現する制御。", "制御", None),
    ("VLA", "Vision-Language-Action", "画像、言語指示、ロボット行動を一つのモデルで結び付けるアプローチ。", "AI", "vla"),
    ("VLM", "Vision-Language Model", "画像と文章を同時に理解し、説明、質問応答、認識支援を行うモデル。", "AI", None),
    ("LLM", "Large Language Model", "大量の文章から言語パターンを学び、生成や推論に使われる大規模モデル。", "AI", None),
    ("生成AI", "Generative AI", "文章、画像、音声、コード、動作候補など新しい内容を生成するAI。", "AI", None),
    ("マルチモーダルAI", "Multimodal AI", "文章、画像、音声、センサー値など複数形式の情報を統合して扱うAI。", "AI", None),
    ("機械学習", "Machine Learning", "明示的な全ルールを書かず、データから予測や判断の規則を学ぶ技術。", "AI", None),
    ("深層学習", "Deep Learning", "多層ニューラルネットワークを使い、複雑な特徴をデータから学ぶ手法。", "AI", None),
    ("強化学習", "Reinforcement Learning", "行動結果の報酬を手掛かりに、望ましい方策を試行錯誤で学ぶ手法。", "学習", "reinforcement-learning"),
    ("模倣学習", "Imitation Learning", "人や既存方策の実演データから、ロボットの行動を学習する方法。", "学習", "imitation-learning"),
    ("教師あり学習", "Supervised Learning", "入力と正解ラベルの組を使って予測モデルを学習する方法。", "学習", None),
    ("教師なし学習", "Unsupervised Learning", "正解ラベルなしのデータから、構造や類似性を見つける方法。", "学習", None),
    ("自己教師あり学習", "Self-Supervised Learning", "データ自身から学習課題を作り、大量の未ラベルデータを活用する方法。", "学習", None),
    ("ファインチューニング", "Fine-Tuning", "既存モデルを特定タスクや自社データに合わせて追加学習すること。", "学習", None),
    ("推論", "Inference", "学習済みモデルに新しい入力を与え、予測や行動候補を出す処理。", "AI", None),
    ("RAG", "Retrieval-Augmented Generation", "外部文書を検索して参照しながら、生成AIの回答精度を高める構成。", "AI", None),
    ("ROS", "Robot Operating System", "ロボット向けソフトウェア部品、通信、ツール群を提供する共通基盤。", "開発", None),
    ("ROS 2", "Robot Operating System 2", "分散通信、品質設定、セキュリティなどを強化した現行世代のROS。", "開発", "ros2"),
    ("SDK", "Software Development Kit", "ロボット機能を利用・拡張するためのライブラリ、仕様書、サンプル群。", "開発", "sdk"),
    ("API", "Application Programming Interface", "外部ソフトウェアから機能やデータを呼び出すための接続仕様。", "開発", "api"),
    ("ミドルウェア", "Middleware", "OSとアプリケーションの間で通信、データ変換、実行管理を支えるソフトウェア。", "開発", None),
    ("リアルタイム制御", "Real-Time Control", "決められた時間内に処理を完了し、遅延を抑えて動作を制御する考え方。", "制御", None),
    ("SLAM", "Simultaneous Localization and Mapping", "自己位置推定と周辺地図作成を同時に行う技術。", "認識", "slam"),
    ("自己位置推定", "Localization", "センサーや地図を使い、ロボットが現在位置と向きを推定する処理。", "認識", None),
    ("物体認識", "Object Recognition", "カメラ等から対象物の種類、位置、姿勢を推定する技術。", "認識", None),
    ("姿勢推定", "Pose Estimation", "人、物体、ロボットの位置と向き、関節状態などを推定する技術。", "認識", None),
    ("センサーフュージョン", "Sensor Fusion", "複数センサーの長所を組み合わせ、認識や推定の安定性を高める処理。", "認識", None),
    ("LiDAR", "Light Detection and Ranging", "レーザー光の反射時間から周囲までの距離を測るセンサー。", "センサー", "lidar"),
    ("RGB-Dカメラ", "RGB-D Camera", "カラー画像と奥行き情報を同時に取得できるカメラ。", "センサー", None),
    ("IMU", "Inertial Measurement Unit", "加速度と角速度を測り、姿勢や運動状態の推定に使うセンサー。", "センサー", None),
    ("力覚センサー", "Force/Torque Sensor", "接触時の力やトルクを測り、組立、把持、安全制御に使うセンサー。", "センサー", "force-sensor"),
    ("触覚センサー", "Tactile Sensor", "接触位置、圧力、滑りなどを検知し、繊細な把持に使うセンサー。", "センサー", "tactile-sensor"),
    ("ロボットハンド", "Robot Hand", "対象物をつかむ、押す、回すなどの操作を行う手先機構。", "機構", "robot-hand"),
    ("多指ハンド", "Multi-Finger Hand", "複数の指を個別制御し、人に近い把持や操作を目指すロボットハンド。", "機構", None),
    ("エンドエフェクタ", "End Effector", "アーム先端に取り付けるハンド、吸着機、工具などの作業装置。", "機構", None),
    ("自由度", "Degrees of Freedom", "ロボットが独立して動かせる軸や方向の数。", "機構", None),
    ("可搬重量", "Payload", "ロボットが仕様上保持・搬送できる対象物の最大重量。", "仕様", None),
    ("繰返し精度", "Repeatability", "同じ指令を繰り返したとき、同じ位置へ戻れる度合い。", "仕様", None),
    ("シミュレーション", "Simulation", "実機を動かす前に、仮想環境で動作、学習、安全性を検証する方法。", "開発", "simulation"),
    ("Sim-to-Real", "Simulation to Reality", "シミュレーションで学習・検証した内容を実機へ移す考え方と技術。", "開発", "sim-to-real"),
    ("デジタルツイン", "Digital Twin", "実設備やロボットの状態を仮想空間に対応付け、分析や予測に使う仕組み。", "開発", None),
    ("Isaac Sim", "NVIDIA Isaac Sim", "NVIDIA Omniverse上でロボットシミュレーションや合成データ生成を行う環境。", "開発", None),
    ("MuJoCo", "Multi-Joint dynamics with Contact", "接触を含むロボット力学の研究や強化学習で使われる物理シミュレータ。", "開発", None),
    ("Gazebo", "Gazebo Simulator", "ROS連携を含むロボットシミュレーションで広く使われる環境。", "開発", None),
    ("データ収集", "Data Collection", "学習、評価、再現性確認のためにセンサー値、画像、操作、結果を記録する工程。", "導入", "data-collection"),
    ("PoC", "Proof of Concept", "限定した範囲で技術成立性、効果、運用条件を確認する検証。", "導入", "poc"),
    ("KPI", "Key Performance Indicator", "PoCや導入の成否を判断するために事前に定める評価指標。", "導入", None),
    ("エッジAI", "Edge AI", "クラウドだけに依存せず、端末やロボット側でAI推論を実行する構成。", "導入", None),
    ("オンプレミス", "On-Premises", "社内設備や研究室内のサーバーでシステムを運用する方式。", "導入", None),
    ("技適", "Technical Regulations Conformity Certification", "日本で無線機能を使用する際に確認が必要になる電波法上の適合表示。", "法規", "giteki"),
    ("UN38.3", "UN Manual of Tests and Criteria 38.3", "リチウム電池の国際輸送で確認される安全試験要件。", "法規", "un38-3"),
]

DETAIL_SLUGS = {term[4] for term in TERMS if term[4]}


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def header(depth: int = 0) -> str:
    p = "../" * depth
    return f'''<header class="site-header"><div class="header-inner glossary-wrap">
<a class="brand" href="{p}index.html" aria-label="AirAdmin8 ロボティクス ホーム"><span class="brand-mark">A8</span><span>AirAdmin8 ロボティクス</span></a>
<nav aria-label="主要ナビゲーション"><a href="{p}products.html">製品</a><a href="{p}use-cases.html">用途</a><a href="{p}support.html">導入支援</a><a href="{p}glossary.html" aria-current="page">用語集</a></nav><span class="menu">メニュー</span></div></header>'''


def footer(depth: int = 0) -> str:
    p = "../" * depth
    return f'''<footer class="site-footer"><div class="glossary-wrap"><strong>AirAdmin8 ロボティクス</strong><p>AIロボット・フィジカルAIの選定、比較、導入、PoCを支援します。</p><p><a href="{p}products.html">製品を探す</a>　<a href="{p}support.html">導入支援</a>　<a href="{p}contact.html">相談する</a></p></div></footer>'''


def base_head(title: str, description: str, canonical: str, depth: int = 0, schema: dict | None = None) -> str:
    p = "../" * depth
    schema_html = f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>' if schema else ""
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(description)}"><link rel="canonical" href="{canonical}">
<link rel="stylesheet" href="{p}assets/css/glossary.css?v=20260731-1">{schema_html}</head><body>'''


def make_index() -> str:
    cards = []
    for jp, en, definition, category, slug in TERMS:
        link = f'<a class="term-link" href="glossary/{slug}.html">詳しく見る →</a>' if slug else ""
        cards.append(f'''<article class="term-card" id="term-{esc(slug or en.lower().replace(' ','-'))}" data-term="{esc(jp + ' ' + en + ' ' + category)}">
<h2>{esc(jp)}</h2><p class="term-en">{esc(en)}</p><p>{esc(definition)}</p><div class="term-meta"><span class="term-tag">{esc(category)}</span></div>{link}</article>''')
    defined_terms = [{"@type": "DefinedTerm", "name": t[0], "alternateName": t[1], "description": t[2]} for t in TERMS]
    schema = {"@context": "https://schema.org", "@type": "DefinedTermSet", "name": "ロボット・フィジカルAI用語集", "url": BASE + "glossary.html", "publisher": {"@type": "Organization", "name": "株式会社AirAdmin8"}, "hasDefinedTerm": defined_terms}
    script = """<script>const q=document.querySelector('#glossary-search');q.addEventListener('input',()=>{const v=q.value.trim().toLowerCase();document.querySelectorAll('.term-card').forEach(c=>{c.hidden=v&&!c.dataset.term.toLowerCase().includes(v)&&!c.textContent.toLowerCase().includes(v);});});</script>"""
    return base_head("ロボット・フィジカルAI用語集｜AirAdmin8 ロボティクス", "AIロボット、フィジカルAI、VLA、ROS 2、SDK、SLAM、センサー、PoC、技適、UN38.3まで、導入判断に役立つ65用語を独自解説。", BASE + "glossary.html", schema=schema) + header() + f'''<main><section class="glossary-hero"><div class="glossary-wrap"><p class="eyebrow">ROBOT & PHYSICAL AI GLOSSARY</p><h1>ロボット・フィジカルAI用語集</h1><p>研究・教育・企業導入の現場で使われる65用語を、単なる定義ではなく、ロボット選定・PoC・運用判断につながる視点で整理しました。</p></div></section>
<section class="glossary-tools"><div class="glossary-wrap"><label for="glossary-search">用語を検索</label><input id="glossary-search" class="glossary-search" type="search" placeholder="例：VLA、ROS 2、LiDAR、PoC"><div class="glossary-index"><a href="#term-ai-robot">AI</a><a href="#term-physical-ai">フィジカルAI</a><a href="#term-vla">VLA</a><a href="#term-ros2">ROS 2</a><a href="#term-sdk">SDK</a><a href="#term-slam">SLAM</a><a href="#term-poc">PoC</a></div></div></section>
<section class="glossary-section"><div class="glossary-wrap"><div class="glossary-grid">{''.join(cards)}</div></div></section></main>''' + footer() + script + "</body></html>"


def make_detail(term: tuple[str, str, str, str, str]) -> str:
    jp, en, definition, category, slug = term
    schema = {"@context": "https://schema.org", "@type": "DefinedTerm", "name": jp, "alternateName": en, "description": definition, "inDefinedTermSet": BASE + "glossary.html", "url": BASE + f"glossary/{slug}.html"}
    related = [t for t in TERMS if t[3] == category and t[4] and t[4] != slug][:5]
    links = "".join(f'<a href="{t[4]}.html">{esc(t[0])}</a>' for t in related) or '<a href="../glossary.html">用語集一覧へ</a>'
    importance = f"{jp}は、製品仕様だけでは判断しにくいロボット導入において、研究目的、データ、制御構成、運用条件を整理するための重要な概念です。"
    use = f"大学・研究機関では実験再現性や拡張性、企業PoCでは安全性、評価指標、既存システムとの接続条件を確認する際に、{jp}の理解が役立ちます。"
    checklist = ["目的と対象タスクを先に決める", "必要なセンサー・計算環境・SDKを確認する", "評価方法とデータ取得条件を定義する", "実機導入前にPoC範囲と安全条件を整理する"]
    return base_head(f"{jp}とは？ロボット導入での意味｜AirAdmin8 ロボティクス", f"{jp}（{en}）の意味、ロボット導入・研究で重要な理由、確認項目をAirAdmin8 ロボティクスが解説。", BASE + f"glossary/{slug}.html", depth=1, schema=schema) + header(1) + f'''<main><section class="glossary-hero"><div class="glossary-wrap"><p class="breadcrumb"><a href="../glossary.html">用語集</a> / {esc(jp)}</p><p class="eyebrow">{esc(category.upper())}</p><h1>{esc(jp)}とは？</h1><p>{esc(en)}</p></div></section><section class="glossary-detail"><div class="glossary-wrap glossary-detail-grid"><article class="glossary-copy"><p class="glossary-note">{esc(definition)}</p><h2>ロボット導入で重要な理由</h2><p>{esc(importance)}</p><h2>研究・PoCでの使われ方</h2><p>{esc(use)}</p><h2>導入前の確認項目</h2><ul>{''.join(f'<li>{esc(x)}</li>' for x in checklist)}</ul><h2>AirAdmin8の整理視点</h2><p>用語だけで判断せず、対象タスク、製品構成、納期、法規、データ取得、SDK、保守まで一つの導入条件として確認します。</p></article><aside class="glossary-side"><h2>関連用語</h2>{links}<a href="../glossary.html">65用語の一覧へ</a></aside></div></section></main>''' + footer(1) + "</body></html>"


def update_sitemap(urls: list[str]) -> None:
    path = OUTPUT / "sitemap.xml"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    today = date.today().isoformat()
    additions = "".join(f"\n  <url><loc>{url}</loc><lastmod>{today}</lastmod></url>" for url in urls if url not in text)
    text = text.replace("</urlset>", additions + "\n</urlset>")
    path.write_text(text, encoding="utf-8")


def generate_robot_ai_glossary(output: Path = OUTPUT) -> tuple[int, list[str]]:
    errors: list[str] = []
    glossary_dir = output / "glossary"
    glossary_dir.mkdir(parents=True, exist_ok=True)
    (output / "glossary.html").write_text(make_index(), encoding="utf-8")
    count = 1
    urls = [BASE + "glossary.html"]
    for term in TERMS:
        if not term[4]:
            continue
        path = glossary_dir / f"{term[4]}.html"
        path.write_text(make_detail(term), encoding="utf-8")
        count += 1
        urls.append(BASE + f"glossary/{term[4]}.html")
    update_sitemap(urls)
    if len(TERMS) != 65:
        errors.append(f"Glossary must contain 65 terms, found {len(TERMS)}")
    if count != 16:
        errors.append(f"Glossary must generate 16 pages, found {count}")
    for required in ("physical-ai", "vla", "ros2", "sdk", "poc", "giteki", "un38-3"):
        if required not in DETAIL_SLUGS:
            errors.append(f"Missing priority glossary detail: {required}")
    return count, errors


if __name__ == "__main__":
    generated, failures = generate_robot_ai_glossary()
    print(f"Generated {generated} glossary page(s).")
    raise SystemExit(1 if failures else 0)
