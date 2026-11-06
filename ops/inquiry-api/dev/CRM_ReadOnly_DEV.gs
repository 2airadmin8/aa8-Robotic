/**
 * DEV owner-only real SSOT read, no mutation and no CustomerID issuance.
 * Reads the two already persisted DEV Inquiry IDs from the existing 27-col ledger.
 * Reads only the real Person SSOT's existing columns needed to identify candidates.
 * It does NOT invoke T006's Production writer or report CustomerID registration.
 */
const DEV_CRM_READ_ONLY = Object.freeze({
  productionPersonSsoTId: '1nLu-r8zOMFUOAXPNgt4msdAwLMb29ona0DizG-HICes',
  personSheet: '02_顧客Master',
  batch: 'AA8-DEV-20261103-R1',
  ids: Object.freeze({
    A: 'INQ-20261104-000403-D19A8041',
    B: 'INQ-20261104-000525-E556D4D7'
  })
});

function devCrmReadOnlyCase_(key) {
  devInquiryEnvironmentGuard_();
  if (key !== 'A' && key !== 'B') throw new Error('DEV_IDENTITY_CASE_NOT_ALLOWED');
  const inquiryId = DEV_CRM_READ_ONLY.ids[key];
  const source = SpreadsheetApp.openById(AA8_DEV.spreadsheetId).getSheetByName('01_Inquiry');
  if (!source) throw new Error('DEV_INQUIRY_SHEET_MISSING');
  const sourceHeaders = source.getRange(1, 1, 1, 27).getValues()[0].map(String);
  if (sourceHeaders.join('|') !== AA8_DEV.headers.join('|')) throw new Error('DEV_27_HEADER_MISMATCH');
  const lastRow = source.getLastRow();
  if (lastRow < 2) throw new Error('DEV_INQUIRY_EMPTY');
  const rows = source.getRange(2, 1, lastRow - 1, 27).getValues();
  const found = rows.filter(r => String(r[0]) === inquiryId);
  if (found.length !== 1) throw new Error('DEV_INQUIRY_NOT_UNIQUE');
  const row = found[0], token = String(row[26]);
  if (token !== DEV_CRM_READ_ONLY.batch + '-' + key ||
      String(row[6]).trim().toLowerCase() !== AA8_DEV.recipient ||
      String(row[4]) !== 'AirAdmin8 DEV University (INTERNAL TEST ONLY)') {
    throw new Error('DEV_RECEIPT_BINDING_MISMATCH');
  }
  const x = {};
  sourceHeaders.forEach((header, i) => { x[header] = row[i]; });

  // Real authoritative rows, read-only. No appending or updating to this SSOT.
  const master = SpreadsheetApp.openById(DEV_CRM_READ_ONLY.productionPersonSsoTId)
    .getSheetByName(DEV_CRM_READ_ONLY.personSheet);
  if (!master) throw new Error('REAL_PERSON_SSOT_MISSING');
  const width = master.getLastColumn(), n = master.getLastRow();
  if (n < 2 || width < 69 || n > 20000) throw new Error('SSOT_UNEXPECTED_DIMENSIONS');
  const headers = master.getRange(1, 1, 1, width).getValues()[0].map(v => String(v).trim());
  const required = ['顧客ID','大学・所属','研究者名','Primaryメール','メール状態','メール情報源URL','氏名一致','所属一致','営業利用可否','ID状態','メール重複'];
  if (required.some(h => headers.filter(k => k === h).length !== 1)) throw new Error('SSOT_SCHEMA_MISMATCH');
  // Existing SSOT columns A:R include identity and email status/evidence.
  const evidence = master.getRange(2, 1, n - 1, 18).getValues();
  const norm = v => String(v == null ? '' : v).normalize('NFKC')
    .replace(/[\s　]+/g, '').toLowerCase();
  const emailMatches = evidence.filter(r => String(r[14] || '').trim().toLowerCase() ===
    String(x.email).trim().toLowerCase());
  const identityMatches = evidence.filter(r => norm(r[3]) === norm(x.organization) &&
    norm(r[5]) === norm(x.name));
  const matches = [...new Set([...emailMatches, ...identityMatches])];
  // Do not copy unverified Person records or data to another spreadsheet.
  // Even a matching email must pass T006's separate evidence & conflict writer.
  const candidates = matches.map(r => ({
    customerId: String(r[0] || ''),
    affiliation: String(r[3] || ''),
    name: String(r[5] || ''),
    primaryEmail: String(r[14] || ''),
    emailStatus: String(r[16] || ''),
    emailEvidenceUrl: String(r[17] || ''),
    evidenceGatePassed: false,
    duplicateGatePassed: false,
    conflict: true
  }));
  const evaluation = evaluateCrmHandoffV129_(x, candidates, {personSsoTReadOnlySnapshotVerified: true});
  // Fail closed even if the proposal was "ready": this is NOT authoritative T006 Writer.
  return Object.freeze({
    environment: 'DEV_ONLY',
    source: 'REAL_01_Inquiry',
    personSsoT: 'REAL_02_顧客Master_READ_ONLY',
    inquiryId: inquiryId,
    sourceRowUnique: true,
    ssotRowsRead: evidence.length,
    matchedEmailCandidates: emailMatches.length,
    matchedNameOrgCandidates: identityMatches.length,
    classification: evaluation.route,
    identityDecision: identityMatches.length ? 'HOLD' : evaluation.identity.decision,
    identityReason: identityMatches.length ? 'EXISTING_IDENTITY_REQUIRES_T006_GATES' : evaluation.identity.reason,
    proposedIntakeSourceId: evaluation.universityIntake ? evaluation.universityIntake.idempotencyKey : null,
    personWriter: 'NOT_CALLED',
    customerId: null,
    registered: false,
    gate: 'HOLD_T006_WRITER_NOT_ISOLATED',
    writesPerformed: 0,
    emailsSent: 0
  });
}

function devCrmReadOnlyResponse_(key) {
  const summary = devCrmReadOnlyCase_(key);
  return HtmlService.createHtmlOutput(
    '<!doctype html><html><head><meta charset="utf-8"></head><body>' +
    '<h1>REAL SSOT READ ONLY / DEV</h1><pre id="identity-result">' +
    devHtml_(JSON.stringify(summary, null, 2)) + '</pre></body></html>'
  );
}
