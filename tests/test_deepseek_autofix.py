"""DeepSeek-only AI proposal tests; all remote API responses are mocked."""
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from deepseek_factory_autofix import (
    ENDPOINT, ALLOWED_MODELS, extract_edits, apply_validated_edits,
    clean_failure, request_deepseek, propose, get_changed_files, collect_source,
)
from factory_autofix_policy import validate_path, validate_patch

class FakeResponse:
    status=200
    def __init__(self, body):self.body=body
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self,limit):return self.body

class TestDeepSeekAutofix(unittest.TestCase):
    def test_model_ids_and_endpoint_only_deepseek(self):
        self.assertEqual(ENDPOINT,"https://api.deepseek.com/chat/completions")
        self.assertEqual(ALLOWED_MODELS,{"deepseek-v4-pro","deepseek-flash"})
        with self.assertRaises(ValueError):
            request_deepseek([],"","deepseek-v4-pro")
        with self.assertRaises(ValueError):
            request_deepseek([],"key","deepseek-chat")
        with self.assertRaises(ValueError):
            request_deepseek([],"key","deepseek-flash",endpoint="https://api.openai.com")
    def test_mock_api_uses_deepseek_provider_without_openai_token(self):
        content='{"edits":[{"path":"tests/example.py","find":"x=1","replace":"x=2"}]}'
        fake=json.dumps({"choices":[{"finish_reason":"stop",
                                     "message":{"content":content}}]}).encode()
        def intercept(req,timeout):
            self.assertEqual(req.full_url,ENDPOINT)
            self.assertEqual(req.get_header("Authorization"),"Bearer test-DEEPSEEK-key")
            payload=json.loads(req.data)
            self.assertEqual(payload["model"],"deepseek-v4-pro")
            self.assertEqual(payload["response_format"],{"type":"json_object"})
            return FakeResponse(fake)
        with patch("urllib.request.urlopen",side_effect=intercept):
            result=request_deepseek([{"role":"user","content":"test"}],
                                    "test-DEEPSEEK-key","deepseek-v4-pro")
        self.assertEqual(result,content)
    def test_scrub_failure_text(self):
        self.assertNotIn("gho_",clean_failure("FAILED Authorization: Bearer foo gho_12345678901234567890"))
        self.assertNotIn("sk-secret",clean_failure("ERROR key sk-secret01234567890"))
    def test_reject_out_of_scope_duplicate_and_empty_edit(self):
        allow=["tests/example.py"]
        for body in (
            '{"edits":[]}',
            '{"edits":[{"path":".github/workflows/pages.yml","find":"x","replace":"y"}]}',
            '{"edits":[{"path":"tests/example.py","find":"","replace":"y"}]}',
            '{"edits":[{"path":"tests/example.py","find":"x","replace":"y"},'
            '{"path":"tests/example.py","find":"a","replace":"b"}]}'
        ):
            with self.subTest(body=body),self.assertRaises((ValueError,TypeError)):
                extract_edits(body,allow)
    def test_mock_edits_create_bounded_git_patch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"tests").mkdir()
            file=root/"tests/example.py"
            file.write_text("def add(a,b):\n    return a-b\n","utf8")
            src=[{"path":"tests/example.py","text":file.read_text("utf8")}]
            edits=extract_edits('{"edits":[{"path":"tests/example.py",'
                                '"find":"return a-b","replace":"return a+b"}]}',
                                ["tests/example.py"])
            changed=apply_validated_edits(root,src,edits)
            self.assertEqual(changed,["tests/example.py"])
            self.assertIn("return a+b",file.read_text("utf8"))
    def test_real_git_patch_is_persisted_before_separate_job(self):
        import subprocess
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"tests").mkdir()
            target=root/"tests/test_factory_autofix_live_probe.py"
            target.write_bytes(b"def add(a,b):\n    return a+b\n")
            def git(*args):
                return subprocess.check_output(["git","-C",str(root),*args],text=True).strip()
            git("init","-q")
            git("config","user.name","QA")
            git("config","user.email","qa@example.invalid")
            git("add","tests/test_factory_autofix_live_probe.py")
            git("commit","-qm","passing baseline")
            base=git("rev-parse","HEAD")
            target.write_bytes(b"def add(a,b):\n    return a-b\n")
            git("add","tests/test_factory_autofix_live_probe.py")
            git("commit","-qm","controlled failing code")
            gate={"state":"RETURN_TO_DEV","release":"HOLD","blocking_gate":"CI",
                  "pr":173,"head_sha":git("rev-parse","HEAD"),
                  "ci_outcomes":{"regression":"failure"}}
            fixed=json.dumps({'edits':[{'path':'tests/test_factory_autofix_live_probe.py','find':'return a-b','replace':'return a+b'}]})
            dest=root/"proposal.patch"
            with patch("deepseek_factory_autofix.request_deepseek",return_value=fixed):
                result=propose(root,base,gate,
                               "FAIL: test in test_factory_autofix_live_probe.py",
                               "mock-not-used","deepseek-flash",patch_out=dest)
            self.assertEqual(result["status"],"PROPOSED_FOR_INDEPENDENT_QA")
            self.assertTrue(dest.is_file())
            patch_bytes=dest.read_bytes()
            self.assertIn(b"+    return a+b",patch_bytes)
            from factory_autofix_policy import validate_patch
            self.assertEqual(validate_patch(patch_bytes)["files"],
                             ["tests/test_factory_autofix_live_probe.py"])
            self.assertIn("return a+b",target.read_text("utf8"))
    def test_no_deepseek_key_fails_closed(self):
        with self.assertRaises(ValueError):
            request_deepseek([],"","deepseek-v4-pro")
    def test_guard_denies_editing_own_engine(self):
        with self.assertRaises(ValueError):
            validate_path("scripts/deepseek_factory_autofix.py")
    def test_many_changed_files_need_a_specific_failing_filename(self):
        from unittest.mock import patch
        class R:
            returncode=0
            stdout="".join("tests/test_probe_%s.py\n" % i for i in range(12))
        class F:
            def is_file(self): return True
        with patch("subprocess.run",return_value=R()), patch.object(Path,"is_file",return_value=True):
            with patch.dict("os.environ",{"AA8_AUTOFIX_FAILURE_LOG":"FAIL: test in test_probe_7.py"}):
                files=get_changed_files(ROOT,"f"*40)
                self.assertEqual(files,["tests/test_probe_7.py"])
            with patch.dict("os.environ",{"AA8_AUTOFIX_FAILURE_LOG":""}):
                with self.assertRaises(ValueError):get_changed_files(ROOT,"f"*40)

    def test_bad_gate_prevents_api_call(self):
        with patch("deepseek_factory_autofix.request_deepseek") as called:
            with self.assertRaises(ValueError):
                propose(ROOT,"f"*40,{"state":"WAIT_DESIGN_QA","release":"HOLD",
                                     "blocking_gate":"G2"}, "FAIL", "testkey", "deepseek-v4-pro")
            called.assert_not_called()
if __name__=="__main__":unittest.main()
