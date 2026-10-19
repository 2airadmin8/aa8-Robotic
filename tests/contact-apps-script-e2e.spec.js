const { test, expect } = require('@playwright/test');

const BASE = 'https://robotics.air-admin8.co.jp';
const STAGING = process.env.E2E_APPS_SCRIPT_URL;
const EMAIL = process.env.E2E_INTERNAL_EMAIL;
const SCRIPT_PATH = '**/assets/js/contact-v2.js*';

test('isolated Apps Script: two distinct submissions, two acknowledged IDs', async ({ page }) => {
  test.setTimeout(100000);
  if (!STAGING || !EMAIL) throw new Error('Missing isolated E2E secrets');
  const originalEndpoint = /https:\/\/script\.google\.com\/macros\/s\/[^'"]+\/exec/g;
  let replaced = 0;
  await page.route(SCRIPT_PATH, async route => {
    const response = await route.fetch();
    const original = await response.text();
    const patched = original.replace(originalEndpoint, () => {
      replaced++;
      return STAGING;
    });
    if (replaced !== 1) throw new Error('Expected exactly one Apps Script URL in contact-v2.js');
    await route.fulfill({ response, body: patched, headers: { ...response.headers(), 'cache-control': 'no-store' } });
  });

  // Prevent accidental POST to the production Apps Script deployment.
  await page.route('https://script.google.com/macros/s/**/exec', async route => {
    if (route.request().url() !== STAGING) {
      throw new Error('Blocked request to non-test Apps Script deployment');
    }
    await route.continue();
  });

  const ids = [];
  for (let n = 1; n <= 2; n++) {
    await page.goto(BASE + '/contact.html', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('[data-contact-form]')).toBeVisible();
    await page.locator('[name=category]').selectOption('導入条件整理');
    await page.locator('[name=use_case]').fill('E2E_ISOLATED_TEST_' + n);
    await page.locator('[name=organization]').fill('AirAdmin8 E2E TEST - NOT CUSTOMER');
    await page.locator('[name=name]').fill('Internal E2E');
    await page.locator('[name=email]').fill(EMAIL);
    await page.locator('[name=privacy]').check();
    await page.locator('[data-contact-form] button[type=submit]').click();
    await expect(page.locator('[data-contact-confirm]')).toHaveJSProperty('open', true);
    await page.locator('[data-confirm-send]').click();
    await expect(page).toHaveURL(/contact-thanks\.html/, { timeout: 30000 });
    const id = new URL(page.url()).searchParams.get('inquiry_id');
    expect(id).toMatch(/^INQ-/);
    ids.push(id);
  }
  expect(replaced).toBe(2);
  expect(ids[0]).not.toBe(ids[1]);
  console.log('Isolated E2E acknowledged two distinct inquiry IDs (IDs omitted from logs)');
});
