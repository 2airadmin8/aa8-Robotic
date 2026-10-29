const { createHash } = require('node:crypto');
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
    // Shared-drive official G1 original g1.png is byte-identical to static
    // assets/img/products/unitree/catalog/28_g1.png, confirmed by SHA256.
    // The 01/FLEXIBILITY proof photo must use this file, while gallery photos remain independent.
    await expect(page.locator('.g1-proof-photo img')).toHaveAttribute(
      'src', '/assets/img/products/unitree/catalog/28_g1.png'
    );
    await expect(page.locator('.g1-detail-grid img')).toHaveCount(6);
    expect(await page.locator('.g1-detail-grid img').first().getAttribute('src')).toContain('/g1/g1-dexterous-hand.jpg');

    await expect(page.locator('.g1-detail-grid img')).toHaveCount(6);
    await expect(page.locator('.g1-use-list article')).toHaveCount(3);
    await expect(page.locator('#models .g1-model-grid article')).toHaveCount(2);
    await expect(page.locator('#models h2')).toHaveText('G1 と G1 EDU の違い');
    await expect(page.locator('.g1-related-grid .g1-related-item')).toHaveCount(6);
    const officialCatalogFiles = ["28_g1.png", "29_g1pl.png", "26_h2.png", "22_go2.png", "24_a2.png", "23_b2.png"];
    const actualCatalogFiles = await page.locator('.g1-related-grid .g1-related-item img').evaluateAll(imgs => imgs.map(x => x.getAttribute('src').split('/').pop()));
    expect(actualCatalogFiles).toEqual(officialCatalogFiles);

    await expect(page.locator('.g1-cta-grid .g1-cta-card')).toHaveCount(3);
    await expect(page.locator('.g1-faq-list details')).toHaveCount(3);
    await expect(page.locator('.g1-spec-table tbody tr:not(.g1-spec-group)')).toHaveCount(28);
    await expect(page.locator('.g1-spec-table thead th').first()).toHaveText('モデル');

    // Missing spec-image prevention, per visible Figma node 62:10 PC / 62:147 SP.
    // Current G1/G1 EDU factual spec values are preserved independently.
    await expect(page.locator('.g1-spec-overview-figure img')).toHaveCount(1);
    await expect(page.locator('.g1-spec-overview-figure img')).toHaveAttribute(
      'src', '/assets/img/products/unitree/g1/g1-spec-annotated-official.jpg'
    );
    // This spec image intentionally uses loading=lazy. Scroll first and wait for
    // the real image to decode rather than checking naturalWidth while off-screen.
    await page.locator('.g1-spec-overview-figure img').scrollIntoViewIfNeeded();
    await expect(page.locator('.g1-spec-overview-figure img')).toHaveJSProperty('naturalWidth', 630);
    const specPhoto = await page.locator('.g1-spec-overview-figure img').evaluate(img => {
      const r=img.getBoundingClientRect();
      const table=document.querySelector('.g1-table-wrap').getBoundingClientRect();
      const style=getComputedStyle(img);
      return {
        width:r.width,height:r.height,objectFit:style.objectFit,
        naturalWidth:img.naturalWidth,naturalHeight:img.naturalHeight,
        top:r.top,bottom:r.bottom,tableTop:table.top
      };
    });
    expect(specPhoto.naturalWidth).toBe(630);
    expect(specPhoto.naturalHeight).toBe(590);
    expect(specPhoto.objectFit).toBe('fill'); // Intrinsic ratio preserved by width:100%, height:auto.
    expect(specPhoto.bottom).toBeLessThan(specPhoto.tableTop);
    // Figma source legend belongs between the overview panel and the
    // comparison table. Never allow it to overflow the absolute image slot.
    const sourceFlow = await page.evaluate(() => {
      const overview = document.querySelector('.g1-spec-overview').getBoundingClientRect();
      const caption = document.querySelector('.g1-spec-image-source').getBoundingClientRect();
      const table = document.querySelector('.g1-table-wrap').getBoundingClientRect();
      return { overviewBottom:overview.bottom, captionTop:caption.top,
        captionBottom:caption.bottom, tableTop:table.top };
    });
    expect(sourceFlow.captionTop).toBeGreaterThanOrEqual(sourceFlow.overviewBottom);
    expect(sourceFlow.captionBottom).toBeLessThan(sourceFlow.tableTop);

    // CEO-approved enlarged image overrides the smaller Figma image slot:
    // PC original 630x590, SP fills 346px and preserves source aspect ratio.
    expect(Math.abs(specPhoto.width-(width===1440?630:346))).toBeLessThanOrEqual(1);
    expect(Math.abs(specPhoto.height-(width===1440?590:346*590/630))).toBeLessThanOrEqual(1);

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

test('G1 Figma official annotated image original-file checksum', async ({ request }) => {
  const response=await request.get('http://127.0.0.1:4173/assets/img/products/unitree/g1/g1-spec-annotated-official.jpg');
  expect(response.status()).toBe(200);
  expect(response.headers()['content-type']).toContain('image/jpeg');
  const bytes=await response.body();
  expect(bytes.length).toBe(26766);
  const digest=createHash('sha256').update(bytes).digest('hex');
  expect(digest).toBe('a67043a37693c814f48c8884e209cf4d647b9660182f3d31d20fef0632fcc0d4');
});

// FAQ Figma content/visibility contract, PC node 11:165 / SP node 13:152.
// The approved design shows all three answers, not three collapsed headings.
for (const width of [1440,390]) {
  test('G1 Figma FAQ initial visual state at '+width+'px',async ({page})=>{
    await page.setViewportSize({width,height:900});
    await page.goto(url,{waitUntil:'networkidle'});
    const faq=page.locator('.g1-faq');
    const faqHeight=await faq.evaluate(el=>el.getBoundingClientRect().height);
    expect(Math.abs(faqHeight-(width===1440?715:630))).toBeLessThanOrEqual(25);
    await expect(faq.locator('.g1-faq-list details')).toHaveCount(3);
    for(const d of await faq.locator('.g1-faq-list details').all()){
      await expect(d).toHaveAttribute('open','');
      await expect(d.locator('p')).toBeVisible();
    }
    const heading=faq.locator('h2');
    await expect(heading).toHaveText('よくあるご質問');
    const position=await heading.evaluate(e=>{
      const h=e.getBoundingClientRect(),s=e.parentElement.getBoundingClientRect();
      return{center:Math.abs((h.left+h.width/2)-(s.left+s.width/2)),kicker:getComputedStyle(e.parentElement.querySelector('.g1-kicker')).display};
    });
    expect(position.center).toBeLessThanOrEqual(1);
    expect(position.kicker).toBe('none');
    const q=faq.locator('details').first().locator('summary');
    if(width===390){
      await expect(q).toContainText('Q. 通常版で独自開発できますか？');
      await expect(faq.locator('.g1-heading .g1-intro')).toContainText('条件は正式資料で最終確認します。');
    } else {
      await expect(q).toContainText('Q. 通常版 G1 で自作プログラムを開発できますか？');
    }
    await q.click();
    await expect(faq.locator('details').first()).not.toHaveAttribute('open','');
  });
}
test('G1 Figma SP capability heading uses mobile copy', async ({page})=>{
  await page.setViewportSize({width:390,height:900});
  await page.goto(url,{waitUntil:'networkidle'});
  await expect(page.locator('#capabilities h2 .g1-sp-only')).toHaveText('動く。学ぶ。つかむ。');
  await expect(page.locator('#capabilities h2 .g1-sp-only')).toBeVisible();
  await expect(page.locator('#capabilities h2 .g1-pc-only')).toBeHidden();
  await expect(page.locator('#capabilities .g1-heading .g1-intro .g1-sp-only')).toHaveText('3つの力で、実機研究の可能性を広げる。');
  await expect(page.locator('#capabilities .g1-proof-photo img')).toHaveAttribute('src','/assets/img/products/unitree/catalog/28_g1.png');
});
