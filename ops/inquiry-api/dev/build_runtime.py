from pathlib import Path
import json, re, hashlib, subprocess

root = Path.home() / 'aa8-inquiry-dev-install-20261103'
repo = root / 'candidate'
source = repo / 'ops/inquiry-api/Code.gs'
base = source.read_text(encoding='utf-8')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip() == '06c16a01b9062808fe00033d57529e131c471e9f'
assert "spreadsheetId: '1dgoeLCBJVE0CXBGgizUwA-ozrRVvJw6Ng9gfGN0h8wI'" in base
sid = '1qHrw3h4siVwwga-fsN4B3pP2ljvbfrJjXzM1AC4qQsCMDlVQ_7TylZy9'
sheet = '1PzfHiB50jFDHCosMGTb7MUvbQ9nC3UD5pHjgHbpY9Qk'
batch = 'AA8-DEV-20261103-R1'
headers = ['inquiry_id','received_at','status','category','organization','name','email','phone','product','use_case','budget','schedule','development','message','source_page','source_product','source_maker','source_service','source_theme','source_case','utm_source','utm_medium','utm_campaign','ga_client_id','server_result','notified_at','submission_token']
base = base.replace("spreadsheetId: '1dgoeLCBJVE0CXBGgizUwA-ozrRVvJw6Ng9gfGN0h8wI'",f"spreadsheetId: '{sheet}'",1).replace("notifyTo: 'airobot@robotics.air-admin8.co.jp'","notifyTo: 'ceo@air-admin8.co.jp'",1).replace("parentOrigin: 'https://robotics.air-admin8.co.jp'","parentOrigin: 'http://127.0.0.1:4173'",1)
original_get = "function doGet() {\n  return HtmlService.createHtmlOutput('AirAdmin8 Robotics Inquiry API');\n}"
assert base.count(original_get) == 1
base = base.replace(original_get,"function doGet(e) { return devInquiryForm_(e); }",1)
base = base.replace('function validateInquiry_(p) {','function validateInquiry_(p) {\n  devInquiryPayloadGuard_(p);',1)
base = base.replace('function getInquirySheet_() {','function getInquirySheet_() {\n  devInquiryEnvironmentGuard_();',1)
base = base.replace("if (!sheet) throw new Error('Inquiry sheet not found');", "if (!sheet) throw new Error('Inquiry sheet not found');\n  if (JSON.stringify(sheet.getRange(1, 1, 1, 27).getValues()[0]) !== JSON.stringify(AA8_DEV.headers)) throw new Error('DEV_SCHEMA_MISMATCH');",1)
base = base.replace("const subject = '【AirAdmin8 Robotics問い合わせ】'", "const subject = '[DEV ONLY][' + AA8_DEV.batch + ']【AirAdmin8 Robotics問い合わせ】'",1)
base = base.replace("const subject = '【AirAdmin8 Robotics】お問い合わせを受け付けました';", "const subject = '[DEV ONLY][' + AA8_DEV.batch + ']【AirAdmin8 Robotics】お問い合わせを受け付けました';",1)
base = base.replace('function sendInquiryNotification_(inquiryId, p) {','function sendInquiryNotification_(inquiryId, p) {\n  devInquiryPayloadGuard_(p);',1)
base = base.replace('function sendCustomerAcknowledgement_(inquiryId, p) {','function sendCustomerAcknowledgement_(inquiryId, p) {\n  devInquiryPayloadGuard_(p);',1)
idx = base.index('function responseHtml_(payload) {')
base = base[:idx] + 'function responseHtml_(payload) { return devInquiryResponse_(payload); }\n'
config = {'scriptId':sid,'spreadsheetId':sheet,'batch':batch,'recipient':'ceo@air-admin8.co.jp','tokens':[batch+'-A',batch+'-B'],'headers':headers}
guard = '''/** DEV ONLY. Same existing project and ledger. No production/customer writer. */
const AA8_DEV = Object.freeze(CONFIG);
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
  const action = 'https://script.google.com/macros/s/AKfycby56N_DdpwQRPRmQmZA9I6Dt5Sk4sME5vApJUYOTTTG2NG9qIMGfKGygvoPoavsW5Tv8A/exec';
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
  const u = 'https://script.google.com/macros/s/AKfycby56N_DdpwQRPRmQmZA9I6Dt5Sk4sME5vApJUYOTTTG2NG9qIMGfKGygvoPoavsW5Tv8A/exec';
  const links = ['A','B','CONFLICT_A','EXTERNAL'].map(c=>'<a target="_top" href="'+devHtml_(u)+'?case='+c+'">'+c+'</a>').join(' | ');
  return HtmlService.createHtmlOutput('<!doctype html><html><head><base target="_top"></head><body><h1>DEV RECEIPT</h1><pre id="result">'+devHtml_(JSON.stringify(result,null,2))+'</pre><p>'+links+'</p></body></html>');
}
'''.replace('CONFIG',json.dumps(config,ensure_ascii=False),1)
manifest = {'timeZone':'Asia/Tokyo','dependencies':{},'exceptionLogging':'STACKDRIVER','runtimeVersion':'V8',
 'oauthScopes':['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/script.send_mail','https://www.googleapis.com/auth/userinfo.email'],
 'webapp':{'executeAs':'USER_DEPLOYING','access':'MYSELF'}}
runtime=root/'runtime'; runtime.mkdir(exist_ok=False)
(runtime/'Code.js').write_text(base,encoding='utf-8')
(runtime/'DEV_Guard.js').write_text(guard,encoding='utf-8')
(runtime/'CRM_Handoff_Contract.js').write_text((repo/'ops/inquiry-api/CRM_Handoff_Contract.gs').read_text(encoding='utf-8'),encoding='utf-8')
(runtime/'appsscript.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
(runtime/'.clasp.json').write_text(json.dumps({'scriptId':sid,'rootDir':'.','scriptExtensions':['.js','.gs'],'htmlExtensions':['.html'],'jsonExtensions':['.json'],'skipSubdirectories':True},indent=2),encoding='utf-8')
assert all(x not in base+guard for x in ['1dgoeLCBJVE0CXBGgizUwA-ozrRVvJw6Ng9gfGN0h8wI','1nLu-r8zOMFUOAXPNgt4msdAwLMb29ona0DizG-HICes','airobot@robotics.air-admin8.co.jp','UrlFetchApp','newTrigger'])
for path in runtime.glob('*.js'): subprocess.run(['node','--check',str(path)],check=True)
checks = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in runtime.iterdir() if p.is_file()}
(root/'runtime-sha256.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
# Keep auditable runtime source in the original PR; .clasp remains local only.
dest=repo/'ops/inquiry-api/dev'; dest.mkdir(exist_ok=True)
(dest/'DEV_Guard.gs').write_text(guard,encoding='utf-8')
(dest/'appsscript.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
(dest/'Code.dev.gs').write_text(base,encoding='utf-8')
print(json.dumps({'runtime':str(runtime),'files':checks,'productionIdsInExecutableCode':False,'recipient':config['recipient'],'access':'MYSELF','maxNewInquiries':2,'crmWriter':'NOT_CONNECTED'},indent=2))
