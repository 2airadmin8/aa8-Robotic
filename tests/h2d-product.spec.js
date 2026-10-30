const {test,expect}=require('@playwright/test');
const BASE=process.env.AA8_TEST_BASE||'http://127.0.0.1:4173';
const PAGE='/products/unitree-h2-d.html';
for(const width of [1440,390,360]){
 test('H2-D actual official assets, SKU facts, hero and PC/SP visual gate at '+width+'px',async({page,request})=>{
  await page.setViewportSize({width,height:950});
  const errors=[],failed=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('response',r=>{if(r.status()>=400&&new URL(r.url()).origin===new URL(BASE).origin)failed.push(r.url()+' status='+r.status())});
  const resp=await page.goto(BASE+PAGE,{waitUntil:'networkidle'});
  expect(resp.status()).toBe(200);
  await expect(page.locator('.h2d-page h1')).toHaveText('Unitree H2-D');
  expect(await page.title()).toContain('Unitree H2-D');
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute('href','https://robotics.air-admin8.co.jp'+PAGE);
  await expect(page.locator('.h2d-capability-grid article')).toHaveCount(3);
  await expect(page.locator('.h2d-use-grid article')).toHaveCount(3);
  await expect(page.locator('.h2d-model-grid article')).toHaveCount(2);
  await expect(page.locator('.h2d-table tbody tr')).toHaveCount(19);
  await expect(page.locator('.h2d-cta-grid a')).toHaveCount(3);
  await expect(page.locator('#faq details[data-faq-item]')).toHaveCount(5);
  const params=await page.locator('#specifications').innerText();
  for(const term of ['19','20','約7kg','約15kg','0.5m','約1.5m/s','48V 18Ah','48V 30Ah','二次開発']){
   expect(params).toContain(term);
  }
  await expect(page.locator('script[src*="/seo.js"]')).toHaveCount(0);
  await expect(page.locator('script[src*="analytics-events.js"]')).toHaveCount(1);
  await expect(page.locator('header.site-header')).toBeVisible();
  await expect(page.locator('footer.footer')).toBeVisible();
  const visual=await page.evaluate(()=>{
   const s=q=>getComputedStyle(document.querySelector(q));
   return {
    heroBg:s('.h2d-hero').backgroundImage,heroTitle:s('.h2d-hero h1').color,
    useBg:s('.h2d-use').backgroundColor,devBg:s('.h2d-development').backgroundColor,
    ctaBg:s('.h2d-cta').backgroundImage,ctaTitle:s('.h2d-cta h2').color,
    horizontal:document.documentElement.scrollWidth,
    videoCount:document.querySelectorAll('video source[type="video/mp4"]').length,
    hasFootnote:document.querySelector('.h2d-spec-foot')?.innerText.includes('Unitree H2-D')
   };
  });
  expect(visual.heroBg).toContain('linear-gradient');
  expect(visual.heroTitle).toBe('rgb(255, 255, 255)');
  expect(visual.useBg).toBe('rgb(241, 247, 251)');
  expect(visual.devBg).toBe('rgb(244, 248, 251)');
  expect(visual.ctaBg).toContain('linear-gradient');
  expect(visual.ctaTitle).toBe('rgb(255, 255, 255)');
  expect(visual.horizontal).toBeLessThanOrEqual(width+1);
  expect(visual.videoCount).toBe(1);
  expect(visual.hasFootnote).toBe(true);
  for(const im of await page.locator('main.h2d-page img').all()){
   await im.scrollIntoViewIfNeeded();
   await expect.poll(()=>im.evaluate(x=>x.naturalWidth),{timeout:15000}).toBeGreaterThan(100);
   expect((await im.getAttribute('alt')||'').trim().length).toBeGreaterThan(8);
  }
  await page.locator('#faq summary').first().click();
  await expect(page.locator('#faq details').first()).toHaveAttribute('open','');
  expect(failed).toEqual([]);
  expect(errors).toEqual([]);
  const v=page.locator('video source');
  await expect(v).toHaveAttribute('src','/assets/img/products/unitree/h2d/h2d-motion.mp4');
  if(width===1440){
   const got=await request.get(BASE+'/assets/img/products/unitree/h2d/h2d-motion.mp4');
   expect(got.status()).toBe(200);
   expect((await got.body()).length).toBeGreaterThan(2000000);
  }
 });
}
test('H2-D in product master and visible comparison card exactly once',async({page,request})=>{
 const data=await (await request.get(BASE+'/data/products.json')).json();
 const products=data.products.filter(p=>p.id==='unitree-h2-d');
 expect(products).toHaveLength(1);
 expect(products[0].name).toBe('Unitree H2-D');
 expect(products[0].imageStatus).toBe('official');
 expect(products[0].salesStatus).toBe('confirmation_required');
 expect(products[0].detailPage).toBe('products/unitree-h2-d.html');
 await page.goto(BASE+'/products.html',{waitUntil:'networkidle'});
 await expect(page.locator('[data-product-list] .research-product-card')).toHaveCount(8);
 await expect(page.locator('[data-product-list] #unitree-h2-d')).toHaveCount(1);
 await expect(page.locator('[data-product-list] #unitree-h2-d a[href*="unitree-h2-d.html"]').first()).toBeVisible();
});
test('H2-D real consultation entry prefilled without POST',async({page})=>{
 let posts=0;
 page.on('request',r=>{if(r.method()==='POST' && r.url().includes('script.google.com'))posts++;});
 await page.goto(BASE+PAGE,{waitUntil:'networkidle'});
 await page.locator('.h2d-hero-buttons .g1-button.primary').click();
 await expect(page).toHaveURL(/\/contact\.html\?/);
 await expect(page.locator('[name="product"]')).toHaveValue('Unitree H2-D');
 await expect(page.locator('[name="source_product"]')).toHaveValue('Unitree H2-D');
 await expect(page.locator('[name="source_theme"]')).toHaveValue('use-case-review');
 await expect(page.locator('[name="category"]')).toHaveValue('導入条件整理');
 await expect(page.locator('[data-contact-form]')).toBeVisible();
 expect(posts).toBe(0);
});
