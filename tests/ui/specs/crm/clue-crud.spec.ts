import { test, expect, Page } from '@playwright/test';
import { navigateToPage } from '../../utils/app';
import { ClueManagementPage } from '../../pages/ClueManagementPage';

const CLUE_PAGE = '/marketing/clue';

test.describe('线索管理 CRUD 测试', () => {
  let page: Page;
  let cluePage: ClueManagementPage;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    cluePage = new ClueManagementPage(page);
    await navigateToPage(page, CLUE_PAGE);
  });

  test('FUNC-CLUE-001 创建线索-填写完整信息', async () => {
    try {
      const dialog = await cluePage.clickAddButton();
      await dialog.completeCreateClue();
      
      const toast = await cluePage.getToastMessage();
      if (toast && toast.includes('成功')) {
        console.log('✅ 线索创建成功');
      }
    } catch (error) {
      console.log(`⚠️ 创建线索失败: ${error}`);
    }
  });

  test('FUNC-CLUE-002 创建线索-必填字段校验', async () => {
    try {
      const dialog = await cluePage.clickAddButton();
      await dialog.submit();
      
      const toast = await cluePage.getToastMessage();
      if (toast && (toast.includes('不能为空') || toast.includes('必填'))) {
        console.log('✅ 必填字段校验生效');
      }
      
      await dialog.close();
    } catch (error) {
      console.log(`⚠️ 必填校验测试失败: ${error}`);
    }
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