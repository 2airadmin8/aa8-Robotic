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


// V15｜CEO annotated multi-page visual regression, 2026-10-30.
// No real business form submission, no GA/CRM writes; checks the actual UI.
const v15Base=(process.env.V15_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const v15Pages=[
 {path:'index.html',marker:'.hero-grid-v2',sections:10,heroPc:700,heroSp:940,hasDark:true,
  headings:['AIロボット導入支援を、4段階で進めます','研究テーマ・現場用途からAIロボットを探す',
   '研究用AIロボットの代表製品','選定だけで終わらない、AIロボット導入支援',
   'AIロボット導入支援の実績を、具体的なプロセスとともにご紹介します',
   'SDK・ROS・VLAの公式資料を確認できます','AIロボット導入支援でよくある質問',
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
    expect(m.darkColor).toBe('rgb(255, 255, 255)');
    expect(m.darkSize).toBeLessThanOrEqual(width===1440?38.1:27.1);
   }
   if(def.path==='index.html')expect(m.darkCaseColor).toBe('rgb(255, 255, 255)');
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
