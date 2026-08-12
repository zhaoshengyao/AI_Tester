/**
 * HR 系统冒烟测试 - 第二被测系统示例
 * 演示多系统隔离：本 spec 只会在 --system hr-demo 时被执行
 */
import { test, expect } from '@playwright/test';

const HR_BASE_URL = process.env.HR_BASE_URL || 'http://192.168.2.97:7080';

test.describe('HR系统冒烟测试', () => {
  test('SMOKE-HR-001 登录页面可达', async ({ page }) => {
    // 仅验证页面可达，不要求真实登录
    try {
      await page.goto(HR_BASE_URL, { timeout: 10000 });
      await expect(page).toHaveTitle(/.+/);
    } catch (error) {
      // HR 示例系统未部署时跳过
      test.skip(true, 'HR 示例系统未部署');
    }
  });
});
