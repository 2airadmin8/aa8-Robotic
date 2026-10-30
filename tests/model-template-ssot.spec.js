const {test,expect}=require('@playwright/test');
const base=process.env.AA8_TEST_BASE||'http://127.0.0.1:4173';
for (const [slug,model] of [['unitree-g1','G1'],['unitree-g1-plus','G1+'],['unitree-h2','H2'],['unitree-h2-d','H2-D'],['unitree-h2-x','H2-X']]) {
 test('G1 inherited model header SSOT: '+slug,async({page})=>{
  await page.goto(base+'/products/'+slug+'.html',{waitUntil:'networkidle'});
  const row=page.locator('main table thead tr').first();
  await expect(row.locator('th').first()).toHaveText('モデル');
  await expect(row.locator('th')).toHaveCount(3);
  await expect(page.locator('header[data-shared-layout="header"]')).toBeVisible();
  await expect(page.locator('footer[data-shared-layout="footer"]')).toBeVisible();
 });
}
for(const width of [1440,390,360]){
 test('H2-X inherited G1 template and SKU-safe PC/SP '+width,async({page})=>{
  await page.setViewportSize({width,height:900});
  const bad=[],exceptions=[];
  page.on('response',r=>{if(r.status()>=400&&r.url().startsWith(base))bad.push(r.status()+' '+r.url())});
  page.on('pageerror',e=>exceptions.push(e.message));
  await page.goto(base+'/products/unitree-h2-x.html',{waitUntil:'networkidle'});
  await expect(page.locator('h1')).toContainText('H2-X');
  await expect(page.locator('.g1-anchor-nav')).toBeVisible();
  await expect(page.locator('.h2-table thead th').first()).toHaveText('モデル');
  await expect(page.locator('.h2x-media-gallery img')).toHaveCount(4);
  await expect(page.locator('.h2x-video-grid video')).toHaveCount(3);
  await expect(page.locator('#contact-h2')).toBeVisible();
  const facts=await page.evaluate(()=>{
   const section=document.querySelector('.h2-strengths'), cta=document.querySelector('.h2-next'),title=document.querySelector('.h2-next h2');
   return {body:getComputedStyle(section).backgroundColor,gradient:getComputedStyle(cta).backgroundImage,ctaText:getComputedStyle(title).color,width:document.documentElement.scrollWidth,alt:document.querySelector('.h2-product-stage img')?.getAttribute('alt'),menu:document.querySelector('.g1-anchor-nav')?.getAttribute('aria-label')};
  });
  expect(facts.body).toBe('rgb(255, 255, 255)');
  expect(facts.gradient).toContain('linear-gradient');
  expect(facts.ctaText).toBe('rgb(255, 255, 255)');
  expect(facts.width).toBeLessThanOrEqual(width+1);
  expect(facts.alt).toContain('H2-X');
  expect(facts.menu).toContain('H2-X');
  expect(await page.locator('main').innerText()).not.toContain('標準H2に標準搭載');
  expect(bad).toEqual([]);
  expect(exceptions).toEqual([]);
 });
}
