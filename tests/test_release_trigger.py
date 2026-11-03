"""Regression tests: production pages must never auto-deploy on main push."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_release_trigger import ReleaseGateError, triggers_from_yaml, verify_manual_release


class ManualPagesReleaseGateTest(unittest.TestCase):
    def test_manual_only_allowed(self):
        source = "name: deploy\non:\n  workflow_dispatch:\npermissions:\n  contents: read\n"
        self.assertEqual(triggers_from_yaml(source), ("workflow_dispatch",))
        verify_manual_release(source, event_name="workflow_dispatch")

    def test_push_main_rejected(self):
        source = "on:\n  push:\n    branches: [main]\n  workflow_dispatch:\njobs:\n"
        with self.assertRaises(ReleaseGateError):
            verify_manual_release(source)

    def test_schedule_rejected(self):
        source = 'on:\n  workflow_dispatch:\n  schedule:\n    - cron: "0 0 * * *"\njobs:\n'
        with self.assertRaises(ReleaseGateError):
            verify_manual_release(source)

    def test_push_event_rejected_even_with_safe_workflow(self):
        source = "on:\n  workflow_dispatch:\njobs:\n"
        with self.assertRaises(ReleaseGateError):
            verify_manual_release(source, event_name="push")

    def test_no_dispatch_rejected(self):
        with self.assertRaises(ReleaseGateError):
            verify_manual_release("on:\n  push:\n    branches: [main]\njobs:\n")

    def test_inline_events_fail_closed(self):
        with self.assertRaises(ReleaseGateError):
            verify_manual_release("on: [push, workflow_dispatch]\njobs:\n")

    def test_real_workflow_manual_only(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / ".github/workflows/pages.yml").read_text(encoding="utf-8")
        verify_manual_release(source)

    def test_real_workflow_deploy_is_one_shot(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / ".github/workflows/pages.yml").read_text(encoding="utf-8")
        self.assertEqual(source.count("uses: actions/deploy-pages@v4"), 1)
        self.assertNotIn("continue-on-error: true", source)
        self.assertNotIn("Retry GitHub Pages deployment", source)
        self.assertNotIn("Wait before retry", source)
        self.assertNotIn("deployment_retry", source)
        self.assertIn("id: deployment_primary", source)


if __name__ == "__main__":
    unittest.main()
