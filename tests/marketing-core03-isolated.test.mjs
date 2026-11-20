import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import crypto from 'node:crypto';
import path from 'node:path';
const src=fs.readFileSync('ops/sales-engagement-gas/08_web_event_ingest.js','utf8');
const sha=crypto.createHash('sha256').update(src.replace(/\r\n/g,'\n')).digest('hex');
if(sha!=='a27836b435ef82cf62e2419a068ed093617e7cd3a656aa773f1e8b3e9510821e')throw Error('SHA_NOT_PINNED');
const RID='DLV-TEST-20261120-CORE03',CID='UAT-CUST-20261120-CORE03',TO='sales@air-admin8.co.jp';
const ID='89a2d324-43af-47ad-843b-bdd4ec0321b1',SECRET='synthetic-32-char-test-secret-no-client-data-123456';
class Sheet{
 constructor(data){this.data=data.map(r=>r.slice());this.max=Math.max(12,...this.data.map(r=>r.length));this.corrupt=false}
 getLastRow(){return this.data.length}getMaxColumns(){return this.max}
 getLastColumn(){return Math.max(1,...this.data.map(r=>r.reduce((x,v,i)=>v!==''&&v!==undefined?i+1:x,0)))}
 insertColumnsAfter(a,n){if(a!==this.max)throw Error('BAD_INSERT');this.max+=n}
 getDataRange(){return this.getRange(1,1,this.data.length,this.getLastColumn())}
 getRange(row,col,nr=1,nc=1){return {
  getValues:()=>Array.from({length:nr},(_,i)=>Array.from({length:nc},(_,j)=>this.corrupt&&row===this.data.length&&col===1&&j===12?'corrupted-event-id':this.data[row+i-1]?.[col+j-1]??'')),
  setValue:x=>{this.data[row-1][col-1]=x;},
  setValues:matrix=>{matrix.forEach((arr,i)=>arr.forEach((x,j)=>{this.data[row+i-1][col+j-1]=x}))}
 }}
 appendRow(r){if(r.length>this.max)throw Error('OUT_OF_BOUNDS');this.data.push([...r]);}
}
const H=['取得日時','送信管理ID','大学名','先生氏名','イベント日時','ページ種別','ページパス','製品ID','閲覧回数','PDF閲覧回数','最終PDF閲覧日時','データソース'];
function fixture(){
 const q=new Sheet([['送信管理ID','ステータス','大学名','先生氏名','実行モード','送信承認','顧客ID','宛先メール','配信環境','GmailメッセージID','GmailスレッドID','送信日時'],
 [RID,'送信済','AA8社内UAT大学','内部検証担当','TEST','NO',CID,TO,'TEST','gmail-msg-core03','gmail-thread-core03','2026-11-20T01:10:00Z']]);
 const imp=new Sheet([['配信ID','顧客ID','メールアドレス','送信状態','Message_ID'],[RID,CID,TO,'送信済','gmail-msg-core03']]);
 const hist=new Sheet([['送信管理ID','顧客ID','宛先','送信結果','GmailメッセージID','GmailスレッドID'],[RID,CID,TO,'送信済','gmail-msg-core03','gmail-thread-core03']]);
 const prod=new Sheet([['送信管理ID'],['DLV-20261020-PROD-001']]),web=new Sheet([H]);
 const map={'UAT_Core03_Queue':q,'UAT_Core03_Import':imp,'UAT_Core03_History':hist,'メール送信管理':prod,'Web行動ログ':web};
 const ctx=vm.createContext({console:{log(){},error(){}},JSON,Date,Math,RegExp,Number,String,Array,Object,
  Utilities:{computeHmacSha256Signature:(s,k)=>Array.from(crypto.createHmac('sha256',k).update(s).digest())},
  ContentService:{MimeType:{JSON:'JSON'},createTextOutput:s=>({body:s,setMimeType(){return this}})},
  PropertiesService:{getScriptProperties:()=>({getProperty:n=>n==='AA8_WEB_EVENT_SIGNING_SECRET'?SECRET:''})},
  LockService:{getScriptLock:()=>({tryLock:()=>true,releaseLock(){}})},SpreadsheetApp:{flush(){}},
  SALES_IMPORT_APP:{QUEUE_SHEET:'メール送信管理'},getSalesSpreadsheet_:()=>({getSheetByName:n=>map[n]}),
  headerMap_:h=>Object.fromEntries(h.map((k,i)=>[k,i])),validateHeaders_:(h,ks)=>{for(const k of ks)if(!(k in h))throw Error('MISSING_HEADER_'+k)},
  value_:(row,h,k)=>row[h[k]]
 });
 vm.runInContext(src,ctx);
 const record={schema:'aa8_web_event_v2',event_id:ID,event:'pdf_open',delivery_id:RID,event_at:new Date().toISOString(),page_path:'/resources/document.html',page_type:'document'};
 function call(rec=record,signatureValid=true){const payload=JSON.stringify(rec),timestamp=String(Date.now()),sig=crypto.createHmac('sha256',SECRET).update(timestamp+'\n'+payload).digest('hex');return JSON.parse(ctx.doPost({postData:{contents:JSON.stringify({timestamp,payload,signature:signatureValid?sig:'0'.repeat(64)})}}).body)}
 return {q,imp,hist,prod,web,map,ctx,record,call};
}
const tests=[];
function check(name,fn){test(name,()=>assert.equal(fn(),true))}
check('one new internal Core03 signed PDF event is written and ACKed',()=>{const f=fixture(),a=f.call();return a.ok===true&&a.persisted===true&&a.duplicate===false&&f.web.data.length===2&&f.web.data[1][5]==='TEST_PDF'&&f.web.data[1][8]===0&&f.web.data[1][9]===0&&f.web.data[1][11]==='VERCEL_WEB_EVENT_TEST'});
check('duplicate event is idempotent and cannot inflate TEST ledger',()=>{const f=fixture();f.call();const a=f.call();return a.ok===true&&a.duplicate===true&&f.web.data.length===2});
check('TEST not sent blocks before Web log mutation',()=>{const f=fixture();f.q.data[1][1]='下書き作成済み';return f.call().ok===false&&f.web.data.length===1});
check('TEST email must be company mailbox',()=>{const f=fixture();f.q.data[1][7]='professor@university.example';return f.call().ok===false&&f.web.data.length===1});
check('TEST Import actual sent Message ID required',()=>{const f=fixture();f.imp.data[1][4]='fake-message';return f.call().ok===false&&f.web.data.length===1});
check('TEST History thread must match',()=>{const f=fixture();f.hist.data[1][5]='changed-thread';return f.call().ok===false&&f.web.data.length===1});
check('no parallel PROD delivery id allowed',()=>{const f=fixture();f.prod.data.push([RID]);return f.call().ok===false&&f.web.data.length===1});
check('TEST no CEO send-approval after sent',()=>{const f=fixture();f.q.data[1][5]='YES';return f.call().ok===false&&f.web.data.length===1});
check('TEST original environment must remain TEST',()=>{const f=fixture();f.q.data[1][8]='PROD';return f.call().ok===false&&f.web.data.length===1});
check('missing one UAT SSOT tab blocks',()=>{const f=fixture();delete f.map.UAT_Core03_History;return f.call().ok===false&&f.web.data.length===1});
check('forged HMAC blocks',()=>{const f=fixture();return f.call(f.record,false).ok===false&&f.web.data.length===1});
check('sink write with corrupted readback cannot ACK success',()=>{const f=fixture();f.web.corrupt=true;const a=f.call();return a.ok===false&&a.error==='web_log_readback_failed'&&f.web.data.length===2});
check('unknown TEST ID does not use internal fixture',()=>{const f=fixture();return f.call({...f.record,delivery_id:'DLV-TEST-20990101-UNKNOWN-001'}).ok===false&&f.web.data.length===1});