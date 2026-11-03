const {test,expect}=require('@playwright/test');
const BASE=process.env.AA8_TEST_BASE||'http://127.0.0.1:4173',PAGE='/products/unitree-h2-x.html';
for(const width of [1440,390,360])test('H2-X official SKU, white layout, actual images at '+width+'px',async({page})=>{
 await page.setViewportSize({width,height:900});
 const bad=[],errors=[];
 page.on('response',r=>{if(r.status()>=400&&r.url().startsWith(BASE))bad.push(r.status()+' '+r.url())});
 page.on('pageerror',e=>errors.push(e.message));
 const resp=await page.goto(BASE+PAGE,{waitUntil:'networkidle'});
 expect(resp.status()).toBe(200);
 await expect(page.locator('main.h2x-page h1')).toContainText('H2-X');
 await expect(page.locator('.h2-card-grid article')).toHaveCount(3);
 await expect(page.locator('.h2-use-grid article')).toHaveCount(3);
 await expect(page.locator('.h2-model-grid article')).toHaveCount(2);
 await expect(page.locator('.h2-table tbody tr')).toHaveCount(15);
 await expect(page.locator('#faq details')).toHaveCount(4);
 await expect(page.locator('.h2x-final-cta .g1-cta-card')).toHaveCount(3);
 const spec=await page.locator('#specifications').innerText();
 for(const text of ['1725 × 455 × 245','65kg以上','31 DoF','300 N·m','150 N·m','1.152kWh','非対応','対応（SDK範囲確認）'])expect(spec).toContain(text);
 await expect(page.locator('link[rel="canonical"]')).toHaveAttribute('href','https://robotics.air-admin8.co.jp'+PAGE);
 const css=await page.evaluate(()=>{
  let s=q=>getComputedStyle(document.querySelector(q));
  return {white:s('.h2-strengths').backgroundColor,blue:s('.h2-use').backgroundColor,gradient:s('.h2-next').backgroundImage,text:s('.h2-next h2').color,width:document.documentElement.scrollWidth};
 });
 expect(css.white).toBe('rgb(255, 255, 255)');
 expect(css.blue).toBe('rgb(255, 255, 255)');
 expect(css.gradient).toContain('g1-cta-figma-pc.png');
 expect(css.text).toBe('rgb(255, 255, 255)');
 expect(css.width).toBeLessThanOrEqual(width+1);
 for(const im of await page.locator('main.h2x-page img').all()){
   await im.scrollIntoViewIfNeeded();
   await expect.poll(()=>im.evaluate(x=>x.naturalWidth),{timeout:15000}).toBeGreaterThan(100);
 }
 expect(bad).toEqual([]);
 expect(errors).toEqual([]);
 await page.locator('#faq summary').first().click();
 await expect(page.locator('#faq details').first()).toHaveAttribute('open','');
});
test('H2-X product master appears once',async({request,page})=>{
 const data=await (await request.get(BASE+'/data/products.json')).json();
 let items=data.products.filter(x=>x.id==='unitree-h2-x');
 expect(items).toHaveLength(1);
 expect(items[0].salesStatus).toBe('confirmation_required');
 await page.goto(BASE+'/products.html',{waitUntil:'networkidle'});
 await expect(page.locator('[data-product-list] #unitree-h2-x')).toHaveCount(1);
});
test('H2-X consultation prefills without actual inquiry',async({page})=>{
 let posts=0;page.on('request',r=>{if(r.method()==='POST'&&r.url().includes('script.google.com'))posts++});
 await page.goto(BASE+PAGE,{waitUntil:'networkidle'});
 await page.locator('.h2-hero-buttons .g1-button.primary').click();
 await expect(page).toHaveURL(/\/contact\.html\?product=/);
 await expect(page.locator('[name=product]')).toHaveValue('Unitree H2-X');
 await expect(page.locator('[name=source_product]')).toHaveValue('Unitree H2-X');
 expect(posts).toBe(0);
});
