const {test,expect}=require('@playwright/test');
const base=process.env.AA8_TEST_BASE||'http://127.0.0.1:4173';
for(const width of [1440,390,320]){
 test('X2 series pilot: manufacturer 35-row preview / '+width,async({page})=>{
  await page.setViewportSize({width,height:900});
  const failures=[];
  page.on('pageerror',e=>failures.push(e.message));
  page.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)failures.push(r.status()+' '+r.url());});
  const response=await page.goto(base+'/x2-pilot-preview.html',{waitUntil:'networkidle'});
  expect(response.status()).toBe(200);
  await expect(page.locator('meta[name=robots]')).toHaveAttribute('content','noindex,nofollow');
  await expect(page.locator('main[data-product-id="agibot-x2-series"]')).toHaveCount(1);
  await expect(page.locator('#specifications tbody tr')).toHaveCount(35);
  await expect(page.locator('.g1-factory-media-grid img')).toHaveCount(3);
  const gallery=page.locator('.g1-factory-media-grid img');
  for(let i=0;i<3;i++){
    await gallery.nth(i).scrollIntoViewIfNeeded();
    await expect.poll(()=>gallery.nth(i).evaluate(img=>img.complete&&img.naturalWidth>0),{timeout:12000}).toBe(true);
  }
  const attrs=await gallery.evaluateAll(all=>all.map(n=>({complete:n.complete,width:n.naturalWidth})));
  expect(attrs.every(x=>x.complete&&x.width>0)).toBeTruthy();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)).toBeLessThanOrEqual(1);
  const hero=page.locator('a[data-factory-cta=hero]');
  const href=await hero.getAttribute('href');
  expect(href).toContain('maker=AGIBOT');
  expect(href).toContain('service=use-case-review');
  expect(href).toContain('source_page=');
  const url=new URL(href,'http://127.0.0.1:4173');
  expect(url.searchParams.get('source_page')).toBe('https://robotics.air-admin8.co.jp/products/agibot-x2-series.html');
  expect(failures).toEqual([]);
 });
}
