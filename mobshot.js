const { chromium } = require('C:/Users/Administrator/WorkBuddy/2026-10-23-13-18-57/node_modules/playwright');
const BASE = 'https://lyzilch-pixel.github.io/ingredient-shield/';
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 375, height: 720 }, deviceScaleFactor: 2, isMobile: true });
  const p = await ctx.newPage();
  await p.goto(BASE, { waitUntil: 'networkidle' });
  await p.waitForTimeout(500);
  await p.check('input[value="peanuts"]');
  await p.check('input[value="mit"]');
  await p.click('.chip:has-text("孕期")');
  await p.waitForTimeout(300);
  await p.screenshot({ path: './screenshots/08-mobile-view.png', fullPage: true });
  // mobile gov mode
  await p.click('#dsSeg .seg-item[data-ds="gov"]');
  await p.waitForTimeout(400);
  await p.screenshot({ path: './screenshots/08b-mobile-gov.png', fullPage: true });
  console.log('mobile shots done');
  await b.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
