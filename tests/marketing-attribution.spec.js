const {test,expect}=require('@playwright/test');

const BASE=process.env.AA8_TEST_BASE||'http://127.0.0.1:4173';
const TRACK='https://hikari-proxy-dev.vercel.app/api/web-event';
const RID='DLV-20990101-SYNTHQA-001';

for(const width of [1440,390,360]){
 test('Marketing: email ID -> clicked SKU -> product view -> contact / '+width,async({page})=>{
  await page.setViewportSize({width,height:900});
  const captured=[];
  await page.route('https://www.googletagmanager.com/**',r=>r.abort());
  await page.route(TRACK,async route=>{
    try{captured.push(JSON.parse(route.request().postData()||'{}'))}catch(_){}
    await route.fulfill({status:202,contentType:'application/json',headers:{'Access-Control-Allow-Origin':BASE},body:'{"ok":true,"persisted":true}'});
  });
  const params='rid='+encodeURIComponent(RID)+'&utm_source=university_sales&utm_medium=email&utm_campaign=ai_robot_intro';
  await page.goto(BASE+'/products.html?'+params,{waitUntil:'domcontentloaded'});
  await expect(page.locator('#unitree-h2-plus')).toBeVisible();
  await expect.poll(()=>captured.some(e=>e.event==='lead_page_view')).toBeTruthy();
  const ref=page.locator('#unitree-h2-plus a.product-link').first();
  await expect(ref).toHaveAttribute('href',/rid=DLV-20990101-SYNTHQA-001/);
  await ref.click();
  await page.waitForURL(/\/products\/unitree-h2-plus\.html\?/);
  await expect.poll(()=>captured.some(e=>e.event==='product_view'&&e.product_id==='unitree-h2-plus')).toBeTruthy();
  await expect.poll(()=>captured.some(e=>e.event==='lead_product_click'&&e.target_product_id==='unitree-h2-plus')).toBeTruthy();
  for(const e of captured){
    expect(e.delivery_id).toBe(RID);
    expect(e.event_id).toMatch(/^[a-f0-9-]{36}$/i);
    expect(e.event_at).toContain('T');
    expect(e.page_path).toMatch(/^\//);
    expect(e).not.toHaveProperty('email');
  }
  const ga=await page.evaluate(()=>JSON.stringify(window.dataLayer||[]));
  expect(ga).not.toContain(RID);
  await page.locator('.g1-final-cta .g1-cta-card').last().click();
  await page.waitForURL(/\/contact\.html\?/);
  expect(new URL(page.url()).searchParams.get('rid')).toBe(RID);
  expect(new URL(page.url()).searchParams.get('utm_campaign')).toBe('ai_robot_intro');
  await expect.poll(()=>captured.some(e=>e.event==='lead_contact_click')).toBeTruthy();
  // Synthetic confirmed webhook event only; NEVER submit a real inquiry.
  await page.evaluate(()=>document.dispatchEvent(new CustomEvent('aa8:inquiry-confirmed')));
  await expect.poll(()=>captured.some(e=>e.event==='lead_inquiry_success')).toBeTruthy();
  expect(captured.some(e=>e.event==='pdf_open')).toBeFalsy();
 });
}
test('Marketing: anonymous visit never attributed to a customer',async({page})=>{
 const captured=[];
 await page.route('https://www.googletagmanager.com/**',r=>r.abort());
 await page.route(TRACK,async route=>{captured.push(route.request().postData());await route.abort()});
 await page.goto(BASE+'/products/unitree-h2-plus.html',{waitUntil:'domcontentloaded'});
 await page.waitForTimeout(350);
 expect(captured).toHaveLength(0);
});
test('Marketing: forged email ID must not inherit stale attribution',async({page})=>{
 const captured=[];
 await page.route('https://www.googletagmanager.com/**',r=>r.abort());
 await page.route(TRACK,async route=>{captured.push(route.request().postData());await route.abort()});
 await page.goto(BASE+'/products.html?rid=BAD-ID',{waitUntil:'domcontentloaded'});
 await page.waitForTimeout(200);
 expect(captured).toHaveLength(0);
});
test('Marketing: PDF landing sends typed event without leaking rid to GA4',async({page})=>{
 const captured=[];
 await page.route('https://www.googletagmanager.com/**',r=>r.abort());
 await page.route(TRACK,async route=>{
   captured.push(JSON.parse(route.request().postData()||'{}'));
   await route.fulfill({status:202,contentType:'application/json',headers:{'Access-Control-Allow-Origin':BASE},body:'{"ok":true,"persisted":true}'});
 });
 await page.goto(BASE+'/resources/document.html?rid='+RID,{waitUntil:'domcontentloaded'});
 await expect.poll(()=>captured.some(e=>e.event==='pdf_open')).toBeTruthy();
 const x=captured.find(e=>e.event==='pdf_open');
 expect(x.delivery_id).toBe(RID);
 expect(x.page_path).toBe('/resources/document.html');
 expect(x.event_id).toBeTruthy();
 const ga=await page.evaluate(()=>JSON.stringify(window.dataLayer||[]));
 expect(ga).not.toContain(RID);
});
