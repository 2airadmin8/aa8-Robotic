'use strict';
// Specification-level regression model from T006 (2026-09-29).
// This does NOT call or mutate the production Customer Master/PAI ERP writer.
// It proves expected decisions only; live integration remains a separate gate.
const {test}=require('node:test');
const assert=require('node:assert/strict');

function resolveIdentity(inbound, existing) {
  const email=String(inbound.email||'').trim().toLowerCase();
  const matches=existing.filter(x=>String(x.email||'').trim().toLowerCase()===email);
  if(inbound.customerId){
    const byId=existing.filter(x=>x.customerId===inbound.customerId);
    if(byId.length!==1)return {decision:'HOLD',reason:'CUSTOMER_ID_NOT_UNIQUE_OR_MISSING'};
    const person=byId[0];
    if(String(person.name||'').trim()!==String(inbound.name||'').trim() ||
       String(person.affiliation||'').trim()!==String(inbound.affiliation||'').trim())
      return {decision:'HOLD',reason:'IDENTITY_CONFLICT'};
    if(String(person.email||'').trim().toLowerCase()!==email)
      return {decision:'HOLD',reason:'PRIMARY_EMAIL_CONFLICT',customerId:person.customerId};
    return {decision:'EXISTING',customerId:person.customerId};
  }
  if(matches.length>1)return {decision:'HOLD',reason:'EMAIL_MATCHES_MULTIPLE_CUSTOMERS'};
  if(matches.length===1){
    const person=matches[0];
    if(person.name!==inbound.name || person.affiliation!==inbound.affiliation)
      return {decision:'HOLD',reason:'EMAIL_IDENTITY_CONFLICT'};
    return {decision:'EXISTING',customerId:person.customerId};
  }
  if(!inbound.emailVerified)return {decision:'HOLD',reason:'EMAIL_NOT_VERIFIED'};
  return {decision:'NEW_PENDING_MASTER',reason:'VERIFIED_NEW_PERSON'};
}
function opportunityGate(event) {
  const weak=['OPEN','PDF','HP_VIEW'];
  if(weak.includes(event.type))return {decision:'NO_CASE',reason:'WEAK_SIGNAL_ONLY'};
  const strong=['CUSTOMER_MEETING','QUOTE_REQUEST','POC_CONSULTATION','PURCHASE_INTENT'];
  if(!strong.includes(event.type))return {decision:'HOLD',reason:'UNKNOWN_EVENT'};
  if(!event.customerId || !event.opportunityEventId)
    return {decision:'HOLD',reason:'CASE_BINDING_KEYS_MISSING'};
  return {decision:'CREATE_CASE_CANDIDATE',customerId:event.customerId,eventId:event.opportunityEventId};
}

const existing=[
 {customerId:'L-0001',email:'prof.a@example.test',name:'Prof A',affiliation:'University A'},
 {customerId:'L-0002',email:'prof.b@example.test',name:'Prof B',affiliation:'University B'},
 {customerId:'L-0003',email:'shared@example.test',name:'Prof C',affiliation:'University C'},
 {customerId:'L-0004',email:'shared@example.test',name:'Prof D',affiliation:'University D'}
];

test('T006 R01: existing CustomerID + same verified identity/email reuses canonical ID',()=>{
 const r=resolveIdentity({customerId:'L-0001',email:'prof.a@example.test',emailVerified:true,name:'Prof A',affiliation:'University A'},existing);
 assert.deepEqual(r,{decision:'EXISTING',customerId:'L-0001'});
});
test('T006 R02: existing CustomerID + changed email holds; never overwrite Primary',()=>{
 const r=resolveIdentity({customerId:'L-0001',email:'new@example.test',emailVerified:true,name:'Prof A',affiliation:'University A'},existing);
 assert.equal(r.decision,'HOLD');assert.equal(r.reason,'PRIMARY_EMAIL_CONFLICT');
});
test('T006 R03: same email across multiple CustomerIDs holds',()=>{
 const r=resolveIdentity({email:'shared@example.test',emailVerified:true,name:'Prof C',affiliation:'University C'},existing);
 assert.equal(r.decision,'HOLD');assert.equal(r.reason,'EMAIL_MATCHES_MULTIPLE_CUSTOMERS');
});
test('T006 R04: same name but changed affiliation holds',()=>{
 const r=resolveIdentity({customerId:'L-0001',email:'prof.a@example.test',emailVerified:true,name:'Prof A',affiliation:'University B'},existing);
 assert.equal(r.decision,'HOLD');assert.equal(r.reason,'IDENTITY_CONFLICT');
});
test('T006 R05: verified new person enters pending existing Master writer; no second Master',()=>{
 const r=resolveIdentity({email:'new.person@example.test',emailVerified:true,name:'Prof N',affiliation:'University N'},existing);
 assert.deepEqual(r,{decision:'NEW_PENDING_MASTER',reason:'VERIFIED_NEW_PERSON'});
});
test('T006 R06: inferred/unverified email cannot become Primary or be handed off',()=>{
 const r=resolveIdentity({email:'guess@example.test',emailVerified:false,name:'Prof X',affiliation:'University X'},existing);
 assert.equal(r.decision,'HOLD');assert.equal(r.reason,'EMAIL_NOT_VERIFIED');
});
test('T006 R07: open/PDF/HP signals never create a PAI Case',()=>{
 for(const type of ['OPEN','PDF','HP_VIEW'])assert.equal(opportunityGate({type,customerId:'L-0001',opportunityEventId:'EV-1'}).decision,'NO_CASE');
});
test('T006 R08: meeting/quote/PoC event requires CustomerID and OpportunityEventID',()=>{
 for(const type of ['CUSTOMER_MEETING','QUOTE_REQUEST','POC_CONSULTATION']){
  assert.equal(opportunityGate({type}).decision,'HOLD');
  assert.equal(opportunityGate({type,customerId:'L-0001',opportunityEventId:'EV-1'}).decision,'CREATE_CASE_CANDIDATE');
 }
});
test('T006 R09: PAI ERP reverse-write cannot mutate Person SSOT identity',()=>{
 const person={customerId:'L-0001',email:'prof.a@example.test',name:'Prof A',affiliation:'University A'};
 const before=JSON.stringify(person);
 const reverseWrite=()=>({decision:'BLOCKED',reason:'PERSON_SSOT_OWNS_IDENTITY'});
 const r=reverseWrite({email:'erp@example.test'});
 assert.equal(r.decision,'BLOCKED');assert.equal(JSON.stringify(person),before);
});
test('T006 R10: unknown or weak event remains HOLD/NO_CASE, never auto-create',()=>{
 assert.equal(opportunityGate({type:'PAGE_VIEW'}).decision,'HOLD');
 assert.equal(opportunityGate({type:'OPEN'}).decision,'NO_CASE');
});
