import { Page, Locator } from '@playwright/test';
import { BasePage, DialogBase } from './BasePage';

export class BusinessManagementPage extends BasePage {
  private addButton: Locator;
  private searchInput: Locator;
  private table: Locator;

  constructor(page: Page) {
    super(page);
    this.addButton = page.locator('button').filter({ hasText: /新增|添加/ }).first();
    this.searchInput = page.locator('input[placeholder*="搜索"]').first();
    this.table = page.locator('.el-table, .amis-table, table').first();
  }

  async navigate(): Promise<void> {
    await super.navigate('/business/BusinessOverview');
  }

  async clickAddButton(): Promise<BusinessAddDialog> {
    if ((await this.addButton.count()) === 0 || !(await this.addButton.isVisible())) {
      throw new Error('未找到新增按钮');
    }
    
    await this.addButton.waitFor({ state: 'visible', timeout: 10000 });
    await this.addButton.click();
    console.log('✅ 点击新增商机按钮');
    
    await this.page.waitForTimeout(3000);
    
    const dialog = await this.waitForDialog();
    return new BusinessAddDialog(this.page, dialog);
  }

  async searchBusiness(keyword: string): Promise<void> {
    await this.search(keyword);
  }

  async getBusinessCount(): Promise<number> {
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

  async clickBusinessRow(rowIndex: number = 0): Promise<void> {
    await this.clickTableRow(rowIndex);
  }

  async goToPage(pageNumber: number): Promise<void> {
    await super.goToPage(pageNumber);
  }
}

export class BusinessAddDialog extends DialogBase {
  constructor(page: Page, dialog: Locator) {
    super(page, dialog);
  }

  async fillBusinessName(value: string): Promise<void> {
    await this.fillByLabel('商机名称', value);
  }

  async fillCustomerName(value: string): Promise<void> {
    await this.fillByLabel('客户名称', value);
  }

  async fillContact(value: string): Promise<void> {
    await this.fillByLabel('联系人', value);
  }

  async fillAmount(value: string): Promise<void> {
    await this.fillByLabel('预估金额', value);
  }

  async fillStage(value: string): Promise<void> {
    await this.selectByLabel('阶段', value);
  }

  async fillStatus(value: string): Promise<void> {
    await this.selectByLabel('状态', value);
  }

  async fillDescription(value: string): Promise<void> {
    await this.fillByLabel('描述', value);
  }

  async completeCreateBusiness(): Promise<void> {
    const timestamp = Date.now();
    
    await this.fillBusinessName(`测试商机_${timestamp}`);
    await this.fillCustomerName(`测试客户_${timestamp}`);
    await this.fillContact('测试联系人');
    await this.fillAmount('100000');
    await this.fillStage('需求确认');
    await this.fillStatus('进行中');
    await this.fillDescription('自动化测试创建');
    
    await this.submit();
  }
}