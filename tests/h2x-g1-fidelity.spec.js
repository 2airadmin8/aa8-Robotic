const {test,expect}=require('@playwright/test');
const base=process.env.AA8_TEST_BASE||'http://127.0.0.1:4173';
const G1='/products/unitree-g1.html', H2X='/products/unitree-h2-x.html';
const ctaBg='g1-cta-figma-pc.png';

for(const width of [1440,390,360]){
 test('H2-X Figma G1 visual inheritance, white background + image CTA / '+width,async({page})=>{
  await page.setViewportSize({width,height:900});
  const errors=[],failed=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('response',r=>{if(r.status()>=400&&r.url().startsWith(base))failed.push(r.status()+' '+r.url())});
  await page.goto(base+G1,{waitUntil:'networkidle'});
  const g1=await page.evaluate(()=>{
    const e=document.querySelector('main .g1-final-cta'),s=getComputedStyle(e);
    return {ctaImage:s.backgroundImage,cards:e.querySelectorAll('.g1-cta-card').length,
      cardWithPhotos:e.querySelectorAll('.g1-cta-card .g1-cta-photo img').length,
      headerBackground:getComputedStyle(document.querySelector('.g1-hero')).backgroundColor,
      backgroundFile:s.backgroundImage.match(/g1-cta-figma-pc\.png/)?.[0]};
  });
  expect(g1.ctaImage).toContain(ctaBg);
  expect(g1.cards).toBe(3);
  expect(g1.cardWithPhotos).toBe(3);
  expect(g1.headerBackground).toBe('rgb(255, 255, 255)');
  const res=await page.goto(base+H2X,{waitUntil:'networkidle'});
  expect(res.status()).toBe(200);
  const metrics=await page.evaluate(()=>{
    const css=q=>getComputedStyle(document.querySelector(q));
    const main=document.querySelector('main.h2x-page');
    const images=[...main.querySelectorAll('.h2x-final-cta .g1-cta-card .g1-cta-photo img')];
    const photos=images.map(e=>({src:e.getAttribute('src'),w:e.naturalWidth,h:e.naturalHeight}));
    const cta=main.querySelector('.h2x-final-cta');
    const cards=[...cta.querySelectorAll('.g1-cta-card')].map(e=>({imageCount:e.querySelectorAll('img').length,height:Math.round(e.getBoundingClientRect().height)}));
    const sections=[...main.querySelectorAll(':scope > section.g1-section')].filter(e=>!e.classList.contains('g1-final-cta')).map(e=>({id:e.id,bg:getComputedStyle(e).backgroundColor}));
    return{heroBg:css('.h2-hero').backgroundColor,heroImage:css('.h2-hero').backgroundImage,
       useBg:css('.h2-use').backgroundColor,researchBg:css('.h2-research').backgroundColor,
       modelBg:css('.h2-model-grid article:last-child').backgroundColor,
       ctaBg:css('.h2x-final-cta').backgroundImage,ctaTitle:css('.h2x-final-cta h2').color,
       ctaKicker:css('.h2x-final-cta .g1-kicker').color, ctaGrid:css('.h2x-final-cta .g1-cta-grid').gridTemplateColumns,
       isApprovedG1Class:cta.classList.contains('g1-final-cta'),photos,cards,sections,
       overflow:document.documentElement.scrollWidth>innerWidth+1};
  });
  expect(metrics.heroBg).toBe('rgb(255, 255, 255)');
  expect(metrics.heroImage).toBe('none');
  expect(metrics.useBg).toBe('rgb(255, 255, 255)');
  expect(metrics.researchBg).toBe('rgb(255, 255, 255)');
  expect(metrics.modelBg).toBe('rgb(255, 255, 255)');
  expect(metrics.ctaBg).toBe(g1.ctaImage);
  expect(metrics.ctaTitle).toBe('rgb(255, 255, 255)');
  expect(metrics.isApprovedG1Class).toBe(true);
  expect(metrics.cards).toHaveLength(3);
  expect(metrics.photos).toHaveLength(3);
  expect(metrics.photos.every(x=>x.w>100 && x.h>100)).toBe(true);
  expect(metrics.cards.every(x=>x.imageCount===1)).toBe(true);
  expect(metrics.sections.every(x=>x.bg==='rgb(255, 255, 255)')).toBe(true);
  expect(metrics.overflow).toBe(false);
  expect(metrics.photos.map(x=>x.src)).toEqual([
   '/assets/img/products/unitree/h2x/drive/image_005.webp',
   '/assets/img/products/unitree/h2x/drive/image_007.webp',
   '/assets/img/products/unitree/h2x/drive/image_013.jpg'
  ]);
  if(width<=780){
   expect(metrics.ctaGrid.split(' ').length).toBe(1);
   expect(metrics.cards.every(x=>x.height===328)).toBe(true);
  }else{
   expect(metrics.ctaGrid.split(' ').length).toBe(3);
  }
  const actions=await page.locator('.h2x-final-cta .g1-cta-card').evaluateAll(as=>as.map(a=>a.getAttribute('href')));
  expect(actions).toEqual([
    '/assets/img/products/unitree/h2x/drive/video_01.mp4',
    '#specifications',
    '/contact.html?product=Unitree%20H2-X&service=university-procurement'
  ]);
  expect(failed).toEqual([]);
  expect(errors).toEqual([]);
 });
}
