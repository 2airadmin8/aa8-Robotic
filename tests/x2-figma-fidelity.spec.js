const {test,expect}=require('@playwright/test');
const fs=require('fs'),path=require('path');
const BASE=(process.env.AA8_TEST_BASE||'http://127.0.0.1:4173').replace(/\/$/,'');
const figma={PC:{viewport:1440,hero:555,shell:1200,title:38},SP:{viewport:390,hero:698,shell:346,title:32}};
for(const [mode,target] of Object.entries(figma)){
  test('X2 Figma V3.2 '+mode+': geometry and comparison',async({page})=>{
    await page.setViewportSize({width:target.viewport,height:960});
    const pageErrors=[],failedAssets=[];
    page.on('pageerror',e=>pageErrors.push(e.message));
    page.on('response',r=>{if(r.url().startsWith(BASE)&&r.status()>=400&&!r.url().endsWith('/favicon.ico'))failedAssets.push(r.url())});
    await page.goto(BASE+'/x2-pilot-preview.html',{waitUntil:'networkidle'});
    await expect(page.locator('main[data-product-id="agibot-x2-series"]')).toHaveCount(1);
    await expect(page.locator('h1')).toHaveText('AGIBOT LINGXI X2');
    await expect(page.locator('#specifications tr[data-spec-row]')).toHaveCount(36);
    await expect(page.locator('#specifications tr.x2-category-row')).toHaveCount(9);
    await expect(page.locator('#specifications tr.x2-compare-head')).toHaveCount(1);
    await expect(page.locator('#specifications tr.x2-spec-row').first().locator('td')).toHaveCount(2);
    const g=await page.evaluate(()=>{
      const box=s=>{let x=document.querySelector(s);let r=x.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height,font:parseFloat(getComputedStyle(x).fontSize),bg:getComputedStyle(x).backgroundColor}};
      return {hero:box('.g1-hero'),shell:box('.g1-hero .g1-shell'),title:box('#product-name'),firstSpec:box('#specifications .x2-spec-row'),overflow:document.documentElement.scrollWidth-innerWidth,firstCell:getComputedStyle(document.querySelector('#specifications .x2-spec-row td')).display};
    });
    expect(Math.abs(g.shell.w-target.shell)).toBeLessThanOrEqual(2);
    expect(Math.abs(g.title.font-target.title)).toBeLessThanOrEqual(1);
    expect(Math.abs(g.hero.h-target.hero)).toBeLessThanOrEqual(mode==='PC'?8:25);
    expect(g.overflow).toBeLessThanOrEqual(1);
    if(mode==='SP'){
      expect(g.firstCell).toBe('block');
      const labels=await page.locator('#specifications tr.x2-spec-row').first().locator('td').evaluateAll(els=>els.map(el=>getComputedStyle(el,'::before').content));
      expect(labels[0]).toContain('X2');
      expect(labels[1]).toContain('X2 Ultra');
    }
    expect(pageErrors).toEqual([]);expect(failedAssets).toEqual([]);
    // A full-page screenshot does not reliably trigger below-the-fold
    // loading="lazy" images. Actually scroll and confirm all 3 related
    // media (and 3 CTA photos) before capturing Figma visual evidence.
    for(const selector of ['.g1-factory-related-photo img','.g1-factory-cta img']){
      const images=page.locator(selector);
      await expect(images).toHaveCount(3);
      for(let i=0;i<3;i++){
        await images.nth(i).scrollIntoViewIfNeeded();
        await expect.poll(()=>images.nth(i).evaluate(img=>
          img.complete&&img.naturalWidth>0&&img.naturalHeight>0
        ),{timeout:12000}).toBe(true);
      }
    }
    // html{scroll-behavior:smooth} previously kept the sticky header at
    // a scrolled position when Chromium captured the full-page proof.
    // Disable only the scroll animation for evidence, never change site CSS.
    await page.evaluate(()=>{
      document.documentElement.style.scrollBehavior='auto';
      window.scrollTo({top:0,left:0,behavior:'instant'});
    });
    await expect.poll(()=>page.evaluate(()=>window.scrollY),{timeout:5000}).toBe(0);
    fs.mkdirSync('x2-qa-artifacts',{recursive:true});
    await page.screenshot({path:path.join('x2-qa-artifacts','X2_'+mode+'_figma_V32.png'),fullPage:true});
    await page.evaluate(()=>document.documentElement.style.removeProperty('scroll-behavior'));
    fs.writeFileSync(path.join('x2-qa-artifacts','X2_'+mode+'_geometry.json'),JSON.stringify({mode,figma:target,observed:g,sha:process.env.GITHUB_SHA||'LOCAL'},null,2));
  });
}
