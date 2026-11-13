/**
 * DEV QA only: original T006 locked CustomerID writer exact extracted functions,
 * with ONLY P1_RUNTIME destination redirected to existing E2E_TEST_ONLY workbook.
 * This file is NEVER added to the production T006 project.
 * L-xxxx values in QA_Customer are NON-CANONICAL test values.
 */
const P1_RUNTIME = Object.freeze({
  SALES_OS_ID:'11aE5zw5OHoqzGFBXxp06VSkwAOJAZ7N6pkxyAgLg0Bw',
  INTAKE_SHEET:'QA_Intake',
  SALES_MASTER_SHEET:'QA_Customer'
});

function p1HeaderMap_(headers) {
  const m = {};
  headers.forEach((v, i) => {
    const k = String(v || '').trim();
    if (k && m[k] !== undefined) throw new Error('DUPLICATE_HEADER_FAIL_CLOSED: ' + k);
    if (k) m[k] = i;
  });
  return m;
}

function p1Text_(v) { return String(v == null ? '' : v).trim(); }
function p1NowId_() { return Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyyMMddHHmmss'); }

function p1RequireHeaders_(h, names, label) {
  const missing = names.filter(n => h[n] === undefined);
  if (missing.length) throw new Error(label + ' 必須列不足: ' + missing.join(', '));
}

function p1RequireHeaders_(h, names, label) {
  const missing = names.filter(n => h[n] === undefined);
  if (missing.length) throw new Error(label + ' 必須列不足: ' + missing.join(', '));
}

function p1NormalizeIdentity_(v) {
  return p1Text_(v).replace(/[\s　]+/g, '').toLowerCase();
}

function p1AssignOfficialCustomerIdFromIntake(intakeRowNumber) {
  const rowNumber = Number(intakeRowNumber);
  if (!Number.isInteger(rowNumber) || rowNumber < 2) throw new Error('INTAKE_ROW_INVALID');

  const lock = LockService.getScriptLock();
  if (!lock.tryLock(10000)) throw new Error('CUSTOMER_ID_ASSIGN_LOCKED');
  try {
    const ss = SpreadsheetApp.openById(P1_RUNTIME.SALES_OS_ID);
    const intake = ss.getSheetByName(P1_RUNTIME.INTAKE_SHEET);
    const master = ss.getSheetByName(P1_RUNTIME.SALES_MASTER_SHEET);
    if (!intake || !master) throw new Error('INTAKE_OR_MASTER_NOT_FOUND');

    const intakeValues = intake.getDataRange().getValues();
    const masterValues = master.getDataRange().getValues();
    const ih = p1HeaderMap_(intakeValues[0] || []);
    const mh = p1HeaderMap_(masterValues[0] || []);
    p1RequireHeaders_(ih, ['大学・所属','研究者名','メール','根拠URL','重複確認','顧客ID','処理状態','備考'], P1_RUNTIME.INTAKE_SHEET);
    p1RequireHeaders_(mh, ['顧客ID','大学・所属','研究者名','Primaryメール','メール状態','営業利用可否'], P1_RUNTIME.SALES_MASTER_SHEET);
    if (rowNumber > intakeValues.length) throw new Error('INTAKE_ROW_NOT_FOUND');

    const row = intakeValues[rowNumber - 1];
    const currentId = p1Text_(row[ih['顧客ID']]);
    const org = p1Text_(row[ih['大学・所属']]);
    const lab = ih['研究室'] !== undefined ? p1Text_(row[ih['研究室']]) : '';
    const person = p1Text_(row[ih['研究者名']]);
    const role = ih['役職'] !== undefined ? p1Text_(row[ih['役職']]) : '';
    const email = p1Text_(row[ih['メール']]).toLowerCase();
    const evidence = p1Text_(row[ih['根拠URL']]);
    const status = p1Text_(row[ih['処理状態']]);

    if (!org || !person) throw new Error('NEW_CUSTOMER_IDENTITY_REQUIRED_FAIL_CLOSED');
    if (status === 'Master登録済' && currentId) {
      const exists = masterValues.slice(1).some(r => p1Text_(r[mh['顧客ID']]) === currentId);
      if (!exists) throw new Error('INTAKE_CUSTOMER_ID_ORPHAN_FAIL_CLOSED: ' + currentId);
      return {status:'ALREADY_REGISTERED', customerId:currentId, intakeRow:rowNumber};
    }
    if (currentId) throw new Error('INTAKE_CUSTOMER_ID_PRESET_FAIL_CLOSED: ' + currentId);

    const emailMatches = [];
    const identityMatches = [];
    const orgKey = p1NormalizeIdentity_(org);
    const personKey = p1NormalizeIdentity_(person);
    for (let i = 1; i < masterValues.length; i++) {
      const m = masterValues[i];
      const id = p1Text_(m[mh['顧客ID']]);
      if (!id) continue;
      const mEmail = p1Text_(m[mh['Primaryメール']]).toLowerCase();
      if (email && mEmail && email === mEmail) emailMatches.push(id);
      if (orgKey && personKey &&
          p1NormalizeIdentity_(m[mh['大学・所属']]) === orgKey &&
          p1NormalizeIdentity_(m[mh['研究者名']]) === personKey) {
        identityMatches.push(id);
      }
    }
    const uniqueEmailIds = [...new Set(emailMatches)];
    const uniqueIdentityIds = [...new Set(identityMatches)];
    if (uniqueEmailIds.length > 1) throw new Error('MASTER_EMAIL_DUPLICATE_FAIL_CLOSED: ' + email);
    if (uniqueIdentityIds.length > 1) throw new Error('MASTER_IDENTITY_DUPLICATE_FAIL_CLOSED: ' + person);
    if (uniqueEmailIds.length && uniqueIdentityIds.length && uniqueEmailIds[0] !== uniqueIdentityIds[0]) {
      throw new Error('MASTER_IDENTITY_EMAIL_CONFLICT_FAIL_CLOSED');
    }

    const existingId = uniqueEmailIds[0] || uniqueIdentityIds[0] || '';
    if (existingId) {
      intake.getRange(rowNumber, ih['重複確認'] + 1).setValue('既存顧客');
      intake.getRange(rowNumber, ih['顧客ID'] + 1).setValue(existingId);
      intake.getRange(rowNumber, ih['処理状態'] + 1).setValue('Master登録済');
      SpreadsheetApp.flush();
      return {status:'EXISTING_INHERITED', customerId:existingId, intakeRow:rowNumber};
    }

    let maxL = 0;
    const usedIds = new Set();
    masterValues.slice(1).forEach(r => {
      const id = p1Text_(r[mh['顧客ID']]);
      if (!id) return;
      usedIds.add(id);
      const m = id.match(/^L-(\d{4})$/);
      if (m) maxL = Math.max(maxL, Number(m[1]));
    });
    intakeValues.slice(1).forEach(r => {
      const id = p1Text_(r[ih['顧客ID']]);
      if (!id) return;
      usedIds.add(id);
      const m = id.match(/^L-(\d{4})$/);
      if (m) maxL = Math.max(maxL, Number(m[1]));
    });
    if (maxL >= 9999) throw new Error('CUSTOMER_ID_NAMESPACE_EXHAUSTED_FAIL_CLOSED');
    const customerId = 'L-' + String(maxL + 1).padStart(4, '0');
    if (usedIds.has(customerId)) throw new Error('CUSTOMER_ID_COLLISION_FAIL_CLOSED: ' + customerId);

    const newRow = new Array(masterValues[0].length).fill('');
    const setMaster = (name, value) => { if (mh[name] !== undefined) newRow[mh[name]] = value == null ? '' : value; };
    setMaster('顧客ID', customerId);
    setMaster('研究優先度', 'B');
    setMaster('大学・所属', org);
    setMaster('研究室', lab);
    setMaster('研究者名', person);
    setMaster('役職', role);
    setMaster('所属状態', '要確認');
    setMaster('メール状態', '要再調査');
    setMaster('営業利用可否', '要確認');
    setMaster('自動送信対象', 'NO');
    setMaster('送信許可', 'NO');
    setMaster('自動化ステータス', '連絡先調査待ち');
    setMaster('研究情報源URL', evidence);
    setMaster('ID状態', '正式');
    setMaster('データ区分', '新規顧客');
    setMaster('確認理由', '00_新規受付から正式採番／PrimaryメールはSafe Writerのみ更新');
    master.getRange(master.getLastRow() + 1, 1, 1, newRow.length).setValues([newRow]);

    intake.getRange(rowNumber, ih['重複確認'] + 1).setValue('新規顧客');
    intake.getRange(rowNumber, ih['顧客ID'] + 1).setValue(customerId);
    intake.getRange(rowNumber, ih['処理状態'] + 1).setValue('Master登録済');
    const beforeNote = p1Text_(row[ih['備考']]);
    intake.getRange(rowNumber, ih['備考'] + 1).setValue(
      (beforeNote ? beforeNote + ' / ' : '') + '正式顧客ID採番=' + customerId + '／PrimaryメールはSafe Writerで確認'
    );
    SpreadsheetApp.flush();

    return {status:'NEW_REGISTERED', customerId, intakeRow:rowNumber, masterRow:master.getLastRow()};
  } finally {
    lock.releaseLock();
  }
}
