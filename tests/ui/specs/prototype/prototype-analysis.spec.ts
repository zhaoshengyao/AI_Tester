import { test } from '@playwright/test';

test.describe.configure({ mode: 'parallel' });

test('分析新原型页面结构', async ({ page }) => {
  await page.goto('http://localhost:5173/', { timeout: 30000 });
  await page.waitForLoadState('networkidle', { timeout: 30000 });
  
  console.log('=== 页面基本信息 ===');
  console.log('页面URL:', page.url());
  console.log('页面标题:', await page.title());
  console.log('页面内容长度:', (await page.content()).length);
  
  console.log('\n=== 页面结构分析 ===');
  console.log('body子元素数量:', await page.locator('body > *').count());
  
  console.log('\n=== 导航菜单分析 ===');
  const menus = await page.locator('.el-menu-item, .menu-title, .nav-item, [role="menuitem"], li a').all();
  console.log('菜单项数量:', menus.length);
  for (let i = 0; i < Math.min(15, menus.length); i++) {
    const text = await menus[i].textContent();
    const tagName = await menus[i].evaluate(el => el.tagName);
    const href = await menus[i].getAttribute('href');
    console.log(`菜单${i}: "${text || ''}" [${tagName}] href=${href || ''}`);
  }
  
  console.log('\n=== 容器元素 ===');
  const containers = ['.app-container', '.main-container', '.content', '.layout', '.container'];
  for (const container of containers) {
    const count = await page.locator(container).count();
    if (count > 0) {
      console.log(`${container}: ${count}`);
    }
  }
  
  console.log('\n=== 按钮元素 ===');
  const buttons = await page.locator('button').all();
  console.log('按钮总数:', buttons.length);
  for (let i = 0; i < Math.min(10, buttons.length); i++) {
    const text = await buttons[i].textContent();
    const className = await buttons[i].getAttribute('class');
    console.log(`按钮${i}: "${text || ''}" class="${className || ''}"`);
  }
  
  console.log('\n=== 数据展示区域 ===');
  const dataElements = ['table', '.el-table', '.table', '.list', '.card', '.grid'];
  for (const el of dataElements) {
    const count = await page.locator(el).count();
    if (count > 0) {
      console.log(`${el}: ${count}`);
    }
  }
  
  console.log('\n=== 表单元素 ===');
  const formElements = ['.el-form', 'form', '.el-input', '.el-select', '.el-date-picker'];
  for (const el of formElements) {
    const count = await page.locator(el).count();
    if (count > 0) {
      console.log(`${el}: ${count}`);
    }
  }
  
  console.log('\n=== 页面截图 ===');
  await page.screenshot({ path: 'prototype-analysis.png', fullPage: true });
  
  console.log('\n=== 页面HTML (前5000字符) ===');
  const html = await page.content();
  console.log(html.substring(0, 5000));
});

test('检查原型登录页面', async ({ page }) => {
  await page.goto('http://localhost:5173/', { timeout: 30000 });
  await page.waitForLoadState('networkidle', { timeout: 30000 });
  
  console.log('=== 登录页面分析 ===');
  
  const usernameInput = page.locator('input[type="text"], input[placeholder*="用户名"], input[placeholder*="账号"]').first();
  const passwordInput = page.locator('input[type="password"], input[placeholder*="密码"]').first();
  const loginButton = page.locator('button').filter({ hasText: /登录|Login/ }).first();
  
  console.log('用户名输入框存在:', await usernameInput.count() > 0);
  console.log('密码输入框存在:', await passwordInput.count() > 0);
  console.log('登录按钮存在:', await loginButton.count() > 0);
  
  if (await loginButton.count() > 0) {
    const btnText = await loginButton.textContent();
    console.log('登录按钮文本:', btnText);
  }
  
  const pageContent = await page.content();
  if (pageContent.includes('login') || pageContent.includes('username') || pageContent.includes('password')) {
    console.log('✅ 检测到登录相关内容');
  }
  
  await page.screenshot({ path: 'prototype-login.png' });
});

test('获取原型所有可见文本', async ({ page }) => {
  await page.goto('http://localhost:5173/', { timeout: 30000 });
  await page.waitForLoadState('networkidle', { timeout: 30000 });
  
  console.log('=== 页面可见文本 ===');
  const allTexts = await page.locator('body *').allTextContents();
  const uniqueTexts = [...new Set(allTexts.filter(t => t.trim().length > 2))];
  
  console.log('可见文本数量:', uniqueTexts.length);
  console.log('--- 文本列表 ---');
  for (const text of uniqueTexts) {
    console.log(`"${text.trim()}"`);
  }
});