"""Guard that DeepSeek-only patch proposal cannot bypass PR/QA/production gates."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WF=(ROOT/'.github/workflows/ci.yml').read_text('utf8')
POLICY=(ROOT/'scripts/factory_autofix_policy.py').read_text('utf8')
def job(name):
 import re
 m=re.search(r"(?m)^  "+re.escape(name)+r":\s*$",WF)
 assert m, name
 start=m.end()
 n=re.search(r"(?m)^  [a-z][a-z0-9-]*:\s*$",WF[start:])
 return WF[start:start+n.start() if n else len(WF)]
class TestAutofixWorkflow(unittest.TestCase):
 def test_jobs_and_gates(self):
  for n in ('build-and-verify','separate-technical-qa','ai-autofix-propose',
            'ai-autofix-validate','ai-autofix-commit'):
   self.assertIn('\n  '+n+':\n',WF)
  propose=job('ai-autofix-propose')
  self.assertIn("vars.AA8_FACTORY_AUTOFIX_ENABLED == 'true'",propose)
  self.assertIn("needs.build-and-verify.result == 'failure'",propose)
  self.assertIn("github.event.pull_request.draft == true",propose)
  self.assertIn("github.event.pull_request.head.repo.full_name == github.repository",propose)
 def test_deepseek_key_only_in_unprivileged_proposal(self):
  propose=job('ai-autofix-propose')
  val=job('ai-autofix-validate')
  writer=job('ai-autofix-commit')
  self.assertEqual(WF.count('secrets.DEEPSEEK_API_KEY_PAIHP'),3)  # probe, read-only proposer, isolated pilot
  self.assertNotIn('secrets.DEEPSEEK_API_KEY }}',WF)
  self.assertNotIn('secrets.OPENAI_API_KEY',WF)
  self.assertNotIn('openai/codex-action@',WF)
  self.assertIn("DeepSeek API - propose minimal source repair",propose)
  self.assertIn("scripts/deepseek_factory_autofix.py",propose)
  self.assertIn("DEEPSEEK_AUTOFIX_MODEL: deepseek-v4-pro",propose)
  self.assertIn("DEEPSEEK_API_KEY:",propose)
  self.assertIn('contents: read',propose)
  self.assertNotIn('contents: write',propose)
  self.assertIn('persist-credentials: false',propose)
  self.assertNotIn('secrets.DEEPSEEK_API_KEY',val+writer)
  self.assertIn('contents: read',val)
  self.assertNotIn('contents: write',val)
  self.assertIn('contents: write',writer)
 def test_deepseek_api_smoke_is_limited_to_same_repo_draft_pr(self):
  # Pure standard-library check: GitHub's Python runner has no PyYAML.
  start=WF.index('      - name: DeepSeek PAIHP secret real API smoke')
  end=WF.index('      - name: Regression gate for manual-only production release',start)
  step=WF[start:end]
  self.assertIn('github.event.pull_request.number == 173',step)
  self.assertIn('github.event.pull_request.draft == true',step)
  self.assertIn('head.repo.full_name == github.repository',step)
  self.assertIn('DEEPSEEK_API_KEY: '+chr(36)+'{{ secrets.DEEPSEEK_API_KEY_PAIHP }}',step)
  self.assertIn('https://api.deepseek.com/models',step)
  self.assertIn('https://api.deepseek.com/chat/completions',step)
  self.assertNotIn('api.openai.com',step)

 def test_real_deepseek_repair_proof_is_separate_readonly_runner(self):
  proof=job('deepseek-isolated-repair-proof')
  self.assertIn('github.event.pull_request.number == 173',proof)
  self.assertIn('github.event.pull_request.draft == true',proof)
  self.assertIn('needs.build-and-verify.result == ',proof)
  self.assertIn('contents: read',proof)
  self.assertIn('persist-credentials: false',proof)
  self.assertIn('tests/deepseek_real_isolated_pilot.py',proof)
  self.assertIn('secrets.DEEPSEEK_API_KEY_PAIHP',proof)
  self.assertNotIn('contents: write',proof)
  self.assertNotIn('git push',proof)
  self.assertNotIn('pages.yml',proof)

 def test_original_pr_sha_guard_and_bounded_writer(self):
  writer=job('ai-autofix-commit')
  self.assertIn("p['head']['sha'] != os.environ['EXPECTED_SHA']",writer)
  self.assertIn("p['state'] != 'open' or not p['draft']",writer)
  self.assertIn('git push origin "HEAD:refs/heads/$branch"',writer)
  self.assertNotIn('--force',writer)
  self.assertIn('gh workflow run ci.yml',writer)
  self.assertIn('AA8-AUTOFIX-ATTEMPT:',writer)
  self.assertNotIn('pages.yml',writer)
  self.assertIn('MAX_ATTEMPTS=3',POLICY)
  self.assertIn('MAX_FILES=8',POLICY)
  self.assertIn('MAX_LINES=300',POLICY)
 def test_dispatch_identity_and_separate_technical_qa(self):
  self.assertIn("autofix_pr:",WF)
  self.assertIn("autofix_head:",WF)
  self.assertIn("autofix_base:",WF)
  self.assertIn('test "$GITHUB_SHA" = "$EXPECTED_HEAD"',WF)
  self.assertIn("p['head']['ref']!=os.environ['GITHUB_REF_NAME']",WF)
  self.assertIn('separate-technical-qa:',WF)
  self.assertIn('factory-separate-qa-',WF)
 def test_existing_pages_workflow_is_manual_only(self):
  x=(ROOT/'.github/workflows/pages.yml').read_text('utf8')
  self.assertIn('workflow_dispatch:',x)
  self.assertNotIn('on:\n  push:',x)
if __name__=='__main__':unittest.main()
