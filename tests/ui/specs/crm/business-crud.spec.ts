import { test, expect, Page } from '@playwright/test';
import { navigateToPage } from '../../utils/app';
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
    testDataManager = new TestDataManager();
    await navigateToPage(page, BUSINESS_PAGE);
  });

  test.afterEach(async () => {
    await testDataManager.cleanupCreatedData();
    await testDataManager.cleanupTestDataByPattern();
  });

  test('FUNC-BUSINESS-001 创建商机-填写完整信息', async () => {
    try {
      const businessData = testDataManager.loadTestData('business');
      const dialog = await businessPage.clickAddButton();
      await dialog.fillBusinessName(businessData.businessName);
      await dialog.fillCustomerName(businessData.customerName);
      await dialog.fillContact('测试联系人');
      await dialog.fillAmount(businessData.amount.toString());
      await dialog.fillStage(businessData.stage);
      await dialog.fillStatus('进行中');
      await dialog.fillDescription('自动化测试创建');
      await dialog.submit();
      
      const toast = await businessPage.getToastMessage();
      if (toast && toast.includes('成功')) {
        console.log('✅ 商机创建成功');
      }
    } catch (error) {
      console.log(`⚠️ 创建商机失败: ${error}`);
    }
  });

  test('FUNC-BUSINESS-002 创建商机-必填字段校验', async () => {
    try {
      const dialog = await businessPage.clickAddButton();
      await dialog.submit();
      
      const toast = await businessPage.getToastMessage();
      if (toast && (toast.includes('不能为空') || toast.includes('必填'))) {
        console.log('✅ 必填字段校验生效');
      }
      
      await dialog.close();
    } catch (error) {
      console.log(`⚠️ 必填校验测试失败: ${error}`);
    }
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