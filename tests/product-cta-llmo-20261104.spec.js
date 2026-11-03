const { test, expect } = require('@playwright/test');

const BASE = 'http://127.0.0.1:4173';
const GENERIC = [
 { slug:'unitree-g1', product:'Unitree G1', maker:'Unitree', selector:'.g1-button.secondary[href*="contact.html?product="]' },
 { slug:'unitree-g1-plus', product:'Unitree G1+', maker:'Unitree', selector:'.g1-button.primary[href*="contact.html?product="]' },
 { slug:'unitree-h2', product:'Unitree H2', maker:'Unitree', selector:'.g1-button.primary[href*="contact.html?product="]' },
 { slug:'unitree-h2-x', product:'Unitree H2-X', maker:'Unitree', selector:'.g1-button.primary[href*="contact.html?product="]' },
 { slug:'agibot-a3-ultra', product:'AGIBOT A3 Ultra', maker:'AGIBOT', selector:'.g1-button.secondary[href*="contact.html?product="]' },
];
const ALL = [
 'unitree-g1','unitree-g1-d','unitree-g1-plus','unitree-h2','unitree-h2-d',
 'unitree-h2-x','unitree-h2-plus','unitree-go2','agibot-x2-edu','agibot-a3-ultra','agibot-g2'
];

test('CTA 5 models: real PC/SP product click passes source, maker and general intent without posting', async ({ page }) => {
 for (const width of [1440,390,360]) {
  await page.setViewportSize({width,height:900});
  for (const entry of GENERIC) {
   await page.goto(BASE + '/products/' + entry.slug + '.html', {waitUntil:'domcontentloaded'});
   const link=page.locator(entry.selector).first();
   await expect(link).toBeVisible();
   const target=new URL(await link.getAttribute('href'),BASE);
   expect(target.searchParams.get('product')).toBe(entry.product);
   expect(target.searchParams.get('maker')).toBe(entry.maker);
   expect(target.searchParams.get('service')).not.toBe('university-procurement');
   await link.click();
   await expect(page).toHaveURL(/\/contact\.html\?/);
   const form=page.locator('[data-contact-form]');
   await expect(form.locator('[name="source_product"]')).toHaveValue(entry.product);
   await expect(form.locator('[name="source_maker"]')).toHaveValue(entry.maker);
   await expect(form.locator('[name="category"]')).toHaveValue('導入条件整理');
   await expect(form.locator('[name="source_page"]')).toHaveValue(BASE+'/products/'+entry.slug+'.html');
   await expect(page.locator('[data-contact-confirm]')).not.toHaveJSProperty('open',true);
  }
 }
});

test('PC1440 SP390 SP360: all 11 products are readable with no document horizontal scroll', async ({page}) => {
 for (const width of [1440,390,360]) {
  await page.setViewportSize({width,height:900});
  for(const slug of ALL){
   await page.goto(BASE+'/products/'+slug+'.html',{waitUntil:'domcontentloaded'});
   await expect(page.locator('h1').first()).toBeVisible();
   const data=await page.evaluate(()=>({
    viewport:innerWidth,
    documentWidth:document.documentElement.scrollWidth,
    contacts:document.querySelectorAll('a[href*="contact.html"]').length,
    schemas:[...document.querySelectorAll('script[type="application/ld+json"]')].map(x=>{
      try{return JSON.parse(x.textContent)['@type']}catch{return null}
    }),
   }));
   expect(data.documentWidth,slug+' at '+width).toBeLessThanOrEqual(data.viewport+2);
   expect(data.contacts,slug+' has no consultation CTA').toBeGreaterThan(0);
   expect(data.schemas.filter(x=>x==='Product'),slug+' Product schema').toHaveLength(1);
  }
 }
});

test('H2-X wording only uses H2-X, and intentional university G1+ EDU remains explicit',async ({page})=>{
 await page.goto(BASE+'/products/unitree-h2-x.html');
 await expect(page.getByRole('heading',{name:'何を検証するかから、H2-Xを選ぶ。'})).toBeVisible();
 await expect(page.getByRole('heading',{name:'何を検証するかから、H2を選ぶ。'})).toHaveCount(0);
 await page.goto(BASE+'/products/unitree-g1-plus.html');
 const edu=page.locator('a[href*="product=Unitree%20G1%2B%20EDU"]').first();
 await expect(edu).toHaveAttribute('href',/service=university-procurement/);
});
