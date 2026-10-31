/**
 * Existing salesEngagementHourlyTrigger_ may invoke this function after
 * syncWebEngagementFromLog_() succeeds; NO new trigger is created.
 * Adds derived columns to the EXISTING メール送信管理 tab, not a new sheet.
 * Open quality is deliberately NOT a proof of human intent.
 */
function syncAa8WebMarketingSummary_() {
  const ss=getSalesSpreadsheet_();
  const queue=ss.getSheetByName(SALES_IMPORT_APP.QUEUE_SHEET);
  const web=ss.getSheetByName('Web行動ログ');
  const open=ss.getSheetByName('EmailOpenLog');
  if(!queue||!web||!open)return {ok:false,error:'existing_sheet_missing'};
  const values=queue.getDataRange().getValues();
  if(values.length<2)return {ok:true,rows:0};
  const h=headerMap_(values[0]);
  validateHeaders_(h,['送信管理ID','実行モード'],SALES_IMPORT_APP.QUEUE_SHEET);
  const required=['Web閲覧数','製品閲覧数','製品リンククリック数','最終クリック製品ID','最終Webページ','最終Web反応日時','開封品質区分'];
  let headers=queue.getRange(1,1,1,queue.getLastColumn()).getDisplayValues()[0];
  const found=required.map(function(name){return headers.indexOf(name)});
  const present=found.filter(function(i){return i>=0});
  // Never overwrite arbitrary business columns if a partial migration exists.
  if(present.length!==0&&present.length!==required.length)
    return {ok:false,error:'partial_derived_columns'};
  let first=queue.getLastColumn()+1;
  if(present.length===required.length){
    first=present[0]+1;
    if(!required.every(function(name,i){return headers[first-1+i]===name}))
      return {ok:false,error:'derived_columns_not_contiguous'};
  }else{
    const need=first+required.length-1-queue.getMaxColumns();
    if(need>0)queue.insertColumnsAfter(queue.getMaxColumns(),need);
    queue.getRange(1,first,1,required.length).setValues([required]);
  }
  const w=web.getDataRange().getValues();
  const wh=headerMap_(w[0]||[]);
  validateHeaders_(wh,['送信管理ID','イベント日時','ページ種別','ページパス','製品ID','データソース'],'Web行動ログ');
  const results=Object.create(null);
  for(let i=1;i<w.length;i++){
    const row=w[i],id=String(value_(row,wh,'送信管理ID')||'').trim();
    const kind=String(value_(row,wh,'ページ種別')||'').trim();
    const source=String(value_(row,wh,'データソース')||'').trim();
    if(!id||kind.startsWith('TEST_')||source==='VERCEL_WEB_EVENT_TEST')continue;
    const date=asDate_(value_(row,wh,'イベント日時'));
    if(!date)continue;
    const obj=results[id]||(results[id]={visits:0,productViews:0,productClicks:0,last:null,lastPath:'',lastProduct:''});
    if(kind==='WEB_VIEW')obj.visits++;
    if(kind==='PRODUCT_VIEW')obj.productViews++;
    if(kind==='PRODUCT_CLICK')obj.productClicks++;
    if(!obj.last||date.getTime()>obj.last.getTime()){
      obj.last=date;
      obj.lastPath=String(value_(row,wh,'ページパス')||'');
      if(kind==='PRODUCT_CLICK')obj.lastProduct=String(value_(row,wh,'製品ID')||'');
    }else if(kind==='PRODUCT_CLICK'&&!obj.lastProduct){
      obj.lastProduct=String(value_(row,wh,'製品ID')||'');
    }
  }
  const openData=open.getDataRange().getValues();
  const oh=headerMap_(openData[0]||[]);
  validateHeaders_(oh,['送信管理ID','user_agent','is_test'],'EmailOpenLog');
  const opened=Object.create(null);
  for(let i=1;i<openData.length;i++){
    const row=openData[i],id=String(value_(row,oh,'送信管理ID')||'').trim();
    if(!id||String(value_(row,oh,'is_test')||'').toUpperCase()==='YES')continue;
    const ua=String(value_(row,oh,'user_agent')||'');
    const proxy=/GoogleImageProxy|ggpht\.com|AppleMail|MailPrivacyProtection|bot|crawler|scanner|preview|linkprotect/i.test(ua);
    const stat=opened[id]||(opened[id]={proxy:0,other:0});
    if(proxy)stat.proxy++;else stat.other++;
  }
  const data=values.slice(1).map(function(row){
    const id=String(value_(row,h,'送信管理ID')||'').trim();
    const mode=String(value_(row,h,'実行モード')||'').trim().toUpperCase();
    // Keep synthetic tests visible only as excluded QA, not as sales KPIs.
    if(mode==='TEST'||/^(?:DLV|RSJ)-TEST-/i.test(id))
      return [0,0,0,'','','','TEST除外'];
    const v=results[id]||{visits:0,productViews:0,productClicks:0,last:null,lastPath:'',lastProduct:''};
    const o=opened[id]||{proxy:0,other:0};
    let quality='未検出';
    if(o.other>0)quality='開封観測・真人未確認';
    else if(o.proxy>0)quality='画像代理取得のみ・真人未確認';
    return [v.visits,v.productViews,v.productClicks,v.lastProduct,v.lastPath,v.last||'',quality];
  });
  if(data.length)queue.getRange(2,first,data.length,required.length).setValues(data);
  SpreadsheetApp.flush();
  return {ok:true,rows:data.length,webRows:w.length-1,openRows:openData.length-1};
}
