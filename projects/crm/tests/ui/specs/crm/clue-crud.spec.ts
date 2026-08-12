import { test, expect, Page } from '@playwright/test';
import { getAuthToken } from '../../utils/app';
import { ClueManagementPage } from '../../pages/ClueManagementPage';
import { TestDataManager } from '../../utils/test-data-manager';

test.describe('线索管理 CRUD 测试', () => {
  let page: Page;
  let cluePage: ClueManagementPage;
  let testDataManager: TestDataManager;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    cluePage = new ClueManagementPage(page);
    const token = getAuthToken();
    testDataManager = new TestDataManager(process.env.API_BASE_URL, token);
    await cluePage.navigate();
  });

  test.afterEach(async () => {
    await testDataManager.cleanupCreatedData();
    await testDataManager.cleanupTestDataByPattern();
  });

  test('FUNC-CLUE-001 创建线索-填写完整信息', async () => {
    const clueData = testDataManager.loadTestData('clue');
    void clueData;
    const dialog = await cluePage.clickAddButton();
    await dialog.fillClueName('测试联系人');
    await dialog.fillCustomerName('测试公司');
    await dialog.fillSource('广告'); // 使用实际存在的选项
    await dialog.fillDepartment('技术部');
    await dialog.fillPosition('工程师');
    await dialog.fillPhone('13800138000');
    await dialog.fillMobile('13900139000');
    await dialog.fillEmail('test@test.com');
    await dialog.fillOwner('赵生尧'); // 负责人需要搜索+下拉选择
    await dialog.fillIndustry('IT/互联网'); // 使用实际存在的选项
    await dialog.submit();
    
    const toast = await cluePage.getToastMessage();
    console.log(`📊 Toast消息: ${toast}`);
    expect(toast ?? '').toContain('成功');
    console.log('✅ 线索创建成功');
  });

  test('FUNC-CLUE-002 创建线索-必填字段校验', async () => {
    const dialog = await cluePage.clickAddButton();
    await dialog.submit();
    
    const toast = await cluePage.getToastMessage();
    console.log(`📊 Toast消息: ${toast}`);
    expect(toast ?? '').toMatch(/不能为空|必填|请输入|请选择|错误|失败/);
    
    await dialog.close();
    console.log('✅ 必填字段校验生效');
  });

  test('FUNC-CLUE-003 查询线索列表-搜索功能', async () => {
    await cluePage.searchClue('测试');
    const count = await cluePage.getClueCount();
    console.log(`✅ 搜索结果数量: ${count}`);
  });

  test('FUNC-CLUE-004 查询线索列表-分页功能', async () => {
    await cluePage.goToPage(2);
  });

  test('FUNC-CLUE-005 查看线索详情', async () => {
    const count = await cluePage.getClueCount();
    if (count > 0) {
      await cluePage.clickClueRow(0);
      await page.waitForTimeout(2000);
      console.log('✅ 已点击第一条线索查看详情');
    }
  });
});
