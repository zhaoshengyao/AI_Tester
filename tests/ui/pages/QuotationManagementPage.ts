import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

export class QuotationManagementPage extends BasePage {
  private pageLoaded: boolean = false;

  constructor(page: Page) {
    super(page);
  }

  async navigate(): Promise<void> {
    await super.navigate('/quotation/quotationList');
    await this.verifyPageLoaded();
  }

  async verifyPageLoaded(): Promise<void> {
    const pageIdentifiers = [
      this.page.locator('body').filter({ hasText: /报价/ }),
      this.page.locator('.el-page-header__title').filter({ hasText: /报价/ }),
      this.page.locator('h1, h2, h3').filter({ hasText: /报价/ })
    ];

    for (const identifier of pageIdentifiers) {
      try {
        await identifier.first().waitFor({ state: 'visible', timeout: 15000 });
        this.pageLoaded = true;
        console.log('✅ 报价管理页面验证通过');
        return;
      } catch {
        continue;
      }
    }

    console.log(`⚠️ 报价管理页面验证失败，当前URL: ${this.page.url()}`);
    this.pageLoaded = false;
  }

  async isPageAvailable(): Promise<boolean> {
    try {
      await this.verifyPageLoaded();
      return this.pageLoaded;
    } catch (error) {
      console.log(`⚠️ 报价管理页面不可用: ${error}`);
      return false;
    }
  }

  async clickAddButton(): Promise<QuotationAddPage> {
    if (!this.pageLoaded) {
      await this.verifyPageLoaded();
    }

    // 先检查所有按钮
    const allButtons = this.page.locator('button');
    const buttonCount = await allButtons.count();
    console.log(`📊 页面按钮数量: ${buttonCount}`);
    
    for (let i = 0; i < Math.min(buttonCount, 20); i++) {
      const btn = allButtons.nth(i);
      const text = await btn.textContent();
      const className = await btn.evaluate(e => e.className);
      if (text && text.trim()) {
        console.log(`  按钮${i}: text="${text.trim()}", class="${className.substring(0, 60)}"`);
      }
    }

    let foundButton: Locator | null = null;
    
    // 优先查找表格上方的"新增"按钮（不是顶部快捷操作栏的按钮）
    const addButton = this.page.locator('button').filter({ hasText: /^新增$/ }).first();
    if ((await addButton.count()) > 0 && await addButton.isVisible()) {
      const parentClass = await addButton.evaluate(e => e.parentElement?.className);
      // 排除顶部快捷操作栏的按钮
      if (!parentClass?.includes('quick-actions') && !parentClass?.includes('crm-search')) {
        foundButton = addButton;
        console.log('✅ 找到表格上方的"新增"按钮');
      }
    }
    
    // 如果没有找到，尝试其他策略
    if (!foundButton) {
      const targetTexts = ['创建报价', '新增报价', '新增'];
      
      for (const targetText of targetTexts) {
        const buttons = this.page.locator('button');
        const count = await buttons.count();
        
        for (let i = 0; i < count; i++) {
          const button = buttons.nth(i);
          const text = await button.textContent();
          if (text && text.trim() === targetText && await button.isVisible()) {
            // 检查父元素是否是快捷操作栏
            const parentClass = await button.evaluate(e => e.parentElement?.className);
            if (!parentClass?.includes('quick-actions') && !parentClass?.includes('crm-search')) {
              foundButton = button;
              break;
            }
          }
        }
        
        if (foundButton) break;
      }
    }

    if (!foundButton) {
      // 如果还是没找到，使用顶部的"创建报价"按钮
      const createQuotationBtn = this.page.locator('button').filter({ hasText: /创建报价/ }).first();
      if ((await createQuotationBtn.count()) > 0 && await createQuotationBtn.isVisible()) {
        foundButton = createQuotationBtn;
        console.log('⚠️ 仅找到顶部快捷操作栏的"创建报价"按钮');
      }
    }

    if (!foundButton) {
      throw new Error('未找到新增按钮');
    }
    
    const buttonText = await foundButton.textContent();
    await foundButton.waitFor({ state: 'visible', timeout: 10000 });
    
    await foundButton.click({ force: true });
    console.log(`✅ 点击[${buttonText}]按钮`);
    
    await this.page.waitForTimeout(3000);
    
    // 检查是否有弹窗或抽屉
    const visibleDialogs = this.page.locator('.el-dialog:visible');
    const visibleDrawers = this.page.locator('.el-drawer:visible');
    
    console.log(`📊 可见弹窗数量: ${await visibleDialogs.count()}`);
    console.log(`📊 可见抽屉数量: ${await visibleDrawers.count()}`);
    
    // 检查当前URL
    console.log(`📊 当前URL: ${this.page.url()}`);
    
    // 如果有弹窗或抽屉，等待表单加载
    if ((await visibleDialogs.count()) > 0 || (await visibleDrawers.count()) > 0) {
      console.log('✅ 使用弹窗/抽屉模式');
      return new QuotationAddPage(this.page);
    }
    
    // 等待页面跳转
    try {
      await this.page.waitForURL('**/quotation/quotationAdd', { timeout: 15000 });
      console.log(`✅ 页面已跳转到新增报价页面: ${this.page.url()}`);
    } catch {
      console.log(`⚠️ 等待URL超时，当前URL: ${this.page.url()}`);
    }
    
    return new QuotationAddPage(this.page);
  }

  async searchQuotation(keyword: string): Promise<void> {
    await this.search(keyword);
  }

  async goToPage(pageNumber: number): Promise<void> {
    await super.goToPage(pageNumber);
  }

  async getQuotationCount(): Promise<number> {
    const rowSelectors = ['.el-table__row', '.amis-table-row', 'table tbody tr'];
    for (const selector of rowSelectors) {
      const rows = this.page.locator(selector);
      const count = await rows.count();
      if (count > 0) {
        return count;
      }
    }
    return 0;
  }

  // ============ 报价审批功能 ============

  // 在列表页查找操作按钮（如提交审批、审批通过等）
  private async findActionButton(actionTexts: RegExp[]): Promise<{btn: Locator, text: string} | null> {
    // 先尝试在列表行内的操作按钮
    const rowButtons = this.page.locator('.el-table__row button, .el-table__row a');
    const rowCount = await rowButtons.count();
    
    for (let i = 0; i < rowCount; i++) {
      const btn = rowButtons.nth(i);
      try {
        if (await btn.isVisible()) {
          const text = await btn.textContent();
          if (text) {
            for (const pattern of actionTexts) {
              if (pattern.test(text.trim())) {
                console.log(`  🎯 找到行内操作按钮: "${text.trim()}"`);
                return { btn, text: text.trim() };
              }
            }
          }
        }
      } catch {}
    }
    
    // 尝试全局查找
    const allButtons = this.page.locator('button, a');
    const totalCount = await allButtons.count();
    
    for (let i = 0; i < totalCount; i++) {
      const btn = allButtons.nth(i);
      try {
        if (await btn.isVisible()) {
          const text = await btn.textContent();
          if (text) {
            for (const pattern of actionTexts) {
              if (pattern.test(text.trim())) {
                console.log(`  🎯 找到操作按钮: "${text.trim()}"`);
                return { btn, text: text.trim() };
              }
            }
          }
        }
      } catch {}
    }
    
    return null;
  }

  async submitForApproval(quotationName: string): Promise<boolean> {
    console.log(`📝 提交报价审批: ${quotationName}`);
    
    // 先搜索报价
    await this.searchQuotation(quotationName);
    await this.page.waitForTimeout(2000);
    
    // 打印页面按钮帮助调试
    const allButtons = this.page.locator('button, a');
    const buttonCount = await allButtons.count();
    console.log(`📊 报价列表页按钮数量: ${buttonCount}`);
    
    for (let i = 0; i < Math.min(buttonCount, 30); i++) {
      const btn = allButtons.nth(i);
      const text = await btn.textContent();
      if (text && text.trim()) {
        console.log(`  按钮${i}: "${text.trim()}"`);
      }
    }
    
    // 策略1：在列表页查找提交审批按钮
    const submitBtnTexts = [/提交审批/, /提交/, /送审/];
    const foundBtn = await this.findActionButton(submitBtnTexts);
    
    if (foundBtn) {
      await foundBtn.btn.click();
      console.log(`✅ 点击"${foundBtn.text}"按钮`);
      await this.page.waitForTimeout(2000);
      
      // 确认提交
      const confirmBtn = this.page.locator('.el-message-box button, .el-dialog button')
        .filter({ hasText: /确定|确认/ }).first();
      if ((await confirmBtn.count()) > 0) {
        await confirmBtn.click();
        console.log('✅ 确认提交审批');
        await this.page.waitForTimeout(2000);
      }
      
      const toast = this.page.locator('.el-message').last();
      const toastText = await toast.textContent();
      console.log(`📊 提交结果: ${toastText}`);
      return toastText?.includes('成功') ?? false;
    }
    
    // 策略2：进入详情页进行提交审批
    console.log('📊 列表页未找到提交审批按钮，尝试进入详情页...');
    const detailResult = await this.submitForApprovalInDetail(quotationName);
    if (detailResult) {
      return true;
    }
    
    console.log('⚠️ 未找到提交审批按钮');
    return false;
  }

  // 在详情页提交审批
  private async submitForApprovalInDetail(quotationName: string): Promise<boolean> {
    console.log(`📝 在详情页提交报价审批: ${quotationName}`);
    
    // 尝试点击查看详情
    const viewButtons = this.page.locator('button, a').filter({ hasText: /查看/ });
    if ((await viewButtons.count()) > 0) {
      await viewButtons.first().click();
      console.log('✅ 点击查看按钮进入详情页');
      await this.page.waitForTimeout(3000);
      
      // 在详情页查找提交审批按钮
      const submitBtnTexts = [/提交审批/, /提交/, /送审/];
      const foundBtn = await this.findActionButton(submitBtnTexts);
      
      if (foundBtn) {
        await foundBtn.btn.click();
        console.log(`✅ 在详情页点击"${foundBtn.text}"按钮`);
        await this.page.waitForTimeout(2000);
        
        // 确认
        const confirmBtn = this.page.locator('.el-message-box button, .el-dialog button')
          .filter({ hasText: /确定|确认/ }).first();
        if ((await confirmBtn.count()) > 0) {
          await confirmBtn.click();
          console.log('✅ 确认提交审批');
          await this.page.waitForTimeout(2000);
        }
        
        const toast = this.page.locator('.el-message').last();
        const toastText = await toast.textContent();
        return toastText?.includes('成功') ?? false;
      }
    }
    
    return false;
  }

  async approveQuotation(quotationName: string): Promise<boolean> {
    console.log(`📝 审批通过报价: ${quotationName}`);
    
    // 先搜索报价
    await this.searchQuotation(quotationName);
    await this.page.waitForTimeout(2000);
    
    // 策略1：在列表页查找审批通过按钮
    const approveBtnTexts = [/审批通过/, /通过/, /审核通过/];
    const foundBtn = await this.findActionButton(approveBtnTexts);
    
    if (foundBtn) {
      await foundBtn.btn.click();
      console.log(`✅ 点击"${foundBtn.text}"按钮`);
      await this.page.waitForTimeout(2000);
      
      // 确认审批
      const confirmBtn = this.page.locator('.el-message-box button, .el-dialog button')
        .filter({ hasText: /确定|确认/ }).first();
      if ((await confirmBtn.count()) > 0) {
        await confirmBtn.click();
        console.log('✅ 确认审批通过');
        await this.page.waitForTimeout(2000);
      }
      
      const toast = this.page.locator('.el-message').last();
      const toastText = await toast.textContent();
      console.log(`📊 审批结果: ${toastText}`);
      return toastText?.includes('成功') ?? false;
    }
    
    // 策略2：在详情页审批
    console.log('📊 列表页未找到审批通过按钮，尝试进入详情页...');
    return await this.approveQuotationInDetail(quotationName);
  }

  // 在详情页审批通过
  private async approveQuotationInDetail(quotationName: string): Promise<boolean> {
    console.log(`📝 在详情页审批通过报价: ${quotationName}`);
    
    // 尝试点击查看详情
    const viewButtons = this.page.locator('button, a').filter({ hasText: /查看/ });
    if ((await viewButtons.count()) > 0) {
      await viewButtons.first().click();
      console.log('✅ 点击查看按钮进入详情页');
      await this.page.waitForTimeout(3000);
      
      // 在详情页查找审批通过按钮
      const approveBtnTexts = [/审批通过/, /通过/, /审核通过/];
      const foundBtn = await this.findActionButton(approveBtnTexts);
      
      if (foundBtn) {
        await foundBtn.btn.click();
        console.log(`✅ 在详情页点击"${foundBtn.text}"按钮`);
        await this.page.waitForTimeout(2000);
        
        const confirmBtn = this.page.locator('.el-message-box button, .el-dialog button')
          .filter({ hasText: /确定|确认/ }).first();
        if ((await confirmBtn.count()) > 0) {
          await confirmBtn.click();
          console.log('✅ 确认审批通过');
          await this.page.waitForTimeout(2000);
        }
        
        const toast = this.page.locator('.el-message').last();
        const toastText = await toast.textContent();
        return toastText?.includes('成功') ?? false;
      }
    }
    
    return false;
  }

  async rejectQuotation(quotationName: string): Promise<boolean> {
    console.log(`📝 审批拒绝报价: ${quotationName}`);
    
    // 先搜索报价
    await this.searchQuotation(quotationName);
    await this.page.waitForTimeout(2000);
    
    // 查找审批拒绝按钮
    const rejectBtnTexts = [/审批拒绝/, /拒绝/, /驳回/];
    const foundBtn = await this.findActionButton(rejectBtnTexts);
    
    if (foundBtn) {
      await foundBtn.btn.click();
      console.log(`✅ 点击"${foundBtn.text}"按钮`);
      await this.page.waitForTimeout(2000);
      
      // 填写拒绝原因
      const rejectReasonInput = this.page.locator('.el-dialog textarea, .el-message-box textarea').first();
      if ((await rejectReasonInput.count()) > 0) {
        await rejectReasonInput.fill('自动化测试-审批拒绝');
        console.log('✅ 填写拒绝原因');
      }
      
      // 确认拒绝
      const confirmBtn = this.page.locator('.el-message-box button, .el-dialog button')
        .filter({ hasText: /确定|确认/ }).first();
      if ((await confirmBtn.count()) > 0) {
        await confirmBtn.click();
        console.log('✅ 确认审批拒绝');
        await this.page.waitForTimeout(2000);
      }
      
      return true;
    }
    
    console.log('⚠️ 未找到审批拒绝按钮');
    return false;
  }

  async exportQuotation(quotationName: string): Promise<boolean> {
    console.log(`📝 导出报价: ${quotationName}`);
    
    // 先搜索报价
    await this.searchQuotation(quotationName);
    await this.page.waitForTimeout(2000);
    
    // 查找导出按钮
    const exportBtnTexts = [/导出/, /下载/];
    const foundBtn = await this.findActionButton(exportBtnTexts);
    
    if (foundBtn) {
      await foundBtn.btn.click();
      console.log(`✅ 点击"${foundBtn.text}"按钮`);
      await this.page.waitForTimeout(2000);
      return true;
    }
    
    console.log('⚠️ 未找到导出按钮');
    return false;
  }

  async checkQuotationStatus(quotationName: string): Promise<string> {
    console.log(`📝 查看报价状态: ${quotationName}`);
    
    // 先搜索报价
    await this.searchQuotation(quotationName);
    await this.page.waitForTimeout(2000);
    
    // 查找状态列
    const statusPatterns = [/待审批/, /已审批/, /已拒绝/, /草稿/, /已提交/];
    for (const pattern of statusPatterns) {
      const statusCells = this.page.locator('.el-table__row .el-table__cell').filter({ hasText: pattern });
      if ((await statusCells.count()) > 0) {
        const statusText = await statusCells.first().textContent();
        console.log(`📊 报价状态: ${statusText}`);
        return statusText?.trim() ?? '未知';
      }
    }
    
    // 如果没找到状态，尝试查看第一行的所有cell
    const firstRowCells = this.page.locator('.el-table__row').first().locator('.el-table__cell');
    const cellCount = await firstRowCells.count();
    console.log(`📊 第一行列数: ${cellCount}`);
    
    for (let i = 0; i < cellCount; i++) {
      const cell = firstRowCells.nth(i);
      const text = await cell.textContent();
      if (text) {
        console.log(`  单元格${i}: "${text.trim()}"`);
        for (const pattern of statusPatterns) {
          if (pattern.test(text)) {
            return text.trim();
          }
        }
      }
    }
    
    return '未知';
  }
}

export class QuotationAddPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async fillCustomerName(value: string): Promise<void> {
    await this.selectWithSearch('客户名称', value, value);
  }

  async fillContact(value: string): Promise<void> {
    await this.fillInputByLabel('联系人', value);
  }

  async fillTotalAmount(value: string): Promise<void> {
    await this.fillInputByLabel('报价单金额', value);
  }

  async fillOwner(value: string): Promise<void> {
    await this.selectWithSearch('负责人', value, value);
  }

  async fillExpirationDate(value: string): Promise<void> {
    console.log('🔧 fillExpirationDate被调用，值:', value);
    
    // 查找包含"有效期至"的el-form-item（标签可能带*号）
    const formItems = this.page.locator('.el-form-item');
    const formItemCount = await formItems.count();
    console.log(`📊 表单元素数量: ${formItemCount}`);
    
    for (let i = 0; i < formItemCount; i++) {
      const formItem = formItems.nth(i);
      const label = formItem.locator('.el-form-item__label').first();
      if ((await label.count()) > 0) {
        const labelTextContent = await label.textContent();
        console.log(`  表单元素${i}: label="${labelTextContent?.trim() ?? 'null'}"`);
        
        // 标签可能是"有效期至"或"* 有效期至"
        if (labelTextContent && labelTextContent.includes('有效期至')) {
          console.log('✅ 找到有效期至字段');
          
          // 查找日期选择器相关元素
          const input = formItem.locator('.el-input').first();
          const inputInner = formItem.locator('.el-input__inner').first();
          
          console.log(`  el-input: ${(await input.count()) > 0}`);
          
          // 方法1：优先使用日历面板选择日期
          if ((await input.count()) > 0 && await input.isVisible()) {
            await input.click();
            console.log('✅ 点击有效期至输入区域');
            await this.page.waitForTimeout(2000);
            
            // 检查日历面板
            const calendarPanel = this.page.locator('.el-picker-panel').first();
            console.log(`  日历面板数量: ${await calendarPanel.count()}`);
            
            if ((await calendarPanel.count()) > 0 && await calendarPanel.isVisible()) {
              console.log('✅ 日历面板可见');
              
              const [year, month, day] = value.split('-').map(Number);
              console.log(`  要选择的日期: 年=${year}, 月=${month}, 日=${day}`);
              
              // 获取当前显示的年份和月份
              const yearLabel = calendarPanel.locator('.el-date-picker__header-label').first();
              const monthLabel = calendarPanel.locator('.el-date-picker__header-label').nth(1);
              const currentYearStr = await yearLabel.textContent();
              const currentMonthStr = await monthLabel.textContent();
              const currentYear = parseInt(currentYearStr?.replace('年', '').trim() ?? '0');
              const currentMonth = parseInt(currentMonthStr?.replace('月', '').trim() ?? '0');
              
              console.log(`  当前显示: ${currentYear}年${currentMonth}月`);
              
              // 切换年份（当前是2026年，目标是2025年，需要向左切换1次）
              if (year !== currentYear) {
                const yearDiff = year - currentYear;
                const yearBtn = yearDiff > 0 
                  ? calendarPanel.locator('.d-arrow-right').first()
                  : calendarPanel.locator('.d-arrow-left').first();
                
                for (let k = 0; k < Math.abs(yearDiff); k++) {
                  await yearBtn.click();
                  await this.page.waitForTimeout(500);
                }
                console.log(`  已切换年份到: ${year}年`);
              }
              
              // 切换月份（从当前月份切换到目标月份）
              if (month !== currentMonth) {
                const monthDiff = month - currentMonth;
                const monthBtn = monthDiff > 0
                  ? calendarPanel.locator('.arrow-right').first()
                  : calendarPanel.locator('.arrow-left').first();
                
                for (let k = 0; k < Math.abs(monthDiff); k++) {
                  await monthBtn.click();
                  await this.page.waitForTimeout(500);
                }
                console.log(`  已切换月份到: ${month}月`);
              }
              
              // 选择日期（使用.el-date-table-cell选择器）
              await this.page.waitForTimeout(500);
              const dayCells = calendarPanel.locator('.el-date-table .el-date-table-cell');
              const dayCount = await dayCells.count();
              console.log(`  日期单元格数量: ${dayCount}`);
              
              // 遍历查找目标日期
              for (let j = 0; j < dayCount; j++) {
                const cell = dayCells.nth(j);
                const text = await cell.textContent();
                const trimmedText = text?.trim() ?? '';
                if (trimmedText === day.toString()) {
                  // 检查是否禁用
                  const isDisabled = await cell.evaluate(el => el.classList.contains('disabled') || el.parentElement?.classList.contains('disabled'));
                  if (!isDisabled) {
                    await cell.click();
                    console.log(`✅ 选择日期: ${value}`);
                    await this.page.waitForTimeout(500);
                    
                    // 验证
                    const currentValue = await inputInner.inputValue();
                    console.log(`  输入框值: "${currentValue}"`);
                    return;
                  }
                }
              }
              
              console.log('⚠️ 未找到匹配的日期单元格');
            } else {
              console.log('⚠️ 日历面板不可见');
            }
          }
          
          // 方法2：尝试通过JavaScript直接设置Vue组件的值（使用更高级的方式）
          if ((await inputInner.count()) > 0) {
            const inputId = await inputInner.getAttribute('id');
            console.log(`  输入框ID: ${inputId}`);
            
            // 使用Vue的方式设置值
            await this.page.evaluate(({ inputId, value }) => {
              const input = document.getElementById(inputId as string);
              if (input) {
                // 尝试获取Vue组件实例
                const vueInstance = (input as any).__vue__ || (input as any)._vue || (input as any)._vnode?.componentInstance;
                if (vueInstance) {
                  vueInstance.$emit('input', value);
                  vueInstance.$emit('change', value);
                } else {
                  // 直接修改input值并触发事件
                  (input as HTMLInputElement).value = value;
                  input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
                  input.dispatchEvent(new Event('input', { bubbles: true }));
                  input.dispatchEvent(new Event('change', { bubbles: true }));
                }
              }
            }, { inputId, value });
            console.log(`✅ 通过JavaScript设置有效期至: ${value}`);
            await this.page.waitForTimeout(500);
            
            // 验证
            const currentValue = await inputInner.inputValue();
            console.log(`  输入框值: "${currentValue}"`);
            return;
          }
          
          // 方法3：尝试直接填写
          if ((await inputInner.count()) > 0) {
            await inputInner.fill(value);
            console.log(`✅ 直接填写有效期至: ${value}`);
            await this.page.keyboard.press('Enter');
            await this.page.waitForTimeout(500);
            return;
          }
        }
      }
    }
    
    console.log('⚠️ 未找到有效期至字段');
  }

  // 搜索+下拉选择（用于客户名称、负责人等需要搜索的字段）
  async selectWithSearch(labelText: string, searchKeyword: string, selectText: string): Promise<void> {
    // 查找包含指定label的el-form-item，使用精确匹配（label标签文本恰好是labelText）
    const formItems = this.page.locator('.el-form-item');
    const formItemCount = await formItems.count();
    console.log(`📊 表单元素数量: ${formItemCount}`);
    
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
    const visibleOptions = this.page.locator('.el-select-dropdown__item:visible');
    let visibleCount = await visibleOptions.count();
    
    if (searchKeyword) {
      const searchInput = this.page.locator('.el-select-dropdown input').first();
      if ((await searchInput.count()) > 0 && await searchInput.isVisible()) {
        await searchInput.fill(searchKeyword);
        console.log(`✅ 在${labelText}搜索框输入: ${searchKeyword}`);
        await this.page.waitForTimeout(1500);
        visibleCount = await visibleOptions.count();
      }
      
      // 使用filter查找选项
      const matchingOption = this.page.locator('.el-select-dropdown__item:visible').filter({ 
        hasText: new RegExp(selectText, 'i') 
      }).first();
      
      if ((await matchingOption.count()) > 0 && await matchingOption.isVisible()) {
        await matchingOption.click();
        const selectedText = await matchingOption.textContent();
        console.log(`✅ 选择${labelText}: ${selectedText?.trim()}`);
        await this.page.waitForTimeout(300);
        return;
      }
      
      // 如果filter没找到，尝试前20个可见选项
      console.log(`📊 ${labelText}可见选项数: ${Math.min(visibleCount, 20)}`);
      for (let j = 0; j < Math.min(visibleCount, 20); j++) {
        const option = visibleOptions.nth(j);
        const text = await option.textContent();
        const trimmedText = text ? text.trim() : '';
        if (j < 5) {
          console.log(`  选项${j}: ${trimmedText}`);
        }
        
        if (trimmedText.includes(selectText) || selectText.includes(trimmedText)) {
          await option.click();
          console.log(`✅ 选择${labelText}: ${trimmedText}`);
          await this.page.waitForTimeout(300);
          return;
        }
      }
    }
    
    // 回退策略：选择第一个可用的选项
    if (visibleCount > 0) {
      const firstOption = visibleOptions.first();
      if ((await firstOption.count()) > 0 && await firstOption.isVisible()) {
        const firstText = await firstOption.textContent();
        await firstOption.click();
        if (searchKeyword) {
          console.log(`⚠️ 未找到${labelText}选项 [${selectText}]，回退选择第一个`);
        } else {
          console.log(`✅ 选择${labelText}第一个选项: ${firstText?.trim()}`);
        }
        await this.page.waitForTimeout(300);
        return;
      }
    }
    console.log(`❌ ${labelText}没有可用选项`);
    await this.page.keyboard.press('Escape');
  }

  async fillDepartment(value: string): Promise<void> {
    await this.fillInputByLabel('归属部门', value);
  }

  async fillRemark(value: string): Promise<void> {
    await this.fillTextareaByLabel('备注', value);
  }

  async fillQuotationNo(value: string): Promise<void> {
    await this.fillInputByLabel('报价单号', value);
  }

  async fillStatus(value: string): Promise<void> {
    await this.selectElOptionByLabel('状态', value);
  }

  async completeCreateQuotation(customerName?: string, ownerName?: string): Promise<void> {
    // 总是尝试选择客户，如果找不到指定客户，回退策略会自动选择第一个可用的
    await this.fillCustomerName(customerName || '');
    
    // 总是尝试选择负责人，如果找不到指定负责人，回退策略会自动选择第一个可用的
    await this.fillOwner(ownerName || '');
    
    await this.fillTotalAmount('50000');
    await this.fillExpirationDate('2027-12-31'); // 有效期至（使用未来日期）
    await this.fillRemark('自动化测试创建');
    
    // 添加产品
    await this.addProductToQuotation();
    
    await this.submit();
  }

  async addProductToQuotation(): Promise<void> {
    // 点击报价单明细tab
    const detailTab = this.page.locator('.el-tabs__item').filter({ hasText: '报价单明细' }).first();
    if ((await detailTab.count()) > 0) {
      await detailTab.click();
      console.log('✅ 点击报价单明细tab');
      await this.page.waitForTimeout(2000);
      
      // 点击从产品列表批量添加按钮
      const addProductBtn = this.page.locator('button').filter({ hasText: '从产品列表批量添加' }).first();
      if ((await addProductBtn.count()) > 0 && await addProductBtn.isVisible()) {
        await addProductBtn.click();
        console.log('✅ 点击从产品列表批量添加按钮');
        await this.page.waitForTimeout(2000);
        
        // 等待弹窗出现
        const dialog = this.page.locator('.el-dialog').first();
        if ((await dialog.count()) > 0) {
          await dialog.waitFor({ state: 'visible', timeout: 10000 });
          console.log('✅ 产品选择弹窗出现');
          
          // 查找第一个产品的复选框
          const checkbox = dialog.locator('.el-table .el-checkbox__input').first();
          if ((await checkbox.count()) > 0 && await checkbox.isVisible()) {
            await checkbox.click();
            console.log('✅ 选择第一个产品');
            await this.page.waitForTimeout(500);
            
            // 点击确定按钮
            const confirmBtn = dialog.locator('.el-dialog__footer button').filter({ hasText: '确定' }).first();
            if ((await confirmBtn.count()) > 0) {
              await confirmBtn.click();
              console.log('✅ 确认添加产品');
              await this.page.waitForTimeout(1000);
              return;
            }
          }
        }
      }
    }
    
    console.log('⚠️ 未能添加产品');
  }

  

  private async fillTextareaByLabel(labelText: string, value: string): Promise<void> {
    const strategies = [
      {
        name: 'el-form-item',
        action: async () => {
          const formItem = this.page.locator('.el-form-item').filter({ hasText: labelText }).first();
          if ((await formItem.count()) === 0) return false;
          const textarea = formItem.locator('.el-textarea__inner').first();
          if ((await textarea.count()) > 0) {
            await textarea.waitFor({ state: 'visible', timeout: 10000 });
            await textarea.fill(value);
            console.log(`✅ 填写 [${labelText}]: ${value}`);
            return true;
          }
          return false;
        }
      },
      {
        name: 'placeholder',
        action: async () => {
          const textarea = this.page.locator(`textarea[placeholder*="${labelText}"]`).first();
          if ((await textarea.count()) > 0 && await textarea.isVisible()) {
            await textarea.fill(value);
            console.log(`✅ 填写 [${labelText}]: ${value}`);
            return true;
          }
          return false;
        }
      },
      {
        name: 'aria-label',
        action: async () => {
          const textarea = this.page.locator(`textarea[aria-label*="${labelText}"]`).first();
          if ((await textarea.count()) > 0 && await textarea.isVisible()) {
            await textarea.fill(value);
            console.log(`✅ 填写 [${labelText}]: ${value}`);
            return true;
          }
          return false;
        }
      }
    ];

    for (const strategy of strategies) {
      try {
        const success = await strategy.action();
        if (success) return;
      } catch (error) {
        console.log(`⚠️ 策略 [${strategy.name}] 失败: ${error}`);
        continue;
      }
    }

    console.log(`❌ 未找到标签为 [${labelText}] 的文本框`);
  }

  private lastSubmitMessage: string | null = null;

  private async waitForSubmitResult(): Promise<void> {
    // Wait for any existing messages to disappear first
    const existingMessages = this.page.locator('.el-message:visible');
    const existingCount = await existingMessages.count();
    if (existingCount > 0) {
      console.log(`📋 等待 ${existingCount} 个已有消息消失...`);
      await existingMessages.last().waitFor({ state: 'hidden', timeout: 3000 }).catch(() => {});
    }
    
    const messageSelector = '.el-message, .el-notification__content, .el-message-box__message, .el-form-item__error';
    
    // 先等待消息出现（在页面跳转前捕获）
    try {
      await this.page.waitForSelector(messageSelector, { state: 'visible', timeout: 3000 });
      // 捕获消息内容
      const messageEl = this.page.locator(messageSelector).first();
      const text = await messageEl.textContent();
      if (text && text.trim()) {
        this.lastSubmitMessage = text.trim();
        console.log(`📊 捕获到提交结果消息: ${this.lastSubmitMessage}`);
      }
    } catch {
      console.log('⚠️ 未检测到消息');
    }
    
    // 等待页面跳转或超时
    await Promise.race([
      this.page.waitForURL('**/quotationList', { timeout: 5000 }).catch(() => {}),
      this.page.waitForTimeout(3000)
    ]);
    
    await this.page.waitForTimeout(300);
  }

  getLastSubmitMessage(): string | null {
    return this.lastSubmitMessage;
  }

  async submit(): Promise<void> {
    const submitSelectors = [
      'button:has-text("确定")',
      'button:has-text("提交")',
      '.el-button--primary'
    ];

    let submitted = false;
    for (const selector of submitSelectors) {
      const button = this.page.locator(selector).first();
      if ((await button.count()) > 0 && await button.isVisible()) {
        try {
          await button.click({ force: true });
          console.log(`✅ 点击确定/提交按钮`);
          await this.waitForSubmitResult();
          submitted = true;
          break;
        } catch (error) {
          console.log(`⚠️ 点击按钮失败: ${error}`);
        }
      }
    }

    if (!submitted) {
      console.log('⚠️ 未找到确定/提交按钮');
    }
  }

  async close(): Promise<void> {
    const closeSelectors = [
      'button:has-text("取消")',
      'button:has-text("返回")',
      '.el-button--default'
    ];

    for (const selector of closeSelectors) {
      const button = this.page.locator(selector).first();
      if ((await button.count()) > 0 && await button.isVisible()) {
        await button.click();
        console.log(`✅ 关闭新增页面`);
        return;
      }
    }

    console.log('⚠️ 未找到关闭/返回按钮');
  }

  async goBack(): Promise<void> {
    await this.page.goBack();
    console.log(`✅ 返回上一页`);
  }
}