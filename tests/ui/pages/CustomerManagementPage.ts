import { Page, Locator } from '@playwright/test';
import { BasePage, DialogBase } from './BasePage';
import { PresetOptions } from '../utils/select-utils';

export class CustomerManagementPage extends BasePage {
  private addButton: Locator;
  private searchInput: Locator;
  private pagination: Locator;

  constructor(page: Page) {
    super(page);
    this.addButton = page.locator('button').filter({ hasText: /新增|添加/ }).first();
    this.searchInput = page.locator('input[placeholder*="搜索"], input[placeholder*="客户"]').first();
    this.pagination = page.locator('.el-pagination, .pagination, [role="navigation"]');
  }

  async clickAddButton(): Promise<CustomerAddDialog> {
    console.log('🔍 查找新增按钮');
    
    if ((await this.addButton.count()) === 0 || !(await this.addButton.isVisible())) {
      throw new Error('未找到新增按钮');
    }
    
    await this.addButton.waitFor({ state: 'visible', timeout: 10000 });
    await this.addButton.click();
    console.log('✅ 点击新增按钮');
    
    await this.page.waitForTimeout(3000);
    
    let dialogLocator = this.page.locator('[role="dialog"]').first();
    if (await dialogLocator.count() === 0) {
      dialogLocator = this.page.locator('.modal').first();
    }
    if (await dialogLocator.count() === 0) {
      dialogLocator = this.page.locator('.el-dialog').first();
    }
    
    await dialogLocator.waitFor({ state: 'visible', timeout: 15000 });
    console.log('✅ 弹窗已打开');
    
    return new CustomerAddDialog(this.page, dialogLocator);
  }

  async searchCustomer(keyword: string): Promise<void> {
    if ((await this.searchInput.count()) === 0) {
      console.log('⚠️ 未找到搜索输入框');
      return;
    }
    
    await this.searchInput.waitFor({ state: 'visible', timeout: 5000 });
    await this.searchInput.fill(keyword);
    await this.searchInput.press('Enter');
    await this.page.waitForTimeout(2000);
    console.log(`✅ 搜索客户: ${keyword}`);
  }

  async goToPage(pageNumber: number): Promise<void> {
    const pageBtn = this.pagination.locator('button').filter({ hasText: String(pageNumber) }).first();
    if (await pageBtn.count() > 0 && await pageBtn.isVisible()) {
      await pageBtn.click();
      await this.page.waitForTimeout(2000);
      console.log(`✅ 切换到第 ${pageNumber} 页`);
    }
  }
}

export class CustomerAddDialog extends DialogBase {
  private nameInput: Locator;
  private codeInput: Locator;
  private contactInput: Locator;
  private phoneInput: Locator;
  private addressInput: Locator;

  constructor(page: Page, dialog: Locator) {
    super(page, dialog);
    this.nameInput = dialog.locator('input[placeholder*="客户名称"], input[placeholder*="名称"]').first();
    this.codeInput = dialog.locator('input[placeholder*="客户编码"], input[placeholder*="编码"]').first();
    this.contactInput = dialog.locator('input[placeholder*="联系人"]').first();
    this.phoneInput = dialog.locator('input[placeholder*="电话"], input[type="tel"]').first();
    this.addressInput = dialog.locator('textarea, input[placeholder*="地址"]').first();
  }

  async fillName(value: string): Promise<void> {
    if ((await this.nameInput.count()) > 0) {
      await this.nameInput.waitFor({ state: 'visible', timeout: 5000 });
      await this.nameInput.fill(value);
      console.log(`✅ 填写客户名称: ${value}`);
    }
  }

  async fillCode(value: string): Promise<void> {
    if ((await this.codeInput.count()) > 0) {
      await this.codeInput.waitFor({ state: 'visible', timeout: 5000 });
      await this.codeInput.fill(value);
      console.log(`✅ 填写客户编码: ${value}`);
    }
  }

  async fillContact(value: string): Promise<void> {
    if ((await this.contactInput.count()) > 0) {
      await this.contactInput.waitFor({ state: 'visible', timeout: 5000 });
      await this.contactInput.fill(value);
      console.log(`✅ 填写联系人: ${value}`);
    }
  }

  async fillPhone(value: string): Promise<void> {
    if ((await this.phoneInput.count()) > 0) {
      await this.phoneInput.waitFor({ state: 'visible', timeout: 5000 });
      await this.phoneInput.fill(value);
      console.log(`✅ 填写联系电话: ${value}`);
    }
  }

  async fillAddress(value: string): Promise<void> {
    if ((await this.addressInput.count()) > 0) {
      await this.addressInput.waitFor({ state: 'visible', timeout: 5000 });
      await this.addressInput.fill(value);
      console.log(`✅ 填写地址: ${value}`);
    }
  }

  async selectStatus(): Promise<void> {
    await this.selectByLabel('状态', PresetOptions.UserStatus);
  }

  async completeCreateCustomer(): Promise<void> {
    const timestamp = Date.now();
    
    await this.fillName(`测试客户_${timestamp}`);
    await this.fillCode(`CUST_${timestamp}`);
    await this.fillContact('测试联系人');
    await this.fillPhone('13800138000');
    await this.fillAddress('测试地址');
    
    await this.selectStatus();
    
    await this.submit();
  }
}