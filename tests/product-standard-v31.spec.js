const {test,expect}=require('@playwright/test');
const products=require('../data/products.json').products;
const ORIGIN='http://127.0.0.1:4173';

// V3.1 deliberately preserves product-specific sections. These browser
// contracts test shared cross-page behavior, not identical visual layouts.
for(const product of products){
  for(const width of [1440,390,360]){
    test(`V3.1 ${product.id} | ${width}px | identity, support, CTA`, async({page})=>{
      await page.setViewportSize({width,height:900});
      const status=await page.goto(ORIGIN+'/'+product.detailPage,{waitUntil:'networkidle'});
      expect(status.status()).toBe(200);
      const root=page.locator('main[data-aa8-product-standard="3.1"]');
      await expect(root).toHaveCount(1);
      await expect(root).toHaveAttribute('data-product-id',product.id);
      await expect(root).toHaveAttribute('data-product-family',product.pageStandard.family);
      await expect(page.locator('h1')).toHaveCount(1);
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth);
      expect(overflow,product.id+' '+width+' horizontal overflow').toBeLessThanOrEqual(2);
      for(const id of product.pageStandard.preserveSectionIds){
        await expect(page.locator('#'+id),product.id+': '+id).toHaveCount(1);
      }
      const bridge=root.locator('.aa8-product-bridge');
      if(product.pageStandard.showBridge){
        await expect(bridge).toBeVisible();
        await expect(page.locator('link[href="/assets/css/product-standard-v31.css"]')).toHaveCount(1);
        const hrefs=await bridge.locator('a').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('href')));
        expect(hrefs).toEqual([product.pageStandard.resourcesHref,product.pageStandard.supportHref]);
        await expect(bridge).toHaveCSS('background-color','rgb(255, 255, 255)');
        const boxes=await bridge.locator('a').evaluateAll(nodes=>nodes.map(x=>({width:x.getBoundingClientRect().width,scrollWidth:x.scrollWidth})));
        expect(boxes.every(b=>b.scrollWidth<=b.width+2)).toBeTruthy();
      }else{
        await expect(bridge).toHaveCount(0);
      }
      // Product-specific consulting CTAs carry the authoritative maker.
      if(!product.designContract){
        const productLinks=await root.locator('a[href*="contact.html?product="]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('href')));
        for(const href of productLinks){
          expect(new URL(href,ORIGIN).searchParams.get('maker')).toBe(product.manufacturerName);
        }
      }
      await page.close();
    });
  }
}
