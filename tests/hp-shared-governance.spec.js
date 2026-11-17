// P1 regression: one shared layout source and one contact prefill system
// across all 13 product pages. Never submit an actual inquiry.
const { test, expect } = require('@playwright/test');
const master = require('../data/products.json');
const ROOT = 'http://127.0.0.1:4173';
const PUBLIC = 'https://robotics.air-admin8.co.jp';

for (const width of [1440, 390, 360]) {
  for (const product of master.products) {
    test('HP shared Header/Footer and CTA prefill ' + product.id + ' ' + width + 'px', async ({ page }) => {
      await page.setViewportSize({ width, height: 900 });
      const sharedMenuFingerprint = async () => page.evaluate(() => {
        const snap = selector => {
          const el = document.querySelector(selector);
          if (!el) return null;
          const style = getComputedStyle(el), rect = el.getBoundingClientRect();
          return {
            position: style.position, color: style.color,
            background: style.backgroundColor,
            width: Math.round(rect.width), height: Math.round(rect.height)
          };
        };
        return {
          header: snap('header.site-header'),
          nav: snap('header.site-header nav.nav'),
          link: snap('header.site-header nav.nav a'),
          cta: snap('header.site-header nav.nav .nav-cta')
        };
      });
      let homepageMenu = null;
      if (width <= 390) {
        await page.goto(ROOT + '/index.html', { waitUntil: 'networkidle' });
        await page.locator('header.site-header button.menu').click();
        homepageMenu = await sharedMenuFingerprint();
      }
      await page.goto(ROOT + '/' + product.detailPage, { waitUntil: 'networkidle' });
      await expect(page.locator('header.site-header[data-shared-layout="header"]')).toHaveCount(1);
      await expect(page.locator('footer.footer[data-shared-layout="footer"]')).toHaveCount(1);
      // Shared shell is not only a presence check: real SP menu must open,
      // expose navigation and close by Escape without horizontal overflow.
      if (width <= 390) {
        const button = page.locator('header.site-header button.menu');
        const nav = page.locator('header.site-header nav.nav');
        await expect(button).toBeVisible();
        await expect(button).toHaveAttribute('aria-expanded', 'false');
        await button.click();
        await expect(button).toHaveAttribute('aria-expanded', 'true');
        expect(await sharedMenuFingerprint(), product.id + ' must match actual homepage SP layout')
          .toEqual(homepageMenu);
        const navConsult = nav.locator('a[href*="contact.html"]').first();
        await expect(navConsult).toBeVisible();
        const navHref = await navConsult.getAttribute('href');
        expect(new URL(navHref, PUBLIC + '/' + product.detailPage).pathname).toBe('/contact.html');
        await page.keyboard.press('Escape');
        await expect(button).toHaveAttribute('aria-expanded', 'false');
        await expect(nav).toBeHidden();
        expect(await page.evaluate(() => document.documentElement.scrollWidth))
          .toBeLessThanOrEqual(width + 2);
      }
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
