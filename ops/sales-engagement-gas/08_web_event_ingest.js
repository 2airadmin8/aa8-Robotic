/**
 * Add this as 08_web_event_ingest.js to the EXISTING airadmin8-haishin project.
 * Same spreadsheet (getSalesSpreadsheet_()) and existing Web行動ログ tab.
 * No new Trigger, Runner, Master, worksheet or email sending.
 *
 * Required GAS Script Property: AA8_WEB_EVENT_SIGNING_SECRET
 * Must equal Vercel AA8_SALES_WEB_EVENT_SIGNING_SECRET.
 * Deploy the EXISTING GAS web app as approved after independent QA.
 *
 * Production deployment is NOT authorized by the source PR alone.
 */
const AA8_WEB_EVENT = Object.freeze({
  accepted: ['lead_page_view','product_view','lead_product_click','lead_contact_click','lead_inquiry_success','pdf_open'],
  idPattern: /^(?:DLV|RSJ)-[A-Za-z0-9._-]{5,153}$/,
  eventPattern: /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i,
  maxSkewMs: 10 * 60 * 1000,
  sheetName: 'Web行動ログ'
});

function aa8WebEventAck_(data) {
  return ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}
function aa8WebEventHex_(bytes) {
  return bytes.map(function(b) {return ('0' + (b & 255).toString(16)).slice(-2);}).join('');
}
function aa8WebEventSecureEqual_(a,b) {
  a=String(a||'');b=String(b||'');
  if(a.length!==64||b.length!==64)return false;
  let diff=0;
  for(let i=0;i<a.length;i++)diff|=a.charCodeAt(i)^b.charCodeAt(i);
  return diff===0;
}
function aa8WebEventVerifyEnvelope_(envelope,secret,now) {
  if(!envelope||typeof envelope!=='object'||typeof envelope.payload!=='string'||envelope.payload.length>4096)return null;
  if(!/^\d{13}$/.test(String(envelope.timestamp||'')))return null;
  const timestamp=Number(envelope.timestamp);
  if(!Number.isFinite(timestamp)||Math.abs(now-timestamp)>AA8_WEB_EVENT.maxSkewMs)return null;
  if(typeof secret!=='string'||secret.length<32)return null;
  const raw=String(envelope.timestamp)+'\n'+envelope.payload;
  const computed=aa8WebEventHex_(Utilities.computeHmacSha256Signature(raw,secret));
  if(!aa8WebEventSecureEqual_(computed,String(envelope.signature||'')))return null;
  let record;
  try{record=JSON.parse(envelope.payload)}catch(_){return null}
  if(!record||record.schema!=='aa8_web_event_v2'||AA8_WEB_EVENT.accepted.indexOf(record.event)<0)return null;
  if(!AA8_WEB_EVENT.idPattern.test(String(record.delivery_id||'')))return null;
  if(!AA8_WEB_EVENT.eventPattern.test(String(record.event_id||'')))return null;
  const date=new Date(record.event_at);
  if(isNaN(date.getTime())||Math.abs(now-date.getTime())>AA8_WEB_EVENT.maxSkewMs)return null;
  if(!/^\/[A-Za-z0-9/_\-.]*$/.test(String(record.page_path||''))||String(record.page_path).includes('..'))return null;
  if(record.target_path&&!/^\/[A-Za-z0-9/_\-.]*$/.test(String(record.target_path)))return null;
  if(record.event==='product_view'&&record.page_path!=='/products/'+record.product_id+'.html')return null;
  if(record.event==='lead_product_click'&&record.target_path!=='/products/'+record.target_product_id+'.html')return null;
  return record;
}

function doPost(e) {
  // This GAS script currently has doGet but no doPost.
  // Keep the existing email-open doGet handler unchanged.
  try {
    const json=JSON.parse(String(e&&e.postData&&e.postData.contents||'{}'));
    const secret=PropertiesService.getScriptProperties().getProperty('AA8_WEB_EVENT_SIGNING_SECRET')||'';
    const record=aa8WebEventVerifyEnvelope_(json,secret,Date.now());
    if(!record)return aa8WebEventAck_({ok:false,error:'unauthorized_or_invalid'});
    const lock=LockService.getScriptLock();
    if(!lock.tryLock(8000))return aa8WebEventAck_({ok:false,error:'busy'});
    try {
      return aa8WebEventAck_(aa8WebEventPersist_(record));
    } finally {lock.releaseLock();}
  } catch (_) {
    // No raw email, event content, signed token or secret in public error logs.
    return aa8WebEventAck_({ok:false,error:'ingest_failed'});
  }
}

function aa8WebEventPersist_(r) {
  const ss=getSalesSpreadsheet_();
  const queue=ss.getSheetByName(SALES_IMPORT_APP.QUEUE_SHEET);
  const log=ss.getSheetByName(AA8_WEB_EVENT.sheetName);
  if(!queue||!log)return {ok:false,error:'existing_sheet_missing'};
  const data=queue.getDataRange().getValues();
  if(data.length<2)return {ok:false,error:'empty_sales_queue'};
  const h=headerMap_(data[0]);
  validateHeaders_(h,['送信管理ID','ステータス','大学名','先生氏名'],SALES_IMPORT_APP.QUEUE_SHEET);
  const matches=[];
  for(let i=1;i<data.length;i++){
    if(String(value_(data[i],h,'送信管理ID')||'').trim()===r.delivery_id) matches.push(data[i]);
  }
  // A delivery ID is not proof of identity. Verify ONE SENT queue row.
  if(matches.length!==1)return {ok:false,error:'unknown_or_duplicate_delivery'};
  const customer=matches[0];
  const status=String(value_(customer,h,'ステータス')||'').trim();
  if(status!=='送信済'&&status!=='SENT')return {ok:false,error:'delivery_not_sent'};

  const headers=log.getRange(1,1,1,Math.max(log.getLastColumn(),12)).getValues()[0];
  const existing=['取得日時','送信管理ID','大学名','先生氏名','イベント日時','ページ種別','ページパス','製品ID','閲覧回数','PDF閲覧回数','最終PDF閲覧日時','データソース'];
  for(let i=0;i<existing.length;i++){
    if(String(headers[i]||'').trim()!==existing[i])return {ok:false,error:'web_log_header_mismatch'};
  }
  const eventCol=13,originCol=14;
  if(headers[eventCol-1]&&headers[eventCol-1]!=='イベントID')return {ok:false,error:'event_id_col_conflict'};
  if(headers[originCol-1]&&headers[originCol-1]!=='遷移元パス')return {ok:false,error:'source_path_col_conflict'};
  // Add columns ONLY to the original Web行動ログ, never a new sheet.
  if(log.getMaxColumns()<originCol)log.insertColumnsAfter(log.getMaxColumns(),originCol-log.getMaxColumns());
  if(!headers[eventCol-1])log.getRange(1,eventCol).setValue('イベントID');
  if(!headers[originCol-1])log.getRange(1,originCol).setValue('遷移元パス');
  const last=log.getLastRow();
  if(last>1){
    const seen=log.getRange(2,eventCol,last-1,1).getValues();
    if(seen.some(function(row){return String(row[0]||'')===r.event_id}))
      return {ok:true,persisted:true,duplicate:true};
  }
  const at=new Date(r.event_at);
  const displayTypes={
    lead_page_view:'WEB_VIEW',product_view:'PRODUCT_VIEW',lead_product_click:'PRODUCT_CLICK',
    lead_contact_click:'CONTACT_CLICK',lead_inquiry_success:'INQUIRY_CONFIRMED',pdf_open:'PDF'
  };
  const kind=displayTypes[r.event];
  if(!kind)return {ok:false,error:'unsupported_event'};
  const product=(r.event==='lead_product_click'?r.target_product_id:r.product_id)||'';
  const path=r.event==='lead_product_click'?r.target_path:r.page_path;
  const isPdf=r.event==='pdf_open';
  // Avoid double-counting one actual page view as two because product_view is
  // a secondary SKU-specific event. Source row remains available for analysis.
  const views=r.event==='lead_page_view'||isPdf?1:0;
  log.appendRow([
    new Date(),r.delivery_id,String(value_(customer,h,'大学名')||''),
    String(value_(customer,h,'先生氏名')||''),at,kind,path,product,
    views,isPdf?1:0,isPdf?at:'','VERCEL_WEB_EVENT',
    r.event_id,r.page_path
  ]);
  SpreadsheetApp.flush();
  return {ok:true,persisted:true,duplicate:false};
}
