const {test,expect}=require('@playwright/test');
const base=process.env.AA8_TEST_BASE||'http://127.0.0.1:4173';
const route='/products/unitree-g1-plus.html';
for(const width of [1440,390,360]){
 test('Unitree G1+ exact SKU, real images, SEO, CTA and responsive at '+width+'px',async ({page})=>{
  await page.setViewportSize({width,height:950});
  const errors=[],failed=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('response',r=>{if(r.status()>=400&&new URL(r.url()).origin===new URL(base).origin)failed.push(r.url()+' '+r.status())});
  const response=await page.goto(base+route,{waitUntil:'networkidle'});
  expect(response.status()).toBe(200);
  await expect(page.locator('main.g1p-page h1')).toHaveText('Unitree G1+');
  await expect(page.locator('main.g1p-page .g1p-upgrade-card')).toHaveCount(6);
  await expect(page.locator('main.g1p-page .g1p-use-grid article')).toHaveCount(3);
  await expect(page.locator('main.g1p-page .g1p-spec-table tbody tr')).toHaveCount(16);
  await expect(page.locator('main.g1p-page .g1p-next-grid a')).toHaveCount(3);
  await expect(page.locator('main.g1p-page #faq details[data-faq-item]')).toHaveCount(4);
  const title=await page.title();
  expect(title).toContain('G1+');
  const canonical=await page.locator('link[rel="canonical"]').getAttribute('href');
  expect(canonical).toBe('https://robotics.air-admin8.co.jp'+route);
  const content=await page.locator('#specifications').innerText();
  expect(content).toContain('25～45 DoF');
  expect(content).toContain('二次開発');
  expect(content).toContain('非対応');
  expect(content).toContain('約3 kg');
  expect(content).toContain('約4 kg');
  const consult=page.locator('.g1p-next-grid a[href*="/contact.html"]');
  expect(await consult.getAttribute('href')).toContain('Unitree%20G1%2B');
  await page.locator('#faq details').first().locator('summary').click();
  expect(await page.locator('#faq details').first().getAttribute('open')).not.toBeNull();
  await expect(page.locator('header.site-header .brand,header.site-header [aria-label*="ホーム"]')).toBeVisible();
  await expect(page.locator('footer.footer')).toBeVisible();
  for(const image of await page.locator('main.g1p-page img').all()){
   await image.scrollIntoViewIfNeeded();
   await expect.poll(()=>image.evaluate(el=>el.naturalWidth),{timeout:15000}).toBeGreaterThan(100);
   expect((await image.getAttribute('alt')||'').trim().length).toBeGreaterThan(4);
  }
  // Visual regression from CEO full-page review: old G1 !important white background
  // must never erase G1+ alternating sections or blue NEXT STEP and its white text.
  const visual=await page.evaluate(()=>{
   const get=q=>getComputedStyle(document.querySelector(q));
   const next=get('main.g1p-page > section.g1p-next');
   const heading=get('.g1p-next h2');
   const usage=get('main.g1p-page > section.g1p-use-section');
   const safety=get('main.g1p-page > section.g1p-safety');
   const area=get('main.g1p-page > section.g1p-intro-section');
   return {nextBackground:next.backgroundImage,
    nextHeadingColor:heading.color,useBackground:usage.backgroundColor,
    safetyBackground:safety.backgroundColor,topPadding:parseFloat(area.paddingTop),
    bottomPadding:parseFloat(area.paddingBottom),
    heroFine:document.querySelectorAll('.g1p-hero .g1-fine').length,
    oldChineseDiagram:document.querySelectorAll('img[src*="g1plus-hero-original.png"]').length};
  });
  expect(visual.nextBackground).toContain('linear-gradient');
  expect(visual.nextHeadingColor).toBe('rgb(255, 255, 255)');
  expect(visual.useBackground).toBe('rgb(244, 249, 252)');
  expect(visual.safetyBackground).toBe('rgb(244, 249, 252)');
  expect(visual.topPadding).toBeLessThanOrEqual(width<=780?50:65);
  expect(visual.bottomPadding).toBeLessThanOrEqual(width<=780?55:70);
  expect(visual.heroFine).toBe(0);
  expect(visual.oldChineseDiagram).toBe(0);
  await expect(page.locator('.g1p-technical-visual img')).toHaveAttribute('src','/assets/img/products/unitree/g1plus/g1plus-touch.png');
  if(width<=480){
   const order=await page.evaluate(()=>{
    const y=(q)=>{const e=document.querySelector(q);return e.getBoundingClientRect().top+scrollY;};
    return [
     y('.g1p-hero .g1-hero-copy h1'),
     y('.g1p-hero .g1p-hero-stage'),
     y('.g1p-hero .g1-hero-description'),
     y('.g1p-hero .g1-hero-ctas')
    ];
   });
   expect(order).toEqual([...order].sort((a,b)=>a-b));
   expect(new Set(order).size).toBe(4);
  }
  expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width+1);
  expect(errors).toEqual([]);
  expect(failed).toEqual([]);
 });
}
test('G1+ appears once in source-of-truth catalog and product list',async({request,page})=>{
 const products=await (await request.get(base+'/data/products.json')).json();
 const items=products.products.filter(p=>p.id==='unitree-g1-plus');
 expect(items).toHaveLength(1);
 expect(items[0].name).toBe('Unitree G1+');
 expect(items[0].salesStatus).toBe('confirmation_required');
 expect(items[0].imageStatus).toBe('official');
 expect(items[0].detailPage).toBe('products/unitree-g1-plus.html');
 await page.goto(base+'/products.html',{waitUntil:'networkidle'});
 await expect(page.locator('[data-product-list] #unitree-g1-plus')).toHaveCount(1);
 await expect(page.locator('[data-product-list] #unitree-g1-plus a[href*="unitree-g1-plus.html"]').first()).toBeVisible();
});
