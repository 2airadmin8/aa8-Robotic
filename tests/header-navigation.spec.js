const { test, expect } = require('@playwright/test');

const pages = ['/index.html', '/support.html', '/glossary.html'];

for (const path of pages) {
  test.describe(`header navigation ${path}`, () => {
    test('SP: menu opens with compact translucent overlay and closes', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto(`http://127.0.0.1:4173${path}`, { waitUntil: 'networkidle' });

      const menu = page.locator('.site-header .menu');
      const nav = page.locator('.site-header .nav');
      const links = nav.locator('a');
      const lastLink = links.last();

      await expect(menu).toBeVisible();
      await expect(menu).toHaveAttribute('aria-expanded', 'false');
      await expect(nav).toBeHidden();

      await menu.click();
      await expect(menu).toHaveAttribute('aria-expanded', 'true');
      await expect(nav).toBeVisible();
      await expect(links).toHaveCount(6);
      await expect(lastLink).toBeVisible();

      const state = await nav.evaluate((element) => {
        const style = getComputedStyle(element);
        const link = element.querySelector('a');
        const linkStyle = link ? getComputedStyle(link) : null;
        return {
          position: style.position,
          height: style.height,
          backgroundImage: style.backgroundImage,
          justifyContent: style.justifyContent,
          linkFontSize: linkStyle?.fontSize || '',
        };
      });

      expect(state.position).toBe('fixed');
      expect(parseFloat(state.height)).toBeGreaterThanOrEqual(800);
      expect(state.backgroundImage).toContain('linear-gradient');
      expect(state.justifyContent).toBe('center');
      expect(parseFloat(state.linkFontSize)).toBeLessThanOrEqual(20);

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
