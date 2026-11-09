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
    fs.mkdirSync('x2-qa-artifacts',{recursive:true});
    await page.screenshot({path:path.join('x2-qa-artifacts','X2_'+mode+'_figma_V32.png'),fullPage:true});
    fs.writeFileSync(path.join('x2-qa-artifacts','X2_'+mode+'_geometry.json'),JSON.stringify({mode,figma:target,observed:g,sha:process.env.GITHUB_SHA||'LOCAL'},null,2));
  });
}
