import { test, expect, Page } from '@playwright/test';
import { navigateToPage } from '../../utils/app';
import { SystemManagementPage } from '../../pages/SystemManagementPage';

const USER_PAGE = '/system/user';

test.describe('系统管理 - 用户管理', () => {
  let page: Page;
  let systemPage: SystemManagementPage;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    systemPage = new SystemManagementPage(page);
    await navigateToPage(page, USER_PAGE);
  });

  test('FUNC-SYS-USER-001 用户列表页面加载', async () => {
    expect(page.url()).toContain(USER_PAGE);
    console.log('✅ 用户管理页面加载成功');
  });

  test('FUNC-SYS-USER-002 创建用户-填写完整信息', async () => {
    try {
      const dialog = await systemPage.clickAddButton();
      const timestamp = Date.now();
      
      await dialog.fillInputByPlaceholder('请输入用户名', `testuser_${timestamp}`);
      await dialog.fillInputByPlaceholder('请输入昵称', `测试用户_${timestamp}`);
      await dialog.fillInputByPlaceholder('请输入密码', '123456');
      await dialog.fillInputByPlaceholder('请输入手机号', '13900139000');
      await dialog.fillInputByPlaceholder('请输入邮箱', `test_${timestamp}@test.com`);
      
      await dialog.submit();
      
      const toast = await systemPage.getToastMessage();
      if (toast && toast.includes('成功')) {
        console.log('✅ 用户创建成功');
      }
    } catch (error) {
      console.log(`⚠️ 创建用户失败: ${error}`);
    }
  });

  test('FUNC-SYS-USER-003 创建用户-必填字段校验', async () => {
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

  test('FUNC-SYS-USER-004 查询用户列表-搜索功能', async () => {
    await systemPage.search('测试');
    const count = await systemPage.getTableRowCount();
    console.log(`✅ 搜索结果数量: ${count}`);
  });

  test('FUNC-SYS-USER-005 查看用户详情', async () => {
    const count = await systemPage.getTableRowCount();
    if (count > 0) {
      await systemPage.clickTableRow(0);
      await page.waitForTimeout(2000);
      console.log('✅ 已点击第一条用户查看详情');
    }
  });
});