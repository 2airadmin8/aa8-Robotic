const { test, expect } = require('@playwright/test');

const BASE = 'http://127.0.0.1:4173';
const API = '**/macros/s/**/exec';

async function fillForm(page, suffix = 'A') {
  await page.goto(BASE + '/contact.html');
  await page.locator('[name="category"]').selectOption('導入条件整理');
  await page.locator('[name="use_case"]').fill('Automated QA ' + suffix);
  await page.locator('[name="organization"]').fill('AirAdmin8 QA (internal)');
  await page.locator('[name="name"]').fill('Internal QA');
  await page.locator('[name="email"]').fill('qa@example.com');
  await page.locator('[name="privacy"]').check();
  await page.locator('[data-contact-form] button[type="submit"]').click();
  await expect(page.locator('[data-contact-confirm]')).toHaveJSProperty('open', true);
}
async function submit(page) {
  await page.locator('[data-confirm-send]').click();
}
function reply(token, id, ok = true) {
  return `<!doctype html><script>window.top.postMessage(${JSON.stringify({
    type: 'aa8-inquiry-response', ok, inquiryId: id, responseToken: token,
  })}, ${JSON.stringify(BASE)})</script>`;
}
test('SP and PC: form renders, privacy links to corporate policy', async ({ page }) => {
  for (const width of [375, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto(BASE + '/contact.html');
    await expect(page.locator('[data-contact-form]')).toBeVisible();
    await expect(page.locator('.privacy-consent a')).toHaveAttribute('href', 'https://www.air-admin8.co.jp/privacy-policy/');
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 2)).toBeTruthy();
  }
});
test('two distinct inquiries in same tab produce different tokens', async ({ page }) => {
  const tokens = [];
  await page.route(API, async route => {
    const data = new URLSearchParams(route.request().postData() || '');
    tokens.push(data.get('submission_token'));
    await route.fulfill({ status: 200, contentType: 'text/html',
      body: reply(data.get('response_token'), 'INQ-QA-' + tokens.length) });
  });
  await fillForm(page, 'first');
  await submit(page);
  await expect(page).toHaveURL(/contact-thanks\.html/);
  await fillForm(page, 'second');
  await submit(page);
  await expect(page).toHaveURL(/contact-thanks\.html/);
  expect(tokens).toHaveLength(2);
  expect(tokens[0]).toBeTruthy();
  expect(tokens[1]).not.toBe(tokens[0]);
});
test('failed request retains draft and token; retry uses same token', async ({ page }) => {
  const tokens = [];
  await page.route(API, async route => {
    const data = new URLSearchParams(route.request().postData() || '');
    tokens.push(data.get('submission_token'));
    await route.fulfill({ status: 200, contentType: 'text/html',
      body: reply(data.get('response_token'), tokens.length === 1 ? '' : 'INQ-QA-RETRY', tokens.length > 1) });
  });
  await fillForm(page);
  await submit(page);
  await expect(page.locator('[data-confirm-send]')).toBeEnabled();
  await expect(page.locator('[data-form-error]')).toBeVisible();
  expect(page.url()).toContain('contact.html');
  await submit(page);
  await expect(page).toHaveURL(/contact-thanks\.html/);
  expect(tokens).toHaveLength(2);
  expect(tokens[0]).toBe(tokens[1]);
});
test('repeated click during sending produces one request', async ({ page }) => {
  let calls = 0;
  await page.route(API, async route => {
    calls++;
    await new Promise(resolve => setTimeout(resolve, 800));
    const data = new URLSearchParams(route.request().postData() || '');
    await route.fulfill({ status: 200, contentType: 'text/html',
      body: reply(data.get('response_token'), 'INQ-QA-ONE') });
  });
  await fillForm(page);
  await submit(page);
  await expect(page.locator('[data-confirm-send]')).toBeDisabled();
  await page.locator('[data-confirm-send]').evaluate(button => button.click());
  await expect(page).toHaveURL(/contact-thanks\.html/);
  expect(calls).toBe(1);
});

// PM_PREFILL regression: verify actual acquisition handoff, not just HTTP 200.
// Never submit the form or call the live Apps Script endpoint.
const pmPrefillBase = (process.env.PM_CONTACT_BASE_URL || BASE).replace(/\/$/, '');
for (const entry of [
  { query: '?product=Unitree%20G1', category: '導入条件整理', product: 'Unitree G1' },
  { query: '?product=Unitree%20G1-D', category: '導入条件整理', product: 'Unitree G1-D' },
  { query: '?theme=data', category: 'VLA・模倣学習データ収集', product: '' },
  { query: '?product=AgiBot%20G2&service=multi-brand-comparison&theme=data', category: '製品比較・選定', product: 'AgiBot G2' },
  { query: '?theme=use-case-review', category: '導入条件整理', product: '' },
  { query: '', category: '', product: '' },
]) {
  test('PM_PREFILL source context '+(entry.query||'plain'), async ({ page }) => {
    await page.goto(pmPrefillBase+'/contact.html'+entry.query, {waitUntil:'networkidle'});
    const form=page.locator('[data-contact-form]');
    await expect(form.locator('[name="category"]')).toHaveValue(entry.category);
    await expect(form.locator('[name="product"]')).toHaveValue(entry.product);
    if (entry.product) {
      await expect(form.locator('[name="source_product"]')).toHaveValue(entry.product);
    }
    const sourceTheme = new URLSearchParams(entry.query).get('theme') || '';
    await expect(form.locator('[name="source_theme"]')).toHaveValue(sourceTheme);
    await expect(page.locator('[data-contact-confirm]')).not.toHaveJSProperty('open',true);
  });
}
test('PM_PREFILL product-only context retains prior draft category',async({page})=>{
  await page.addInitScript(()=>{
    if(!window.localStorage.getItem('airadmin8-contact-draft-v1')) {
      window.localStorage.setItem('airadmin8-contact-draft-v1',
        JSON.stringify({savedAt:Date.now(),values:{category:'見積・大学購買'}}));
    }
  });
  await page.goto(pmPrefillBase+'/contact.html?product=Unitree%20G1',{waitUntil:'networkidle'});
  await expect(page.locator('[name="category"]')).toHaveValue('見積・大学購買');
  await expect(page.locator('[name="product"]')).toHaveValue('Unitree G1');
});

// PM_RECEIPT production regression: receipt page must not claim an accepted
// inquiry without both success status and the form's actual inquiry_id key.
// Analytics requests are blocked: tests MUST NOT record fake conversions.
const pmReceiptBase = (process.env.PM_RECEIPT_BASE_URL || BASE).replace(/\/$/, '');
for (const width of [1440, 390]) {
  for (const query of ['', '?status=success', '?status=success&id=OLD-KEY', '?inquiry_id=INQ-NO-STATUS']) {
    test('PM_RECEIPT unverified arrival stays neutral '+width+' '+(query||'(direct)'), async ({page}) => {
      await page.setViewportSize({width,height:900});
      await page.route(/googletagmanager[.]com|google-analytics[.]com|google[.]com/, route=>route.abort());
      const response=await page.goto(pmReceiptBase+'/contact-thanks.html'+query,{waitUntil:'networkidle'});
      expect(response.status()).toBe(200);
      await expect(page.locator('[data-contact-receipt-heading]')).toHaveText('受付結果を確認できません。');
      await expect(page.locator('[data-contact-receipt-link]')).toHaveAttribute('href','/contact.html');
      const leadEvents=await page.evaluate(()=>(window.dataLayer||[]).map(x=>Array.from(x)).filter(x=>x[0]==='event'&&x[1]==='generate_lead'));
      expect(leadEvents).toHaveLength(0);
      expect(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)).toBeLessThanOrEqual(1);
    });
  }
  test('PM_RECEIPT confirmed success uses inquiry_id and never an empty lead event '+width,async({page})=>{
    await page.setViewportSize({width,height:900});
      await page.route(/googletagmanager[.]com|google-analytics[.]com|google[.]com/, route=>route.abort());
    await page.goto(pmReceiptBase+'/contact-thanks.html?status=success&inquiry_id=PM-QA-NOT-SUBMITTED',{waitUntil:'networkidle'});
    await expect(page.locator('[data-contact-receipt-heading]')).toHaveText('お問い合わせを受け付けました。');
    await expect(page.locator('[data-contact-receipt-link]')).toHaveAttribute('href','/');
    const events=await page.evaluate(()=>(window.dataLayer||[]).map(x=>Array.from(x)).filter(x=>x[0]==='event'&&x[1]==='generate_lead'));
    expect(events).toHaveLength(1);
    expect(events[0][2].inquiry_id).toBe('PM-QA-NOT-SUBMITTED');
    expect(page.url()).toBe(pmReceiptBase+'/contact-thanks.html');
    expect(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)).toBeLessThanOrEqual(1);
    // Refresh after stripping query keeps the accepted screen but cannot create a second fake lead event.
    await page.reload({waitUntil:'networkidle'});
    await expect(page.locator('[data-contact-receipt-heading]')).toHaveText('お問い合わせを受け付けました。');
    const secondEvents=await page.evaluate(()=>(window.dataLayer||[]).map(x=>Array.from(x)).filter(x=>x[0]==='event'&&x[1]==='generate_lead'));
    expect(secondEvents).toHaveLength(0);
  });
}
