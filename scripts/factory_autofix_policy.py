#!/usr/bin/env python3
"""Strict guard for existing-PR Codex autofix. No network, credentials, merge or deployment."""
from __future__ import annotations
import argparse
import json
from pathlib import Path, PurePosixPath
import re
import sys

SHA_RE=re.compile(r"^[a-f0-9]{40}$")
BRANCH_RE=re.compile(r"^(?:feat|fix|draft|chore)/[a-zA-Z0-9._/-]+$")
TRAILER_RE=re.compile(r"(?im)^AA8-AUTOFIX-ATTEMPT:\s*(\d+)\s*$")
DIFF_RE=re.compile(r"^diff --git a/([a-zA-Z0-9_./-]+) b/([a-zA-Z0-9_./-]+)$")
MAX_ATTEMPTS=3
MAX_FILES=8
MAX_LINES=300
MAX_PATCH_BYTES=120000
PREFIXES=("scripts/","tests/","products/","assets/css/","assets/js/")
PROTECTED=("scripts/factory_autofix_policy.py",".github/","data/","secrets/","assets/js/analytics-events.js")
SUFFIXES=(".py",".js",".css",".html",".json",".md",".txt")
def check(condition:bool,message:str):
    if not condition: raise ValueError(message)

def attempt_count(log_messages:str)->int:
    # Sum explicit repair commit trailers in the PR history; no silent retry reset.
    numbers=[int(x) for x in TRAILER_RE.findall(log_messages)]
    check(not numbers or all(1<=n<=MAX_ATTEMPTS for n in numbers),"Malformed or over-limit repair marker")
    check(numbers == sorted(numbers,reverse=True),"Non-monotonic repair history") if len(numbers)>1 else None
    return max(numbers,default=0)

def preflight(*,pr:int,sha:str,branch:str,actor:str,scope:str,history:str,repo:str)->dict:
    check(repo=="2airadmin8/aa8-Robotic","Unexpected repository")
    check(isinstance(pr,int) and pr>0,"Invalid PR")
    check(bool(SHA_RE.fullmatch(sha)),"Exact HEAD SHA is required")
    check(bool(BRANCH_RE.fullmatch(branch)) and ".." not in branch and "//" not in branch,
          "Non-feature or unsafe branch")
    check(actor in {"2airadmin8","PAI-airadmin8","github-actions[bot]"},"Untrusted actor")
    check(scope in {"PRODUCT","MULTI_PRODUCT","GLOBAL_FACTORY"},"No eligible Factory scope")
    count=attempt_count(history)
    check(count < MAX_ATTEMPTS, "Repair attempt limit reached")
    return {"schema_version":"factory-ai-autofix-preflight-v1",
            "pr":pr,"head_sha":sha,"branch":branch,"actor":actor,
            "attempt":count+1,"max_attempts":MAX_ATTEMPTS,
            "status":"READY_TO_PROPOSE_NOT_AUTHORIZED_TO_MERGE",
            "release":"HOLD","allowed_paths":list(PREFIXES),
            "prohibited":"workflow/main/master/production/CRM writes"}

def validate_path(path:str)->None:
    check(bool(path) and not path.startswith("/") and not path.endswith("/"),"Invalid path")
    check(not any(x in path for x in ["\\",":","//","../","/..","\x00"]),"Traversal or unsafe path")
    check(all(part not in ("..",".","") for part in PurePosixPath(path).parts),"Unsafe path segment")
    check(re.fullmatch(r"[a-zA-Z0-9_./-]+",path) is not None,"Path has unsupported characters")
    check(any(path.startswith(prefix) for prefix in PREFIXES),"Unapproved changed-file directory")
    check(not any(path.startswith(prefix) for prefix in PROTECTED),"Protected file changed")
    check(path.endswith(SUFFIXES),"Binary/non-source extension rejected")

def validate_patch(raw:bytes)->dict:
    check(0<len(raw)<=MAX_PATCH_BYTES,"Empty or excessive patch")
    text=raw.decode("utf-8","strict")
    check(not any(x in text for x in ["GIT binary patch","Binary files ","rename from ","rename to ","deleted file mode","old mode ","new mode ","Submodule "]),"Binary/rename/delete/mode change forbidden")
    changed=[];plus=minus=0;current=None
    for line in text.splitlines():
        if line.startswith("diff --git "):
            m=DIFF_RE.fullmatch(line)
            check(m is not None and m.group(1)==m.group(2),"Diff path mismatch")
            current=m.group(1)
            validate_path(current)
            changed.append(current)
        elif line.startswith("--- "):
            check(current is not None, "Source header without diff")
            check(line in ("--- /dev/null","--- a/"+current),"Patch source path mismatch")
            if line=="--- /dev/null":
                check(current.startswith("tests/"),"New files only under tests/")
        elif line.startswith("+++ "):
            check(current is not None and line=="+++ b/"+current,"Patch target path mismatch")
        elif line.startswith("new file mode "):
            check(line=="new file mode 100644" and current and current.startswith("tests/"),
                  "Only regular new regression tests permitted")
        elif line.startswith("index ") or line.startswith("@@ "):
            pass
        elif line.startswith("+") and not line.startswith("+++"):
            plus+=1
        elif line.startswith("-") and not line.startswith("---"):
            minus+=1
    check(changed and len(set(changed))==len(changed) and len(changed)<=MAX_FILES,"Invalid file count")
    check(plus+minus<=MAX_LINES,"Excessive patch lines")
    return {"schema_version":"factory-ai-autofix-patch-v1","status":"PATCH_ACCEPTED_FOR_ISOLATED_TEST",
            "files":changed,"added":plus,"deleted":minus,"merge":False,"release":"HOLD"}

def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="action",required=True)
    a=sub.add_parser("preflight")
    for key in ("sha","branch","actor","scope","repo"):
        a.add_argument("--"+key,required=True)
    a.add_argument("--pr",type=int,required=True)
    a.add_argument("--history-file",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    b=sub.add_parser("patch-check")
    b.add_argument("--patch",type=Path,required=True)
    b.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    try:
        if args.action=="preflight":
            obj=preflight(pr=args.pr,sha=args.sha,branch=args.branch,actor=args.actor,
                          scope=args.scope,repo=args.repo,history=args.history_file.read_text("utf8"))
        else:
            obj=validate_patch(args.patch.read_bytes())
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print(json.dumps({"status":obj["status"],"release":"HOLD"}))
    except (ValueError,OSError,UnicodeError) as exc:
        print("AUTOFIX_HOLD: "+str(exc),file=sys.stderr)
        return 2
    return 0
if __name__=="__main__":
    sys.exit(main())
