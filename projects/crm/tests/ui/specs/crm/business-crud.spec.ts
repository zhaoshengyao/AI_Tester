import { test, expect, Page } from '@playwright/test';
import { navigateToPage, getAuthToken } from '../../utils/app';
import { BusinessManagementPage } from '../../pages/BusinessManagementPage';
import { TestDataManager } from '../../utils/test-data-manager';

const BUSINESS_PAGE = '/business/BusinessOverview';

test.describe('商机管理 CRUD 测试', () => {
  let page: Page;
  let businessPage: BusinessManagementPage;
  let testDataManager: TestDataManager;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    businessPage = new BusinessManagementPage(page);
    const token = getAuthToken();
    testDataManager = new TestDataManager(process.env.API_BASE_URL, token);
    
    // 通过菜单导航到商机管理页面
    await page.goto('/index', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);
    
    // 展开商机管理子菜单
    const businessSubMenu = page.locator('.el-sub-menu__title').filter({ hasText: '商机管理' }).first();
    if ((await businessSubMenu.count()) > 0) {
      await businessSubMenu.click();
      await page.waitForTimeout(2000);
      
      // 点击商机总览链接
      const businessLink = page.locator('a[href="/business/BusinessOverview"]').first();
      if ((await businessLink.count()) > 0) {
        await businessLink.click();
        await page.waitForTimeout(5000);
        console.log(`✅ 通过菜单导航到商机总览: ${page.url()}`);
        return;
      }
    }
    
    // 备用方案：直接导航
    await navigateToPage(page, BUSINESS_PAGE);
    console.log(`✅ 导航到商机总览页面: ${page.url()}`);
  });

  test.afterEach(async () => {
    await testDataManager.cleanupCreatedData();
    await testDataManager.cleanupTestDataByPattern();
  });

  test('FUNC-BUSINESS-001 创建商机-填写完整信息', async () => {
    const businessData = testDataManager.loadTestData('business');
    const dialog = await businessPage.clickAddButton();
    await dialog.fillBusinessName(businessData.businessName);
    // 客户名留空，使用回退策略自动选择第一个可用客户
    await dialog.fillCustomerName('');
    await dialog.fillCompetitor('竞争对手A');
    await dialog.fillNextAction('跟进客户需求');
    await dialog.fillRemark('自动化测试创建');
    await dialog.submit();
    
    const toast = await businessPage.getToastMessage();
    expect(toast ?? '').toContain('成功');
    console.log('✅ 商机创建成功');
  });

  test('FUNC-BUSINESS-002 创建商机-必填字段校验', async () => {
    const dialog = await businessPage.clickAddButton();
    await dialog.submit();
    
    const toast = await businessPage.getToastMessage();
    expect(toast ?? '').toMatch(/不能为空|必填|请输入|请选择/);
    
    await dialog.close();
    console.log('✅ 必填字段校验生效');
  });

  test('FUNC-BUSINESS-003 查询商机列表-搜索功能', async () => {
    await businessPage.searchBusiness('测试');
    const count = await businessPage.getBusinessCount();
    console.log(`✅ 搜索结果数量: ${count}`);
  });

  test('FUNC-BUSINESS-004 查询商机列表-分页功能', async () => {
    await businessPage.goToPage(2);
  });

  test('FUNC-BUSINESS-005 查看商机详情', async () => {
    const count = await businessPage.getBusinessCount();
    if (count > 0) {
      await businessPage.clickBusinessRow(0);
      await page.waitForTimeout(2000);
      console.log('✅ 已点击第一条商机查看详情');
    }
  });
});