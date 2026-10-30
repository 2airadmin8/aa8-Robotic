const { test, expect } = require('@playwright/test');
const base = process.env.AA8_TEST_BASE || 'http://127.0.0.1:4173';
const product = '/products/factory-qa.html';
for (const width of [1440, 390, 360]) {
  test('generated G1 factory / real browser / '+width+'px', async ({ page }) => {
    await page.setViewportSize({width, height: 900});
    const failed = [];
    page.on('pageerror', error => failed.push('pageerror ' + error.message));
    page.on('response', response => {
      if (response.url().startsWith(base) && response.status() >= 400)
        failed.push(response.status() + ' ' + response.url());
    });
    const r = await page.goto(base + product, {waitUntil:'networkidle'});
    expect(r.status()).toBe(200);
    await expect(page.locator('main.g1-page[data-product-factory="g1-v1"]')).toBeVisible();
    await expect(page.locator('.site-header[data-shared-layout="header"]')).toHaveCount(1);
    await expect(page.locator('footer[data-shared-layout="footer"]')).toHaveCount(1);
    await expect(page.locator('h1')).toHaveText('QA Fixture Robot');
    await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', 'noindex,nofollow');
    await expect(page.locator('.g1-cta-grid .g1-cta-card')).toHaveCount(3);
    await expect(page.locator('#specifications tbody tr')).toHaveCount(3);
    await expect(page.locator('.g1-faq-list details')).toHaveCount(3);
    await page.locator('.g1-cta-grid').scrollIntoViewIfNeeded();
    const m = await page.evaluate(() => {
      const main = document.querySelector('main.g1-page');
      const hero = main.querySelector('.g1-hero');
      const sections = [...main.querySelectorAll(':scope > .g1-section:not(.g1-final-cta)')];
      const cta = main.querySelector('.g1-final-cta');
      const imgs = [...cta.querySelectorAll('.g1-cta-card img')];
      return {
        hero: getComputedStyle(hero).backgroundColor,
        sections: sections.map(n => getComputedStyle(n).backgroundColor),
        cta: getComputedStyle(cta).backgroundImage,
        photos: imgs.map(n => ({complete:n.complete,width:n.naturalWidth})),
        overflow: document.documentElement.scrollWidth-innerWidth,
        columns: getComputedStyle(cta.querySelector('.g1-cta-grid')).gridTemplateColumns.split(' ').length,
      };
    });
    expect(m.hero).toBe('rgb(255, 255, 255)');
    expect(m.sections.length).toBeGreaterThanOrEqual(5);
    expect(m.sections.every(color => color === 'rgb(255, 255, 255)')).toBeTruthy();
    expect(m.cta).toContain('g1-cta-figma-pc.png');
    expect(m.photos).toHaveLength(3);
    expect(m.photos.every(x => x.complete && x.width > 100)).toBeTruthy();
    expect(m.overflow).toBeLessThanOrEqual(1);
    expect(m.columns).toBe(width <= 780 ? 1 : 3);
    await page.locator('.g1-cta-grid .g1-cta-card').nth(2).click();
    await expect(page).toHaveURL(/\/contact\.html\?product=QA%20Fixture%20Robot/);
    await expect(page.locator('input[name="product"]')).toHaveValue('QA Fixture Robot');
    expect(failed).toEqual([]);
  });
}
