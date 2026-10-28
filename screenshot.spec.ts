import { test, expect } from '@playwright/test';

const BASE_URL = 'https://lyzilch-pixel.github.io/ingredient-shield/';
const OUT_DIR = './screenshots';

test.describe.configure({ retries: 0 });

test('screenshot all required states for 1024 submission', async ({ page }) => {
  // 1. 首页 + 免责声明
  await page.goto(BASE_URL, { waitUntil: 'networkidle' });
  await page.screenshot({ path: `${OUT_DIR}/01-home-disclaimer.png`, fullPage: false });

  // 2. 安全画像配置：勾选花生+麸质（食品）、MIT+香精（日化）、孕期（健康状态）
  // 食品过敏原
  await page.check('input[value="peanuts"]');
  await page.check('input[value="gluten"]');
  // 日化风险物质
  await page.check('input[value="mit"]');
  await page.check('input[value="fragrance"]');
  // 健康状态：孕期
  await page.click('.chip:has-text("孕期")');
  await page.screenshot({ path: `${OUT_DIR}/02-profile-configured.png`, fullPage: false });

  // 3. 食品 Tab 分析结果（默认就是食品）
  await page.screenshot({ path: `${OUT_DIR}/03-food-tab-results.png`, fullPage: true });

  // 4. 日化个护 Tab
  await page.click('.tab[data-cat="daily_chem"]');
  await page.waitForTimeout(300);
  await page.screenshot({ path: `${OUT_DIR}/04-daily-chem-tab.png`, fullPage: true });

  // 5. 药品 Tab
  await page.click('.tab[data-cat="drug"]');
  await page.waitForTimeout(300);
  await page.screenshot({ path: `${OUT_DIR}/05-drug-tab.png`, fullPage: true });

  // 6. 跨品类召回预警（往上滚一点看预警卡）
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(200);
  await page.screenshot({ path: `${OUT_DIR}/06-alerts-banner.png`, fullPage: false });

  // 7. 生成分享卡
  await page.click('#genBtn');
  await page.waitForTimeout(1500); // 等待 canvas 渲染
  // 截取 canvas 区域
  const canvas = page.locator('#shareCanvas');
  await expect(canvas).toBeVisible();
  await canvas.screenshot({ path: `${OUT_DIR}/07-share-card.png` });

  // 8. 手机视图（375×667）
  await page.setViewportSize({ width: 375, height: 667 });
  await page.goto(BASE_URL, { waitUntil: 'networkidle' });
  await page.check('input[value="peanuts"]');
  await page.check('input[value="mit"]');
  await page.click('.chip:has-text("孕期")');
  await page.screenshot({ path: `${OUT_DIR}/08-mobile-view.png`, fullPage: true });

  // 9. 引擎/数据目录（GitHub 仓库页）
  await page.goto('https://github.com/lyzilch-pixel/ingredient-shield', { waitUntil: 'networkidle' });
  await page.screenshot({ path: `${OUT_DIR}/09-github-repo.png`, fullPage: true });
});

test.afterAll(async () => {
  console.log('Screenshots saved to', OUT_DIR);
});