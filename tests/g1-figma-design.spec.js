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
    // PC half-size 315x295, SP fills 346px and preserves source aspect ratio.
    expect(Math.abs(specPhoto.width-(width===1440?315:346))).toBeLessThanOrEqual(1);
    expect(Math.abs(specPhoto.height-(width===1440?295:346*590/630))).toBeLessThanOrEqual(1);

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

// Figma remaining SP-only content design contract (13:96, 13:118, 13:137, 151:55).
// Prevent desktop copy from appearing on mobile by checking the VISIBLE spans.
test('Figma remaining SP-only content design contract',async ({page})=>{
  await page.setViewportSize({width:390,height:900});
  await page.goto(url,{waitUntil:'networkidle'});
  const expected=[
    ['#architecture h2 .g1-sp-only','研究から実機検証へ。'],
    ['#architecture .g1-heading .g1-intro .g1-sp-only','目的別に、構成と評価方法を整理します。'],
    ['#readiness h2 .g1-sp-only','購入前に確認したいこと'],
    ['#readiness .g1-heading .g1-intro .g1-sp-only','研究環境・設置条件を整理します。'],
    ['#readiness article:nth-child(1) h3 .g1-sp-only','研究目的・評価指標'],
    ['#readiness article:nth-child(2) h3 .g1-sp-only','SDKとソフトウェア'],
    ['#readiness article:nth-child(3) h3 .g1-sp-only','安全・設置環境'],
    ['#readiness article:nth-child(4) h3 .g1-sp-only','見積・納期・検収'],
    ['.g1-support h2 .g1-sp-only','社会実装を目指す。'],
    ['.g1-support .g1-heading .g1-intro .g1-sp-only','AirAdmin8が研究・PoCから見積・導入条件まで整理']
  ];
  for (const [selector,txt] of expected) {
    const e=page.locator(selector);
    await expect(e).toBeVisible();
    await expect(e).toHaveText(txt);
  }
  await expect(page.locator('.g1-related .g1-heading h2 .g1-sp-only')).toContainText('ほかの宇樹ロボットも、');
  for (const selector of ['#architecture h2','#readiness h2','.g1-support h2','.g1-related .g1-heading h2']){
    await expect(page.locator(selector+' .g1-pc-only')).toBeHidden();
  }
});
test('PC existing architecture/readiness/support wording unaffected',async ({page})=>{
  await page.setViewportSize({width:1440,height:900});
  await page.goto(url,{waitUntil:'networkidle'});
  for (const [selector,txt] of [
    ['#architecture h2 .g1-pc-only','研究と産業、それぞれの「実証環境」を設計する。'],
    ['#readiness h2 .g1-pc-only','導入前に確認したいこと。'],
    ['.g1-support h2 .g1-pc-only','AirAdmin8と、社会実装を目指す。'],
    ['.g1-related .g1-heading h2 .g1-pc-only','目的に合う、次のUnitreeロボットを。']
  ]){
    await expect(page.locator(selector)).toBeVisible();
    await expect(page.locator(selector)).toHaveText(txt);
  }
});

// Figma mobile final readiness/support/related visuals (13:118/13:137/151:55).
test('Figma mobile final readiness/support/related visuals',async ({page})=>{
  await page.setViewportSize({width:390,height:900});
  await page.goto(url,{waitUntil:'networkidle'});
  const observed=await page.evaluate(()=>{
    const rd=document.querySelector('#readiness'),
      su=document.querySelector('.g1-support'),
      action=document.querySelector('.g1-related-actions .g1-text-link:first-child');
    const metrics=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);
      return {height:r.height,width:r.width,background:s.backgroundColor,color:s.color}};
    return {
      readiness:metrics(rd),support:metrics(su),
      readinessCenter:getComputedStyle(rd.querySelector('.g1-heading')).textAlign,
      supportCenter:getComputedStyle(su.querySelector('.g1-heading')).textAlign,
      readinessItems:[...rd.querySelectorAll('.g1-check-grid article')].map(e=>({
        heading:getComputedStyle(e.querySelector('h3 .g1-sp-only')).color,
        description:getComputedStyle(e.querySelector('p .g1-sp-only')).color})),
      readinessKicker:getComputedStyle(rd.querySelector('.g1-heading .g1-kicker')).display,
      supportKicker:getComputedStyle(su.querySelector('.g1-heading .g1-kicker')).display,
      action:metrics(action),actionHref:action.getAttribute('href')
    };
  });
  expect(Math.abs(observed.readiness.height-765)).toBeLessThanOrEqual(25);
  expect(Math.abs(observed.support.height-618)).toBeLessThanOrEqual(25);
  expect(observed.readinessCenter).toBe('center');
  expect(observed.supportCenter).toBe('center');
  expect(observed.readinessKicker).toBe('none');
  expect(observed.supportKicker).toBe('none');
  expect(observed.readinessItems).toHaveLength(4);
  observed.readinessItems.forEach(item=>{
    expect(item.heading).toBe('rgb(51, 51, 51)');
    expect(item.description).toBe('rgb(102, 102, 102)');
  });
  expect(observed.action.background).toBe('rgb(0, 155, 210)');
  expect(observed.action.color).toBe('rgb(255, 255, 255)');
  expect(Math.abs(observed.action.width-346)).toBeLessThanOrEqual(1);
  expect(Math.abs(observed.action.height-50)).toBeLessThanOrEqual(1);
  expect(observed.actionHref).toBe('/products.html');
});

// Figma PC related lineup button visual contract 151:2 (300x52),
// while SP 151:55 remains the already-approved 346x50.
test('Figma PC related lineup button visual contract',async ({page})=>{
  await page.setViewportSize({width:1440,height:900});
  await page.goto(url,{waitUntil:'networkidle'});
  const button=page.locator('.g1-related-actions .g1-text-link:first-child');
  await expect(button).toHaveAttribute('href','/products.html');
  const s=await button.evaluate(el=>{const r=el.getBoundingClientRect(),c=getComputedStyle(el);
    return{width:r.width,height:r.height,bg:c.backgroundColor,color:c.color,display:c.display}});
  expect(Math.abs(s.width-300)).toBeLessThanOrEqual(1);
  expect(Math.abs(s.height-52)).toBeLessThanOrEqual(1);
  expect(s.bg).toBe('rgb(0, 155, 210)');
  expect(s.color).toBe('rgb(255, 255, 255)');
  expect(s.display).toBe('flex');
});


// Figma NEXT STEP proposal A approved scrim regression:
// PC 256:2 / SP 256:44, same manufacturer image and card positions.
for(const width of [1440,390]){
  test('Figma NEXT STEP proposal A approved scrim regression / '+width+'px',async({page})=>{
    await page.setViewportSize({width,height:900});
    await page.goto(url,{waitUntil:'networkidle'});
    const node=page.locator('main.g1-page > section.g1-section.g1-final-cta');
    await expect(node).toBeVisible();
    await expect(node.locator('.g1-cta-grid .g1-cta-card')).toHaveCount(3);
    const details=await node.evaluate(section=>{
      const css=getComputedStyle(section),
            top=getComputedStyle(section,'::before'),
            foot=getComputedStyle(section,'::after'),
            shell=getComputedStyle(section.querySelector('.g1-shell'));
      const cards=[...section.querySelectorAll('.g1-cta-card')].map(el=>{
        const b=el.getBoundingClientRect();
        return {x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height)}
      });
      return {
        background:css.backgroundImage,
        top:{height:top.height,y:top.top,background:top.backgroundImage,events:top.pointerEvents,z:top.zIndex},
        foot:{height:foot.height,bottom:foot.bottom,background:foot.backgroundImage,events:foot.pointerEvents,z:foot.zIndex},
        shellZ:shell.zIndex,
        cards,
        links:[...section.querySelectorAll('.g1-cta-card')].map(el=>el.getAttribute('href'))
      };
    });
    expect(details.background).toContain('g1-cta-figma-pc.png');
    expect(details.top.height).toBe('207px');
    expect(details.top.y).toBe('0px');
    expect(details.foot.height).toBe(width===1440?'107px':'108px');
    expect(details.foot.bottom).toBe('0px');
    expect(details.top.background).toContain('rgba(5, 38, 61, 0.43)');
    expect(details.foot.background).toContain('rgba(5, 38, 61, 0.43)');
    expect(details.top.background).toContain('21%');
    expect(details.foot.background).toContain('78%');
    expect(details.top.events).toBe('none');
    expect(details.foot.events).toBe('none');
    expect(details.top.z).toBe('0');
    expect(details.foot.z).toBe('0');
    expect(details.shellZ).toBe('1');
    expect(details.cards.every(x=>x.w>300)).toBe(true);
    expect(details.cards.every(x=>Math.abs(x.h-(width===1440?405:328))<=1)).toBe(true);
    expect(details.cards.every(x=>Math.abs(x.w-(width===1440?383:346))<=1)).toBe(true);
    expect(details.links[0]).toContain('youtube.com');
    expect(details.links[1]).toBe('#specifications');
    expect(details.links[2]).toContain('/contact.html');
    expect(await page.evaluate(()=>document.documentElement.scrollWidth))
      .toBeLessThanOrEqual(width+1);
  });
}

// Figma 13:56 (SP 390) / 11:65 (PC1440): single-line 24px research title.
test('Figma SP research title one-line geometry',async({page})=>{
  await page.setViewportSize({width:390,height:900});
  await page.goto(url,{waitUntil:'networkidle'});
  const actual=await page.locator('#research .g1-heading h2').evaluate(el=>{
    const r=el.getBoundingClientRect(),c=getComputedStyle(el),section=el.closest('#research');
    return {font:parseFloat(c.fontSize),height:r.height,section:section.getBoundingClientRect().height,
      text:el.innerText.trim(),width:r.width,overflow:document.documentElement.scrollWidth>innerWidth+1}
  });
  expect(actual.text).toBe('身体性AI、新時代の幕開け。');
  expect(actual.font).toBe(24);
  expect(actual.height).toBeLessThanOrEqual(37);
  expect(Math.abs(actual.section-855)).toBeLessThanOrEqual(15);
  expect(actual.overflow).toBe(false);
});
test('Figma PC research headline remains desktop 30px',async({page})=>{
  await page.setViewportSize({width:1440,height:900});
  await page.goto(url,{waitUntil:'networkidle'});
  const font=await page.locator('#research .g1-heading h2').evaluate(el=>parseFloat(getComputedStyle(el).fontSize));
  expect(font).toBe(30);
});


// Figma G1/EDU comparison 390x840 spatial regression at SP node 13:41.
// Preserve additional purchasing guidance approved as useful business content.
for(const width of [390,360]){
  test('Figma G1/EDU comparison 390x840 spatial regression / '+width+'px',async({page})=>{
    await page.setViewportSize({width,height:900});
    await page.goto(url,{waitUntil:'networkidle'});
    const d=await page.evaluate(()=>{
      const section=document.querySelector('#models'),
            root=section.getBoundingClientRect(),
            rect=sel=>{const e=section.querySelector(sel),r=e.getBoundingClientRect();
              return {top:Math.round(r.top-root.top),height:Math.round(r.height),text:e.innerText.trim()}};
      return {
        sectionHeight:root.height,
        title:rect('h2'),
        intro:rect('.g1-heading .g1-intro'),
        first:rect('.g1-model-grid article:first-child .g1-kicker'),
        second:rect('.g1-model-grid article:nth-child(2) .g1-kicker'),
        note:rect('.g1-model-note'),
        guidance:[...section.querySelectorAll('.g1-model-grid article .g1-fine')]
          .map(e=>e.textContent.trim()),
        overflow:document.documentElement.scrollWidth>innerWidth+1
      };
    });
    expect(Math.abs(d.sectionHeight-840)).toBeLessThanOrEqual(3);
    expect(Math.abs(d.title.top-20)).toBeLessThanOrEqual(1);
    expect(Math.abs(d.intro.top-86)).toBeLessThanOrEqual(2);
    expect(Math.abs(d.first.top-181)).toBeLessThanOrEqual(2);
    // Additional guidance in live HTML remains and explains +12px vs older Figma model 02.
    expect(Math.abs(d.second.top-468)).toBeLessThanOrEqual(3);
    expect(d.guidance).toEqual([
      '購入前に制御範囲・用途を照合',
      '研究目的・開発環境・構成部品を照合'
    ]);
    expect(d.overflow).toBe(false);
  });
}
test('PC model section preserved while SP spacing fixed',async({page})=>{
  await page.setViewportSize({width:1440,height:900});
  await page.goto(url,{waitUntil:'networkidle'});
  const size=await page.locator('#models').evaluate(el=>el.getBoundingClientRect().height);
  expect(Math.abs(size-698)).toBeLessThanOrEqual(3);
});

// Figma SP six-photo gallery headline wraps at the design line break
// node 150:31; protect against splitting the last "る。" from the title.
test('Figma SP six-photo gallery headline wraps at the design line break',async({page})=>{
  await page.setViewportSize({width:390,height:900});
  await page.goto(url,{waitUntil:'networkidle'});
  const h=page.locator('.g1-detail-gallery .g1-heading h2');
  const span=h.locator('.g1-sp-only');
  await expect(span).toBeVisible();
  await expect(h.locator('.g1-pc-only')).toBeHidden();
  await expect(span).toHaveText('機体の可能性を、細部から見る。');
  expect(await span.locator('br').count()).toBe(1);
  const m=await h.evaluate(el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);
    return{font:parseFloat(s.fontSize),line:parseFloat(s.lineHeight),height:r.height}});
  expect(m.font).toBe(24);
  expect(Math.abs(m.height-74)).toBeLessThanOrEqual(2);
  const imgs=page.locator('.g1-detail-grid img');
  await expect(imgs).toHaveCount(6);
});
test('Figma PC six-photo gallery heading unchanged',async({page})=>{
  await page.setViewportSize({width:1440,height:900});
  await page.goto(url,{waitUntil:'networkidle'});
  const h=page.locator('.g1-detail-gallery .g1-heading h2');
  await expect(h.locator('.g1-pc-only')).toBeVisible();
  await expect(h.locator('.g1-sp-only')).toBeHidden();
  expect(await h.evaluate(el=>parseFloat(getComputedStyle(el).fontSize))).toBe(30);
});


// Figma six-photo SP 150:31 card geometry guard.
// The source manufacturer's six images and all PC titles remain unchanged.
for(const width of [390,360]){
  test('Figma six-photo SP 150:31 card geometry guard at '+width+'px',async({page})=>{
    await page.setViewportSize({width,height:900});
    await page.goto(url,{waitUntil:'networkidle'});
    const v=await page.locator('.g1-detail-gallery').evaluate(section=>{
      const origin=section.getBoundingClientRect();
      const box=e=>{const r=e.getBoundingClientRect();
        return {x:Math.round(r.x-origin.x),y:Math.round(r.y-origin.y),w:Math.round(r.width),h:Math.round(r.height)}};
      const cards=[...section.querySelectorAll('.g1-detail-item')];
      return {
        section:box(section),
        kicker:box(section.querySelector('.g1-heading .g1-kicker')),
        title:box(section.querySelector('h2')),
        intro:box(section.querySelector('.g1-heading .g1-intro')),
        grid:box(section.querySelector('.g1-detail-grid')),
        cards:cards.map(c=>({card:box(c),image:box(c.querySelector('.g1-detail-image')),
          title:c.querySelector('h3 .g1-sp-only')?.textContent.trim(),
          pc:getComputedStyle(c.querySelector('h3 .g1-pc-only')).display})),
        note:box(section.querySelector('.g1-shell>.g1-fine')),
        sources:[...section.querySelectorAll('img')].map(i=>i.getAttribute('src')),
        overflow:document.documentElement.scrollWidth>innerWidth+1
      };
    });
    expect(Math.abs(v.section.h-1113)).toBeLessThanOrEqual(1);
    expect(v.kicker.y).toBe(30);
    expect(v.title.y).toBe(69);
    expect(v.intro.y).toBe(143);
    expect(v.grid.y).toBe(215);
    expect(v.cards).toHaveLength(6);
    for(let i=0;i<6;i++){
      const c=v.cards[i];
      expect(c.card.y).toBe([215,215,485,485,755,755][i]);
      expect(c.card.h).toBe(249);
      expect(c.image.h).toBe(173);
      expect(c.pc).toBe('none');
    }
    if(width===390){
      expect(v.cards[0].card.w).toBe(164);
      expect(v.cards[0].image.w).toBe(146);
      expect(v.note.y).toBe(1044);
    }
    expect(v.cards.map(c=>c.title)).toEqual([
      '力制御ハンド','機体構造','全身の可動域',
      '関節の駆動','バッテリー','環境を捉える感知'
    ]);
    expect(v.sources).toHaveLength(6);
    expect(v.overflow).toBe(false);
  });
}
test('PC six-photo layout and original desktop titles preserved',async({page})=>{
  await page.setViewportSize({width:1440,height:900});
  await page.goto(url,{waitUntil:'networkidle'});
  const v=await page.locator('.g1-detail-gallery').evaluate(s=>({
    height:s.getBoundingClientRect().height,
    cards:[...s.querySelectorAll('.g1-detail-item')].map(c=>({
      title:c.querySelector('h3 .g1-pc-only').textContent.trim(),
      height:c.getBoundingClientRect().height
    }))
  }));
  expect(Math.abs(v.height-759)).toBeLessThanOrEqual(1);
  expect(v.cards).toHaveLength(6);
  expect(v.cards.every(c=>c.height===241)).toBe(true);
  expect(v.cards[0].title).toBe('力を制御する3指ハンド');
  expect(v.cards[5].title).toBe('3D LiDAR＋深度カメラ');
});

// Figma PC gallery 150:2 pixel geometry after gap correction.
// PC exact original frame 1440x759, cards y198/458 and note y716.
// Previously approved SP 150:31 stays 1113px with six correct original images.
test('Figma PC gallery 150:2 pixel geometry after gap correction',async({page})=>{
  await page.setViewportSize({width:1440,height:900});
  await page.goto(url,{waitUntil:'networkidle'});
  const a=await page.locator('.g1-detail-gallery').evaluate(sec=>{
    const base=sec.getBoundingClientRect();
    const rect=el=>{const r=el.getBoundingClientRect();return{x:Math.round(r.x-base.x),y:Math.round(r.y-base.y),w:Math.round(r.width),h:Math.round(r.height)}};
    return {section:rect(sec),kicker:rect(sec.querySelector('.g1-heading .g1-kicker')),
      title:rect(sec.querySelector('h2')),intro:rect(sec.querySelector('.g1-heading .g1-intro')),
      grid:rect(sec.querySelector('.g1-detail-grid')),note:rect(sec.querySelector('.g1-shell>.g1-fine')),
      cards:[...sec.querySelectorAll('.g1-detail-item')].map(c=>({card:rect(c),image:rect(c.querySelector('.g1-detail-image'))})),
      sources:[...sec.querySelectorAll('img')].map(x=>x.getAttribute('src'))
    };
  });
  expect(a.section.h).toBe(759);
  expect(a.kicker.y).toBe(35);
  expect(a.title.y).toBe(76);
  expect(a.intro.y).toBe(134);
  expect(a.grid.y).toBe(198);
  expect(a.grid.h).toBe(501);
  expect(a.note.y).toBe(716);
  expect(a.note.h).toBe(19);
  expect(a.cards.map(x=>x.card.y)).toEqual([198,198,198,458,458,458]);
  expect(a.cards.every(x=>x.card.h===241)).toBe(true);
  expect(a.sources).toHaveLength(6);
});

// Figma original PC Hero y-coordinates: node 11:28, 1440x555.
// Preserve manufacturer video in-page playback and fallback link,
// rather than removing valid business text to force the Figma screenshot.
test('Figma original PC Hero y-coordinates',async({page})=>{
  await page.setViewportSize({width:1440,height:900});
  await page.goto(url,{waitUntil:'networkidle'});
  const a=await page.locator('.g1-hero').evaluate(section=>{
    const r=section.getBoundingClientRect();
    const coord=q=>{const e=section.querySelector(q),b=e.getBoundingClientRect();
      return {y:Math.round(b.top-r.top),x:Math.round(b.left-r.left),h:Math.round(b.height)}};
    return {
      hero:coord('.g1-shell'),
      height:Math.round(r.height),
      eyebrow:coord('.g1-hero-copy>.g1-kicker'),
      title:coord('#g1-title'),
      lead:coord('.g1-hero-lead'),
      description:coord('.g1-hero-description'),
      actions:coord('.g1-hero-ctas'),
      note:coord('.g1-hero-note'),
      video:coord('.g1-hero-video'),
      externalFallback:!!section.querySelector('.g1-image-caption a[href*="youtube.com"]')
    };
  });
  expect(a.height).toBe(555);
  expect(a.eyebrow).toMatchObject({x:120,y:101});
  expect(a.title).toMatchObject({x:120,y:136});
  expect(Math.abs(a.lead.y-202)).toBeLessThanOrEqual(1);
  expect(a.description).toMatchObject({x:120,y:312});
  expect(a.actions).toMatchObject({x:120,y:414,h:50});
  expect(a.note).toMatchObject({x:120,y:482});
  expect(a.video).toMatchObject({x:720,y:86,h:400});
  expect(a.externalFallback).toBe(true);
});
for (const width of [1024,390]){
  test('PC Hero CSS adjustment does not affect '+width+'px layout',async({page})=>{
    await page.setViewportSize({width,height:900});
    await page.goto(url,{waitUntil:'networkidle'});
    const a=await page.locator('.g1-hero').evaluate(e=>({
      h:Math.round(e.getBoundingClientRect().height),
      titleY:Math.round(e.querySelector('#g1-title').getBoundingClientRect().top-e.getBoundingClientRect().top),
      overflow:document.documentElement.scrollWidth>innerWidth+1
    }));
    expect(Math.abs(a.h-(width===1024?532:696))).toBeLessThanOrEqual(2);
    expect(a.titleY).toBe(width===1024?121:79);
    expect(a.overflow).toBe(false);
  });
}

// Figma PC Research 11:65 exact section geometry 1440x485;
// retain research examples, PC typography and previously approved SP.
test('Figma PC Research 11:65 exact section geometry',async({page})=>{
  await page.setViewportSize({width:1440,height:900});
  await page.goto(url,{waitUntil:'networkidle'});
  const a=await page.locator('#research').evaluate(el=>{
    const b=el.getBoundingClientRect(),rect=q=>{const r=el.querySelector(q).getBoundingClientRect();
      return{y:Math.round(r.y-b.y),height:Math.round(r.height)}};
    return{height:Math.round(b.height),kicker:rect('.g1-heading .g1-kicker'),
      headline:rect('h2'),intro:rect('.g1-heading .g1-intro'),
      first:rect('.g1-use-list article'),note:rect('.g1-shell>.g1-fine'),
      cards:el.querySelectorAll('.g1-use-list article').length};
  });
  expect(a.height).toBe(485);
  expect(a.kicker.y).toBe(48);
  expect(a.headline.y).toBe(89);
  expect(a.intro.y).toBe(155);
  expect(a.first).toMatchObject({y:203,height:178});
  expect(a.note.y).toBe(403);
  expect(a.cards).toBe(3);
});
for(const width of [1024,390]){
  test('Figma PC research refinement does not alter '+width+'px',async({page})=>{
    await page.setViewportSize({width,height:900});
    await page.goto(url,{waitUntil:'networkidle'});
    const a=await page.locator('#research').evaluate(e=>({
      height:Math.round(e.getBoundingClientRect().height),
      title:parseFloat(getComputedStyle(e.querySelector('h2')).fontSize),
      overflow:document.documentElement.scrollWidth>innerWidth+1}));
    expect(a.height).toBe(width===1024?462:845);
    expect(a.title).toBe(width===1024?30:24);
    expect(a.overflow).toBe(false);
  });
}
