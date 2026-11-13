/**
 * Robotics Inquiry -> existing T006 official CustomerID writer admission.
 * No Sheets/Mail calls and NO ID allocation. Install alongside existing T006
 * 05_runtime_p1.js only after separately approved exact-code change.
 * CustomerID may only be returned by the original locked T006 writer.
 *
 * IMPORTANT: verifiedEvidence is INTERNAL T006 result, not public request or
 * user-entered evidence URL. The caller must construct this after authoritative
 * Evidence/Identity/Dedup checks; this function never upgrades self-reports.
 */
function t006RoboticsOfficialAdmission_(inquiry, intakeRows, masterRows, verifiedEvidence) {
  const clean = v => String(v == null ? '' : v).normalize('NFKC').trim();
  const norm = v => clean(v).replace(/[\s　]+/g, '').toLowerCase();
  const email = v => clean(v).toLowerCase();
  const out = (decision, reason, id) => Object.freeze({
    decision, reason, existingCustomerId: id || null,
    newCustomerId: null, writesPerformed: 0, marketingPermission: false
  });
  if (!inquiry || inquiry.source !== 'Robotics_Web_Inquiry')
    return out('NOT_APPLICABLE', 'NOT_ROBOTICS_WEB_INQUIRY');
  const id = clean(inquiry.inquiryId);
  if (!/^INQ-[0-9]{8}-[0-9]{6}-[A-F0-9]{8}$/.test(id))
    return out('HOLD', 'INVALID_SOURCE_ID');
  if (!Array.isArray(intakeRows) || !Array.isArray(masterRows))
    return out('HOLD', 'AUTHORITATIVE_SSOT_NOT_READ');
  const sourceMatches = intakeRows.filter(r => clean(r && r.sourceId) === id);
  if (sourceMatches.length !== 1)
    return out('HOLD', sourceMatches.length > 1 ? 'DUPLICATE_SOURCE_ID' : 'SOURCE_NOT_REGISTERED');
  const intake = sourceMatches[0];
  if (clean(intake.source) !== 'Robotics_Web_Inquiry' ||
      norm(intake.organization) !== norm(inquiry.organization) ||
      norm(intake.name) !== norm(inquiry.name) ||
      email(intake.email) !== email(inquiry.email))
    return out('HOLD', 'INQUIRY_INTAKE_IDENTITY_MISMATCH');
  const person = norm(intake.name), org = norm(intake.organization);
  if (!person || !org || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email(intake.email)))
    return out('HOLD', 'INCOMPLETE_IDENTITY');
  if (clean(intake.customerId))
    return out('HOLD', 'CUSTOMER_ID_ALREADY_PRESET_RECONCILE');
  const ematches = masterRows.filter(r => email(r && r.primaryEmail) === email(intake.email) &&
    clean(r && r.customerId));
  const nmatches = masterRows.filter(r => norm(r && r.name) === person &&
    norm(r && r.organization) === org && clean(r && r.customerId));
  const emIds = [...new Set(ematches.map(r => clean(r.customerId)))];
  const nmIds = [...new Set(nmatches.map(r => clean(r.customerId)))];
  if (emIds.length > 1 || nmIds.length > 1)
    return out('HOLD', 'DUPLICATE_PERSON_MATCH');
  if (emIds.length && nmIds.length && emIds[0] !== nmIds[0])
    return out('HOLD', 'EMAIL_NAME_AFFILIATION_CONFLICT');
  if (emIds.length && !nmIds.length)
    return out('HOLD', 'EMAIL_MATCH_IDENTITY_NOT_CONFIRMED');
  if (nmIds.length && emIds.length === 0)
    return out('HOLD', 'NAME_MATCH_EMAIL_NOT_CONFIRMED');

  const gate = verifiedEvidence || {};
  // Never accept a form privacy checkbox or an ordinary source_page as evidence.
  if (gate.origin !== 'T006_AUTHORIZED_EVIDENCE_WRITER' ||
      gate.sourceId !== id ||
      gate.identityVerified !== true ||
      gate.officialEmailVerified !== true ||
      gate.duplicateGatePassed !== true ||
      gate.conflict === true ||
      !/^https:\/\//.test(clean(gate.officialEvidenceUrl)) ||
      email(gate.verifiedEmail) !== email(intake.email) ||
      norm(gate.verifiedName) !== person ||
      norm(gate.verifiedOrganization) !== org)
    return out('HOLD', 'T006_EVIDENCE_IDENTITY_GATE_REQUIRED');

  if (emIds.length === 1 && nmIds.length === 1 && emIds[0] === nmIds[0])
    return out('READY_REUSE_EXISTING', 'CALL_EXISTING_LOCKED_T006_WRITER', emIds[0]);
  if (emIds.length === 0 && nmIds.length === 0)
    return out('READY_REGISTER_NEW', 'CALL_EXISTING_LOCKED_T006_WRITER');
  return out('HOLD', 'UNRESOLVED_IDENTITY_CONFLICT');
}
