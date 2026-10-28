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

  // 直接调用页面内的 analyzeCombinations（含修复后的 DRUG_INTERACTIONS + _drugMatch）
  // 用真实数据中的中文成分关键词构建 5 个相互作用药品
  const warns = await page.evaluate(() => {
    const evs = [
      { it: { id: 'ibu', name: '布洛芬缓释胶囊', cat: 'drug', comp: ['布洛芬', '淀粉'], contra: [] } },
      { it: { id: 'lev', name: '左氧氟沙星片', cat: 'drug', comp: ['左氧氟沙星'], contra: [] } },
      { it: { id: 'asp', name: '阿司匹林肠溶片', cat: 'drug', comp: ['阿司匹林', '淀粉'], contra: [] } },
      { it: { id: 'ery', name: '红霉素软膏', cat: 'drug', comp: ['红霉素'], contra: [] } },
      { it: { id: 'cal', name: '碳酸钙D3片', cat: 'drug', comp: ['碳酸钙', '维生素D3'], contra: [] } },
    ];
    const prof = { conds: [] };
    return analyzeCombinations(evs, prof).map(w => ({ level: w.level, title: w.title }));
  });

  const expected = ['阿司匹林 + 布洛芬', '左氧氟沙星 + 布洛芬', '左氧氟沙星 + 阿司匹林', '钙剂 + 左氧氟沙星', '钙剂 + 红霉素'];
  const got = warns.map(w => w.title.replace('药品相互作用：', ''));
  const missing = expected.filter(e => !got.includes(e));

  console.log(JSON.stringify({
    errors,
    warnings: warns,
    missing,
    result: missing.length === 0 && warns.length === expected.length ? 'PASS' : 'FAIL'
  }, null, 2));

  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
