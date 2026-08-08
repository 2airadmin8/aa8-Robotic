const INQUIRY_CONFIG = {
  spreadsheetId: '1dgoeLCBJVE0CXBGgizUwA-ozrRVvJw6Ng9gfGN0h8wI',
  sheetName: '01_Inquiry',
  notifyTo: 'airobot@robotics.air-admin8.co.jp',
  parentOrigin: 'https://robotics.air-admin8.co.jp',
  timezone: 'Asia/Tokyo'
};

function doGet() {
  return HtmlService.createHtmlOutput('AirAdmin8 Robotics Inquiry API');
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
      try {
        sendInquiryNotification_(inquiryId, p);
        sendCustomerAcknowledgement_(inquiryId, p);
        markNotificationStatus_(inquiryId, 'NOTIFIED', new Date());
      } catch (mailError) {
        console.error('Notification failed: ' + (mailError && mailError.stack ? mailError.stack : mailError));
        markNotificationStatus_(inquiryId, 'FAILED', '');
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
        inquiryId: String(sheet.getRange(i + 2, 1).getValue() || '')
      };
    }
  }
  return null;
}

function sendInquiryNotification_(inquiryId, p) {
  const subject = '【AirAdmin8 Robotics問い合わせ】' + clean_(p.category) + '｜' + clean_(p.organization);
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
  const subject = '【AirAdmin8 Robotics】お問い合わせを受け付けました';
  const body = [
    clean_(p.name) + ' 様',
    '',
    'AirAdmin8 Roboticsへお問い合わせいただき、ありがとうございます。',
    '以下の内容で受け付けました。内容を確認のうえ、担当よりご連絡します。',
    '',
    '問い合わせID：' + inquiryId,
    '相談区分：' + clean_(p.category),
    '製品・メーカー：' + (clean_(p.product) || '未定'),
    '',
    '※このメールはお問い合わせ受付時に自動送信しています。',
    '※追加情報がある場合は、このメールへの返信ではなく airobot@robotics.air-admin8.co.jp までご連絡ください。',
    '',
    'AirAdmin8 Robotics',
    'https://robotics.air-admin8.co.jp/'
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
  const sheet = SpreadsheetApp.openById(INQUIRY_CONFIG.spreadsheetId)
    .getSheetByName(INQUIRY_CONFIG.sheetName);
  if (!sheet) throw new Error('Inquiry sheet not found');
  return sheet;
}

function clean_(value) {
  return String(value == null ? '' : value).trim().slice(0, 10000);
}

function responseHtml_(payload) {
  const json = JSON.stringify({
    type: 'aa8-inquiry-response',
    ok: !!payload.ok,
    inquiryId: payload.inquiryId || '',
    responseToken: payload.responseToken || '',
    duplicate: !!payload.duplicate,
    error: payload.error || ''
  }).replace(/</g, '\\u003c');

  return HtmlService.createHtmlOutput(
    '<!doctype html><html lang="ja"><head><meta charset="utf-8"></head><body>' +
    '<script>window.top.postMessage(' + json + ',' + JSON.stringify(INQUIRY_CONFIG.parentOrigin) + ');<\/script>' +
    '</body></html>'
  );
}
