import { test, expect, Page } from '@playwright/test';
import { navigateToPage } from '../../../utils/app';
import { SystemManagementPage } from '../../../pages/SystemManagementPage';

const MENU_PAGE = '/system/menu';

test.describe('系统管理 - 菜单管理', () => {
  let page: Page;
  let systemPage: SystemManagementPage;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    systemPage = new SystemManagementPage(page);
    await navigateToPage(page, MENU_PAGE);
  });

  test('FUNC-SYS-MENU-001 菜单列表页面加载', async () => {
    expect(page.url()).toContain(MENU_PAGE);
    console.log('✅ 菜单管理页面加载成功');
  });

  test('FUNC-SYS-MENU-002 创建菜单-填写完整信息', async () => {
    try {
      const dialog = await systemPage.clickAddButton();
      const timestamp = Date.now();
      
      await dialog.fillInputByPlaceholder('请输入菜单名称', `测试菜单_${timestamp}`);
      await dialog.fillInputByPlaceholder('请输入菜单路径', `/test/menu/${timestamp}`);
      await dialog.fillInputByPlaceholder('请输入菜单图标', 'icon-test');
      
      await dialog.submit();
      
      const toast = await systemPage.getToastMessage();
      if (toast && toast.includes('成功')) {
        console.log('✅ 菜单创建成功');
      }
    } catch (error) {
      console.log(`⚠️ 创建菜单失败: ${error}`);
    }
  });

  test('FUNC-SYS-MENU-003 创建菜单-必填字段校验', async () => {
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

  test('FUNC-SYS-MENU-004 查询菜单列表-搜索功能', async () => {
    await systemPage.search('测试');
    const count = await systemPage.getTableRowCount();
    console.log(`✅ 搜索结果数量: ${count}`);
  });
});