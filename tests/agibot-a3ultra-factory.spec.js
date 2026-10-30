const {test,expect}=require('@playwright/test');
const base=process.env.AA8_TEST_BASE||'http://127.0.0.1:4173';
const pageUrl='/products/agibot-a3-ultra.html';
const hero='/assets/img/products/agibot/a3-ultra/drive/A3Ultra_One-bg.jpg';
for(const width of [1440,390,360]){
 test('A3 Ultra factory official provenance / G1 white '+width,async({page})=>{
  await page.setViewportSize({width,height:900});
  const errors=[],fail=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)fail.push(String(r.status())+' '+r.url())});
  const r=await page.goto(base+pageUrl,{waitUntil:'networkidle'});
  expect(r.status()).toBe(200);
  await expect(page.locator('h1')).toHaveText('AGIBOT A3 Ultra');
  const h=page.locator('.g1-hero-image img');
  await expect(h).toHaveAttribute('src',hero);
  await expect(page.locator('.g1-factory-media-grid figure')).toHaveCount(8);
  await expect(page.locator('.g1-factory-videos video')).toHaveCount(3);
  await expect(page.locator('.g1-factory-related-card')).toHaveCount(4);
  await expect(page.locator('.g1-final-cta .g1-cta-card')).toHaveCount(3);
  for(const img of await page.locator('.g1-factory-media-grid img').all()){
   await img.scrollIntoViewIfNeeded();
   await expect.poll(()=>img.evaluate(e=>e.naturalWidth)).toBeGreaterThan(0);
  }
  for(const image of await page.locator('.g1-factory-related-card img').all()){
    await image.scrollIntoViewIfNeeded();
    await expect.poll(()=>image.evaluate(el=>el.naturalWidth)).toBeGreaterThan(0);
  }
  await page.locator('.g1-final-cta').scrollIntoViewIfNeeded();
  const m=await page.evaluate(()=>{
   const main=document.querySelector('main.g1-page'),cs=e=>getComputedStyle(e);
   const sections=[...main.querySelectorAll(':scope > .g1-section:not(.g1-final-cta)')];
   const cta=main.querySelector('.g1-final-cta'),gallery=[...main.querySelectorAll('.g1-factory-media-grid img')];
   const related=[...main.querySelectorAll('.g1-factory-related-card img')];
   const images=[...cta.querySelectorAll('.g1-cta-card img')];
   return {whiteHero:cs(main.querySelector('.g1-hero')).backgroundColor,
    whites:sections.map(s=>cs(s).backgroundColor),ctaBackground:cs(cta).backgroundImage,
    ctaLoaded:images.filter(i=>i.complete&&i.naturalWidth>0).length,
    relatedLoaded:related.filter(i=>i.complete&&i.naturalWidth>0).length,
    galleryLoaded:gallery.filter(i=>i.complete&&i.naturalWidth>0).length,
    ctaColumns:cs(cta.querySelector('.g1-cta-grid')).gridTemplateColumns.split(' ').length,
    overflow:document.documentElement.scrollWidth-innerWidth,heroWidth:main.querySelector('.g1-hero-image img').naturalWidth,
    links:[...cta.querySelectorAll('.g1-cta-card')].map(a=>a.getAttribute('href'))};
  });
  expect(m.whiteHero).toBe('rgb(255, 255, 255)');
  expect(m.whites.length).toBeGreaterThanOrEqual(6);
  expect(m.whites.every(x=>x==='rgb(255, 255, 255)')).toBeTruthy();
  expect(m.ctaBackground).toContain('g1-cta-figma-pc.png');
  expect(m.ctaLoaded).toBe(3);
  expect(m.galleryLoaded).toBe(8);
  expect(m.relatedLoaded).toBe(4);
  expect(m.heroWidth).toBeGreaterThan(0);
  expect(m.ctaColumns).toBe(width>780?3:1);
  expect(m.overflow).toBeLessThanOrEqual(1);
  expect(m.links[0]).toContain('1.mp4');
  expect(m.links[1]).toBe('#specifications');
  expect(m.links[2]).toContain('product=AGIBOT%20A3%20Ultra');
  await page.locator('.g1-final-cta .g1-cta-card').nth(2).click();
  await page.waitForURL(/\/contact\.html\?/);
  await expect(page.locator('input[name="product"]')).toHaveValue('AGIBOT A3 Ultra');
  expect(errors).toEqual([]);expect(fail).toEqual([]);
 });
}
test('A3 Ultra source-safe Master/SEO, no A2 Ultra archive contamination',async({request,page})=>{
 const r=await request.get(base+pageUrl),html=await r.text();
 expect(r.status()).toBe(200);
 expect(html).toContain('A3Ultra_One-bg.jpg');
 expect(html).not.toContain('image_023.png');
 const specs=html.match(/<section class="g1-section g1-factory-section" id="specifications">([\s\S]*?)<\/section>/)?.[1]||'';
 expect(specs).toContain('700 TOPS');
 // FAQ can legitimately warn that the DIFFERENT A3 model is 55kg/10h;
 // those values must never appear as A3 Ultra technical specifications.
 expect(specs).not.toContain('55KG');
 expect(specs).not.toContain('10時間');
 expect(specs).not.toContain('55kg');
 expect(html).toContain('700 TOPS');
 const j=await (await request.get(base+'/data/products.json')).json();
 const x=j.products.find(p=>p.id==='agibot-a3-ultra');
 expect(x).toBeTruthy();
 expect(x.image).toContain('A3Ultra_One-bg.jpg');
 expect(x.pageFactory.images).toHaveLength(8);
 expect(x.pageFactory.videos).toHaveLength(3);
 expect(x.pageFactory.relatedProductIds).toHaveLength(4);
 await page.goto(base+'/products.html',{waitUntil:'networkidle'});
 await expect(page.locator('#agibot-a3-ultra')).toHaveCount(1);
});
