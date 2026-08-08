const INQUIRY_CONFIG = {
  spreadsheetId: '1dgoeLCBJVE0CXBGgizUwA-ozrRVvJw6Ng9gfGN0h8wI',
  sheetName: '01_Inquiry',
  notifyTo: 'airobot@robotics.air-admin8.co.jp',
  successRedirect: 'https://robotics.air-admin8.co.jp/contact-thanks.html',
  timezone: 'Asia/Tokyo'
};

function doGet() {
  return HtmlService.createHtmlOutput('AirAdmin8 Robotics Inquiry API');
}

function doPost(e) {
  try {
    const p = (e && e.parameter) || {};
    validateInquiry_(p);

    const lock = LockService.getScriptLock();
    lock.waitLock(10000);

    let inquiryId;
    try {
      inquiryId = createInquiryId_();
      appendInquiry_(inquiryId, p);
      sendInquiryNotification_(inquiryId, p);
      markNotified_(inquiryId);
    } finally {
      lock.releaseLock();
    }

    return redirectHtml_(
      INQUIRY_CONFIG.successRedirect + '?status=success&id=' + encodeURIComponent(inquiryId)
    );
  } catch (error) {
    console.error(error && error.stack ? error.stack : error);
    return HtmlService.createHtmlOutput(
      '<!doctype html><html lang="ja"><meta charset="utf-8"><title>送信エラー</title>' +
      '<body><h1>送信できませんでした</h1><p>入力内容をご確認のうえ、もう一度お試しください。</p>' +
      '<p><a href="https://robotics.air-admin8.co.jp/contact.html">問い合わせ画面へ戻る</a></p></body></html>'
    );
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

function appendInquiry_(inquiryId, p) {
  const sheet = SpreadsheetApp.openById(INQUIRY_CONFIG.spreadsheetId)
    .getSheetByName(INQUIRY_CONFIG.sheetName);
  if (!sheet) throw new Error('Inquiry sheet not found');

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
    'SAVED',
    ''
  ]);
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
    subject,
    body,
    name: 'AirAdmin8 Robotics Inquiry'
  });
}

function markNotified_(inquiryId) {
  const sheet = SpreadsheetApp.openById(INQUIRY_CONFIG.spreadsheetId)
    .getSheetByName(INQUIRY_CONFIG.sheetName);
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return;

  const ids = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
  for (let i = ids.length - 1; i >= 0; i--) {
    if (ids[i][0] === inquiryId) {
      sheet.getRange(i + 2, 25).setValue('NOTIFIED');
      sheet.getRange(i + 2, 26).setValue(new Date());
      return;
    }
  }
}

function clean_(value) {
  return String(value == null ? '' : value).trim().slice(0, 10000);
}

function redirectHtml_(url) {
  const safe = String(url).replace(/&/g, '&amp;').replace(/"/g, '&quot;');
  return HtmlService.createHtmlOutput(
    '<!doctype html><html lang="ja"><head><meta charset="utf-8">' +
    '<meta http-equiv="refresh" content="0;url=' + safe + '"></head>' +
    '<body><p>送信が完了しました。移動します。</p>' +
    '<script>location.replace(' + JSON.stringify(url) + ');<\/script></body></html>'
  );
}
