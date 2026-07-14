import { Page, Locator } from '@playwright/test';
import { BasePage, DialogBase } from './BasePage';

export class QuotationManagementPage extends BasePage {
  private addButton: Locator;
  private searchInput: Locator;

  constructor(page: Page) {
    super(page);
    this.addButton = page.locator('button').filter({ hasText: /新增|添加/ }).first();
    this.searchInput = page.locator('input[placeholder*="搜索"]').first();
  }

  async navigate(): Promise<void> {
    await super.navigate('/quotation/quotationList');
  }

  async clickAddButton(): Promise<QuotationAddDialog> {
    if ((await this.addButton.count()) === 0 || !(await this.addButton.isVisible())) {
      throw new Error('未找到新增按钮');
    }
    
    await this.addButton.waitFor({ state: 'visible', timeout: 10000 });
    await this.addButton.click();
    console.log('✅ 点击新增报价按钮');
    
    await this.page.waitForTimeout(3000);
    
    const dialog = await this.waitForDialog();
    return new QuotationAddDialog(this.page, dialog);
  }

  async searchQuotation(keyword: string): Promise<void> {
    await this.search(keyword);
  }

  async goToPage(pageNumber: number): Promise<void> {
    await super.goToPage(pageNumber);
  }
}

export class QuotationAddDialog extends DialogBase {
  constructor(page: Page, dialog: Locator) {
    super(page, dialog);
  }

  async fillQuotationNo(value: string): Promise<void> {
    await this.fillByLabel('报价单号', value);
  }

  async fillCustomerName(value: string): Promise<void> {
    await this.fillByLabel('客户名称', value);
  }

  async fillContact(value: string): Promise<void> {
    await this.fillByLabel('联系人', value);
  }

  async fillTotalAmount(value: string): Promise<void> {
    await this.fillByLabel('总金额', value);
  }

  async fillStatus(value: string): Promise<void> {
    await this.selectByLabel('状态', value);
  }

  async completeCreateQuotation(): Promise<void> {
    const timestamp = Date.now();
    
    await this.fillQuotationNo(`QUO_${timestamp}`);
    await this.fillCustomerName(`测试客户_${timestamp}`);
    await this.fillContact('测试联系人');
    await this.fillTotalAmount('50000');
    await this.fillStatus('待确认');
    
    await this.submit();
  }
}