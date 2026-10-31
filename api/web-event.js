/**
 * Existing Robotics web-event gateway V2.
 * Browser -> Vercel -> signed webhook -> existing airadmin8-haishin GAS
 * -> original Web行動ログ; no parallel database, logger or automation.
 */
import { createHmac } from 'node:crypto';

const ALLOWED_ORIGINS = new Set(['https://robotics.air-admin8.co.jp','https://2airadmin8.github.io']);
const EVENTS = new Set(['lead_page_view','product_view','lead_product_click','lead_contact_click','lead_inquiry_success','pdf_open']);
const DELIVERY_RE = /^(?:DLV|RSJ)-[A-Za-z0-9._-]{5,153}$/;
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const SLUG_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
function reply(res,status,data){res.setHeader('Cache-Control','no-store');return res.status(status).json(data)}
function clean(x,n){return typeof x==='string'?x.trim().slice(0,n):''}
function pathOnly(x){
 const s=clean(x,500);
 if(!s.startsWith('/')||s.startsWith('//')||/[?#\\\r\n]/.test(s)||s.split('/').includes('..'))return '';
 return /^\/[A-Za-z0-9/_\-.]*$/.test(s)?s:'';
}
function slug(x){const s=clean(x,160);return SLUG_RE.test(s)?s:''}
function parse(req){
 if(req.body&&typeof req.body==='object'&&!Buffer.isBuffer(req.body))return req.body;
 const raw=Buffer.isBuffer(req.body)?req.body.toString('utf8'):req.body;
 if(typeof raw!=='string'||raw.length>4096)return null;
 try{return JSON.parse(raw)}catch(_){return null}
}
function allowedWebhook(s){
 try{
  const u=new URL(s);
  return u.protocol==='https:'&&u.hostname==='script.google.com'
    &&/^\/macros\/s\/[A-Za-z0-9_-]+\/exec$/.test(u.pathname)
    &&!u.search&&!u.hash&&!u.username&&!u.password;
 }catch(_){return false}
}
function recordFrom(body,now){
 if(!body||typeof body!=='object'||Array.isArray(body))return null;
 if(!EVENTS.has(body.event)||!DELIVERY_RE.test(body.delivery_id)||!UUID_RE.test(body.event_id||''))return null;
 const when=Date.parse(body.event_at);
 if(!Number.isFinite(when)||Math.abs(now-when)>10*60*1000)return null;
 const page=pathOnly(body.page_path);
 if(!page||page.startsWith('/assets/'))return null;
 const target=body.target_path?pathOnly(body.target_path):'';
 if(body.target_path&&!target)return null;
 const product=body.product_id?slug(body.product_id):'';
 if(body.product_id&&!product)return null;
 let targetProduct='';
 if(body.event==='lead_product_click'){
  const m=target.match(/^\/products\/([a-z0-9-]+)\.html$/);
  if(!m||body.target_product_id&&body.target_product_id!==m[1])return null;
  targetProduct=m[1];
 }else if(body.target_product_id){
  targetProduct=slug(body.target_product_id);
  if(!targetProduct)return null;
 }
 if(body.event==='product_view'&&(page!=='/products/'+product+'.html'||!product))return null;
 if(body.event==='lead_contact_click'&&target!=='/contact.html')return null;
 if(body.event==='lead_inquiry_success'&&page!=='/contact.html')return null;
 if(body.event==='pdf_open'&&page!=='/resources/document.html')return null;
 if(body.event==='lead_page_view'&&target)return null;
 return {
  schema:'aa8_web_event_v2',event_id:body.event_id.toLowerCase(),event:body.event,
  delivery_id:body.delivery_id,event_at:new Date(when).toISOString(),received_at:new Date(now).toISOString(),
  page_path:page,page_type:clean(body.page_type,48),product_id:product,target_product_id:targetProduct,
  target_path:target,source:'VERCEL_WEB_EVENT'
 };
}
export default async function handler(req,res){
 const origin=req.headers?.origin||'';
 if(ALLOWED_ORIGINS.has(origin)){res.setHeader('Access-Control-Allow-Origin',origin);res.setHeader('Vary','Origin')}
 res.setHeader('Access-Control-Allow-Methods','POST, OPTIONS');
 res.setHeader('Access-Control-Allow-Headers','Content-Type');
 if(req.method==='OPTIONS')return ALLOWED_ORIGINS.has(origin)?res.status(204).end():reply(res,403,{ok:false,error:'forbidden_origin'});
 if(req.method!=='POST')return reply(res,405,{ok:false,error:'method_not_allowed'});
 if(!ALLOWED_ORIGINS.has(origin))return reply(res,403,{ok:false,error:'forbidden_origin'});
 const record=recordFrom(parse(req),Date.now());
 if(!record)return reply(res,400,{ok:false,error:'invalid_event'});
 const url=process.env.AA8_SALES_WEB_EVENT_WEBHOOK_URL||'';
 const secret=process.env.AA8_SALES_WEB_EVENT_SIGNING_SECRET||'';
 if(!allowedWebhook(url)||secret.length<32)return reply(res,503,{ok:false,error:'sink_not_configured'});
 const payload=JSON.stringify(record),timestamp=String(Date.now());
 const signature=createHmac('sha256',secret).update(timestamp+'\n'+payload).digest('hex');
 try{
  const response=await fetch(url,{
   method:'POST',redirect:'follow',headers:{'Content-Type':'application/json'},
   body:JSON.stringify({timestamp,payload,signature}),signal:AbortSignal.timeout(8000)
  });
  if(!response.ok)return reply(res,503,{ok:false,error:'sink_unavailable'});
  const raw=(await response.text()).slice(0,4096);let ack;
  try{ack=JSON.parse(raw)}catch(_){return reply(res,503,{ok:false,error:'invalid_sink_ack'})}
  if(ack.ok!==true||(ack.persisted!==true&&ack.duplicate!==true))return reply(res,503,{ok:false,error:'sink_not_confirmed'});
  return reply(res,202,{ok:true,persisted:true,duplicate:Boolean(ack.duplicate),event_id:record.event_id});
 }catch(_){return reply(res,503,{ok:false,error:'sink_unavailable'})}
}
