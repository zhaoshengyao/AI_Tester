import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

export class ClueManagementPage extends BasePage {
  private addButton: Locator;
  private searchInput: Locator;
  private table: Locator;
  private pagination: Locator;

  constructor(page: Page) {
    super(page);
    this.addButton = page.locator('button').filter({ hasText: /新增|添加/ }).first();
    this.searchInput = page.locator('input[placeholder*="搜索"]').first();
    this.table = page.locator('.el-table, .amis-table, table').first();
    this.pagination = page.locator('.el-pagination, .amis-pagination').first();
  }

  async navigate(): Promise<void> {
    await super.navigate('/marketing/clue');
  }

  async closeOpenDialog(): Promise<void> {
    const closeSelectors = [
      '.el-overlay-dialog .el-dialog__close',
      '.el-overlay-dialog [aria-label="关闭"]',
      '.el-dialog__close',
      'button:has-text("取消")'
    ];

    for (const selector of closeSelectors) {
      const button = this.page.locator(selector).first();
      if ((await button.count()) > 0 && await button.isVisible()) {
        await button.click();
        await this.page.waitForTimeout(1000);
        console.log('✅ 关闭了已打开的弹窗');
        return;
      }
    }
  }

  async clickAddButton(): Promise<ClueAddDialog> {
    await this.closeOpenDialog();

    if ((await this.addButton.count()) === 0 || !(await this.addButton.isVisible())) {
      throw new Error('未找到新增按钮');
    }
    
    await this.addButton.waitFor({ state: 'visible', timeout: 10000 });
    await this.addButton.click();
    console.log('✅ 点击新增线索按钮');
    
    await this.page.waitForTimeout(5000);
    
    return new ClueAddDialog(this.page);
  }

  async searchClue(keyword: string): Promise<void> {
    await this.search(keyword);
  }

  async getClueCount(): Promise<number> {
    const rowSelectors = ['.el-table__row', 'table tbody tr'];
    for (const selector of rowSelectors) {
      const rows = this.page.locator(selector);
      const count = await rows.count();
      if (count > 0) {
        return count;
      }
    }
    return 0;
  }

  async clickClueRow(rowIndex: number = 0): Promise<void> {
    await this.clickTableRow(rowIndex);
  }

  async goToPage(pageNumber: number): Promise<void> {
    await super.goToPage(pageNumber);
  }
}

export class ClueAddDialog {
  private page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async fillClueCode(value: string): Promise<void> {
    const input = this.page.locator('input[placeholder="请输入线索编码"]').first();
    if ((await input.count()) > 0 && await input.isVisible()) {
      await input.fill(value);
      console.log(`✅ 填写线索编码: ${value}`);
    } else {
      console.log('⚠️ 未找到线索编码输入框');
    }
  }

  async fillClueName(value: string): Promise<void> {
    const input = this.page.locator('input[placeholder="请输入线索名称"]').first();
    if ((await input.count()) > 0 && await input.isVisible()) {
      await input.fill(value);
      console.log(`✅ 填写线索名称: ${value}`);
    } else {
      console.log('⚠️ 未找到线索名称输入框');
    }
  }

  async fillCompanyName(value: string): Promise<void> {
    const input = this.page.locator('input[placeholder="请输入公司名称"]').first();
    if ((await input.count()) > 0 && await input.isVisible()) {
      await input.fill(value);
      console.log(`✅ 填写公司名称: ${value}`);
    } else {
      console.log('⚠️ 未找到公司名称输入框');
    }
  }

  async fillContact(value: string): Promise<void> {
    const input = this.page.locator('input[placeholder="请输入联系人"]').first();
    if ((await input.count()) > 0 && await input.isVisible()) {
      await input.fill(value);
      console.log(`✅ 填写联系人: ${value}`);
    } else {
      console.log('⚠️ 未找到联系人输入框');
    }
  }

  async fillPhone(value: string): Promise<void> {
    const input = this.page.locator('input[placeholder="请输入联系电话"]').first();
    if ((await input.count()) > 0 && await input.isVisible()) {
      await input.fill(value);
      console.log(`✅ 填写联系电话: ${value}`);
    } else {
      console.log('⚠️ 未找到联系电话输入框');
    }
  }

  async fillSource(value: string): Promise<void> {
    const dialogSelects = this.page.locator('.el-overlay-dialog .el-select');
    if ((await dialogSelects.count()) > 0) {
      const select = dialogSelects.first();
      if (await select.isVisible()) {
        await select.click();
        await this.page.waitForTimeout(300);
        const options = this.page.locator('.el-select-dropdown__item');
        const optionCount = await options.count();
        console.log(`下拉选项数量: ${optionCount}`);
        
        for (let i = 0; i < optionCount; i++) {
          const option = options.nth(i);
          const optionText = await option.textContent();
          if (optionText && optionText.includes(value)) {
            await option.click({ force: true });
            console.log(`✅ 选择来源: ${value}`);
            return;
          }
        }
        console.log('⚠️ 未找到来源选项');
      } else {
        console.log('⚠️ 来源选择框不可见');
      }
    } else {
      console.log('⚠️ 未找到来源选择框');
    }
  }

  async fillStatus(value: string): Promise<void> {
    const dialogSelects = this.page.locator('.el-overlay-dialog .el-select');
    const selectCount = await dialogSelects.count();
    if (selectCount > 1) {
      const select = dialogSelects.nth(1);
      if (await select.isVisible()) {
        await select.click();
        await this.page.waitForTimeout(300);
        const options = this.page.locator('.el-select-dropdown__item');
        const optionCount = await options.count();
        
        for (let i = 0; i < optionCount; i++) {
          const option = options.nth(i);
          const optionText = await option.textContent();
          if (optionText && optionText.includes(value)) {
            await option.click({ force: true });
            console.log(`✅ 选择状态: ${value}`);
            return;
          }
        }
        console.log('⚠️ 未找到状态选项');
      } else {
        console.log('⚠️ 状态选择框不可见');
      }
    } else {
      console.log('⚠️ 未找到足够的选择框');
    }
  }

  async completeCreateClue(): Promise<void> {
    const timestamp = Date.now();
    
    await this.fillClueCode(`CLUE_${timestamp}`);
    await this.fillClueName(`测试线索_${timestamp}`);
    await this.fillCompanyName(`测试公司_${timestamp}`);
    await this.fillContact('测试联系人');
    await this.fillPhone('13800138000');
    await this.fillSource('线上');
    await this.fillStatus('待跟进');
    
    await this.submit();
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
    const closeBtn = this.page.locator('.el-overlay-dialog .el-dialog__close, .el-overlay-dialog [aria-label="关闭"]').first();
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