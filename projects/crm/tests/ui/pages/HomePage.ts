import { Page, expect } from '@playwright/test';

export class HomePage {
  constructor(private page: Page) {}

  async assertDashboardVisible() {
    await expect(this.page.getByRole('heading', { name: '首页' })).toBeVisible({ timeout: 15_000 });
    await expect(this.page.getByText('设备总数量').first()).toBeVisible({ timeout: 15_000 });
  }

  async gotoMenu(name: string) {
    await this.page.getByText(name, { exact: true }).click();
  }

  async assertTextVisible(text: RegExp | string) {
    await expect(this.page.getByText(text).first()).toBeVisible();
  }
}
