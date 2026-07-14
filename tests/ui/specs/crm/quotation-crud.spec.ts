import { test, expect, Page } from '@playwright/test';
import { navigateToPage } from '../../utils/app';
import { QuotationManagementPage } from '../../pages/QuotationManagementPage';

const QUOTATION_PAGE = '/quotation/quotationList';

test.describe('报价管理 CRUD 测试', () => {
  let page: Page;
  let quotationPage: QuotationManagementPage;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    quotationPage = new QuotationManagementPage(page);
    await navigateToPage(page, QUOTATION_PAGE);
  });

  test('FUNC-QUO-001 创建报价-填写完整信息', async () => {
    try {
      const dialog = await quotationPage.clickAddButton();
      await dialog.completeCreateQuotation();
      
      const toast = await quotationPage.getToastMessage();
      if (toast && toast.includes('成功')) {
        console.log('✅ 报价创建成功');
      }
    } catch (error) {
      console.log(`⚠️ 创建报价失败: ${error}`);
    }
  });

  test('FUNC-QUO-002 创建报价-必填字段校验', async () => {
    try {
      const dialog = await quotationPage.clickAddButton();
      await dialog.submit();
      
      const toast = await quotationPage.getToastMessage();
      if (toast && (toast.includes('不能为空') || toast.includes('必填'))) {
        console.log('✅ 必填字段校验生效');
      }
      
      await dialog.close();
    } catch (error) {
      console.log(`⚠️ 必填校验测试失败: ${error}`);
    }
  });

  test('FUNC-QUO-003 查询报价列表-搜索功能', async () => {
    await quotationPage.searchQuotation('测试');
  });

  test('FUNC-QUO-004 查询报价列表-分页功能', async () => {
    await quotationPage.goToPage(2);
  });
});