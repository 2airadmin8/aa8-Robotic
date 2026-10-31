import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const src=fs.readFileSync('tests/fixtures/sales-head-syncWebEngagement-patched.js.txt','utf8');
const REAL='DLV-20990101-SYNTHQA-001';
const SYN='DLV-TEST-SYNTHQA-20261101-001';
const HEAD=['取得日時','送信管理ID','大学名','先生氏名','イベント日時','ページ種別',
            'ページパス','製品ID','閲覧回数','PDF閲覧回数','最終PDF閲覧日時','データソース'];
function event(id,kind,source='VERCEL_WEB_EVENT',when='2026-11-01T10:15:00Z'){
 return [new Date(),id,'SYNTHETIC_ORG','SYNTHETIC_RESEARCHER',when,kind,
         '/products/unitree-h2-plus.html','unitree-h2-plus',0,0,'',source];
}
function setup(events, initialDate=''){
 const queue=[
  ['送信管理ID','最終反応日時'],
  [SYN,initialDate],
  [REAL,initialDate],
 ];
 const web=[HEAD,...events];
 const properties={};
 const queueSheet={
  getDataRange:()=>({getValues:()=>queue.map(row=>[...row])})
 };
 const webSheet={getDataRange:()=>({getValues:()=>web.map(row=>[...row])})};
 const context=vm.createContext({
  JSON,Date,Math,String,Number,Array,Object,
  console:{log:()=>{},error:()=>{}},
  SALES_IMPORT_APP:{QUEUE_SHEET:'メール送信管理'},
  getSalesSpreadsheet_:()=>({getSheetByName:n=>n==='メール送信管理'?queueSheet:n==='Web行動ログ'?webSheet:null}),
  headerMap_:h=>Object.fromEntries(h.map((k,i)=>[k,i])),
  validateHeaders_:(map,names)=>{for(const name of names)if(!(name in map))throw Error('missing '+name)},
  value_:(row,map,name)=>row[map[name]],
  clean_:x=>String(x??'').trim(),
  asDate_:x=>x?new Date(x):null,
  setQueueValue_:(sh,row,headers,name,value)=>{if(sh!==queueSheet)throw Error('incorrect sheet');queue[row-1][headers[name]]=value;},
  PropertiesService:{getScriptProperties:()=>({setProperty:(name,value)=>{properties[name]=value;}})},
  formatNow_:()=> 'SYNTHETIC_NOW',
  SpreadsheetApp:{flush:()=>{}}
 });
 vm.runInContext(src,context);
 return {queue,web,properties,run:()=>context.syncWebEngagementFromLog_()};
}
test('TEST event is kept for audit but does not update sales last-reaction',()=>{
 const x=setup([event(SYN,'TEST_PRODUCT_CLICK','VERCEL_WEB_EVENT_TEST')]);
 const res=x.run();
 assert.equal(res.mapped,0);assert.equal(res.updated,0);
 assert.equal(x.queue[1][1],'');
 assert.equal(x.queue[2][1],'');
 assert.deepEqual(JSON.parse(x.properties.WEB_ENGAGEMENT_SUMMARY_JSON),{});
});
test('TEST-sourced event is excluded even if page type lacks TEST prefix',()=>{
 const x=setup([event(SYN,'PRODUCT_CLICK','VERCEL_WEB_EVENT_TEST')]);
 assert.equal(x.run().updated,0);
 assert.equal(x.queue[1][1],'');
});
test('TEST-prefixed page type excluded even if source label was legacy',()=>{
 const x=setup([event(SYN,'TEST_PRODUCT_VIEW','VERCEL_WEB_EVENT')]);
 assert.equal(x.run().mapped,0);
 assert.equal(x.queue[1][1],'');
});
test('production click updates only matching real SENT record',()=>{
 const x=setup([
  event(SYN,'TEST_PRODUCT_CLICK','VERCEL_WEB_EVENT_TEST'),
  event(REAL,'PRODUCT_CLICK')
 ]);
 const result=x.run();
 assert.equal(result.mapped,1);
 assert.equal(result.updated,1);
 assert.equal(x.queue[1][1],'');
 assert.ok(x.queue[2][1] instanceof Date);
 assert.equal(x.queue[2][1].toISOString(),'2026-11-01T10:15:00.000Z');
 const stats=JSON.parse(x.properties.WEB_ENGAGEMENT_SUMMARY_JSON);
 assert.equal(Object.hasOwn(stats,REAL),true);
 assert.equal(Object.hasOwn(stats,SYN),false);
});
test('existing non-test PDF record behavior stays unchanged',()=>{
 const x=setup([event(REAL,'PDF','VERCEL_WEB_EVENT','2026-11-01T11:15:00Z')]);
 const r=x.run();
 assert.equal(r.mapped,1);assert.equal(r.updated,1);
 assert.equal(x.queue[2][1].toISOString(),'2026-11-01T11:15:00.000Z');
});
test('older real event never rolls back a later confirmed reaction',()=>{
 const x=setup([event(REAL,'PRODUCT_VIEW','VERCEL_WEB_EVENT','2026-11-01T10:00:00Z')],'2026-11-01T12:30:00Z');
 assert.equal(x.run().updated,0);
 assert.equal(x.queue[2][1],'2026-11-01T12:30:00Z');
});
