#!/usr/bin/env python3
"""Trusted-main, read-only Preview lookup and audited CEO re-review handoff.

Called only after a real PR repair is committed and exact-SHA CI + separate QA
both succeed. No merge, Pages, CRM, mail or arbitrary URL is authorized.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit

REPO = "2airadmin8/aa8-Robotic"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
MARKER = "<!-- AA8-CEO-REWORK-READY sha={sha} comment_id={comment_id} -->"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError("PREVIEW_HANDOFF_HOLD: " + message)


def github(path: str, method: str = "GET", body: str = "") -> object:
    require(path.startswith("repos/" + REPO + "/") and ".." not in path,
            "untrusted GitHub resource")
    cmd = ["gh", "api", "-X", method, path]
    if method == "POST":
        cmd.extend(["-f", "body=" + body])
    response = subprocess.run(cmd, text=True, encoding="utf-8",
                              capture_output=True, timeout=30, check=False)
    require(response.returncode == 0, "GitHub API read/write failed")
    return json.loads(response.stdout)


def eligible_preview(sha: str, deployments: list,
                     statuses: dict[str, list]) -> list[str]:
    """Use only successful GitHub deployments tied to exact SHA and Vercel."""
    require(bool(SHA_RE.fullmatch(sha)), "invalid SHA")
    found = []
    for deployment in deployments:
        if deployment.get("sha") != sha:
            continue
        if not str(deployment.get("environment") or "").startswith("Preview"):
            continue
        for status in statuses.get(str(deployment.get("id")), []):
            if status.get("state") != "success":
                continue
            url = status.get("environment_url") or ""
            p = urlsplit(url)
            if (p.scheme != "https" or not p.hostname
                    or not p.hostname.endswith(".vercel.app")
                    or p.username or p.password or p.query or p.fragment):
                continue
            if url not in found:
                found.append(url)
    # This project already uses an existing X2 review Preview; prefer that
    # but show other verified provider URLs as fallbacks.
    return sorted(found, key=lambda u: (0 if "x2-edu-make-review" in u else 1, u))


def verify_live(sha: str, pr: int, comment_id: int) -> None:
    require(pr > 0 and comment_id > 0 and bool(SHA_RE.fullmatch(sha)),
            "invalid PR, comment or SHA")
    item = github(f"repos/{REPO}/pulls/{pr}")
    require(item.get("state") == "open" and item.get("draft") is True,
            "original PR is no longer Draft")
    require((item.get("head") or {}).get("sha") == sha
            and ((item.get("head") or {}).get("repo") or {}).get("full_name") == REPO
            and ((item.get("base") or {}).get("ref") == "main"),
            "live PR HEAD or base changed")
    commit = github(f"repos/{REPO}/commits/{sha}")
    message = str(((commit.get("commit") or {}).get("message") or ""))
    email = str((((commit.get("commit") or {}).get("committer") or {}).get("email") or ""))
    require(re.search(r"(?m)^AA8-AUTOFIX-ATTEMPT: [123]\s*$", message) is not None,
            "new HEAD is not a bounded AI repair commit")
    require("github-actions[bot]" in email, "untrusted commit identity")
    comment = github(f"repos/{REPO}/issues/comments/{comment_id}")
    require(comment.get("issue_url") == f"https://api.github.com/repos/{REPO}/issues/{pr}"
            and (comment.get("user") or {}).get("id") == 211299962,
            "original CEO rejection not found")
    require("<!-- AA8-CEO-RETURNED sha=" in str(comment.get("body") or ""),
            "origin not a valid CEO rejection")


def preview_probe(url: str) -> str:
    """Fail-closed Preview probe: HTML_VERIFIED / AUTH_REQUIRED / INVALID.

    AUTH_REQUIRED means SSO is correctly enforced, not that the CEO saw the
    page. This read-only probe never uses a bypass token or stores cookies.
    """
    try:
        requested = urlsplit(url)
        if (requested.scheme != "https" or not requested.hostname
                or not requested.hostname.endswith(".vercel.app")
                or requested.username or requested.password
                or requested.query or requested.fragment):
            return "INVALID"
        request = urllib.request.Request(url, headers={
            "User-Agent": "AirAdmin8-Factory-Preview-Verification",
            "Cache-Control": "no-cache",
        })
        with urllib.request.urlopen(request, timeout=15) as response:
            final = urlsplit(response.url)
            if final.hostname == "vercel.com" and final.path == "/sso-api":
                return "AUTH_REQUIRED"
            if (response.status != 200 or final.hostname != requested.hostname
                    or final.path != requested.path):
                return "INVALID"
            if "text/html" not in response.headers.get("Content-Type", "").lower():
                return "INVALID"
            content = response.read(1_000_001)
            if len(content) > 1_000_000:
                return "INVALID"
            html = content.decode("utf-8", errors="replace")
            if re.search(r"(?i)vercel authentication|vercel.com/sso-api|log[ -]?in", html):
                return "AUTH_REQUIRED"
            checks = (
                re.search(r'<main\b[^>]*data-product-id="[a-z0-9-]+"', html),
                re.search(r'data-product-factory="g1-v1"', html),
                re.search(r'<meta\s+name="robots"\s+content="noindex,nofollow"', html),
                re.search(r'<header\b[^>]*data-shared-layout="header"', html),
                re.search(r'<footer\b[^>]*data-shared-layout="footer"', html),
                re.search(r'data-factory-cta="hero"', html),
                re.search(r'data-aa8-menu-runtime="true"', html),
                re.search(r'class="aa8-main-logo"', html),
            )
            return "HTML_VERIFIED" if all(checks) else "INVALID"
    except urllib.error.HTTPError as exc:
        return "AUTH_REQUIRED" if exc.code in (401, 403) else "INVALID"
    except (urllib.error.URLError, TimeoutError, ValueError, UnicodeError):
        return "INVALID"


def reachable(url: str) -> bool:
    """Compatibility wrapper: SSO screens are NEVER an HTML PASS."""
    return preview_probe(url) == "HTML_VERIFIED"


def trusted_review_previews(sha: str, deployments: list,
                            statuses: dict[str, list]) -> list[str]:
    """Only successful exact-SHA x2 review deployments by Vercel's bot.

    An authenticated CEO browser can open a protected Preview; the server-side
    workflow must never pretend its anonymous HTTP request viewed that HTML.
    """
    safe = []
    trusted_statuses = {}
    for d in deployments:
        if (d.get("sha") != sha
                or d.get("environment") != "Preview – x2-edu-make-review"):
            continue
        did = str(d.get("id"))
        approved = []
        for st in statuses.get(did, []):
            url = str(st.get("environment_url") or "")
            host = urlsplit(url).hostname or ""
            actor = (st.get("creator") or {}).get("login")
            if (actor == "vercel[bot]"
                    and re.fullmatch(r"x2-edu-make-review-[a-z0-9-]+\.vercel\.app", host)):
                approved.append(st)
        if approved:
            safe.append(d)
            trusted_statuses[did] = approved
    return eligible_preview(sha, safe, trusted_statuses)


def preview_path_from_pr(pr: int) -> str:
    """Use the ONE preview artifact declared by the original Draft PR diff.

    Never make up an A2 route for a different SKU. No untrusted PR code is run.
    """
    files = github(f"repos/{REPO}/pulls/{pr}/files?per_page=100")
    require(isinstance(files, list) and len(files) < 100,
            "PR file history requires pagination or is invalid")
    candidates = []
    for item in files:
        if not isinstance(item, dict):
            continue
        name = str(item.get("filename") or "")
        match = re.fullmatch(r"tests/fixtures/([a-z0-9-]+)/preview\.html", name)
        if match:
            candidates.append(match.group(1) + "-preview.html")
    require(len(candidates) == 1,
            "exactly one approved product-specific Preview fixture required")
    return candidates[0]


def require_postdeploy_sha_gate(sha: str) -> None:
    """CEO handoff is impossible without the trusted Vercel source-file gate.

    GitHub CI success and Vercel READY alone never establish the exact bytes
    of an SSO-protected reviewer deployment. The newest exact-SHA commit
    status must be produced by verified trusted-main postdeploy CI.
    """
    commit = github(f"repos/{REPO}/commits/{sha}/status")
    items = commit.get("statuses") if isinstance(commit,dict) else None
    require(isinstance(items,list), "post-deploy GitHub SHA evidence missing")
    related = [x for x in items if x.get("context") == "aa8-preview-postdeploy"]
    require(bool(related), "Vercel post-deploy exact-source SHA gate NOT_CONNECTED")
    latest=related[0]  # GitHub combined-status API returns newest first.
    require(latest.get("state") == "success"
            and (latest.get("creator") or {}).get("login") == "github-actions[bot]"
            and re.fullmatch(r"https://github\.com/2airadmin8/aa8-Robotic/actions/runs/\d+",
                             str(latest.get("target_url") or "")) is not None,
            "Vercel post-deploy exact-source SHA gate failed or unauthenticated")


def deliver(sha: str, pr: int, comment_id: int, run_id: int) -> dict:
    verify_live(sha, pr, comment_id)
    marker = MARKER.format(sha=sha, comment_id=comment_id)
    comments = github(f"repos/{REPO}/issues/{pr}/comments?per_page=100")
    require(isinstance(comments, list) and len(comments) < 100,
            "comment history requires pagination review")
    if any(marker in str(c.get("body") or "") for c in comments):
        return {"status": "ALREADY_DELIVERED", "sha": sha, "pr": pr}
    require_postdeploy_sha_gate(sha)
    previews = []
    # Bounded provider readiness polling; no recursive workflow or rerun.
    for attempt in range(6):
        deployments = github(f"repos/{REPO}/deployments?sha={sha}&per_page=100")
        status_map = {}
        for d in deployments[:20]:
            did = d.get("id")
            if (isinstance(did, int)
                    and d.get("sha") == sha
                    and d.get("environment") == "Preview – x2-edu-make-review"):
                status_map[str(did)] = github(
                    f"repos/{REPO}/deployments/{did}/statuses?per_page=5")
        candidates = trusted_review_previews(sha, deployments, status_map)
        previews = [(url, preview_probe(url)) for url in candidates]
        previews = [(url, status) for url, status in previews
                    if status in ("HTML_VERIFIED", "AUTH_REQUIRED")]
        if previews:
            break
        if attempt < 5:
            time.sleep(12)
    require(bool(previews), "no successful exact-SHA x2 review deployment with vercel[bot] proof")
    # An SSO 302 is sufficient to hand the protected link to the CEO, NOT
    # sufficient to claim HTML content was reviewed or approved.
    protected = any(status == "AUTH_REQUIRED" for _, status in previews)
    # Do not infer product identity from the Vercel deployment's project name.
    preview_path = preview_path_from_pr(pr)
    evidence_lines = []
    for url, state in previews:
        review_url = url.rstrip("/") + "/" + preview_path
        kind = ("受保护Preview部署成功；HTML仍待CEO登录确认" if state == "AUTH_REQUIRED"
                else "匿名HTML内容检查通过；仍待CEO实际审核")
        evidence_lines.append(f"- {kind}：{review_url}\n")
    body = (
        f"{marker}\n"
        f"### CEO再验收｜AI返工完成・精确SHA部署交接\n\n"
        f"- 原退回评论ID：{comment_id}\n"
        f"- 原Draft PR：#{pr}\n"
        f"- 新HEAD：\x60{sha}\x60\n"
        f"- 新SHA CI / 独立QA："
        f"https://github.com/{REPO}/actions/runs/{run_id}\n"
        + "".join(evidence_lines)
        + "\n**请通过现有SSO登录并实际查看新版HTML，再批准或退回。** "
          "Vercel READY / GitHub部署状态不是CEO已看页面的证明；"
          "不代表CEO批准、main合并或Production授权。"
    )
    github(f"repos/{REPO}/issues/{pr}/comments", method="POST", body=body)
    return {"status": "WAIT_CEO_SSO_REVIEW" if protected else "READY_FOR_CEO_REVIEW",
            "pr": pr, "sha": sha, "preview_count": len(previews),
            "html_verified": not protected, "release": "HOLD"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--comment-id", type=int, required=True)
    parser.add_argument("--run-id", type=int, required=True)
    args = parser.parse_args()
    try:
        require(args.repo == REPO, "wrong repository")
        print(json.dumps(deliver(args.sha, args.pr, args.comment_id,
                                 args.run_id), ensure_ascii=False))
        return 0
    except (ValueError, KeyError, TypeError, json.JSONDecodeError,
            subprocess.TimeoutExpired) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
