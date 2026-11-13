/** DEV-only original Inquiry -> existing QA workbook, NOT official CRM. */
const QA_INTAKE = Object.freeze({
  book:'11aE5zw5OHoqzGFBXxp06VSkwAOJAZ7N6pkxyAgLg0Bw',
  source:'1PzfHiB50jFDHCosMGTb7MUvbQ9nC3UD5pHjgHbpY9Qk',
  ids:Object.freeze({
    A:'INQ-20261104-000403-D19A8041',
    B:'INQ-20261104-000525-E556D4D7'
  })
});
function devQaStage_(key) {
  devInquiryEnvironmentGuard_();
  if (!Object.prototype.hasOwnProperty.call(QA_INTAKE.ids,key))
    throw new Error('QA_CASE_DENIED');
  if (QA_INTAKE.book === DEV_CRM_READ_ONLY.productionPersonSsoTId ||
      QA_INTAKE.book === AA8_DEV.spreadsheetId) throw new Error('QA_ISOLATION_FAILED');
  const source=SpreadsheetApp.openById(QA_INTAKE.source).getSheetByName('01_Inquiry');
  const original=source.getDataRange().getValues();
  if (original[0].map(String).join('|')!==AA8_DEV.headers.join('|'))
    throw new Error('SOURCE_SCHEMA_CHANGED');
  const id=QA_INTAKE.ids[key];
  const found=original.slice(1).filter(r=>String(r[0])===id);
  if(found.length!==1) throw new Error('SOURCE_NOT_UNIQUE');
  const x=found[0];
  if(String(x[26])!==AA8_DEV.batch+'-'+key ||
     String(x[6]).toLowerCase()!==AA8_DEV.recipient ||
     x[4]!=='AirAdmin8 DEV University (INTERNAL TEST ONLY)' ||
     x[5]!=='INTERNAL QA '+key) throw new Error('SOURCE_NOT_INTERNAL');
  const qa=SpreadsheetApp.openById(QA_INTAKE.book);
  const target=qa.getSheetByName('QA_Intake');
  const master=qa.getSheetByName('QA_Customer');
  if(!target || !master || target.getLastColumn()!==17 ||
     master.getLastColumn()!==69) throw new Error('QA_SCHEMA_INVALID');
  const h=target.getRange(1,1,1,17).getValues()[0].map(String);
  if(h[15]!=='SourceID'||h[12]!=='顧客ID'||h[13]!=='処理状態')
    throw new Error('QA_INTAKE_HEADERS_INVALID');
  const lock=LockService.getScriptLock();
  if(!lock.tryLock(10000)) throw new Error('QA_LOCK_BUSY');
  try {
    const existing=target.getDataRange().getValues().slice(1).filter(r=>String(r[15])===id);
    if(existing.length>1) throw new Error('DUPLICATE_SOURCEID');
    if(existing.length===1) return {qaOnly:true,sourceId:id,state:'ALREADY_STAGED',
      writesPerformed:0,officialCustomerId:null};
    const row=[
      Utilities.formatDate(new Date(x[1]),'Asia/Tokyo','yyyy-MM-dd'),
      'Robotics_Web_Inquiry',String(x[4]),'',String(x[5]),'',
      String(x[6]),String(x[7]||''),'','','','未確認','',
      'HOLD_EVIDENCE','QA_ONLY; NOT VERIFIED; InquiryID='+id,
      id,''
    ];
    if(row.length!==17) throw new Error('QA_ROW_SIZE_INVALID');
    target.getRange(target.getLastRow()+1,1,1,17).setValues([row]);
    SpreadsheetApp.flush();
    return {qaOnly:true,sourceId:id,state:'QA_STAGED_HOLD_EVIDENCE',
      writesPerformed:1,officialCustomerId:null};
  } finally {lock.releaseLock();}
}
function devQaStageResponse_(key) {
  const result=devQaStage_(key);
  return HtmlService.createHtmlOutput('<!doctype html><meta charset="utf-8">'+
    '<h1>QA ONLY / NO OFFICIAL CUSTOMERID</h1><pre id="qa-result">'+
    devHtml_(JSON.stringify(result,null,2))+'</pre>');
}
