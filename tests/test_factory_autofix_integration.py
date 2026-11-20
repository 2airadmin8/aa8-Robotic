"""Real isolated Git apply/commit regression; deterministic stub, NOT a successful AI call."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from factory_autofix_policy import validate_patch,attempt_count,preflight

def git(root,*args):
 p=subprocess.run(['git','-C',str(root),*args],capture_output=True,text=True,encoding='utf8')
 if p.returncode:
  raise AssertionError('git failed '+repr(args)+' stdout='+p.stdout[-350:]+' stderr='+p.stderr[-350:])
 return p.stdout.strip()
class TestIsolatedAutofixGit(unittest.TestCase):
 def test_failed_test_then_validated_patch_then_local_commit(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   (root/'scripts').mkdir()
   (root/'tests').mkdir()
   src=root/'scripts/math_engine.py'
   src.write_bytes(b'def add(a,b):\n    return a-b\n')
   (root/'tests/test_math_engine.py').write_text(
     'import unittest\nfrom scripts.math_engine import add\n'
     'class TestMath(unittest.TestCase):\n'
     ' def test_add(self): self.assertEqual(add(2,3),5)\n',encoding='utf8')
   git(root,'init','-q')
   git(root,'config','core.autocrlf','false')
   git(root,'add','scripts/math_engine.py','tests/test_math_engine.py')
   git(root,'-c','user.name=AA8-QA','-c','user.email=qa@example.invalid',
       'commit','-qm','isolated failing baseline')
   before=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_*.py','-q'],
                         cwd=root,capture_output=True,text=True)
   self.assertNotEqual(before.returncode,0)
   self.assertIn('-1 != 5',before.stderr)
   # Deterministic repair stub verifies orchestration only; no AI success is implied.
   src.write_bytes(b'def add(a,b):\n    return a+b\n')
   patch=subprocess.check_output(['git','-C',str(root),'diff','--binary','HEAD'])
   guard=validate_patch(patch)
   self.assertEqual(guard['files'],['scripts/math_engine.py'])
   git(root,'restore','--','scripts/math_engine.py')
   patchfile=root/'validated-fix.patch'
   patchfile.write_bytes(patch)
   git(root,'apply','--check',str(patchfile))
   git(root,'apply','--index',str(patchfile))
   after=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_*.py','-q'],
                        cwd=root,capture_output=True,text=True)
   self.assertEqual(after.returncode,0,after.stderr)
   git(root,'diff','--cached','--check')
   git(root,'-c','user.name=AA8-QA','-c','user.email=qa@example.invalid','commit',
       '-qm','isolated bounded repair','-m','AA8-AUTOFIX-ATTEMPT: 1')
   self.assertEqual(attempt_count(git(root,'log','-n','30','--format=%B')),1)
   p=preflight(pr=173,sha='403020c3c82e3e493ef19b8165231df2249cbaec',
               branch='feat/x2-series-factory-pilot-20261109',
               actor='2airadmin8',scope='PRODUCT',repo='2airadmin8/aa8-Robotic',
               history=git(root,'log','-n','30','--format=%B'))
   self.assertEqual(p['attempt'],2)
 def test_malicious_pages_patch_is_blocked(self):
  bad=(b'diff --git a/.github/workflows/pages.yml b/.github/workflows/pages.yml\n'
       b'--- a/.github/workflows/pages.yml\n+++ b/.github/workflows/pages.yml\n'
       b'@@ -1 +1 @@\n-on: workflow_dispatch\n+on: push\n')
  with self.assertRaises(ValueError):
   validate_patch(bad)
if __name__=='__main__':unittest.main()
