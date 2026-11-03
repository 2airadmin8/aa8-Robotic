/**
 * AirAdmin8 Robotics | V129 inbound Inquiry -> existing CRM contract
 * STATUS: DRAFT / PURE / NO SIDE EFFECTS. Not deployed to any Apps Script.
 *
 * SSOT ownership:
 *  - Inquiry ledger: AirAdmin8_Robotics_Inquiry_Master/01_Inquiry (27 columns)
 *  - University Person: existing 00_新規受付 -> 02_顧客Master
 *  - Organization and Opportunity: existing PAI ERP/Robot FDE Writer (NOT this file)
 *
 * This module only PRODUCES a proposed handoff and immutable field mapping.
 * It MUST NEVER write Sheets, call GAS/CRM API, create customers, create cases,
 * send emails, derive a canonical CustomerID, or change Primary Email.
 * Production use requires a separate approved DEV integration/SSOT gate.
 */

const INQUIRY_CRM_V129 = Object.freeze({
  version: 'V129',
  mode: 'PURE_CONTRACT_NO_WRITES',
  universityIntakeSheet: '00_新規受付',
  personMasterSheet: '02_顧客Master',
  intakeHeaders: Object.freeze([
    '受付日', 'データ来源', '大学・所属', '研究室', '研究者名', '役職',
    'メール', '電話', 'researchmap_URL', 'KAKEN_URL', '根拠URL',
    '重複確認', '顧客ID', '処理状態', '備考', 'SourceID', 'ImportBatchID'
  ])
});

function crmV129Clean_(value, maxLength) {
  return String(value == null ? '' : value).normalize('NFKC').trim().slice(0, maxLength || 500);
}

function crmV129Email_(value) {
  return crmV129Clean_(value, 254).toLowerCase();
}

/** Date is stored as a true Date in Inquiry Sheet, while 00_新規受付
 * takes only 受付日. Japan has UTC+09 without DST; this pure function
 * intentionally does not depend on a GAS token or production clock. */
function crmV129JstDate_(value) {
  if (Object.prototype.toString.call(value) === '[object Date]') {
    const n = value.getTime();
    if (!Number.isFinite(n)) return '';
    return new Date(n + 9 * 60 * 60 * 1000).toISOString().slice(0, 10);
  }
  const s = crmV129Clean_(value, 40);
  return /^\d{4}-\d{2}-\d{2}(?:\D|$)/.test(s) ? s.slice(0, 10) : '';
}

/** Sheet writer must set TEXT number format; these pre-sanitized cell proposals
 * also guard against formula injection until a trusted writer is verified. */
function crmV129TextCell_(value, limit) {
  const s = crmV129Clean_(value, limit || 500);
  return /^[=+\-@\t\r]/.test(s) ? "'" + s : s;
}

function crmV129OrgType_(organization) {
  const value = crmV129Clean_(organization, 500);
  const university = /大学|大學|\buniversity\b/i.test(value);
  const corporate = /株式会社|合同会社|有限会社|\binc\.?\b|\bltd\.?\b|\bllc\b|\bcorp\.?\b|\bcorporation\b/i.test(value);
  if (university && !corporate) return 'UNIVERSITY_PERSON';
  if (corporate && !university) return 'PAI_ORGANIZATION';
  // Mixed and unnamed institutions are ambiguous: never guess an SSOT.
  return 'HOLD_UNKNOWN_ENTITY';
}

function crmV129EventType_(category) {
  const c = crmV129Clean_(category, 120);
  if (c === '見積・大学購買') return 'QUOTE_REQUEST';
  if (c === 'PoC設計') return 'POC_CONSULTATION';
  // Selection, SDK, pages, opens and raw submissions are NOT case events.
  return null;
}

/** Return the proposed 17 physical columns. Never put a website URL in
 * 根拠URL: it is a lead source, not identity or email-verification evidence. */
function crmV129IntakeProposal_(inquiry) {
  const date = crmV129JstDate_(inquiry.received_at);
  const inquiryId = crmV129Clean_(inquiry.inquiry_id, 128);
  const notes = [
    'InquiryID=' + inquiryId,
    'Product=' + crmV129Clean_(inquiry.source_product || inquiry.product, 120),
    'Maker=' + crmV129Clean_(inquiry.source_maker, 100),
    'Source=' + crmV129Clean_(inquiry.source_page, 220)
  ].join('; ').slice(0, 800);
  return [
    crmV129TextCell_(date, 40),
    'Robotics_Web_Inquiry',
    crmV129TextCell_(inquiry.organization, 300),
    '', // Lab is not an Inquiry field.
    crmV129TextCell_(inquiry.name, 200),
    '', // No professor/rank inference.
    crmV129TextCell_(inquiry.email, 254), // Self-provided; NOT verified Primary.
    crmV129TextCell_(inquiry.phone, 100),
    '', // No inferred researchmap URL.
    '', // No inferred KAKEN URL.
    '', // The product/source_page is not email identity evidence.
    '未確認',
    '', // CustomerID assigned ONLY by existing Master Writer.
    'HOLD_EVIDENCE',
    crmV129TextCell_(notes, 800),
    crmV129TextCell_(inquiryId, 128), // Existing SourceID = idempotency key.
    ''  // Existing ImportBatchID stays owned by existing import writer.
  ];
}

function crmV129Identity_(inquiry, candidates, authoritativeSnapshot) {
  if (!authoritativeSnapshot || !Array.isArray(candidates)) {
    return { decision: 'HOLD', reason: 'PERSON_SSOT_NOT_READ', customerId: null };
  }
  const email = crmV129Email_(inquiry.email);
  const matches = candidates.filter(c => crmV129Email_(c.primaryEmail || c.email) === email);
  const ids = new Set(matches.map(c => crmV129Clean_(c.customerId, 128)));
  if (matches.length > 1 || ids.size > 1) {
    return { decision: 'HOLD', reason: 'DUPLICATE_EMAIL_MATCH', customerId: null };
  }
  if (matches.length === 0) {
    // A user self-report cannot prove canonical email or Person identity.
    return { decision: 'NEW_PENDING_VERIFICATION', reason: 'EMAIL_EVIDENCE_REQUIRED', customerId: null };
  }
  const person = matches[0];
  const sameName = crmV129Clean_(person.name, 200) === crmV129Clean_(inquiry.name, 200);
  const sameOrg = crmV129Clean_(person.affiliation, 300) === crmV129Clean_(inquiry.organization, 300);
  if (!sameName || !sameOrg) {
    return { decision: 'HOLD', reason: 'PERSON_NAME_OR_AFFILIATION_CONFLICT', customerId: null };
  }
  const verifiedEmail = person.emailStatus === 'CONFIRMED' &&
    /^https:\/\//i.test(crmV129Clean_(person.emailEvidenceUrl, 1024));
  if (!verifiedEmail || !crmV129Clean_(person.customerId, 128)) {
    return { decision: 'HOLD', reason: 'CANONICAL_EMAIL_OR_CUSTOMER_ID_UNVERIFIED', customerId: null };
  }
  if (person.conflict === true) {
    return { decision: 'HOLD', reason: 'EXISTING_PERSON_CONFLICT', customerId: null };
  }
  return {
    decision: 'EXISTING_VERIFIED',
    reason: 'MATCHED_EXISTING_PERSON_SSOT',
    customerId: crmV129Clean_(person.customerId, 128)
  };
}

/** Main V129 pure decision: internal model for authorized DEV writer integration.
 * personCandidates must come from an independently verified read-only snapshot,
 * never a value supplied by the public browser. */
function evaluateCrmHandoffV129_(inquiry, personCandidates, trustedContext) {
  const x = inquiry || {};
  const context = trustedContext || {};
  const inquiryId = crmV129Clean_(x.inquiry_id, 128);
  const invalid = !/^INQ-[A-Za-z0-9-]{8,122}$/.test(inquiryId) ||
    !crmV129Clean_(x.organization, 300) || !crmV129Clean_(x.name, 200) ||
    !crmV129Clean_(x.category, 120) ||
    !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(crmV129Email_(x.email));
  const base = {
    version: INQUIRY_CRM_V129.version,
    mode: INQUIRY_CRM_V129.mode,
    writesPerformed: 0,
    emailsSent: 0,
    inquiryId: inquiryId,
    sourceProduct: crmV129Clean_(x.source_product || x.product, 120),
    sourceMaker: crmV129Clean_(x.source_maker, 120),
    inboundIntakeRef: inquiryId,
    route: null,
    gate: 'BLOCKED',
    identity: { decision: 'HOLD', reason: 'NOT_EVALUATED', customerId: null },
    universityIntake: null,
    opportunity: { eventType: null, caseEventId: null, state: 'NO_CASE', customerId: null },
    followUp: { state: 'TRIAGE_UNASSIGNED', owner: null, dueAt: null }
  };
  if (invalid) {
    base.gate = 'INVALID_INQUIRY';
    base.followUp.state = 'BLOCKED_INVALID_INQUIRY';
    return base;
  }
  const route = crmV129OrgType_(x.organization);
  base.route = route;
  const eventType = crmV129EventType_(x.category);
  if (eventType) {
    base.opportunity.eventType = eventType;
    // Deterministic event identity for the future existing PAI Writer.
    base.opportunity.caseEventId = inquiryId + ':' + eventType;
    base.opportunity.state = 'HOLD_CUSTOMER_ID';
  }
  if (route === 'PAI_ORGANIZATION') {
    base.identity.reason = 'EXISTING_PAI_ORGANIZATION_WRITER_NOT_VERIFIED';
    base.gate = 'HOLD_ORGANIZATION_ROUTE';
    return base;
  }
  if (route !== 'UNIVERSITY_PERSON') {
    base.identity.reason = 'ENTITY_TYPE_AMBIGUOUS';
    base.gate = 'HOLD_ENTITY_CLASSIFICATION';
    return base;
  }
  base.universityIntake = {
    target: INQUIRY_CRM_V129.universityIntakeSheet,
    headers: INQUIRY_CRM_V129.intakeHeaders.slice(),
    values: crmV129IntakeProposal_(x),
    idempotencyKey: inquiryId,
    committed: false
  };
  base.identity = crmV129Identity_(x, personCandidates, context.personSsoTReadOnlySnapshotVerified === true);
  if (base.identity.decision === 'EXISTING_VERIFIED') {
    // A matching Person is NOT authorization to create a Case or send mail.
    base.gate = 'READY_FOR_EXISTING_WRITER_REVIEW';
    if (eventType) {
      base.opportunity.state = 'CASE_EVENT_CANDIDATE_ONLY';
      base.opportunity.customerId = base.identity.customerId;
    }
  } else {
    base.gate = 'HOLD_IDENTITY_GATE';
  }
  return base;
}
