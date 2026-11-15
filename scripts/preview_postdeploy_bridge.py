#!/usr/bin/env python3
"""Trusted preview post-deployment bridge (no checkout of unreviewed PR code).

Entry: existing Vercel Git integration's vercel.deployment.ready dispatch, or
an authorized exact-ID controlled replay. Uses protected VERCEL_TOKEN in CI to
read deployment + source file list, validates team/project/exact SHA, then
reuses verify_preview_bundle's existing immutable SHA1 contract.

Never merges, promotes, deploys, weakens SSO, or writes Production/CRM.
Missing token or source manifest is a HARD HOLD, not a skipped check.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler

from verify_preview_bundle import select_deployed_previews, verify_deployment

PROJECT_ID = "prj_vH6kcA1vFU6FPCm3skNdpudINkEh"
TEAM_ID = "team_xYXQL3tQXxLKFRUNOYVaMoYA"
API = "https://api.vercel.com"
SHA = re.compile(r"^[0-9a-f]{40}$")
DEPLOY = re.compile(r"^dpl_[A-Za-z0-9]+$")
MAX_JSON = 3_000_000


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError("PREVIEW_POSTDEPLOY_HOLD: " + reason)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise ValueError("PREVIEW_POSTDEPLOY_HOLD: Vercel API redirect refused")


def api_json(path: str, token: str) -> object:
    require(bool(token), "protected VERCEL_TOKEN missing")
    require(path.startswith("/") and "?" not in path and ".." not in path,
            "unexpected Vercel endpoint")
    address=API+path+"?"+urlencode({"teamId": TEAM_ID})
    req=Request(address,headers={
        "Authorization":"Bearer "+token,
        "Accept":"application/json",
        "User-Agent":"AirAdmin8-PreviewPostdeployGate/1",
    })
    try:
        with build_opener(NoRedirect).open(req,timeout=18) as response:
            require(response.status==200, "Vercel returned HTTP non-200")
            data=response.read(MAX_JSON+1)
            require(len(data)<=MAX_JSON, "Vercel metadata too large")
            return json.loads(data.decode("utf-8"))
    except HTTPError as exc:
        raise ValueError("PREVIEW_POSTDEPLOY_HOLD: Vercel read authorization/API HTTP "+str(exc.code)) from None
    except (URLError,TimeoutError,UnicodeError,json.JSONDecodeError) as exc:
        raise ValueError("PREVIEW_POSTDEPLOY_HOLD: Vercel metadata/readback unavailable") from None


def audit_postdeploy(expected:dict, deployment:dict, tree:object,
                     deployment_id:str, expected_sha:str)->dict:
    """Pure trusted computation. Source data does not grant permissions."""
    require(bool(DEPLOY.fullmatch(deployment_id)), "invalid deployment ID")
    require(bool(SHA.fullmatch(expected_sha)), "invalid expected SHA")
    require(expected.get("revision")==expected_sha, "CI source manifest SHA drift")
    require(deployment.get("id")==deployment_id, "deployment ID drift")
    project=deployment.get("projectId") or (deployment.get("project") or {}).get("id")
    require(project==PROJECT_ID, "deployment project mismatch")
    require(deployment.get("teamId") in (None,TEAM_ID), "deployment team mismatch")
    state=deployment.get("readyState") or deployment.get("state")
    target=deployment.get("target")
    require(state=="READY" and target is None, "not a READY isolated Preview")
    meta=deployment.get("meta") or {}
    candidates=[
        meta.get("githubCommitSha"), meta.get("aa8_source_sha"),
        (deployment.get("gitSource") or {}).get("sha"),
    ]
    candidates=[x for x in candidates if x is not None]
    require(bool(candidates) and all(x==expected_sha for x in candidates),
            "deployment git/metadata source SHA mismatch")
    selected=select_deployed_previews(expected,tree)
    result=verify_deployment(selected,tree,deployed_revision=expected_sha,
                             state=state,target=target)
    return {
        "status":"PREVIEW_POSTDEPLOY_PASS",
        "checked_at":datetime.now(timezone.utc).isoformat(),
        "deployment_id":deployment_id,
        "team_id":TEAM_ID,"project_id":PROJECT_ID,
        "reviewed_sha":expected_sha,
        "reviewed_previews":sorted(selected["previews"]),
        "verified_required_files":result["files_checked"],
        "files_mismatch":[],"missing":[],
        "environment":"isolated_preview",
        "ceo_authenticated_browser_review":"NOT_ATTESTED",
        "production_release":"HOLD",
    }


def main()->int:
    a=argparse.ArgumentParser()
    a.add_argument("--deployment-id",required=True)
    a.add_argument("--expected-sha",required=True)
    a.add_argument("--manifest",type=Path,required=True)
    a.add_argument("--evidence",type=Path)
    opts=a.parse_args()
    try:
        require(bool(DEPLOY.fullmatch(opts.deployment_id)), "invalid deployment ID")
        require(bool(SHA.fullmatch(opts.expected_sha)), "invalid SHA")
        require(opts.manifest.is_file(), "existing CI manifest missing")
        expected=json.loads(opts.manifest.read_text("utf-8"))
        require(expected.get("revision")==opts.expected_sha, "CI manifest does not bind expected SHA")
        token=os.environ.get("VERCEL_TOKEN","")
        require(bool(token), "protected VERCEL_TOKEN missing; configure in CI secrets")
        deploy=api_json("/v13/deployments/"+opts.deployment_id,token)
        tree=api_json("/v6/deployments/"+opts.deployment_id+"/files",token)
        report=audit_postdeploy(expected,deploy,tree,opts.deployment_id,opts.expected_sha)
        if opts.evidence:
            opts.evidence.parent.mkdir(parents=True,exist_ok=True)
            opts.evidence.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n","utf-8")
        print(json.dumps(report,ensure_ascii=False))
        return 0
    except (ValueError,OSError,KeyError,TypeError,json.JSONDecodeError) as exc:
        # Failure is a red gate; NEVER print credentials, raw responses or
        # create a fake PASS artifact.
        print(json.dumps({"status":"PREVIEW_POSTDEPLOY_HOLD",
                          "reason":str(exc).splitlines()[0],
                          "production_release":"HOLD"},ensure_ascii=False))
        return 2


if __name__=="__main__":
    raise SystemExit(main())
