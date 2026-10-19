# Inquiry E2E test environment (isolated)

This is a manual-only workflow. It MUST NOT target the production Apps Script deployment or production Inquiry Master.

## One-time setup
1. Make a separate Google Spreadsheet with a test-only `01_Inquiry` sheet, copying the 27 header names from the production schema, not customer records.
2. Use the dedicated `ops/inquiry-api/e2e-test/Code.gs` in a **separate** Apps Script project (do not copy production Code.gs). Its test spreadsheet ID is fixed. Set Apps Script Script Property `E2E_INTERNAL_EMAIL` to the same internal mailbox used by the GitHub E2E environment. It rejects other recipients and non-E2E form data. Never paste this into the production Apps Script project.
3. Deploy the test script as a Web App accessible to the CI test runner; restrict the deployment's business logic to internal test recipient addresses. Verify that its ID is different from the production Web App ID.
4. In GitHub, create Environment `inquiry-e2e` with approval protection and add secrets `E2E_APPS_SCRIPT_URL` (test Web App URL) and `E2E_INTERNAL_EMAIL` (internal mailbox).
5. Manually run **Inquiry Apps Script E2E (isolated)**. It uses the public form UI but intercepts the JS file to replace its Apps Script endpoint **only inside the test browser**.

## Gates
- The workflow refuses a missing URL, non-Google Web App URL, production Web App ID, or non-internal email.
- Real Google Apps Script E2E must return two distinct inquiry IDs and redirect correctly.
- It does **not** independently verify test spreadsheet rows, inbox receipt, or Slack. Those require separate read-only reconciliation and must not be reported PASS until implemented.
- Do not merge to main or schedule this workflow until the separate test deployment and protection settings are confirmed.
- No customer data, real customer mail, or production Spreadsheet writes are permitted.
