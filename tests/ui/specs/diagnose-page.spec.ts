import { test } from '@playwright/test';

test('诊断登录后页面结构', async ({ page }) => {
  await page.goto('/index');
  await page.waitForLoadState('domcontentloaded');
  await page.waitForTimeout(3000);
  
  console.log('=== 页面诊断 ===');
  console.log('当前URL:', page.url());
  console.log('页面标题:', await page.title());
  
  console.log('\n=== 页面内容 ===');
  const htmlContent = await page.content();
  console.log('页面长度:', htmlContent.length);
  
  console.log('\n=== 查找CRM相关元素 ===');
  const crmElements = await page.locator('text=CRM').count();
  console.log('CRM文本出现次数:', crmElements);
  
  const menuItems = await page.locator('.el-menu-item, .menu-title, [class*="menu"]').count();
  console.log('菜单元素数量:', menuItems);
  
  const allButtons = await page.locator('button').count();
  console.log('按钮元素数量:', allButtons);
  
  const divs = await page.locator('div').count();
  console.log('div元素数量:', divs);
  
  console.log('\n=== 获取所有文本内容 ===');
  const bodyText = await page.locator('body').textContent();
  if (bodyText) {
    const textPreview = bodyText.substring(0, 2000);
    console.log(textPreview);
  }
  
  await page.screenshot({ path: 'd:\\AICode\\TestHub\\AITestDemo\\tests\\ui\\diagnose-screenshot.png' });
  console.log('\n截图已保存');
});