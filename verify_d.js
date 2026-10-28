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

  // 直接在页面评估 evaluate() 的日化浓度分级
  const cases = await page.evaluate(() => {
    const res = [];
    // 1. 有浓度声明 formaldehyde_releaser: 0.15% -> warn 阈值(0.05%) < 0.15% < high(0.2%) -> "风险物质(浓度 0.15%≥0.05%): 甲醛释放体"
    const it1 = { cat: 'daily_chem', comp: ['水','甘油','甲基异噻唑啉酮','dmdm乙内酰脲'], conc: { formaldehyde_releaser: 0.15 } };
    const a1 = analyzeItem(it1);
    const r1 = evaluate(it1, {ids:[],conds:[],cons:{}});
    res.push({name:'婴儿手口湿巾', reasons:r1.reasons});

    // 2. 无浓度声明 -> "风险物质(浓度未标注): 氧苯酮" 等
    const it2 = { cat: 'daily_chem', comp: ['水','氧苯酮','香精'] };
    const a2 = analyzeItem(it2);
    const r2 = evaluate(it2, {ids:[],conds:[],cons:{}});
    res.push({name:'防晒喷雾', reasons:r2.reasons});

    // 3. 高浓度 coal_tar: 2.0% >= high(1.0%) -> "高风险物质(浓度 2%≥1%): 煤焦油/染发剂"
    const it3 = { cat: 'daily_chem', comp: ['水','对苯二胺','煤焦油','香精'], conc: { coal_tar: 2.0 } };
    const a3 = analyzeItem(it3);
    const r3 = evaluate(it3, {ids:[],conds:[],cons:{}});
    res.push({name:'染发剂', reasons:r3.reasons});

    return res;
  });

  console.log(JSON.stringify({errors, cases}, null, 2));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });