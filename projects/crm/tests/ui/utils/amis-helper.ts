import { Page, Locator } from '@playwright/test';

export class AmisPageHelper {
  private page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async clickButtonByText(text: string | RegExp): Promise<void> {
    const selectors = [
      `button:has-text("${text}")`,
      `.amis-btn:has-text("${text}")`,
      `[type="button"]:has-text("${text}")`,
      `.btn:has-text("${text}")`
    ];

    for (const selector of selectors) {
      const button = this.page.locator(selector).first();
      if ((await button.count()) > 0 && await button.isVisible()) {
        await button.click();
        console.log(`✅ 点击按钮: ${text}`);
        return;
      }
    }

    const regexButton = this.page.locator('button').filter({ hasText: text }).first();
    if ((await regexButton.count()) > 0 && await regexButton.isVisible()) {
      await regexButton.click();
      console.log(`✅ 点击按钮: ${text}`);
      return;
    }

    throw new Error(`未找到按钮: ${text}`);
  }

  async fillInputByName(name: string, value: string): Promise<void> {
    const selectors = [
      `input[name="${name}"]`,
      `input[data-name="${name}"]`,
      `[data-amis-name="${name}"] input`,
      `.amis-input[name="${name}"]`,
      `.form-item[data-name="${name}"] input`
    ];

    for (const selector of selectors) {
      const input = this.page.locator(selector).first();
      if ((await input.count()) > 0) {
        await input.waitFor({ state: 'visible', timeout: 5000 });
        await input.fill(value);
        console.log(`✅ 填写 [${name}]: ${value}`);
        return;
      }
    }

    console.log(`⚠️ 未找到输入框 [${name}]`);
  }

  async fillInputByLabel(labelText: string, value: string): Promise<void> {
    const selectors = [
      `.amis-form-item:has-text("${labelText}") input`,
      `.form-item:has-text("${labelText}") input`,
      `.field-label:has-text("${labelText}") ~ input`,
      `.control-label:has-text("${labelText}") ~ input`,
      `label:has-text("${labelText}") + input`,
      `label:has-text("${labelText}") ~ input`
    ];

    for (const selector of selectors) {
      const input = this.page.locator(selector).first();
      if ((await input.count()) > 0) {
        await input.waitFor({ state: 'visible', timeout: 5000 });
        await input.fill(value);
        console.log(`✅ 填写 [${labelText}]: ${value}`);
        return;
      }
    }

    const labelElement = this.page.locator('.amis-form-item').filter({ hasText: labelText }).first();
    if ((await labelElement.count()) > 0) {
      const input = labelElement.locator('input, textarea').first();
      if ((await input.count()) > 0) {
        await input.waitFor({ state: 'visible', timeout: 5000 });
        await input.fill(value);
        console.log(`✅ 填写 [${labelText}]: ${value}`);
        return;
      }
    }

    console.log(`⚠️ 未找到输入框 [${labelText}]`);
  }

  async selectOptionByLabel(labelText: string, optionText: string): Promise<void> {
    const selectContainer = this.page.locator('.amis-form-item').filter({ hasText: labelText }).first();
    if ((await selectContainer.count()) === 0) {
      console.log(`⚠️ 未找到标签 [${labelText}]`);
      return;
    }

    const selectBox = selectContainer.locator('.amis-select, .el-select, select').first();
    if ((await selectBox.count()) === 0) {
      console.log(`⚠️ 未找到下拉框 [${labelText}]`);
      return;
    }

    await selectBox.click();
    await this.page.waitForTimeout(300);

    const option = this.page.locator('.amis-select-option, .el-select-dropdown__item, option').filter({ hasText: optionText }).first();
    if ((await option.count()) > 0 && await option.isVisible()) {
      await option.click();
      console.log(`✅ 选择 [${labelText}]: ${optionText}`);
      return;
    }

    console.log(`⚠️ 未找到选项 [${optionText}]`);
  }

  async waitForDialog(titleText?: string): Promise<Locator> {
    const selectors = [
      '.amis-modal',
      '.el-dialog',
      '[role="dialog"]',
      '.modal-dialog',
      '.popup-content'
    ];

    for (const selector of selectors) {
      let dialog: Locator;
      if (titleText) {
        dialog = this.page.locator(selector).filter({ hasText: titleText }).first();
      } else {
        dialog = this.page.locator(selector).first();
      }

      if ((await dialog.count()) > 0) {
        await dialog.waitFor({ state: 'visible', timeout: 15000 });
        console.log(`✅ 弹窗已打开`);
        return dialog;
      }
    }

    throw new Error('未找到弹窗');
  }

  async submitDialog(): Promise<void> {
    const submitSelectors = [
      'button:has-text("确定")',
      'button:has-text("提交")',
      '.amis-modal-footer button:has-text("确定")',
      '.el-dialog__footer button:has-text("确定")',
      '[type="submit"]'
    ];

    for (const selector of submitSelectors) {
      const button = this.page.locator(selector).first();
      if ((await button.count()) > 0 && await button.isVisible()) {
        await button.click();
        console.log(`✅ 点击确定/提交按钮`);
        await this.page.waitForTimeout(2000);
        return;
      }
    }

    throw new Error('未找到确定/提交按钮');
  }

  async closeDialog(): Promise<void> {
    const closeSelectors = [
      '.amis-modal-close',
      '.el-dialog__close',
      'button:has-text("取消")',
      '.modal-close',
      '[aria-label="关闭"]'
    ];

    for (const selector of closeSelectors) {
      const button = this.page.locator(selector).first();
      if ((await button.count()) > 0 && await button.isVisible()) {
        await button.click();
        console.log(`✅ 关闭弹窗`);
        return;
      }
    }

    console.log('⚠️ 未找到关闭按钮');
  }

  async search(keyword: string): Promise<void> {
    const searchSelectors = [
      'input[placeholder*="搜索"]',
      '.search-input',
      '.amis-search-input'
    ];

    for (const selector of searchSelectors) {
      const input = this.page.locator(selector).first();
      if ((await input.count()) > 0 && await input.isVisible()) {
        await input.fill(keyword);
        await input.press('Enter');
        await this.page.waitForTimeout(2000);
        console.log(`✅ 搜索: ${keyword}`);
        return;
      }
    }

    console.log('⚠️ 未找到搜索框');
  }

  async clickTableRow(rowIndex: number = 0): Promise<void> {
    const rowSelectors = [
      '.amis-table-row',
      '.el-table__row',
      'table tbody tr'
    ];

    for (const selector of rowSelectors) {
      const rows = this.page.locator(selector);
      if ((await rows.count()) > rowIndex) {
        await rows.nth(rowIndex).click();
        console.log(`✅ 点击第 ${rowIndex + 1} 行`);
        return;
      }
    }

    console.log('⚠️ 未找到表格行');
  }

  async getTableCellValue(rowIndex: number, columnIndex: number): Promise<string | null> {
    const cellSelectors = [
      `.amis-table-row:nth-child(${rowIndex + 1}) td:nth-child(${columnIndex + 1})`,
      `.el-table__row:nth-child(${rowIndex + 1}) td:nth-child(${columnIndex + 1})`,
      `table tbody tr:nth-child(${rowIndex + 1}) td:nth-child(${columnIndex + 1})`
    ];

    for (const selector of cellSelectors) {
      const cell = this.page.locator(selector).first();
      if ((await cell.count()) > 0 && await cell.isVisible()) {
        return cell.textContent();
      }
    }

    return null;
  }

  async goToPage(pageNumber: number): Promise<void> {
    const paginationSelectors = [
      '.el-pagination',
      '.amis-pagination',
      '[role="navigation"]'
    ];

    for (const selector of paginationSelectors) {
      const pagination = this.page.locator(selector).first();
      if ((await pagination.count()) > 0 && await pagination.isVisible()) {
        const pageButton = pagination.locator('button').filter({ hasText: String(pageNumber) }).first();
        if ((await pageButton.count()) > 0 && await pageButton.isVisible()) {
          await pageButton.click();
          await this.page.waitForTimeout(2000);
          console.log(`✅ 切换到第 ${pageNumber} 页`);
          return;
        }
      }
    }

    console.log('⚠️ 未找到分页控件或指定页码');
  }

  async waitForPageLoad(timeout: number = 30000): Promise<void> {
    await this.page.waitForLoadState('domcontentloaded', { timeout });
    await this.page.waitForTimeout(3000);
  }

  async getToastMessage(): Promise<string | null> {
    const toastSelectors = [
      '.amis-toast',
      '.el-message',
      '.toast-message',
      '[role="alert"]'
    ];

    for (const selector of toastSelectors) {
      const toast = this.page.locator(selector).first();
      if ((await toast.count()) > 0 && await toast.isVisible()) {
        const text = await toast.textContent();
        await this.page.waitForTimeout(1000);
        return text;
      }
    }

    return null;
  }
}