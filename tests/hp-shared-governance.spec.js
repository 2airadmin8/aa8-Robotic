// P1 regression: one shared layout source and one contact prefill system
// across all 13 product pages. Never submit an actual inquiry.
const { test, expect } = require('@playwright/test');
const master = require('../data/products.json');
const ROOT = process.env.AA8_TEST_BASE || 'http://127.0.0.1:4173';
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
        // Google Fonts/third-party timing must not make the local menu test
        // depend on idle network; DOMContentLoaded waits for deferred scripts.
        await page.goto(ROOT + '/index.html', { waitUntil: 'domcontentloaded' });
        await expect(page.locator('header.site-header button.menu')).toBeVisible();
        await page.locator('header.site-header button.menu').click();
        homepageMenu = await sharedMenuFingerprint();
      }
      await page.goto(ROOT + '/' + product.detailPage, { waitUntil: 'networkidle' });
      // V3.3 real-browser policy: prove *computed* mother font and neutral
      // specifications on every public product, not only CSS file existence.
      await expect(page.locator('main[data-aa8-visual-version="3.3"]')).toHaveCount(1);
      await expect(page.locator('link[href*="product-standard-v33.css"]')).toHaveCount(1);
      const v33 = await page.evaluate(() => {
        const c = el => getComputedStyle(el).backgroundColor;
        const main = document.querySelector('main[data-aa8-visual-version="3.3"]');
        const neutral = ['rgb(255, 255, 255)', 'rgb(245, 245, 245)', 'rgb(238, 238, 238)'];
        const category = '.g1-spec-group,.a2-category-row,.x2-category-row,.spec-group,.group-row';
        const specs = [...main.querySelectorAll('table')].map(table => ({
          table: c(table),
          section: c(table.closest('section') || table.parentElement),
          rows: [...table.querySelectorAll('tbody tr')].map((row, i) => ({
            rendered: c(row),
            expected: row.matches(category) ? neutral[2] : (i % 2 ? neutral[1] : neutral[0]),
          })),
        }));
        const x2 = main.querySelector('#specs .spec-table');
        const x2Rows = x2 ? [...x2.querySelectorAll('p')].map((row, i) => ({
          rendered: c(row),
          expected: i % 2 ? neutral[1] : neutral[0],
        })) : [];
        return {
          font: getComputedStyle(main).fontFamily,
          bodyFont: getComputedStyle(document.body).fontFamily,
          bodyInk: getComputedStyle(document.body).color,
          footer: c(document.querySelector('footer.footer')),
          specCount: specs.length + (x2 ? 1 : 0),
          surfaces: specs.flatMap(x => [x.table, x.section]).concat(x2 ? [
            c(main.querySelector('#specs')),c(x2)] : []),
          violations: specs.flatMap(x => x.rows.filter(r => r.rendered !== r.expected))
            .concat(x2Rows.filter(r => r.rendered !== r.expected)),
        };
      });
      expect(v33.font, product.id + ' Noto body font').toContain('Noto Sans JP');
      expect(v33.bodyFont, product.id + ' site Noto font').toContain('Noto Sans JP');
      expect(v33.bodyInk, product.id + ' corporate text').toBe('rgb(51, 51, 51)');
      expect(v33.footer, product.id + ' corporate light footer').toBe('rgb(244, 248, 250)');
      expect(v33.specCount, product.id + ' missing specs').toBeGreaterThan(0);
      expect(v33.surfaces, product.id + ' blue/colored spec surface')
        .toEqual(v33.surfaces.map(() => 'rgb(255, 255, 255)'));
      expect(v33.violations, product.id + ' wrong white/grey row pattern').toEqual([]);
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


// C07 V3.3 spacing CSS mapping: native Figma variables 4..80 read back;
// component-level Figma variable binding is NOT attested by this browser test.
for (const width of [1440, 390, 360]) {
  test('C07 V3.3 spacing CSS mapping '+width+'px',async ({page}) => {
    await page.setViewportSize({width,height:900});
    await page.goto(ROOT+'/index.html',{waitUntil:'domcontentloaded'});
    const result=await page.evaluate(()=>{
      const root=getComputedStyle(document.documentElement);
      const space=[4,8,12,16,24,32,40,48,64,80];
      return {
        variables:space.map(n=>root.getPropertyValue('--aa8-v33-spacing-'+n).trim()),
        heroGap:getComputedStyle(document.querySelector('.hero .actions')).gap,
        overflow:document.documentElement.scrollWidth-innerWidth
      };
    });
    expect(result.variables).toEqual(
      [4,8,12,16,24,32,40,48,64,80].map(n=>n+'px'));
    // Current approved SP hero overrides the generic 12px gap with 10px.
    expect(result.heroGap).toBe(width===1440?'12px':'10px');
    expect(result.overflow).toBeLessThanOrEqual(1);
  });
}
