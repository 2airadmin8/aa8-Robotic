'use strict';
/** Read-only contract tests. NEVER call a real Apps Script deployment. */
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const sourcePath = path.join(__dirname, '..', 'ops', 'inquiry-api', 'Code.gs');
const original = fs.readFileSync(sourcePath, 'utf8');
const PROD_SHEET = '1dgoeLCBJVE0CXBGgizUwA-ozrRVvJw6Ng9gfGN0h8wI';
const DEV_SHEET = '1PzfHiB50jFDHCosMGTb7MUvbQ9nC3UD5pHjgHbpY9Qk';
const TEST_NOTIFY = 'ceo@air-admin8.co.jp';
const base = (token = 'submission-dev-qa') => ({
  category: '導入条件整理', organization: 'AirAdmin8 Internal QA',
  name: 'QA-Only', email: 'qa@example.test', use_case: 'QA simulation only',
  product: 'Unitree H2 Plus', source_page: 'https://robotics.air-admin8.co.jp/products/unitree-h2-plus.html',
  source_product: 'Unitree H2 Plus', source_maker: 'Unitree',
  submission_token: token, response_token: 'response-qa', website: ''
});

function harness() {
  const rows = [], mails = [], opened = [];
  let id = 0;
  let failTo = '';
  // Memory-only patch. No clasp push, doPost network, API access, or customer data.
  const isolated = original.replace(PROD_SHEET, DEV_SHEET)
    .replace("notifyTo: 'airobot@robotics.air-admin8.co.jp'", "notifyTo: '"+TEST_NOTIFY+"'")
    .replace("parentOrigin: 'https://robotics.air-admin8.co.jp'", "parentOrigin: 'http://127.0.0.1:4173'");
  assert(!isolated.includes(PROD_SHEET), 'production ID must be absent from simulated code');
  const sheet = {
    appendRow: values => { assert.equal(values.length, 27); rows.push([...values]); },
    getLastRow: () => rows.length + 1,
    getRange: (start, col, count = 1, width = 1) => ({
      getValues: () => Array.from({length:count}, (_,i)=> Array.from({length:width}, (_,j)=>rows[start + i - 2][col + j - 1])),
      getValue: () => rows[start - 2][col - 1],
      setValue: value => { rows[start - 2][col - 1] = value; }
    })
  };
  const context = vm.createContext({
    SpreadsheetApp: {openById: sheetId => {assert.equal(sheetId, DEV_SHEET);opened.push(sheetId);return {getSheetByName: name=>{assert.equal(name,'01_Inquiry');return sheet;}};}},
    LockService: {getScriptLock:()=>({waitLock:()=>{},releaseLock:()=>{}})},
    Utilities: {formatDate:()=> '20261103-120000',getUuid:()=> 'ABCD'+String(++id).padStart(4,'0')+'-DEMO'},
    HtmlService: {createHtmlOutput: html=>({html})},
    MailApp: {sendEmail: msg=>{if(msg.to===failTo)throw new Error('MOCK_NOTIFICATION_FAILURE');mails.push(msg);}},
    console: {error:()=>{}},
    Date,JSON,String,Object,Array,Error
  });
  vm.runInContext(isolated, context);
  return {
    rows, mails, opened,
    setFailTo: x=>{failTo=x;},
    post: p => {
      const html = context.doPost({parameter:p}).html;
      const match = html.match(/window\.top\.postMessage\((\{.*?\}),/s);
      assert(match, 'GAS postMessage contract');
      return JSON.parse(match[1]);
    }
  };
}

test('DEV mock: canonical sheet ID is isolated and exactly 27 fields are recorded', ()=>{
  const h=harness(),r=h.post(base());
  assert.equal(r.ok,true);assert.match(r.inquiryId,/^INQ-/);
  assert.deepEqual(h.opened,[DEV_SHEET,DEV_SHEET,DEV_SHEET,DEV_SHEET,DEV_SHEET].slice(0,h.opened.length));
  assert.equal(h.rows.length,1);
  assert.equal(h.rows[0][15],'Unitree H2 Plus');
  assert.equal(h.rows[0][16],'Unitree');
  assert.equal(h.rows[0][26],'submission-dev-qa');
  assert.equal(h.rows[0][24],'NOTIFIED');
  assert.equal(h.mails.length,2);
  assert.equal(h.mails[0].to,TEST_NOTIFY);
});

test('DEV mock: identical submission_token is idempotent',()=>{
  const h=harness(),p=base();
  const first=h.post(p),second=h.post(p);
  assert.equal(first.inquiryId,second.inquiryId);
  assert.equal(second.duplicate,true);
  assert.equal(h.rows.length,1);
  assert.equal(h.mails.length,2);
});

test('DEV mock: separate tokens produce separate IDs',()=>{
  const h=harness(),a=h.post(base('submission-first')),b=h.post(base('submission-second'));
  assert.notEqual(a.inquiryId,b.inquiryId);assert.equal(h.rows.length,2);
});

test('KNOWN GAP: same token with changed payload is acknowledged as old record',()=>{
  const h=harness(),p=base(),a=h.post(p);
  const b=h.post({...p,product:'Different Robot',source_product:'Different Robot'});
  assert.equal(a.inquiryId,b.inquiryId);assert.equal(h.rows.length,1);
  assert.equal(h.rows[0][8],'Unitree H2 Plus');
  assert.notEqual(h.rows[0][8],'Different Robot');
});

test('KNOWN GAP: internal mail failure records FAILED but success ACK; duplicate cannot safely resend',()=>{
  const h=harness(),p=base();
  h.setFailTo(TEST_NOTIFY);
  const r=h.post(p);
  assert.equal(r.ok,true);assert.equal(h.rows.length,1);
  assert.equal(h.rows[0][24],'FAILED');
  h.setFailTo('');
  const repeat=h.post(p);
  assert.equal(repeat.duplicate,true);
  assert.equal(h.mails.length,0);
});

test('KNOWN GAP: acknowledgment mail failure hides already-sent internal mail',()=>{
  const h=harness(),p=base();h.setFailTo('qa@example.test');
  const r=h.post(p);
  assert.equal(r.ok,true);assert.equal(h.rows[0][24],'FAILED');
  assert.equal(h.mails.length,1);
  assert.equal(h.mails[0].to,TEST_NOTIFY);
});

test('IDENTITY GATE: inquiry GAS has no CanonicalCustomerID/Identity-Dedup or CRM case writer',()=>{
  assert(!original.includes('CanonicalCustomerID'));
  assert(!original.includes('00_新規受付'));
  assert(!original.includes('IdentityResolver'));
  assert(!original.includes('CanonicalCaseID'));
});

test('DEV SAFETY GATE: unpatched GAS explicitly targets PRODUCTION and must not be used as DEV',()=>{
  assert(original.includes(PROD_SHEET));
  assert(original.includes("parentOrigin: 'https://robotics.air-admin8.co.jp'"));
  assert(original.includes("notifyTo: 'airobot@robotics.air-admin8.co.jp'"));
});
