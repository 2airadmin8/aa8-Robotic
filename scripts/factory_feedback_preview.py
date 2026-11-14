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


def reachable(url: str) -> bool:
    try:
        request = urllib.request.Request(url, headers={
            "User-Agent": "AirAdmin8-Factory-Preview-Verification",
            "Cache-Control": "no-cache",
        })
        with urllib.request.urlopen(request, timeout=15) as response:
            final = urlsplit(response.url)
            if (response.status != 200 or not final.hostname
                    or not final.hostname.endswith(".vercel.app")):
                return False
            first = response.read(2048).lower()
            return b"<" in first and b"vercel authentication" not in first
    except (urllib.error.URLError, TimeoutError, ValueError):
        return False


def deliver(sha: str, pr: int, comment_id: int, run_id: int) -> dict:
    verify_live(sha, pr, comment_id)
    marker = MARKER.format(sha=sha, comment_id=comment_id)
    comments = github(f"repos/{REPO}/issues/{pr}/comments?per_page=100")
    require(isinstance(comments, list) and len(comments) < 100,
            "comment history requires pagination review")
    if any(marker in str(c.get("body") or "") for c in comments):
        return {"status": "ALREADY_DELIVERED", "sha": sha, "pr": pr}
    previews = []
    # Bounded provider readiness polling; no recursive workflow or rerun.
    for _ in range(6):
        deployments = github(f"repos/{REPO}/deployments?sha={sha}&per_page=100")
        status_map = {}
        for d in deployments[:20]:
            did = d.get("id")
            if isinstance(did, int) and str(d.get("environment") or "").startswith("Preview"):
                status_map[str(did)] = github(
                    f"repos/{REPO}/deployments/{did}/statuses?per_page=5")
        previews = [u for u in eligible_preview(sha, deployments, status_map)
                    if reachable(u)]
        if previews:
            break
        time.sleep(12)
    require(bool(previews), "no verified online Preview for exact new SHA")
    body = (
        f"{marker}\n"
        f"### CEO再验收｜AI返工完成・精确SHA证据\n\n"
        f"- 原退回评论ID：{comment_id}\n"
        f"- 原Draft PR：#{pr}\n"
        f"- 新HEAD：\x60{sha}\x60\n"
        f"- 新SHA CI / 独立QA："
        f"https://github.com/{REPO}/actions/runs/{run_id}\n"
        + "".join(f"- 已验证在线Preview：{url}\n" for url in previews)
        + "\n**请查看新版真实HTML后再次批准或退回。** "
          "这里只是技术QA/Preview证据，不代表CEO批准、main合并或Production授权。"
    )
    github(f"repos/{REPO}/issues/{pr}/comments", method="POST", body=body)
    return {"status": "READY_FOR_CEO_REVIEW", "pr": pr, "sha": sha,
            "preview_count": len(previews), "release": "HOLD"}


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
