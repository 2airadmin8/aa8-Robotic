/** DEV ONLY. Same existing project and ledger. No production/customer writer. */
const AA8_DEV = Object.freeze({"scriptId": "1qHrw3h4siVwwga-fsN4B3pP2ljvbfrJjXzM1AC4qQsCMDlVQ_7TylZy9", "spreadsheetId": "1PzfHiB50jFDHCosMGTb7MUvbQ9nC3UD5pHjgHbpY9Qk", "batch": "AA8-DEV-20261103-R1", "recipient": "ceo@air-admin8.co.jp", "tokens": ["AA8-DEV-20261103-R1-A", "AA8-DEV-20261103-R1-B"], "headers": ["inquiry_id", "received_at", "status", "category", "organization", "name", "email", "phone", "product", "use_case", "budget", "schedule", "development", "message", "source_page", "source_product", "source_maker", "source_service", "source_theme", "source_case", "utm_source", "utm_medium", "utm_campaign", "ga_client_id", "server_result", "notified_at", "submission_token"]});
function devInquiryEnvironmentGuard_() {
  if (ScriptApp.getScriptId() !== AA8_DEV.scriptId ||
      INQUIRY_CONFIG.spreadsheetId !== AA8_DEV.spreadsheetId ||
      INQUIRY_CONFIG.notifyTo !== AA8_DEV.recipient ||
      Session.getEffectiveUser().getEmail() !== AA8_DEV.recipient) {
    throw new Error('DEV_ENVIRONMENT_MISMATCH');
  }
}
function devInquiryPayloadGuard_(p) {
  devInquiryEnvironmentGuard_();
  if (!p || !AA8_DEV.tokens.includes(String(p.submission_token)) ||
      String(p.email).trim().toLowerCase() !== AA8_DEV.recipient ||
      p.organization !== 'AirAdmin8 DEV University (INTERNAL TEST ONLY)' ||
      !['INTERNAL QA A','INTERNAL QA B'].includes(p.name) ||
      p.use_case !== AA8_DEV.batch + ' internal acceptance only' ||
      p.privacy !== 'true') throw new Error('DEV_INTERNAL_TEST_ONLY');
  Object.keys(p).forEach(function(k) {
    if (/^[=+@]/.test(String(p[k] || ''))) throw new Error('DEV_UNSAFE_CELL');
  });
}
function devHtml_(x) {
  return String(x == null ? '' : x).replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}
function devFixture_(which) {
  const c = which === 'B' ? 'B' : 'A';
  return {category:'導入条件整理', organization:'AirAdmin8 DEV University (INTERNAL TEST ONLY)',
    name:'INTERNAL QA '+c, email:AA8_DEV.recipient, phone:'', product:'Unitree H2 Plus',
    use_case:AA8_DEV.batch+' internal acceptance only', budget:'TEST ONLY', schedule:'TEST ONLY',
    development:'', message:'DEV acceptance '+c, source_page:'https://robotics.air-admin8.co.jp/products/unitree-h2-plus.html',
    source_product:'Unitree H2 Plus', source_maker:'Unitree', source_service:'', source_theme:'', source_case:'',
    utm_source:'dev_internal', utm_medium:'acceptance', utm_campaign:AA8_DEV.batch, ga_client_id:'', website:'',
    privacy:'true', submission_token:AA8_DEV.batch+'-'+c, response_token:AA8_DEV.batch+'-ACK-'+c};
}
function devInquiryForm_(e) {
  devInquiryEnvironmentGuard_();
  const p = (e && e.parameter) || {}, kind = String(p.case || 'A');
  const data = devFixture_(kind);
  if (kind === 'CONFLICT_A') data.message = 'Changed payload must not overwrite A';
  if (kind === 'EXTERNAL') data.email = 'blocked@example.invalid';
  const action = ScriptApp.getService().getUrl();
  if (!action || !/^https:\/\/script.google.com\/macros\/s\//.test(action)) throw new Error('DEV_SERVICE_URL_UNAVAILABLE');
  const fields = Object.keys(data).map(k => '<input type="hidden" name="'+devHtml_(k)+'" value="'+devHtml_(data[k])+'">').join('');
  const nav = ['A','B','CONFLICT_A','EXTERNAL'].map(c => '<a href="'+devHtml_(action)+'?case='+c+'" target="_top">'+c+'</a>').join(' | ');
  return HtmlService.createHtmlOutput('<!doctype html><html><head><base target="_top"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'+
    '<h1>AirAdmin8 Inquiry DEV ONLY</h1><p>'+devHtml_(AA8_DEV.batch)+'</p><p>Case: '+devHtml_(kind)+'</p>'+
    '<p>Internal recipient: '+devHtml_(AA8_DEV.recipient)+'</p><p>CRM: BLOCKED - verified isolated writer not configured</p>'+
    '<form method="post" action="'+devHtml_(action)+'" target="_top">'+fields+'<button type="submit" style="font-size:24px;padding:16px">SUBMIT '+devHtml_(kind)+' - REAL DEV POST</button></form><p>'+nav+'</p></body></html>');
}
function devInquiryResponse_(payload) {
  const result = {environment:'DEV_ONLY', batch:AA8_DEV.batch, ok:!!payload.ok,
    inquiryId:payload.inquiryId||'', duplicate:!!payload.duplicate, responseToken:payload.responseToken||'',
    error:payload.error||'', crmStatus:'BLOCKED_NO_VERIFIED_ISOLATED_WRITER', customerId:null};
  if (result.ok) {
    try {
      const s = getInquirySheet_(), data = s.getDataRange().getValues();
      const row = data.slice(1).find(r => String(r[0]) === result.inquiryId);
      if (!row) throw new Error('DEV_READBACK_MISSING');
      result.persisted = true; result.serverResult = String(row[24]);
      result.matchingTokenRows = data.slice(1).filter(r => r[26] === row[26]).length;
    } catch (err) { result.persisted = false; result.readbackError = 'DEV_READBACK_FAILED'; }
  }
  const u = ScriptApp.getService().getUrl();
  const links = ['A','B','CONFLICT_A','EXTERNAL'].map(c=>'<a target="_top" href="'+devHtml_(u)+'?case='+c+'">'+c+'</a>').join(' | ');
  return HtmlService.createHtmlOutput('<!doctype html><html><head><base target="_top"></head><body><h1>DEV RECEIPT</h1><pre id="result">'+devHtml_(JSON.stringify(result,null,2))+'</pre><p>'+links+'</p></body></html>');
}
