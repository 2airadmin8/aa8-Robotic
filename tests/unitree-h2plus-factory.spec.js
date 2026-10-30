const {test,expect} = require('@playwright/test');
const base=process.env.AA8_TEST_BASE||'http://127.0.0.1:4173';
const target='/products/unitree-h2-plus.html';
const hero='/assets/img/products/unitree/h2plus/drive/h2plus.png';
for (const width of [1440,390,360]) {
 test('H2 Plus G1 approved contract / '+width+'px',async({page})=>{
  await page.setViewportSize({width,height:900});
  const errors=[],bad=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('response',r=>{
   if(r.url().startsWith(base) && r.status()>=400)bad.push(String(r.status())+' '+r.url());
  });
  let r=await page.goto(base+target,{waitUntil:'networkidle'});
  expect(r.status()).toBe(200);
  await expect(page.locator('main.g1-page[data-product-factory="g1-v1"]')).toBeVisible();
  await expect(page.locator('h1')).toHaveText('Unitree H2 Plus');
  await expect(page.locator('.site-header[data-shared-layout="header"]')).toHaveCount(1);
  await expect(page.locator('footer[data-shared-layout="footer"]')).toHaveCount(1);
  await expect(page.locator('.g1-hero-image img')).toHaveAttribute('src',hero);
  await expect(page.locator('.g1-factory-media-grid figure')).toHaveCount(9);
  await expect(page.locator('.g1-factory-related-grid a')).toHaveCount(4);
  await expect(page.locator('.g1-final-cta .g1-cta-card')).toHaveCount(3);
  await expect(page.locator('.g1-factory-videos video')).toHaveCount(0);
  await expect(page.locator('main')).toContainText('検証可能な動画がありません');
  // Real lazy-loaded gallery must be visited before checking decoded pixels.
  for (const image of await page.locator('.g1-factory-media-grid img').all()) {
    await image.scrollIntoViewIfNeeded();
    await expect.poll(()=>image.evaluate(el=>el.naturalWidth)).toBeGreaterThan(0);
  }
  await page.locator('.g1-final-cta').scrollIntoViewIfNeeded();
  const m=await page.evaluate(()=>{
   const main=document.querySelector('main.g1-page');
   const cs=x=>getComputedStyle(x);
   const hero=main.querySelector('.g1-hero');
   const sections=[...main.querySelectorAll(':scope > .g1-section:not(.g1-final-cta)')];
   const cta=main.querySelector('.g1-final-cta');
   const cards=[...cta.querySelectorAll('.g1-cta-card')];
   const gallery=[...main.querySelectorAll('.g1-factory-media-grid img')];
   const related=[...main.querySelectorAll('.g1-factory-related-photo img')];
   const h=main.querySelector('.g1-hero-image img');
   return {
    heroBg:cs(hero).backgroundColor,
    sectionColors:sections.map(x=>cs(x).backgroundColor),
    ctaBg:cs(cta).backgroundImage,
    ctaImages:cards.map(c=>{let i=c.querySelector('img');return {src:i?.getAttribute('src'),natural:i?.naturalWidth,loaded:i?.complete}}),
    galleryReady:gallery.filter(i=>i.complete&&i.naturalWidth>40).length,
    relatedReady:related.filter(i=>i.complete&&i.naturalWidth>40).length,
    heroReady:h.complete&&h.naturalWidth>0,
    ctaColumns:cs(cta.querySelector('.g1-cta-grid')).gridTemplateColumns.split(' ').length,
    relatedColumns:cs(main.querySelector('.g1-factory-related-grid')).gridTemplateColumns.split(' ').length,
    overflow:document.documentElement.scrollWidth-innerWidth,
    links:cards.map(c=>c.getAttribute('href'))
   };
  });
  expect(m.heroBg).toBe('rgb(255, 255, 255)');
  expect(m.sectionColors.length).toBeGreaterThanOrEqual(6);
  expect(m.sectionColors.every(c=>c==='rgb(255, 255, 255)')).toBeTruthy();
  expect(m.ctaBg).toContain('g1-cta-figma-pc.png');
  expect(m.ctaImages).toHaveLength(3);
  expect(m.ctaImages.every(i=>i.natural>0&&i.loaded)).toBeTruthy();
  expect(m.galleryReady).toBe(9);
  expect(m.heroReady).toBeTruthy();
  expect(m.relatedReady).toBe(4);
  expect(m.ctaColumns).toBe(width>780?3:1);
  expect(m.relatedColumns).toBe(width>900?4:width>520?2:1);
  expect(m.overflow).toBeLessThanOrEqual(1);
  expect(m.links[0]).toBe('https://www.unitree.com/H2plus');
  expect(m.links[1]).toBe('#specifications');
  expect(m.links[2]).toContain('product=Unitree%20H2%20Plus');
  await page.locator('.g1-final-cta .g1-cta-card').nth(2).click();
  await page.waitForURL(/\/contact\.html\?product=/);
  await expect(page.locator('input[name="product"]')).toHaveValue('Unitree H2 Plus');
  expect(errors).toEqual([]);
  expect(bad).toEqual([]);
 });
}
test('H2 Plus SEO manufacturer / Master status / model isolation',async({page,request})=>{
 const r=await request.get(base+target);
 expect(r.status()).toBe(200);
 const source=await r.text();
 expect(source).toContain('href="https://robotics.air-admin8.co.jp/products/unitree-h2-plus.html"');
 expect(source).toContain('h2plus.png');
 expect(source).toContain('2,070');
 expect(source).toContain('SharpaWave');
 expect(source).not.toContain('name="robots" content="noindex');
 const cat=await request.get(base+'/data/products.json');
 const products=(await cat.json()).products;
 const model=products.find(x=>x.id==='unitree-h2-plus');
 expect(model).toBeTruthy();
 expect(model.image).toContain('/h2plus.png');
 expect(model.pageFactory.releaseReady).toBe(true);
 expect(model.pageFactory.videos).toHaveLength(0);
 expect(model.pageFactory.relatedProductIds).toHaveLength(4);
 await page.goto(base+'/products.html',{waitUntil:'networkidle'});
 await expect(page.locator('[data-product-list] #unitree-h2-plus')).toHaveCount(1);
 await page.locator('[data-product-list] #unitree-h2-plus a').first().click();
 await expect(page).toHaveURL(/products\/unitree-h2-plus\.html/);
});
