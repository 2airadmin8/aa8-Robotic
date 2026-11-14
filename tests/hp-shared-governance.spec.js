// P1 regression: one shared layout source and one contact prefill system
// across all 13 product pages. Never submit an actual inquiry.
const { test, expect } = require('@playwright/test');
const master = require('../data/products.json');
const ROOT = 'http://127.0.0.1:4173';
const PUBLIC = 'https://robotics.air-admin8.co.jp';

for (const width of [1440, 390]) {
  for (const product of master.products) {
    test('HP shared Header/Footer and CTA prefill ' + product.id + ' ' + width + 'px', async ({ page }) => {
      await page.setViewportSize({ width, height: 900 });
      await page.goto(ROOT + '/' + product.detailPage, { waitUntil: 'networkidle' });
      await expect(page.locator('header.site-header[data-shared-layout="header"]')).toHaveCount(1);
      await expect(page.locator('footer.footer[data-shared-layout="footer"]')).toHaveCount(1);
      const links = await page.locator('main a[href*="contact.html"]').evaluateAll(
        nodes => nodes.map(n => n.getAttribute('href')).filter(Boolean));
      const actual = links.map(link => {
        try { return new URL(link, PUBLIC + '/' + product.detailPage); }
        catch (_) { return null; }
      }).filter(x => x && x.pathname === '/contact.html' &&
                    x.searchParams.get('product'));
      expect(actual.length, 'No product CTA for ' + product.id).toBeGreaterThan(0);
      const chosen = actual[0];
      const productParam = chosen.searchParams.get('product');
      await page.goto(ROOT + chosen.pathname + chosen.search, { waitUntil: 'networkidle' });
      await expect(page.locator('form [name="product"]')).toHaveValue(productParam);
      await expect(page.locator('#contact-form')).toBeVisible();
      // Never submit the form or write a customer record.
    });
  }
}
