const { test, expect } = require('@playwright/test');
const url = 'http://127.0.0.1:4173/products/unitree-g1.html';
const officialVideo = 'https://www.youtube.com/watch?v=O5GphCrjx98';
// Figma: H97ouesPVrnegchKuYqoRr, node 11:2.
// Prevent technically green legacy-template deployments with incorrect design.
for (const width of [1440, 390]) {
  test('G1 Figma design contract / ' + width + 'px', async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto(url, { waitUntil: 'networkidle' });
    await expect(page.locator('main.g1-page')).toBeVisible();
    await expect(page.locator('.site-header[data-shared-layout="header"]')).toHaveCount(1);
    await expect(page.locator('footer[data-shared-layout="footer"]')).toHaveCount(1);
    await expect(page.locator('#g1-title')).toHaveText('Unitree G1');
    await expect(page.locator('.g1-hero-ctas a').first()).toHaveAttribute('href', officialVideo);
    await expect(page.locator('.g1-hero-video')).toHaveAttribute('href', officialVideo);
    await expect(page.locator('.g1-video-play')).toBeVisible();
    const links = await page.locator('.g1-anchor-nav a').allTextContents();
    expect(links.map(s => s.trim())).toEqual(['G1の特長', '研究テーマ', 'G1 / EDUの違い', '仕様・開発環境']);
    await expect(page.locator('.g1-proof-list article')).toHaveCount(3);
    await expect(page.locator('.g1-detail-grid img')).toHaveCount(6);
    await expect(page.locator('.g1-use-list article')).toHaveCount(3);
    await expect(page.locator('#models .g1-model-grid article')).toHaveCount(2);
    await expect(page.locator('#models h2')).toHaveText('G1 と G1 EDU の違い');
    await expect(page.locator('.g1-related-grid .g1-related-item')).toHaveCount(6);
    await expect(page.locator('.g1-cta-grid .g1-cta-card')).toHaveCount(3);
    await expect(page.locator('.g1-faq-list details')).toHaveCount(3);
    await expect(page.locator('.g1-spec-table tbody tr:not(.g1-spec-group)')).toHaveCount(28);
    const boxes = await page.evaluate(() => {
      const box = q => { const r = document.querySelector(q).getBoundingClientRect();return { x:r.x, y:r.y, width:r.width }; };
      return { copy:box('.g1-hero-copy'), media:box('.g1-hero-media'), modelHeading:box('#models h2'),
        overflow:document.documentElement.scrollWidth > innerWidth + 1 };
    });
    expect(boxes.overflow).toBe(false);
    if (width === 1440) {
      expect(boxes.copy.x).toBeLessThan(boxes.media.x);
      expect(boxes.media.width).toBeGreaterThanOrEqual(590);
    } else expect(boxes.copy.y).toBeLessThan(boxes.media.y);
    const errors = await page.evaluate(async () => {
      const imgs=[...document.querySelectorAll('.g1-page img')];
      await Promise.all(imgs.map(img => {
        img.loading='eager';
        return new Promise(done => {
          if(img.complete)return done();
          img.addEventListener('load',done,{once:true});
          img.addEventListener('error',done,{once:true});
        });
      }));
      return imgs.filter(img=>!img.naturalWidth).map(img=>img.src);
    });
    expect(errors).toEqual([]);
  });
}
