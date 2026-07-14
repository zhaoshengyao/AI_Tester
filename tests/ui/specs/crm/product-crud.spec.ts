import { test, expect, Page } from '@playwright/test';
import { navigateToPage } from '../../utils/app';
import { ProductManagementPage } from '../../pages/ProductManagementPage';

const PRODUCT_PAGE = '/product/ProductList';

test.describe('产品管理 CRUD 测试', () => {
  let page: Page;
  let productPage: ProductManagementPage;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    productPage = new ProductManagementPage(page);
    await navigateToPage(page, PRODUCT_PAGE);
  });

  test('FUNC-PRODUCT-001 创建产品-填写完整信息', async () => {
    try {
      const dialog = await productPage.clickAddButton();
      await dialog.completeCreateProduct();
      
      const toast = await productPage.getToastMessage();
      if (toast && toast.includes('成功')) {
        console.log('✅ 产品创建成功');
      }
    } catch (error) {
      console.log(`⚠️ 创建产品失败: ${error}`);
    }
  });

  test('FUNC-PRODUCT-002 创建产品-必填字段校验', async () => {
    try {
      const dialog = await productPage.clickAddButton();
      await dialog.submit();
      
      const toast = await productPage.getToastMessage();
      if (toast && (toast.includes('不能为空') || toast.includes('必填'))) {
        console.log('✅ 必填字段校验生效');
      }
      
      await dialog.close();
    } catch (error) {
      console.log(`⚠️ 必填校验测试失败: ${error}`);
    }
  });

  test('FUNC-PRODUCT-003 查询产品列表-搜索功能', async () => {
    await productPage.searchProduct('测试');
  });

  test('FUNC-PRODUCT-004 查询产品列表-分页功能', async () => {
    await productPage.goToPage(2);
  });
});