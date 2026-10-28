const { chromium } = require('C:/Users/Administrator/WorkBuddy/2026-10-23-13-18-57/node_modules/playwright');
const path = require('path');

(async () => {
  const fileUrl = 'file://' + path.resolve('docs/index.html');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 1000 } });
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));

  await page.goto(fileUrl, { waitUntil: 'networkidle' });
  await page.waitForTimeout(400);

  // demo mode count
  const demoCount = await page.$eval('#sumBar', el => el.textContent.trim());
  const demoItems = await page.$$eval('#resultBox .item', els => els.length);

  // switch to gov
  await page.click('#dsSeg .seg-item[data-ds="gov"]');
  await page.waitForTimeout(300);
  const govNote = await page.$eval('#dsNote', el => el.textContent.trim());
  const govItems = await page.$$eval('#resultBox .item', els => els.length);
  const provCount = await page.$$eval('#resultBox .prov', els => els.length);
  const govCount = await page.$eval('#sumBar', el => el.textContent.trim());

  // back to demo
  await page.click('#dsSeg .seg-item[data-ds="demo"]');
  await page.waitForTimeout(200);
  const backItems = await page.$$eval('#resultBox .item', els => els.length);
  const backProv = await page.$$eval('#resultBox .prov', els => els.length);

  console.log(JSON.stringify({
    errors,
    demoCount, demoItems,
    govNote, govItems, provCount, govCount,
    backItems, backProv
  }, null, 2));

  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
