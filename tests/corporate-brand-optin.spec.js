// Exact mother-site Corporate V1 opt-in regression.
// Browser rewrites ONLY the temporary response body class; no published page is modified.
const { test, expect } = require('@playwright/test');
const BASE = 'http://127.0.0.1:4173';
async function openOptIn(page, width) {
  await page.setViewportSize({width, height: 844});
  await page.route(BASE + '/index.html', async route => {
    const response = await route.fetch();
    let html = await response.text();
    if (!/<body\b/i.test(html)) throw Error('Corporate QA: missing body');
    html = html.replace(/<body([^>]*)>/i, (_, attrs) => {
      const match = /\bclass=(["'])(.*?)\1/i.exec(attrs);
      if (match) return '<body' + attrs.replace(match[0],
        'class=' + match[1] + match[2] + ' aa8-corporate-v1' + match[1]) + '>';
      return '<body' + attrs + ' class="aa8-corporate-v1">';
    });
    await route.fulfill({response,body:html});
  });
  await page.goto(BASE + '/index.html', {waitUntil:'networkidle'});
  await expect(page.locator('body.aa8-corporate-v1')).toHaveCount(1);
}
for (const width of [1440,1024]) {
  test('corporate PC header/footer and brand tokens ' + width, async ({page}) => {
    await openOptIn(page,width);
    await expect(page.locator('header.site-header .nav')).toBeVisible();
    await expect(page.locator('header.site-header .menu')).toBeHidden();
    const s=await page.evaluate(()=>{
      const root=getComputedStyle(document.documentElement);
      const header=getComputedStyle(document.querySelector('.site-header'));
      const footer=getComputedStyle(document.querySelector('.footer'));
      return {blue:root.getPropertyValue('--aa8-corp-primary').trim(),deep:root.getPropertyValue('--aa8-corp-deep').trim(),ink:header.color,footer:footer.backgroundColor};
    });
    expect(s.blue).toBe('#009bd2');
    expect(s.deep).toBe('#0069b5');
    expect(s.ink).toBe('rgb(51, 51, 51)');
    expect(s.footer).toBe('rgb(244, 248, 250)');
    expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width+2);
  });
}
for (const width of [1023,390,360]) {
  test('corporate SP full-viewport menu and focus contract '+width, async ({page})=>{
    await openOptIn(page,width);
    const toggle=page.locator('.site-header .menu');
    const nav=page.locator('.site-header .nav');
    await expect(toggle).toBeVisible();
    await expect(nav).toBeHidden();
    await toggle.click();
    await expect(toggle).toHaveAttribute('aria-expanded','true');
    await expect(nav).toBeVisible();
    await expect(nav.locator('a').first()).toHaveCSS('color','rgb(255, 255, 255)');
    await expect(page.locator('body')).toHaveClass(/aa8-corporate-menu-open/);
    const navStyle=await nav.evaluate(el=>({
      position:getComputedStyle(el).position,
      background:getComputedStyle(el).backgroundImage,
      width:Math.round(el.getBoundingClientRect().width)
    }));
    expect(navStyle.position).toBe('fixed');
    expect(navStyle.background).toContain('linear-gradient');
    expect(navStyle.width).toBeLessThanOrEqual(width+2);
    const last=nav.locator('a').last();
    await expect(last).toBeVisible();
    await last.focus();
    await page.keyboard.press('Tab');
    await expect(toggle).toBeFocused();
    await page.keyboard.press('Escape');
    await expect(nav).toBeHidden();
    await expect(toggle).toHaveAttribute('aria-expanded','false');
    await expect(toggle).toBeFocused();
    await expect(page.locator('body')).not.toHaveClass(/aa8-corporate-menu-open/);
    expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width+2);
  });
}
