import { test, expect } from '@playwright/test';

const PAGE_PATHS = {
  home: '/index',
  customer: '/customer/customer',
  clue: '/marketing/clue',
  business: '/business/BusinessOverview',
  quotation: '/quotation/quotationList',
  product: '/product/ProductList',
  report: '/report'
};

test.describe('CRM系统冒烟测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/index');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);
  });

  test('SMOKE-001 登录成功验证', async ({ page }) => {
    console.log('当前URL:', page.url());
    expect(page.url()).toContain('/index');
  });

  test('SMOKE-002 客户管理页面可达', async ({ page }) => {
    await page.goto(PAGE_PATHS.customer);
    await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
    await page.waitForTimeout(3000);
    
    console.log('客户管理页面URL:', page.url());
    expect(page.url()).toContain(PAGE_PATHS.customer);
    
    await expect(page.locator('body')).toHaveText(/客户/);
  });

  test('SMOKE-003 线索管理页面可达', async ({ page }) => {
    await page.goto(PAGE_PATHS.clue);
    await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
    await page.waitForTimeout(3000);
    
    console.log('线索管理页面URL:', page.url());
    expect(page.url()).toContain(PAGE_PATHS.clue);
    
    await expect(page.locator('body')).toHaveText(/线索/);
  });

  test('SMOKE-004 商机管理页面可达', async ({ page }) => {
    await page.goto(PAGE_PATHS.business);
    await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
    await page.waitForTimeout(3000);
    
    console.log('商机管理页面URL:', page.url());
    expect(page.url()).toContain(PAGE_PATHS.business);
  });

  test('SMOKE-005 报价管理页面可达', async ({ page }) => {
    await page.goto(PAGE_PATHS.quotation);
    await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
    await page.waitForTimeout(3000);
    
    console.log('报价管理页面URL:', page.url());
    expect(page.url()).toContain(PAGE_PATHS.quotation);
    
    await expect(page.locator('body')).toHaveText(/报价/);
  });

  test('SMOKE-006 产品管理页面可达', async ({ page }) => {
    await page.goto(PAGE_PATHS.product);
    await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
    await page.waitForTimeout(3000);
    
    console.log('产品管理页面URL:', page.url());
    expect(page.url()).toContain(PAGE_PATHS.product);
    
    await expect(page.locator('body')).toHaveText(/产品/);
  });

  test('SMOKE-007 报表页面可达', async ({ page }) => {
    await page.goto(PAGE_PATHS.report);
    await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
    await page.waitForTimeout(3000);
    
    console.log('报表页面URL:', page.url());
    expect(page.url()).toContain(PAGE_PATHS.report);
  });
});