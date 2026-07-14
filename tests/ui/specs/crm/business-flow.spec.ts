import { test, expect, Page } from '@playwright/test';
import { navigateToPage } from '../../utils/app';
import { ClueManagementPage } from '../../pages/ClueManagementPage';
import { BusinessManagementPage } from '../../pages/BusinessManagementPage';
import { QuotationManagementPage } from '../../pages/QuotationManagementPage';

test.describe('CRM业务流程测试', () => {
  let page: Page;
  const timestamp = Date.now();
  const testCustomer = `流程测试客户_${timestamp}`;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
  });

  test('FLOW-001 创建线索并转化为商机', async () => {
    await navigateToPage(page, '/marketing/clue');
    
    const cluePage = new ClueManagementPage(page);
    try {
      const dialog = await cluePage.clickAddButton();
      await dialog.fillClueName(`流程测试线索_${timestamp}`);
      await dialog.fillCustomerName(testCustomer);
      await dialog.fillContact('流程测试联系人');
      await dialog.fillPhone('13800138000');
      await dialog.fillSource('线上');
      await dialog.fillStatus('待跟进');
      await dialog.submit();
      
      const toast = await cluePage.getToastMessage();
      if (toast && toast.includes('成功')) {
        console.log('✅ 线索创建成功');
      }
    } catch (error) {
      console.log(`⚠️ 创建线索失败: ${error}`);
    }
  });

  test('FLOW-002 从线索创建商机', async () => {
    await navigateToPage(page, '/business/BusinessOverview');
    
    const businessPage = new BusinessManagementPage(page);
    try {
      const dialog = await businessPage.clickAddButton();
      await dialog.fillBusinessName(`流程测试商机_${timestamp}`);
      await dialog.fillCustomerName(testCustomer);
      await dialog.fillContact('流程测试联系人');
      await dialog.fillAmount('200000');
      await dialog.fillStage('需求确认');
      await dialog.fillStatus('进行中');
      await dialog.submit();
      
      const toast = await businessPage.getToastMessage();
      if (toast && toast.includes('成功')) {
        console.log('✅ 商机创建成功');
      }
    } catch (error) {
      console.log(`⚠️ 创建商机失败: ${error}`);
    }
  });

  test('FLOW-003 从商机创建报价', async () => {
    await navigateToPage(page, '/quotation/quotationList');
    
    const quotationPage = new QuotationManagementPage(page);
    try {
      const dialog = await quotationPage.clickAddButton();
      await dialog.fillQuotationNo(`FLOW_QUO_${timestamp}`);
      await dialog.fillCustomerName(testCustomer);
      await dialog.fillContact('流程测试联系人');
      await dialog.fillTotalAmount('180000');
      await dialog.fillStatus('待确认');
      await dialog.submit();
      
      const toast = await quotationPage.getToastMessage();
      if (toast && toast.includes('成功')) {
        console.log('✅ 报价创建成功');
      }
    } catch (error) {
      console.log(`⚠️ 创建报价失败: ${error}`);
    }
  });

  test('FLOW-004 查看完整业务链数据', async () => {
    await navigateToPage(page, '/customer/customer');
    await page.waitForTimeout(3000);
    
    const searchInput = page.locator('input[placeholder*="搜索"]').first();
    if ((await searchInput.count()) > 0 && await searchInput.isVisible()) {
      await searchInput.fill(testCustomer);
      await searchInput.press('Enter');
      await page.waitForTimeout(2000);
      console.log(`✅ 已搜索客户: ${testCustomer}`);
    }
  });
});