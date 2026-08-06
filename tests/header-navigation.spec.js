const { test, expect } = require('@playwright/test');

const pages = ['/index.html', '/support.html', '/glossary.html'];

for (const path of pages) {
  test.describe(`header navigation ${path}`, () => {
    test('SP: full-screen menu opens cleanly and closes', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto(`http://127.0.0.1:4173${path}`, { waitUntil: 'networkidle' });

      const menu = page.locator('.site-header .menu');
      const nav = page.locator('.site-header .nav');
      const links = nav.locator('a');
      const cta = nav.locator('.nav-cta');

      await expect(menu).toBeVisible();
      await expect(menu).toHaveAttribute('aria-expanded', 'false');
      await expect(nav).toBeHidden();

      await menu.click();
      await expect(menu).toHaveAttribute('aria-expanded', 'true');
      await expect(nav).toBeVisible();
      await expect(links).toHaveCount(6);
      await expect(cta).toBeVisible();

      const navBox = await nav.boundingBox();
      expect(navBox).not.toBeNull();
      expect(navBox.x).toBe(0);
      expect(navBox.y).toBe(0);
      expect(navBox.width).toBeGreaterThanOrEqual(389);
      expect(navBox.height).toBeGreaterThanOrEqual(843);

      const navStyle = await nav.evaluate((node) => {
        const style = getComputedStyle(node);
        return { position: style.position, overflowY: style.overflowY };
      });
      expect(navStyle.position).toBe('fixed');
      expect(navStyle.overflowY).toBe('auto');

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
