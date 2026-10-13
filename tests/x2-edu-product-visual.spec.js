const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const url = 'http://127.0.0.1:4173/products/agibot-x2-edu.html';
for (const viewport of [{ name: 'pc-1440', width: 1440, height: 900 }, { name: 'sp-390', width: 390, height: 844 }]) {
 test(`X2 EDU visual gate ${viewport.name}`, async ({ page }) => {
  await page.setViewportSize({ width: viewport.width, height: viewport.height });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  const res = await page.goto(url, {waitUntil:'networkidle'});
  expect(res.status()).toBe(200);
  await expect(page.locator('h1')).toHaveCount(1);
  await expect(page.locator('h1')).toContainText('X2 EDU');
  expect(await page.locator('body').evaluate(el => el.scrollWidth <= window.innerWidth + 1)).toBeTruthy();
  const hero = page.locator('.product-detail-visual img');
  await expect(hero).toBeVisible();
  const metrics = await hero.evaluate(el => {const r=el.getBoundingClientRect(),cs=getComputedStyle(el);return {loaded:el.complete&&el.naturalWidth>0,naturalWidth:el.naturalWidth,naturalHeight:el.naturalHeight,displayWidth:r.width,displayHeight:r.height,objectFit:cs.objectFit,src:el.currentSrc};});
  expect(metrics.loaded).toBeTruthy();
  expect(metrics.naturalWidth).toBeGreaterThanOrEqual(500);
  expect(metrics.displayWidth).toBeGreaterThan(180);
  expect(metrics.displayWidth).toBeLessThanOrEqual(viewport.width);
  expect(metrics.objectFit).toBe('contain');
  expect(metrics.src).toContain('agibot-x2-edu-manufacturer-product.jpg');
  expect(errors).toEqual([]);
  fs.mkdirSync('qa-artifacts/x2-edu',{recursive:true});
  await page.screenshot({path:`qa-artifacts/x2-edu/${viewport.name}.png`,fullPage:true});
  fs.writeFileSync(`qa-artifacts/x2-edu/${viewport.name}.json`,JSON.stringify(metrics,null,2));
 });
}
test('X2 EDU no deferred partner CTA / no fabricated visual', async ({page})=>{
 await page.goto(url);
 await expect(page.locator('a[href*="partners/x2-edu"]')).toHaveCount(0);
 await expect(page.locator('img[src*="robot-humanoid.svg"]')).toHaveCount(0);
 await expect(page.locator('a[href*="contact.html"]')).not.toHaveCount(0);
});
