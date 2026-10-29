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
    await expect(page.locator('.g1-hero-video-poster')).toHaveAttribute('href', officialVideo);
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
      const box = q => { const r = document.querySelector(q).getBoundingClientRect();return { x:r.x, y:r.y, width:r.width, height:r.height }; };
      return { copy:box('.g1-hero-copy'), media:box('.g1-hero-media'),
        lead:box('.g1-hero-lead'), video:box('.g1-hero-video'), description:box('.g1-hero-description'),
        buttons:box('.g1-hero-ctas'), primary:box('.g1-hero-ctas .g1-button:first-child'),
        secondary:box('.g1-hero-ctas .g1-button:last-child'), hero:box('.g1-hero'),
        modelHeading:box('#models h2'),
        overflow:document.documentElement.scrollWidth > innerWidth + 1 };
    });
    expect(boxes.overflow).toBe(false);
    if (width === 1440) {
      expect(boxes.copy.x).toBeLessThan(boxes.media.x);
      expect(boxes.media.width).toBeGreaterThanOrEqual(590);
    } else {
      // Figma visible SP 390 Product-first 2.1 / 13:2, 22:81:
      // headline, then official video, then description, two equal CTAs on one row.
      expect(boxes.lead.y).toBeLessThan(boxes.video.y);
      expect(boxes.video.y).toBeLessThan(boxes.description.y);
      expect(boxes.description.y).toBeLessThan(boxes.buttons.y);
      expect(boxes.primary.y).toBe(boxes.secondary.y);
      expect(Math.abs(boxes.primary.width - 167)).toBeLessThanOrEqual(3);
      expect(Math.abs(boxes.secondary.width - 167)).toBeLessThanOrEqual(3);
      expect(boxes.video.width).toBeGreaterThanOrEqual(340);
      expect(boxes.hero.height).toBeLessThan(760);
      expect(boxes.hero.height).toBeGreaterThan(600);
      // Figma SP node 13:164: NEXT STEP 1330px, three cards 328px each.
      const cta = await page.evaluate(() => {
        const rect = e => e.getBoundingClientRect();
        return {
          height:rect(document.querySelector('.g1-final-cta')).height,
          cards:[...document.querySelectorAll('.g1-cta-card')].map(e => rect(e).height),
          images:[...document.querySelectorAll('.g1-cta-photo')].map(e => rect(e).height),
          title:document.querySelector('.g1-final-cta h2').innerText.trim()
        };
      });
      expect(Math.abs(cta.height - 1330)).toBeLessThanOrEqual(35);
      for (const h of cta.cards) expect(Math.abs(h - 328)).toBeLessThanOrEqual(3);
      for (const h of cta.images) expect(Math.abs(h - 140)).toBeLessThanOrEqual(3);
      expect(cta.title).toContain('次の一歩へ');
      await expect(page.locator('.g1-hero-ctas a').first()).toContainText('公式デモを見る');
      await expect(page.locator('.g1-hero-ctas a').last()).toContainText('導入を相談する');
      await expect(page.locator('#models .g1-heading .g1-sp-only')).toContainText('通常版の二次開発は非対応です。');
    }
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
    // A visitor must stay on AirAdmin8 while playing the manufacturer's
    // original YouTube video, with the inquiry CTA still available.
    await expect(page.locator('.g1-video-iframe')).toHaveCount(0);
    await page.locator('.g1-hero-video-poster').click();
    await expect(page.locator('.g1-video-iframe')).toHaveAttribute(
      'src', /youtube-nocookie[.]com\/embed\/O5GphCrjx98/
    );
    await expect(page.locator('.g1-hero-ctas a.secondary')).toHaveAttribute('href', /contact[.]html/);
    expect(page.url()).toContain('/products/unitree-g1.html');
    const ctaStyle = await page.locator('.g1-final-cta').evaluate(el => {
      const s = getComputedStyle(el);
      return { background: s.backgroundImage, h2Color: getComputedStyle(el.querySelector('h2')).color };
    });
    expect(ctaStyle.background).toContain('g1-cta-figma-pc.png');
    expect(ctaStyle.h2Color).toBe('rgb(255, 255, 255)');
  });
}

test('G1 bottom video CTA plays on this page without external navigation', async ({ page }) => {
  await page.setViewportSize({width: 1440, height: 900});
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.locator('.g1-cta-grid [data-g1-video-trigger]').click();
  await expect(page.locator('.g1-video-iframe')).toHaveCount(1);
  expect(page.url()).toContain('/products/unitree-g1.html');
});

// Figma PC 11:2 / SP 13:2 background color contract.
// All primary content sections are pure white, no alternating legacy pale tint.
// NEXT STEP alone uses exact approved Figma geometric blue asset (#12).
for (const width of [1440, 390]) {
  test('G1 Figma white backgrounds and approved CTA asset / ' + width + 'px', async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto(url, { waitUntil: 'networkidle' });
    const audit = await page.evaluate(() => {
      const selectors = [
        '.g1-hero', '.g1-anchor-nav', '#capabilities', '.g1-detail-gallery',
        '#research', '#models', '#specifications', '#architecture',
        '#readiness', '.g1-support', '.g1-faq', '.g1-related'
      ];
      const sections = selectors.map(sel => ({ selector:sel,
        color:getComputedStyle(document.querySelector(sel)).backgroundColor,
        image:getComputedStyle(document.querySelector(sel)).backgroundImage }));
      const cta=document.querySelector('.g1-final-cta');
      return {
        sections, ctaBackground:getComputedStyle(cta).backgroundImage,
        titleColor:getComputedStyle(cta.querySelector('h2')).color,
        kickerColor:getComputedStyle(cta.querySelector('.g1-kicker')).color,
        bodyColor:getComputedStyle(cta.querySelector('.g1-shell > p:not(.g1-kicker)')).color
      };
    });
    expect(audit.sections.filter(x=>x.color!=='rgb(255, 255, 255)')).toEqual([]);
    expect(audit.sections.filter(x=>x.image!=='none')).toEqual([]);
    expect(audit.ctaBackground).toContain('g1-cta-figma-pc.png');
    expect(audit.titleColor).toBe('rgb(255, 255, 255)');
    const response=await page.request.get('http://127.0.0.1:4173/assets/img/products/unitree/g1/g1-cta-figma-pc.png');
    expect(response.status()).toBe(200);
    expect((await response.body()).length).toBeGreaterThan(100000);
  });
}
