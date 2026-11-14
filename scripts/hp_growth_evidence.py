#!/usr/bin/env python3
"""P2: read-only GSC + Inquiry aggregate -> max 3 evidence-based candidates.

Only consumes safe aggregate exports. Never connects CRM, sends emails, writes
Products/HTML, deploys, or creates GitHub issues.
"""
from __future__ import annotations
import argparse
from datetime import date
import json
from pathlib import Path
import re
from urllib.parse import urlsplit


SOURCE_GSC = "1VTLnGjyld_pNWBad-gJcPNqGy0jUnrDKiiU18S6OgbM"
SOURCE_INQUIRY = "1dgoeLCBJVE0CXBGgizUwA-ozrRVvJw6Ng9gfGN0h8wI"
SOURCE_HOST = "robotics.air-admin8.co.jp"


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError("GROWTH_HOLD: " + message)


def integer(value, what: str) -> int:
    require(type(value) is int and value >= 0, "nonnegative count expected for " + what)
    return value


def inspect(snapshot: dict) -> dict:
    require(snapshot.get("schema") == "aa8-hp-gsc-inquiry-aggregate-v1",
            "unknown aggregate schema")
    s = snapshot.get("sources") or {}
    require(s.get("gscId") == SOURCE_GSC and s.get("inquiryId") == SOURCE_INQUIRY,
            "unverified source ids")
    require(s.get("gscSyncStatus") == "SUCCESS", "GSC sync failed")
    date_end = date.fromisoformat(s["gscLastEndDate"])
    collected = date.fromisoformat(snapshot["collectedAt"])
    require(0 <= (collected - date_end).days <= 7, "stale or future GSC period")
    periods = snapshot["periods"]
    require(len(periods) == 2 and periods[0]["name"] == "current"
            and periods[1]["name"] == "previous", "two 7-day windows required")
    for p in periods:
        require((date.fromisoformat(p["to"]) -
                 date.fromisoformat(p["from"])).days == 6, "not a 7-day window")
    require(date.fromisoformat(periods[0]["to"]) == date_end,
            "current window not latest")
    require((date.fromisoformat(periods[0]["from"]) -
             date.fromisoformat(periods[1]["to"])).days == 1,
            "two periods must be contiguous")
    weekly = snapshot["weekly"]
    for period in ("current", "previous"):
        require(integer(weekly[period]["days"], period + " days") == 7,
                "incomplete daily data")
        for col in ("clicks", "impressions"):
            integer(weekly[period][col], period + col)
    lead = snapshot["inquiry"]
    total = integer(lead["total"], "inquiries")
    for key in ("withSourceProduct", "withSourceService",
                "withUtmSource", "withProduct", "withNotifiedAt"):
        require(integer(lead[key], key) <= total, "bad coverage count: " + key)
    for kind in ("pages", "queries"):
        require(len(snapshot[kind]) <= 50, "too many aggregate data rows")
        for item in snapshot[kind]:
            for key in ("current", "previous"):
                for col in ("clicks", "impressions"):
                    integer(item[key][col], kind + ":" + col)
            if kind == "pages":
                u = urlsplit(item["url"])
                require(u.scheme == "https" and u.netloc == SOURCE_HOST
                        and not u.query and not u.fragment, "invalid official page URL")
            else:
                require(len(item.get("query", "")) <= 120, "excessive query")
    forbidden = ("email", "phone", "organization", "customerName", "message",
                 "submission_token", "ga_client_id", "client_id")
    serialized = json.dumps(snapshot, ensure_ascii=False).lower()
    require(not any('"' + key + '"' in serialized for key in forbidden),
            "PII fields in aggregate snapshot")
    return snapshot


def candidate(kind: str, priority: str, title: str, facts: dict,
              action: str, outcome: str, no_go: str) -> dict:
    return {"type": kind, "priority": priority, "title": title,
            "evidence": facts, "proposed_action": action,
            "success_measure": outcome, "prohibited": no_go,
            "status": "PROPOSAL_ONLY_NO_PRODUCTION_WRITE"}


def propose(snapshot: dict) -> dict:
    snap = inspect(snapshot)
    source = snap["sources"]
    current, previous = snap["weekly"]["current"], snap["weekly"]["previous"]
    inquiries = snap["inquiry"]
    plans = []

    if inquiries["total"] >= 5 and inquiries["withSourceProduct"] * 2 < inquiries["total"]:
        plans.append(candidate(
            "ATTRIBUTION_EVIDENCE_GAP", "P1",
            "咨询来源归因不完整：先补验证，不改正式CRM",
            {"inquiryRecords": inquiries["total"],
             "hasSourceProduct": inquiries["withSourceProduct"],
             "hasSourceService": inquiries["withSourceService"],
             "hasUtmSource": inquiries["withUtmSource"],
             "source": f"Google Sheets Inquiry Master {SOURCE_INQUIRY}",
             "caution": "包含测试/非有效线索，不能算真实客户成交转化"},
            "只读核查正式产品CTA→contact预填与Inquiry Master字段映射；提交隔离回归和差异清单",
            "下一周新增有效来源记录的字段完整率提升，测试记录单独统计",
            "禁止直接写CRM、猜填缺失来源、把全部记录当有效商机"))
    product_pages = [p for p in snap["pages"]
                     if urlsplit(p["url"]).path.startswith("/products/")]
    eligible = [p for p in product_pages
                if p["current"]["impressions"] >= 15
                and p["current"]["clicks"] == 0]
    if eligible:
        p = max(eligible, key=lambda x: x["current"]["impressions"])
        plans.append(candidate(
            "PRODUCT_HIGH_IMPRESSION_ZERO_CLICK", "P2",
            "高曝光但零点击的产品页：审核标题和搜索意图",
            {"url": p["url"], "current7d": p["current"],
             "previous7d": p["previous"],
             "source": f"GSC Master 03_Page {SOURCE_GSC}",
             "note": "仅建议人工审核，不证明排名或文案是原因"},
            "核对搜索Query、title/description与真实研究选型价值，提出最小文案候选PR",
            "未来完整7日的展示和点击变化；低样本不能保证增长",
            "禁止改变厂家规格、价格、产品事实或共享视觉模板"))
    guides = [p for p in snap["pages"]
              if "/guides/" in urlsplit(p["url"]).path
              and p["current"]["impressions"] >= 8
              and p["current"]["clicks"] > 0]
    if guides:
        p = max(guides, key=lambda x: (x["current"]["clicks"],
                                      x["current"]["impressions"]))
        plans.append(candidate(
            "TECHNICAL_SEARCH_DEMAND", "P2",
            "技术资料搜索需求：核对SDK／研究导线",
            {"url": p["url"], "current7d": p["current"],
             "previous7d": p["previous"],
             "source": f"GSC Master 03_Page {SOURCE_GSC}"},
            "只建议检查页面资源有效性、官方SDK出处和相关产品入口，不自动改内容",
            "下一完整7日的有效点击与产品咨询来源字段变化",
            "禁止承诺未验证的SDK兼容性、提供虚构下载"))
    return {
        "schema": "aa8-hp-growth-proposals-v1",
        "period": {"current": snap["periods"][0], "previous": snap["periods"][1]},
        "siteKPI": {"current": current, "previous": previous},
        "inquiryCoverage": {k: inquiries[k] for k in (
            "total", "withSourceProduct", "withSourceService", "withUtmSource")},
        "candidates": plans[:3], "candidateLimit": 3,
        "sourceIsReadOnly": True, "productionWriteAuthorized": False,
        "businessRevenueProven": False,
        "note": "Recommendations are NOT change approval. Recheck actual newest weekly data.",
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    data = propose(json.loads(a.input.read_text(encoding="utf-8")))
    require(a.input.resolve() != a.output.resolve(), "output cannot overwrite source")
    require(a.output.parent.resolve() != Path(__file__).resolve().parents[1] /
            "products", "cannot write products directory")
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(json.dumps({"candidates": len(data["candidates"]),
                      "gsc": data["siteKPI"],
                      "inquiries": data["inquiryCoverage"],
                      "output": str(a.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
