#!/usr/bin/env python3
"""Independent-device A2 source-to-Japanese technical fact QA, NOT human approval.

A separately authored, 37-row semantic reference is checked against a live
manufacturer HTML snapshot and each rendered Japanese value in both model
columns. This does not bypass independent human/CEO Production release gates.
"""
from __future__ import annotations
from datetime import datetime, timezone
from hashlib import sha256
import argparse
import json
import platform
from pathlib import Path
import sys
from maker_spec_watch import load_contract, fetch, parse_source, compare, norm

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "tests/fixtures/a2-factory"
# Independent bilingual acceptance baseline derived from official row labels,
# options, model cells and qualifiers. NOT imported from product.json's text.
# Format: parameter_id, exact English maker heading, accepted Japanese A2,
# optional A2-PRO override (otherwise the same verified wording).
REFERENCE = [
 ("立位寸法","Size (Standing)","820 × 440 × 570 mm"),
 ("伏臥寸法","Size (Lying Prone)","720 × 550 × 220 mm"),
 ("本体材質","Material","アルミ合金＋高強度エンジニアリングプラスチック"),
 ("電池除外重量","Weight (without battery)","約35 kg"),
 ("電池装着重量","Weight (with battery)","約42 kg"),
 ("関節自由度","Degrees of Freedom (Joint Motors)","12 DoF"),
 ("関節軸受","Joint Bearings","産業用クロスローラーベアリング（高精度・高荷重対応）"),
 ("関節モーター","Joint Motors","低慣性・高速インナーロータPMSM（応答性・放熱性を強化）"),
 ("最大関節トルク","Max Joint Torque","約180 N·m"),
 ("関節可動域","Range of Motion","胴体：−58～58°／大腿：−134～180°・−89～225°／下腿：−158～−30°"),
 ("電源電圧","Supply Voltage","50.4 V"),
 ("関節エンコーダ","Joint Encoder","デュアルエンコーダ"),
 ("冷却方式","Cooling System","部分空冷"),
 ("電源構成","Power Supply","2スロット・デュアルバッテリー"),
 ("バッテリー容量","Battery Capacity","1本9,000 mAh（453.6 Wh）／2本合計18,000 mAh（907.2 Wh）"),
 ("無線通信","Wi-Fi 6, Bluetooth 5.2","Wi-Fi 6／Bluetooth 5.2 対応"),
 ("スピーカー","Speaker","搭載"),
 ("マイク","Microphone","マイクアレイ"),
 ("前照灯","Front Light","搭載"),
 ("ワイヤレスベクトル追従モジュール","Wireless vector follow module","オプション","拡張構成で搭載"),
 ("GPS","GPS","オプション","拡張構成で搭載"),
 ("4G通信","4G","オプション","拡張構成で搭載"),
 ("センサー構成","Sensor","LiDAR ×1＋HDカメラ ×1","LiDAR ×2＋HDカメラ ×1"),
 ("制御・演算","Control & Compute","標準：高性能8コアCPU（本体制御）＋Intel Core i7（ユーザー開発）",
  "標準：高性能8コアCPU（本体制御）＋Intel Core i7（ユーザー開発）／高演算能力拡張Dockはオプション"),
 ("外部インターフェース","External Interfaces","RS485×2／CAN×2／GbE×2／USB3.0 Type-C（8コアCPU側）×2＋（i7側）×2／12V・24V・BAT出力"),
 ("動作温度","Operating Temperature","−20～55°C"),
 ("歩行持続時間・距離","Battery Life","無積載：5時間超／約20 km。25 kg積載：3時間超／約12.5 km（メーカー試験条件）"),
 ("最大立位静荷重","Max Standing Load","約100 kg（歩行積載ではない）"),
 ("連続歩行積載","Continuous Walking Load","約25 kg（理想条件では約35 kgに達する場合あり。通常保証値ではない）"),
 ("登坂能力","Slope Walking Capability","約45°"),
 ("階段・段差","Stair Climbing Capability","最大段差高 約30 cm"),
 ("最大乗越え高さ","Max Climb Height","約0.5～1 m"),
 ("走行速度","Speed","0～3.7 m/s（最高約5 m/s）"),
 ("防護等級","Ingress Protection Rating","IP56","IP56～IP67（主要部品はIP67）"),
 ("スマートOTA更新","Smart OTA Upgrade","継続アップデート"),
 ("二次開発","Secondary Development","対応（SDK／ROS 2具体条件は要確認）"),
 ("保証期間","Warranty","12か月（日本向け条件・窓口は要確認）"),
]
# An exact frozen manufacturer page hash is required for independently signed
# machine fact evidence. Manufacturer revisions require a new independent review.
FROZEN_OFFICIAL_SOURCE_SHA256 = "5030d11181e572a5427fbf3270fde32c7a2d132a1841d7fa1265320bb5aef489"

EXPECTED_GROUPS = (
 ("Mechanical Parameters",10),
 ("Electrical Characteristics",15),
 ("Performance Metrics",9),
 ("Other",3),
)
assert len(REFERENCE)==37 and sum(n for _,n in EXPECTED_GROUPS)==37
assert len({r[0] for r in REFERENCE})==37

def evaluate(contract:dict, product:dict, parsed:dict, source_digest:str,
             *, enforce_live_hash:bool=False)->dict:
    """Checks all model cells against a separately authored bilingual baseline."""
    issues=[]
    if enforce_live_hash and source_digest!=FROZEN_OFFICIAL_SOURCE_SHA256:
        issues.append("source snapshot changed: independent fact approval requires a new official source audit")
    if parsed["models"]!=["A2","A2-PRO"]:
        issues.append("wrong maker model columns")
    counts=[(g["name"],len(g["rows"])) for g in parsed["categories"]]
    if counts!=list(EXPECTED_GROUPS):
        issues.append("manufacturer categories/counts changed")
    try:
        drift=compare(parsed,contract)
        if drift:
            issues.append("manufacturer raw cells changed: "+json.dumps(drift,ensure_ascii=False))
    except (KeyError,ValueError,TypeError) as e:
        issues.append("manufacturer contract diverges: "+str(e))
    actual=[r for g in parsed["categories"] for r in g["rows"]]
    frozen=[r for g in contract["categories"] for r in g["rows"]]
    screen=product["pageFactory"]["specifications"]
    if not(len(actual)==len(frozen)==len(screen)==37):
        issues.append("37 rows not retained")
    evidence=[]
    for i,entry in enumerate(REFERENCE):
        if i>=min(len(actual),len(frozen),len(screen)):
            break
        pid,en,ja,*pro_override=entry
        jp={"A2":ja,"A2-PRO":(pro_override[0] if pro_override else ja)}
        a,f,p=actual[i],frozen[i],screen[i]
        if a["source_label"]!=en or f.get("source_label")!=en or f.get("id")!=pid or p.get("parameter")!=pid:
            issues.append(f"row identity {i+1}/{pid}")
        if p.get("sourceUrl")!="https://www.unitree.com/A2/":
            issues.append(f"untrusted display evidence URL: {pid}")
        expected_value=(jp["A2"] if jp["A2"]==jp["A2-PRO"]
                        else "A2："+jp["A2"]+"／A2-PRO："+jp["A2-PRO"])
        if p.get("value")!=expected_value:
            issues.append(f"legacy text value differs from verified model cells: {pid}")
        for model in ("A2","A2-PRO"):
            raw=a["models"].get(model)
            proposed=p.get("models",{}).get(model)
            recorded=f.get("approved_display",{}).get(model)
            status="TECH_SEMANTIC_MATCH" if proposed==jp[model] and recorded==jp[model] else "FAIL"
            if status=="FAIL":
                issues.append(f"Japanese semantic mismatch: {pid}/{model}; expected={jp[model]!r} got={proposed!r}")
            evidence.append({
                "row":i+1,"parameter_id":pid,"model":model,
                "official_heading":en,"official_raw_cell":raw,
                "japanese_display":proposed,
                "independent_expected_ja":jp[model],
                "technical_semantic_status":status,
                "official_source":"https://www.unitree.com/A2/",
            })
    if len(evidence)!=74:
        issues.append(f"not 74 Japanese cells: {len(evidence)}")
    return {
        "status":"TECH_SEMANTIC_QA_PASS" if not issues else "TECH_SEMANTIC_QA_HOLD",
        "maker":"Unitree","sku":"unitree-a2",
        "source_sha256":source_digest,
        "checked_at":datetime.now(timezone.utc).isoformat(),
        "models":["A2","A2-PRO"],"row_count":37,
        "cells_checked":len(evidence),"errors":issues,
        "execution_host":platform.node(),
        "technical_reference":"separately authored 37-row bilingual acceptance baseline",
        "independent_human_review":"NOT_ATTESTED",
        "production_release":"HOLD",
        "evidence":evidence,
    }

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-file",type=Path,default=None)
    ap.add_argument("--output",type=Path,default=None)
    args=ap.parse_args()
    c=load_contract(BASE/"maker-live-contract.json")
    p=json.loads((BASE/"product.json").read_text("utf-8"))
    blob=args.source_file.read_bytes() if args.source_file else fetch(c["source_url"],contract=c)
    parsed=parse_source(blob,c)
    report=evaluate(c,p,parsed,sha256(blob).hexdigest(),enforce_live_hash=True)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n","utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="evidence"},ensure_ascii=False))
    return 0 if report["status"]=="TECH_SEMANTIC_QA_PASS" else 2

if __name__=="__main__":
    sys.exit(main())
