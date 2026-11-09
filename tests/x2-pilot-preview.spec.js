const {test,expect}=require('@playwright/test');
const base=process.env.AA8_TEST_BASE||'http://127.0.0.1:4173';
for(const width of [1440,390,320]){
 test('X2 series pilot: manufacturer 36-row Figma-fidelity preview / '+width,async({page})=>{
  await page.setViewportSize({width,height:900});
  const failures=[];
  page.on('pageerror',e=>failures.push(e.message));
  page.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)failures.push(r.status()+' '+r.url());});
  const response=await page.goto(base+'/x2-pilot-preview.html',{waitUntil:'networkidle'});
  expect(response.status()).toBe(200);
  await expect(page.locator('meta[name=robots]')).toHaveAttribute('content','noindex,nofollow');
  await expect(page.locator('main[data-product-id="agibot-x2-series"]')).toHaveCount(1);
  await expect(page.locator('#specifications tbody tr')).toHaveCount(36);
  await expect(page.locator('.g1-factory-media-grid img')).toHaveCount(3);
  const gallery=page.locator('.g1-factory-media-grid img');
  for(let i=0;i<3;i++){
    await gallery.nth(i).scrollIntoViewIfNeeded();
    await expect.poll(()=>gallery.nth(i).evaluate(img=>img.complete&&img.naturalWidth>0),{timeout:12000}).toBe(true);
  }
  const attrs=await gallery.evaluateAll(all=>all.map(n=>({complete:n.complete,width:n.naturalWidth})));
  expect(attrs.every(x=>x.complete&&x.width>0)).toBeTruthy();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)).toBeLessThanOrEqual(1);
  const hero=page.locator('a[data-factory-cta=hero]');
  const href=await hero.getAttribute('href');
  expect(href).toContain('maker=AGIBOT');
  expect(href).toContain('service=use-case-review');
  expect(href).toContain('source_page=');
  const url=new URL(href,'http://127.0.0.1:4173');
  expect(url.searchParams.get('source_page')).toBe('https://robotics.air-admin8.co.jp/products/agibot-x2-series.html');
  // Figma V3.2 visual parity for the X2 series *photo-only* fallback.
  // Figma reference: PC 33:2714 (~555px Hero), SP 29:1657 (~698px).
  const layout=await page.evaluate(()=>{
    const b=s=>{const n=document.querySelector(s);if(!n)return null;
      const q=n.getBoundingClientRect();return{y:q.top+window.scrollY,height:q.height,width:q.width}};
    return{hero:b('.g1-hero'),title:b('.g1-hero-copy h1'),
      lead:b('.g1-hero-lead'),photo:b('.g1-hero-image'),
      description:b('.g1-hero-description'),cta:b('.g1-hero-ctas'),
      source:b('.g1-hero-copy > p.g1-fine'),
      background:getComputedStyle(document.querySelector('.g1-hero')).backgroundColor,
      fakeVideo:!!document.querySelector('.g1-hero-video, .g1-video-play')};
  });
  expect(layout.background).toBe('rgb(255, 255, 255)');
  expect(layout.fakeVideo).toBe(false);
  expect(layout.title).toBeTruthy();
  expect(layout.photo).toBeTruthy();
  if(width>=781){
    expect(layout.photo.height).toBeGreaterThanOrEqual(398);
    expect(layout.photo.height).toBeLessThanOrEqual(402);
    expect(layout.title.y).toBeLessThan(layout.cta.y);
    expect(layout.hero.height).toBeLessThanOrEqual(660);
  } else {
    expect(layout.photo.height).toBeGreaterThanOrEqual(214);
    expect(layout.photo.height).toBeLessThanOrEqual(218);
    // Figma SP: kicker -> title -> lead -> media -> description -> CTAs -> note.
    expect(layout.title.y).toBeLessThan(layout.lead.y);
    expect(layout.lead.y).toBeLessThan(layout.photo.y);
    expect(layout.photo.y).toBeLessThan(layout.description.y);
    expect(layout.description.y).toBeLessThan(layout.cta.y);
    expect(layout.cta.y).toBeLessThan(layout.source.y);
    expect(layout.hero.height).toBeLessThanOrEqual(width===390?750:860);
  }
  expect(failures).toEqual([]);
 });
}
