"""Autofix safety: exact PR/HEAD, max 3, source-only patch, never production."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from factory_autofix_policy import preflight,validate_patch,attempt_count
SHA="403020c3c82e3e493ef19b8165231df2249cbaec"
BASE={"pr":173,"sha":SHA,"branch":"feat/x2-series-factory-pilot-20261109",
      "actor":"2airadmin8","scope":"PRODUCT","history":"","repo":"2airadmin8/aa8-Robotic"}
def patch(path="scripts/x2_example.py",new_line="    return a + b"):
 return ("diff --git a/"+path+" b/"+path+"\n"
         "index 76d..65a 100644\n--- a/"+path+"\n+++ b/"+path+
         "\n@@ -1,3 +1,3 @@\n def add(a,b):\n-    return a-b\n+"+new_line+"\n").encode()
class TestAutofixPolicy(unittest.TestCase):
 def test_allowed_first_attempt(self):
  p=preflight(**BASE)
  self.assertEqual(p["attempt"],1);self.assertEqual(p["release"],"HOLD")
  self.assertEqual(p["status"],"READY_TO_PROPOSE_NOT_AUTHORIZED_TO_MERGE")
 def test_trusted_github_bot_only_after_exact_dispatch_gate(self):
  x=preflight(**(BASE|{"actor":"github-actions[bot]"}))
  self.assertEqual(x["release"],"HOLD")
 def test_attempt_2_3_allowed_4_denied(self):
  for n in (1,2):
   x=BASE|{"history":"AA8-AUTOFIX-ATTEMPT: "+str(n)}
   self.assertEqual(preflight(**x)["attempt"],n+1)
  with self.assertRaises(ValueError):
   preflight(**(BASE|{"history":"AA8-AUTOFIX-ATTEMPT: 3"}))
 def test_untrusted_actor_fork_and_main_denied(self):
  for kw in [{"actor":"evil"},{"repo":"other/repo"},{"branch":"main"},
             {"branch":"feat/../../bad"},{"sha":"bad"},{"scope":"NO_PRODUCT_SCOPE"}]:
   with self.subTest(kw=kw),self.assertRaises(ValueError):
    preflight(**(BASE|kw))
 def test_valid_narrow_patch(self):
  v=validate_patch(patch())
  self.assertEqual(v["files"],["scripts/x2_example.py"])
  self.assertEqual(v["added"],1);self.assertEqual(v["deleted"],1)
 def test_bad_paths_and_workflows_denied(self):
  for path in (".github/workflows/ci.yml","data/products.json","scripts/.env",
               "tests/../../secret.py","assets/img/cat.png","scripts/factory_autofix_policy.py"):
   with self.subTest(path=path),self.assertRaises(ValueError):
    validate_patch(patch(path))
 def test_patch_header_cannot_hide_protected_target(self):
  malicious=patch().replace(b"--- a/scripts/x2_example.py",b"--- a/.github/workflows/pages.yml")
  with self.assertRaises(ValueError): validate_patch(malicious)
  malicious=patch().replace(b"+++ b/scripts/x2_example.py",b"+++ b/data/products.json")
  with self.assertRaises(ValueError): validate_patch(malicious)
 def test_symlink_new_file_rejected(self):
  candidate=(b"diff --git a/tests/symlink.py b/tests/symlink.py\n"
   b"new file mode 120000\n--- /dev/null\n+++ b/tests/symlink.py\n@@ -0,0 +1 @@\n+/etc/passwd\n")
  with self.assertRaises(ValueError):validate_patch(candidate)
 def test_deletions_binary_and_renames_denied(self):
  for patchtext in (b"deleted file mode 100644",b"GIT binary patch",b"rename from scripts/a.py"):
   with self.subTest(patch=patchtext),self.assertRaises(ValueError):
    validate_patch(patch()+patchtext)
 def test_bad_patch_size_and_no_change(self):
  with self.assertRaises(ValueError):validate_patch(b"")
  with self.assertRaises(ValueError):validate_patch(b"x"*120001)
  with self.assertRaises(ValueError):validate_patch(b"this is not a diff")
 def test_unbounded_line_growth_denied(self):
  payload=("diff --git a/tests/a.py b/tests/a.py\n--- a/tests/a.py\n+++ b/tests/a.py\n@@ -1 +1,301 @@\n"+
           "+line\n"*301).encode()
  with self.assertRaises(ValueError):validate_patch(payload)
 def test_nonmonotonic_repair_history_denied(self):
  with self.assertRaises(ValueError):
   attempt_count("AA8-AUTOFIX-ATTEMPT: 1\nAA8-AUTOFIX-ATTEMPT: 2")
if __name__=="__main__":unittest.main()
