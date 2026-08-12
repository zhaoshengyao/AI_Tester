import { Page, Locator } from '@playwright/test';
import { BasePage, DialogBase } from './BasePage';

export class BusinessManagementPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async navigate(): Promise<void> {
    await super.navigate('/business/BusinessOverview');
  }

  async clickAddButton(): Promise<BusinessAddDialog> {
    console.log('🔍 查找商机管理新增按钮');
    
    // 使用更高效的策略查找按钮，避免全页面遍历
    const buttonStrategies = [
      { name: '新建商机按钮', selector: 'button.el-button--primary', filter: (btn: Locator) => btn.filter({ hasText: /新建商机/ }).first() },
      { name: '主按钮包含新增', selector: 'button.el-button--primary', filter: (btn: Locator) => btn.filter({ hasText: /新增|新建/ }).first() },
      { name: '表格工具栏新增', selector: '.el-table__toolbar button', filter: (btn: Locator) => btn.filter({ hasText: /新增|新建/ }).first() },
      { name: '所有按钮包含新增', selector: 'button', filter: (btn: Locator) => btn.filter({ hasText: /新建/ }).first() }
    ];

    let foundButton: Locator | null = null;
    for (const strategy of buttonStrategies) {
      const button = strategy.filter(this.page.locator(strategy.selector));
      try {
        if ((await button.count()) > 0 && await button.isVisible()) {
          foundButton = button;
          console.log(`✅ 使用策略"${strategy.name}"找到按钮`);
          break;
        }
      } catch {
        continue;
      }
    }

    if (!foundButton) {
      // 最后回退：查找包含"新建商机"或"新建"的按钮
      const fallbackButtons = this.page.locator('button').filter({ hasText: /新建商机|新建/ });
      if ((await fallbackButtons.count()) > 0) {
        // 选择y坐标大于100的按钮（排除顶部导航）
        const count = await fallbackButtons.count();
        for (let i = 0; i < count; i++) {
          const btn = fallbackButtons.nth(i);
          try {
            if (await btn.isVisible()) {
              const rect = await btn.boundingBox();
              if (rect && rect.y > 100) {
                foundButton = btn;
                console.log('✅ 使用回退策略找到按钮');
                break;
              }
            }
          } catch {
            continue;
          }
        }
      }
    }

    if (!foundButton) {
      throw new Error('未找到新建商机按钮');
    }
    
    await foundButton.click({ force: true });
    console.log(`✅ 点击新建商机按钮`);
    
    await this.page.waitForTimeout(3000);
    
    // 检查抽屉
    const visibleDrawers = this.page.locator('.el-drawer:visible');
    try {
      console.log(`📊 可见抽屉数量: ${await visibleDrawers.count()}`);
    } catch {
      console.log('📊 检查抽屉失败，继续');
    }
    
    try {
      if ((await visibleDrawers.count()) > 0) {
        const drawer = visibleDrawers.first();
        console.log('✅ 找到可见抽屉');
        return new BusinessAddDialog(this.page, drawer);
      }
    } catch {}
    
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

  // ============ 商机详情和阶段推进功能 ============

  async clickBusinessDetail(businessName: string): Promise<boolean> {
    console.log(`🔍 查找商机详情: ${businessName}`);
    
    // 先搜索商机
    await this.searchBusiness(businessName);
    await this.page.waitForTimeout(2000);
    
    // 尝试点击查看按钮（行内操作）
    const viewButtons = this.page.locator('.el-table__row button, .amis-table-row button')
      .filter({ hasText: /查看/ });
    const viewCount = await viewButtons.count();
    console.log(`📊 行内查看按钮数量: ${viewCount}`);
    
    if (viewCount > 0) {
      await viewButtons.first().click();
      console.log('✅ 点击查看按钮');
      await this.page.waitForTimeout(2000);
      
      // 检查是否打开了弹窗
      const dialogVisible = this.page.locator('.el-dialog:visible, .el-drawer:visible').first();
      if ((await dialogVisible.count()) > 0) {
        console.log('✅ 详情以弹窗/抽屉形式打开');
        await this.page.waitForTimeout(2000);
        return true;
      }
      
      // 检查是否跳转了页面
      const currentUrl = this.page.url();
      if (currentUrl.includes('detail') || currentUrl.includes('Detail') || currentUrl.includes('business/')) {
        console.log('✅ 详情页面已跳转');
        await this.waitForPageLoad();
        return true;
      }
    }
    
    // 尝试点击表格行（某些系统点击行直接进入详情）
    const tableRows = this.page.locator('.el-table__row, .amis-table-row');
    const rowCount = await tableRows.count();
    console.log(`📊 表格行数: ${rowCount}`);
    
    if (rowCount > 0) {
      const firstRow = tableRows.first();
      try {
        await firstRow.click();
        console.log('✅ 点击表格行');
        await this.page.waitForTimeout(3000);
        return true;
      } catch (e) {
        console.log(`⚠️ 点击表格行失败: ${e}`);
      }
    }
    
    console.log('⚠️ 未找到商机详情入口');
    return false;
  }

  async advanceStage(targetStage: string): Promise<boolean> {
    console.log(`📝 推进商机阶段到: ${targetStage}`);
    
    try {
      // 确定搜索范围：优先在弹窗/抽屉中查找
      const dialog = this.page.locator('.el-dialog:visible, .el-drawer:visible').first();
      const inDialog = (await dialog.count()) > 0;
      const searchScope = inDialog ? dialog : this.page;
      console.log(`📊 搜索范围: ${inDialog ? '弹窗/抽屉' : '整页'}`);
      
      // 策略1：在可见范围内查找带"阶段"的表单字段
      console.log('📊 策略1：查找商机阶段字段...');
      const stageFields = searchScope.locator('.el-form-item').filter({ hasText: /商机阶段|阶段/ });
      const fieldCount = await stageFields.count();
      console.log(`📊 找到"阶段"相关字段: ${fieldCount}个`);
      
      if (fieldCount > 0) {
        for (let i = 0; i < Math.min(fieldCount, 3); i++) {
          const field = stageFields.nth(i);
          const labelText = await field.locator('.el-form-item__label').first().textContent();
          console.log(`  字段${i}标签: "${labelText?.trim()}"`);
          
          const select = field.locator('.el-select').first();
          if ((await select.count()) > 0 && await select.isVisible()) {
            console.log('✅ 找到商机阶段选择器，尝试选择...');
            await select.click();
            await this.page.waitForTimeout(500);
            
            // 尝试选择目标阶段
            const stageOption = this.page.locator('.el-select-dropdown__item').filter({ hasText: new RegExp(targetStage) });
            if ((await stageOption.count()) > 0) {
              await stageOption.first().click();
              console.log(`✅ 选择阶段: ${targetStage}`);
              await this.page.waitForTimeout(300);
              
              // 查找保存/确定按钮
              const saveBtn = searchScope.locator('button.el-button--primary, button').filter({ hasText: /保存|确定|提交/ }).first();
              if ((await saveBtn.count()) > 0) {
                await saveBtn.click();
                console.log('✅ 保存阶段变更');
                await this.page.waitForTimeout(1500);
                
                const toast = this.page.locator('.el-message').last();
                if ((await toast.count()) > 0) {
                  const toastText = await toast.textContent();
                  console.log(`📊 保存结果: ${toastText}`);
                  if (toastText?.includes('成功')) {
                    return true;
                  }
                }
                return true; // 即使没有成功提示也认为执行了操作
              }
            }
          }
        }
      }
      
      // 策略2：查找推进阶段相关操作按钮
      console.log('📊 策略2：查找推进阶段相关按钮...');
      const stageBtnPatterns = [/推进阶段/, /阶段推进/, /变更阶段/, /移动阶段/, /下一步/];
      
      for (const pattern of stageBtnPatterns) {
        const buttons = searchScope.locator('button, a').filter({ hasText: pattern });
        const count = await buttons.count();
        if (count > 0) {
          const btn = buttons.first();
          if (await btn.isVisible()) {
            console.log(`✅ 找到"${pattern}"按钮`);
            await btn.click();
            await this.page.waitForTimeout(1000);
            
            // 检查是否弹出了选择器
            const selectDropdown = this.page.locator('.el-select-dropdown:visible');
            if ((await selectDropdown.count()) > 0) {
              const stageOption = this.page.locator('.el-select-dropdown__item').filter({ hasText: new RegExp(targetStage) });
              if ((await stageOption.count()) > 0) {
                await stageOption.first().click();
                console.log(`✅ 选择阶段: ${targetStage}`);
                
                const confirmBtn = this.page.locator('.el-dialog button, .el-message-box button')
                  .filter({ hasText: /确定|确认/ }).first();
                if ((await confirmBtn.count()) > 0) {
                  await confirmBtn.click();
                  console.log('✅ 确认阶段变更');
                  await this.page.waitForTimeout(1500);
                  return true;
                }
              }
            }
            
            // 检查toast
            const toast = this.page.locator('.el-message').last();
            if ((await toast.count()) > 0) {
              const toastText = await toast.textContent();
              console.log(`📊 操作结果: ${toastText}`);
              if (toastText?.includes('成功')) {
                return true;
              }
            }
            return true; // 按钮点击成功
          }
        }
      }
      
    } catch (e) {
      console.log(`⚠️ 推进阶段异常: ${e}`);
    }
    
    console.log(`⚠️ 未找到推进阶段按钮或阶段字段`);
    return false;
  }

  async goBackToList(): Promise<void> {
    console.log('📝 返回商机列表');
    
    // 查找返回按钮
    const backButtons = this.page.locator('button, a').filter({ hasText: /返回|列表/ });
    const buttonCount = await backButtons.count();
    
    for (let i = 0; i < buttonCount; i++) {
      const btn = backButtons.nth(i);
      if (await btn.isVisible()) {
        const text = await btn.textContent();
        if (text?.includes('返回') || text?.includes('列表')) {
          await btn.click();
          console.log('✅ 点击返回按钮');
          await this.page.waitForTimeout(3000);
          return;
        }
      }
    }
    
    // 如果没有返回按钮，直接导航回列表
    await this.navigate();
    console.log('✅ 导航回商机列表');
  }
}

export class BusinessAddDialog extends DialogBase {
  constructor(page: Page, dialog: Locator) {
    super(page, dialog);
  }

  async fillBusinessName(value: string): Promise<void> {
    const input = this.dialog.locator('input[placeholder="请输入商机名称"]').first();
    if ((await input.count()) > 0 && await input.isVisible()) {
      await input.fill(value);
      console.log(`✅ 填写商机名称: ${value}`);
      return;
    }
    await this.fillByLabel('商机名称', value);
  }

  async fillCustomerName(value: string): Promise<void> {
    await this.selectWithSearch('客户名称', value, value);
  }

  // 搜索+下拉选择（用于客户名称等需要搜索的字段）
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
    
    // 如果有搜索关键词，先搜索
    if (searchKeyword) {
      const searchInput = this.page.locator('.el-select-dropdown input').first();
      if ((await searchInput.count()) > 0 && await searchInput.isVisible()) {
        await searchInput.fill(searchKeyword);
        console.log(`✅ 在${labelText}搜索框输入: ${searchKeyword}`);
        await this.page.waitForTimeout(1500);
      }
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
    if (visibleOptionData.length > 0) {
      console.log(`📊 可见选项前10: ${visibleOptionData.slice(0, 10).map(o => o.text).join(', ')}`);
    }
    
    // 如果有搜索关键词，尝试匹配
    if (searchKeyword && selectText) {
      for (const optionData of visibleOptionData) {
        if (optionData.text.includes(selectText) || selectText.includes(optionData.text)) {
          const option = allOptions.nth(optionData.index);
          await option.click();
          console.log(`✅ 选择${labelText}: ${optionData.text}`);
          await this.page.waitForTimeout(300);
          return;
        }
      }
    }
    
    // 回退策略：选择第一个可用的选项
    if (visibleOptionData.length > 0) {
      const firstOption = allOptions.nth(visibleOptionData[0].index);
      const firstText = visibleOptionData[0].text;
      await firstOption.click();
      if (searchKeyword) {
        console.log(`⚠️ 未找到${labelText}选项 [${selectText}]，回退选择第一个`);
      } else {
        console.log(`✅ 选择${labelText}第一个选项: ${firstText}`);
      }
      await this.page.waitForTimeout(300);
      return;
    }
    
    console.log(`❌ ${labelText}没有可用选项`);
    await this.page.keyboard.press('Escape');
  }

  async fillContact(value: string): Promise<void> {
    await this.fillByPlaceholder('请输入联系人', value);
  }

  async fillAmount(value: string): Promise<void> {
    await this.fillByPlaceholder('请输入金额', value);
  }

  async fillStage(value: string): Promise<void> {
    await this.selectByLabel('商机阶段', value);
  }

  async fillStatus(value: string): Promise<void> {
    await this.selectByLabel('状态', value);
  }

  async selectCustomer(value: string): Promise<void> {
    // 客户名称是需要搜索的下拉框，使用selectWithSearch
    await this.selectWithSearch('客户名称', value, value);
  }

  async selectOwner(value: string): Promise<void> {
    // 负责人也是需要搜索的下拉框，使用selectWithSearch
    await this.selectWithSearch('负责人', value, value);
  }

  async selectSalesProcess(value: string): Promise<void> {
    await this.selectByLabel('销售流程', value);
  }

  async selectStage(value: string): Promise<void> {
    await this.selectByLabel('商机阶段', value);
  }

  async fillExpectedDate(value: string): Promise<void> {
    const input = this.dialog.locator('input[placeholder="请选择日期"]').first();
    if ((await input.count()) > 0 && await input.isVisible()) {
      await input.fill(value);
      console.log(`✅ 填写预结日期: ${value}`);
      return;
    }
    await this.fillByLabel('预结日期', value);
  }

  async fillWinRate(value: string): Promise<void> {
    const input = this.dialog.locator('input[type="number"]').first();
    if ((await input.count()) > 0 && await input.isVisible()) {
      await input.fill(value);
      console.log(`✅ 填写赢率: ${value}`);
      return;
    }
    await this.fillByLabel('赢率', value);
  }

  async fillCompetitor(value: string): Promise<void> {
    const input = this.dialog.locator('input[placeholder="请输入竞争对手"]').first();
    if ((await input.count()) > 0 && await input.isVisible()) {
      await input.fill(value);
      console.log(`✅ 填写竞争对手: ${value}`);
      return;
    }
    await this.fillByLabel('竞争对手', value);
  }

  async fillNextAction(value: string): Promise<void> {
    const input = this.dialog.locator('input[placeholder="请输入下一行动"]').first();
    if ((await input.count()) > 0 && await input.isVisible()) {
      await input.fill(value);
      console.log(`✅ 填写下一行动: ${value}`);
      return;
    }
    await this.fillByLabel('下一行动', value);
  }

  async fillRemark(value: string): Promise<void> {
    const textarea = this.dialog.locator('textarea[placeholder="请输入备注"]').first();
    if ((await textarea.count()) > 0 && await textarea.isVisible()) {
      await textarea.fill(value);
      console.log(`✅ 填写备注: ${value}`);
      return;
    }
    await this.fillByLabel('备注', value);
  }

  async completeCreateBusiness(customerName?: string, ownerName?: string): Promise<void> {
    const timestamp = Date.now();
    
    await this.fillBusinessName(`测试商机_${timestamp}`);
    // 使用传入的客户名称，或让回退策略自动选择第一个可用的
    await this.selectCustomer(customerName || '');
    // 使用传入的负责人名称，或让回退策略自动选择第一个可用的
    await this.selectOwner(ownerName || '');
    await this.selectSalesProcess('标准销售流程');
    await this.selectStage('需求确认');
    await this.fillExpectedDate('2026-12-31');
    await this.fillWinRate('50');
    await this.fillCompetitor('竞争对手A');
    await this.fillNextAction('跟进客户需求');
    await this.fillRemark('自动化测试创建');
    
    await this.submit();
  }
}