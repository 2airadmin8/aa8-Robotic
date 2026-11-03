const INQUIRY_CONFIG = {
  spreadsheetId: '1PzfHiB50jFDHCosMGTb7MUvbQ9nC3UD5pHjgHbpY9Qk',
  sheetName: '01_Inquiry',
  notifyTo: 'ceo@air-admin8.co.jp',
  parentOrigin: 'http://127.0.0.1:4173',
  timezone: 'Asia/Tokyo'
};

function doGet(e) {
  const kind = String((e && e.parameter && e.parameter.case) || '');
  if (kind === 'IDENTITY_A' || kind === 'IDENTITY_B')
    return devCrmReadOnlyResponse_(kind.slice(-1));
  return devInquiryForm_(e);
}

function doPost(e) {
  const p = (e && e.parameter) || {};
  const responseToken = clean_(p.response_token);

  try {
    validateInquiry_(p);

    const submissionToken = clean_(p.submission_token);
    if (!submissionToken) throw new Error('Missing submission token');

    const lock = LockService.getScriptLock();
    lock.waitLock(10000);

    let inquiryId;
    let isDuplicate = false;

    try {
      const existing = findBySubmissionToken_(submissionToken);
      if (existing) {
        // A lost browser ACK must not silently bind edited content to the old ID.
        // The row is the persisted truth; a conflicting retry is rejected.
        if (!sameInquiryPayload_(existing.fields, p)) {
          throw new Error('Submission token already used with different inquiry content');
        }
        inquiryId = existing.inquiryId;
        isDuplicate = true;
      } else {
        inquiryId = createInquiryId_();
        appendInquiry_(inquiryId, p, submissionToken);
      }
    } finally {
      lock.releaseLock();
    }

    if (!isDuplicate) {
      // Save the internal delivery checkpoint before attempting customer ACK.
      // Duplicate tokens NEVER automatically resend either email; failures need
      // explicit reconciliation by an authorized operator.
      let internalSent = false;
      try {
        sendInquiryNotification_(inquiryId, p);
        internalSent = true;
        markNotificationStatus_(inquiryId, 'INTERNAL_SENT', new Date());
      } catch (mailError) {
        console.error('Internal notification failed: ' + String(mailError));
        if (!internalSent) markNotificationStatus_(inquiryId, 'INTERNAL_FAILED', '');
        // If status persistence failed AFTER MailApp.sendEmail, do not overwrite
        // a possibly-sent email as FAILED or trigger another automatic send.
      }
      if (internalSent) {
        try {
          sendCustomerAcknowledgement_(inquiryId, p);
          markNotificationStatus_(inquiryId, 'NOTIFIED', new Date());
        } catch (mailError) {
          console.error('Customer ACK failed: ' + String(mailError));
          markNotificationStatus_(inquiryId, 'ACK_FAILED', new Date());
        }
      }
    }

    return responseHtml_({
      ok: true,
      inquiryId: inquiryId,
      responseToken: responseToken,
      duplicate: isDuplicate
    });
  } catch (error) {
    console.error(error && error.stack ? error.stack : error);
    return responseHtml_({
      ok: false,
      inquiryId: '',
      responseToken: responseToken,
      error: '送信できませんでした。入力内容をご確認のうえ、もう一度お試しください。'
    });
  }
}

function validateInquiry_(p) {
  devInquiryPayloadGuard_(p);
  const required = ['category', 'organization', 'name', 'email', 'use_case'];
  required.forEach((key) => {
    if (!String(p[key] || '').trim()) throw new Error('Missing required field: ' + key);
  });

  const email = String(p.email || '').trim();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    throw new Error('Invalid email');
  }

  // Honeypot. Humans should never fill this field.
  if (String(p.website || '').trim()) throw new Error('Spam rejected');
}

function createInquiryId_() {
  const stamp = Utilities.formatDate(new Date(), INQUIRY_CONFIG.timezone, 'yyyyMMdd-HHmmss');
  const suffix = Utilities.getUuid().slice(0, 8).toUpperCase();
  return 'INQ-' + stamp + '-' + suffix;
}

function appendInquiry_(inquiryId, p, submissionToken) {
  const sheet = getInquirySheet_();
  sheet.appendRow([
    inquiryId,
    new Date(),
    'NEW',
    clean_(p.category),
    clean_(p.organization),
    clean_(p.name),
    clean_(p.email),
    clean_(p.phone),
    clean_(p.product),
    clean_(p.use_case),
    clean_(p.budget),
    clean_(p.schedule),
    clean_(p.development),
    clean_(p.message),
    clean_(p.source_page),
    clean_(p.source_product),
    clean_(p.source_maker),
    clean_(p.source_service),
    clean_(p.source_theme),
    clean_(p.source_case),
    clean_(p.utm_source),
    clean_(p.utm_medium),
    clean_(p.utm_campaign),
    clean_(p.ga_client_id),
    'PENDING',
    '',
    submissionToken
  ]);
}

function findBySubmissionToken_(submissionToken) {
  const sheet = getInquirySheet_();
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return null;

  const tokens = sheet.getRange(2, 27, lastRow - 1, 1).getValues();
  for (let i = tokens.length - 1; i >= 0; i--) {
    if (String(tokens[i][0] || '') === submissionToken) {
      return {
        inquiryId: String(sheet.getRange(i + 2, 1).getValue() || ''),
        fields: sheet.getRange(i + 2, 4, 1, 21).getValues()[0]
      };
    }
  }
  return null;
}

// 21 immutable public inquiry fields stored in columns D:X of 01_Inquiry.
// CustomerID/CanonicalCaseID are not included and remain owned by their SSOTs.
const INQUIRY_PAYLOAD_FIELDS_ = [
  'category', 'organization', 'name', 'email', 'phone', 'product', 'use_case',
  'budget', 'schedule', 'development', 'message', 'source_page',
  'source_product', 'source_maker', 'source_service', 'source_theme',
  'source_case', 'utm_source', 'utm_medium', 'utm_campaign', 'ga_client_id'
];

function sameInquiryPayload_(fields, p) {
  if (!Array.isArray(fields) || fields.length !== INQUIRY_PAYLOAD_FIELDS_.length) return false;
  return INQUIRY_PAYLOAD_FIELDS_.every((key, index) =>
    clean_(fields[index]) === clean_(p[key])
  );
}

function sendInquiryNotification_(inquiryId, p) {
  devInquiryPayloadGuard_(p);
  const subject = '[DEV ONLY][' + AA8_DEV.batch + ']【AirAdmin8 Robotics問い合わせ】' + clean_(p.category) + '｜' + clean_(p.organization);
  const body = [
    '問い合わせID：' + inquiryId,
    '',
    '大学・会社名：' + clean_(p.organization),
    'お名前：' + clean_(p.name),
    'メール：' + clean_(p.email),
    '電話：' + clean_(p.phone),
    '相談区分：' + clean_(p.category),
    '製品・メーカー：' + clean_(p.product),
    '予算：' + clean_(p.budget),
    '希望時期：' + clean_(p.schedule),
    'SDK・開発環境：' + clean_(p.development),
    '',
    '【研究・業務用途】',
    clean_(p.use_case),
    '',
    '【補足】',
    clean_(p.message),
    '',
    '【流入】',
    '参照ページ：' + clean_(p.source_page),
    '製品：' + clean_(p.source_product),
    'メーカー：' + clean_(p.source_maker),
    '支援：' + clean_(p.source_service),
    '用途：' + clean_(p.source_theme),
    '事例：' + clean_(p.source_case),
    'utm_source：' + clean_(p.utm_source),
    'utm_medium：' + clean_(p.utm_medium),
    'utm_campaign：' + clean_(p.utm_campaign)
  ].join('\n');

  MailApp.sendEmail({
    to: INQUIRY_CONFIG.notifyTo,
    replyTo: clean_(p.email),
    subject: subject,
    body: body,
    name: 'AirAdmin8 Robotics Inquiry'
  });
}

function sendCustomerAcknowledgement_(inquiryId, p) {
  devInquiryPayloadGuard_(p);
  const subject = '[DEV ONLY][' + AA8_DEV.batch + ']【AirAdmin8 Robotics】お問い合わせを受け付けました';
  const body = [
    clean_(p.name) + ' 様',
    '',
    'AirAdmin8 Roboticsへお問い合わせいただき、誠にありがとうございます。',
    '以下の内容で受け付けました。内容を確認のうえ、担当者よりご連絡いたします。',
    '',
    '問い合わせID：' + inquiryId,
    '相談区分：' + clean_(p.category),
    '製品・メーカー：' + (clean_(p.product) || '未定'),
    '',
    '追加情報や補足がございましたら、本メールへそのままご返信いただけます。',
    '',
    '------------------------------',
    '株式会社AirAdmin8',
    'AirAdmin8 Robotics 問い合わせ窓口',
    'E-mail：' + INQUIRY_CONFIG.notifyTo,
    'Web：https://robotics.air-admin8.co.jp/',
    '------------------------------',
    '',
    '※本メールはお問い合わせ受付時に自動送信しています。'
  ].join('\n');

  MailApp.sendEmail({
    to: clean_(p.email),
    replyTo: INQUIRY_CONFIG.notifyTo,
    subject: subject,
    body: body,
    name: 'AirAdmin8 Robotics'
  });
}

function markNotificationStatus_(inquiryId, status, notifiedAt) {
  const sheet = getInquirySheet_();
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return;

  const ids = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
  for (let i = ids.length - 1; i >= 0; i--) {
    if (String(ids[i][0] || '') === inquiryId) {
      sheet.getRange(i + 2, 25).setValue(status);
      if (notifiedAt) sheet.getRange(i + 2, 26).setValue(notifiedAt);
      return;
    }
  }
}

function getInquirySheet_() {
  devInquiryEnvironmentGuard_();
  const sheet = SpreadsheetApp.openById(INQUIRY_CONFIG.spreadsheetId)
    .getSheetByName(INQUIRY_CONFIG.sheetName);
  if (!sheet) throw new Error('Inquiry sheet not found');
  if (JSON.stringify(sheet.getRange(1, 1, 1, 27).getValues()[0]) !== JSON.stringify(AA8_DEV.headers)) throw new Error('DEV_SCHEMA_MISMATCH');
  return sheet;
}

function clean_(value) {
  return String(value == null ? '' : value).trim().slice(0, 10000);
}

function responseHtml_(payload) { return devInquiryResponse_(payload); }
