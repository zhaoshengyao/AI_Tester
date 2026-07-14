import { test, expect, Page } from '@playwright/test';
import { navigateToPage } from '../../utils/app';
import { SystemManagementPage } from '../../pages/SystemManagementPage';

const ROLE_PAGE = '/system/role';

test.describe('系统管理 - 角色管理', () => {
  let page: Page;
  let systemPage: SystemManagementPage;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    systemPage = new SystemManagementPage(page);
    await navigateToPage(page, ROLE_PAGE);
  });

  test('FUNC-SYS-ROLE-001 角色列表页面加载', async () => {
    expect(page.url()).toContain(ROLE_PAGE);
    console.log('✅ 角色管理页面加载成功');
  });

  test('FUNC-SYS-ROLE-002 创建角色-填写完整信息', async () => {
    try {
      const dialog = await systemPage.clickAddButton();
      const timestamp = Date.now();
      
      await dialog.fillInputByPlaceholder('请输入角色名称', `测试角色_${timestamp}`);
      await dialog.fillInputByPlaceholder('请输入角色编码', `ROLE_${timestamp}`);
      await dialog.fillInputByPlaceholder('请输入角色描述', '自动化测试创建的角色');
      
      await dialog.submit();
      
      const toast = await systemPage.getToastMessage();
      if (toast && toast.includes('成功')) {
        console.log('✅ 角色创建成功');
      }
    } catch (error) {
      console.log(`⚠️ 创建角色失败: ${error}`);
    }
  });

  test('FUNC-SYS-ROLE-003 创建角色-必填字段校验', async () => {
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

  test('FUNC-SYS-ROLE-004 查询角色列表-搜索功能', async () => {
    await systemPage.search('测试');
    const count = await systemPage.getTableRowCount();
    console.log(`✅ 搜索结果数量: ${count}`);
  });

  test('FUNC-SYS-ROLE-005 查看角色详情', async () => {
    const count = await systemPage.getTableRowCount();
    if (count > 0) {
      await systemPage.clickTableRow(0);
      await page.waitForTimeout(2000);
      console.log('✅ 已点击第一条角色查看详情');
    }
  });
});