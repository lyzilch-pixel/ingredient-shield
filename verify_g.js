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

  // 1. 初始状态：localStorage 为空，重置按钮存在
  const resetBtn = await page.$('#btnResetProfile');
  console.log('resetBtn exists:', !!resetBtn);

  // 2. 勾选几项画像（花生过敏 + 孕期 + 钠上限 1000）
  await page.evaluate(() => {
    // 清空旧数据
    localStorage.removeItem('is_profile');
    // 模拟用户操作
    document.querySelector('#foodGrid input[value="peanuts"]').checked = true;
    document.querySelector('#condChips .chip[data-id="pregnancy"]').click();
    document.getElementById('cSodium').value = '1000';
    // 触发保存
    getProfile(); // 这会调用 saveProfile
  });
  await page.waitForTimeout(200);

  // 3. 验证 localStorage 已保存
  const stored = await page.evaluate(() => localStorage.getItem('is_profile'));
  console.log('stored after interaction:', stored);
  const parsed = stored ? JSON.parse(stored) : null;
  console.log('parsed profile:', parsed);

  // 4. 刷新页面，验证画像自动恢复
  await page.reload({ waitUntil: 'networkidle' });
  await page.waitForTimeout(300);
  const restored = await page.evaluate(() => {
    const checks = [...document.querySelectorAll('#foodGrid input:checked')].map(c=>c.value);
    const conds = [...document.querySelectorAll('#condChips .chip.on')].map(c=>c.dataset.id);
    const sodium = document.getElementById('cSodium').value;
    return {checks, conds, sodium};
  });
  console.log('restored after reload:', restored);

  // 5. 点击重置按钮，验证清空
  await page.click('#btnResetProfile');
  await page.waitForTimeout(300);
  const afterReset = await page.evaluate(() => {
    const checks = [...document.querySelectorAll('#foodGrid input:checked')].map(c=>c.value);
    const conds = [...document.querySelectorAll('#condChips .chip.on')].map(c=>c.dataset.id);
    const sodium = document.getElementById('cSodium').value;
    return {checks, conds, sodium, stored: localStorage.getItem('is_profile')};
  });
  console.log('after reset:', afterReset);

  console.log(JSON.stringify({errors, restored, afterReset}, null, 2));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });