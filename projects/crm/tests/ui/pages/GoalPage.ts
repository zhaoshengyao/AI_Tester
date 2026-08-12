import { Page, Locator } from '@playwright/test';
import { BasePage, DialogBase } from './BasePage';

export class GoalPage extends BasePage {
  private searchInput: Locator;

  constructor(page: Page) {
    super(page);
    this.searchInput = page.locator('input[placeholder*="搜索"], input[placeholder*="目标"]').first();
  }

  async navigate(): Promise<void> {
    await super.navigate('/goal/goalList');
  }

  async isPageAvailable(): Promise<boolean> {
    try {
      await this.page.waitForSelector('.el-table, .el-card', { state: 'attached', timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  async clickAddButton(): Promise<GoalAddDialog> {
    console.log('🔍 查找目标管理新增按钮');
    
    const buttonStrategies = [
      { name: '设定目标按钮', selector: 'button', filter: (btn: Locator) => btn.filter({ hasText: /设定目标/ }).first() },
      { name: '新增按钮', selector: 'button', filter: (btn: Locator) => btn.filter({ hasText: /新增/ }).first() },
      { name: '创建目标按钮', selector: 'button', filter: (btn: Locator) => btn.filter({ hasText: /创建目标/ }).first() }
    ];

    let foundButton: Locator | null = null;
    for (const strategy of buttonStrategies) {
      const button = strategy.filter(this.page.locator(strategy.selector));
      if ((await button.count()) > 0 && await button.isVisible()) {
        foundButton = button;
        console.log(`✅ 使用策略"${strategy.name}"找到按钮`);
        break;
      }
    }

    if (!foundButton) {
      throw new Error('未找到设定目标按钮');
    }
    
    await foundButton.waitFor({ state: 'visible', timeout: 10000 });
    await foundButton.click();
    console.log('✅ 点击设定目标按钮');
    
    const dialogLocator = await this.waitForDialog();
    console.log('✅ 目标弹窗已打开');
    
    return new GoalAddDialog(this.page, dialogLocator);
  }

  async searchGoal(keyword: string): Promise<void> {
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

  async approveGoal(goalName: string): Promise<boolean> {
    console.log(`🔍 审核目标: ${goalName}`);
    
    await this.searchGoal(goalName);
    
    const approveButtons = this.page.locator('button').filter({ hasText: /审核通过/ });
    if ((await approveButtons.count()) > 0) {
      await approveButtons.first().click();
      console.log('✅ 点击审核通过按钮');
      await this.page.waitForTimeout(2000);
      
      const toast = this.page.locator('.el-message').last();
      const toastText = await toast.textContent();
      return toastText?.includes('成功') ?? false;
    }
    
    console.log('⚠️ 未找到审核通过按钮');
    return false;
  }

  async rejectGoal(goalName: string): Promise<boolean> {
    console.log(`🔍 驳回目标: ${goalName}`);
    
    await this.searchGoal(goalName);
    
    const rejectButtons = this.page.locator('button').filter({ hasText: /审核拒绝/ });
    if ((await rejectButtons.count()) > 0) {
      await rejectButtons.first().click();
      console.log('✅ 点击审核拒绝按钮');
      await this.page.waitForTimeout(2000);
      return true;
    }
    
    console.log('⚠️ 未找到审核拒绝按钮');
    return false;
  }

  async getGoalCount(): Promise<number> {
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

  async viewGoalStats(): Promise<void> {
    console.log('📊 查看目标统计');
    
    const statsTab = this.page.locator('.el-tabs__item').filter({ hasText: /统计|分析|对比/ }).first();
    if ((await statsTab.count()) > 0) {
      await statsTab.click();
      console.log('✅ 切换到统计Tab');
      await this.page.waitForTimeout(2000);
    } else {
      console.log('⚠️ 未找到统计Tab');
    }
  }
}

export class GoalAddDialog extends DialogBase {
  private nameInput: Locator;
  private amountInput: Locator;
  private _periodSelect: Locator;

  constructor(page: Page, dialog: Locator) {
    super(page, dialog);
    this.nameInput = dialog.locator('input[placeholder*="目标名称"], input[placeholder*="名称"]').first();
    this.amountInput = dialog.locator('input[placeholder*="金额"], input[placeholder*="目标额"]').first();
    this._periodSelect = dialog.locator('.el-select').first();
  }

  async fillGoalName(value: string): Promise<void> {
    if ((await this.nameInput.count()) > 0) {
      await this.nameInput.waitFor({ state: 'visible', timeout: 5000 });
      await this.nameInput.fill(value);
      console.log(`✅ 填写目标名称: ${value}`);
    }
  }

  async fillTargetAmount(value: string): Promise<void> {
    if ((await this.amountInput.count()) > 0) {
      await this.amountInput.waitFor({ state: 'visible', timeout: 5000 });
      await this.amountInput.fill(value);
      console.log(`✅ 填写目标金额: ${value}`);
    }
  }

  async selectPeriod(period: string): Promise<void> {
    const periodOptions = ['本月', '本季度', '本年', '月度', '季度', '年度'];
    if (periodOptions.includes(period)) {
      // 使用 _periodSelect 作为备选方案
      const select = this._periodSelect;
      if ((await select.count()) > 0) {
        await select.click();
        await this.page.getByText(period).click();
      } else {
        await this.selectByLabel('目标周期', period);
      }
    }
  }

  async fillSalesTarget(value: string): Promise<void> {
    await this.fillInputByLabel('销售目标', value);
  }

  async completeCreateGoal(): Promise<void> {
    const timestamp = Date.now();
    await this.fillGoalName(`测试目标_${timestamp}`);
    await this.fillTargetAmount('1000000');
    await this.selectPeriod('本季度');
    await this.submit();
  }
}
