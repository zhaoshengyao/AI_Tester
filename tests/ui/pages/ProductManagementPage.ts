import { Page, Locator } from '@playwright/test';
import { BasePage, DialogBase } from './BasePage';

export class ProductManagementPage extends BasePage {
  private addButton: Locator;
  private searchInput: Locator;

  constructor(page: Page) {
    super(page);
    this.addButton = page.locator('button').filter({ hasText: /新增|添加/ }).first();
    this.searchInput = page.locator('input[placeholder*="搜索"]').first();
  }

  async navigate(): Promise<void> {
    await super.navigate('/product/ProductList');
  }

  async clickAddButton(): Promise<ProductAddDialog> {
    if ((await this.addButton.count()) === 0 || !(await this.addButton.isVisible())) {
      throw new Error('未找到新增按钮');
    }
    
    await this.addButton.waitFor({ state: 'visible', timeout: 10000 });
    await this.addButton.click();
    console.log('✅ 点击新增产品按钮');
    
    await this.page.waitForTimeout(3000);
    
    const dialog = await this.waitForDialog();
    return new ProductAddDialog(this.page, dialog);
  }

  async searchProduct(keyword: string): Promise<void> {
    await this.search(keyword);
  }

  async goToPage(pageNumber: number): Promise<void> {
    await super.goToPage(pageNumber);
  }
}

export class ProductAddDialog extends DialogBase {
  constructor(page: Page, dialog: Locator) {
    super(page, dialog);
  }

  async fillProductName(value: string): Promise<void> {
    await this.fillByLabel('产品名称', value);
  }

  async fillProductCode(value: string): Promise<void> {
    await this.fillByLabel('产品编码', value);
  }

  async fillCategory(value: string): Promise<void> {
    await this.selectByLabel('分类', value);
  }

  async fillPrice(value: string): Promise<void> {
    await this.fillByLabel('价格', value);
  }

  async fillStatus(value: string): Promise<void> {
    await this.selectByLabel('状态', value);
  }

  async fillDescription(value: string): Promise<void> {
    await this.fillByLabel('描述', value);
  }

  async completeCreateProduct(): Promise<void> {
    const timestamp = Date.now();
    
    await this.fillProductName(`测试产品_${timestamp}`);
    await this.fillProductCode(`PRO_${timestamp}`);
    await this.fillCategory('默认分类');
    await this.fillPrice('1000');
    await this.fillStatus('启用');
    await this.fillDescription('自动化测试创建');
    
    await this.submit();
  }
}