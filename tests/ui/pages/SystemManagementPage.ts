import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

export class SystemManagementPage extends BasePage {
  private addButton: Locator;
  private searchInput: Locator;

  constructor(page: Page) {
    super(page);
    this.addButton = page.locator('button').filter({ hasText: /新增|添加/ }).first();
    this.searchInput = page.locator('input[placeholder*="搜索"]').first();
  }

  async navigate(url: string): Promise<void> {
    await super.navigate(url);
  }

  async closeOpenDialog(): Promise<void> {
    const closeSelectors = [
      '.el-overlay-dialog .el-dialog__close',
      '.el-overlay-dialog [aria-label="关闭"]',
      '.el-dialog__close',
      '.el-overlay-dialog button:has-text("取消")'
    ];

    for (const selector of closeSelectors) {
      const button = this.page.locator(selector).first();
      if ((await button.count()) > 0 && await button.isVisible()) {
        await button.click({ force: true });
        await this.page.waitForTimeout(1000);
        console.log('✅ 关闭了已打开的弹窗');
        return;
      }
    }
  }

  async clickAddButton(): Promise<SystemAddDialog> {
    await this.closeOpenDialog();
    if ((await this.addButton.count()) === 0 || !(await this.addButton.isVisible())) {
      console.log('⚠️ 未找到新增按钮');
      throw new Error('未找到新增按钮');
    }
    
    await this.addButton.click();
    console.log('✅ 点击新增按钮');
    await this.page.waitForTimeout(5000);
    
    return new SystemAddDialog(this.page);
  }

  async search(keyword: string): Promise<void> {
    if ((await this.searchInput.count()) > 0 && await this.searchInput.isVisible()) {
      await this.searchInput.fill(keyword);
      await this.searchInput.press('Enter');
      await this.page.waitForTimeout(2000);
      console.log(`✅ 搜索: ${keyword}`);
    } else {
      console.log('⚠️ 未找到搜索框');
    }
  }

  async getTableRowCount(): Promise<number> {
    const rows = this.page.locator('.el-table__row');
    return rows.count();
  }

  async clickTableRow(rowIndex: number = 0): Promise<void> {
    const rows = this.page.locator('.el-table__row');
    const count = await rows.count();
    if (count > rowIndex) {
      await rows.nth(rowIndex).click();
      console.log(`✅ 点击第 ${rowIndex + 1} 行`);
    }
  }
}

export class SystemAddDialog {
  private page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async fillInputByPlaceholder(placeholder: string, value: string): Promise<void> {
    const input = this.page.locator(`input[placeholder="${placeholder}"]`).first();
    if ((await input.count()) > 0 && await input.isVisible()) {
      await input.fill(value);
      console.log(`✅ 填写 [${placeholder}]: ${value}`);
    } else {
      console.log(`⚠️ 未找到输入框 [${placeholder}]`);
    }
  }

  async selectByPlaceholder(placeholder: string, optionText: string): Promise<void> {
    const select = this.page.locator('.el-select').filter({ hasText: placeholder }).first();
    if ((await select.count()) > 0 && await select.isVisible()) {
      await select.click();
      await this.page.waitForTimeout(300);
      const options = this.page.locator('.el-select-dropdown__item');
      const optionCount = await options.count();
      
      for (let i = 0; i < optionCount; i++) {
        const option = options.nth(i);
        const text = await option.textContent();
        if (text && text.includes(optionText)) {
          await option.click({ force: true });
          console.log(`✅ 选择 [${placeholder}]: ${optionText}`);
          return;
        }
      }
    } else {
      console.log(`⚠️ 未找到选择框 [${placeholder}]`);
    }
  }

  async submit(): Promise<void> {
    const submitButton = this.page.locator('.el-overlay-dialog button').filter({ hasText: /确\s*定/ }).first();
    if ((await submitButton.count()) > 0 && await submitButton.isVisible()) {
      await submitButton.click();
      console.log(`✅ 点击确定按钮`);
      await this.page.waitForTimeout(2000);
    } else {
      console.log('⚠️ 未找到确定按钮');
    }
  }

  async close(): Promise<void> {
    const closeBtn = this.page.locator('.el-overlay-dialog .el-dialog__close').first();
    if ((await closeBtn.count()) > 0 && await closeBtn.isVisible()) {
      await closeBtn.click();
      console.log(`✅ 关闭弹窗`);
    } else {
      const cancelBtn = this.page.locator('.el-overlay-dialog button').filter({ hasText: /取消/ }).first();
      if ((await cancelBtn.count()) > 0 && await cancelBtn.isVisible()) {
        await cancelBtn.click();
        console.log(`✅ 点击取消关闭弹窗`);
      }
    }
  }
}