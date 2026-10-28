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
  await page.waitForTimeout(300);

  // 设置画像：花生过敏 + 钠上限 800
  await page.evaluate(() => {
    localStorage.removeItem('is_profile');
    document.querySelector('#foodGrid input[value="peanuts"]').checked = true;
    document.getElementById('cSodium').value = '800';
    getProfile();
  });
  await page.waitForTimeout(200);

  // 查找含花生的食品
  const results = await page.evaluate(() => {
    const prof = getProfile();
    const items = PRODUCTS.filter(it => it.cat === 'food');
    const evs = items.map(it => ({it, ev: evaluate(it, prof)}));
    return evs.filter(x => x.ev.reasonDetails && x.ev.reasonDetails.length).map(x => ({
      name: x.it.name,
      cat: x.it.cat,
      status: x.ev.status,
      details: x.ev.reasonDetails
    }));
  });

  console.log(JSON.stringify({errors, results}, null, 2));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });