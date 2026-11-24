// QG-V1.0 | Exact-HEAD final-artifact quality checks for the EXISTING CI.
// This is machine QA, NOT independent human/Figma or business-fact signoff.
// The only permitted interactions are read-only browsing and safe links.
const {test,expect}=require('@playwright/test');
const fs=require('fs');
const path=require('path');
const contract=require('../docs/governance/hp-ui-quality-contract-v1.json');
const tokens=require('../ops/brand-preview/figma-product-v33-tokens.json');
const rootUrl=(process.env.HUB_QA_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const expectedBg=rgbFromHex(tokens.color.surface.page.$value);
const candidateSHA=process.env.PR_HEAD_SHA||'ISOLATED_LOCAL';
const evidenceRoot=path.resolve(__dirname,'..','ui-quality-evidence');
const screenshots=contract.screenshotEvidence;
test.use({screenshot:'only-on-failure',trace:'retain-on-failure'});
function rgbFromHex(hex){
 const s=hex.replace('#','');
 return 'rgb('+[0,2,4].map(i=>parseInt(s.slice(i,i+2),16)).join(', ')+')';
}
function rectangleOverlap(a,b){
 return Math.max(0,Math.min(a.right,b.right)-Math.max(a.left,b.left))*
        Math.max(0,Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top));
}
function fits(inner,outer){
 return inner.left>=outer.left-1&&inner.right<=outer.right+1&&
        inner.top>=outer.top-1&&inner.bottom<=outer.bottom+1;
}
function collectBadges(){
 const rectangleOverlap=(a,b)=>Math.max(0,Math.min(a.right,b.right)-Math.max(a.left,b.left))*
                             Math.max(0,Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top));
 const fits=(inner,outer)=>inner.left>=outer.left-1&&inner.right<=outer.right+1&&
                           inner.top>=outer.top-1&&inner.bottom<=outer.bottom+1;
 const cards=[...document.querySelectorAll('.home-product-grid .research-product-card')];
 return cards.map(c=>{
  const visual=c.querySelector('.product-visual');
  const maker=c.querySelector('.home-product-maker');
  const ribbon=c.querySelector('.product-priority-ribbon');
  if(!visual||!maker||!ribbon)return{id:c.id,missing:true};
  const v=visual.getBoundingClientRect(),m=maker.getBoundingClientRect(),r=ribbon.getBoundingClientRect();
  return {
   id:c.id,maker:maker.textContent.trim(),makerInside:fits(m,v),ribbonInside:fits(r,v),
   overlappingArea:rectangleOverlap(m,r),
   makerNoWrap:getComputedStyle(maker).whiteSpace==='nowrap',
   makerOverflow:maker.scrollWidth-maker.clientWidth,
   makerHeight:m.height
  };
 });
}
function luminance(color){
 const rgb=(color.match(/\d+(?:\.\d+)?/g)||[]).slice(0,3).map(Number);
 if(rgb.length!==3)return NaN;
 return rgb.map(v=>{const n=v/255;return n<=0.04045?n/12.92:((n+0.055)/1.055)**2.4})
           .reduce((s,v,i)=>s+v*[0.2126,0.7152,0.0722][i],0);
}
function contrast(fg,bg){
 const a=luminance(fg),b=luminance(bg);
 return (Math.max(a,b)+0.05)/(Math.min(a,b)+0.05);
}

for(const width of contract.mandatoryViewports){
 test('QG-V1 shared-page machine gate '+width+'px',async({page},testInfo)=>{
  test.setTimeout(180000);
  await page.setViewportSize({width,height:900});
  const reports=[];
  const root=new URL(rootUrl);
  for(const item of contract.pageMatrix){
   await test.step(item.path+' / '+width+'px',async()=>{
    const errors=[],failedAssets=[];
    const onError=e=>errors.push(e.message);
    const onResponse=r=>{
     if(r.status()>=400 && new URL(r.url()).origin===root.origin &&
        /(?:\/assets\/|\/data\/)/.test(new URL(r.url()).pathname)){
      failedAssets.push({status:r.status(),url:r.url()});
     }
    };
    page.on('pageerror',onError);
    page.on('response',onResponse);
    try{
     const res=await page.goto(rootUrl+'/'+item.path,{waitUntil:'networkidle'});
     expect(res&&res.status(),item.path+' page HTTP status').toBe(200);
     await expect(page.locator('header.site-header[data-shared-layout="header"]'),item.path+' shared header').toHaveCount(1);
     await expect(page.locator('footer[data-shared-layout="footer"]'),item.path+' shared footer').toHaveCount(1);
     await expect(page.locator('main h1'),item.path+' exactly one H1').toHaveCount(1);
     await page.evaluate(async()=>{
       await document.fonts.ready;
       for(const img of document.querySelectorAll('main img'))img.loading='eager';
       await Promise.all([...document.querySelectorAll('main img')].map(img=>img.decode().catch(()=>{})));
     });
     const m=await page.evaluate(()=>{
      const broken=[...document.querySelectorAll('main img')].filter(img=>{
        const src=img.currentSrc||img.src;
        if(!src||new URL(src,location.href).origin!==location.origin)return false;
        const r=img.getBoundingClientRect();
        return r.width>0&&r.height>0&&(!img.complete||img.naturalWidth===0);
      }).map(img=>img.currentSrc||img.src);
      const logo=document.querySelector('header.site-header a.brand');
      return {overflow:document.documentElement.scrollWidth-innerWidth,
       broken,logo:logo?.getAttribute('href')||null,
       homeBackgrounds:[...document.querySelectorAll('main > section')].map(e=>getComputedStyle(e).backgroundColor)};
     });
     expect(m.overflow,item.path+' horizontal scroll').toBeLessThanOrEqual(contract.maxHorizontalOverflowPx);
     expect(m.broken,item.path+' broken visible local images').toEqual([]);
     expect(m.logo,item.path+' Logo/home href').toMatch(/^(?:\.\.\/)*index\.html$/);
     if(item.category==='home'){
      expect(m.homeBackgrounds.every(bg=>bg===expectedBg),'home must use mother-site white').toBe(true);
      const cards=page.locator('.home-product-grid .research-product-card');
      await expect(cards,'home must show 3 SSOT cards').toHaveCount(3);
      const badges=await page.evaluate(collectBadges);
      expect(badges.map(x=>x.id),'unexpected homepage models').toEqual(contract.makerBadges.cardIds);
      expect(badges.map(x=>x.maker),'wrong maker').toEqual(contract.makerBadges.expectedMakers);
      for(const badge of badges){
       expect(badge.missing,badge.id+' missing badge').toBeFalsy();
       expect(badge.makerInside,badge.id+' maker escapes image').toBe(true);
       expect(badge.ribbonInside,badge.id+' ribbon escapes image').toBe(true);
       expect(badge.overlappingArea,badge.id+' badge collision').toBeLessThanOrEqual(contract.makerBadges.maxOverlapAreaPx2);
       if(width<=640){
        expect(badge.makerNoWrap,badge.id+' manufacturer wraps').toBe(true);
        expect(badge.makerOverflow,badge.id+' manufacturer truncated').toBeLessThanOrEqual(1);
        expect(badge.makerHeight,badge.id+' manufacturer label too tall').toBeLessThanOrEqual(26);
       }
      }
      const heroButtons=page.locator('main .hero-copy .actions a.button');
      await expect(heroButtons).toHaveCount(2);
      const buttonBounds=await heroButtons.evaluateAll(as=>as.map(a=>{
        const r=a.getBoundingClientRect();
        return{w:r.width,h:r.height,href:a.getAttribute('href'),visible:r.width>0&&r.height>0};
      }));
      expect(buttonBounds.every(x=>x.visible && x.href), 'hero CTA hidden/empty').toBe(true);
      if(width<=640){
       expect(buttonBounds.every(x=>x.h>=contract.mobileHeroMinCtaHeightPx),'mobile hero CTA too small').toBe(true);
      }
      const caseCTA=page.locator('main .case-feature .text-link');
      await expect(caseCTA).toBeVisible();
      const cr=await caseCTA.evaluate(e=>({foreground:getComputedStyle(e).color,background:getComputedStyle(e).backgroundColor}));
      expect(contrast(cr.foreground,cr.background),'case CTA contrast').toBeGreaterThanOrEqual(contract.caseCtaMinContrast);
     }
     if(item.requireMainContactCTA){
      const action=page.locator('main a[href*="contact.html"]');
      await expect(action.first(),item.path+' no contact CTA').toBeAttached();
      const links=await action.evaluateAll(as=>as.map(a=>a.getAttribute('href')));
      expect(links.some(h=>{try{return new URL(h,rootUrl+'/'+item.path).pathname.endsWith('/contact.html')}catch(_){return false}}),
       item.path+' invalid inquiry CTA href').toBe(true);
     }
     expect(errors,item.path+' JavaScript errors').toEqual([]);
     expect(failedAssets,item.path+' HTTP >=400 assets').toEqual([]);
     reports.push({path:item.path,viewport:width,result:'MACHINE_PASS',
      checks:contract.rules.map(x=>x.id),businessFact:'NOT_ATTESTED',
      figmaHumanVisual:'NOT_ATTESTED',writing:'CEO_APPROVAL_REQUIRED'});
     if(screenshots.viewports.includes(width)&&screenshots.pages.includes(item.path)){
      fs.mkdirSync(evidenceRoot,{recursive:true});
      const name=item.path.replaceAll('/','__').replace(/\.html$/,'');
      await page.screenshot({path:path.join(evidenceRoot,'page-'+name+'-'+width+'.png'),fullPage:true});
     }
    }finally{
     page.off('pageerror',onError);
     page.off('response',onResponse);
    }
   });
  }
  fs.mkdirSync(evidenceRoot,{recursive:true});
  fs.writeFileSync(path.join(evidenceRoot,'report-'+width+'.json'),
   JSON.stringify({schema:contract.schemaVersion,revision:candidateSHA,viewport:width,
    pages:reports,overall:'MACHINE_PASS',
    designApproval:'HOLD',businessApproval:'HOLD',releaseAuthorization:'HOLD'},null,2)+'\n');
 });
}

// Negative probe: CI MUST prove the detector would catch the real SP mistake.
// Do NOT modify source, shared CSS files, Factory flags, or release controls.
test('QG-V1 negative probe detects intentional SP maker collision',async({page})=>{
 await page.setViewportSize({width:390,height:900});
 await page.goto(rootUrl+'/index.html',{waitUntil:'networkidle'});
 await expect(page.locator('.home-product-grid .research-product-card')).toHaveCount(3);
 const before=await page.evaluate(collectBadges);
 expect(before.every(x=>x.overlappingArea<=contract.makerBadges.maxOverlapAreaPx2)).toBe(true);
 await page.addStyleTag({content:
   '@media(max-width:640px){.home-product-grid .home-product-maker{top:8px!important;left:8px!important;right:auto!important}}'});
 const after=await page.evaluate(collectBadges);
 expect(after.some(x=>x.overlappingArea>contract.makerBadges.maxOverlapAreaPx2),
  'NEGATIVE TEST INVALID: original overlapping badge no longer detected').toBe(true);
});
