// 2026-10-30 user screenshot regression: research themes and product listing.
// Requires only real browser navigation; no mocks, no writes to business systems.
const {test,expect}=require('@playwright/test');
const base=(process.env.HUB_QA_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const target=(path)=>base+'/'+path.replace(/^\//,'');
const sizes=[{width:1440,height:900},{width:390,height:844}];

for(const viewport of sizes){
  test('shared brand Logo navigates to actual homepage / '+viewport.width,async({page})=>{
    await page.setViewportSize(viewport);
    for(const relative of ['products.html','use-cases.html','products/unitree-g1.html']){
      await page.goto(target(relative),{waitUntil:'networkidle'});
      const logo=page.locator('header.site-header a.brand');
      await expect(logo).toBeVisible();
      const href=await logo.getAttribute('href');
      expect(href).toMatch(/^(?:\.\.\/)*index\.html$/);
      const resolved=new URL(href,page.url());
      expect(resolved.pathname).toBe('/index.html');
      await logo.click();
      await expect(page).toHaveURL(/\/index\.html(?:\?.*)?$/);
      await expect(page.locator('main h1').first()).toBeVisible();
    }
  });

  test('research-use-cases title and dark CTA are legible / '+viewport.width,async({page})=>{
    await page.setViewportSize(viewport);
    const res=await page.goto(target('use-cases.html'),{waitUntil:'networkidle'});
    expect(res.status()).toBe(200);
    const raw=await (await page.request.get(target('use-cases.html'))).text();
    expect(raw).toContain('<h1>研究目的から、<br>必要な構成を整理する</h1>');
    const details=await page.evaluate(()=>{
      const css=s=>getComputedStyle(document.querySelector(s));
      const height=s=>document.querySelector(s).getBoundingClientRect().height;
      const dark=css('.compact-dark-cta h2'),main=css('.hub-hero h1');
      const heads=[...document.querySelectorAll('main .section-heading h2')];
      const themes=document.querySelector('#themes'),next=themes.nextElementSibling;
      return {h1:document.querySelector('.hub-hero h1').textContent.trim(),h1Size:parseFloat(main.fontSize),
        headingSizes:heads.map(x=>parseFloat(getComputedStyle(x).fontSize)),
        headingNames:heads.map(x=>x.textContent.trim()),
        darkSize:parseFloat(dark.fontSize),darkColor:dark.color,darkText:document.querySelector('.compact-dark-cta h2').textContent.trim(),
        themeBottom:parseFloat(getComputedStyle(themes).paddingBottom),
        nextTop:parseFloat(getComputedStyle(next).paddingTop),
        themeCards:document.querySelectorAll('.theme-card').length,logicSteps:document.querySelectorAll('.logic-flow article').length,
        overflow:document.documentElement.scrollWidth-innerWidth};
    });
    expect(details.h1).toBe('研究目的から、必要な構成を整理する');
    expect(details.h1Size).toBeLessThanOrEqual(viewport.width>640?50.1:33.1);
    expect(details.headingSizes.every(size=>size<=(viewport.width>640?38.1:27.1))).toBe(true);
    expect(details.headingNames.every(name=>!name.endsWith('。'))).toBe(true);
    expect(details.darkColor).toBe('rgb(255, 255, 255)');
    expect(details.darkSize).toBeLessThanOrEqual(viewport.width>640?38.1:28.1);
    expect(details.darkText.endsWith('。')).toBe(false);
    expect(details.themeBottom).toBeLessThanOrEqual(viewport.width>640?42:32);
    expect(details.nextTop).toBeLessThanOrEqual(viewport.width>640?45:36);
    expect(details.themeCards).toBe(6);
    expect(details.logicSteps).toBe(4);
    expect(details.overflow).toBeLessThanOrEqual(1);
  });

  test('product categories compact, headings readable and controls intact / '+viewport.width,async({page})=>{
    await page.setViewportSize(viewport);
    const res=await page.goto(target('products.html'),{waitUntil:'networkidle'});
    expect(res.status()).toBe(200);
    const m=await page.evaluate(()=>{
      const hero=document.querySelector('.product-page-hero');
      const cards=[...document.querySelectorAll('.priority-category')];
      const size=x=>parseFloat(getComputedStyle(x).fontSize);
      const head=[...document.querySelectorAll('main .section-heading h2')];
      const dark=document.querySelector('.compact-dark-cta h2'),darkCSS=getComputedStyle(dark);
      const rect=cards.map(c=>{const r=c.getBoundingClientRect(),h=c.querySelector('h3').getBoundingClientRect();return{h:r.height,titleY:h.y-r.y}});
      return {heroTop:parseFloat(getComputedStyle(hero).paddingTop),headings:head.map(x=>({text:x.textContent.trim(),size:size(x)})),
        cards:rect,categoryLinks:cards.map(c=>c.getAttribute('href')),
        darkColor:darkCSS.color,darkSize:parseFloat(darkCSS.fontSize),darkText:dark.textContent.trim(),
        catalogCards:document.querySelectorAll('[data-product-list] .research-product-card').length,
        productFilters:document.querySelectorAll('.product-filter button').length,
        overflow:document.documentElement.scrollWidth-innerWidth};
    });
    expect(m.heroTop).toBeLessThanOrEqual(viewport.width>640?42:34);
    expect(m.headings.length).toBeGreaterThanOrEqual(5);
    expect(m.headings.every(x=>x.size<=(viewport.width>640?38.1:27.1)&&!x.text.endsWith('。'))).toBe(true);
    expect(m.cards).toHaveLength(4);
    expect(m.cards[0].h).toBeLessThanOrEqual(viewport.width>640?390:255);
    expect(m.cards[0].titleY).toBeLessThanOrEqual(viewport.width>640?165:100);
    expect(m.cards.slice(1).every(c=>c.h<=(viewport.width>640?190:180))).toBe(true);
    expect(m.categoryLinks.every(h=>h.includes('filter=')&&h.includes('#lineup'))).toBe(true);
    expect(m.darkColor).toBe('rgb(255, 255, 255)');
    expect(m.darkSize).toBeLessThanOrEqual(viewport.width>640?38.1:28.1);
    expect(m.darkText.endsWith('。')).toBe(false);
    expect(m.catalogCards).toBeGreaterThanOrEqual(6);
    expect(m.productFilters).toBeGreaterThanOrEqual(6);
    expect(m.overflow).toBeLessThanOrEqual(1);
  });
}
