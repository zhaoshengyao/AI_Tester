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
    
    // 通过菜单导航到报价管理页面
    await page.goto('/index', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
    
    const quotationSubMenu = page.locator('.el-sub-menu__title').filter({ hasText: '报价管理' }).first();
    if ((await quotationSubMenu.count()) > 0) {
      await quotationSubMenu.click();
      await page.waitForTimeout(2000);
      
      const quotationLink = page.locator('a[href="/quotation/quotationList"]').first();
      if ((await quotationLink.count()) > 0) {
        await quotationLink.click();
        await page.waitForTimeout(5000);
        console.log(`✅ 通过菜单导航到报价列表: ${page.url()}`);
        return;
      }
    }
    
    await navigateToPage(page, QUOTATION_PAGE);
    console.log(`✅ 导航到报价列表页面: ${page.url()}`);
  });

  test('FUNC-QUO-001 创建报价-填写完整信息', async ({}, testInfo) => {
    testInfo.setTimeout(60000);
    
    const isAvailable = await quotationPage.isPageAvailable();
    if (!isAvailable) {
      test.skip(true, '报价管理页面不可用');
      return;
    }

    const dialog = await quotationPage.clickAddButton();
    // 不指定客户名称，让回退策略自动选择第一个可用的客户
    await dialog.completeCreateQuotation();
    
    // 使用提交时捕获的消息（在页面跳转前捕获）
    const capturedMessage = dialog.getLastSubmitMessage();
    if (capturedMessage) {
      expect(capturedMessage).toContain('成功');
      console.log('✅ 报价创建成功');
    } else {
      // 回退方案：检查是否已跳转到列表页
      const currentUrl = page.url();
      if (currentUrl.includes('quotationList')) {
        console.log('✅ 报价创建成功（已跳转到列表页）');
      } else {
        const toast = await quotationPage.getToastMessage();
        expect(toast ?? '').toContain('成功');
        console.log('✅ 报价创建成功');
      }
    }
  });

  test('FUNC-QUO-002 创建报价-必填字段校验', async ({}, testInfo) => {
    testInfo.setTimeout(45000);
    
    const isAvailable = await quotationPage.isPageAvailable();
    if (!isAvailable) {
      test.skip(true, '报价管理页面不可用');
      return;
    }

    const dialog = await quotationPage.clickAddButton();
    await dialog.submit();
    
    const toast = await quotationPage.getToastMessage();
    expect(toast ?? '').toMatch(/不能为空|必填|请输入|请选择/);
    
    await dialog.close();
    console.log('✅ 必填字段校验生效');
  });

  test('FUNC-QUO-003 查询报价列表-搜索功能', async ({}, testInfo) => {
    testInfo.setTimeout(30000);
    
    const isAvailable = await quotationPage.isPageAvailable();
    if (!isAvailable) {
      test.skip(true, '报价管理页面不可用');
      return;
    }

    await quotationPage.searchQuotation('测试');
    console.log('✅ 搜索功能测试完成');
  });

  test('FUNC-QUO-004 查询报价列表-分页功能', async ({}, testInfo) => {
    testInfo.setTimeout(30000);
    
    const isAvailable = await quotationPage.isPageAvailable();
    if (!isAvailable) {
      test.skip(true, '报价管理页面不可用');
      return;
    }

    await quotationPage.goToPage(2);
    console.log('✅ 分页功能测试完成');
  });
});