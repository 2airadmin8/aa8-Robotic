const { createHash } = require('node:crypto');
const { test, expect } = require('@playwright/test');
const base='http://127.0.0.1:4173';
const originals={
  'unitree-g1-d':{file:'assets/img/products/unitree/catalog/unitree-g1-d.png',sha:'fe461d3c3195d5821c42fd5eca3731e0a36fd522bbe4b0b4b5c370dd7a8c2cc1',w:801,h:800},
  'unitree-g1':{file:'assets/img/products/unitree/catalog/28_g1.png',sha:'9d7cc68a7b6e53f337c7bf92ba942bd8d115d56cec63a7f79aaee8fee79ecbd7',w:500,h:500}
};
test('G1-D and G1 source images match approved Drive SHA256',async ({request})=>{
 const response=await request.get(base+'/data/products.json');
 expect(response.status()).toBe(200);
 const data=await response.json();
 for (const id of Object.keys(originals)){
   const expected=originals[id]; const item=data.products.find(p=>p.id===id);
   expect(item.image).toBe(expected.file);
   expect(item.imageStatus).toBe('official');
   const image=await request.get(base+'/'+expected.file);
   expect(image.status()).toBe(200);
   expect(createHash('sha256').update(await image.body()).digest('hex')).toBe(expected.sha);
 }
 expect(data.products.find(p=>p.id==='agibot-g2').image).toBe('assets/img/robot-humanoid.svg');
});
for (const path of ['/index.html','/products.html']){
 for (const width of [1440,390]){
   test('Original G1-D/G1 images in '+path+' at '+width+'px', async ({page})=>{
     await page.setViewportSize({width,height:900});
     await page.goto(base+path,{waitUntil:'networkidle'});
     for (const id of Object.keys(originals)){
       const expected=originals[id];
       const image=page.locator('[data-product-list] #'+id+' .product-visual img');
       await expect(image).toHaveCount(1);
       await expect(image).toHaveAttribute('src',expected.file);
       await image.scrollIntoViewIfNeeded();
       await expect.poll(()=>image.evaluate(i=>i.naturalWidth),{timeout:15000}).toBe(expected.w);
       const details=await image.evaluate(i=>{const r=i.getBoundingClientRect(),s=getComputedStyle(i);
         return {height:r.height,width:r.width,fit:s.objectFit,opacity:s.opacity,naturalHeight:i.naturalHeight};});
       expect(details.naturalHeight).toBe(expected.h);
       expect(details.fit).toBe('contain');
       expect(details.opacity).toBe('1');
       expect(details.width).toBeGreaterThan(70);
       expect(details.height).toBeGreaterThan(80);
     }
     await expect(page.locator('[data-product-list] #agibot-g2 .product-visual img'))
       .toHaveAttribute('src','assets/img/robot-humanoid.svg');
     expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width+1);
   });
 }
}
