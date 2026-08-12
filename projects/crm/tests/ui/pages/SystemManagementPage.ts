import { Page, Locator } from '@playwright/test';
import { BasePage, DialogBase } from './BasePage';

export class SystemManagementPage extends BasePage {
  private addButton: Locator;
  private searchInput: Locator;

  constructor(page: Page) {
    super(page);
    this.addButton = page.locator('button').filter({ hasText: /新增|添加/ }).first();
    this.searchInput = page.locator('input[placeholder*="搜索"]').first();
  }

  async navigate(url: string): Promise<void> {
    // 如果是系统管理页面，先展开系统管理子菜单
    if (url.startsWith('/system/')) {
      await this.expandSystemManagementMenu();
    }
    await super.navigate(url);
  }

  async expandSystemManagementMenu(): Promise<void> {
    // 查找系统管理子菜单
    const systemSubMenu = this.page.locator('.el-sub-menu').filter({ hasText: '系统管理' }).first();
    if ((await systemSubMenu.count()) > 0) {
      // 检查是否已展开
      const isExpanded = await systemSubMenu.evaluate(el => {
        const arrow = el.querySelector('.el-sub-menu__icon-arrow');
        return arrow ? (arrow as HTMLElement).style.transform === 'rotate(180deg)' : false;
      });
      
      if (!isExpanded) {
        await systemSubMenu.click();
        console.log('✅ 展开系统管理子菜单');
        await this.page.waitForTimeout(1000);
      }
    }
  }

  async closeOpenDialog(): Promise<void> {
    const closeSelectors = [
      '.el-dialog__close',
      'button:has-text("取消")'
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
    
    const dialogLocator = await this.waitForDialog();
    return new SystemAddDialog(this.page, dialogLocator);
  }

  async search(keyword: string): Promise<void> {
    if ((await this.searchInput.count()) > 0 && await this.searchInput.isVisible()) {
      await this.searchInput.fill(keyword);
      console.log(`✅ 填写搜索关键词: ${keyword}`);
      
      // 在搜索框附近查找搜索按钮
      const parentForm = this.searchInput.locator('..').locator('..').locator('..');
      let searchButton = parentForm.locator('button').filter({ hasText: /搜索/ }).first();
      
      if ((await searchButton.count()) === 0 || !(await searchButton.isVisible())) {
        const searchButtons = this.page.locator('button').filter({ hasText: /搜索/ });
        const buttonCount = await searchButtons.count();
        
        for (let i = 0; i < buttonCount; i++) {
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

export class SystemAddDialog extends DialogBase {
  constructor(page: Page, dialog: Locator) {
    super(page, dialog);
  }

  async fillInputByPlaceholder(placeholder: string, value: string): Promise<void> {
    await this.fillByPlaceholder(placeholder, value);
  }

  async selectByPlaceholder(placeholder: string, optionText: string): Promise<void> {
    await this.selectByLabel(placeholder, optionText);
  }
}