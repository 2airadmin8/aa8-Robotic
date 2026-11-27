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
    // Data-backed cards render asynchronously after the document. A zero-card
    // result is still a failure after a bounded wait, never accepted as PASS.
    await expect.poll(async()=>page.locator('[data-product-list] .research-product-card').count(),
      {timeout:15000,intervals:[150,300,700,1200]}).toBeGreaterThanOrEqual(6);
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


// V15｜CEO annotated multi-page visual regression, 2026-10-30.
// No real business form submission, no GA/CRM writes; checks the actual UI.
const v15Base=(process.env.V15_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const v15Pages=[
 {path:'index.html',marker:'.hero-grid-v2',sections:10,heroPc:700,heroSp:940,hasDark:true,
  headings:['AIロボット導入までの流れ','研究テーマ・現場用途からAIロボットを探す',
   'AIロボットの代表製品','選定から運用までの導入支援',
   'AIロボット導入支援の実績',
   'SDK・ROS・VLAの技術資料','よくある質問',
   'AIロボットの製品が未定でも相談できます']},
 {path:'cases.html',marker:'.case-proof-card',sections:6,heroPc:570,heroSp:960,hasDark:true,
  headings:['ページ内の情報を4段階で表示','AIロボット導入支援事例','標準支援例',
   '事例ページで確認できること','似た条件から、必要な工程を整理します']},
 {path:'resources.html',marker:'.resource-hero',sections:6,heroPc:510,heroSp:890,hasDark:true,
  headings:['見積前に、導入条件を一枚で整理','目的から公式資料へ',
   '公式入口と公開状況を絞り込む','公開コードがあっても、導入可否は別問題',
   'SDKの有無ではなく、研究に使えるかを確認']},
 {path:'support.html',marker:'.service-module-grid',sections:7,heroPc:570,heroSp:980,hasDark:true,
  headings:['ロボット導入に必要な工程を分けて支援','相談から運用までの標準工程',
   'ロボットPoCで先に決めること','誰がどこまで責任を持つか',
   '本体、PoC、開発、保守を分けて見積します']},
 {path:'contact.html',marker:'.contact-hero',sections:2,heroPc:430,heroSp:710,hasDark:false,
  headings:[]},
];
for(const width of [1440,390]){
 for(const def of v15Pages){
  test('V15 screenshot visual+logo+CTA '+def.path+' '+width,async({page})=>{
   await page.setViewportSize({width,height:900});
   const errors=[];page.on('pageerror',e=>errors.push(String(e)));
   const response=await page.goto(v15Base+'/'+def.path,{waitUntil:'networkidle'});
   expect(response.status()).toBe(200);
   await expect(page.locator('main '+def.marker).first()).toBeVisible();
   await page.evaluate(async()=>{
    document.querySelectorAll('main img').forEach(i=>i.loading='eager');
    await document.fonts.ready;
    await Promise.all([...document.querySelectorAll('main img')].map(i=>i.decode().catch(()=>{})));
   });
   const m=await page.evaluate(()=>{
    const f=(selector)=>document.querySelector(selector);
    const font=(e)=>parseFloat(getComputedStyle(e).fontSize);
    const hh=(e)=>e.getBoundingClientRect().height;
    const sec=[...document.querySelectorAll('main > section')];
    const h1=f('main h1');
    const dark=f('main > section.dark h2');
    const headings=[...document.querySelectorAll('main > section.section .section-heading h2, main > section.section .contact-panel h2, main > section.section .contact-panel-dark h2, main > section.section .resource-cta-grid h2')];
    const brand=f('header.site-header a.brand');
    const blocks=sec.filter(e=>e.classList.contains('section'));
    return {h1Count:document.querySelectorAll('main h1').length,h1Size:font(h1),h1Text:h1.textContent.trim(),
      heroHeight:hh(sec[0]),sections:sec.length,
      headingNames:headings.map(e=>e.textContent.trim()),headingSizes:headings.map(font),
      darkColor:dark?getComputedStyle(dark).color:null,darkSize:dark?font(dark):null,
      darkCaseColor:f('.case-feature h3')?getComputedStyle(f('.case-feature h3')).color:null,
      logoHref:brand.getAttribute('href'),overflow:document.documentElement.scrollWidth-innerWidth,
      broken:[...document.querySelectorAll('main img')].filter(i=>!i.complete||!i.naturalWidth).length,
      sectionPadding:blocks.map(e=>({top:parseFloat(getComputedStyle(e).paddingTop),bottom:parseFloat(getComputedStyle(e).paddingBottom)})),
      casesAxis:f('.comparison-axis-grid')?getComputedStyle(f('.comparison-axis-grid')).gridTemplateColumns.trim().split(/\s+/).length:null,
      casesAxisCount:document.querySelectorAll('.comparison-axis-grid article').length,
      resourceCount:document.querySelectorAll('.resource-card').length,
      servicesCount:document.querySelectorAll('.service-module-grid article').length,
      contactForm:!!f('[data-contact-form]'),
      canonical:f('link[rel="canonical"]')?.href
    };
   });
   expect(m.h1Count).toBe(1);
   expect(m.h1Size).toBeLessThanOrEqual(width===1440?50.1:33.1);
   expect(m.heroHeight).toBeLessThanOrEqual(width===1440?def.heroPc:def.heroSp);
   expect(m.sections).toBe(def.sections);
   for(const name of def.headings) {
    expect(m.headingNames, name).toContain(name);
    expect(name.endsWith('。')).toBe(false);
   }
   if(def.path!=='contact.html'){
    expect(m.headingSizes.every(z=>z<=(width===1440?38.1:27.1))).toBe(true);
    expect(m.sectionPadding.filter(x=>x.top>49||x.bottom>49).length).toBe(0);
   }else{
    expect(m.contactForm).toBe(true);
    const formTitle=await page.locator('#contact-form-title').evaluate(el=>parseFloat(getComputedStyle(el).fontSize));
    expect(formTitle).toBeLessThanOrEqual(width===1440?36.1:29.1);
   }
   if(def.hasDark){
    expect(m.darkColor).toBe(def.path==='index.html'?'rgb(23, 51, 66)':'rgb(255, 255, 255)');
    expect(m.darkSize).toBeLessThanOrEqual(width===1440?38.1:27.1);
   }
   if(def.path==='index.html')expect(m.darkCaseColor).toBe('rgb(23, 51, 66)');
   if(def.path==='cases.html'){
    expect(m.casesAxisCount).toBe(4);
    expect(m.casesAxis).toBe(width===1440?4:1);
   }
   if(def.path==='resources.html')expect(m.resourceCount).toBeGreaterThanOrEqual(15);
   if(def.path==='support.html')expect(m.servicesCount).toBe(6);
   expect(m.canonical).toBe('https://robotics.air-admin8.co.jp/'+(def.path==='index.html'?'':def.path));
   expect(m.overflow).toBeLessThanOrEqual(1);
   expect(m.broken).toBe(0);
   expect(errors).toEqual([]);
   expect(m.logoHref).toMatch(/^(?:\.\.\/)*index\.html$/);
   await page.locator('header.site-header a.brand').click();
   await expect(page).toHaveURL(/\/index\.html(?:\?.*)?$/);
  });
 }
}

// Issue #200: CEO annotated home screenshot regression, read-only browser checks.
for (const width of [1440, 1280, 390, 360]) {
  test('HOME #200 cards, links and accessible case CTA / '+width, async ({page}) => {
    await page.setViewportSize({width,height:900});
    const response=await page.goto(base+'/index.html',{waitUntil:'networkidle'});
    expect(response.status()).toBe(200);
    const cards=page.locator('.home-product-grid .research-product-card');
    await expect(cards).toHaveCount(3);
    await expect(page.locator('.hero-trust-note')).toHaveCount(0);
    await expect(page.locator('.home-process article')).toHaveCount(4);
    // MARK-02–04: each category must retain its own filter and anchor.
    const categoryLinks = page.locator('.category-lineup figcaption a');
    await expect(categoryLinks).toHaveCount(3);
    for (const [index, filter] of ['humanoid', 'quadruped', 'arm'].entries()) {
      const link = categoryLinks.nth(index);
      await expect(link).toBeVisible();
      await expect(link).toHaveAttribute('href', 'products.html?filter=' + filter + '#lineup');
    }
    // MARK-05/06/23/25/30/31: preserve the approved redline resolution.
    // Update expectations together with any separately approved future copy.
    const sectionHeading = marker => page.locator('main .section-heading').filter({
      has: page.getByText(marker, {exact: true})
    });
    for (const [marker, text] of [
      ['IMPLEMENTATION PROCESS', 'AIロボット導入までの流れ'],
      ['ROBOT COMPARISON', 'AIロボットの代表製品'],
      ['SUPPORT MENU', '選定から運用までの導入支援'],
      ['CASE & EVIDENCE', 'AIロボット導入支援の実績'],
      ['TECHNICAL RESOURCES', 'SDK・ROS・VLAの技術資料'],
      ['FAQ', 'よくある質問']
    ]) {
      const title = sectionHeading(marker).getByRole('heading', {level: 2});
      await expect(title).toBeVisible();
      await expect(title).toHaveText(text);
    }
    // MARK-24: no redundant heading link, and all three distinct service links remain.
    const supportHeading = sectionHeading('SUPPORT MENU');
    await expect(supportHeading.locator('a')).toHaveCount(0);
    const supportSection = supportHeading.locator('xpath=ancestor::section[1]');
    await expect(supportSection.locator('a')).toHaveCount(3);
    const serviceLinks = supportSection.locator('a.service-card');
    await expect(serviceLinks).toHaveCount(3);
    for (const [index, path] of [
      'support/university-procurement.html', 'support.html#poc', 'use-cases/vla-data-collection.html'
    ].entries()) {
      await expect(serviceLinks.nth(index)).toHaveAttribute('href', path);
    }
    // MARK-07: the featured G1-D entry must be one visible, working detail link.
    const feature = page.locator('.g1d-detail-entry');
    await expect(feature).toHaveCount(1);
    const featureLink = page.locator('a.g1d-detail-entry, .g1d-detail-entry a');
    await expect(featureLink).toBeVisible();
    await expect(featureLink).toHaveAttribute('href', 'products/unitree-g1-d.html');
    // MARK-15: exactly one visible G1 summary and no repeated sentence inside it.
    const g1Summary = page.locator('.home-product-grid #unitree-g1 .product-summary');
    await expect(g1Summary).toHaveCount(1);
    await expect(g1Summary).toBeVisible();
    const g1Sentences = (await g1Summary.innerText()).split('。').map(s => s.trim()).filter(Boolean);
    expect(g1Sentences.length).toBeGreaterThan(0);
    expect(new Set(g1Sentences).size).toBe(g1Sentences.length);
    await expect(page.locator('.case-feature .text-link')).toBeVisible();
    const details=await page.evaluate(()=>{
      const cards=[...document.querySelectorAll('.home-product-grid .research-product-card')];
      const links=[...document.querySelectorAll('.category-lineup figcaption a')];
      const cta=document.querySelector('.case-feature .text-link');
      const style=getComputedStyle(cta);
      const rgb=(c)=>c.match(/\d+/g).slice(0,3).map(Number);
      const luminance=(c)=>rgb(c).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4})
        .reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
      const a=luminance(style.color),b=luminance(style.backgroundColor);
      const contrast=(Math.max(a,b)+.05)/(Math.min(a,b)+.05);
      return {
        ids:cards.map(x=>x.id),
        details:cards.map(x=>x.querySelector('.product-link')?.getAttribute('href')),
        visiblePrimary:cards.every(x=>getComputedStyle(x.querySelector('.product-link')).display!=='none'),
        invisibleDuplicate:cards.every(x=>getComputedStyle(x.querySelector('.product-consult-link')).display==='none'),
        invisiblePills:cards.every(x=>getComputedStyle(x.querySelector('.product-condition-meta')).display==='none'),
        makerCount:cards.map(x=>x.querySelectorAll('.product-maker').length),
        makerBadges:cards.map(x=>x.querySelector('.product-visual .home-product-maker')?.textContent.trim()),
        makerBadgePlacement:cards.every(x=>{
          const image=x.querySelector('.product-visual').getBoundingClientRect();
          const maker=x.querySelector('.home-product-maker').getBoundingClientRect();
          return maker.left>=image.left+image.width*.45 && maker.right<=image.right+1
            && maker.top>=image.top && maker.bottom<=image.top+65;
        }),
        bodyMakerHidden:cards.every(x=>getComputedStyle(x.querySelector('.product-maker')).display==='none'),
        noCategoryDuplicate:cards.every(x=>!x.querySelector('.product-category-label')),
        introAllVisible:cards.every(x=>{
          const summary=x.querySelector('.product-summary');
          const style=getComputedStyle(summary);
          return style.overflow==='visible' && style.webkitLineClamp==='none'
            && summary.scrollWidth<=summary.clientWidth+1
            && summary.scrollHeight<=summary.clientHeight+1;
        }),
        caseContrast:contrast,
        caseUrl:cta.getAttribute('href'),
        categoryAllInViewport:links.every(x=>{const r=x.getBoundingClientRect();return r.width>0&&r.left>=0&&r.right<=innerWidth+1;}),
        overflow:document.documentElement.scrollWidth-innerWidth
      };
    });
    expect(details.ids).toEqual(['unitree-g1-d','agibot-g2','unitree-g1']);
    expect(details.details).toEqual([
      'products/unitree-g1-d.html','products/agibot-g2.html','products/unitree-g1.html'
    ]);
    expect(details.visiblePrimary).toBe(true);
    expect(details.invisibleDuplicate).toBe(true);
    expect(details.invisiblePills).toBe(true);
    expect(details.noCategoryDuplicate).toBe(true);
    expect(details.makerCount).toEqual([1,1,1]);
    expect(details.makerBadges).toEqual(['Unitree','AgiBot','Unitree']);
    expect(details.makerBadgePlacement).toBe(true);
    expect(details.bodyMakerHidden).toBe(true);
    expect(details.introAllVisible).toBe(true);
    expect(details.caseContrast).toBeGreaterThanOrEqual(4.5);
    expect(details.caseUrl).toBe('cases/keio-selection.html');
    expect(details.categoryAllInViewport).toBe(true);
    expect(details.overflow).toBeLessThanOrEqual(1);
  });
}

for (const width of [360, 390]) {
  test('HOME #200 MARK-14 long model and SDK tokens wrap / '+width, async ({page}) => {
    await page.setViewportSize({width,height:900});
    const response=await page.goto(base+'/index.html');
    expect(response.status()).toBe(200);
    const summaries=page.locator('.home-product-grid .research-product-card .product-summary');
    await expect(summaries).toHaveCount(3);
    const results=await summaries.evaluateAll(elements=>{
      const tokens=[
        'AA8ModelIdentifier'.repeat(6),
        'SDK_API_BINDING_'.repeat(7),
        'ROBOTICS_CONTROLLER_INTERFACE_'.repeat(4)
      ];
      function measure(summary) {
        const range=document.createRange();
        range.selectNodeContents(summary);
        const rects=[...range.getClientRects()];
        const box=summary.getBoundingClientRect();
        const card=summary.closest('.research-product-card').getBoundingClientRect();
        const style=getComputedStyle(summary);
        return {
          card:summary.closest('.research-product-card').id,
          lines:rects.length,
          excess:Math.max(0,...rects.map(r=>Math.max(box.left-r.left,r.right-box.right,card.left-r.left,r.right-card.right))),
          bottomExcess:Math.max(0,...rects.map(r=>r.bottom-box.bottom)),
          widthOverflow:summary.scrollWidth-summary.clientWidth,
          heightOverflow:summary.scrollHeight-summary.clientHeight,
          clamped:style.webkitLineClamp!=='none'
        };
      }
      const original=elements.map((e,i)=>{
        e.textContent=tokens[i];
        return measure(e);
      });
      // Negative control: remove just the protective CSS rule in this browser page.
      const broken=elements.map(e=>{
        e.style.setProperty('overflow-wrap','normal','important');
        return measure(e);
      });
      return {original,broken};
    });
    for (const result of results.original) {
      expect(result.lines,result.card+' must wrap').toBeGreaterThan(1);
      expect(result.excess,result.card+' scrolls beyond the card/summary').toBeLessThanOrEqual(1);
      expect(result.widthOverflow,result.card+' summary overflows horizontally').toBeLessThanOrEqual(1);
      expect(result.heightOverflow,result.card+' summary is clipped vertically').toBeLessThanOrEqual(1);
      expect(result.bottomExcess,result.card+' last line is clipped').toBeLessThanOrEqual(1);
      expect(result.clamped,result.card+' summary is line-clamped').toBe(false);
    }
    for (const result of results.broken) {
      expect(result.excess,result.card+' negative control should detect overflow').toBeGreaterThan(1);
    }
  });
}

// MARK-02–04: correct href alone is insufficient if the receiving page ignores the filter.
test('HOME #200 category links apply the destination filter / 390', async ({page}) => {
  await page.setViewportSize({width:390,height:900});
  for (const [index, filter, productId] of [
    [0, 'humanoid', 'unitree-g1'],
    [1, 'quadruped', 'unitree-go2-edu'],
    [2, 'arm', 'tianji-marvin']
  ]) {
    const home = await page.goto(base+'/index.html');
    expect(home.status()).toBe(200);
    await page.locator('.category-lineup figcaption a').nth(index).click();
    await expect(page).toHaveURL(base+'/products.html?filter='+filter+'#lineup');
    await expect(page.locator('#lineup [data-product-filter="'+filter+'"]')).toHaveClass(/\bis-active\b/);
    await expect(page.locator('#lineup [data-product-list] #'+productId)).toBeVisible();
    const otherProduct = filter === 'humanoid' ? 'unitree-go2-edu' : 'unitree-g1';
    await expect(page.locator('#lineup [data-product-list] #'+otherProduct)).toBeHidden();
  }
});



// Keep one sequential detail stop per card. The picture and heading remain
// native links, while the catalog's compare and consultation stay keyboard reachable.
for (const width of [1440,390,360]) {
  test('product cards have one keyboard detail stop / '+width, async ({page}) => {
    await page.setViewportSize({width,height:900});
    for (const isCatalog of [false,true]) {
      const here = isCatalog ? 'products.html' : 'index.html';
      await page.goto(base+'/'+here);
      const grid = page.locator(isCatalog ? '.product-lineup-grid' : '.home-product-grid');
      const cards = grid.locator('.research-product-card:visible');
      await expect(cards.first()).toHaveAttribute('data-product-order',/^\d+$/);
      if (isCatalog) await expect(cards.first().locator('[data-compare-checkbox]')).toBeVisible();
      else await expect(cards).toHaveCount(3);
      // Start exactly before the unchanged production grid; every subsequent
      // move uses the actual browser keyboard order, not programmatic focus.
      await grid.evaluate(root=>{
        for (const [id,position] of [['qa-before-product-grid','beforebegin'],['qa-after-product-grid','afterend']]) {
          const marker=document.createElement('button');
          marker.id=id;
          marker.type='button';
          marker.textContent=id;
          root.insertAdjacentElement(position,marker);
        }
      });
      await page.locator('#qa-before-product-grid').focus();
      let finalHref, finalModel;
      for (const card of await cards.all()) {
        const model=(await card.locator('h3').innerText()).trim();
        const detail=card.locator('.product-link');
        const href=await detail.getAttribute('href');
        const consult=card.locator('.product-consult-link');
        await expect(card.locator('a.product-visual')).toHaveAttribute('href',href);
        await expect(card.locator('h3 a')).toHaveAttribute('href',href);
        if (isCatalog) {
          await page.keyboard.press('Tab');
          // On narrow screens Chromium may focus the horizontally scrollable chips.
          if (await card.locator('.feature-list:focus').count()) await page.keyboard.press('Tab');
          await expect(card.locator('[data-compare-checkbox]')).toBeFocused();
        }
        await page.keyboard.press('Tab');
        await expect(detail).toBeFocused();
        await expect.poll(()=>detail.evaluate(el=>el.matches(':focus-visible'))).toBe(true);
        await expect(detail).toHaveAccessibleName(model+'の製品詳細を見る');
        if (isCatalog) {
          await page.keyboard.press('Tab');
          await expect(consult).toBeFocused();
          finalHref=await consult.getAttribute('href');
          finalModel=model;
        } else finalHref=href;
      }
      await page.keyboard.press('Tab');
      await expect(page.locator('#qa-after-product-grid')).toBeFocused();
      await page.keyboard.press('Shift+Tab');
      await page.keyboard.press('Enter');
      await expect(page).toHaveURL(url=>{
        const expected=new URL(finalHref,base+'/');
        return url.pathname===expected.pathname && url.searchParams.get('product')===expected.searchParams.get('product');
      });
      if (isCatalog) await expect(page.locator('input[name="product"]')).toHaveValue(finalModel);
      else if (width===390) {
        for (const selector of ['a.product-visual','h3 a']) {
          await page.goto(base+'/index.html');
          const link=page.locator('.home-product-grid .research-product-card').first().locator(selector);
          await expect(link).toBeVisible();
          const target=await link.getAttribute('href');
          await link.click();
          await expect(page).toHaveURL(base+'/'+target);
        }
      }
    }
  });
}


test.describe('HOME cards in the delivered HTML without JavaScript', () => {
  test.use({javaScriptEnabled:false});
  for (const width of [1440,390,360]) {
    test('homepage product details are usable without JavaScript / '+width, async ({page}) => {
      await page.setViewportSize({width,height:900});
      const html=await page.goto(base+'/index.html');
      expect(html.ok()).toBe(true);
      const grid=page.locator('.home-product-grid');
      await expect(grid).toHaveAttribute('data-prerendered-products','true');
      const cards=grid.locator('.research-product-card');
      await expect(cards).toHaveCount(3);
      const models=[
        ['Unitree G1-D','Unitree','products/unitree-g1-d.html'],
        ['AgiBot G2','AgiBot','products/agibot-g2.html'],
        ['Unitree G1','Unitree','products/unitree-g1.html']
      ];
      for (const [i,[name,maker,href]] of models.entries()) {
        const card=cards.nth(i);
        await expect(card.getByRole('heading',{name})).toBeVisible();
        await expect(card.locator('.home-product-maker')).toHaveText(maker);
        await expect(card.locator('.home-product-maker')).toBeVisible();
        await expect(card.locator('.product-summary')).toBeVisible();
        await expect(card.locator('.product-summary')).not.toBeEmpty();
        const image=card.locator('img');
        await image.scrollIntoViewIfNeeded();
        await expect.poll(()=>image.evaluate(img=>img.complete && img.naturalWidth>0)).toBe(true);
        await expect(card.locator('.product-link')).toHaveAttribute('href',href);
      }
      expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width+1);
      await cards.first().getByRole('link',{name:'Unitree G1-Dの製品詳細を見る'}).click();
      await expect(page).toHaveURL(base+'/products/unitree-g1-d.html');
    });
  }
});

// HOME: an official GitHub entry must resolve to verified-source direct links,
// not merely an HTTP 200 or a manufacturer download landing page.
for (const {width,height} of sizes) {
  test('HOME catches official GitHub routing regression / '+width, async ({page}) => {
    await page.setViewportSize({width,height});
    const result = await page.request.get(base+'/data/resources.json');
    expect(result.ok()).toBe(true);
    const {resources} = await result.json();
    const valid = resources.filter(({sourceLabel,url}) => {
      if (sourceLabel !== '公式GitHub' || !url) return false;
      const target = new URL(url);
      return target.protocol === 'https:' && target.hostname === 'github.com';
    });
    const expected = valid.map(x=>x.url).sort();
    expect(expected.length).toBeGreaterThan(0);
    expect(valid.some(x=>x.id==='unitree-ros2')).toBe(true);
    await page.goto(base+'/index.html');
    const entry = page.locator('.resource-list a').filter({hasText:/^\s*公式GitHub\s*$/});
    await expect(entry).toHaveCount(1);
    await entry.click();
    await expect(page).toHaveURL(base+'/resources.html?type=github#resource-search');
    await expect(page.locator('select[name="type"]')).toHaveValue('github');
    await expect(page.locator('[data-resource-count]')).toHaveText(String(expected.length));
    const visible = page.locator('.resource-card:visible a.resource-open-link');
    await expect(visible).toHaveCount(expected.length);
    expect((await visible.evaluateAll(links=>links.map(link=>link.href))).sort()).toEqual(expected);

    // The previously published bookmark should still surface direct repositories.
    await page.goto(base+'/resources.html?keyword=GitHub#resource-search');
    await expect(page.locator('.resource-card:visible a[href="https://github.com/unitreerobotics/unitree_ros2"]')).toBeVisible();
  });
}

// HOME-13 P0: public SSOT reconciled against verified September delivery.
// Completion of university acceptance must NOT be inferred from delivery.
test('HOME #200 P0 cross-page case disclosure follows evidence master', async ({page}) => {
  const response=await page.request.get(base+'/data/case-evidence.json');
  expect(response.status()).toBe(200);
  const master=await response.json();
  const record=master.cases.find(x=>x.id==='keio-selection');
  expect(record).toBeTruthy();
  expect(record.status).toBe('in_progress');
  expect(record.statusLabel).toBe('納品・初期確認完了');
  expect(record.progress.filter(x=>x.state==='done').length).toBe(5);
  expect(record.progress.find(x=>x.order===6)?.state).toBe('pending');
  expect(record.title).not.toContain('慶應義塾大学');
  for (const path of ['index.html','cases.html','cases/keio-selection.html']) {
    const res=await page.goto(base+'/'+path,{waitUntil:'networkidle'});
    expect(res.status()).toBe(200);
    const caseStatusSelector=path==='index.html'
      ? '.case-feature .status'
      : path==='cases.html'
        ? '.case-proof-featured .case-status-line .status'
        : '.hub-hero .status';
    await expect(page.locator(caseStatusSelector)).toHaveText(record.statusLabel);
    const html=await page.locator('main').innerText();
    expect(html).not.toContain('現在は納品済みです');
    expect(html).not.toContain('慶應義塾大学');
    expect(await page.title()).not.toContain('慶應義塾大学');
    expect(html).not.toContain('正式発注を経て現在は納品済み');
    expect(html).toContain('納品・初期確認');
    expect(html).not.toContain('正式発注・納品・検収の完了は公開確認待ち');
    if(path!=='index.html') {
      const steps=page.locator('.case-progress-panel .progress-list li.is-done');
      await expect(steps.first()).toBeVisible();
      expect(await steps.count()).toBe(5);
      await expect(page.locator('.case-caution')).toContainText('未確認');
    }
    if(path==='cases/keio-selection.html') {
      await expect(page.locator('.specs tr').filter({hasText:'納品状況'})).toContainText('納品・初期確認完了');
      await expect(page.locator('.specs tr').filter({hasText:'大学側正式検収'})).toContainText('未確認');
    }
  }
});

// HOME-18 / MARK-032: pure-white homepage background contract.
for (const width of [1440, 1280, 390, 360]) {
  test('HOME #200 pure-white main backgrounds / '+width, async ({page}) => {
    await page.setViewportSize({width, height:900});
    const result=await page.goto(base+'/index.html',{waitUntil:'networkidle'});
    expect(result.status()).toBe(200);
    // The actual product image is inserted by async SSOT renderer. Wait until
    // present instead of evaluating a null node under multi-worker CI load.
    await expect(page.locator('.home-product-grid .product-visual').first()).toBeVisible({timeout:15000});
    const styles=await page.evaluate(()=>{
      const bg=(s)=>getComputedStyle(document.querySelector(s)).backgroundColor;
      const color=(s)=>getComputedStyle(document.querySelector(s)).color;
      return {
        allSections:[...document.querySelectorAll('main > section')].map(x=>getComputedStyle(x).backgroundColor),
        hero:bg('main > section.hero'),
        caseSection:bg('main > section.dark'),
        casePanel:bg('main .case-feature'),
        process:bg('main .home-process article'),
        contact:bg('main .contact-panel'),
        productVisual:bg('main .home-product-grid .product-visual'),
        caseHeading:color('main > section.dark h2'),
        caseBody:color('main .case-feature p'),
        ctaBg:bg('main .case-feature .text-link'),
        overflow:document.documentElement.scrollWidth-innerWidth
      };
    });
    expect(styles.allSections.every(x=>x==='rgb(255, 255, 255)')).toBe(true);
    for (const key of ['hero','caseSection','casePanel','process','contact','productVisual']) {
      expect(styles[key],key).toBe('rgb(255, 255, 255)');
    }
    expect(styles.caseHeading).toBe('rgb(23, 51, 66)');
    expect(styles.caseBody).not.toBe('rgb(255, 255, 255)');
    expect(styles.ctaBg).not.toBe('rgb(255, 255, 255)');
    expect(styles.overflow).toBeLessThanOrEqual(1);
  });
}

// HOME #200 P0: Final release artifact must not load legacy GitHub Pages
// assets or publish stale customer identity/address through browser JSON-LD.
for(const width of [1440,390]){
  test('HOME #200 SEO asset status + canonical schema / '+width,async({page})=>{
    await page.setViewportSize({width,height:900});
    const paths=['index.html','cases/keio-selection.html','products/unitree-g1.html'];
    const broken=[];
    page.on('response',r=>{
      const url=new URL(r.url());
      if(url.origin===new URL(base).origin && url.pathname.includes('/assets/') && r.status()===404){
        broken.push(url.pathname);
      }
    });
    for(const path of paths){
      const res=await page.goto(base+'/'+path,{waitUntil:'networkidle'});
      expect(res.status()).toBe(200);
      const d=await page.evaluate(()=>{
        const parse=id=>{const n=document.getElementById(id);return n?JSON.parse(n.textContent):null};
        const org=parse('organization-schema');
        const pageData=parse('page-schema');
        return {
          scripts:[...document.querySelectorAll('script[src]')].map(x=>new URL(x.src).pathname),
          styles:[...document.querySelectorAll('link[rel=stylesheet]')].map(x=>new URL(x.href).pathname),
          canonical:document.querySelector('link[rel=canonical]')?.href,
          org,
          pageData
        };
      });
      expect(d.org, 'organization schema missing').toBeTruthy();
      expect(d.org.url).toBe('https://robotics.air-admin8.co.jp/');
      // The release meta injector may supply the verified Corporate address.
      // Reject the former hardcoded Otemachi office rather than deleting it.
      expect(JSON.stringify(d.org.address || {})).not.toContain('大手町');
      expect(JSON.stringify(d.org.address || {})).not.toContain('千代田区');
      expect(d.canonical).toBe('https://robotics.air-admin8.co.jp/'+(path==='index.html'?'':path));
      expect([...d.scripts,...d.styles].some(u=>u.startsWith('/aa8-Robotic/assets/'))).toBe(false);
      expect(JSON.stringify(d.pageData)).not.toContain('慶應義塾大学');
    }
    expect(broken,'404 assets in public site build').toEqual([]);
  });
}

// Issue #200 HOME-06-R1: independently detect the SP tag collision visible
// in the live 2026-11-24 screenshots despite the earlier 27/27 DOM suite.
for (const width of [1440, 640, 390, 360]) {
  test('HOME #200 maker/ribbon never overlap or wrap / '+width, async ({page}) => {
    await page.setViewportSize({width, height:900});
    const response=await page.goto(base+'/index.html',{waitUntil:'networkidle'});
    expect(response.status()).toBe(200);
    const cards=page.locator('.home-product-grid .research-product-card');
    await expect(cards).toHaveCount(3);
    const layout=await page.evaluate(()=>{
      const inside=(rect,container)=>rect.left>=container.left-1
        && rect.right<=container.right+1
        && rect.top>=container.top-1
        && rect.bottom<=container.bottom+1;
      return [...document.querySelectorAll('.home-product-grid .research-product-card')].map(card=>{
        const ribbon=card.querySelector('.product-priority-ribbon');
        const maker=card.querySelector('.home-product-maker');
        const visual=card.querySelector('.product-visual');
        const a=ribbon.getBoundingClientRect(),b=maker.getBoundingClientRect();
        const v=visual.getBoundingClientRect();
        const area=Math.max(0,Math.min(a.right,b.right)-Math.max(a.left,b.left))
          *Math.max(0,Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top));
        return {id:card.id, makerText:maker.textContent.trim(),
          tagInside:inside(a,v),makerInside:inside(b,v),
          intersectionArea:area,
          makerNoWrap:getComputedStyle(maker).whiteSpace==='nowrap',
          makerOverflow:maker.scrollWidth-maker.clientWidth,
          makerHeight:b.height};
      });
    });
    expect(layout.map(x=>x.makerText)).toEqual(['Unitree','AgiBot','Unitree']);
    for(const item of layout){
      expect(item.tagInside, item.id+' ribbon leaves image column').toBe(true);
      expect(item.makerInside, item.id+' maker leaves image column').toBe(true);
      expect(item.intersectionArea, item.id+' maker/ribbon overlap').toBeLessThanOrEqual(.5);
      if(width<=640){
        expect(item.makerNoWrap, item.id+' manufacturer wraps on SP').toBe(true);
        expect(item.makerOverflow, item.id+' manufacturer clips').toBeLessThanOrEqual(1);
        expect(item.makerHeight, item.id+' manufacturer label too tall').toBeLessThanOrEqual(26);
      }
    }
  });
}
