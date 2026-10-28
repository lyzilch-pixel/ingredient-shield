const { chromium } = require('C:/Users/Administrator/WorkBuddy/2026-10-23-13-18-57/node_modules/playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 1000 }, deviceScaleFactor: 2 });
  await p.goto('https://lyzilch-pixel.github.io/ingredient-shield/', { waitUntil: 'networkidle' });
  await p.waitForTimeout(500);
  await p.check('input[value="peanuts"]');
  await p.check('input[value="gluten"]');
  await p.check('input[value="mit"]');
  await p.click('.chip:has-text("孕期")');
  await p.evaluate(() => window.scrollTo(0, 0));
  await p.waitForTimeout(200);
  await p.click('#dsSeg .seg-item[data-ds="gov"]');
  await p.waitForTimeout(500);
  await p.screenshot({ path: './screenshots/09-gov-data-mode.png', fullPage: true });
  // also a focused top-of-results crop
  const box = await p.locator('#resultBox').boundingBox();
  await p.screenshot({ path: './screenshots/09b-gov-top.png', clip: { x: box.x, y: box.y, width: box.width, height: Math.min(box.height, 900) } });
  console.log('gov shot done');
  await b.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
