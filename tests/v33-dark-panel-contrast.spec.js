const {test,expect}=require('@playwright/test');
const fs=require('fs');
const path=require('path');
const base=process.env.AA8_TEST_BASE||'http://127.0.0.1:4173';
const products=JSON.parse(fs.readFileSync(path.join(__dirname,'../data/products.json'),'utf8')).products;

/** Chrome guard for the V3.3 neutral-spec heading override.
 * Detect unreadable headings on *solid* dark backgrounds across all public SKUs.
 * Gradient or image-backed headings must retain their dedicated visual QA;
 * the G1+ dark rear-view panel has explicit WCAG tests in g1plus-product.spec.js.
 */
for(const width of [1440,390,360]){
 test('V3.3 protects solid-dark section headings for all 13 public SKUs at '+width+'px',async({browser})=>{
  test.setTimeout(85000);
  const context=await browser.newContext({viewport:{width,height:900}});
  const violations=[],scanned=[];
  for(const product of products){
   const page=await context.newPage();
   try{
    const response=await page.goto(base+'/'+product.detailPage,{waitUntil:'domcontentloaded',timeout:18000});
    expect(response.status(),product.id).toBe(200);
    const headings=await page.evaluate(()=>{
      const lum=(value)=>{
        const parts=(value.match(/[\d.]+/g)||[]).map(Number);
        if(parts.length<3||(parts[3]!==undefined&&parts[3]<.95))return null;
        const c=parts.slice(0,3).map(x=>x/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4);
        return .2126*c[0]+.7152*c[1]+.0722*c[2];
      };
      const list=[];
      for(const heading of document.querySelectorAll('main h1,main h2,main h3,main h4')){
        const r=heading.getBoundingClientRect(),h=getComputedStyle(heading);
        if(r.height<1||r.width<1||h.visibility==='hidden'||h.display==='none')continue;
        let target=heading,bg=null;
        for(let i=0;i<9&&target;i++,target=target.parentElement){
          const t=getComputedStyle(target);
          if(t.backgroundImage!=='none')break;
          const l=lum(t.backgroundColor);
          if(l!==null){bg=l;break;}
        }
        if(bg===null||bg>.18)continue;
        const fg=lum(h.color);if(fg===null)continue;
        const contrast=(Math.max(fg,bg)+.05)/(Math.min(fg,bg)+.05);
        list.push({text:heading.textContent.trim().slice(0,70),contrast,element:heading.tagName});
      }
      return list;
    });
    scanned.push({sku:product.id,count:headings.length});
    for(const h of headings)if(h.contrast<4.5)violations.push({sku:product.id,width,...h});
   }finally{await page.close();}
  }
  await context.close();
  expect(scanned).toHaveLength(13);
  expect(scanned.some(x=>x.sku==='unitree-g1-plus'&&x.count>0)).toBe(true);
  expect(violations,'WCAG AA solid-dark headings: '+JSON.stringify(violations)).toEqual([]);
 });
}
