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
from hashlib import sha1
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

from verify_preview_bundle import select_deployed_previews, verify_deployment

PROJECT_ID = "prj_vH6kcA1vFU6FPCm3skNdpudINkEh"
TEAM_ID = "team_xYXQL3tQXxLKFRUNOYVaMoYA"
API = "https://api.vercel.com"
SHA = re.compile(r"^[0-9a-f]{40}$")
DEPLOY = re.compile(r"^dpl_[A-Za-z0-9]+$")
MAX_JSON = 3_000_000
MAX_STATIC_FILE = 12_000_000


class DeploymentSourceTreeUnavailable(ValueError):
    """Git-linked Vercel deployments do not expose the API files-key tree."""



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
        if exc.code == 404 and path.endswith("/files"):
            raise DeploymentSourceTreeUnavailable(
                "PREVIEW_POSTDEPLOY_HOLD: Git deployment has no source Files API tree") from None
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


def runtime_file_bytes(deployment:dict, path:str, bypass_secret:str)->bytes:
    """Read the REAL deployed asset, not the Git source blob or SSO login.

    Vercel Git builds have no /v6/deployments/<id>/files manifest.  Only an
    authenticated, no-redirect request to the exact deployment hostname can
    prove which bytes the customer would actually receive. A missing bypass
    secret is always HOLD; never disable SSO or follow redirects.
    """
    require(bool(bypass_secret), "VERCEL_AUTOMATION_BYPASS_SECRET missing")
    host=str(deployment.get("url") or "")
    url=urlsplit("https://"+host)
    require(url.hostname is not None and url.hostname.endswith(".vercel.app")
            and host == url.hostname and url.port is None
            and not url.username and not url.password,
            "untrusted Vercel runtime hostname")
    require(isinstance(path,str) and path and not path.startswith("/")
            and "\\" not in path and "?" not in path and "#" not in path
            and all(part not in ("", ".", "..") for part in path.split("/")),
            "unsafe deployed asset path")
    req=Request("https://"+host+"/"+path, headers={
        "User-Agent":"AirAdmin8-ExactSHA-Postdeploy/1",
        "X-Vercel-Protection-Bypass":bypass_secret,
        "Accept-Encoding":"identity",
        "Cache-Control":"no-cache",
    })
    try:
        with build_opener(NoRedirect).open(req,timeout=15) as response:
            require(response.status==200,"runtime asset HTTP not 200: "+path)
            require(response.headers.get("Content-Encoding","identity")=="identity",
                    "deployed asset compressed inconsistently: "+path)
            blob=response.read(MAX_STATIC_FILE+1)
            require(len(blob)<=MAX_STATIC_FILE,
                    "deployed asset unexpectedly large: "+path)
            return blob
    except HTTPError as exc:
        raise ValueError("PREVIEW_POSTDEPLOY_HOLD: deployed asset HTTP "+
                         str(exc.code)+" for "+path) from None
    except (URLError,TimeoutError,UnicodeError):
        raise ValueError("PREVIEW_POSTDEPLOY_HOLD: deployed asset unreachable: "+path) from None


def audit_runtime_git(expected:dict,deployment:dict,deployment_id:str,
                      expected_sha:str,bypass_secret:str,fetcher=None)->dict:
    """Validate every registered generated Preview and every byte it needs.

    Git source file trees are unavailable in Vercel; use runtime SHA1 instead,
    with mandatory SSO bypass. A source commit match alone is NOT acceptance.
    """
    require(bool(SHA.fullmatch(expected_sha))
            and expected.get("revision")==expected_sha, "source SHA drift")
    require(bool(DEPLOY.fullmatch(deployment_id))
            and deployment.get("id")==deployment_id, "deployment ID drift")
    project=deployment.get("projectId") or (deployment.get("project") or {}).get("id")
    require(project==PROJECT_ID and deployment.get("teamId") in (None,TEAM_ID),
            "wrong Vercel team/project")
    require(deployment.get("readyState",deployment.get("state"))=="READY"
            and deployment.get("target") is None, "not isolated READY preview")
    meta=deployment.get("meta") or {}
    matches=[v for v in [meta.get("githubCommitSha"),meta.get("aa8_source_sha"),
                         (deployment.get("gitSource") or {}).get("sha")] if v is not None]
    require(bool(matches) and all(v==expected_sha for v in matches),
            "deployment Git source SHA mismatch")
    require(deployment.get("source")=="git",
            "runtime fallback only allowed for native Git deployments")
    require(bool(bypass_secret), "VERCEL_AUTOMATION_BYPASS_SECRET missing")
    previews=expected.get("previews")
    relations=expected.get("per_preview_assets")
    assets=expected.get("assets")
    require(isinstance(previews,dict) and isinstance(relations,dict)
            and isinstance(assets,dict), "incomplete CI bundle contract")
    # The synthetic factory-qa file is not a real product Preview; actual
    # registered draft product artifacts have the -preview.html suffix.
    pages=sorted(name for name in previews if name.endswith("-preview.html"))
    require(bool(pages) and len(pages)<=100,"no bounded registered draft previews")
    required={name:previews[name] for name in pages}
    for name in pages:
        needs=relations.get(name)
        require(isinstance(needs,list) and bool(needs),
                "missing linked assets for "+name)
        for path in needs:
            require(path in assets, "undeclared source asset "+str(path))
            required[path]=assets[path]["sha1"]
    require(len(required)<=500,"too many deployed bytes to audit")
    get_bytes=fetcher or runtime_file_bytes
    for path,digest in sorted(required.items()):
        require(isinstance(digest,str) and bool(SHA.fullmatch(digest)),
                "invalid expected source file SHA")
        blob=get_bytes(deployment,path,bypass_secret)
        require(isinstance(blob,bytes) and sha1(blob).hexdigest()==digest,
                "runtime file SHA mismatch: "+path)
    return {
        "status":"PREVIEW_POSTDEPLOY_PASS",
        "method":"LIVE_RUNTIME_SHA1_WITH_SSO_BYPASS",
        "checked_at":datetime.now(timezone.utc).isoformat(),
        "deployment_id":deployment_id,"project_id":PROJECT_ID,
        "team_id":TEAM_ID,"reviewed_sha":expected_sha,
        "reviewed_previews":pages,"verified_required_files":len(required),
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
        try:
            tree=api_json("/v6/deployments/"+opts.deployment_id+"/files",token)
        except DeploymentSourceTreeUnavailable:
            # Native Vercel Git deploy: source-tree API 404 is normal, not a
            # reason to silently skip postdeploy verification. Read actual
            # protected runtime bytes and compare every SHA instead.
            report=audit_runtime_git(expected,deploy,opts.deployment_id,
                    opts.expected_sha,os.environ.get("VERCEL_AUTOMATION_BYPASS_SECRET",""))
        else:
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
