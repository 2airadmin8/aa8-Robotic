import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import crypto from 'node:crypto';

const root=path.resolve('ops/sales-engagement-gas');
const sources=['08_web_event_ingest.js','09_campaign_summary.js','11_campaign_link_utils.js']
  .map(name=>fs.readFileSync(path.join(root,name),'utf8')).join('\n');
const SECRET='synthetic-32-char-test-secret-no-customer-data-12345';
const RID='DLV-20261020-RM1137-001';
const eventId='89a2d324-43af-47ad-843b-bdd4ec0321b1';
const webHeaders=['取得日時','送信管理ID','大学名','先生氏名','イベント日時','ページ種別','ページパス',
                  '製品ID','閲覧回数','PDF閲覧回数','最終PDF閲覧日時','データソース'];
class Sheet {
 constructor(rows){this.rows=rows.map(r=>[...r]);this.max=Math.max(1,...this.rows.map(r=>r.length))}
 getLastColumn(){return Math.max(1,...this.rows.map(r=>r.reduce((a,v,i)=>v!==''&&v!==undefined?i+1:a,0)))}
 getMaxColumns(){return this.max}
 getLastRow(){return this.rows.length}
 insertColumnsAfter(after,count){if(after!==this.max)throw Error('must insert at tail');this.max+=count}
 getDataRange(){return this.getRange(1,1,this.getLastRow(),this.getLastColumn())}
 getRange(row,col,nr=1,nc=1){
  if(col+nc-1>this.max)throw Error('out of bounds '+col+' max '+this.max);
  return {
   getValues:()=>Array.from({length:nr},(_,i)=>Array.from({length:nc},(_,j)=>this.rows[row-1+i]?.[col-1+j]??'')),
   getDisplayValues:()=>Array.from({length:nr},(_,i)=>Array.from({length:nc},(_,j)=>String(this.rows[row-1+i]?.[col-1+j]??''))),
   setValue:v=>{while(this.rows.length<row)this.rows.push([]);this.rows[row-1][col-1]=v},
   setValues:matrix=>{if(matrix.length!==nr||matrix.some(x=>x.length!==nc))throw Error('bad matrix');
    for(let i=0;i<nr;i++){while(this.rows.length<row+i)this.rows.push([]);
      for(let j=0;j<nc;j++)this.rows[row-1+i][col-1+j]=matrix[i][j]}}
  }
 }
 appendRow(row){if(row.length>this.max)throw Error('append past max');this.rows.push([...row])}
}
function create({status='送信済',oldLogRows=[],openRows=[],duplicateId=false}={}){
 const queue=new Sheet([
  ['送信管理ID','ステータス','大学名','先生氏名'],
  [RID,status,'SYNTHETIC_UNIVERSITY','TEST_RESEARCHER']
 ]);
 const web=new Sheet([webHeaders,...oldLogRows]);
 const open=new Sheet([['送信管理ID','user_agent','is_test'],...openRows]);
 const map={'メール送信管理':queue,'Web行動ログ':web,'EmailOpenLog':open};
 const context=vm.createContext({
  console:{log:()=>{},error:()=>{}},
  JSON,Date,Math,RegExp,Number,String,Array,Object,
  Utilities:{computeHmacSha256Signature:(str,sec)=>Array.from(crypto.createHmac('sha256',sec).update(str).digest())},
  ContentService:{MimeType:{JSON:'JSON'},createTextOutput:s=>({body:s,setMimeType(){return this}})},
  PropertiesService:{getScriptProperties:()=>({getProperty:key=>key==='AA8_WEB_EVENT_SIGNING_SECRET'?SECRET:''})},
  LockService:{getScriptLock:()=>({tryLock:()=>true,releaseLock:()=>{}})},
  SpreadsheetApp:{flush:()=>{}},
  SALES_IMPORT_APP:{QUEUE_SHEET:'メール送信管理'},
  getSalesSpreadsheet_:()=>({getSheetByName:name=>map[name]}),
  headerMap_:h=>Object.fromEntries(h.map((name,i)=>[name,i])),
  validateHeaders_:(map,names,tab)=>{for(const k of names)if(!(k in map))throw Error('missing '+k+' in '+tab)},
  value_:(row,h,key)=>row[h[key]],
  asDate_:x=>{const d=new Date(x);return Number.isNaN(d.getTime())?null:d},
 });
 vm.runInContext(sources,context);
 const record=(data={})=>({
  schema:'aa8_web_event_v2',event_id:eventId,event:'lead_product_click',delivery_id:RID,
  event_at:new Date().toISOString(),page_path:'/products.html',target_path:'/products/unitree-h2-plus.html',
  target_product_id:'unitree-h2-plus',product_id:'',...data
 });
 const envelope=(data={},opts={})=>{
  const value=JSON.stringify(record(data));
  const timestamp=String(opts.timestamp??Date.now());
  const sign=crypto.createHmac('sha256',opts.secret??SECRET).update(timestamp+'\n'+value).digest('hex');
  return {timestamp,payload:value,signature:opts.signature??sign};
 };
 function call(data={},opts={}){const env=envelope(data,opts);return JSON.parse(context.doPost({postData:{contents:JSON.stringify(env)}}).body)}
 return {queue,web,open,context,call,envelope};
}
test('signed click persists exactly once to existing Web行動ログ, with product/path',()=>{
 const c=create();const a=c.call();assert.equal(a.ok,true);assert.equal(a.persisted,true);
 assert.equal(c.web.rows.length,2);assert.equal(c.web.max,14);
 const row=c.web.rows[1];
 assert.equal(row[1],RID);assert.equal(row[5],'PRODUCT_CLICK');
 assert.equal(row[6],'/products/unitree-h2-plus.html');
 assert.equal(row[7],'unitree-h2-plus');assert.equal(row[8],0);
 assert.equal(row[11],'VERCEL_WEB_EVENT');
 assert.equal(row[12],eventId);assert.equal(row[13],'/products.html');
 assert.equal(c.web.rows[0][12],'イベントID');
 assert.equal(c.queue.rows.length,2);
});
test('event_id deduplicated; replay cannot inflate counts',()=>{
 const c=create();assert.equal(c.call().duplicate,false);
 const b=c.call();assert.equal(b.ok,true);assert.equal(b.duplicate,true);
 assert.equal(c.web.rows.length,2);
});
test('reject forged payloads/signatures and stale events without altering sheets',()=>{
 const c=create();const initial=c.web.rows.length;
 for(const options of [
  {secret:'wrong-secret-xxxxxxxxxxxxxxxxxxxxxxxxx'},
  {signature:'0'.repeat(64)},
  {timestamp:Date.now()-30*60*1000}
 ])assert.equal(c.call({},options).ok,false);
 assert.equal(c.web.rows.length,initial);
});
test('do not record unknown or unsent delivery ID',()=>{
 let a=create({status:'未作成'});assert.equal(a.call().ok,false);assert.equal(a.web.rows.length,1);
 a=create();assert.equal(a.call({delivery_id:'DLV-20261020-RM9999-001'}).ok,false);assert.equal(a.web.rows.length,1);
});
test('PDF landing records are not falsely counted as confirmed PDF reading',()=>{
 const c=create();const value=c.call({event:'pdf_open',page_path:'/resources/document.html',target_path:'',
   target_product_id:'',product_id:''});
 assert.equal(value.ok,true);
 const row=c.web.rows[1];
 assert.equal(row[5],'PDF');assert.equal(row[9],1);
 assert.equal(row[7],'');assert.equal(row[6],'/resources/document.html');
});
test('summary reuses original sales sheet, records clicked product and proxy uncertainty',()=>{
 const c=create({openRows:[[RID,'Mozilla/5.0 (via ggpht.com GoogleImageProxy)','NO']]});
 c.call();
 const result=c.context.syncAa8WebMarketingSummary_();
 assert.equal(result.ok,true);
 assert.equal(c.queue.rows.length,2);
 assert.equal(c.queue.rows[0][4],'Web閲覧数');
 assert.equal(c.queue.rows[1][6],1);
 assert.equal(c.queue.rows[1][7],'unitree-h2-plus');
 assert.equal(c.queue.rows[1][10],'画像代理取得のみ・真人未確認');
});
test('open events with real browser UA still NOT assert a verified human',()=>{
 const c=create({openRows:[[RID,'Mozilla/5.0 Chrome/156','NO']]});
 const result=c.context.syncAa8WebMarketingSummary_();
 assert.equal(result.ok,true);
 assert.equal(c.queue.rows[1][10],'開封観測・真人未確認');
});
test('test opens excluded from production sales assessment',()=>{
 const c=create({openRows:[[RID,'Mozilla/5.0 Chrome/156','YES']]});
 c.context.syncAa8WebMarketingSummary_();
 assert.equal(c.queue.rows[1][10],'未検出');
});
test('tracked catalog link joins delivery ID and campaign, never an email address',()=>{
 const c=create();let u=c.context.buildTrackedCatalogUrl_(RID);
 const parsed=new URL(u);assert.equal(parsed.searchParams.get('rid'),RID);
 assert.equal(parsed.searchParams.get('utm_source'),'university_sales');
 assert.equal(parsed.pathname,'/products.html');
 assert.ok(!u.includes('@'));
});
test('failed server-side input does not create a second Master or Sheet',()=>{
 const c=create({status:'未作成'});
 assert.equal(c.call().ok,false);
 assert.deepEqual(Object.keys({'a':c.queue,'b':c.web,'c':c.open}).sort(),['a','b','c']);
});
