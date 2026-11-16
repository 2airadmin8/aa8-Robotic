"""Post-deployment readback from Vercel is mandatory, SHA-bound and fail closed."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import preview_postdeploy_bridge as gate
from verify_preview_bundle import SCHEMA


def provider_tree(file_map):
    root={}
    for path,sha in file_map.items():
        node=root
        segments=path.split("/")
        for seg in segments[:-1]:
            node=node.setdefault(seg,{})
        node[segments[-1]]=sha
    def walk(node):
        return [{"name":k,"type":"directory","children":walk(v)}
                if isinstance(v,dict) else {"name":k,"type":"file","uid":v}
                for k,v in node.items()]
    return walk(root)


class RealPostDeployBridge(unittest.TestCase):
    def setUp(self):
        self.sha="a"*40
        self.did="dpl_ABC12345"
        self.manifest={
            "schema":SCHEMA,"revision":self.sha,
            "previews":{
                "a2-factory-preview.html":"b"*40,
                "x2-pilot-preview.html":"c"*40
            },
            "per_preview_assets":{
                "a2-factory-preview.html":["assets/img/airadmin8-robotics-logo-footer.svg",
                                           "assets/css/shared-layout.css"],
                "x2-pilot-preview.html":["assets/img/airadmin8-robotics-logo-footer.svg",
                                         "assets/img/x2-prototype.webp"]
            },
            "assets":{
                "assets/img/airadmin8-robotics-logo-footer.svg":{"sha1":"d"*40,"size":42},
                "assets/css/shared-layout.css":{"sha1":"e"*40,"size":128},
                "assets/img/x2-prototype.webp":{"sha1":"f"*40,"size":512}
            }
        }
        self.deploy={
            "id":self.did,"projectId":gate.PROJECT_ID,"teamId":gate.TEAM_ID,
            "readyState":"READY","target":None,
            "meta":{"githubCommitSha":self.sha}
        }
        self.files=provider_tree({
            "a2-factory-preview.html":"b"*40,
            "index.html":"b"*40,
            "assets/img/airadmin8-robotics-logo-footer.svg":"d"*40,
            "assets/css/shared-layout.css":"e"*40
        })

    def test_one_product_validated_against_full_ci_many_product_manifest(self):
        result=gate.audit_postdeploy(self.manifest,self.deploy,self.files,
                                     self.did,self.sha)
        self.assertEqual(result["status"],"PREVIEW_POSTDEPLOY_PASS")
        self.assertEqual(result["reviewed_previews"],["a2-factory-preview.html"])
        self.assertEqual(result["verified_required_files"],3)
        self.assertEqual(result["production_release"],"HOLD")

    def test_missing_logo_and_stale_css_are_hard_hold(self):
        mutated=deepcopy(self.files)
        images=next(x for x in next(y for y in mutated if y["name"]=="assets")["children"]
                    if x["name"]=="img")
        images["children"]=[]
        with self.assertRaisesRegex(ValueError,"missing=.*footer"):
            gate.audit_postdeploy(self.manifest,self.deploy,mutated,self.did,self.sha)
        mutated=deepcopy(self.files)
        css=next(x for x in next(y for y in mutated if y["name"]=="assets")["children"]
                 if x["name"]=="css")
        css["children"][0]["uid"]="0"*40
        with self.assertRaisesRegex(ValueError,"sha_mismatch=.*shared-layout"):
            gate.audit_postdeploy(self.manifest,self.deploy,mutated,self.did,self.sha)

    def test_source_project_team_or_production_drift_are_hold(self):
        for prop,val in [
            ("projectId","prj_bad"),("teamId","team_bad"),
            ("target","production"),("readyState","ERROR")]:
            with self.subTest(property=prop):
                changed=deepcopy(self.deploy);changed[prop]=val
                with self.assertRaisesRegex(ValueError,"PREVIEW_POSTDEPLOY_HOLD"):
                    gate.audit_postdeploy(self.manifest,changed,self.files,self.did,self.sha)
        for name,val in [("githubCommitSha","0"*40),("aa8_source_sha","0"*40)]:
            changed=deepcopy(self.deploy);changed["meta"][name]=val
            with self.subTest(metadata=name):
                with self.assertRaisesRegex(ValueError,"source SHA mismatch"):
                    gate.audit_postdeploy(self.manifest,changed,self.files,self.did,self.sha)
        with self.assertRaisesRegex(ValueError,"CI source manifest SHA drift"):
            gate.audit_postdeploy(self.manifest,self.deploy,self.files,self.did,"0"*40)

    def test_unregistered_deployment_preview_is_rejected(self):
        tree=provider_tree({"unknown-preview.html":"b"*40,
                            "assets/img/airadmin8-robotics-logo-footer.svg":"d"*40})
        with self.assertRaisesRegex(ValueError,"unregistered deployed Preview"):
            gate.audit_postdeploy(self.manifest,self.deploy,tree,self.did,self.sha)

    def test_git_deployment_real_runtime_sha_fallback_verified(self):
        from hashlib import sha1
        a2=b"<html>exact signed Preview</html>"
        logo=b"<svg>signed official footer</svg>"
        css=b"body{color:#111}"
        self.manifest["previews"]["a2-factory-preview.html"]=sha1(a2).hexdigest()
        self.manifest["assets"]["assets/img/airadmin8-robotics-logo-footer.svg"]["sha1"]=sha1(logo).hexdigest()
        self.manifest["assets"]["assets/css/shared-layout.css"]["sha1"]=sha1(css).hexdigest()
        self.manifest["per_preview_assets"].pop("x2-pilot-preview.html")
        self.manifest["previews"].pop("x2-pilot-preview.html")
        self.manifest["assets"].pop("assets/img/x2-prototype.webp")
        deploy={**self.deploy,"source":"git","url":"test-preview.vercel.app"}
        files={"a2-factory-preview.html":a2,
               "assets/img/airadmin8-robotics-logo-footer.svg":logo,
               "assets/css/shared-layout.css":css}
        seen=[]
        def retrieve(d,path,bypass):
            seen.append(path)
            self.assertEqual(bypass,"private-bypass")
            return files[path]
        proof=gate.audit_runtime_git(self.manifest,deploy,self.did,self.sha,
                                     "private-bypass",fetcher=retrieve)
        self.assertEqual(proof["status"],"PREVIEW_POSTDEPLOY_PASS")
        self.assertEqual(proof["method"],"LIVE_RUNTIME_SHA1_WITH_SSO_BYPASS")
        self.assertEqual(proof["verified_required_files"],3)
        self.assertEqual(sorted(seen),sorted(files))
        self.assertEqual(proof["ceo_authenticated_browser_review"],"NOT_ATTESTED")
        self.assertEqual(proof["production_release"],"HOLD")
        # A real broken Footer logo or stale CSS is always a hard hold.
        for file in ("assets/img/airadmin8-robotics-logo-footer.svg",
                     "assets/css/shared-layout.css"):
            wrong=dict(files);wrong[file]=b"wrong bytes"
            with self.subTest(file=file):
                with self.assertRaisesRegex(ValueError,"runtime file SHA mismatch"):
                    gate.audit_runtime_git(self.manifest,deploy,self.did,self.sha,
                        "private-bypass",fetcher=lambda _,p,b:wrong[p])

    def test_git_runtime_missing_auth_or_wrong_identity_hold(self):
        deploy={**self.deploy,"source":"git","url":"test-preview.vercel.app"}
        with self.assertRaisesRegex(ValueError,"BYPASS_SECRET missing"):
            gate.audit_runtime_git(self.manifest,deploy,self.did,self.sha,"")
        for key,value in (("target","production"),("projectId","other"),
                          ("readyState","ERROR"),("source","api")):
            with self.subTest(key=key):
                wrong={**deploy,key:value}
                with self.assertRaisesRegex(ValueError,"PREVIEW_POSTDEPLOY_HOLD"):
                    gate.audit_runtime_git(self.manifest,wrong,self.did,self.sha,
                        "private-bypass")
        with self.assertRaisesRegex(ValueError,"source SHA drift"):
            gate.audit_runtime_git(self.manifest,deploy,self.did,"0"*40,
                                   "private-bypass")

    def test_git_source_tree_404_uses_runtime_fallback_never_skips_verification(self):
        with tempfile.TemporaryDirectory() as d:
            manifest=Path(d)/"manifest.json"
            manifest.write_text(json.dumps(self.manifest),encoding="utf-8")
            deploy={**self.deploy,"source":"git","url":"test-preview.vercel.app"}
            with patch("sys.argv",["gate","--deployment-id",self.did,
                                   "--expected-sha",self.sha,"--manifest",str(manifest)]):
                with patch.dict("os.environ",{"VERCEL_TOKEN":"fake",
                    "VERCEL_AUTOMATION_BYPASS_SECRET":"private-bypass"}):
                    with patch.object(gate,"api_json",side_effect=[
                        deploy,gate.DeploymentSourceTreeUnavailable("no Git source file tree")]):
                        with patch.object(gate,"audit_runtime_git",return_value={
                            "status":"PREVIEW_POSTDEPLOY_PASS",
                            "production_release":"HOLD"}) as actual:
                            self.assertEqual(gate.main(),0)
                            self.assertEqual(actual.call_count,1)
                # With no SSO bypass secret, a 404 is a HARD HOLD.
                with patch.dict("os.environ",{"VERCEL_TOKEN":"fake"},clear=True):
                    with patch.object(gate,"api_json",side_effect=[
                        deploy,gate.DeploymentSourceTreeUnavailable("no Git source file tree")]):
                        self.assertEqual(gate.main(),2)

    def test_cli_missing_secret_refuses_without_network_or_false_pass(self):
        with tempfile.TemporaryDirectory() as d:
            manifest=Path(d)/"manifest.json"
            manifest.write_text(json.dumps(self.manifest),encoding="utf-8")
            with patch("sys.argv",["bridge","--deployment-id",self.did,
                                    "--expected-sha",self.sha,
                                    "--manifest",str(manifest)]):
                with patch.dict("os.environ",{},clear=True):
                    with patch.object(gate,"api_json",side_effect=AssertionError("network accessed")):
                        self.assertEqual(gate.main(),2)

class TrustedMainManifestOrderContract(unittest.TestCase):
    """Guard the exact CI-before-deployed-bytes sequence against regression."""

    def test_native_vercel_event_waits_for_complete_same_sha_ci(self):
        workflow=(ROOT/".github"/"workflows"/"ci.yml").read_text("utf-8")
        self.assertIn("Wait boundedly for SUCCESSFUL exact-SHA PR CI manifest",workflow)
        self.assertIn("for attempt in $(seq 1 24)",workflow)
        self.assertRegex(workflow, r"preview-postdeploy-readback:[\\s\\S]{0,500}timeout-minutes: 12")
        self.assertIn("if (( attempt < 24 )); then",workflow)
        self.assertIn('r.get("head_sha")==sha and r.get("event")=="pull_request"',workflow)
        self.assertIn('r.get("conclusion")=="success"',workflow)
        self.assertIn('(a.get("workflow_run") or {}).get("id") in valid_runs',workflow)
        self.assertIn('manifest.get("revision")!=os.environ["EXPECTED_SHA"]',workflow)
        self.assertIn("PREVIEW_POSTDEPLOY_HOLD: no SUCCESSFUL exact-HEAD",workflow)
        self.assertIn("runtime fallback only allowed for native Git deployments",
                      (ROOT/"scripts"/"preview_postdeploy_bridge.py").read_text("utf-8"))
        self.assertIn("Mark deployment verification failure as hard HOLD",workflow)
        self.assertIn("Mark exact verified commit only (after authenticated Vercel PASS)",workflow)


if __name__=="__main__":
    unittest.main()
