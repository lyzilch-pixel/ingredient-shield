const { chromium } = require('C:/Users/Administrator/WorkBuddy/2026-10-23-13-18-57/node_modules/playwright');
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 375, height: 760 }, deviceScaleFactor: 2, isMobile: true });
  const p = await ctx.newPage();
  await p.goto('https://lyzilch-pixel.github.io/ingredient-shield/', { waitUntil: 'networkidle' });
  await p.waitForTimeout(500);
  await p.click('#dsSeg .seg-item[data-ds="gov"]');
  await p.waitForTimeout(400);
  const card = await p.locator('.results-col .card:has(#dsSeg)');
  await card.scrollIntoViewIfNeeded();
  await p.waitForTimeout(200);
  await card.screenshot({ path: './screenshots/08c-mobile-dsclip.png' });
  console.log('clip done');
  await b.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
