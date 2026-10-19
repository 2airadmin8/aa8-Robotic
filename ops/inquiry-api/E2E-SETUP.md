# Robotics inquiry E2E — existing DEV only

## Verified
- GitHub SSOT: 2airadmin8/aa8-Robotic, PR #127.
- PROD Spreadsheet: 1dgoeLCBJVE0CXBGgizUwA-ozrRVvJw6Ng9gfGN0h8wI.
- Existing DEV Spreadsheet: 1PzfHiB50jFDHCosMGTb7MUvbQ9nC3UD5pHjgHbpY9Qk (27 columns, historical test entries).
- Existing DEV Apps Script project ID / deployment URL / actual code / mail recipients: **NOT VERIFIED**.

## Do not create a third environment
The additional blank E2E Spreadsheet created during investigation is not an SSOT and is not connected to this workflow. Do not write test data to it or delete it without approval.

## Mandatory preflight before any live POST
1. Read-only confirm the existing DEV Apps Script project ID and deployment URL.
2. Read-only verify DEV deployment's effective spreadsheet ID is the existing DEV sheet above; do not infer from filenames.
3. Verify DEV mail recipients and customer acknowledgement can only reach an approved internal inbox. If this cannot be demonstrated, STOP: do not run live E2E.
4. GitHub environment `inquiry-e2e`: set `E2E_APPS_SCRIPT_URL` to verified DEV URL, `E2E_INTERNAL_EMAIL` to an internal address, require environment approval.
5. Verify URL is different from production Apps Script URL; workflow rejects production deployment ID.
6. Run manually via workflow_dispatch. Never schedule live submissions before isolation proof.

## Acceptance
Two distinct server-acknowledged IDs and thanks-page transitions; independent read-only check of two DEV sheet rows; duplicate token behavior; internal inbox actual receipt. Mail and Slack checks not yet automated and MUST NOT be marked PASS without evidence.

## No production changes
Do not alter production Script Properties, PROD Web App, WADAX, DNS, customers, or production Spreadsheet.

## Company-wide architecture alignment (営業OS SSOT v1.5)
- `Inquiry_Master` and `Inquiry_DEV` are inbound **inquiry event logs**, not customer/person Masters. Do not assign or overwrite canonical customer IDs in this E2E project.
- Corporate Person Master remains `大学AIロボット営業_顧客Master_APP完成版`. Production outbound mail runtime remains `本番_大学営業メール自動化_自動調査シンプル版_v4.0`.
- Future inbound CRM routing, if separately approved, must use `00_新規受付 → identity/dedup review → canonical customer ID → permission checks → 配信可否`. Do not directly inject web inquiries into the production mailing core.
- No new Writer, Trigger, customer Master, mail queue, or campaign is permitted in PR #127.
- Production Apps Script source, active deployment, triggers and mail recipients remain unverified. Do not modify them. Separate DEV Web App URL must be mapped and proven before live POST.
- Do not treat `NOTIFIED` in the inquiry log as verified recipient delivery. Independent Gmail and Slack receipt checks are separate gates.
