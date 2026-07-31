import { test } from '@playwright/test';
import { navigateToPage } from '../../utils/app';

test('诊断系统管理页面结构', async ({ page }) => {
  await navigateToPage(page, '/system/user');
  
  console.log(`✅ 页面加载完成: ${page.url()}`);
  
  // 获取页面标题
  const title = await page.title();
  console.log(`📊 页面标题: ${title}`);
  
  // 查看页面结构 - 获取body的HTML
  const bodyHtml = await page.locator('body').innerHTML();
  console.log(`\n=== 页面body结构 (前8000字符) ===`);
  console.log(bodyHtml.substring(0, 8000));
  
  // 查找导航菜单
  const navItems = page.locator('.el-menu-item, .el-sub-menu, [router-link]');
  const navCount = await navItems.count();
  console.log(`\n📊 导航菜单数量: ${navCount}`);
  
  for (let i = 0; i < Math.min(navCount, 30); i++) {
    const nav = navItems.nth(i);
    const text = await nav.textContent();
    const className = await nav.evaluate(el => el.className);
    if (text && text.trim()) {
      console.log(`  导航${i}: text="${text.trim().substring(0, 50)}", class="${className}"`);
    }
  }
  
  // 查找表格
  const tables = page.locator('.el-table');
  const tableCount = await tables.count();
  console.log(`\n📊 表格数量: ${tableCount}`);
  
  if (tableCount > 0) {
    const headers = tables.first().locator('.el-table__header-wrapper th');
    const headerCount = await headers.count();
    console.log(`📊 表格列数: ${headerCount}`);
    
    for (let i = 0; i < headerCount; i++) {
      const header = headers.nth(i);
      const text = await header.textContent();
      console.log(`  列${i}: ${text ? text.trim() : ''}`);
    }
  }
});
