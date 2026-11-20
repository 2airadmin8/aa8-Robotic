const { test, expect } = require('@playwright/test');
const BASE='http://127.0.0.1:4173';
const PAGES=[
 'unitree-g1','unitree-g1-plus','unitree-h2','unitree-h2-d','unitree-h2-x',
 'unitree-h2-plus','agibot-a3-ultra'
];
const SELECTOR=[
 'section.g1-related','section.g1p-related','section.h2-related',
 'section.h2d-related','section.g1-factory-related'
].join(',');
test('RELATED PRODUCTS unified title, aligned to existing product template in PC/SP',async({page})=>{
 for(const width of [1440,390,360]){
  await page.setViewportSize({width,height:900});
  for(const slug of PAGES){
   await page.goto(BASE+'/products/'+slug+'.html',{waitUntil:'domcontentloaded'});
   const block=page.locator(SELECTOR);
   await expect(block,slug+' section').toHaveCount(1);
   await expect(block.locator('.g1-kicker').first()).toHaveText('RELATED PRODUCTS');
   const title=block.locator('h2').first();
   await expect(title).toBeVisible();
   if(slug==='unitree-g1'){
    await expect(title.locator('.g1-pc-only')).toHaveText('あわせて比較したい製品');
    await expect(title.locator('.g1-sp-only')).toHaveText('あわせて比較したい製品');
   }else await expect(title).toHaveText('あわせて比較したい製品');
   const geometry=await block.evaluate(section=>{
    const kicker=section.querySelector('.g1-kicker');
    const heading=section.querySelector('h2');
    const grid=section.querySelector('.g1-factory-related-grid, .g1-related-grid, .g1p-related-links, .h2-related-grid, .h2d-related-links');
    const left=e=>e.getBoundingClientRect().left;
    return {kicker:left(kicker),heading:left(heading),grid:grid?left(grid):null,
      overflow:document.documentElement.scrollWidth-innerWidth,
      anchorCount:section.querySelectorAll('a').length};
   });
   expect(Math.abs(geometry.kicker-geometry.heading),slug+' title alignment '+width).toBeLessThanOrEqual(2);
   expect(geometry.grid,slug+' grid exists').not.toBeNull();
   expect(Math.abs(geometry.kicker-geometry.grid),slug+' grid alignment '+width).toBeLessThanOrEqual(3);
   expect(geometry.overflow,slug+' no horizontal scroll '+width).toBeLessThanOrEqual(2);
   expect(geometry.anchorCount,slug+' related cards retained').toBeGreaterThanOrEqual(3);
  }
 }
});
