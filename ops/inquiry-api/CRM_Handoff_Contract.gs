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

/** Inquiry Date/explicit-offset timestamps are instants, converted to JST.
 * Existing yyyy-MM-dd[ HH:mm:ss] Sheet display strings are already JST.
 * Reject rollover/partial dates; never depend on the machine's local timezone.
 * This is a pure projection, not a Sheet write or an environment probe. */
function crmV129JstDate_(value) {
  const jstMs = 9 * 60 * 60 * 1000;
  const fromInstant = function (n) {
    if (!Number.isFinite(n)) return '';
    const shifted = new Date(n + jstMs);
    if (!Number.isFinite(shifted.getTime())) return '';
    const iso = shifted.toISOString();
    return /^\d{4}-/.test(iso) && shifted.getUTCFullYear() > 0 ? iso.slice(0, 10) : '';
  };
  if (Object.prototype.toString.call(value) === '[object Date]') {
    try { return fromInstant(Date.prototype.getTime.call(value)); }
    catch (_) { return ''; }
  }
  if (typeof value !== 'string') return '';
  // Do not truncate: an otherwise valid prefix followed by junk is not a date.
  const s = value.trim();
  const m = /^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,3}))?(Z|[+-]\d{2}:\d{2})?)?$/.exec(s);
  if (!m) return '';
  const year = Number(m[1]), month = Number(m[2]), day = Number(m[3]);
  const hour = Number(m[4] || 0), minute = Number(m[5] || 0), second = Number(m[6] || 0);
  if (year < 1 || month < 1 || month > 12 || day < 1 || day > 31 ||
      hour > 23 || minute > 59 || second > 59) return '';
  const calendar = new Date(0);
  // setUTCFullYear avoids Date.UTC's special treatment of years 00 through 99.
  calendar.setUTCFullYear(year, month - 1, day);
  calendar.setUTCHours(hour, minute, second, Number((m[7] || '').padEnd(3, '0')));
  if (calendar.getUTCFullYear() !== year || calendar.getUTCMonth() !== month - 1 ||
      calendar.getUTCDate() !== day) return '';
  const zone = m[8];
  if (!zone) return s.slice(0, 10); // Validated, existing JST Sheet representation.
  let offsetMinutes = 0;
  if (zone !== 'Z') {
    const zoneHour = Number(zone.slice(1, 3)), zoneMinute = Number(zone.slice(4, 6));
    if (zoneHour > 23 || zoneMinute > 59) return '';
    offsetMinutes = (zone[0] === '+' ? 1 : -1) * (zoneHour * 60 + zoneMinute);
  }
  return fromInstant(calendar.getTime() - offsetMinutes * 60 * 1000);
}

/** Sheet writer must set TEXT number format; these pre-sanitized cell proposals
 * also guard against formula injection until a trusted writer is verified. */
function crmV129TextCell_(value, limit) {
  const s = crmV129Clean_(value, limit || 500);
  return /^[=+\-@\t\r]/.test(s) ? "'" + s : s;
}

/** Retain a same-origin product path only. Never leak query tokens, email
 * addresses or external referrers into the university Master notes. */
function crmV129SafeSourcePath_(value) {
  const raw = crmV129Clean_(value, 1024);
  const m = /^https:\/\/robotics\.air-admin8\.co\.jp(\/[a-z0-9._/-]*)/i.exec(raw);
  return m ? m[1].slice(0, 200) : '';
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
    'Source=' + crmV129SafeSourcePath_(inquiry.source_page)
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

/** Strict adapter for EXISTING 02_顧客Master physical columns. This is
 * read-only projection, not a Customer Master writer. The actual T006 evidence
 * and duplicate Gates must provide independent trusted approvals; a physical
 * status cell or even a matching URL is not that approval by itself. */
function crmV129PersonFromMasterPhysicalRow_(headers, row, t006GateEvidence) {
  if (!Array.isArray(headers) || !Array.isArray(row) || headers.length !== row.length) return null;
  const required = [
    '顧客ID', '大学・所属', '研究者名', 'Primaryメール',
    'メール状態', 'メール情報源URL', '氏名一致', '所属一致',
    '営業利用可否', 'ID状態', 'メール重複'
  ];
  if (required.some(key => headers.filter(h => h === key).length !== 1)) return null;
  const get = key => crmV129Clean_(row[headers.indexOf(key)], key === 'メール情報源URL' ? 1024 : 500);
  const gate = t006GateEvidence || {};
  return {
    customerId: get('顧客ID'),
    primaryEmail: get('Primaryメール'),
    name: get('研究者名'),
    affiliation: get('大学・所属'),
    emailStatus: get('メール状態'),
    emailEvidenceUrl: get('メール情報源URL'),
    evidenceGatePassed: gate.officialEmailEvidencePassed === true,
    duplicateGatePassed: gate.identityAndDedupPassed === true,
    salesUseAllowed: get('営業利用可否') === '可',
    conflict: gate.conflict === true || /重複|CONFLICT|衝突/i.test(get('メール重複'))
  };
}

function crmV129Identity_(inquiry, candidates, authoritativeSnapshot) {
  if (!authoritativeSnapshot || !Array.isArray(candidates)) {
    return { decision: 'HOLD', reason: 'PERSON_SSOT_NOT_READ', customerId: null };
  }
  if (candidates.some(c => !c || typeof c !== 'object')) {
    return { decision: 'HOLD', reason: 'PERSON_SSOT_ROW_INVALID', customerId: null };
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
  // Physically observed 02_顧客Master Q-column values include:
  // 確認済 / 確認済み / 有効 / 要再調査 / 未確認.
  // 有効 is NOT sufficient to prove Person identity or verified Primary.
  const confirmedStatuses = ['確認済', '確認済み', 'CONFIRMED'];
  const verifiedEmail = confirmedStatuses.includes(crmV129Clean_(person.emailStatus, 40)) &&
    /^https:\/\//i.test(crmV129Clean_(person.emailEvidenceUrl, 1024)) &&
    person.evidenceGatePassed === true &&
    person.duplicateGatePassed === true;
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
    !crmV129JstDate_(x.received_at) ||
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
