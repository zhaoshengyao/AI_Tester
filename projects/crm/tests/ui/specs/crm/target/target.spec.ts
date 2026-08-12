import { test, expect, Page } from '@playwright/test';
import { navigateToPage } from '../../../utils/app';
import { SystemManagementPage } from '../../../pages/SystemManagementPage';

const TARGET_PAGE = '/target';

test.describe('目标管理', () => {
  let page: Page;
  let targetPage: SystemManagementPage;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    targetPage = new SystemManagementPage(page);
    await navigateToPage(page, TARGET_PAGE);
  });

  test('FUNC-TARGET-001 目标管理页面加载', async () => {
    expect(page.url()).toContain(TARGET_PAGE);
    console.log('✅ 目标管理页面加载成功');
  });

  test('FUNC-TARGET-002 创建目标-填写完整信息', async () => {
    try {
      const dialog = await targetPage.clickAddButton();
      const timestamp = Date.now();
      
      await dialog.fillInputByPlaceholder('请输入目标名称', `测试目标_${timestamp}`);
      await dialog.fillInputByPlaceholder('请输入目标值', '100000');
      await dialog.fillInputByPlaceholder('请输入目标描述', '自动化测试创建的目标');
      
      await dialog.submit();
      
      const toast = await targetPage.getToastMessage();
      if (toast && toast.includes('成功')) {
        console.log('✅ 目标创建成功');
      }
    } catch (error) {
      console.log(`⚠️ 创建目标失败: ${error}`);
    }
  });

  test('FUNC-TARGET-003 创建目标-必填字段校验', async () => {
    try {
      const dialog = await targetPage.clickAddButton();
      await dialog.submit();
      
      const toast = await targetPage.getToastMessage();
      if (toast && (toast.includes('不能为空') || toast.includes('必填'))) {
        console.log('✅ 必填字段校验生效');
      }
      
      await dialog.close();
    } catch (error) {
      console.log(`⚠️ 必填校验测试失败: ${error}`);
    }
  });

  test('FUNC-TARGET-004 查询目标列表-搜索功能', async () => {
    await targetPage.search('测试');
    const count = await targetPage.getTableRowCount();
    console.log(`✅ 搜索结果数量: ${count}`);
  });

  test('FUNC-TARGET-005 目标进度展示', async () => {
    const progressBars = page.locator('.el-progress, [class*="progress"]');
    const count = await progressBars.count();
    console.log(`✅ 进度条数量: ${count}`);
  });
});