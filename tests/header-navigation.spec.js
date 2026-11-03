const { test, expect } = require('@playwright/test');

const pages = ['/index.html', '/support.html', '/glossary.html', '/products/unitree-g1.html'];

for (const path of pages) {
  test.describe(`header navigation ${path}`, () => {
    test('SP: menu opens, is usable, and closes', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto(`http://127.0.0.1:4173${path}`, { waitUntil: 'networkidle' });

      const menu = page.locator('.site-header .menu');
      const nav = page.locator('.site-header .nav');
      const lastLink = nav.locator('a').last();

      await expect(menu).toBeVisible();
      await expect(menu).toHaveAttribute('aria-expanded', 'false');
      await expect(nav).toBeHidden();

      await menu.click();
      await expect(menu).toHaveAttribute('aria-expanded', 'true');
      await expect(nav).toBeVisible();
      await expect(lastLink).toBeVisible();

      const navBox = await nav.boundingBox();
      expect(navBox).not.toBeNull();
      expect(navBox.x).toBeGreaterThanOrEqual(0);
      expect(navBox.y).toBeGreaterThanOrEqual(0);
      expect(navBox.width).toBeLessThanOrEqual(390);

      await menu.click();
      await expect(menu).toHaveAttribute('aria-expanded', 'false');
      await expect(nav).toBeHidden();
    });

    test('PC: navigation is visible and menu button is hidden', async ({ page }) => {
      await page.setViewportSize({ width: 1440, height: 900 });
      await page.goto(`http://127.0.0.1:4173${path}`, { waitUntil: 'networkidle' });

      await expect(page.locator('.site-header .nav')).toBeVisible();
      await expect(page.locator('.site-header .menu')).toBeHidden();
    });
  });
}

test('breakpoint contract: 980 is SP, 981 is PC', async ({ page }) => {
  await page.setViewportSize({ width: 980, height: 844 });
  await page.goto('http://127.0.0.1:4173/index.html', { waitUntil: 'networkidle' });
  await expect(page.locator('.site-header .menu')).toBeVisible();
  await expect(page.locator('.site-header .nav')).toBeHidden();

  await page.setViewportSize({ width: 981, height: 844 });
  await expect(page.locator('.site-header .menu')).toBeHidden();
  await expect(page.locator('.site-header .nav')).toBeVisible();
});

test('legacy repository-prefix product URL redirects to the current URL', async ({ page }) => {
  await page.goto('http://127.0.0.1:4173/aa8-Robotic/products/tianji-marvin.html');
  await expect(page).toHaveURL('https://robotics.air-admin8.co.jp/products/tianji-marvin.html');
});

// G1 must render the same site-owned header and footer as the Robotics homepage,
// not page-specific lookalikes. Check real computed geometry at PC and SP widths.
for (const width of [1440, 390]) {
  test(`G1 common header/footer parity at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    const measure = async (path) => {
      await page.goto(`http://127.0.0.1:4173${path}`, { waitUntil: 'networkidle' });
      return page.evaluate(() => {
        const measureNode = (selector) => {
          const el = document.querySelector(selector);
          if (!el) return null;
          const computed = getComputedStyle(el);
          const r = el.getBoundingClientRect();
          return {
            width: Math.round(r.width), height: Math.round(r.height),
            display: computed.display, color: computed.color,
            background: computed.backgroundColor, position: computed.position
          };
        };
        return {
          headerCount: document.querySelectorAll('header.site-header[data-shared-layout="header"]').length,
          footerCount: document.querySelectorAll('footer.footer[data-shared-layout="footer"]').length,
          header: measureNode('.site-header'),
          headerInner: measureNode('.site-header .header-inner'),
          footer: measureNode('footer.footer'),
          footerGrid: measureNode('.footer .footer-grid'),
          navigation: [...document.querySelectorAll('.site-header .nav a')].map(x => x.textContent.trim()),
          footerLinks: [...document.querySelectorAll('.footer .footer-links a')].map(x => x.textContent.trim())
        };
      });
    };
    const home = await measure('/index.html');
    const g1 = await measure('/products/unitree-g1.html');
    expect(g1).toEqual(home);
    expect(g1.headerCount).toBe(1);
    expect(g1.footerCount).toBe(1);
  });
}


// Issue #138: actual G1+ -> inquiry handoff must never fetch retired GitHub Pages assets.
// This test checks navigation and prefilling only: it MUST NOT submit a real inquiry.
for (const width of [1440, 390]) {
  test(`Issue138 G1+ inquiry zero legacy asset 404 at ${width}px`, async ({page}) => {
    await page.setViewportSize({width, height:900});
    const brokenAssets=[], pageErrors=[];
    page.on('response', response => {
      const url=new URL(response.url());
      if (url.origin === 'http://127.0.0.1:4173' && response.status() >= 400)
        brokenAssets.push({path:url.pathname, status:response.status()});
    });
    page.on('pageerror', error => pageErrors.push(error.message));
    await page.goto('http://127.0.0.1:4173/products/unitree-g1-plus.html',
      {waitUntil:'networkidle'});
    await page.locator('.g1-hero-ctas .g1-button.primary').click();
    await expect(page).toHaveURL(/\/contact\.html\?product=/);
    await page.waitForLoadState('networkidle');
    await expect(page.locator('[name="source_product"]')).toHaveValue('Unitree G1+');
    await expect(page.locator('[name="product"]')).toHaveValue('Unitree G1+');
    await expect(page.locator('[name="source_service"]')).toHaveValue('university-procurement');
    await expect(page.locator('[name="category"]')).toHaveValue('見積・大学購買');
    await expect(page.locator('#contact-form')).toBeVisible();
    await expect(page.locator('script[src*="analytics-events.js"]')).toHaveCount(1);
    await expect(page.locator('script[src*="/seo.js"]')).toHaveCount(0);
    expect(await page.evaluate(() =>
      [...document.scripts].some(s=>s.src.includes('/aa8-Robotic/assets/')))).toBe(false);
    expect(await page.evaluate(() => document.documentElement.scrollWidth))
      .toBeLessThanOrEqual(width + 1);
    expect(brokenAssets).toEqual([]);
    expect(pageErrors).toEqual([]);
  });
}
