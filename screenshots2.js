const { chromium } = require('C:/Users/Administrator/WorkBuddy/2026-10-23-13-18-57/node_modules/playwright');
const fs = require('fs');

const BASE_URL = 'https://lyzilch-pixel.github.io/ingredient-shield/';
const OUT = './screenshots';
if (!fs.existsSync(OUT)) fs.mkdirSync(OUT, { recursive: true });

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 1000 }, deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  await page.goto(BASE_URL, { waitUntil: 'networkidle' });
  await page.waitForTimeout(400);

  // 01 home + disclaimer
  await page.screenshot({ path: `${OUT}/01-home-disclaimer.png` });

  // 02 profile configured
  await page.check('input[value="peanuts"]');
  await page.check('input[value="gluten"]');
  await page.check('input[value="mit"]');
  await page.check('input[value="fragrance"]');
  await page.click('.chip:has-text("孕期")');
  await page.screenshot({ path: `${OUT}/02-profile-configured.png` });

  // 03 food results (full)
  await page.screenshot({ path: `${OUT}/03-food-tab-results.png`, fullPage: true });

  // 04 daily_chem
  await page.click('.tab[data-cat="daily_chem"]');
  await page.waitForTimeout(300);
  await page.screenshot({ path: `${OUT}/04-daily-chem-tab.png`, fullPage: true });

  // 05 drug
  await page.click('.tab[data-cat="drug"]');
  await page.waitForTimeout(300);
  await page.screenshot({ path: `${OUT}/05-drug-tab.png`, fullPage: true });

  // 06 alerts banner
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(200);
  await page.screenshot({ path: `${OUT}/06-alerts-banner.png` });

  // 07 share card
  await page.click('#genBtn');
  await page.waitForTimeout(1500);
  await page.locator('#shareCanvas').screenshot({ path: `${OUT}/07-share-card.png` });

  // 08 mobile
  const m = await ctx.newPage();
  await m.setViewportSize({ width: 375, height: 667 });
  await m.goto(BASE_URL, { waitUntil: 'networkidle' });
  await m.check('input[value="peanuts"]');
  await m.check('input[value="mit"]');
  await m.click('.chip:has-text("孕期")');
  await m.waitForTimeout(300);
  await m.screenshot({ path: `${OUT}/08-mobile-view.png`, fullPage: true });

  // 09 gov public-data mode (showing toggle + provenance)
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(200);
  await page.click('#dsSeg .seg-item[data-ds="gov"]');
  await page.waitForTimeout(400);
  await page.screenshot({ path: `${OUT}/09-gov-data-mode.png`, fullPage: true });

  // 10 github repo
  const g = await ctx.newPage();
  await g.goto('https://github.com/lyzilch-pixel/ingredient-shield', { waitUntil: 'networkidle' });
  await g.waitForTimeout(800);
  await g.screenshot({ path: `${OUT}/10-github-repo.png`, fullPage: true });

  console.log('done');
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
