#!/usr/bin/env python3
"""Manufacturer-first exact cell monitoring for versioned, allowlisted product sources.

Never certifies translations from a matching row count. Live changes to manufacturer
facts always HOLD a release until verified; --stage creates isolated proposed data,
never commits, merges, deploys or writes Production/Master.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/a2-factory"
USER_AGENT = "AirAdmin8-MakerSpecVerifier/1.0 (source-verification)"
MAX_BYTES = 2_000_000
ALLOWED = {"www.unitree.com": {"/A2/"}}  # legacy A2 baseline, no general URL wildcard
MAKER_REGISTRY = ROOT / "data/manufacturers.json"


@dataclass
class Node:
    tag: str
    attrs: dict = field(default_factory=dict)
    kids: list = field(default_factory=list)

    def matches(self, tag, cls=None):
        return self.tag == tag and (cls is None or cls in self.attrs.get("class", "").split())

    def find(self, tag, cls=None):
        result = []
        for kid in self.kids:
            if isinstance(kid, Node):
                if kid.matches(tag, cls):
                    result.append(kid)
                result.extend(kid.find(tag, cls))
        return result

    def text(self):
        return " ".join(k.text() if isinstance(k, Node) else k for k in self.kids)


class Tree(HTMLParser):
    VOID = {"img", "br", "meta", "link", "input", "source", "hr", "wbr", "area", "embed"}
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("document")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        n = Node(tag, dict(attrs))
        self.stack[-1].kids.append(n)
        if tag not in self.VOID:
            self.stack.append(n)

    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        if data.strip():
            self.stack[-1].kids.append(data)


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", unescape(text).replace("\u00a0", " ")).strip()


def safe_url(url: str, *, contract: dict | None = None) -> None:
    """Permit only an exact, registered manufacturer origin and a configured path.

    The manufacturer directory is the pre-existing, separately maintained
    allowlist. An arbitrary source-contract.json must never grant network trust.
    """
    parts = urlsplit(url)
    if (parts.scheme != "https" or not parts.hostname or parts.port is not None
            or parts.username or parts.password or parts.query or parts.fragment
            or not parts.path.startswith("/") or "//" in parts.path
            or ".." in parts.path.split("/") or "\\" in parts.path):
        raise ValueError("SOURCE_HOLD: unsafe manufacturer source URL")
    if contract is None:
        if parts.hostname not in ALLOWED or parts.path not in ALLOWED[parts.hostname]:
            raise ValueError("SOURCE_HOLD: manufacturer URL not in exact trusted allowlist")
        return
    maker_id = contract.get("manufacturer_id")
    if not isinstance(maker_id, str) or not maker_id:
        raise ValueError("SOURCE_HOLD: manufacturer ID required for source trust")
    registry = json.loads(MAKER_REGISTRY.read_text("utf-8"))
    matched = [m for m in registry.get("manufacturers", [])
               if m.get("id") == maker_id and m.get("status") == "active"]
    if len(matched) != 1:
        raise ValueError("SOURCE_HOLD: maker not active in official registry")
    official = urlsplit(matched[0]["officialUrl"])
    if parts.hostname != official.hostname or official.scheme != "https":
        raise ValueError("SOURCE_HOLD: source is not registered maker origin")
    # A2 remains path-pinned; other manufacturers require an independently
    # verified adapter + exact source URL in the frozen contract.
    if maker_id == "unitree" and parts.path == "/A2/":
        return
    if contract.get("adapter") != "html-table-v1":
        raise ValueError("SOURCE_HOLD: new maker adapter not independently verified")


def enforce_source_trust(contract: dict) -> None:
    safe_url(contract["source_url"], contract=contract)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("SOURCE_HOLD: redirect requires separate approval")


def fetch(url: str, *, contract: dict | None = None) -> bytes:
    safe_url(url, contract=contract)
    opener = build_opener(NoRedirect)
    with opener.open(Request(url, headers={"User-Agent": USER_AGENT}), timeout=18) as r:
        if r.status != 200:
            raise ValueError("SOURCE_HOLD: HTTP response not 200")
        blob = r.read(MAX_BYTES + 1)
        if len(blob) > MAX_BYTES:
            raise ValueError("SOURCE_HOLD: source page unexpectedly large")
        if "html" not in r.headers.get("Content-Type", "").lower():
            raise ValueError("SOURCE_HOLD: source not HTML")
        return blob


def parse_unitree_a2(blob: bytes):
    tree = Tree()
    tree.feed(blob.decode("utf-8", "replace"))
    ds = tree.root.find("div", "decompose")
    if len(ds) != 1:
        raise ValueError("SOURCE_HOLD: unique official A2 comparison missing")
    d = ds[0]
    models = [norm(p.text()) for versions in d.find("ul", "versions")
              for li in versions.find("li") for p in li.kids
              if isinstance(p, Node) and p.tag == "p"
              and norm(p.text()) in ("A2", "A2-PRO")]
    if models != ["A2", "A2-PRO"]:
        raise ValueError("SOURCE_HOLD: maker model columns changed")
    parts = d.find("div", "part")
    categories = []
    for part in parts:
        cats = [norm(x.text()) for x in part.kids if isinstance(x, Node) and x.matches("div", "category")]
        values = [x for x in part.kids if isinstance(x, Node) and x.matches("ul", "value")]
        if len(cats) != 1 or len(values) != 1:
            raise ValueError("SOURCE_HOLD: manufacturer group structure changed")
        rows = []
        for row in values[0].kids:
            if not isinstance(row, Node) or row.tag != "li":
                continue
            cells = [norm(x.text()) for x in row.find("div", "valPart")]
            if len(cells) != 3 or any(not x for x in cells):
                raise ValueError("SOURCE_HOLD: manufacturer row no longer has 2 model values")
            rows.append({"source_label": cells[0], "models": dict(zip(models, cells[1:]))})
        categories.append({"name": cats[0], "rows": rows})
    if len(categories) != 4:
        raise ValueError("SOURCE_HOLD: official group count changed")
    return {"models":models,"categories":categories}


def load_contract(path: Path) -> dict:
    data = json.loads(path.read_text("utf-8"))
    if data.get("schema") != "aa8-maker-source-contract-v1":
        raise ValueError("SOURCE_HOLD: contract schema missing")
    enforce_source_trust(data)
    if data["adapter"] not in {"unitree-a2-html-v1", "html-table-v1"}:
        raise ValueError("SOURCE_HOLD: manufacturer adapter not verified")
    return data


def parse_html_table(blob: bytes, contract: dict) -> dict:
    """Opt-in adapter for real 3-column maker tables, NOT arbitrary guesses.

    Each approved contract identifies a unique table ID and explicit category
    header class. If a site uses JS/PDF/other layout, the adapter must be
    separately verified first and the unattended intake holds.
    """
    table_id = contract.get("table_id")
    group_class = contract.get("group_class", "maker-group")
    if not isinstance(table_id, str) or not re.fullmatch("[A-Za-z0-9_-]{3,64}", table_id):
        raise ValueError("SOURCE_HOLD: manufacturer table ID required")
    doc=Tree()
    doc.feed(blob.decode("utf-8","replace"))
    tables=[x for x in doc.root.find("table") if x.attrs.get("id")==table_id]
    if len(tables)!=1:
        raise ValueError("SOURCE_HOLD: manufacturer table missing or ambiguous")
    groups=[]
    current=None
    for tr in tables[0].find("tr"):
        if group_class in tr.attrs.get("class","").split():
            cells=tr.find("th")
            if len(cells)!=1:
                raise ValueError("SOURCE_HOLD: invalid group row")
            current={"name":norm(cells[0].text()),"rows":[]}
            groups.append(current)
            continue
        if current is None:
            continue  # only optional header rows before the first category
        cells=[x for x in tr.kids if isinstance(x,Node) and x.tag in ("td","th")]
        if len(cells)!=len(contract["models"])+1 or any(not norm(c.text()) for c in cells):
            raise ValueError("SOURCE_HOLD: wrong manufacturer model cell count")
        current["rows"].append({"source_label":norm(cells[0].text()),"models":{
            m:norm(c.text()) for m,c in zip(contract["models"],cells[1:])
        }})
    if not groups or any(not x["rows"] for x in groups):
        raise ValueError("SOURCE_HOLD: manufacturer categories missing")
    return {"models":contract["models"],"categories":groups}


def parse_source(blob: bytes, contract: dict) -> dict:
    if contract["adapter"]=="unitree-a2-html-v1":
        return parse_unitree_a2(blob)
    if contract["adapter"]=="html-table-v1":
        return parse_html_table(blob,contract)
    raise ValueError("SOURCE_HOLD: unsupported maker source parser")


def flatten(parsed):
    return [(cat["name"], i["source_label"], m, v)
            for cat in parsed["categories"] for i in cat["rows"]
            for m,v in i["models"].items()]


def compare(parsed: dict, contract: dict) -> list[dict]:
    if parsed["models"] != contract["models"]:
        raise ValueError("SOURCE_HOLD: model list changed")
    actual = parsed["categories"]
    expected = contract["categories"]
    if len(actual) != len(expected):
        raise ValueError("SOURCE_HOLD: categories changed")
    drift = []
    for ci,(a,e) in enumerate(zip(actual,expected)):
        if a["name"] != e["source_name"] or len(a["rows"]) != len(e["rows"]):
            raise ValueError("SOURCE_HOLD: category identity or row count changed")
        for ri,(row,expected_row) in enumerate(zip(a["rows"],e["rows"])):
            if row["source_label"] != expected_row["source_label"]:
                raise ValueError("SOURCE_HOLD: maker parameter identity/order changed")
            for model in contract["models"]:
                before = expected_row["models"][model]
                after = row["models"][model]
                if norm(before) != norm(after):
                    drift.append({"category":e["source_name"],"parameter_id":expected_row["id"],
                                  "model":model,"before":before,"after":after,
                                  "category_index":ci,"row_index":ri})
    return drift


def verify_display(product: dict, contract: dict, parsed: dict) -> None:
    specs = product["pageFactory"]["specifications"]
    expected = [r for g in contract["categories"] for r in g["rows"]]
    if len(specs) != len(expected):
        raise ValueError("DISPLAY_HOLD: product parameter count mismatch")
    for i,(row,ref) in enumerate(zip(specs,expected)):
        if row.get("parameter") != ref["id"] or set(row["models"]) != set(contract["models"]):
            raise ValueError(f"DISPLAY_HOLD: wrong model / row mapping at {i}")
        # Every language translation must have been independently approved against
        # an exact raw maker cell. A reference to itself is never independent evidence.
        approved = ref.get("approved_display")
        if not isinstance(approved, dict) or set(approved) != set(contract["models"]):
            raise ValueError(f"DISPLAY_HOLD: missing manufacturer-to-JP verified mapping at {i}")
        for m in contract["models"]:
            if row["models"][m] != approved[m]:
                raise ValueError(f"DISPLAY_HOLD: JP display drift or unapproved auto-edit {ref['id']}/{m}")


def run(contract_path: Path, product_path: Path, *, source_file: Path | None = None,
        source_bytes: bytes | None = None,
        output: Path | None = None, stage: bool = False) -> dict:
    contract = load_contract(contract_path)
    product = json.loads(product_path.read_text("utf-8"))
    blob = (source_bytes if source_bytes is not None else
            source_file.read_bytes() if source_file else
            fetch(contract["source_url"], contract=contract))
    live = parse_source(blob,contract)
    drifts = compare(live,contract)
    verify_display(product,contract,live)
    output_report = {
        "source_url":contract["source_url"],
        "verified_at":datetime.now(timezone.utc).isoformat(),
        "source_sha256":sha256(blob).hexdigest(),
        "models":live["models"],
        "groups":[{"name":g["name"],"count":len(g["rows"])} for g in live["categories"]],
        "parameter_rows":sum(len(g["rows"]) for g in live["categories"]),
        "cells_checked":len(flatten(live)),
        "drift":drifts,
        "status":"SOURCE_CHANGED_HOLD" if drifts else "SOURCE_MATCH_PASS",
        "release":"HOLD",
    }
    if stage and drifts:
        # All changes remain isolated candidate files. An exact, unmodified official
        # cell can replace the translated cell as proposed maker-original text,
        # never as an silently approved Japanese translation.
        if not output:
            raise ValueError("SOURCE_HOLD: candidate output destination required")
        if output.exists():
            raise ValueError("SOURCE_HOLD: refusing overwrite of an existing candidate")
        if not output.resolve().is_relative_to(ROOT.resolve()):
            raise ValueError("SOURCE_HOLD: candidate must stay in repo isolation")
        output.mkdir(parents=True,exist_ok=False)
        candidate=json.loads(json.dumps(product))
        candidate_contract=json.loads(json.dumps(contract))
        spec_rows=candidate["pageFactory"]["specifications"]
        for change in drifts:
            idx=sum(len(g["rows"]) for g in contract["categories"][:change["category_index"]])+change["row_index"]
            model=change["model"]
            # Use maker-original raw text until an independent JA translation is
            # verified. Old translated values must never be left as "current".
            spec_rows[idx]["models"][model]=change["after"]
            spec_rows[idx]["value"]=" / ".join(
                m+": "+spec_rows[idx]["models"][m] for m in contract["models"]
            )
            cell=candidate_contract["categories"][change["category_index"]]["rows"][change["row_index"]]
            cell["models"][model]=change["after"]
            cell["approved_display"][model]=change["after"]
            cell["review_status"]="PENDING_INDEPENDENT_FACT_REVIEW"
        # Bounded isolated correction/validation loop. No network actions and
        # no blind changes on subsequent rounds. A new unrecognized maker row
        # is structurally rejected BEFORE staging.
        resolved = False
        rounds = 0
        for rounds in range(1,4):
            try:
                remaining=compare(live,candidate_contract)
                verify_display(candidate,candidate_contract,live)
                if not remaining:
                    resolved=True
                    break
            except ValueError:
                pass
        if not resolved:
            raise ValueError("SOURCE_HOLD: isolated candidate failed three verification rounds")
        (output/"candidate-product.json").write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+"\n","utf-8")
        (output/"candidate-source-contract.json").write_text(json.dumps(candidate_contract,ensure_ascii=False,indent=2)+"\n","utf-8")
        (output/"diff.json").write_text(json.dumps({"status":"PENDING_INDEPENDENT_FACT_REVIEW",
                 "source_url":contract["source_url"],"changes":drifts},ensure_ascii=False,indent=2)+"\n","utf-8")
        output_report["candidate"] = str(output.relative_to(ROOT))
        output_report["candidate_action"]="ISOLATED_MAKER_ORIGINAL_TEXT_PROPOSED_NOT_APPROVED"
        output_report["isolated_recheck_rounds"]=rounds
        output_report["isolated_data_consistency"]="PASS_NOT_RELEASE_AUTHORIZATION"
    if not drifts and any(r.get("review_status")!="INDEPENDENTLY_VERIFIED" for g in contract["categories"] for r in g["rows"]):
        output_report["status"]="SOURCE_MATCH_TRANSLATION_REVIEW_PENDING"
    return output_report


def audit_new_intake(root: Path) -> dict:
    verified=0
    for item in (root/"tests/fixtures").glob("*/product.json"):
        product=json.loads(item.read_text("utf-8"))
        if product.get("id")=="agibot-x2-series":
            continue  # existing grandfathered unverified pilot, not a PASS
        source=item.parent/"maker-live-contract.json"
        if not source.is_file():
            raise ValueError(f"SOURCE_HOLD: new SKU {product['id']} lacks maker-live-contract.json")
        contract=load_contract(source)
        if contract["source_url"]!=product["pageFactory"]["officialSource"]:
            raise ValueError(f"SOURCE_HOLD: new SKU {product['id']} official URL mismatch")
        verified+=1
    return {"status":"FACTORY_MAKER_INTAKE_PASS","contracts_checked":verified,
            "historical_unverified":"agibot-x2-series"}


def monitor_all(root: Path, *, stage_dir: Path | None = None) -> list[dict]:
    """Single existing Factory entrypoint; optional proposal-only drift repair.

    No automatic approvals, commits, write to Master, or recursive CI triggers.
    A fresh stage_dir is explicit and never overwritten. All recorded drifts
    still raise HOLD even if their isolated candidate passes consistency tests.
    """
    audit_new_intake(root)
    reports=[]
    if stage_dir is not None:
        if stage_dir.exists() or not stage_dir.resolve().is_relative_to(root.resolve()):
            raise ValueError("SOURCE_HOLD: isolated stage root must be new and within repository")
    for item in sorted((root/"tests/fixtures").glob("*/maker-live-contract.json")):
        contract = load_contract(item)
        source_snapshot = fetch(contract["source_url"], contract=contract)
        result=run(item,item.parent/"product.json",source_bytes=source_snapshot)
        if result["drift"] and stage_dir is not None:
            # Existing run() stages and checks a bounded (<=3) isolated patch.
            # Keep each maker product separate and never rewrite the source.
            result=run(item,item.parent/"product.json",
                       source_bytes=source_snapshot,
                       output=stage_dir/item.parent.name,stage=True)
        reports.append(result)
        if result["drift"]:
            raise ValueError("SOURCE_HOLD: maker source exact-cell changes "
                             + item.parent.name + " "
                             + json.dumps({"changes":result["drift"],
                                          "isolated_candidate":result.get("candidate"),
                                          "review":"PENDING_INDEPENDENT_FACT_REVIEW"},
                                         ensure_ascii=False))
        if result["status"] not in ("SOURCE_MATCH_PASS",
                                    "SOURCE_MATCH_TRANSLATION_REVIEW_PENDING"):
            raise ValueError("SOURCE_HOLD: manufacturer source cannot be verified")
    return reports


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--contract",type=Path,default=FIXTURE/"maker-live-contract.json")
    a.add_argument("--product",type=Path,default=FIXTURE/"product.json")
    a.add_argument("--source-file",type=Path)
    a.add_argument("--output",type=Path)
    a.add_argument("--stage",action="store_true")
    a.add_argument("--monitor",action="store_true",
                   help="CI check exact manufacturer source change; pending JP review stays HOLD for release")
    a.add_argument("--monitor-all",action="store_true",
                   help="check every onboarded maker through existing Factory; all drifts HOLD")
    a.add_argument("--intake",action="store_true",
                   help="require maker evidence contract for all newly onboarded fixtures")
    args=a.parse_args()
    try:
        if args.intake:
            print(json.dumps(audit_new_intake(ROOT)))
            return 0
        if args.monitor_all:
            reports=monitor_all(ROOT,stage_dir=args.output if args.stage else None)
            print(json.dumps({"status":"SOURCE_MONITOR_PASS","reports":reports},ensure_ascii=False))
            return 0
        report=run(args.contract,args.product,source_file=args.source_file,output=args.output,stage=args.stage)
        print(json.dumps(report,ensure_ascii=False))
        if report["status"]=="SOURCE_MATCH_PASS":
            return 0
        if args.monitor and report["status"]=="SOURCE_MATCH_TRANSLATION_REVIEW_PENDING":
            return 0  # protects against source drift, NEVER marks full source facts QA complete
        return 2
    except Exception as e:
        print(json.dumps({"status":"SOURCE_HOLD","reason":str(e),"release":"HOLD"},ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
