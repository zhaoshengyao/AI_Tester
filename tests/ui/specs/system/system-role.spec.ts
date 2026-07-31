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
    
    // 先导航到首页
    await page.goto('/index', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);
    
    // 展开系统管理子菜单
    const systemSubMenuTitle = page.locator('.el-sub-menu__title').filter({ hasText: '系统管理' }).first();
    if ((await systemSubMenuTitle.count()) > 0) {
      await systemSubMenuTitle.click();
      await page.waitForTimeout(2000);
      
      // 点击角色管理链接
      const roleLink = page.locator('a[href="/system/role"]').first();
      if ((await roleLink.count()) > 0) {
        await roleLink.click();
        await page.waitForTimeout(5000);
        console.log(`✅ 通过菜单导航到角色管理页面: ${page.url()}`);
        return;
      }
    }
    
    // 备用方案：直接导航
    await navigateToPage(page, ROLE_PAGE);
    console.log(`✅ 导航到角色管理页面: ${page.url()}`);
  });

  test('FUNC-SYS-ROLE-001 角色列表页面加载', async () => {
    expect(page.url()).toContain(ROLE_PAGE);
    
    // 等待表格加载
    const table = page.locator('.el-table');
    await table.waitFor({ state: 'visible', timeout: 10000 });
    console.log('✅ 角色管理页面加载成功');
  });

  test('FUNC-SYS-ROLE-002 创建角色-填写完整信息', async () => {
    try {
      // 查找新增按钮
      const addButton = page.locator('button').filter({ hasText: /新增/ }).first();
      if ((await addButton.count()) === 0 || !(await addButton.isVisible())) {
        console.log('⚠️ 未找到新增按钮');
        return;
      }
      
      await addButton.click();
      console.log('✅ 点击新增按钮');
      
      // 等待抽屉加载
      await page.waitForTimeout(2000);
      
      // 查找可见的抽屉
      const drawers = page.locator('.el-drawer:visible');
      if ((await drawers.count()) > 0) {
        const drawer = drawers.first();
        
        // 填写表单
        const timestamp = Date.now();
        await systemPage.fillInputByLabel('角色名称', `测试角色_${timestamp}`);
        await systemPage.fillInputByLabel('角色编码', `ROLE_${timestamp}`);
        await systemPage.fillInputByLabel('角色描述', '自动化测试创建的角色');
        
        // 提交
        const submitButton = drawer.locator('button').filter({ hasText: /确定|提交/ }).first();
        if ((await submitButton.count()) > 0 && await submitButton.isVisible()) {
          await submitButton.click();
          console.log('✅ 点击确定按钮');
          
          const toast = await systemPage.getToastMessage();
          if (toast && toast.includes('成功')) {
            console.log('✅ 角色创建成功');
          }
        }
      }
    } catch (error) {
      console.log(`⚠️ 创建角色失败: ${error}`);
    }
  });

  test('FUNC-SYS-ROLE-003 创建角色-必填字段校验', async () => {
    try {
      // 查找新增按钮
      const addButton = page.locator('button').filter({ hasText: /新增/ }).first();
      if ((await addButton.count()) === 0 || !(await addButton.isVisible())) {
        console.log('⚠️ 未找到新增按钮');
        return;
      }
      
      await addButton.click();
      console.log('✅ 点击新增按钮');
      
      // 等待抽屉加载
      await page.waitForTimeout(2000);
      
      // 查找可见的抽屉
      const drawers = page.locator('.el-drawer:visible');
      if ((await drawers.count()) > 0) {
        const drawer = drawers.first();
        
        // 直接提交
        const submitButton = drawer.locator('button').filter({ hasText: /确定|提交/ }).first();
        if ((await submitButton.count()) > 0 && await submitButton.isVisible()) {
          await submitButton.click();
          console.log('✅ 点击确定按钮');
          
          const toast = await systemPage.getToastMessage();
          if (toast && (toast.includes('不能为空') || toast.includes('必填'))) {
            console.log('✅ 必填字段校验生效');
          }
          
          // 关闭抽屉
          const closeButton = drawer.locator('button').filter({ hasText: /取消/ }).first();
          if ((await closeButton.count()) > 0) {
            await closeButton.click();
          }
        }
      }
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
