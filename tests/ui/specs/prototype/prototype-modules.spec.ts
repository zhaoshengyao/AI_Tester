import { test } from '@playwright/test';

const menuItems = [
  { name: '工作台首页', url: '/#/workbench/sales' },
  { name: '我的待办', url: '/#/workbench/sales' },
  { name: '线索池', url: '/#/marketing/lead-pool' },
  { name: '我的线索', url: '/#/marketing/my-leads' },
  { name: '客户列表', url: '/#/customer/list' },
  { name: '公海池', url: '/#/customer/public-pool' },
  { name: '商机总览', url: '/#/business/overview' },
  { name: '报价单列表', url: '/#/quote/list' },
  { name: '产品列表', url: '/#/product/list' },
  { name: '目标管理', url: '/#/performance/target' },
  { name: '报表中心', url: '/#/report/center' },
];

test.describe('新原型功能模块详细分析', () => {
  for (const menu of menuItems) {
    test(`分析模块: ${menu.name}`, async ({ page }) => {
      try {
        await page.goto(menu.url, { timeout: 30000 });
        await page.waitForLoadState('networkidle', { timeout: 30000 });
        
        console.log(`\n=== ${menu.name} (${menu.url}) ===`);
        console.log('页面标题:', await page.title());
        console.log('当前URL:', page.url());
        
        const buttons = await page.locator('button').all();
        console.log('按钮数量:', buttons.length);
        const buttonTexts: string[] = [];
        for (let i = 0; i < Math.min(15, buttons.length); i++) {
          const text = await buttons[i].textContent();
          const className = await buttons[i].getAttribute('class');
          if (text && text.trim()) {
            buttonTexts.push(text.trim());
          }
        }
        console.log('按钮文本:', buttonTexts.join(', '));
        
        const tables = await page.locator('table, .el-table').all();
        console.log('表格数量:', tables.length);
        
        const forms = await page.locator('.el-form, form').all();
        console.log('表单数量:', forms.length);
        
        const inputs = await page.locator('.el-input').all();
        console.log('输入框数量:', inputs.length);
        
        const selects = await page.locator('.el-select').all();
        console.log('下拉框数量:', selects.length);
        
        const dialogs = await page.locator('.el-dialog').all();
        console.log('弹窗数量:', dialogs.length);
        
        const cards = await page.locator('.card, .el-card').all();
        console.log('卡片数量:', cards.length);
        
        const pageTexts = await page.locator('body *').allTextContents();
        const uniqueTexts = [...new Set(pageTexts.filter(t => t.trim().length > 3 && t.trim().length < 50))].slice(0, 30);
        console.log('页面关键词:', uniqueTexts.join(', '));
        
        await page.screenshot({ path: `d:\\AICode\\TestHub\\AITestDemo\\tests\\ui\\prototype-${menu.name.replace(/\s/g, '')}.png`, fullPage: true });
        
      } catch (error) {
        console.log(`❌ 分析 ${menu.name} 失败: ${(error as Error).message}`);
      }
    });
  }
  
  test('分析角色切换功能', async ({ page }) => {
    await page.goto('http://localhost:5173/#/workbench/sales', { timeout: 30000 });
    await page.waitForLoadState('networkidle', { timeout: 30000 });
    
    console.log('\n=== 角色切换功能分析 ===');
    
    const userMenu = page.locator('.user-menu, .avatar, .user-info').first();
    if (await userMenu.count() > 0) {
      console.log('用户菜单存在');
    }
    
    const roleSwitch = page.locator('button', { hasText: '切换角色' });
    if (await roleSwitch.count() > 0) {
      console.log('切换角色按钮存在');
      await roleSwitch.click();
      await page.waitForTimeout(2000);
      
      const roles = await page.locator('.el-dropdown-menu__item, .role-item').all();
      console.log('可用角色数量:', roles.length);
      for (let i = 0; i < roles.length; i++) {
        const text = await roles[i].textContent();
        console.log(`角色${i}: ${text || ''}`);
      }
    }
    
    await page.screenshot({ path: 'd:\\AICode\\TestHub\\AITestDemo\\tests\\ui\\prototype-roles.png' });
  });
  
  test('分析销售漏斗组件', async ({ page }) => {
    await page.goto('http://localhost:5173/#/workbench/sales', { timeout: 30000 });
    await page.waitForLoadState('networkidle', { timeout: 30000 });
    
    console.log('\n=== 销售漏斗分析 ===');
    
    const funnel = page.locator('.funnel, .sales-funnel, .el-chart').first();
    if (await funnel.count() > 0) {
      console.log('销售漏斗组件存在');
    }
    
    const funnelItems = await page.locator('.funnel-item, .stage-item').all();
    console.log('漏斗阶段数量:', funnelItems.length);
    for (let i = 0; i < funnelItems.length; i++) {
      const text = await funnelItems[i].textContent();
      console.log(`阶段${i}: ${text || ''}`);
    }
    
    await page.screenshot({ path: 'd:\\AICode\\TestHub\\AITestDemo\\tests\\ui\\prototype-funnel.png' });
  });
});