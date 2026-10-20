const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const src = fs.readFileSync('ops/inquiry-api/Code.gs', 'utf8');
const cases = [[false,false,'NOTIFIED'],[true,false,'FAILED'],[false,true,'FAILED'],[true,true,'FAILED']];
for (const [failInternal,failCustomer,expected] of cases) {
  const calls = [], row = [];
  const sheet = {
    getLastRow:()=>row.length ? 2 : 1,
    appendRow:(r)=>row.push(r),
    getRange:(r,c,n)=>({getValues:()=>c===27?row.map(x=>[x[26]]):row.map(x=>[x[0]]),getValue:()=>row[0][c-1],setValue:(v)=>{row[0][c-1]=v;}})
  };
  const context = {console:{error:()=>{}},Date,JSON,String,Error,
    LockService:{getScriptLock:()=>({waitLock:()=>{},releaseLock:()=>{}})},
    SpreadsheetApp:{openById:()=>({getSheetByName:()=>sheet})},
    Utilities:{formatDate:()=> '20261021-000000',getUuid:()=> '12345678-abc'},
    MailApp:{sendEmail:({to})=>{calls.push(to);if(to==='airobot@robotics.air-admin8.co.jp'&&failInternal)throw Error('internal');if(to==='qa@example.com'&&failCustomer)throw Error('customer');}},
    HtmlService:{createHtmlOutput:(html)=>html}
  };
  vm.createContext(context);vm.runInContext(src,context);
  const p={category:'製品比較・選定',organization:'AA8 QA',name:'QA',email:'qa@example.com',use_case:'test',submission_token:'tok1',response_token:'resp1'};
  const first=context.doPost({parameter:p});
  assert.match(first,/"ok":true/);
  assert.equal(row[0][24],expected);
  assert.deepEqual(calls,['airobot@robotics.air-admin8.co.jp','qa@example.com']);
  context.doPost({parameter:p});
  assert.equal(row.length,1);assert.equal(calls.length,2);
  console.log('PASS mail isolation:',failInternal,failCustomer,'status:',expected);
}
