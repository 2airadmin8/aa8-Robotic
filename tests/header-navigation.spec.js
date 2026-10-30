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

// V16｜CEO main-site reference: gradient full-screen SP overlay, not a white
// bottom-aligned drawer. These assertions must fail on the pre-fix production.
const v16Base = (process.env.SP_MENU_BASE_URL || 'http://127.0.0.1:4173').replace(/\/$/, '');
const v16Sizes = [
  {width: 390, height: 844},
  {width: 375, height: 667},
  {width: 360, height: 640},
  {width: 320, height: 480},
  {width: 768, height: 900},
  {width: 980, height: 844},
];

for (const viewport of v16Sizes) {
  test('V16 main-site mobile menu visual and accessibility ' +
    viewport.width + 'x' + viewport.height, async ({page}) => {
    await page.setViewportSize(viewport);
    const errors=[];page.on('pageerror',error=>errors.push(error.message));
    await page.goto(v16Base+'/index.html',{waitUntil:'networkidle'});
    // Open from the real visible header, not an offscreen synthetic scroll state.
    // The overlay itself must lock the underlying document while it is open.
    const beforeY=await page.evaluate(()=>scrollY);
    const menu=page.locator('header.site-header .menu');
    const nav=page.locator('header.site-header #nav');

    await expect(menu).toBeVisible();
    await expect(menu).toHaveAttribute('aria-expanded','false');
    await expect(menu).toHaveAttribute('aria-label','メニューを開く');
    await expect(nav).toBeHidden();
    await menu.click();
    await expect(menu).toHaveAttribute('aria-expanded','true');
    await expect(menu).toHaveAttribute('aria-label','メニューを閉じる');
    await expect(nav).toBeVisible();
    await expect(page.locator('body')).toHaveClass(/nav-is-open/);

    const m=await page.evaluate(()=>{
      const nav=document.querySelector('.site-header #nav');
      const menu=document.querySelector('.site-header .menu');
      const r=nav.getBoundingClientRect(),c=getComputedStyle(nav);
      const mr=menu.getBoundingClientRect(),mc=getComputedStyle(menu);
      const links=[...nav.querySelectorAll('a')].map(a=>{
        const v=a.getBoundingClientRect(),s=getComputedStyle(a);
        return {text:a.textContent.trim(),href:a.getAttribute('href'),x:v.x,y:v.y,w:v.width,h:v.height,
          color:s.color,font:parseFloat(s.fontSize),border:s.borderColor,bg:s.backgroundColor,
          radius:s.borderRadius};
      });
      const style=getComputedStyle(document.body);
      return {rect:{x:r.x,y:r.y,w:r.width,h:r.height},navBackground:c.backgroundImage,
        navPosition:c.position,justify:c.justifyContent,scrollHeight:nav.scrollHeight,
        clientHeight:nav.clientHeight,bodyOverflow:style.overflow,
        menuRect:{x:mr.x,y:mr.y,w:mr.width,h:mr.height},
        menuFont:parseFloat(mc.fontSize),menuBefore:getComputedStyle(menu,'::before').backgroundColor,
        menuAfter:getComputedStyle(menu,'::after').backgroundColor,
        links,docOverflow:document.documentElement.scrollWidth-innerWidth};
    });
    expect(m.navPosition).toBe('fixed');
    expect(Math.abs(m.rect.x)).toBeLessThanOrEqual(1);
    expect(Math.abs(m.rect.y)).toBeLessThanOrEqual(1);
    expect(Math.abs(m.rect.w-viewport.width)).toBeLessThanOrEqual(1);
    expect(Math.abs(m.rect.h-viewport.height)).toBeLessThanOrEqual(1);
    // Exact colors sampled from the CEO-provided AirAdmin8 main-site screenshot.
    expect(m.navBackground).toContain('rgb(18, 117, 187)');
    expect(m.navBackground).toContain('rgb(18, 162, 213)');
    expect(m.navBackground).toContain('rgb(18, 183, 193)');
    expect(m.bodyOverflow).toBe('hidden');
    expect(m.menuBefore).toBe('rgb(255, 255, 255)');
    expect(m.menuAfter).toBe('rgb(255, 255, 255)');
    expect(m.menuFont).toBe(0);
    expect(m.menuRect.x).toBeGreaterThan(viewport.width-70);
    expect(m.menuRect.y).toBeLessThanOrEqual(20);
    expect(m.links).toHaveLength(6);
    expect(m.links.slice(0,5).every(x=>
      x.color==='rgb(255, 255, 255)' && x.font>=17 &&
      Math.abs(x.x+x.w/2-viewport.width/2)<=1
    )).toBe(true);
    expect(m.links[0].y).toBeLessThan(viewport.height*.5);
    expect(m.links[5].text).toBe('導入を相談する');
    expect(m.links[5].border).toBe('rgb(255, 255, 255)');
    expect(m.links[5].radius).toBe('999px');
    expect(m.links[5].h).toBeGreaterThanOrEqual(44);
    expect(m.docOverflow).toBeLessThanOrEqual(1);

    // The overlay must trap keyboard focus and close without hiding the page.
    await menu.focus();
    await page.keyboard.press('Shift+Tab');
    await expect(nav.locator('a').last()).toBeFocused();
    await page.keyboard.press('Tab');
    await expect(menu).toBeFocused();
    await page.keyboard.press('Escape');
    await expect(nav).toBeHidden();
    await expect(menu).toHaveAttribute('aria-expanded','false');
    await expect(menu).toHaveAttribute('aria-label','メニューを開く');
    await expect(page.locator('body')).not.toHaveClass(/nav-is-open/);
    await expect(menu).toBeFocused();
    const afterY=await page.evaluate(()=>scrollY);
    expect(Math.abs(afterY-beforeY)).toBeLessThanOrEqual(2);
    expect(errors).toEqual([]);
  });
}

// Shared Header must work on all page templates, including nested G1 and G1+.
for (const path of ['/index.html','/products.html','/cases.html','/resources.html',
  '/support.html','/contact.html','/products/unitree-g1.html','/products/unitree-g1-plus.html']) {
  test('V16 SP shared header route and close '+path,async({page})=>{
    await page.setViewportSize({width:390,height:844});
    const errors=[];page.on('pageerror',error=>errors.push(error.message));
    await page.goto(v16Base+path,{waitUntil:'networkidle'});
    const menu=page.locator('.site-header .menu'),nav=page.locator('.site-header #nav');
    await menu.click();
    await expect(nav).toBeVisible();
    await expect(page.locator('body')).toHaveClass(/nav-is-open/);
    await menu.click();
    await expect(nav).toBeHidden();
    await expect(page.locator('body')).not.toHaveClass(/nav-is-open/);
    await menu.click();
    await nav.locator('a[data-nav-key="products"]').click();
    await expect(page).toHaveURL(/\/products\.html(?:\?.*)?$/);
    await expect(page.locator('.site-header #nav')).toBeHidden();
    await expect(page.locator('body')).not.toHaveClass(/nav-is-open/);
    expect(errors).toEqual([]);
  });
}

test('V16 PC breakpoint unaffected and responsive transition closes overlay',async({page})=>{
  await page.setViewportSize({width:980,height:844});
  await page.goto(v16Base+'/index.html',{waitUntil:'networkidle'});
  const menu=page.locator('.site-header .menu'),nav=page.locator('.site-header #nav');
  await menu.click();
  await expect(nav).toBeVisible();
  await expect(page.locator('body')).toHaveClass(/nav-is-open/);
  await page.setViewportSize({width:981,height:844});
  await expect(menu).toBeHidden();
  await expect(nav).toBeVisible();
  await expect(page.locator('body')).not.toHaveClass(/nav-is-open/);
  const layout=await page.evaluate(()=>{
    const n=document.querySelector('.site-header #nav');
    return{display:getComputedStyle(n).display,position:getComputedStyle(n).position,
      gradient:getComputedStyle(n).backgroundImage};
  });
  expect(layout.display).toBe('flex');
  expect(layout.position).toBe('static');
  expect(layout.gradient).toBe('none');
});
