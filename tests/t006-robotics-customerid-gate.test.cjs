const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.resolve(__dirname,'../ops/inquiry-api/T006_Robotics_CustomerID_Gate.gs'),'utf8');
const ctx = vm.createContext({});
vm.runInContext(source,ctx);
const decide = (i,rows,master,e) => ctx.t006RoboticsOfficialAdmission_(i,rows,master,e);
const i={source:'Robotics_Web_Inquiry',inquiryId:'INQ-20261104-000403-D19A8041',
  organization:'東京テスト大学',name:'安全 太郎',email:'qa@example.org'};
const row={source:'Robotics_Web_Inquiry',sourceId:i.inquiryId,
  organization:i.organization,name:i.name,email:i.email,customerId:''};
const proof={origin:'T006_AUTHORIZED_EVIDENCE_WRITER',sourceId:i.inquiryId,
  identityVerified:true,officialEmailVerified:true,duplicateGatePassed:true,
  officialEvidenceUrl:'https://example.ac.jp/researcher',verifiedEmail:i.email,
  verifiedName:i.name,verifiedOrganization:i.organization,conflict:false};
test('Unverified self-report must never create canonical ID',()=>{
  const r=decide(i,[row],[],null);
  assert.equal(r.decision,'HOLD');
  assert.equal(r.existingCustomerId,null);
  assert.equal(r.newCustomerId,null);
});
test('Email-only existing match must not inherit someone else ID',()=>{
  const r=decide(i,[row],[{customerId:'L-0420',primaryEmail:i.email,name:'別人',organization:i.organization}],proof);
  assert.equal(r.reason,'EMAIL_MATCH_IDENTITY_NOT_CONFIRMED');
});
test('Conflicting identity or duplicate SourceID must hold',()=>{
  const masters=[
    {customerId:'L-0420',primaryEmail:i.email,name:'別人',organization:i.organization},
    {customerId:'L-0421',primaryEmail:'different@example.org',name:i.name,organization:i.organization}
  ];
  assert.equal(decide(i,[row],masters,proof).reason,'EMAIL_NAME_AFFILIATION_CONFLICT');
  assert.equal(decide(i,[row,row],[],proof).reason,'DUPLICATE_SOURCE_ID');
});
test('Only independently verified new identity can reach existing writer',()=>{
  const r=decide(i,[row],[],proof);
  assert.equal(r.decision,'READY_REGISTER_NEW');
  assert.equal(r.newCustomerId,null);
  assert.equal(r.writesPerformed,0);
  assert.equal(r.marketingPermission,false);
});
test('Only strong existing identity+email matches may reuse canonical ID',()=>{
  const r=decide(i,[row],[{customerId:'L-0420',primaryEmail:i.email,name:i.name,organization:i.organization}],proof);
  assert.equal(r.decision,'READY_REUSE_EXISTING');
  assert.equal(r.existingCustomerId,'L-0420');
  assert.equal(r.newCustomerId,null);
});
test('Form-provided evidence URL without T006 proof is insufficient',()=>{
  const r=decide(i,[row],[],{...proof,origin:'PUBLIC_FORM'});
  assert.equal(r.decision,'HOLD');
  assert.equal(r.reason,'T006_EVIDENCE_IDENTITY_GATE_REQUIRED');
});


test('QA namespace collision L-0001/L-0002 is not an approved official ID',()=>{
  for(const testId of ['L-0001','L-0002','QA_NONCANONICAL:L-0001']){
    const out=decide(i,[{...row,customerId:testId}],[],proof);
    assert.equal(out.decision,'HOLD');
    assert.equal(out.reason,'CUSTOMER_ID_ALREADY_PRESET_RECONCILE');
    assert.equal(out.existingCustomerId,null);
    assert.equal(out.newCustomerId,null);
    assert.equal(out.writesPerformed,0);
  }
});
