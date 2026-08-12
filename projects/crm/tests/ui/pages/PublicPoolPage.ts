import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

export class PublicPoolPage extends BasePage {
  private searchInput: Locator;

  constructor(page: Page) {
    super(page);
    this.searchInput = page.locator('input[placeholder*="搜索"], input[placeholder*="客户"]').first();
  }

  async navigate(): Promise<void> {
    await super.navigate('/customer/publicPool');
  }

  async isPageAvailable(): Promise<boolean> {
    try {
      await this.page.waitForSelector('.el-table, .amis-table', { state: 'attached', timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  async searchCustomer(keyword: string): Promise<void> {
    if ((await this.searchInput.count()) === 0) {
      console.log('⚠️ 未找到搜索输入框');
      return;
    }
    
    await this.searchInput.waitFor({ state: 'visible', timeout: 5000 });
    await this.searchInput.fill(keyword);
    console.log(`✅ 填写搜索关键词: ${keyword}`);
    
    const parentForm = this.searchInput.locator('..').locator('..').locator('..');
    let searchButton = parentForm.locator('button').filter({ hasText: /搜索/ }).first();
    
    if ((await searchButton.count()) === 0 || !(await searchButton.isVisible())) {
      const searchButtons = this.page.locator('button').filter({ hasText: /搜索/ });
      for (let i = 0; i < await searchButtons.count(); i++) {
        const btn = searchButtons.nth(i);
        if (await btn.isVisible()) {
          const rect = await btn.boundingBox();
          if (rect && rect.y > 100) {
            searchButton = btn;
            break;
          }
        }
      }
    }
    
    if ((await searchButton.count()) > 0 && await searchButton.isVisible()) {
      await searchButton.click();
      console.log('✅ 点击搜索按钮');
    } else {
      await this.searchInput.press('Enter');
      console.log('✅ 使用Enter键搜索');
    }
    
    await this.page.waitForTimeout(2000);
  }

  async claimCustomer(customerName: string): Promise<boolean> {
    console.log(`🔍 尝试领取客户: ${customerName}`);
    
    await this.searchCustomer(customerName);
    
    const claimButtons = this.page.locator('button').filter({ hasText: /领取/ });
    const buttonCount = await claimButtons.count();
    console.log(`📊 领取按钮数量: ${buttonCount}`);
    
    if (buttonCount > 0) {
      const claimButton = claimButtons.first();
      if (await claimButton.isVisible()) {
        await claimButton.click();
        console.log('✅ 点击领取按钮');
        await this.page.waitForTimeout(2000);
        
        const toast = this.page.locator('.el-message').last();
        const toastText = await toast.textContent();
        console.log(`📊 领取结果: ${toastText}`);
        
        return toastText?.includes('成功') ?? false;
      }
    }
    
    console.log('⚠️ 未找到可领取的客户');
    return false;
  }

  async getPublicPoolCount(): Promise<number> {
    const rowSelectors = ['.amis-table-row', '.el-table__row', 'table tbody tr'];
    for (const selector of rowSelectors) {
      const rows = this.page.locator(selector);
      const count = await rows.count();
      if (count > 0) {
        return count;
      }
    }
    return 0;
  }

  async verifyCustomerInPool(customerName: string): Promise<boolean> {
    await this.searchCustomer(customerName);
    await this.page.waitForTimeout(1000);
    
    const rows = this.page.locator('.el-table__row, .amis-table-row');
    for (let i = 0; i < await rows.count(); i++) {
      const rowText = await rows.nth(i).textContent();
      if (rowText?.includes(customerName)) {
        return true;
      }
    }
    return false;
  }
}
