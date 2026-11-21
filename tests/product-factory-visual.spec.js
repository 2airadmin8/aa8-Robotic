const { test, expect } = require('@playwright/test');
const base = process.env.AA8_TEST_BASE || 'http://127.0.0.1:4173';
const product = '/products/factory-qa.html';
for (const width of [1440, 390, 360]) {
  test('generated G1 factory / real browser / '+width+'px', async ({ page }) => {
    await page.setViewportSize({width, height: 900});
    const failed = [];
    page.on('pageerror', error => failed.push('pageerror ' + error.message));
    page.on('response', response => {
      if (response.url().startsWith(base) && response.status() >= 400)
        failed.push(response.status() + ' ' + response.url());
    });
    const r = await page.goto(base + product, {waitUntil:'networkidle'});
    expect(r.status()).toBe(200);
    await expect(page.locator('main.g1-page[data-product-factory="g1-v1"]')).toBeVisible();
    await expect(page.locator('.site-header[data-shared-layout="header"]')).toHaveCount(1);
    await expect(page.locator('footer[data-shared-layout="footer"]')).toHaveCount(1);
    await expect(page.locator('h1')).toHaveText('QA Fixture Robot');
    await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', 'noindex,nofollow');
    await expect(page.locator('.g1-cta-grid .g1-cta-card')).toHaveCount(3);
    await expect(page.locator('#specifications tbody tr')).toHaveCount(3);
    await expect(page.locator('.g1-faq-list details')).toHaveCount(3);
    await page.locator('.g1-cta-grid').scrollIntoViewIfNeeded();
    // Images are loading=lazy. Scrolling reveals them asynchronously;
    // enforce real decoded images rather than testing before the request finishes.
    await expect.poll(() => page.locator('.g1-cta-grid .g1-cta-card img')
      .evaluateAll(imgs => imgs.length === 3 &&
        imgs.every(img => img.complete && img.naturalWidth > 100)),
      { timeout: 15000 }).toBeTruthy();
    const m = await page.evaluate(() => {
      const main = document.querySelector('main.g1-page');
      const hero = main.querySelector('.g1-hero');
      const sections = [...main.querySelectorAll(':scope > .g1-section:not(.g1-final-cta)')];
      const cta = main.querySelector('.g1-final-cta');
      const imgs = [...cta.querySelectorAll('.g1-cta-card img')];
      return {
        hero: getComputedStyle(hero).backgroundColor,
        sections: sections.map(n => getComputedStyle(n).backgroundColor),
        cta: getComputedStyle(cta).backgroundImage,
        photos: imgs.map(n => ({complete:n.complete,width:n.naturalWidth})),
        overflow: document.documentElement.scrollWidth-innerWidth,
        columns: getComputedStyle(cta.querySelector('.g1-cta-grid')).gridTemplateColumns.split(' ').length,
      };
    });
    expect(m.hero).toBe('rgb(255, 255, 255)');
    expect(m.sections.length).toBeGreaterThanOrEqual(5);
    expect(m.sections.every(color => color === 'rgb(255, 255, 255)')).toBeTruthy();
    expect(m.cta).toContain('g1-cta-figma-pc.png');
    expect(m.photos).toHaveLength(3);
    expect(m.photos.every(x => x.complete && x.width > 100)).toBeTruthy();
    expect(m.overflow).toBeLessThanOrEqual(1);
    expect(m.columns).toBe(width <= 780 ? 1 : 3);
    await page.locator('.g1-cta-grid .g1-cta-card').nth(2).click();
    await expect(page).toHaveURL(/\/contact\.html\?product=QA%20Fixture%20Robot/);
    // Wait for deferred contact-v2.js prefill after cross-page navigation.
    await page.waitForLoadState('domcontentloaded');
    await expect(page.locator('input[name="product"]')).toHaveValue('QA Fixture Robot');
    expect(failed).toEqual([]);
  });
}


// AA8 STRICT new quadruped buyer/visual contract.
// These constraints deliberately fail on old "200 + images + no overflow"
// previews. Reuse this CI-listed Playwright spec; no second QA framework.
for (const width of [1440,390,360]) {
  test('AA8 STRICT new quadruped buyer/visual contract / '+width+'px', async ({page}) => {
    await page.setViewportSize({width,height:900});
    const bad=[];
    page.on('pageerror',e=>bad.push('JS '+e.message));
    page.on('response',r=>{
      if(r.url().startsWith(base)&&r.status()>=400) bad.push(r.status()+' '+r.url());
    });
    const response=await page.goto(base+'/unitree-b2-new-real-pilot-preview.html',
                                    {waitUntil:'domcontentloaded',timeout:30000});
    expect(response.status()).toBe(200);
    await expect(page.locator('body.aa8-corporate-v1')).toHaveCount(1);
    const main=page.locator('main.g1-page[data-product-id="unitree-b2"]'
                          +'[data-page-design-v33="strict"][data-aa8-visual-version="3.3"]');
    await expect(main).toHaveCount(1);
    await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content','noindex,nofollow');
    await expect(page.locator('header.site-header')).toHaveCount(1);
    await expect(page.locator('footer.footer')).toHaveCount(1);
    const roles=['capabilities','applications','decision-checks','media','specifications',
                 'development','solutions','introduction','faq','related','contact-product'];
    for(const id of roles) await expect(main.locator('#'+id)).toHaveCount(1);
    const count=async (css,n)=>expect(await main.locator(css).count()).toBe(n);
    await count('#capabilities .g1-factory-facts article',4);
    await count('#applications .g1-factory-applications article',2);
    await count('#decision-checks .g1-factory-decision-grid article',5);
    await count('#media .g1-factory-media-grid img',4);
    await count('#media video',1);
    await count('#specifications .g1-factory-spec-table thead th',2);
    await count('#specifications .g1-factory-spec-table tbody tr',19);
    await count('#specifications .g1-factory-spec-table tbody a',0);
    await count('#development .g1-factory-applications article',3);
    await count('#solutions .g1-factory-applications article',3);
    await count('#introduction .g1-factory-applications article',5);
    await count('#faq details',3);
    await count('#related .g1-factory-related-card',1);
    await count('#contact-product .g1-cta-card',3);
    await expect(main.locator('.g1-hero-ctas a').first()).toHaveAttribute('href',/contact\.html\?/);
    await expect(main.locator('.g1-anchor-nav a[href="#decision-checks"]')).toHaveCount(1);
    await expect(main.locator('#decision-checks')).toContainText('積載・機体構成');
    await expect(main.locator('#decision-checks')).toContainText('安全・運用責任');
    await expect(main.locator('.g1-hero-lead')).not.toContainText('非公開プレビュー');
    await expect(main.locator('#related')).not.toContainText('Unitree H2-D');
    await expect(main.locator('#contact-product .g1-cta-card').first()).toHaveAttribute('href','#media');
    await page.evaluate(async()=>{
      for(const img of document.images) img.loading='eager';
      await Promise.all([...document.images].map(img=>img.decode().catch(()=>null)));
    });
    const metric=await page.evaluate(()=>{
      const qs=(s)=>document.querySelector(s);
      const rgba=(n)=>getComputedStyle(n).backgroundColor;
      const style=(n)=>getComputedStyle(n);
      const main=qs('main[data-page-design-v33="strict"]');
      const roles=[...main.querySelectorAll(':scope > section.g1-section')];
      const spec=qs('#specifications .g1-factory-spec-table');
      return {
        heroHeight:qs('main > .g1-hero').getBoundingClientRect().height,
        sectionPadding:parseFloat(style(qs('#capabilities')).paddingTop),
        gridColumns: {
          features:style(qs('#capabilities .g1-factory-facts')).gridTemplateColumns.split(' ').length,
          applications:style(qs('#applications .g1-factory-applications')).gridTemplateColumns.split(' ').length,
          media:style(qs('#media .g1-factory-media-grid')).gridTemplateColumns.split(' ').length,
          decisions:style(qs('#decision-checks .g1-factory-decision-grid')).gridTemplateColumns.split(' ').length,
          sdk:style(qs('#development .g1-factory-applications')).gridTemplateColumns.split(' ').length,
        },
        heroBG:rgba(qs('main > .g1-hero')),
        specBG:rgba(qs('#specifications')),
        specHeaderBG:rgba(spec.querySelector('thead tr')),
        specOddBG:rgba(spec.querySelector('tbody tr:nth-child(1)')),
        specEvenBG:rgba(spec.querySelector('tbody tr:nth-child(2)')),
        fontFamily:style(qs('main h1')).fontFamily,
        leakedTracking:!!document.querySelector('script[src*="googletagmanager"],script[src*="analytics-events"]'),
        overflow:document.documentElement.scrollWidth-document.documentElement.clientWidth,
        badImages:[...document.images].filter(x=>!x.complete||x.naturalWidth<=0).map(x=>x.getAttribute('src')),
        allMediaSrc:[...document.querySelectorAll('#media video source')].map(s=>s.getAttribute('src')),
        sectionIds:roles.map(r=>r.id).filter(Boolean),
      };
    });
    expect(metric.heroHeight).toBeLessThan(width===1440?740:850);
    expect(metric.gridColumns).toEqual(
      Object.fromEntries(['features','applications','media','decisions','sdk']
        .map(key=>[key,width===1440?2:1]))
    );
    expect(metric.sectionPadding).toBeGreaterThan(26);
    expect(metric.sectionPadding).toBeLessThanOrEqual(width===1440?60:42);
    expect(metric.heroBG).toBe('rgb(255, 255, 255)');
    expect(metric.specBG).toBe('rgb(255, 255, 255)');
    expect(metric.specHeaderBG).toBe('rgb(255, 255, 255)');
    expect(metric.specOddBG).toBe('rgb(255, 255, 255)');
    expect(metric.specEvenBG).toBe('rgb(245, 245, 245)');
    expect(metric.fontFamily).toContain('Noto Sans JP');
    expect(metric.overflow).toBeLessThanOrEqual(1);
    expect(metric.badImages).toEqual([]);
    expect(metric.leakedTracking).toBe(false);
    expect(metric.allMediaSrc).toHaveLength(1);
    expect(metric.sectionIds).toEqual(['capabilities','applications','decision-checks','media',
      'specifications','development','solutions','introduction','faq','related','contact-product']);
    // Real anchor click after smooth scrolling must not hide headings behind sticky nav.
    for(const target of ['#decision-checks','#specifications','#development']){
      await page.locator('.g1-anchor-nav a[href="'+target+'"]').click();
      await expect.poll(async()=>page.locator(target).evaluate(el=>{
        const top=el.getBoundingClientRect().top;
        const margin=parseFloat(getComputedStyle(el).scrollMarginTop);
        return Math.abs(top-margin);
      }),{timeout:6500,intervals:[100,200,350,550]}).toBeLessThanOrEqual(3);
      const layout=await page.evaluate(target=>{
        const rect=s=>document.querySelector(s).getBoundingClientRect();
        return {headingTop:rect(target+' h2').top,
                headerBottom:rect('header.site-header').bottom,
                navBottom:rect('nav.g1-anchor-nav').bottom};
      },target);
      expect(layout.headingTop).toBeGreaterThan(layout.headerBottom+10);
      expect(layout.headingTop).toBeGreaterThan(layout.navBottom+10);
    }
    expect(bad).toEqual([]);
  });
}
