# Existing Inquiry DEV installation — 2026-11-03
CEO authorized installation into existing DEV and real internal-only acceptance. This supersedes the previous no-DEV-deploy hold only for the verified DEV target. Production remains forbidden.

- Existing Script: 1qHrw3h4siVwwga-fsN4B3pP2ljvbfrJjXzM1AC4qQsCMDlVQ_7TylZy9
- Existing Sheet: 1PzfHiB50jFDHCosMGTb7MUvbQ9nC3UD5pHjgHbpY9Qk / 01_Inquiry, unchanged 27 headers.
- Access: MYSELF. Execute as owner. Script identity, Sheet and notification target pinned at runtime.
- Only recipient: ceo@air-admin8.co.jp. Both internal notification and acknowledgement carry DEV ONLY subjects.
- At most two new batch tokens (A/B). Existing backend persists receipt and rejects altered-payload replay. No automatic resend.
- Original Code.gs and CRM contract baseline: 06c16a01b9062808fe00033d57529e131c471e9f. Production source files are unchanged.
- Code.dev.gs changes are isolated target configuration, input/mail/environment guards, and a DEV-only real HTTP form/receipt display. This form does not claim public contact.html browser regression.
- NO Customer Master/Case writes. A direct read of the existing T006 p1AssignOfficialCustomerIdFromIntake found its SALES_OS_ID pinned to Production and no verified DEV destination. This missing integration is explicitly BLOCKED, not marked PASS.
- No new GAS, spreadsheets, tabs, CRM, triggers, automation, or permanent runner.
- Rollback source/manifest and SHA256 are retained on AA8-N-018 in aa8-inquiry-dev-install-20261103/rollback-before and rollback-sha256.json. No rollback is run automatically.

Installation and live E2E results must be recorded after actual execution; this source commit alone proves neither deployment nor mail receipt.