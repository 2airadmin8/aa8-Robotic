import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import crypto from 'node:crypto';

// Exact doGet function slices extracted from the authenticated airadmin8-haishin
// production @43 snapshot and current approved HEAD on AA8-N-018.
// No real Gmail, GAS or EmailOpenLog call is made by these tests.
const fixture=(name)=>fs.readFileSync('tests/fixtures/sales-'+name+'-doGet.js.txt','utf8');
const v43=fixture('v43'), head=fixture('head');
// Windows git checkout may convert LF to CRLF. Pin the exact UTF-8
// *content* hash while preserving all business-code bytes except line endings.
const canonicalLF=(s)=>s.replace(/\r\n/g,'\n');
const digest=(s)=>crypto.createHash('sha256').update(canonicalLF(s),'utf8').digest('hex');

function exercise(source, parameters={},throwOpen=false){
 const recorded=[],errors=[];
 const context=vm.createContext({
  String,JSON,
  console:{error:(...args)=>errors.push(args.map(String).join(' '))},
  ContentService:{
   MimeType:{TEXT:'TEXT'},
   createTextOutput:(value)=>({
    value, mime:'',
    setMimeType(t){this.mime=t;return this;}
   })
  },
  recordEmailOpen_:(id,isTest)=>{
   recorded.push({id,isTest});
   if(throwOpen)throw Error('synthetic-failure-private-details');
  }
 });
 vm.runInContext(source,context,{timeout:1000});
 const result=context.doGet({parameter:parameters});
 return {value:result.value,mime:result.mime,recorded,errors};
}

test('doGet fixtures are immutable hashes from @43 and current GAS HEAD',()=>{
 assert.equal(digest(v43),'2be621d09982b7bceffdf5212178317b33ef2a20ae86572c46b774ad83976146');
 assert.equal(digest(head),'970bfe4b005c370e9ee686749cfb716ae3a9760107231f39ec9a747b100e849b');
});

test('Windows CRLF and Unix LF yield the exact same approved fixture SHA',()=>{
 for(const [label,source,approved] of [
  ['@43',v43,'2be621d09982b7bceffdf5212178317b33ef2a20ae86572c46b774ad83976146'],
  ['HEAD',head,'970bfe4b005c370e9ee686749cfb716ae3a9760107231f39ec9a747b100e849b']
 ]){
  const unix=canonicalLF(source);
  const windows=unix.replace(/\n/g,'\r\n');
  assert.equal(digest(unix),approved,label+' LF');
  assert.equal(digest(windows),approved,label+' Windows CRLF');
  assert.equal(digest(source),approved,label+' checked-out version');
  // The guard must not hide a real logic change: ONLY newline variants match.
  assert.notEqual(digest(unix.replace('email_open','email_open_changed')),approved,label+' business drift');
 }
});

test('after safe privacy normalization, deployed @43 and HEAD open code is equivalent',()=>{
 const canonical=(s)=>s.replace("'ERROR: ' + msg","'ERROR'").replace(/\s+/g,'');
 assert.equal(canonical(v43),canonical(head));
 assert.equal((head.match(/function doGet\(e\)/g)||[]).length,1);
});

for(const [label,params] of [
 ['plain GET',{}],
 ['unknown action',{action:'health'}],
 ['pixel real',{action:'email_open',sid:'DLV-20990101-SYNTHQA-001',test:'0'}],
 ['pixel synthetic',{action:'email_open',sid:'DLV-TEST-SYNTHQA-20261101-001',test:'1'}]
]){
 test('open compatibility '+label,()=>{
  const old=exercise(v43,params),now=exercise(head,params);
  assert.equal(now.mime,'TEXT');
  assert.equal(now.value,'ok');
  assert.deepEqual(now.recorded,old.recorded);
  assert.equal(now.value,old.value);
  if(params.action==='email_open')assert.equal(now.recorded[0].isTest,params.test==='1');
  else assert.equal(now.recorded.length,0);
 });
}

test('doGet errors fail closed and new HEAD never exposes server-side details',()=>{
 const params={action:'email_open',sid:'DLV-TEST-SYNTHQA-20261101-001',test:'1'};
 const old=exercise(v43,params,true),now=exercise(head,params,true);
 assert.equal(old.mime,'TEXT');assert.equal(now.mime,'TEXT');
 assert.equal(now.value,'ERROR');
 assert.equal(old.value.startsWith('ERROR:'),true);
 assert.ok(!now.value.includes('synthetic-failure-private-details'));
 assert.equal(now.recorded.length,1);
 assert.equal(now.errors.length,1);
});

test('new doPost is separate: it cannot overwrite legacy doGet symbol',()=>{
 assert.equal(v43.includes('function doPost('),false);
 assert.equal(head.includes('function doPost('),false);
 const ingest=fs.readFileSync('ops/sales-engagement-gas/08_web_event_ingest.js','utf8');
 assert.equal((ingest.match(/^function doPost\(e\)/gm)||[]).length,1);
});
