#!/usr/bin/env python3
"""One-time real DeepSeek repair of intentionally broken disposable Git repo.

Runs ONLY on GitHub-hosted isolated PR #173 proof job. No network to GitHub,
no actual Product Master changes, no remote Git push, no CRM, no publishing.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from deepseek_factory_autofix import propose

def run(cwd: Path,*argv:str,allow_fail:bool=False):
    p=subprocess.run(list(argv),cwd=cwd,capture_output=True,text=True,timeout=20,check=False)
    if p.returncode and not allow_fail:
        raise RuntimeError("Isolated step failed: "+argv[0]+" "+argv[1])
    return p

def pilot(output_dir:Path):
    key=os.environ.get("DEEPSEEK_API_KEY","")
    if not key:
        raise ValueError("DEEPSEEK_API_KEY_PAIHP missing")
    with tempfile.TemporaryDirectory(prefix="aa8-deepseek-pilot-") as td:
        root=Path(td)
        (root/"scripts").mkdir()
        (root/"tests").mkdir()
        source=root/"scripts/math_engine.py"
        tests=root/"tests/test_math_engine.py"
        source.write_text("def add(a,b):\n    return a+b\n",encoding="utf8")
        tests.write_text(
            "import unittest\nfrom scripts.math_engine import add\n"
            "class TestMath(unittest.TestCase):\n"
            " def test_add(self): self.assertEqual(add(2,3),5)\n",encoding="utf8")
        run(root,"git","init","-q")
        run(root,"git","config","user.name","AA8-Isolated-QA")
        run(root,"git","config","user.email","isolated-qa@example.invalid")
        run(root,"git","add","scripts/math_engine.py","tests/test_math_engine.py")
        run(root,"git","commit","-qm","safe passing baseline")
        base_sha=run(root,"git","rev-parse","HEAD").stdout.strip()
        run(root,sys.executable,"-B","-m","unittest","discover","-s","tests","-q")
        # Introduce a tiny, deliberate error in a separate local commit.
        source.write_text("def add(a,b):\n    return a-b\n",encoding="utf8")
        run(root,"git","add","scripts/math_engine.py")
        run(root,"git","commit","-qm","deliberately failing local test")
        before=run(root,sys.executable,"-B","-m","unittest","discover","-s","tests","-q",allow_fail=True)
        if before.returncode==0 or "FAIL" not in before.stderr:
            raise RuntimeError("Expected isolated failing test not reproduced")
        gate={
            "state":"RETURN_TO_DEV","release":"HOLD","blocking_gate":"CI",
            "pr":173,"head_sha":run(root,"git","rev-parse","HEAD").stdout.strip(),
            "ci_outcomes":{"regression":"failure"}
        }
        ai=propose(root,base_sha,gate,before.stderr,key,model="deepseek-flash")
        after=run(root,sys.executable,"-B","-m","unittest","discover","-s","tests","-q",allow_fail=True)
        if after.returncode!=0:
            raise RuntimeError("DeepSeek changed file but did not fix actual test")
        diff=run(root,"git","diff","--binary","HEAD").stdout
        if not diff or ai["files"]!=["scripts/math_engine.py"]:
            raise RuntimeError("Unexpected AI patch files")
        run(root,"git","diff","--check")
        (output_dir/"proposed-fix.diff").write_text(diff,encoding="utf8")
        run(root,"git","add","scripts/math_engine.py")
        run(root,"git","commit","-qm","isolated DeepSeek AI repair proof")
        report={
            "result":"PASS_REAL_DEEPSEEK_ISOLATED_REPAIR",
            "timestamp":datetime.now(timezone.utc).isoformat(),
            "model":"deepseek-flash",
            "provider":"DeepSeek",
            "failed_before":True,"passed_after":True,
            "changed_files":ai["files"],
            "isolated_local_commit":run(root,"git","rev-parse","HEAD").stdout.strip(),
            "patch_sha256":hashlib.sha256(diff.encode()).hexdigest(),
            "source_repo_write":False,
            "production_release":False,
            "business_CRM_write":False,
            "global_autofix_enabled":False,
            "safe_event":"github PR #173 dedicated proof job only"
        }
        (output_dir/"proof.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
        print("REAL_DEEPSEEK_ISOLATED_REPAIR_PASS; patched 1 temporary Python file, test PASS, no production writes")

def main():
    output=Path(sys.argv[1]) if len(sys.argv)>1 else Path("deepseek-isolated-evidence")
    output.mkdir(parents=True,exist_ok=True)
    try:
        pilot(output)
    except Exception as e:
        # Avoid printing input logs, response or credentials.
        print("REAL_DEEPSEEK_ISOLATED_REPAIR_HOLD: "+type(e).__name__+": "+str(e)[:150],file=sys.stderr)
        return 2
    return 0
if __name__=="__main__":
    raise SystemExit(main())
