import { test } from '@playwright/test';

test('深度分析CRM页面结构', async ({ page }) => {
  await page.goto('/customer/customer');
  await page.waitForLoadState('domcontentloaded');
  await page.waitForTimeout(3000);
  
  await page.waitForLoadState('domcontentloaded');
  await page.waitForTimeout(3000);
  
  console.log('=== 页面结构分析 ===');
  console.log('页面URL:', page.url());
  console.log('页面标题:', await page.title());
  
  console.log('\n=== 容器元素 ===');
  console.log('.app-container:', await page.locator('.app-container').count());
  console.log('.main-container:', await page.locator('.main-container').count());
  console.log('.content:', await page.locator('.content').count());
  
  console.log('\n=== 按钮元素 ===');
  console.log('.el-button:', await page.locator('.el-button').count());
  const buttons = await page.locator('.el-button').all();
  for (let i = 0; i < Math.min(5, buttons.length); i++) {
    const text = await buttons[i].textContent();
    console.log(`按钮${i}: "${text}"`);
  }
  
  console.log('\n=== 数据展示区域 ===');
  console.log('table:', await page.locator('table').count());
  console.log('.el-table:', await page.locator('.el-table').count());
  console.log('.table:', await page.locator('.table').count());
  console.log('.list:', await page.locator('.list').count());
  console.log('.card:', await page.locator('.card').count());
  
  console.log('\n=== 布局组件 ===');
  console.log('.el-container:', await page.locator('.el-container').count());
  console.log('.el-row:', await page.locator('.el-row').count());
  console.log('.el-col:', await page.locator('.el-col').count());
  
  console.log('\n=== 搜索区域 ===');
  console.log('.el-input:', await page.locator('.el-input').count());
  console.log('.search-form:', await page.locator('.search-form').count());
  
  await page.screenshot({ path: 'd:\\AICode\\TestHub\\AITestDemo\\tests\\ui\\crm-page-analysis.png' });
  console.log('\n截图已保存');
});