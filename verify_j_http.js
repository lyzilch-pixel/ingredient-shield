const { chromium } = require('C:/Users/Administrator/WorkBuddy/2026-10-23-13-18-57/node_modules/playwright');
const path = require('path');

(async () => {
  // 对接运行中的 HTTP 服务器 (port 8137)
  const fileUrl = 'http://localhost:8137/';
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 1000 } });
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));

  await page.goto(fileUrl, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000); // 等待 loadAlerts/loadGov 完成

  // 验证 ALERTS 已加载且渲染正确
  const results = await page.evaluate(() => {
    const box = document.getElementById('alertBox');
    return {
      html: box.innerHTML,
      alertsCount: ALERTS.length,
      meta: ALERTS_META,
    };
  });

  console.log(JSON.stringify({errors, results}, null, 2));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });