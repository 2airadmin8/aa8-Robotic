/** Private DEV-only orchestrator. All writes confined to EXISTING E2E_TEST_ONLY workbook. */
function qaActions_(kind) {
  devInquiryEnvironmentGuard_();
  if (kind !== 'QA_PANEL') throw new Error('QA_PANEL_NOT_ALLOWED');
  const action='https://script.google.com/macros/s/AKfycby56N_DdpwQRPRmQmZA9I6Dt5Sk4sME5vApJUYOTTTG2NG9qIMGfKGygvoPoavsW5Tv8A/exec';
  const actions=['STAGE_A','STAGE_B','WRITE_A','WRITE_B'];
  const buttons=actions.map(x => '<form method="post" target="_top" action="'+devHtml_(action)+'">' +
    '<input type="hidden" name="qa_action" value="'+devHtml_(x)+'">'+
    '<button style="font-size:20px;padding:14px;margin:8px" type="submit">'+devHtml_(x)+' QA ONLY</button></form>').join('');
  return HtmlService.createHtmlOutput('<!doctype html><html lang="en"><meta charset="utf-8"><h1>QA ISOLATED INTAKE & WRITER - NO OFFICIAL ID</h1>'+buttons);
}
function qaAssertBook_() {
  devInquiryEnvironmentGuard_();
  if (!QA_INTAKE || !P1_RUNTIME ||
      QA_INTAKE.book !== P1_RUNTIME.SALES_OS_ID ||
      QA_INTAKE.book === AA8_DEV.spreadsheetId ||
      QA_INTAKE.book === DEV_CRM_READ_ONLY.productionPersonSsoTId ||
      P1_RUNTIME.INTAKE_SHEET !== 'QA_Intake' ||
      P1_RUNTIME.SALES_MASTER_SHEET !== 'QA_Customer') {
    throw new Error('QA_WRITER_BOUNDARY_FAIL_CLOSED');
  }
  const b=SpreadsheetApp.openById(QA_INTAKE.book);
  const intake=b.getSheetByName('QA_Intake'), master=b.getSheetByName('QA_Customer');
  if (!intake || !master || intake.getLastColumn()!==17 || master.getLastColumn()!==69) {
    throw new Error('QA_TARGET_SCHEMA_MISMATCH');
  }
  return {intake, master};
}
function qaReadback_(key) {
  const {intake,master}=qaAssertBook_(), id=QA_INTAKE.ids[key];
  const rows=intake.getDataRange().getValues();
  const values=rows.slice(1).filter(x=>String(x[15])===id);
  if (values.length!==1) throw new Error('QA_READBACK_SOURCE_NOT_UNIQUE');
  const receipt=values[0];
  const testId=String(receipt[12]||'');
  const masters=master.getDataRange().getValues().slice(1);
  const corresponding=testId?masters.filter(x=>String(x[0])===testId):[];
  if(corresponding.length>1) throw new Error('QA_DUPLICATE_CUSTOMERID');
  return {
    sourceId:id,
    intakeRowCount:values.length,
    intakeStatus:String(receipt[13]),
    intakeCustomerId:testId?'QA_NONCANONICAL:'+testId:null,
    qaCustomerRows:corresponding.length,
    qaCustomerId:testId?'QA_NONCANONICAL:'+testId:null,
    officialCustomerId:null,
    realProductionWrites:0,
    externalEmailsSent:0
  };
}
function qaRealPost_(e) {
  const p=e&&e.parameter||{}, action=String(p.qa_action||'');
  qaAssertBook_();
  if(!['STAGE_A','STAGE_B','WRITE_A','WRITE_B'].includes(action)) throw new Error('QA_ACTION_REJECTED');
  const key=action.slice(-1), isWrite=action.startsWith('WRITE_');
  let result;
  if(!isWrite) result=devQaStage_(key);
  else {
    // Only the two exact internal, already persisted Inquiry source records.
    devQaReadSourceViaPinnedReceipt_(key);
    const b=SpreadsheetApp.openById(QA_INTAKE.book), intake=b.getSheetByName('QA_Intake');
    const rows=intake.getDataRange().getValues(), match=[];
    for(let i=1;i<rows.length;i++) if(String(rows[i][15])===QA_INTAKE.ids[key]) match.push(i+1);
    if(match.length!==1) throw new Error('QA_SOURCE_NOT_STAGED_UNIQUELY');
    const existing=rows[match[0]-1];
    if(String(existing[1])!=='Robotics_Web_Inquiry'||
       String(existing[2])!=='AirAdmin8 DEV University (INTERNAL TEST ONLY)'||
       String(existing[4])!=='INTERNAL QA '+key||
       String(existing[6]).toLowerCase()!==AA8_DEV.recipient)
       throw new Error('QA_SOURCE_NOT_SYNTHETIC');
    // Original T006 locked function; P1_RUNTIME points ONLY to QA workbook.
    const actual=p1AssignOfficialCustomerIdFromIntake(match[0]);
    result={state:actual.status,qaId:actual.customerId?'QA_NONCANONICAL:'+actual.customerId:null};
  }
  const readback=qaReadback_(key);
  return HtmlService.createHtmlOutput('<!doctype html><html><meta charset="utf-8"><body>'+
    '<h1>QA ONLY - REAL WRITER READBACK</h1><pre id="qa-result">'+
    devHtml_(JSON.stringify({mode:'QA_ISOLATED_REAL_SHEETS',action,result,readback},null,2))+
    '</pre><a href="https://script.google.com/macros/s/AKfycby56N_DdpwQRPRmQmZA9I6Dt5Sk4sME5vApJUYOTTTG2NG9qIMGfKGygvoPoavsW5Tv8A/exec?case=QA_PANEL">QA panel</a></body></html>');
}
function devQaReadSourceViaPinnedReceipt_(key) {
  if(!Object.prototype.hasOwnProperty.call(QA_INTAKE.ids,key)) throw new Error('QA_KEY_INVALID');
  const sh=SpreadsheetApp.openById(QA_INTAKE.source).getSheetByName('01_Inquiry');
  const v=sh.getDataRange().getValues();
  const m=v.slice(1).filter(x=>String(x[0])===QA_INTAKE.ids[key]);
  if(m.length!==1||String(m[0][26])!==AA8_DEV.batch+'-'+key)
    throw new Error('QA_REAL_INQUIRY_BINDING_FAILED');
}
