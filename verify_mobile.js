const { chromium } = require('C:/Users/Administrator/WorkBuddy/2026-10-23-13-18-57/node_modules/playwright');
const path = require('path');
(async () => {
  const url = 'file://' + path.resolve('docs/index.html');
  const b = await chromium.launch();
  const errors = [];
  for (const w of [320, 375, 390]) {
    const ctx = await b.newContext({ viewport: { width: w, height: 800 }, deviceScaleFactor: 2 });
    const p = await ctx.newPage();
    p.on('pageerror', e => errors.push(`w${w}: ${e.message}`));
    await p.goto(url, { waitUntil: 'networkidle' });
    await p.waitForTimeout(300);
    const overflow = await p.evaluate(() => {
      const sw = document.documentElement.scrollWidth;
      const iw = window.innerWidth;
      // also check the ds-toggle seg width vs card
      const seg = document.querySelector('#dsSeg');
      const card = document.querySelector('.results-col .card');
      const segRect = seg ? seg.getBoundingClientRect() : null;
      const cardRect = card ? card.getBoundingClientRect() : null;
      return { sw, iw, overflowX: sw - iw, segRight: segRect?Math.round(segRect.right):null, cardRight: cardRect?Math.round(cardRect.right):null };
    });
    // toggle to gov and back
    await p.click('#dsSeg .seg-item[data-ds="gov"]');
    await p.waitForTimeout(200);
    const govItems = await p.$$eval('#resultBox .item', e => e.length);
    const prov = await p.$$eval('#resultBox .prov', e => e.length);
    await p.click('#dsSeg .seg-item[data-ds="demo"]');
    await p.waitForTimeout(150);
    const demoItems = await p.$$eval('#resultBox .item', e => e.length);
    console.log(JSON.stringify({ w, ...overflow, govItems, prov, demoItems, govOverflowOK: overflow.overflowX <= 1 }));
    await ctx.close();
  }
  console.log('errors:', errors);
  await b.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
