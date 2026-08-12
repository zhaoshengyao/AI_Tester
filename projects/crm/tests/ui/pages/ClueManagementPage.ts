import { Page, Locator } from '@playwright/test';
import { BasePage, DialogBase } from './BasePage';

export class ClueManagementPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async navigate(): Promise<void> {
    console.log('🔄 正在加载线索池页面...');
    await super.navigate('/marketing/clue');
    console.log('⏳ 等待页面渲染...');
    
    try {
      await this.page.waitForSelector('.el-table, .el-empty', { timeout: 15000 });
      console.log('✅ 表格区域已加载');
    } catch (e) {
      console.log('⚠️ 等待表格超时，继续执行');
    }
    
    await this.page.waitForTimeout(1000);
    console.log('✅ 已导航到线索池页面');
  }

  private async waitForTableLoad(): Promise<void> {
    console.log('⏳ 等待页面元素加载...');
    
    await this.page.waitForTimeout(2000);
    
    const pageInfo = await this.page.evaluate(() => {
      const tables = document.querySelectorAll('.el-table, .table, [class*="table"]');
      const buttons = document.querySelectorAll('button');
      const visibleButtons = Array.from(buttons).filter(b => {
        const rect = b.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
      });
      return {
        tableCount: tables.length,
        buttonCount: buttons.length,
        visibleButtonCount: visibleButtons.length,
        buttonTexts: visibleButtons.map(b => b.textContent?.trim()).filter(t => t && t.length < 20)
      };
    });
    
    console.log(`📊 页面状态: 表格=${pageInfo.tableCount}, 按钮=${pageInfo.buttonCount}, 可见按钮=${pageInfo.visibleButtonCount}`);
    console.log(`📊 可见按钮文字: ${pageInfo.buttonTexts}`);
    
    if (pageInfo.tableCount === 0) {
      console.log('⚠️ 未检测到表格，继续等待...');
      await this.page.waitForTimeout(3000);
    }
  }

  async searchClue(keyword: string): Promise<void> {
    // 先尝试使用带"线索"placeholder的搜索框
    const searchInput = this.page.locator('input[placeholder*="线索"]').first();
    if ((await searchInput.count()) > 0 && await searchInput.isVisible()) {
      await searchInput.fill(keyword);
      console.log(`✅ 填写线索搜索关键词: ${keyword}`);
      
      // 在搜索框附近查找搜索按钮
      const parentForm = searchInput.locator('..').locator('..').locator('..');
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
        await searchInput.press('Enter');
        console.log('✅ 使用Enter键搜索');
      }
      
      await this.page.waitForTimeout(2000);
    } else {
      // 回退到通用搜索
      await super.search(keyword);
    }
  }

  async getClueCount(): Promise<number> {
    const rows = this.page.locator('.el-table__row');
    return await rows.count();
  }

  async clickClueRow(rowIndex: number = 0): Promise<void> {
    await this.clickTableRow(rowIndex);
  }

  async clickAddButton(): Promise<ClueAddDialog> {
    await this.waitForTableLoad();

    // 使用更高效的策略查找按钮，避免全页面遍历
    let foundButton: Locator | null = null;
    
    // 策略1：查找主按钮类的新增按钮
    const primaryAddButtons = this.page.locator('.el-button--primary').filter({ hasText: /新增/ });
    try {
      if ((await primaryAddButtons.count()) > 0 && await primaryAddButtons.first().isVisible()) {
        foundButton = primaryAddButtons.first();
        console.log('✅ 使用策略1：匹配primary类的新增按钮');
      }
    } catch {}
    
    // 策略2：查找表格工具栏的新增按钮
    if (!foundButton) {
      const toolbarButtons = this.page.locator('.el-table__toolbar button').filter({ hasText: /新增/ });
      try {
        if ((await toolbarButtons.count()) > 0 && await toolbarButtons.first().isVisible()) {
          foundButton = toolbarButtons.first();
          console.log('✅ 使用策略2：匹配表格工具栏的新增按钮');
        }
      } catch {}
    }
    
    // 策略3：查找不在顶部导航区域的新增按钮（排除顶部的"新增跟进"按钮）
    if (!foundButton) {
      const allAddButtons = this.page.locator('button').filter({ hasText: /新增/ });
      try {
        const count = await allAddButtons.count();
        for (let i = 0; i < count; i++) {
          const btn = allAddButtons.nth(i);
          try {
            if (await btn.isVisible()) {
              const rect = await btn.boundingBox();
              if (rect && rect.y > 50) { // 排除顶部导航区域的按钮
                foundButton = btn;
                console.log('✅ 使用策略3：匹配非顶部区域的新增按钮');
                break;
              }
            }
          } catch {
            continue;
          }
        }
      } catch {}
    }

    if (!foundButton) {
      throw new Error('未找到新增按钮');
    }

    const buttonText = await foundButton.textContent();
    console.log(`✅ 准备点击按钮: text="${buttonText || ''}"`);
    
    await foundButton.click();
    console.log('✅ 点击新增按钮');

    // 等待弹窗出现
    await this.page.waitForSelector('.el-dialog', { timeout: 15000 });
    console.log('✅ 弹窗已出现');
    
    // 使用locator而不是ElementHandle
    const dialogLocator = this.page.locator('.el-dialog').first();
    return new ClueAddDialog(this.page, dialogLocator);
  }

  async goToPage(pageNumber: number): Promise<void> {
    const pageInput = this.page.locator('.el-pagination .el-input__inner').first();
    if ((await pageInput.count()) > 0) {
      await pageInput.fill(String(pageNumber));
      await this.page.keyboard.press('Enter');
      console.log(`✅ 跳转到第 ${pageNumber} 页`);
      await this.page.waitForTimeout(2000);
    }
  }
}

export class ClueAddDialog extends DialogBase {
  constructor(page: Page, dialog: Locator) {
    super(page, dialog);
  }

  // 根据label定位输入框并填写
  async fillInputByLabel(labelText: string, value: string): Promise<void> {
    // 查找包含指定label的el-form-item
    const formItem = this.dialog.locator('.el-form-item').filter({ hasText: labelText }).first();
    if ((await formItem.count()) > 0 && await formItem.isVisible()) {
      // 在form-item内查找input
      const input = formItem.locator('input').first();
      if ((await input.count()) > 0 && await input.isVisible()) {
        await input.fill(value);
        console.log(`✅ 填写${labelText}: ${value}`);
        return;
      }
      // 尝试查找textarea
      const textarea = formItem.locator('textarea').first();
      if ((await textarea.count()) > 0 && await textarea.isVisible()) {
        await textarea.fill(value);
        console.log(`✅ 填写${labelText}: ${value}`);
        return;
      }
    }
    console.log(`⚠️ 未找到${labelText}输入框`);
  }

  // 根据label定位下拉选择器并选择
  async selectByLabel(labelText: string, value: string): Promise<void> {
    // 查找包含指定label的el-form-item
    const formItem = this.dialog.locator('.el-form-item').filter({ hasText: labelText }).first();
    if ((await formItem.count()) > 0 && await formItem.isVisible()) {
      // 在form-item内查找el-select
      const select = formItem.locator('.el-select').first();
      if ((await select.count()) > 0 && await select.isVisible()) {
        await select.click();
        console.log(`✅ 点击${labelText}下拉框`);
        
        // 等待下拉框出现
        await this.page.waitForTimeout(1500);
        
        // 查找所有.el-select-dropdown__item并过滤出可见的
        const allOptions = this.page.locator('.el-select-dropdown__item');
        const allCount = await allOptions.count();
        console.log(`📊 ${labelText}所有选项数: ${allCount}`);
        
        // 收集可见选项
        const visibleOptionData: Array<{text: string, index: number}> = [];
        for (let j = 0; j < allCount; j++) {
          const option = allOptions.nth(j);
          const isVisible = await option.isVisible();
          if (isVisible) {
            const text = await option.textContent();
            const trimmedText = text ? text.trim() : '';
            visibleOptionData.push({ text: trimmedText, index: j });
          }
        }
        
        console.log(`📊 ${labelText}可见选项数: ${visibleOptionData.length}`);
        console.log(`📊 可见选项: ${visibleOptionData.slice(0, 10).map(o => o.text).join(', ')}`);
        
        // 使用includes匹配
        for (const optionData of visibleOptionData) {
          if (optionData.text.includes(value) || value.includes(optionData.text)) {
            const option = allOptions.nth(optionData.index);
            await option.click();
            console.log(`✅ 选择${labelText}: ${optionData.text}`);
            await this.page.waitForTimeout(300);
            return;
          }
        }
        
        console.log(`⚠️ 未找到${labelText}选项 [${value}]`);
        await this.page.keyboard.press('Escape');
        return;
      }
      
      // 如果没有el-select，尝试查找input类型的选择器（可能是自定义选择器）
      const input = formItem.locator('input').first();
      if ((await input.count()) > 0 && await input.isVisible()) {
        await input.click();
        console.log(`✅ 点击${labelText}输入框（可能是选择器）`);
        
        // 等待下拉框出现
        await this.page.waitForTimeout(1500);
        
        // 查找所有.el-select-dropdown__item并过滤出可见的
        const allOptions = this.page.locator('.el-select-dropdown__item');
        const allCount = await allOptions.count();
        console.log(`📊 ${labelText}所有选项数: ${allCount}`);
        
        // 收集可见选项
        const visibleOptionData: Array<{text: string, index: number}> = [];
        for (let j = 0; j < allCount; j++) {
          const option = allOptions.nth(j);
          const isVisible = await option.isVisible();
          if (isVisible) {
            const text = await option.textContent();
            const trimmedText = text ? text.trim() : '';
            visibleOptionData.push({ text: trimmedText, index: j });
          }
        }
        
        console.log(`📊 ${labelText}可见选项数: ${visibleOptionData.length}`);
        console.log(`📊 可见选项: ${visibleOptionData.slice(0, 10).map(o => o.text).join(', ')}`);
        
        // 使用includes匹配
        for (const optionData of visibleOptionData) {
          if (optionData.text.includes(value) || value.includes(optionData.text)) {
            const option = allOptions.nth(optionData.index);
            await option.click();
            console.log(`✅ 选择${labelText}: ${optionData.text}`);
            await this.page.waitForTimeout(300);
            return;
          }
        }
        
        console.log(`⚠️ 未找到${labelText}选项 [${value}]`);
        await this.page.keyboard.press('Escape');
        return;
      }
    }
    console.log(`⚠️ 未找到${labelText}选择器`);
  }

  async fillCustomerName(value: string): Promise<void> {
    await this.fillInputByLabel('公司', value);
  }

  async fillClueName(value: string): Promise<void> {
    await this.fillInputByLabel('姓名', value);
  }

  async fillSource(value: string): Promise<void> {
    await this.selectByLabel('来源', value);
  }

  async fillStatus(value: string): Promise<void> {
    await this.selectByLabel('状态', value);
  }

  // 搜索+下拉选择（用于负责人等需要搜索的字段）
  async selectWithSearch(labelText: string, searchKeyword: string, selectText: string): Promise<void> {
    // 查找包含指定label的el-form-item，使用精确匹配（label标签文本恰好是labelText）
    const formItems = this.dialog.locator('.el-form-item');
    const formItemCount = await formItems.count();
    
    let targetFormItem = null;
    for (let i = 0; i < formItemCount; i++) {
      const formItem = formItems.nth(i);
      const label = formItem.locator('.el-form-item__label').first();
      if ((await label.count()) > 0) {
        const labelTextContent = await label.textContent();
        if (labelTextContent && labelTextContent.trim() === labelText) {
          targetFormItem = formItem;
          break;
        }
      }
    }
    
    if (!targetFormItem) {
      console.log(`⚠️ 未找到${labelText}字段的el-form-item`);
      return;
    }
    
    console.log(`✅ 找到${labelText}字段的el-form-item`);
    
    // 在form-item内查找.el-select或.el-input
    const select = targetFormItem.locator('.el-select').first();
    const input = targetFormItem.locator('.el-input').first();
    
    if ((await select.count()) > 0 && await select.isVisible()) {
      await select.click();
      console.log(`✅ 点击${labelText}下拉框`);
    } else if ((await input.count()) > 0 && await input.isVisible()) {
      await input.click();
      console.log(`✅ 点击${labelText}输入框`);
    } else {
      console.log(`⚠️ ${labelText}字段内未找到.el-select或.el-input`);
      return;
    }
    
    // 等待下拉框出现
    await this.page.waitForTimeout(1500);
    
    // 查找搜索输入框（通常在.el-select-dropdown内）
    const searchInput = this.page.locator('.el-select-dropdown input').first();
    if ((await searchInput.count()) > 0 && await searchInput.isVisible()) {
      // 在搜索框中输入关键词
      await searchInput.fill(searchKeyword);
      console.log(`✅ 在${labelText}搜索框输入: ${searchKeyword}`);
      
      // 等待搜索结果加载
      await this.page.waitForTimeout(1500);
    }
    
    // 查找所有可见的下拉选项
    const allOptions = this.page.locator('.el-select-dropdown__item');
    const allCount = await allOptions.count();
    console.log(`📊 ${labelText}搜索后选项数: ${allCount}`);
    
    // 收集可见选项
    const visibleOptionData: Array<{text: string, index: number}> = [];
    for (let j = 0; j < allCount; j++) {
      const option = allOptions.nth(j);
      const isVisible = await option.isVisible();
      if (isVisible) {
        const text = await option.textContent();
        const trimmedText = text ? text.trim() : '';
        visibleOptionData.push({ text: trimmedText, index: j });
      }
    }
    
    console.log(`📊 ${labelText}可见选项数: ${visibleOptionData.length}`);
    console.log(`📊 可见选项: ${visibleOptionData.slice(0, 10).map(o => o.text).join(', ')}`);
    
    // 使用includes匹配
    for (const optionData of visibleOptionData) {
      if (optionData.text.includes(selectText) || selectText.includes(optionData.text)) {
        const option = allOptions.nth(optionData.index);
        await option.click();
        console.log(`✅ 选择${labelText}: ${optionData.text}`);
        await this.page.waitForTimeout(300);
        return;
      }
    }
    
    console.log(`⚠️ 未找到${labelText}选项 [${selectText}]`);
    await this.page.keyboard.press('Escape');
  }

  async fillOwner(value: string): Promise<void> {
    // 负责人字段需要先搜索再选择
    await this.selectWithSearch('负责人', value, value);
  }

  async fillIndustry(value: string): Promise<void> {
    await this.selectByLabel('1级行业', value);
  }

  async fillContact(value: string): Promise<void> {
    await this.fillInputByLabel('姓名', value);
  }

  async fillPhone(value: string): Promise<void> {
    await this.fillInputByLabel('电话', value);
  }

  async fillEmail(value: string): Promise<void> {
    await this.fillInputByLabel('邮箱', value);
  }

  async fillAddress(value: string): Promise<void> {
    await this.fillInputByLabel('地址', value);
  }

  async fillDepartment(value: string): Promise<void> {
    await this.fillInputByLabel('部门', value);
  }

  async fillPosition(value: string): Promise<void> {
    await this.fillInputByLabel('职务', value);
  }

  async fillMobile(value: string): Promise<void> {
    await this.fillInputByLabel('手机', value);
  }

  async fillExternalOwner(value: string): Promise<void> {
    await this.fillInputByLabel('外部负责人', value);
  }

  async fillMarketActivity(value: string): Promise<void> {
    await this.selectByLabel('市场活动', value);
  }

  async fillExpectedAmount(value: string): Promise<void> {
    await this.fillInputByLabel('预计金额', value);
  }

  async fillNextFollowupTime(value: string): Promise<void> {
    await this.fillInputByLabel('下次跟进时间', value);
  }

  async fillRemark(value: string): Promise<void> {
    await this.fillInputByLabel('备注', value);
  }

  async fillSalesDetail(value: string): Promise<void> {
    await this.fillInputByLabel('销售线索详情', value);
  }

  async fillSecondIndustry(value: string): Promise<void> {
    await this.selectByLabel('2级行业', value);
  }

  async fillWebsite(value: string): Promise<void> {
    await this.fillInputByLabel('网站', value);
  }

  async submit(): Promise<void> {
    // 列出dialog内所有按钮用于调试
    const allButtons = this.dialog.locator('button');
    const buttonCount = await allButtons.count();
    const buttonTexts: string[] = [];
    for (let i = 0; i < buttonCount; i++) {
      const btn = allButtons.nth(i);
      const text = await btn.textContent();
      buttonTexts.push(text ? text.trim() : '');
    }
    console.log(`📊 dialog内按钮数量: ${buttonCount}`);
    console.log(`📊 dialog内按钮文本: ${buttonTexts.join(', ')}`);
    
    // 策略1：查找包含"确定"的按钮
    const confirmButton = this.dialog.locator('button').filter({ hasText: /确定/ }).first();
    if ((await confirmButton.count()) > 0 && await confirmButton.isVisible()) {
      await confirmButton.click();
      console.log('✅ 点击确定按钮');
      return;
    }
    
    // 策略2：查找包含"提交"的按钮
    const submitButton = this.dialog.locator('button').filter({ hasText: /提交/ }).first();
    if ((await submitButton.count()) > 0 && await submitButton.isVisible()) {
      await submitButton.click();
      console.log('✅ 点击提交按钮');
      return;
    }
    
    // 策略3：查找primary按钮（通常是主要操作按钮）
    const primaryButton = this.dialog.locator('.el-button--primary').first();
    if ((await primaryButton.count()) > 0 && await primaryButton.isVisible()) {
      const text = await primaryButton.textContent();
      await primaryButton.click();
      console.log(`✅ 点击primary按钮: ${text}`);
      return;
    }
    
    // 策略4：查找.el-dialog__footer内的按钮
    const footerButton = this.dialog.locator('.el-dialog__footer button').first();
    if ((await footerButton.count()) > 0 && await footerButton.isVisible()) {
      const text = await footerButton.textContent();
      await footerButton.click();
      console.log(`✅ 点击footer按钮: ${text}`);
      return;
    }
    
    console.log('⚠️ 未找到确定/提交按钮');
  }

  async close(): Promise<void> {
    // 弹窗按钮文本是"取 消"（中间有空格）
    const cancelButton = this.dialog.locator('button').filter({ hasText: /取消/ }).first();
    if ((await cancelButton.count()) > 0 && await cancelButton.isVisible()) {
      await cancelButton.click();
      console.log('✅ 点击取消按钮');
      return;
    }
    console.log('⚠️ 未找到取消按钮');
  }
}
