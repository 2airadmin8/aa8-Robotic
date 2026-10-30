const {test,expect}=require('@playwright/test');
const base=process.env.AA8_TEST_BASE||'http://127.0.0.1:4203';
for(const width of [1440,390,360]){
test('H2-X assets photo and video layout / '+width,async({page,request})=>{
 await page.setViewportSize({width,height:900});
 const failed=[],errors=[];
 page.on('response',r=>{if(r.status()>=400&&r.url().startsWith(base))failed.push(r.url()+' '+r.status())});
 page.on('pageerror',e=>errors.push(e.message));
 const res=await page.goto(base+'/products/unitree-h2-x.html',{waitUntil:'networkidle'});
 expect(res.status()).toBe(200);
 await expect(page.locator('#media-h2x')).toBeVisible();
 await expect(page.locator('.h2x-media-gallery img')).toHaveCount(4);
 await expect(page.locator('.h2x-video-grid video')).toHaveCount(3);
 for(const im of await page.locator('.h2x-media-gallery img').all()){
  await im.scrollIntoViewIfNeeded();
  await expect.poll(()=>im.evaluate(e=>e.naturalWidth),{timeout:12000}).toBeGreaterThan(100);
 }
 const scroll=await page.evaluate(()=>document.documentElement.scrollWidth);
 expect(scroll).toBeLessThanOrEqual(width+1);
 expect(errors).toEqual([]);expect(failed).toEqual([]);
});
}
test('3 original H2-X assets are H264 MP4 and nonempty',async({request})=>{
 for(const i of ['01','02','03']){
  const res=await request.get(base+'/assets/img/products/unitree/h2x/drive/video_'+i+'.mp4');
  expect([200,206]).toContain(res.status());
  const buf=await res.body();expect(buf.length).toBeGreaterThan(5000000);
  expect(buf.includes(Buffer.from('avc1'))).toBe(true);
 }
});
