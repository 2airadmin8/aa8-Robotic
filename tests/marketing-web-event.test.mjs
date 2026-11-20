import test from 'node:test';
import assert from 'node:assert/strict';
import { createHmac } from 'node:crypto';
import handler from '../api/web-event.js';

const ORIGIN='https://robotics.air-admin8.co.jp';
const WEBHOOK='https://script.google.com/macros/s/AKfycbREALAPPROVEDTESTENDPOINT/exec';
const SECRET='test-only-signing-secret-not-a-production-credential-123';
const ID='89a2d324-43af-47ad-843b-bdd4ec0321b1';
const RID='DLV-20990101-SYNTHQA-001';
let currentFetch,oldUrl,oldSecret;
test.beforeEach(()=>{
 currentFetch=globalThis.fetch;
 oldUrl=process.env.AA8_SALES_WEB_EVENT_WEBHOOK_URL;
 oldSecret=process.env.AA8_SALES_WEB_EVENT_SIGNING_SECRET;
 delete process.env.AA8_SALES_WEB_EVENT_WEBHOOK_URL;
 delete process.env.AA8_SALES_WEB_EVENT_SIGNING_SECRET;
});
test.afterEach(()=>{
 globalThis.fetch=currentFetch;
 if(oldUrl===undefined)delete process.env.AA8_SALES_WEB_EVENT_WEBHOOK_URL;
 else process.env.AA8_SALES_WEB_EVENT_WEBHOOK_URL=oldUrl;
 if(oldSecret===undefined)delete process.env.AA8_SALES_WEB_EVENT_SIGNING_SECRET;
 else process.env.AA8_SALES_WEB_EVENT_SIGNING_SECRET=oldSecret;
});
const build=(overrides={})=>({
 event:'product_view',event_id:ID,event_at:new Date().toISOString(),
 delivery_id:RID,page_path:'/products/unitree-h2-plus.html',
 page_type:'product_detail',product_id:'unitree-h2-plus',...overrides
});
function response(){
 const r={code:0,headers:{},jsonBody:null,ended:false,
  setHeader(k,v){this.headers[k]=v;return this},
  status(n){this.code=n;return this},
  json(obj){this.jsonBody=obj;return this},
  end(){this.ended=true;return this}
 };
 return r;
}
async function run(body=build(),origin=ORIGIN,method='POST'){
 const res=response();await handler({method,headers:{origin},body},res);return res;
}
test('no sink configured: fail closed, never claim persisted',async()=>{
 const r=await run();assert.equal(r.code,503);assert.equal(r.jsonBody.ok,false);
 assert.equal(r.jsonBody.error,'sink_not_configured');
});
test('reject invalid origin and do not emit customer information',async()=>{
 let r=await run(build(),'https://attacker.example');assert.equal(r.code,403);
 r=await run(build(),'');assert.equal(r.code,403);
});
test('OPTIONS allowed but no CORS wildcards',async()=>{
 let a=await run({},ORIGIN,'OPTIONS');assert.equal(a.code,204);
 assert.equal(a.headers['Access-Control-Allow-Origin'],ORIGIN);
 let b=await run({},'https://attacker.example','OPTIONS');assert.equal(b.code,403);
});
test('wrong verb or invalid document',async()=>{
 assert.equal((await run(build(),ORIGIN,'GET')).code,405);
 for(const patch of [
  {delivery_id:'TEST-OPEN-001'}, {delivery_id:'bad'}, {event_id:'not-uuid'},
  {event:'email_open'}, {event_at:'2024-01-01T00:00:00Z'}, {page_path:'//evil'},
  {page_path:'/../../secrets'}, {page_path:'/products/foo.html?email=test@example.com'},
  {product_id:'unitree-h2-x'},{event:'pdf_open'},{target_product_id:'foo!'}
 ])assert.equal((await run(build(patch))).code,400,JSON.stringify(patch));
});
test('valid click target must match ID and cannot spoof external URL',async()=>{
 const good=build({event:'lead_product_click',page_path:'/products.html',
  target_path:'/products/unitree-h2-plus.html',target_product_id:'unitree-h2-plus',product_id:''});
 assert.equal((await run(good)).code,503); // valid but persistence missing
 assert.equal((await run({...good,target_product_id:'unitree-h2-x'})).code,400);
 assert.equal((await run({...good,target_path:'https://evil.example'})).code,400);
});
test('valid contact and PDF events are authorized types',async()=>{
 assert.equal((await run(build({event:'lead_contact_click',page_path:'/products/unitree-h2.html',target_path:'/contact.html',product_id:'unitree-h2'}))).code,503);
 assert.equal((await run(build({event:'lead_inquiry_success',page_path:'/contact.html',product_id:''}))).code,503);
 assert.equal((await run(build({event:'pdf_open',page_path:'/resources/document.html',product_id:''}))).code,503);
});
test('accepts only ACK after signed durable write, not HTTP200 alone',async()=>{
 process.env.AA8_SALES_WEB_EVENT_WEBHOOK_URL=WEBHOOK;
 process.env.AA8_SALES_WEB_EVENT_SIGNING_SECRET=SECRET;
 let calls=0;
 globalThis.fetch=async(url,opts)=>{
  calls++;
  assert.equal(url,WEBHOOK);assert.equal(opts.method,'POST');
  const envelope=JSON.parse(opts.body);
  assert.match(envelope.timestamp,/^\d{13}$/);
  const computed=createHmac('sha256',SECRET).update(envelope.timestamp+'\n'+envelope.payload).digest('hex');
  assert.equal(envelope.signature,computed);
  const event=JSON.parse(envelope.payload);
  assert.equal(event.schema,'aa8_web_event_v2');
  assert.equal(event.delivery_id,RID);
  assert.equal(event.product_id,'unitree-h2-plus');
  assert.equal(event.event_id,ID);
  assert.equal(event.page_path,'/products/unitree-h2-plus.html');
  assert.ok(!('email' in event)&&!('ip' in event)&&!('name' in event));
  return {ok:true,status:200,text:async()=>JSON.stringify({ok:true,persisted:true,duplicate:false})};
 };
 const r=await run();assert.equal(r.code,202);assert.equal(r.jsonBody.persisted,true);assert.equal(calls,1);
});
test('repeated event ACK from GAS must be marked duplicate',async()=>{
 process.env.AA8_SALES_WEB_EVENT_WEBHOOK_URL=WEBHOOK;process.env.AA8_SALES_WEB_EVENT_SIGNING_SECRET=SECRET;
 globalThis.fetch=async()=>({ok:true,status:200,text:async()=>JSON.stringify({ok:true,duplicate:true})});
 const r=await run();assert.equal(r.code,202);assert.equal(r.jsonBody.duplicate,true);
});
test('Google App webhook must be allowlisted HTTPS, never an arbitrary URL',async()=>{
 process.env.AA8_SALES_WEB_EVENT_WEBHOOK_URL='https://169.254.169.254/latest/meta-data';
 process.env.AA8_SALES_WEB_EVENT_SIGNING_SECRET=SECRET;
 assert.equal((await run()).code,503);
});
test('no 204 on failed, non-json or false sink ack',async()=>{
 process.env.AA8_SALES_WEB_EVENT_WEBHOOK_URL=WEBHOOK;process.env.AA8_SALES_WEB_EVENT_SIGNING_SECRET=SECRET;
 for(const fake of [
  {ok:false,status:503,text:async()=>''},
  {ok:true,status:200,text:async()=>'<html>GAS error</html>'},
  {ok:true,status:200,text:async()=>JSON.stringify({ok:true,persisted:false})}
 ]){
  globalThis.fetch=async()=>fake;
  const r=await run();assert.equal(r.code,503);assert.equal(r.jsonBody.ok,false);
 }
});
test('timeout/outage returns safe 503 without secret or personal data',async()=>{
 process.env.AA8_SALES_WEB_EVENT_WEBHOOK_URL=WEBHOOK;process.env.AA8_SALES_WEB_EVENT_SIGNING_SECRET=SECRET;
 globalThis.fetch=async()=>{throw Error('service failed including secret '+SECRET)};
 const r=await run();assert.equal(r.code,503);assert.ok(!JSON.stringify(r.jsonBody).includes(SECRET));
});
