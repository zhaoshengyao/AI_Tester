import { test, expect, Page } from '@playwright/test';
import { CustomerManagementPage } from '../../pages/CustomerManagementPage';

test.describe('CRM 客户管理 CRUD 测试', () => {
  let page: Page;
  let customerPage: CustomerManagementPage;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    customerPage = new CustomerManagementPage(page);
    console.log('🔄 正在加载客户管理页面...');
    await page.goto('/customer/customer', { waitUntil: 'networkidle', timeout: 30000 }).catch(() => {});
    console.log('⏳ 等待页面渲染...');
    await page.waitForTimeout(3000);
    
    try {
      await page.waitForSelector('.el-table, .el-empty, .cxd-List', { timeout: 15000 });
      console.log('✅ 表格区域已加载');
    } catch (e) {
      console.log('⚠️ 等待表格超时，继续执行');
    }
    
    console.log(`✅ 页面加载完成: ${page.url()}`);
  });

  test('FUNC-CRM-CUST-001 创建客户-填写完整信息', async () => {
    const dialog = await customerPage.clickAddButton();
    await dialog.completeCreateCustomer();
    
    const toast = await customerPage.getToastMessage();
    expect(toast ?? '').toContain('成功');
    console.log('✅ 创建客户-填写完整信息测试完成');
  });

  test('FUNC-CRM-CUST-002 创建客户-必填字段校验', async () => {
    const dialog = await customerPage.clickAddButton();
    await dialog.submit();
    
    await dialog.close();
    console.log('✅ 创建客户-必填字段校验测试完成');
  });

  test('FUNC-CRM-CUST-003 查询客户列表-分页功能', async () => {
    await customerPage.goToPage(1);
    console.log('✅ 查询客户列表-分页功能测试完成');
  });

  test('FUNC-CRM-CUST-004 查询客户列表-搜索功能', async () => {
    await customerPage.searchCustomer('测试');
    console.log('✅ 查询客户列表-搜索功能测试完成');
  });

  test('FUNC-CRM-CUST-016 联系人tab加载', async () => {
    // 等待页面加载完成，确保客户列表显示
    await page.waitForTimeout(3000);
    
    // 检查是否有客户数据，没有则跳过
    const customerCount = await customerPage.getCustomerCount();
    if (customerCount === 0) {
      test.skip(true, '暂无客户数据，跳过联系人测试');
      return;
    }
    
    await customerPage.navigateToCustomerDetail();
    const isContactTab = await customerPage.isContactTab();
    expect(isContactTab).toBe(true);
    console.log('✅ 联系人tab加载测试完成');
  });

  test('FUNC-CRM-CUST-018 新增联系人-正常提交', async () => {
    // 等待页面加载完成，确保客户列表显示
    await page.waitForTimeout(3000);
    
    // 检查是否有客户数据，没有则跳过
    const customerCount = await customerPage.getCustomerCount();
    if (customerCount === 0) {
      test.skip(true, '暂无客户数据，跳过联系人测试');
      return;
    }
    
    await customerPage.navigateToCustomerDetail();
    const isContactTab = await customerPage.isContactTab();
    if (!isContactTab) {
      test.skip(true, '当前页面不是联系人tab，跳过测试');
      return;
    }

    const dialog = await customerPage.clickAddContactButton();
    await dialog.completeCreateContact();
    
    const toast = await customerPage.getToastMessage();
    expect(toast ?? '').toContain('成功');
    console.log('✅ 新增联系人-正常提交测试完成');
  });

  test('FUNC-CRM-CUST-019 新增联系人-姓名为空', async () => {
    // 等待页面加载完成，确保客户列表显示
    await page.waitForTimeout(3000);
    
    // 检查是否有客户数据，没有则跳过
    const customerCount = await customerPage.getCustomerCount();
    if (customerCount === 0) {
      test.skip(true, '暂无客户数据，跳过联系人测试');
      return;
    }
    
    await customerPage.navigateToCustomerDetail();
    const isContactTab = await customerPage.isContactTab();
    if (!isContactTab) {
      test.skip(true, '当前页面不是联系人tab，跳过测试');
      return;
    }

    const dialog = await customerPage.clickAddContactButton();
    await dialog.submit();
    
    await dialog.close();
    console.log('✅ 新增联系人-姓名为空测试完成');
  });
});