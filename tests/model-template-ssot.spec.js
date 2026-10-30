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

const heroAsset='/assets/img/products/unitree/h2x/drive/image_007.webp';
for(const width of [1440,390,360]){
 test('H2-X approved G1 structure, correct hero, media navigation / '+width,async({page,request})=>{
  await page.setViewportSize({width,height:900});
  const bad=[],errors=[];
  page.on('response',res=>{if(res.status()>=400&&res.url().startsWith(base))bad.push(res.status()+' '+res.url())});
  page.on('pageerror',err=>errors.push(err.message));
  const pageResponse=await page.goto(base+'/products/unitree-h2-x.html',{waitUntil:'networkidle'});
  expect(pageResponse.status()).toBe(200);
  const hero=page.locator('.h2-hero .h2-product-stage img');
  await expect(hero).toHaveAttribute('src',heroAsset);
  await expect(hero).toHaveAttribute('width','1290');
  await expect(hero).toHaveAttribute('height','1930');
  expect(await hero.evaluate(x=>({w:x.naturalWidth,h:x.naturalHeight}))).toEqual({w:1290,h:1930});
  await expect(page.locator('meta[property="og:image"]')).toHaveAttribute('content','https://robotics.air-admin8.co.jp'+heroAsset);
  const imageResponse=await request.get(base+heroAsset);expect(imageResponse.status()).toBe(200);
  const imageBuffer=await imageResponse.body();expect(imageBuffer.length).toBe(88124);
  const nav=page.locator('.g1-anchor-nav a[href="#media-h2x"]');await expect(nav).toHaveText('写真・動画');
  const anchorIds=await page.locator('.g1-anchor-nav a[href^="#"]').evaluateAll(as=>as.map(a=>a.getAttribute('href')?.slice(1)));
  for(const id of anchorIds)await expect(page.locator('[id="'+id+'"]')).toHaveCount(1);
  const sections=await page.locator('main .h2-heading > .g1-kicker').allTextContents();
  const nums=sections.filter(x=>/^0[1-6] \/ /.test(x)).map(x=>x.slice(0,2));
  expect(nums).toEqual(['01','02','03','04','05','06']);
  const rootClasses=await page.locator('main').getAttribute('class');
  expect(rootClasses).toContain('g1-page');
  await expect(page.locator('main .g1-shell').first()).toBeVisible();
  await expect(page.locator('.g1-hero')).toHaveCount(1);
  await expect(page.locator('.g1-button.primary').first()).toBeVisible();
  await expect(page.locator('.h2x-media-gallery img')).toHaveCount(4);
  await expect(page.locator('.h2x-video-grid video')).toHaveCount(3);
  const props=await page.evaluate(()=>{
    const hero=document.querySelector('.h2-product-stage img');
    const section=getComputedStyle(document.querySelector('.h2-strengths'));
    const cta=getComputedStyle(document.querySelector('.h2-next'));
    return {imageFit:getComputedStyle(hero).objectFit,sectionBackground:section.backgroundColor,ctaBackground:cta.backgroundImage,overflow:document.documentElement.scrollWidth};
  });
  expect(props.imageFit).toBe('contain');
  expect(props.sectionBackground).toBe('rgb(255, 255, 255)');
  expect(props.ctaBackground).toContain('linear-gradient');
  expect(props.overflow).toBeLessThanOrEqual(width+1);
  expect(errors).toEqual([]);
  expect(bad).toEqual([]);
 });
}
test('H2-X product catalog uses the same selected hero image',async({request,page})=>{
 const catalog=await (await request.get(base+'/data/products.json')).json();
 const item=catalog.products.filter(x=>x.id==='unitree-h2-x');
 expect(item).toHaveLength(1);
 expect(item[0].image).toBe(heroAsset.slice(1));
 expect(item[0].imageAlt).toContain('H2-X');
 await page.goto(base+'/products.html',{waitUntil:'networkidle'});
 const card=page.locator('#unitree-h2-x');
 await expect(card).toHaveCount(1);
 await expect(card.locator('img').first()).toHaveAttribute('src',heroAsset.slice(1));
});
