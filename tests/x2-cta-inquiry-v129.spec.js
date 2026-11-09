const {test,expect}=require('@playwright/test');
const BASE=(process.env.AA8_TEST_BASE||'http://127.0.0.1:4173').replace(/\/$/,'');
const API='**/macros/s/**/exec';
const OFFICIAL='https://robotics.air-admin8.co.jp/products/agibot-x2-series.html';

test('X2 actual CTA -> contact -> signed acknowledgement (browser-only, NO production POST)',async({page})=>{
  let calls=0,payload=null;
  await page.route(API,async route=>{
    calls++;
    payload=Object.fromEntries(new URLSearchParams(route.request().postData()||''));
    const token=payload.response_token;
    await route.fulfill({status:200,contentType:'text/html',
      body:'<!doctype html><script>window.top.postMessage('+JSON.stringify({
        type:'aa8-inquiry-response',ok:true,inquiryId:'INQ-QA-SIMULATED-NOT-STORED',responseToken:token
      })+','+JSON.stringify(BASE)+')</script>'});
  });
  await page.goto(BASE+'/x2-pilot-preview.html',{waitUntil:'networkidle'});
  const hero=page.locator('a[data-factory-cta="hero"]');
  await expect(hero).toHaveAttribute('href',/source_page=/);
  await hero.click();
  await expect(page).toHaveURL(/contact\.html\?/);
  const form=page.locator('[data-contact-form]');
  await expect(form.locator('[name="product"]')).toHaveValue('AGIBOT LINGXI X2');
  await expect(form.locator('[name="source_product"]')).toHaveValue('AGIBOT LINGXI X2');
  await expect(form.locator('[name="source_maker"]')).toHaveValue('AGIBOT');
  await expect(form.locator('[name="source_service"]')).toHaveValue('use-case-review');
  await expect(form.locator('[name="source_page"]')).toHaveValue(OFFICIAL);
  await expect(form.locator('[name="category"]')).toHaveValue('導入条件整理');

  await form.locator('[name="organization"]').fill('AirAdmin8 QA internal only');
  await form.locator('[name="name"]').fill('QA Test User');
  await form.locator('[name="email"]').fill('qa@example.invalid');
  await form.locator('[name="use_case"]').fill('x2-v129-field-handoff-test');
  await form.locator('[name="privacy"]').check();
  await form.locator('button[type="submit"]').click();
  await expect(page.locator('[data-contact-confirm]')).toHaveJSProperty('open',true);
  await expect(page.locator('[data-confirm-summary]')).toContainText('AGIBOT LINGXI X2');
  expect(calls).toBe(0);
  await page.locator('[data-confirm-send]').click();
  await expect(page).toHaveURL(/contact-thanks\.html/);
  expect(calls).toBe(1);
  expect(payload).toMatchObject({
    product:'AGIBOT LINGXI X2',source_product:'AGIBOT LINGXI X2',
    source_maker:'AGIBOT',source_service:'use-case-review',source_page:OFFICIAL,
    category:'導入条件整理',use_case:'x2-v129-field-handoff-test'
  });
  expect(payload.submission_token).toBeTruthy();
  expect(payload.response_token).toBeTruthy();
  // contact-thanks intentionally scrubs inquiry_id from browser URL after receipt.
  await expect(page.locator('[data-contact-receipt-heading]')).toHaveText('お問い合わせを受け付けました。');
  expect(page.url()).not.toContain('INQ-QA-SIMULATED-NOT-STORED');
});

test('X2 source_page rejects external/altered URLs before form submission',async({page})=>{
  for(const source of [
    'https://attacker.example/products/agibot-x2-series.html',
    'https://robotics.air-admin8.co.jp/products/agibot-x2-series.html?token=secret',
    'javascript:alert(1)'
  ]){
    const url=BASE+'/contact.html?product=AGIBOT%20LINGXI%20X2&maker=AGIBOT&source_page='+encodeURIComponent(source);
    await page.goto(url,{waitUntil:'domcontentloaded'});
    const hidden=await page.locator('[name="source_page"]').inputValue();
    expect(hidden).not.toBe(source);
  }
});
