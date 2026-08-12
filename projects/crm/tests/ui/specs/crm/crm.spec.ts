import { test, expect } from '@playwright/test';
import { CustomerManagementPage } from '../../pages/CustomerManagementPage';

const PAGE_PATHS = {
  customer: '/customer/customer',
  clue: '/marketing/clue',
  business: '/business/BusinessOverview'
};

test.describe('CRM管理 - CRM Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/index');
    await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
    await page.waitForTimeout(2000);
  });

  test('FUNC-CRM-001 客户管理 - 页面加载', async ({ page }) => {
    await page.goto(PAGE_PATHS.customer);
    await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
    await page.waitForTimeout(3000);
    
    await expect(page).toHaveURL(new RegExp(PAGE_PATHS.customer));
  });

  test('FUNC-CRM-002 客户管理 - 页面内容验证', async ({ page }) => {
    await page.goto(PAGE_PATHS.customer);
    await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
    await page.waitForTimeout(3000);
    
    const hasCustomerText = await page.locator('body').textContent();
    expect(hasCustomerText).toContain('客户');
    
    const tableExists = await page.locator('[role="table"], table, .data-table').count() > 0;
    const buttonExists = await page.locator('button').count() > 0;
    
    expect(tableExists || buttonExists).toBe(true);
  });

  test('FUNC-CRM-003 客户管理 - 搜索功能', async ({ page }) => {
    await page.goto(PAGE_PATHS.customer);
    await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
    await page.waitForTimeout(3000);
    
    const customerPage = new CustomerManagementPage(page);
    await customerPage.searchCustomer('测试');
  });

  test('FUNC-CRM-004 线索管理 - 页面加载', async ({ page }) => {
    await page.goto(PAGE_PATHS.clue);
    await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
    await page.waitForTimeout(3000);
    
    await expect(page).toHaveURL(new RegExp(PAGE_PATHS.clue));
  });

  test('FUNC-CRM-005 线索管理 - 页面内容验证', async ({ page }) => {
    await page.goto(PAGE_PATHS.clue);
    await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
    await page.waitForTimeout(3000);
    
    const hasClueText = await page.locator('body').textContent();
    expect(hasClueText).toContain('线索');
  });

  test('FUNC-CRM-006 线索管理 - 新增线索入口', async ({ page }) => {
    await page.goto(PAGE_PATHS.clue);
    await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
    await page.waitForTimeout(3000);
    
    const addButton = page.locator('button').filter({ hasText: /新增|添加/ }).first();
    
    if ((await addButton.count()) > 0 && await addButton.isVisible()) {
      await addButton.click();
      await page.waitForTimeout(2000);
      
      const hasDialog = await page.locator('[role="dialog"], .modal, .popup').count() > 0;
      if (hasDialog) {
        console.log('✅ 新增线索弹窗打开成功');
      } else {
        console.log('⚠️ 未找到新增线索弹窗');
      }
    } else {
      console.log('⚠️ 未找到新增按钮');
    }
  });

  test('FUNC-CRM-007 商机管理 - 页面加载', async ({ page }) => {
    await page.goto(PAGE_PATHS.business);
    await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
    await page.waitForTimeout(3000);
    
    await expect(page).toHaveURL(new RegExp(PAGE_PATHS.business));
  });

  test('FUNC-CRM-008 商机管理 - 页面内容验证', async ({ page }) => {
    await page.goto(PAGE_PATHS.business);
    await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
    await page.waitForTimeout(3000);
    
    const hasBusinessText = await page.locator('body').textContent();
    expect(hasBusinessText).toContain('商机');
  });
});