const {test,expect}=require('@playwright/test');
const base=process.env.AA8_TEST_BASE||'http://127.0.0.1:4173';
for(const width of [1440,390]){
  test('products catalog, hero and G1 image baseline at '+width+'px',async({page})=>{
    await page.setViewportSize({width,height:900});
    await page.goto(base+'/products.html',{waitUntil:'networkidle'});
    const hero=page.locator('.product-page-hero h1');
    await expect(hero).toBeVisible();
    const title=await hero.evaluate(e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();
      return{font:parseFloat(s.fontSize),lineHeight:parseFloat(s.lineHeight),height:r.height,width:r.width,scrollWidth:e.scrollWidth}});
    expect(title.font).toBeLessThanOrEqual(width===1440?49:35);
    expect(title.font).toBeGreaterThanOrEqual(width===1440?38:28);
    expect(title.scrollWidth).toBeLessThanOrEqual(title.width+1);
    const root=page.locator('[data-product-list]');
    await expect(root).toHaveAttribute('data-exclude-products','limx-oli');
    await expect(root.locator('.research-product-card')).toHaveCount(12);
    await expect(root.locator('#unitree-g1-plus')).toHaveCount(1);
    await expect(root.locator('#unitree-h2-d')).toHaveCount(1);
    await expect(root.locator('#limx-oli')).toHaveCount(0);
    await expect(page.locator('.product-list-summary')).toContainText('12製品を比較');
    for(const [id,filename] of [['unitree-g1-d','unitree-g1-d.png'],['unitree-g1','28_g1.png']]){
      const im=root.locator('#'+id+' .product-visual img');
      await expect(im).toHaveAttribute('src',new RegExp(filename.replaceAll('.','\\.')+'$'));
      await im.scrollIntoViewIfNeeded();
      await expect.poll(()=>im.evaluate(i=>i.naturalWidth)).toBe(id==='unitree-g1-d'?801:500);
      const c=await im.evaluate(i=>{const s=getComputedStyle(i);return{fit:s.objectFit,position:s.objectPosition,padBottom:parseFloat(s.paddingBottom)};});
      expect(c.fit).toBe('contain');
      expect(c.position).toBe('50% 100%');
      expect(c.padBottom).toBe(0);
    }
    await expect(root.locator('#agibot-g2')).toHaveCount(1);
    expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width+1);
  });
  test('CEO requested G1 specification photo half-scale only on desktop '+width+'px',async({page})=>{
    await page.setViewportSize({width,height:900});
    await page.goto(base+'/products/unitree-g1.html',{waitUntil:'networkidle'});
    const image=page.locator('.g1-spec-overview-figure img');
    await image.scrollIntoViewIfNeeded();
    await expect.poll(()=>image.evaluate(i=>i.naturalWidth)).toBe(630);
    const measure=await image.evaluate(i=>{const r=i.getBoundingClientRect();return{w:r.width,h:r.height};});
    const w=width===1440?315:346, h=width===1440?295:346*590/630;
    expect(Math.abs(measure.w-w)).toBeLessThanOrEqual(1);
    expect(Math.abs(measure.h-h)).toBeLessThanOrEqual(1);
    await expect(page.locator('.g1-spec-table tbody tr:not(.g1-spec-group)')).toHaveCount(28);
    expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width+1);
  });
}


for(const width of [1440,390]){
  test('C19 catalog filter states and accessible empty result '+width+'px',async({page})=>{
    await page.setViewportSize({width,height:900});
    await page.goto(base+'/products.html?filter=quadruped',{waitUntil:'networkidle'});
    const root=page.locator('[data-product-list]');
    await expect(root).not.toHaveAttribute('aria-busy','true');
    await expect(page.locator('[data-product-loading]')).toBeHidden();
    const quad=page.locator('[data-product-filter="quadruped"]');
    await expect(quad).toHaveAttribute('aria-pressed','true');
    await expect(page.locator('[data-product-filter="all"]')).toHaveAttribute('aria-pressed','false');
    expect(await root.locator('.research-product-card:visible').count()).toBeGreaterThan(0);
    await page.locator('[data-product-filter="all"]').click();
    await expect(page.locator('[data-product-filter="all"]')).toHaveAttribute('aria-pressed','true');
    await page.goto(base+'/products.html?maker=not-a-maker&filter=humanoid',{waitUntil:'networkidle'});
    await expect(root.locator('.research-product-card')).toHaveCount(12);
    await expect(root.locator('.research-product-card:visible')).toHaveCount(0);
    await expect(page.locator('[data-product-empty]')).toBeVisible();
    await expect(page.locator('[data-product-filter="humanoid"]')).toHaveAttribute('aria-pressed','true');
    expect(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)).toBeLessThanOrEqual(1);
  });
  test('C20 loading completes and C13 catalog fetch failure is visible '+width+'px',async({page})=>{
    await page.setViewportSize({width,height:900});
    await page.route('**/data/products.json',route=>route.abort('failed'));
    await page.goto(base+'/products.html',{waitUntil:'networkidle'});
    await expect(page.locator('[data-product-list] [role="alert"]')).toContainText('読み込めませんでした');
    await expect(page.locator('[data-product-loading]')).toBeHidden();
    await expect(page.locator('[data-product-list]')).not.toHaveAttribute('aria-busy','true');
    expect(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)).toBeLessThanOrEqual(1);
  });
}


// C10 related product card: real Product Master contract, focus, navigation,
// and deterministic image error handling. Never edits product truth or sends inquiry.
const c10Master = require('../data/products.json');
const c10Known = c10Master.products.find(item=>item.id==='agibot-g2');
for(const width of [1440,390,360]){
  test('C10 related product card content hover focus keyboard '+width+'px',async({page})=>{
    await page.setViewportSize({width,height:900});
    await page.goto(base+'/products.html',{waitUntil:'networkidle'});
    const card=page.locator('[data-product-list] #agibot-g2');
    await expect(card).toBeVisible();
    await expect(card.locator('h3')).toHaveText(c10Known.name);
    await expect(card.locator('.product-maker')).toHaveText(c10Known.manufacturerName);
    await expect(card.locator('.product-topline .status')).toHaveText(c10Known.statusLabel);
    await expect(card.locator('.product-visual img')).toHaveAttribute('src',c10Known.image);
    await expect(card.locator('.product-visual')).toHaveAttribute('href',c10Known.detailPage);
    // Figma native Cards and Content 217:127 labels the desktop MEDIA SLOT 16:9.
    if(width===1440)
      await expect(card.locator('.product-visual')).toHaveCSS('aspect-ratio','16 / 9');
    const consult=card.locator('.product-consult-link');
    await expect(consult).toHaveAttribute('href','contact.html?product='+encodeURIComponent(c10Known.name));
    await card.scrollIntoViewIfNeeded();
    await page.mouse.move(0,0);
    const baseline=await card.evaluate(el=>{
      const cs=getComputedStyle(el);return {border:cs.borderColor,shadow:cs.boxShadow};
    });
    await card.hover();
    // CSS transitions do not finish synchronously with Playwright hover().
    await expect.poll(()=>card.evaluate((el,b)=>{
      const cs=getComputedStyle(el);return cs.borderColor!==b.border||cs.boxShadow!==b.shadow;
    },baseline)).toBe(true);
    const detail=card.locator('.product-visual');
    await detail.focus();
    const focus=await card.evaluate(el=>{
      const cs=getComputedStyle(el);return{focused:el.matches(':focus-within'),outline:cs.outlineStyle,width:parseFloat(cs.outlineWidth)};
    });
    expect(focus.focused).toBe(true);
    expect(focus.outline).not.toBe('none');
    expect(focus.width).toBeGreaterThanOrEqual(2);
    await detail.press('Enter');
    await expect(page).toHaveURL(/\/products\/agibot-g2\.html$/);
    expect(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)).toBeLessThanOrEqual(2);
  });
  test('C10 image failure shows honest accessible fallback '+width+'px',async({page})=>{
    await page.setViewportSize({width,height:900});
    await page.route('**/'+c10Known.image,route=>route.abort('failed'));
    await page.goto(base+'/products.html',{waitUntil:'domcontentloaded'});
    const card=page.locator('[data-product-list] #agibot-g2');
    await expect(card).toBeVisible();
    await card.locator('.product-visual').scrollIntoViewIfNeeded();
    await expect(card.locator('.product-image-fallback')).toBeVisible();
    await expect(card.locator('.product-image-fallback')).toContainText('画像を表示できません');
    await expect(card.locator('.product-visual img')).toBeHidden();
    await expect(card.locator('.product-visual')).toHaveAttribute('href',c10Known.detailPage);
    await expect(card.locator('h3')).toHaveText(c10Known.name);
    expect(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)).toBeLessThanOrEqual(2);
  });
}


// C10 12 visible catalog cards plus excluded SKU remains in official Master;
// image evidence is from true local Product Master paths, not synthetic images.
for(const width of [1440,390,360]){
  test('C10 full public catalog preserves SSOT, media and AA links '+width+'px',async({page})=>{
    await page.setViewportSize({width,height:900});
    await page.goto(base+'/products.html',{waitUntil:'networkidle'});
    const products=c10Master.products.filter(x=>x.visibility==='public'&&x.id!=='limx-oli');
    expect(products).toHaveLength(12);
    const root=page.locator('[data-product-list]');
    await expect(root.locator('article.research-product-card')).toHaveCount(products.length);
    for(const item of products){
      const card=root.locator('#'+item.id);
      await expect(card.locator('h3')).toHaveText(item.name);
      await expect(card.locator('.product-maker')).toHaveText(item.manufacturerName);
      await expect(card.locator('.status')).toContainText(item.statusLabel);
      const detail=card.locator('.product-visual');
      await expect(detail).toHaveAttribute('href',item.detailPage);
      const image=detail.locator('img');
      await expect(image).toHaveAttribute('src',item.image);
      await detail.scrollIntoViewIfNeeded();
      await expect.poll(()=>image.evaluate(el=>el.naturalWidth),{timeout:20000}).toBeGreaterThan(0);
      await expect(card.locator('.product-image-fallback')).toHaveCount(0);
      const consult=card.locator('.product-consult-link');
      await expect(consult).toHaveAttribute('href','contact.html?product='+encodeURIComponent(item.name));
      const contrast=await consult.evaluate(el=>{
        const rgb=s=>(s.match(/[0-9.]+/g)||[]).slice(0,3).map(Number);
        const lum=s=>rgb(s).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4})
          .reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722][i],0);
        const s=getComputedStyle(el),c=lum(s.color),b=lum(s.backgroundColor);
        // Transparent action link has a white parent card surface.
        const background=s.backgroundColor==='rgba(0, 0, 0, 0)'
          ?lum(getComputedStyle(el.closest('.research-product-card')).backgroundColor):b;
        return (Math.max(c,background)+.05)/(Math.min(c,background)+.05);
      });
      expect(contrast,item.id+' consult link contrast').toBeGreaterThanOrEqual(4.5);
      const contrasts=await card.evaluate(el=>{
        const rgb=s=>(s.match(/[0-9.]+/g)||[]).slice(0,3).map(Number);
        const lum=s=>rgb(s).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4})
          .reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722][i],0);
        const ratio=(a,b)=>{a=lum(a);b=lum(b);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05)};
        const detail=getComputedStyle(el.querySelector('.product-card-actions .product-link'));
        const tag=el.querySelector('.product-condition-meta .tag');
        const tagBg=getComputedStyle(tag).backgroundColor;
        const prefix=getComputedStyle(tag,'::before');
        return{detail:ratio(detail.color,'rgb(255,255,255)'),prefix:ratio(prefix.color,tagBg)};
      });
      expect(contrasts.detail,item.id+' detail-link AA contrast').toBeGreaterThanOrEqual(4.5);
      expect(contrasts.prefix,item.id+' price/lead-time prefix contrast').toBeGreaterThanOrEqual(4.5);
    }
    await expect(root.locator('#limx-oli')).toHaveCount(0);
    expect(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth))
      .toBeLessThanOrEqual(2);
  });
}
