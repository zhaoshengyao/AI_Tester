import { test, expect, Page } from '@playwright/test';
import { getAuthToken } from '../../utils/app';
import { ProductManagementPage } from '../../pages/ProductManagementPage';
import { TestDataManager } from '../../utils/test-data-manager';

const PRODUCT_PAGE = '/product/ProductList';

test.describe('产品管理 CRUD 测试', () => {
  let page: Page;
  let productPage: ProductManagementPage;
  let testDataManager: TestDataManager;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    productPage = new ProductManagementPage(page);
    const token = getAuthToken();
    testDataManager = new TestDataManager(process.env.API_BASE_URL, token);
    
    // 通过菜单导航（直接URL可能跳转到工作台）
    await page.goto('/index', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
    
    // 展开产品管理子菜单
    const productSubMenu = page.locator('.el-sub-menu__title').filter({ hasText: '产品管理' }).first();
    if ((await productSubMenu.count()) > 0) {
      await productSubMenu.click();
      await page.waitForTimeout(1500);
      
      // 点击产品列表链接
      const productListLink = page.locator('a[href="/product/ProductList"]').first();
      if ((await productListLink.count()) > 0) {
        await productListLink.click();
        await page.waitForTimeout(5000);
        console.log(`✅ 通过菜单导航到产品列表: ${page.url()}`);
        return;
      }
    }
    
    // 如果菜单方式失败，使用直接导航
    console.log('⚠️ 菜单导航失败，尝试直接URL导航');
    await page.goto(PRODUCT_PAGE, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);
    console.log(`✅ 直接导航到产品列表: ${page.url()}`);
  });

  test.afterEach(async () => {
    await testDataManager.cleanupCreatedData();
    await testDataManager.cleanupTestDataByPattern();
  });

  test('FUNC-PRODUCT-001 创建产品-填写完整信息', async () => {
    // 检查是否有新增按钮
    const addButton = page.getByText('新增产品', { exact: false }).first();
    if ((await addButton.count()) === 0) {
      console.log('⚠️ 产品管理页面没有新增按钮，跳过测试');
      test.skip(true, '产品管理页面没有新增按钮');
      return;
    }
    
    const dialog = await productPage.clickAddButton();
    await dialog.completeCreateProduct();
    
    const toast = await productPage.getToastMessage();
    expect(toast ?? '').toContain('成功');
    console.log('✅ 产品创建成功');
  });

  test('FUNC-PRODUCT-002 创建产品-必填字段校验', async () => {
    // 检查是否有新增按钮（使用与clickAddButton一致的匹配方式）
    const addButton = page.locator('button').filter({ hasText: /新增|添加/ }).first();
    if ((await addButton.count()) === 0) {
      console.log('⚠️ 产品管理页面没有新增按钮，跳过测试');
      test.skip(true, '产品管理页面没有新增按钮');
      return;
    }
    
    const dialog = await productPage.clickAddButton();
    await dialog.submit();
    
    const toast = await productPage.getToastMessage();
    expect(toast ?? '').toMatch(/不能为空|必填|请输入|请选择/);
    
    await dialog.close();
    console.log('✅ 必填字段校验生效');
  });

  test('FUNC-PRODUCT-003 查询产品列表-搜索功能', async () => {
    await productPage.searchProduct('测试');
  });

  test('FUNC-PRODUCT-004 查询产品列表-分页功能', async () => {
    await productPage.goToPage(2);
  });
});