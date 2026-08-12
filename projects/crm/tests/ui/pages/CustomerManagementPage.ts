import { Page, Locator } from '@playwright/test';
import { BasePage, DialogBase } from './BasePage';
import { PresetOptions } from '../utils/select-utils';

export class CustomerManagementPage extends BasePage {
  private searchInput: Locator;
  private pagination: Locator;

  constructor(page: Page) {
    super(page);
    this.searchInput = page.locator('input[placeholder*="搜索"], input[placeholder*="客户"]').first();
    this.pagination = page.locator('.el-pagination, .pagination, [role="navigation"]');
  }

  async navigateToCustomerDetail(): Promise<void> {
    const detailButtons = this.page.locator('button').filter({ hasText: /详情/ });
    if ((await detailButtons.count()) > 0) {
      const firstDetailBtn = detailButtons.first();
      await firstDetailBtn.click();
      console.log('✅ 点击详情按钮');
      await this.page.waitForTimeout(5000);

      const contactTab = this.page.locator('.el-tabs__item').filter({ hasText: '联系人' }).first();
      if ((await contactTab.count()) > 0) {
        await contactTab.click();
        console.log('✅ 切换到联系人tab');
        await this.page.waitForTimeout(2000);
      }
    } else {
      throw new Error('未找到详情按钮');
    }
  }

  async isContactTab(): Promise<boolean> {
    const contactTab = this.page.locator('.el-tabs__item').filter({ hasText: '联系人' }).first();
    if ((await contactTab.count()) === 0) {
      return false;
    }
    const isActive = await contactTab.evaluate((el) => el.classList.contains('is-active'));
    return isActive;
  }

  async clickAddContactButton(): Promise<ContactAddDialog> {
    console.log('🔍 查找新增联系人按钮');
    
    const buttonStrategies = [
      { name: '新增联系人按钮', selector: 'button', filter: (btn: Locator) => btn.filter({ hasText: /新增联系人/ }).first() },
      { name: '新增按钮', selector: 'button', filter: (btn: Locator) => btn.filter({ hasText: /新增|添加/ }).first() }
    ];

    let foundButton: Locator | null = null;
    for (const strategy of buttonStrategies) {
      const button = strategy.filter(this.page.locator(strategy.selector));
      if ((await button.count()) > 0 && await button.isVisible()) {
        foundButton = button;
        break;
      }
    }

    if (!foundButton) {
      throw new Error('未找到新增联系人按钮');
    }
    
    await foundButton.waitFor({ state: 'visible', timeout: 10000 });
    await foundButton.click();
    console.log('✅ 点击新增联系人按钮');
    
    const dialogLocator = await this.waitForDialog();
    console.log('✅ 联系人弹窗已打开');
    
    return new ContactAddDialog(this.page, dialogLocator);
  }

  async clickAddButton(): Promise<CustomerAddDialog> {
    console.log('🔍 查找新增按钮');

    const buttonStrategies = [
      { name: '添加客户按钮', selector: 'button', filter: (btn: Locator) => btn.filter({ hasText: /添加客户/ }).first() },
      { name: '新增按钮', selector: 'button', filter: (btn: Locator) => btn.filter({ hasText: /新增|添加/ }).first() }
    ];

    let foundButton: Locator | null = null;
    for (const strategy of buttonStrategies) {
      const button = strategy.filter(this.page.locator(strategy.selector));
      if ((await button.count()) > 0 && await button.isVisible()) {
        foundButton = button;
        break;
      }
    }

    if (!foundButton) {
      throw new Error('未找到新增按钮');
    }
    
    await foundButton.waitFor({ state: 'visible', timeout: 10000 });
    await foundButton.click();
    console.log('✅ 点击新增按钮');
    
    const dialogLocator = await this.waitForDialog();
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
    console.log(`✅ 填写搜索关键词: ${keyword}`);
    
    // 在搜索框附近查找搜索按钮
    const parentForm = this.searchInput.locator('..').locator('..').locator('..');
    let searchButton = parentForm.locator('button').filter({ hasText: /搜索/ }).first();
    
    // 如果父容器内没有搜索按钮，尝试页面上的搜索按钮
    if ((await searchButton.count()) === 0 || !(await searchButton.isVisible())) {
      const searchButtons = this.page.locator('button').filter({ hasText: /搜索/ });
      const buttonCount = await searchButtons.count();
      
      for (let i = 0; i < buttonCount; i++) {
        const btn = searchButtons.nth(i);
        if (await btn.isVisible()) {
          const rect = await btn.boundingBox();
          if (rect && rect.y > 100) { // 排除顶部导航的按钮
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
      // 如果没有搜索按钮，使用Enter键
      await this.searchInput.press('Enter');
      console.log('✅ 使用Enter键搜索');
    }
    
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

  async getCustomerCount(): Promise<number> {
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

  async clickCustomerRow(rowIndex: number = 0): Promise<void> {
    const rowSelectors = ['.amis-table-row', '.el-table__row', 'table tbody tr'];
    for (const selector of rowSelectors) {
      const rows = this.page.locator(selector);
      const count = await rows.count();
      if (count > rowIndex) {
        await rows.nth(rowIndex).click();
        console.log(`✅ 点击第 ${rowIndex + 1} 行客户`);
        return;
      }
    }
    console.log(`⚠️ 未找到第 ${rowIndex + 1} 行客户`);
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
    await this.selectByLabel('状态', PresetOptions.UserStatus[0]);
  }

  async completeCreateCustomer(): Promise<void> {
    const timestamp = Date.now();
    
    await this.fillName(`测试客户_${timestamp}`);
    await this.fillCode(`CUST_${timestamp}`);
    await this.fillContact('测试联系人');
    await this.fillPhone('13800138000');
    await this.fillAddress('测试地址');
    
    await this.submit();
  }
}

export class ContactAddDialog extends DialogBase {
  private nameInput: Locator;
  private phoneInput: Locator;
  private emailInput: Locator;

  constructor(page: Page, dialog: Locator) {
    super(page, dialog);
    this.nameInput = dialog.locator('input[placeholder*="姓名"], input[placeholder*="名称"]').first();
    this.phoneInput = dialog.locator('input[placeholder*="手机号"], input[placeholder*="电话"], input[type="tel"]').first();
    this.emailInput = dialog.locator('input[placeholder*="邮箱"], input[type="email"]').first();
  }

  async fillName(value: string): Promise<void> {
    if ((await this.nameInput.count()) > 0) {
      await this.nameInput.waitFor({ state: 'visible', timeout: 5000 });
      await this.nameInput.fill(value);
      console.log(`✅ 填写联系人姓名: ${value}`);
    }
  }

  async fillPhone(value: string): Promise<void> {
    if ((await this.phoneInput.count()) > 0) {
      await this.phoneInput.waitFor({ state: 'visible', timeout: 5000 });
      await this.phoneInput.fill(value);
      console.log(`✅ 填写手机号: ${value}`);
    }
  }

  async fillEmail(value: string): Promise<void> {
    if ((await this.emailInput.count()) > 0) {
      await this.emailInput.waitFor({ state: 'visible', timeout: 5000 });
      await this.emailInput.fill(value);
      console.log(`✅ 填写邮箱: ${value}`);
    }
  }

  async completeCreateContact(): Promise<void> {
    const timestamp = Date.now();
    
    await this.fillName(`测试联系人_${timestamp}`);
    await this.fillPhone('13900139000');
    await this.fillEmail(`test_${timestamp}@example.com`);
    
    await this.submit();
  }
}