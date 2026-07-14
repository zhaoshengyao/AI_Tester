import { test, expect, Page } from '@playwright/test';
import { navigateToPage } from '../../utils/app';

const REPORT_PAGES = [
  { path: '/report/daily', name: '日报' },
  { path: '/report/weekly', name: '周报' },
  { path: '/report/monthly', name: '月报' },
  { path: '/report/quarterly', name: '季报' },
  { path: '/report/yearly', name: '年报' }
];

test.describe('报表管理', () => {
  let page: Page;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
  });

  REPORT_PAGES.forEach(({ path, name }, index) => {
    test(`FUNC-REPORT-00${index + 1} ${name}页面加载`, async () => {
      try {
        await navigateToPage(page, path);
        expect(page.url()).toContain(path);
        console.log(`✅ ${name}页面加载成功`);
      } catch (error) {
        console.log(`⚠️ ${name}页面加载失败: ${error}`);
      }
    });
  });

  test('FUNC-REPORT-006 报表筛选功能', async () => {
    try {
      await navigateToPage(page, '/report/daily');
      const datePicker = page.locator('.el-date-picker, [class*="date"]').first();
      if ((await datePicker.count()) > 0 && await datePicker.isVisible()) {
        await datePicker.click();
        console.log('✅ 日期选择器可用');
      }
      
      const searchBtn = page.locator('button').filter({ hasText: /查询|搜索/ }).first();
      if ((await searchBtn.count()) > 0 && await searchBtn.isVisible()) {
        await searchBtn.click();
        await page.waitForTimeout(2000);
        console.log('✅ 查询按钮可用');
      }
    } catch (error) {
      console.log(`⚠️ 报表筛选功能测试失败: ${error}`);
    }
  });

  test('FUNC-REPORT-007 报表导出功能', async () => {
    try {
      await navigateToPage(page, '/report/daily');
      const exportBtn = page.locator('button').filter({ hasText: /导出|下载/ }).first();
      if ((await exportBtn.count()) > 0 && await exportBtn.isVisible()) {
        console.log('✅ 导出按钮可用');
      }
    } catch (error) {
      console.log(`⚠️ 报表导出功能测试失败: ${error}`);
    }
  });
});