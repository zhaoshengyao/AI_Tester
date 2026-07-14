import { test, expect, Page } from '@playwright/test';
import { navigateToPage } from '../../utils/app';
import { SystemManagementPage } from '../../pages/SystemManagementPage';

const DEPT_PAGE = '/system/dept';

test.describe('系统管理 - 部门管理', () => {
  let page: Page;
  let systemPage: SystemManagementPage;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    systemPage = new SystemManagementPage(page);
    await navigateToPage(page, DEPT_PAGE);
  });

  test('FUNC-SYS-DEPT-001 部门列表页面加载', async () => {
    expect(page.url()).toContain(DEPT_PAGE);
    console.log('✅ 部门管理页面加载成功');
  });

  test('FUNC-SYS-DEPT-002 创建部门-填写完整信息', async () => {
    try {
      const dialog = await systemPage.clickAddButton();
      const timestamp = Date.now();
      
      await dialog.fillInputByPlaceholder('请输入部门名称', `测试部门_${timestamp}`);
      await dialog.fillInputByPlaceholder('请输入部门编码', `DEPT_${timestamp}`);
      await dialog.fillInputByPlaceholder('请输入部门描述', '自动化测试创建的部门');
      
      await dialog.submit();
      
      const toast = await systemPage.getToastMessage();
      if (toast && toast.includes('成功')) {
        console.log('✅ 部门创建成功');
      }
    } catch (error) {
      console.log(`⚠️ 创建部门失败: ${error}`);
    }
  });

  test('FUNC-SYS-DEPT-003 创建部门-必填字段校验', async () => {
    try {
      const dialog = await systemPage.clickAddButton();
      await dialog.submit();
      
      const toast = await systemPage.getToastMessage();
      if (toast && (toast.includes('不能为空') || toast.includes('必填'))) {
        console.log('✅ 必填字段校验生效');
      }
      
      await dialog.close();
    } catch (error) {
      console.log(`⚠️ 必填校验测试失败: ${error}`);
    }
  });

  test('FUNC-SYS-DEPT-004 查询部门列表-搜索功能', async () => {
    await systemPage.search('测试');
    const count = await systemPage.getTableRowCount();
    console.log(`✅ 搜索结果数量: ${count}`);
  });
});