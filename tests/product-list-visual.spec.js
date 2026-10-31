const {test,expect}=require('@playwright/test');
const base=process.env.AA8_TEST_BASE||'http://127.0.0.1:4173';
for(const width of [1440,390]){
  test('products catalog, hero and G1 image baseline at '+width+'px',async({page})=>{
    await page.setViewportSize({width,height:900});
    await page.goto(base+'/products.html',{waitUntil:'networkidle'});
    const hero=page.locator('.product-page-hero h1');
    await expect(hero).toBeVisible();
    const title=await hero.evaluate(e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();
      return{font:parseFloat(s.fontSize),lineHeight:parseFloat(s.lineHeight),height:r.height,width:r.width,scrollWidth:e.scrollWidth}});
    expect(title.font).toBeLessThanOrEqual(width===1440?49:35);
    expect(title.font).toBeGreaterThanOrEqual(width===1440?38:28);
    expect(title.scrollWidth).toBeLessThanOrEqual(title.width+1);
    const root=page.locator('[data-product-list]');
    await expect(root).toHaveAttribute('data-exclude-products','limx-oli');
    await expect(root.locator('.research-product-card')).toHaveCount(11);
    await expect(root.locator('#unitree-g1-plus')).toHaveCount(1);
    await expect(root.locator('#unitree-h2-d')).toHaveCount(1);
    await expect(root.locator('#limx-oli')).toHaveCount(0);
    await expect(page.locator('.product-list-summary')).toContainText('11製品を比較');
    for(const [id,filename] of [['unitree-g1-d','unitree-g1-d.png'],['unitree-g1','28_g1.png']]){
      const im=root.locator('#'+id+' .product-visual img');
      await expect(im).toHaveAttribute('src',new RegExp(filename.replaceAll('.','\\.')+'$'));
      await im.scrollIntoViewIfNeeded();
      await expect.poll(()=>im.evaluate(i=>i.naturalWidth)).toBe(id==='unitree-g1-d'?801:500);
      const c=await im.evaluate(i=>{const s=getComputedStyle(i);return{fit:s.objectFit,position:s.objectPosition,padBottom:parseFloat(s.paddingBottom)};});
      expect(c.fit).toBe('contain');
      expect(c.position).toBe('50% 100%');
      expect(c.padBottom).toBe(0);
    }
    await expect(root.locator('#agibot-g2')).toHaveCount(1);
    expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width+1);
  });
  test('CEO requested G1 specification photo half-scale only on desktop '+width+'px',async({page})=>{
    await page.setViewportSize({width,height:900});
    await page.goto(base+'/products/unitree-g1.html',{waitUntil:'networkidle'});
    const image=page.locator('.g1-spec-overview-figure img');
    await image.scrollIntoViewIfNeeded();
    await expect.poll(()=>image.evaluate(i=>i.naturalWidth)).toBe(630);
    const measure=await image.evaluate(i=>{const r=i.getBoundingClientRect();return{w:r.width,h:r.height};});
    const w=width===1440?315:346, h=width===1440?295:346*590/630;
    expect(Math.abs(measure.w-w)).toBeLessThanOrEqual(1);
    expect(Math.abs(measure.h-h)).toBeLessThanOrEqual(1);
    await expect(page.locator('.g1-spec-table tbody tr:not(.g1-spec-group)')).toHaveCount(28);
    expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width+1);
  });
}
