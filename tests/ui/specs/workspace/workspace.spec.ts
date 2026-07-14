import { test, expect, Page } from '@playwright/test';
import { navigateToPage } from '../../utils/app';

const WORKSPACE_PAGE = '/index';

test.describe('工作台', () => {
  let page: Page;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    await navigateToPage(page, WORKSPACE_PAGE);
  });

  test('FUNC-WORKSPACE-001 工作台页面加载', async () => {
    expect(page.url()).toContain(WORKSPACE_PAGE);
    console.log('✅ 工作台页面加载成功');
  });

  test('FUNC-WORKSPACE-002 工作台看板展示', async () => {
    const cards = page.locator('.dashboard-card, .stat-card, [class*="card"]');
    const cardCount = await cards.count();
    console.log(`✅ 工作台卡片数量: ${cardCount}`);
    
    const charts = page.locator('.chart-container, [class*="chart"]');
    const chartCount = await charts.count();
    console.log(`✅ 工作台图表数量: ${chartCount}`);
  });

  test('FUNC-WORKSPACE-003 工作台快捷入口', async () => {
    const quickLinks = page.locator('[class*="quick"], [class*="shortcut"], [class*="entry"]');
    const linkCount = await quickLinks.count();
    console.log(`✅ 快捷入口数量: ${linkCount}`);
  });

  test('FUNC-WORKSPACE-004 工作台数据统计', async () => {
    const stats = page.locator('[class*="stat"], [class*="count"], [class*="number"]');
    const statCount = await stats.count();
    console.log(`✅ 数据统计项数量: ${statCount}`);
  });
});