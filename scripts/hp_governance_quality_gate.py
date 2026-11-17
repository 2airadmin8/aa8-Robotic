#!/usr/bin/env python3
"""AA8 PM/CTO HP governance: trace approved design contracts to code/tests.

Two distinct checks:
  audit: mandatory component ownership, source code and mapped regression paths
  pr: classify future GitHub PR changes and require scoped, evidence-backed intake

The "80 point" rule NEVER waives security/functionality/QA. Approval and real
independent browser QA remain separate; this checker does not self-approve.
No writes to CRM, products, main, GitHub or Production.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
TRACE = "docs/governance/hp-design-code-trace-v1.json"
FAMILY = "data/hp-page-family-contract-v1.json"
REPO = "2airadmin8/aa8-Robotic"
REQUIRED_SECTIONS = (
    "设计正本 / Design SSOT", "变更与根因 / Change & RCA",
    "防再发回归 / Regression", "真实业务证据 / E2E",
    "独立 QA 与发布",
)

PLACEHOLDER = re.compile(r"(?i)^(?:tbd|todo|none|later|unknown|n/?a|pending|未定|待确认)[.! ]*$")
CLASS_RE = re.compile(r"(?<![A-Z0-9])P[0-3](?![0-9])")
SOURCE_RE = re.compile(r"https?://\S+|#[0-9]+\b|GSC|Inquiry Master", re.I)
# Changes to the site, design, security and this governance itself are in scope.
SCOPED_ROOTS = ("products/", "includes/", "assets/css/", "assets/js/",
                "tests/", "scripts/", "docs/governance/", ".github/workflows/")
SCOPED_FILES = ("contact.html", "data/products.json", FAMILY, TRACE,
                ".github/ISSUE_TEMPLATE/hp-factory-governance.yml")


def ensure(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError("AA8_GOVERNANCE_HOLD: " + reason)


def load(root: Path = ROOT) -> dict:
    c = json.loads((root / TRACE).read_text("utf-8"))
    ensure(c.get("schemaVersion") == "aa8-hp-design-code-trace-v1",
           "design/code trace version")
    ensure(c.get("qualityRule", {}).get("maxAutoRepair") == 3,
           "maximum 3 bounded repairs")
    q = c["qualityRule"]
    ensure(q.get("mandatory") ==
           "ALL_SECURITY_FUNCTIONAL_DATA_INTEGRITY_AND_APPLICABLE_QA_GATES_PASS",
           "mandatory quality must be 100%")
    ensure(q.get("scoreIsNotReleaseAuthorization") is True,
           "quality score cannot authorize release")
    ensure(tuple(c["changeGate"]["headings"]) == REQUIRED_SECTIONS,
           "intake contract drift")
    ensure("figma.com/design/" in c["designSources"]["visual"]["reference"],
           "approved Figma reference missing")
    ensure("NOT_AUTOMATIC_FIGMA_PIXEL_PARITY" in
           c["designSources"]["visual"]["verification"],
           "must not claim automated Figma pixel proof")
    semantic_doc = root / c["designSources"]["content"]["path"]
    renderer_doc = root / c["designSources"]["factory"]["path"]
    ensure(semantic_doc.is_file() and renderer_doc.is_file(),
           "source design specification absent")
    family = json.loads((root / FAMILY).read_text("utf-8"))
    ensure(family["schemaVersion"] == "aa8-hp-page-family-contract-v1"
           and family["contentAuthority"].find("V3.1") >= 0
           and family["designAuthority"].find("V3.2") >= 0,
           "design/semantic version contract mismatch")
    ensure(len(family["families"]) == 4, "four content family contracts required")
    template = (root / ".github/PULL_REQUEST_TEMPLATE.md").read_text("utf-8")
    for heading in REQUIRED_SECTIONS:
        ensure("## " + heading in template,
               "existing PR template drift: " + heading)
    for label in ("优先级 P0/P1/P2/P3", "设计→代码对应模块ID",
                  "影响页面/组件/PC-SP", "终止条件与价值证明"):
        ensure(label in template, "mandatory PR field missing: " + label)
    modules = c["traceability"]
    ensure(len(modules) == 6 and len({x["id"] for x in modules}) == len(modules),
           "missing/duplicate traced modules")
    workflow = (root / ".github/workflows/ci.yml").read_text("utf-8")
    for module in modules:
        for kind in ("designDoc",):
            path = root / module[kind]
            ensure(path.is_file() and path.resolve().is_relative_to(root.resolve()),
                   module["id"] + " design document missing")
        for kind in ("implementation", "tests"):
            paths = module[kind]
            ensure(isinstance(paths, list) and bool(paths),
                   module["id"] + " empty " + kind)
            for relative in paths:
                path = root / relative
                ensure(path.resolve().is_relative_to(root.resolve()) and path.is_file(),
                       module["id"] + " missing " + kind + " " + relative)
                if kind == "tests":
                    ensure(path.name in workflow,
                           module["id"] + " test not wired into CI: " + relative)
    # Stronger than a text-only reference: the existing build actually owns
    # the shared shell; governance code must never create a second Header/Footer.
    build = (root / "scripts/build_site.py").read_text("utf-8")
    ensure('includes" / "site-header.html"' in build
           and 'includes" / "site-footer.html"' in build,
           "shared Header/Footer source no longer owned by current build")
    pages = (root / "data/products.json").read_text("utf-8")
    ensure(len(json.loads(pages)["products"]) == 13,
           "13 current product regression targets changed without review")
    return c


def parse_sections(body: str) -> dict[str, str]:
    """Reuse existing AA8 PR template, no duplicate forms or approvals."""
    ensure(isinstance(body, str) and len(body) <= 100000, "unexpected PR body")
    headings = [(m.group(1).strip(), m.start(), m.end())
                for m in re.finditer(r"(?m)^##[ \t]+([^\r\n]+)[ \t]*$", body)]
    sections: dict[str, str] = {}
    for i, (title, _, end) in enumerate(headings):
        if title not in REQUIRED_SECTIONS:
            continue
        ensure(title not in sections, "duplicate PR section " + title)
        next_start = headings[i + 1][1] if i + 1 < len(headings) else len(body)
        data = body[end:next_start].strip()
        ensure(len(data) >= 24 and not PLACEHOLDER.fullmatch(data),
               "missing PR section content for " + title)
        sections[title] = data
    ensure(set(sections) == set(REQUIRED_SECTIONS),
           "missing existing PR template headings: " +
           ", ".join(x for x in REQUIRED_SECTIONS if x not in sections))
    return sections


def field(sections: dict[str, str], section: str, label: str) -> str:
    """Missing/empty template answers fail; labels alone are NOT evidence."""
    source = sections[section]
    pattern = r"(?m)^-[ \t]*" + re.escape(label) + r"[：:][ \t]*([^\r\n]*)"
    match = re.search(pattern, source)
    ensure(match is not None, "missing PR answer label: " + label)
    answer = match.group(1).strip()
    ensure(len(answer) >= 8 and not PLACEHOLDER.fullmatch(answer),
           "empty or placeholder answer: " + label)
    return answer


def normalized_files(file_list: object) -> list[str]:
    if isinstance(file_list, dict):
        ensure(isinstance(file_list.get("files"), list), "invalid file list")
        file_list = file_list["files"]
    # GitHub 'gh api --paginate --slurp' delivers list of pages of file records.
    if isinstance(file_list, list) and file_list and isinstance(file_list[0], list):
        file_list = [row for page in file_list for row in page]
    ensure(isinstance(file_list, list) and 0 < len(file_list) <= 300,
           "missing or too many changed files")
    result = []
    for item in file_list:
        ensure(isinstance(item, dict) and isinstance(item.get("filename"), str),
               "unrecognized changed file entry")
        relative = item["filename"]
        ensure(len(relative) < 255 and not relative.startswith(("/", "\\")) and
               "\\" not in relative and ".." not in Path(relative).parts,
               "unsafe changed path")
        result.append(relative)
    ensure(len(result) == len(set(result)), "duplicate file entries")
    return result


def mapped_module(path: str, c: dict) -> set[str]:
    ids = set()
    for m in c["traceability"]:
        if path in m["implementation"] or path in m["tests"] or path == m["designDoc"]:
            ids.add(m["id"])
    if path.startswith("products/") or path.startswith("assets/img/products/"):
        ids.add("PRODUCT_FACTS")
    if path.startswith("docs/governance/") or path.startswith(".github/ISSUE_TEMPLATE/"):
        ids.add("GOVERNANCE")
    return ids


def check_pr(event: dict, file_list: object, root: Path = ROOT,
             contract: dict | None = None) -> dict:
    c = contract or load(root)
    ensure(event.get("action") in ("opened", "synchronize", "reopened",
                                   "ready_for_review", "edited"),
           "not a supported PR event")
    repository = (event.get("repository") or {}).get("full_name")
    pr = event.get("pull_request") or {}
    ensure(repository == REPO and isinstance(pr.get("number"), int) and
           (pr.get("base") or {}).get("ref") == "main" and
           (pr.get("head") or {}).get("repo", {}).get("full_name") == REPO,
           "wrong repository or fork")
    files = normalized_files(file_list)
    scope = [f for f in files if f in SCOPED_FILES or f.startswith(SCOPED_ROOTS)]
    created = datetime.fromisoformat(str(pr["created_at"]).replace("Z", "+00:00"))
    effective = datetime.fromisoformat(c["effectiveFromUtc"])
    ensure(created.tzinfo and effective.tzinfo, "timestamp lacks timezone")
    if not scope:
        return {"status": "OUT_OF_SCOPE", "checked": len(files)}
    if created < effective:
        return {"status": "LEGACY_INTAKE_EXEMPT_NOT_SAFETY_EXEMPT",
                "checked": len(files)}
    sections = parse_sections(pr.get("body") or "")
    design = sections["设计正本 / Design SSOT"]
    change = sections["变更与根因 / Change & RCA"]
    qa = sections["防再发回归 / Regression"]
    e2e = sections["真实业务证据 / E2E"]
    approval = sections["独立 QA 与发布"]
    source = field(sections, "设计正本 / Design SSOT", "Design / Figma / Drive")
    business = field(sections, "设计正本 / Design SSOT", "业务目标与范围")
    exclusions = field(sections, "设计正本 / Design SSOT", "禁止改动的文件、流程")
    priority = field(sections, "变更与根因 / Change & RCA", "优先级 P0/P1/P2/P3")
    trace = field(sections, "变更与根因 / Change & RCA", "设计→代码对应模块ID")
    impact = field(sections, "变更与根因 / Change & RCA", "影响页面/组件/PC-SP")
    field(sections, "变更与根因 / Change & RCA", "本次修复范围")
    field(sections, "防再发回归 / Regression", "自动测试文件与测试名称")
    field(sections, "防再发回归 / Regression", "PC/SP、关键业务边界检查")
    stop = field(sections, "真实业务证据 / E2E", "失败 / 回滚时的应对")
    value_rule = field(
        sections, "真实业务证据 / E2E",
        "终止条件与价值证明（安全/核心功能100%；视觉/文案达标即停；额外打磨需收益证据）")
    field(sections, "独立 QA 与发布", "独立QA审查者（不得与Dev相同）")
    ensure(SOURCE_RE.search(source + " " + business) is not None,
           "missing actual design/business evidence source")
    category = CLASS_RE.search(priority)
    ensure(category is not None, "P0/P1/P2/P3 priority missing")
    if category.group() in ("P2", "P3"):
        ensure(re.search(r"(?i)baseline|基准|実績|過去7日", business) is not None
               and re.search(r"\d", business) is not None,
               "P2/P3 requires measured business baseline")
    target_modules: set[str] = set()
    for path in scope:
        target_modules.update(mapped_module(path, c))
    ensure(bool(target_modules)
           and all(re.search(r"\b" + re.escape(x) + r"\b", trace, re.I)
                   for x in target_modules),
           "affected design-code module IDs missing: " +
           ", ".join(sorted(target_modules)))
    shared = any(f in {
        "includes/site-header.html", "includes/site-footer.html",
        "assets/css/shared-layout.css",
    } for f in scope)
    if shared:
        ensure("13" in impact and "pc" in impact.lower()
               and "sp" in impact.lower(),
               "shared shell requires 13 product PC/SP impact statement")
    ensure("HOLD" in stop.upper() and
           re.search(r"(?i)sha|commit|head", stop) is not None,
           "missing HOLD and exact-SHA rollback rule")
    ensure("100" in value_rule and ("停止" in value_rule or
           "stop" in value_rule.lower() or "收口" in value_rule),
           "mandatory quality and stop-when-approved principle missing")
    return {
        "status": "SCOPED_INTAKE_READY_NOT_RELEASE_APPROVED",
        "category": category.group(), "mappedModules": sorted(target_modules),
        "changed": len(files), "relevant": len(scope),
    }



# CEO A2 redline screenshot integrity audit; NOT automated visual approval.
A2_REDLINE_SHOTS = {
    "V01": "a2-fullpage", "V02": "a2-fullpage",
    "V03": "a2-buglist-facts", "V04": "a2-buglist-usecases",
    "V05": "a2-sales-media", "V06": "a2-fullpage",
    "V07": "a2-fullpage", "V08": "a2-spec-first-row",
    "V09": "a2-spec-heading", "V10": "a2-sales-sdk",
    "V11": "a2-sales-solutions", "V12": "a2-sales-process",
    "V13": "a2-sales-faq", "V14": "a2-sales-related",
    "V15": "a2-sales-cta",
}
A2_VISUAL_VIEWPORTS = (1440, 390, 360)


def a2_visual_evidence(head_sha: str, screenshots: Path, out: Path) -> dict:
    """Validate exact-SHA PNG evidence; never certify CEO design alignment."""
    import hashlib
    import struct

    ensure(re.fullmatch(r"[0-9a-f]{40}", head_sha) is not None,
           "A2 screenshot exact SHA missing")
    ensure(screenshots.is_dir(), "A2 screenshots absent")

    def check_image(filename: str, viewport: int) -> dict:
        image = screenshots / filename
        ensure(image.is_file(), "screenshot missing: " + filename)
        raw = image.read_bytes()
        ensure(len(raw) > 1024 and raw[:8] == b"\x89PNG\r\n\x1a\n"
               and raw[12:16] == b"IHDR",
               "invalid/empty PNG: " + filename)
        # Check actual PNG chunk framing/CRC. A forged IHDR-only blob is
        # not a screenshot and must not pass an independent evidence gate.
        import zlib
        cursor = 8
        seen_idat = False
        seen_iend = False
        while cursor + 12 <= len(raw):
            size = struct.unpack(">I", raw[cursor:cursor+4])[0]
            end = cursor + 12 + size
            ensure(size <= 100_000_000 and end <= len(raw),
                   "PNG chunk truncated: " + filename)
            kind = raw[cursor+4:cursor+8]
            data = raw[cursor+8:cursor+8+size]
            checksum = struct.unpack(">I", raw[cursor+8+size:end])[0]
            ensure(zlib.crc32(kind + data) & 0xffffffff == checksum,
                   "PNG chunk CRC invalid: " + filename)
            if kind == b"IDAT":
                seen_idat = True
            if kind == b"IEND":
                seen_iend = True
                ensure(end == len(raw), "PNG trailing bytes: " + filename)
                break
            cursor = end
        ensure(seen_idat and seen_iend,
               "PNG image data missing: " + filename)
        width, height = struct.unpack(">II", raw[16:24])
        # Full-page captures must match the viewport. Cropped module/row
        # screenshots are intentionally narrower and some table rows short.
        is_fullpage = filename.startswith("a2-fullpage-")
        ensure(80 <= width <= viewport + 2 and height >= 40
               and (not is_fullpage or width == viewport),
               "wrong viewport PNG: " + filename)
        return {"file": filename, "sha256": hashlib.sha256(raw).hexdigest(),
                "width": width, "height": height}

    bugs = {}
    for bug, stem in A2_REDLINE_SHOTS.items():
        bugs[bug] = {
            "status": "HOLD_INDEPENDENT_VISUAL_COMPARISON",
            "screenshots": {str(view): check_image(f"{stem}-{view}.png", view)
                            for view in A2_VISUAL_VIEWPORTS},
        }
    for viewport in (390, 360):
        check_image(f"a2-sp-cta-after-anchor-{viewport}.png", viewport)
    report = {
        "schema": "aa8-a2-redline-visual-evidence-v1",
        "pr": 180, "head_sha": head_sha, "bugs": bugs,
        "screenshot_integrity": "PASS",
        "independent_reference_comparison": "NOT_ATTESTED",
        "p0_p1_closure": "NOT_ATTESTED",
        "visual_approval": "HOLD", "production_release": "HOLD",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n",
                   encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("audit", "pr", "visual-evidence"))
    parser.add_argument("--event", type=Path)
    parser.add_argument("--files", type=Path)
    parser.add_argument("--head-sha")
    parser.add_argument("--screenshots", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        c = load()
        if args.mode == "visual-evidence":
            ensure(args.head_sha and args.screenshots and args.out,
                   "A2 exact SHA, screenshots and output required")
            result = a2_visual_evidence(args.head_sha,
                                        args.screenshots, args.out)
            print(json.dumps({"status":"A2_EVIDENCE_PASS",
                "visual_approval":result["visual_approval"],
                "bugs":len(result["bugs"]), "head_sha":args.head_sha}))
        elif args.mode == "audit":
            print(json.dumps({"status": "DESIGN_CODE_TRACE_PASS",
                              "modules": [x["id"] for x in c["traceability"]],
                              "release": "HOLD"}, ensure_ascii=False))
        else:
            ensure(args.event is not None and args.files is not None,
                   "PR event and GitHub changed-file list required")
            result = check_pr(json.loads(args.event.read_text("utf-8-sig")),
                              json.loads(args.files.read_text("utf-8-sig")),
                              contract=c)
            print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
