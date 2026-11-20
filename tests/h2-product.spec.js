const {test,expect}=require('@playwright/test');
const base=process.env.AA8_TEST_BASE||'http://127.0.0.1:4173',route='/products/unitree-h2.html';
for(const width of [1440,390,360]){
test('Unitree H2 white-base facts, images, CTA, responsive '+width,async({page})=>{
 await page.setViewportSize({width,height:950});
 const failed=[],errors=[];
 page.on('response',r=>{if(r.status()>=400&&r.url().startsWith(base))failed.push(r.url()+' '+r.status())});
 page.on('pageerror',e=>errors.push(e.message));
 const r=await page.goto(base+route,{waitUntil:'networkidle'});
 expect(r.status()).toBe(200);
 await expect(page.locator('.h2-page h1')).toContainText('Unitree H2');
 await expect(page.locator('.h2-card-grid article')).toHaveCount(3);
 await expect(page.locator('.h2-use-grid article')).toHaveCount(3);
 await expect(page.locator('.h2-model-grid article')).toHaveCount(2);
 await expect(page.locator('.h2-table tbody tr')).toHaveCount(15);
 await expect(page.locator('#faq details')).toHaveCount(4);
 await expect(page.locator('.h2-next-grid a')).toHaveCount(3);
 const text=await page.locator('#specifications').innerText();
 for(const t of ['31 DoF','360 N·m','120 N·m','70 kg','非対応','対応（SDK範囲確認）'])expect(text).toContain(t);
 await expect(page.locator('link[rel=canonical]')).toHaveAttribute('href','https://robotics.air-admin8.co.jp'+route);
 const css=await page.evaluate(()=>{
 const s=q=>getComputedStyle(document.querySelector(q));
 return {hero:s('.h2-hero').backgroundImage,section:s('.h2-strengths').backgroundColor,use:s('.h2-use').backgroundColor,next:s('.h2-next').backgroundImage,nextText:s('.h2-next h2').color,overflow:document.documentElement.scrollWidth};
 });
 expect(css.hero).toContain('linear-gradient');
 expect(css.section).toBe('rgb(255, 255, 255)');
 expect(css.use).toBe('rgb(243, 248, 251)');
 expect(css.next).toContain('linear-gradient');
 expect(css.nextText).toBe('rgb(255, 255, 255)');
 expect(css.overflow).toBeLessThanOrEqual(width+1);
 for(const i of await page.locator('main.h2-page img').all()){
   await i.scrollIntoViewIfNeeded();
   await expect.poll(()=>i.evaluate(x=>x.naturalWidth),{timeout:15000}).toBeGreaterThan(100);
 }
 await page.locator('#faq summary').first().click();
 await expect(page.locator('#faq details').first()).toHaveAttribute('open','');
 expect(failed).toEqual([]);expect(errors).toEqual([]);
});
}
test('H2 catalog one record and compare card',async({request,page})=>{
 const data=await (await request.get(base+'/data/products.json')).json();
 const h2=data.products.filter(x=>x.id==='unitree-h2');expect(h2).toHaveLength(1);
 expect(h2[0].salesStatus).toBe('confirmation_required');
 await page.goto(base+'/products.html',{waitUntil:'networkidle'});
 await expect(page.locator('#unitree-h2')).toHaveCount(1);
 await expect(page.locator('.research-product-card')).toHaveCount(12);
});
test('H2 inquiry CTA prefills without submitting',async({page})=>{
 let post=0;page.on('request',r=>{if(r.method()==='POST' && (r.url().includes('script.google.com')||r.url().includes('contact-v2')))post++});
 await page.goto(base+route,{waitUntil:'networkidle'});
 await page.locator('.h2-hero-buttons .g1-button.primary').click();
 await expect(page).toHaveURL(/\/contact\.html\?product=/);
 await expect(page.locator('[name=product]')).toHaveValue('Unitree H2');
 await expect(page.locator('[name=source_product]')).toHaveValue('Unitree H2');
 expect(post).toBe(0);
});
