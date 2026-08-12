import { Page, Locator } from '@playwright/test';

export class BasePage {
  protected page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async navigate(url: string): Promise<void> {
    console.log(`🔄 导航到: ${url}`);
    
    if (!url.startsWith('http') && !url.startsWith('/')) {
      url = '/' + url;
    }

    // 不再强制添加 /index# 前缀，直接使用history模式路由
    await this.page.goto(url);
    await this.waitForPageLoad();
    console.log(`✅ 页面加载完成: ${this.page.url()}`);
  }

  async clickButtonByText(text: string | RegExp): Promise<void> {
    const patterns = [
      text instanceof RegExp ? text : new RegExp(text),
      text instanceof RegExp ? text : new RegExp(text.replace(/./g, '$&\\s*'))
    ];

    for (const pattern of patterns) {
      const button = this.page.locator('button').filter({ hasText: pattern }).first();
      if ((await button.count()) > 0 && await button.isVisible()) {
        await button.click();
        console.log(`✅ 点击按钮: ${text}`);
        return;
      }
    }

    const selectors = [
      `button:has-text("${text}")`,
      `.el-button:has-text("${text}")`,
      `[type="button"]:has-text("${text}")`
    ];

    for (const selector of selectors) {
      const button = this.page.locator(selector).first();
      if ((await button.count()) > 0 && await button.isVisible()) {
        await button.click();
        console.log(`✅ 点击按钮: ${text}`);
        return;
      }
    }

    throw new Error(`未找到按钮: ${text}`);
  }

  protected async fillInputByLabel(labelText: string, value: string): Promise<void> {
    const strategies = [
      { name: 'el-form-item', action: async () => {
        const formItem = this.page.locator('.el-form-item').filter({ hasText: labelText }).first();
        if ((await formItem.count()) > 0) {
          const input = formItem.locator('.el-input__inner, input:not(.el-select__input), textarea').first();
          if ((await input.count()) > 0) {
            await input.waitFor({ state: 'visible', timeout: 10000 });
            await input.fill(value);
            console.log(`✅ 填写 [${labelText}]: ${value}`);
            return true;
          }
        }
        return false;
      }},
      { name: 'placeholder', action: async () => {
        const placeholderInput = this.page.locator(`input[placeholder*="${labelText}"]`).first();
        if ((await placeholderInput.count()) > 0) {
          await placeholderInput.waitFor({ state: 'visible', timeout: 10000 });
          await placeholderInput.fill(value);
          console.log(`✅ 通过占位符填写 [${labelText}]: ${value}`);
          return true;
        }
        return false;
      }},
      { name: 'aria-label', action: async () => {
        const ariaInput = this.page.locator(`input[aria-label*="${labelText}"], textarea[aria-label*="${labelText}"]`).first();
        if ((await ariaInput.count()) > 0) {
          await ariaInput.waitFor({ state: 'visible', timeout: 10000 });
          await ariaInput.fill(value);
          console.log(`✅ 通过aria-label填写 [${labelText}]: ${value}`);
          return true;
        }
        return false;
      }},
      { name: 'label for', action: async () => {
        const label = this.page.locator('label').filter({ hasText: labelText }).first();
        if ((await label.count()) > 0) {
          const forAttr = await label.getAttribute('for');
          if (forAttr) {
            const input = this.page.locator(`#${forAttr}`).first();
            if ((await input.count()) > 0) {
              await input.waitFor({ state: 'visible', timeout: 10000 });
              await input.fill(value);
              console.log(`✅ 通过label for填写 [${labelText}]: ${value}`);
              return true;
            }
          }
        }
        return false;
      }},
      { name: 'span label', action: async () => {
        const labelSpan = this.page.locator('span').filter({ hasText: labelText }).first();
        if ((await labelSpan.count()) > 0) {
          const parentForm = labelSpan.locator('..').locator('.el-form-item').first();
          if ((await parentForm.count()) > 0) {
            const input = parentForm.locator('.el-input__inner, input:not(.el-select__input), textarea').first();
            if ((await input.count()) > 0) {
              await input.waitFor({ state: 'visible', timeout: 10000 });
              await input.fill(value);
              console.log(`✅ 通过span标签填写 [${labelText}]: ${value}`);
              return true;
            }
          }
        }
        return false;
      }}
    ];

    for (const strategy of strategies) {
      const success = await strategy.action();
      if (success) return;
    }

    console.log(`⚠️ 未找到输入框 [${labelText}]`);
  }

  async selectElOptionByLabel(labelText: string, optionText: string, container?: Locator): Promise<void> {
    const targetContainer = container || this.page;

    const labelSelector = targetContainer.locator('.el-form-item__label').filter({ hasText: labelText }).first();
    if ((await labelSelector.count()) === 0) {
      console.log(`⚠️ 未找到标签 [${labelText}]`);
      return;
    }

    const formItem = labelSelector.locator('..').first();
    const selectInForm = formItem.locator('.el-select').first();

    if ((await selectInForm.count()) > 0) {
      await this.selectElOptionFromLocator(selectInForm, optionText, labelText);
      return;
    }

    console.log(`⚠️ 未找到下拉框 [${labelText}]`);
  }

  private async selectElOptionFromLocator(selectLocator: Locator, optionText: string, labelText: string): Promise<void> {
    for (let retry = 0; retry < 3; retry++) {
      try {
        await selectLocator.click();
        await this.page.waitForTimeout(500);

        try {
          await this.page.waitForSelector('.el-select-dropdown__item', { timeout: 8000 });
        } catch {
          console.log(`⚠️ 第 ${retry + 1} 次等待下拉选项超时，重新点击`);
          continue;
        }

        const option = this.page.locator('.el-select-dropdown__item').filter({ hasText: optionText }).first();
        if ((await option.count()) > 0 && await option.isVisible()) {
          await option.click();
          console.log(`✅ 选择 [${labelText}]: ${optionText}`);
          return;
        }

        const allOptions = this.page.locator('.el-select-dropdown__item');
        const count = await allOptions.count();
        for (let i = 0; i < Math.min(count, 50); i++) {
          const opt = allOptions.nth(i);
          const text = await opt.textContent();
          if (text && text.trim().includes(optionText)) {
            await opt.click();
            console.log(`✅ 选择 [${labelText}]: ${optionText}`);
            return;
          }
        }

        const searchInput = selectLocator.locator('.el-select__input').first();
        if ((await searchInput.count()) > 0 && await searchInput.isVisible()) {
          await searchInput.fill(optionText);
          await searchInput.press('Enter');
          await this.page.waitForTimeout(1000);

          const filteredOption = this.page.locator('.el-select-dropdown__item').filter({ hasText: optionText }).first();
          if ((await filteredOption.count()) > 0 && await filteredOption.isVisible()) {
            await filteredOption.click();
            console.log(`✅ 搜索并选择 [${labelText}]: ${optionText}`);
            return;
          }

          const firstFiltered = this.page.locator('.el-select-dropdown__item').first();
          if ((await firstFiltered.count()) > 0 && await firstFiltered.isVisible()) {
            await firstFiltered.click();
            console.log(`✅ 搜索后选择第一个选项 [${labelText}]`);
            return;
          }
        }

        break;
      } catch (error) {
        console.log(`⚠️ 第 ${retry + 1} 次尝试失败: ${error}`);
        await this.page.waitForTimeout(500);
      }
    }

    console.log(`⚠️ 未找到选项 [${optionText}]`);
  }

  async search(keyword: string): Promise<void> {
    const searchInput = this.page.locator('input[placeholder*="搜索"]').first();
    if ((await searchInput.count()) > 0 && await searchInput.isVisible()) {
      await searchInput.fill(keyword);
      console.log(`✅ 填写搜索关键词: ${keyword}`);
      
      // 在搜索框附近查找搜索按钮
      const parentForm = searchInput.locator('..').locator('..').locator('..');
      let searchButton = parentForm.locator('button').filter({ hasText: /搜索/ }).first();
      
      // 如果父容器内没有搜索按钮，尝试页面上的搜索按钮，但优先选择表格区域的
      if ((await searchButton.count()) === 0) {
        // 查找表格工具栏或表单区域的搜索按钮
        const searchButtons = this.page.locator('.el-table__toolbar button, .el-form button, button').filter({ hasText: /搜索/ });
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
        await searchInput.press('Enter');
        console.log('✅ 使用Enter键搜索');
      }
      
      await this.page.waitForTimeout(2000);
      console.log(`✅ 搜索: ${keyword}`);
    } else {
      console.log('⚠️ 未找到搜索框');
    }
  }

  async waitForDialog(titleText?: string): Promise<Locator> {
    const maxRetries = 15;
    const retryDelay = 800;
    
    for (let retry = 0; retry < maxRetries; retry++) {
      const dialogSelectors = ['.el-dialog', '.el-drawer'];

      for (const selector of dialogSelectors) {
        let dialog: Locator;
        if (titleText) {
          dialog = this.page.locator(selector).filter({ hasText: titleText }).first();
        } else {
          dialog = this.page.locator(selector).first();
        }

        if ((await dialog.count()) > 0) {
          try {
            const rect = await dialog.evaluate(el => {
              const r = el.getBoundingClientRect();
              const hasForm = el.querySelectorAll('.el-form').length > 0;
              const hasBody = el.querySelectorAll('.el-dialog__body, .el-drawer__body').length > 0;
              return { width: r.width, height: r.height, hasForm, hasBody };
            });
            
            if (rect.width > 100 && rect.height > 100 && rect.hasBody) {
              console.log(`✅ 弹窗已打开: ${selector} (尺寸: ${Math.round(rect.width)}x${Math.round(rect.height)}, 有表单: ${rect.hasForm})`);
              return dialog;
            } else {
              console.log(`⚠️ 弹窗 ${selector} 存在但未完全加载(尺寸: ${Math.round(rect.width)}x${Math.round(rect.height)}, 有body: ${rect.hasBody})，等待加载...`);
            }
          } catch {
            console.log(`⚠️ 弹窗 ${selector} 检测异常`);
          }
        }
      }

      if (retry < maxRetries - 1) {
        await this.page.waitForTimeout(retryDelay);
      }
    }

    console.log(`⚠️ 弹窗多次检测未通过，尝试其他方式...`);
    await this.page.waitForTimeout(2000);

    const visibleContent = this.page.locator('.el-dialog__body:visible, .el-drawer__body:visible');
    if ((await visibleContent.count()) > 0) {
      const wrapper = visibleContent.locator('..').locator('..').first();
      console.log(`✅ 通过内容区域找到弹窗/抽屉`);
      return wrapper;
    }

    const dialogHeader = this.page.locator('.el-dialog__header:visible, .el-drawer__header:visible');
    if ((await dialogHeader.count()) > 0) {
      const wrapper = dialogHeader.locator('..').first();
      console.log(`✅ 通过标题区域找到弹窗/抽屉`);
      return wrapper;
    }

    const hasTitleDialog = this.page.locator('.el-dialog__title').first();
    if ((await hasTitleDialog.count()) > 0) {
      const wrapper = hasTitleDialog.locator('..').locator('..').first();
      console.log(`✅ 通过标题文本找到弹窗`);
      return wrapper;
    }

    const dialogInfo = await this.page.evaluate(() => {
      const overlays = document.querySelectorAll('.el-overlay-dialog, .el-dialog, [role="dialog"], .el-drawer');
      const results: Array<{ index: number; class: string; isVisible: boolean; hasContent: boolean; width: number; height: number; children: number }> = [];
      overlays.forEach((el: Element, index: number) => {
        const style = window.getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        const childCount = el.querySelectorAll('.el-dialog__body, .el-dialog__header, .el-drawer__body, .el-drawer__header').length;
        results.push({
          index,
          class: el.className,
          isVisible: style.display !== 'none' && style.visibility !== 'hidden',
          hasContent: childCount > 0,
          width: rect.width,
          height: rect.height,
          children: childCount
        });
      });
      return results;
    });

    console.log(`📊 弹窗检测信息: ${JSON.stringify(dialogInfo)}`);

    const visibleDialogs = dialogInfo.filter(d => d.isVisible && d.hasContent);
    if (visibleDialogs.length > 0) {
      const selector = `.${visibleDialogs[0].class.split(' ').filter(c => c).join('.')}`;
      console.log(`✅ JS检测到可见弹窗: ${selector} (尺寸: ${visibleDialogs[0].width}x${visibleDialogs[0].height})`);
      return this.page.locator(selector).first();
    }

    const allOverlays = await this.page.locator('.el-overlay-dialog, .el-dialog').count();
    if (allOverlays > 0) {
      const lastOverlay = this.page.locator('.el-overlay-dialog, .el-dialog').last();
      console.log(`⚠️ 返回最后一个弹窗元素`);
      return lastOverlay;
    }

    throw new Error('未找到弹窗');
  }

  async clickTableRow(rowIndex: number = 0): Promise<void> {
    const rows = this.page.locator('.el-table__row');
    if ((await rows.count()) > rowIndex) {
      await rows.nth(rowIndex).click();
      console.log(`✅ 点击第 ${rowIndex + 1} 行`);
    } else {
      console.log('⚠️ 未找到表格行');
    }
  }

  async goToPage(pageNumber: number): Promise<void> {
    const pagination = this.page.locator('.el-pagination').first();
    if ((await pagination.count()) > 0 && await pagination.isVisible()) {
      const pageButton = pagination.locator('button').filter({ hasText: String(pageNumber) }).first();
      if ((await pageButton.count()) > 0 && await pageButton.isVisible()) {
        await pageButton.click();
        await this.page.waitForTimeout(2000);
        console.log(`✅ 切换到第 ${pageNumber} 页`);
      }
    }
  }

  async getToastMessage(timeout: number = 5000): Promise<string | null> {
    // 优先使用 waitForSelector 等待消息出现，比轮询更快
    const selectors = ['.el-message', '.el-notification__content', '.el-message-box__message', '.el-form-item__error'];
    const messageSelector = selectors.join(', ');
    
    // 先尝试快速等待
    try {
      await this.page.waitForSelector(messageSelector, { state: 'visible', timeout: 3000 });
    } catch {
      // 如果没有出现，立即检查当前是否有可见的消息
    }
    
    // 检查当前可见的消息
    for (const selector of selectors) {
      const element = this.page.locator(selector).first();
      if ((await element.count()) > 0) {
        try {
          if (await element.isVisible()) {
            const text = await element.textContent();
            if (text && text.trim()) {
              console.log(`📊 消息 [${selector}]: ${text.trim()}`);
              return text.trim();
            }
          }
        } catch {
          continue;
        }
      }
    }
    
    // 如果还没找到，用轮询方式再等一会
    const pollInterval = 100;
    const maxAttempts = Math.floor((timeout - 3000) / pollInterval);
    
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      for (const selector of selectors) {
        const element = this.page.locator(selector).first();
        if ((await element.count()) > 0) {
          try {
            if (await element.isVisible()) {
              const text = await element.textContent();
              if (text && text.trim()) {
                console.log(`📊 消息 [${selector}]: ${text.trim()}`);
                return text.trim();
              }
            }
          } catch {
            continue;
          }
        }
      }
      
      await this.page.waitForTimeout(pollInterval);
    }
    
    console.log('⚠️ 等待消息超时，未检测到toast或表单错误');
    return null;
  }

  protected async waitForPageLoad(): Promise<void> {
    // 等待DOM内容加载
    try {
      await this.page.waitForLoadState('domcontentloaded', { timeout: 15000 });
    } catch {
      console.log('⚠️ domcontentloaded 超时，继续等待');
    }
    
    // 等待主要内容区域加载
    const contentSelectors = [
      '.el-table',
      '.el-table__body',
      '.amis-table',
      '.el-form',
      '.el-main',
      'main'
    ];
    
    let contentLoaded = false;
    for (const selector of contentSelectors) {
      try {
        await this.page.waitForSelector(selector, { state: 'attached', timeout: 5000 });
        contentLoaded = true;
        console.log(`✅ 内容区域已加载: ${selector}`);
        break;
      } catch {
        continue;
      }
    }
    
    if (!contentLoaded) {
      console.log('⚠️ 未检测到主要内容区域，等待2秒后继续');
    }
    
    // 额外等待时间，确保动态内容渲染完成
    await this.page.waitForTimeout(2000);
  }

  /**
   * 等待指定元素出现在页面上，带重试机制
   */
  protected async waitForElement(selector: string, timeout: number = 10000): Promise<boolean> {
    try {
      await this.page.waitForSelector(selector, { state: 'visible', timeout });
      return true;
    } catch {
      console.log(`⚠️ 等待元素超时: ${selector}`);
      return false;
    }
  }

  protected async waitForVisible(locator: Locator, timeout: number = 10000): Promise<void> {
    await locator.waitFor({ state: 'visible', timeout });
  }
}

export class DialogBase extends BasePage {
  protected dialog: Locator;

  constructor(page: Page, dialog: Locator) {
    super(page);
    this.dialog = dialog;
  }

  protected async ensureDialogScope(): Promise<void> {
    if ((await this.dialog.locator('.el-form-item').count()) === 0) {
      const visibleDialog = this.page.locator('.el-dialog:visible, .el-drawer:visible').first();
      if ((await visibleDialog.count()) > 0) {
        console.log('⚠️ 修正弹窗定位器');
        this.dialog = visibleDialog;
      }
    }
  }

  async fillByPlaceholder(placeholder: string, value: string): Promise<void> {
    await this.ensureDialogScope();
    const strategies = [
      { name: 'exact placeholder', action: async () => {
        const input = this.dialog.locator(`input[placeholder="${placeholder}"]`).first();
        if ((await input.count()) > 0 && await input.isVisible()) {
          await input.waitFor({ state: 'visible', timeout: 10000 });
          await input.fill(value);
          console.log(`✅ 填写 [${placeholder}]: ${value}`);
          return true;
        }
        return false;
      }},
      { name: 'contains placeholder', action: async () => {
        const input = this.dialog.locator(`input[placeholder*="${placeholder}"]`).first();
        if ((await input.count()) > 0 && await input.isVisible()) {
          await input.waitFor({ state: 'visible', timeout: 10000 });
          await input.fill(value);
          console.log(`✅ 通过包含占位符填写 [${placeholder}]: ${value}`);
          return true;
        }
        return false;
      }},
      { name: 'textbox role', action: async () => {
        const input = this.dialog.locator(`[role="textbox"][placeholder*="${placeholder}"]`).first();
        if ((await input.count()) > 0 && await input.isVisible()) {
          await input.waitFor({ state: 'visible', timeout: 10000 });
          await input.fill(value);
          console.log(`✅ 通过textbox角色填写 [${placeholder}]: ${value}`);
          return true;
        }
        return false;
      }}
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

    console.log(`❌ 未找到占位符为 [${placeholder}] 的输入框（仅在弹窗内查找）`);
  }

  async fillByLabel(labelText: string, value: string): Promise<void> {
    await this.ensureDialogScope();
    const strategies = [
      { name: 'el-form-item', action: async () => {
        const formItem = this.dialog.locator('.el-form-item').filter({ hasText: labelText }).first();
        if ((await formItem.count()) > 0) {
          const input = formItem.locator('.el-input__inner, input:not(.el-select__input), textarea').first();
          if ((await input.count()) > 0) {
            await input.waitFor({ state: 'visible', timeout: 10000 });
            await input.fill(value);
            console.log(`✅ 填写 [${labelText}]: ${value}`);
            return true;
          }
        }
        return false;
      }},
      { name: 'placeholder', action: async () => {
        const placeholderInput = this.dialog.locator(`input[placeholder*="${labelText}"]`).first();
        if ((await placeholderInput.count()) > 0) {
          await placeholderInput.waitFor({ state: 'visible', timeout: 10000 });
          await placeholderInput.fill(value);
          console.log(`✅ 通过占位符填写 [${labelText}]: ${value}`);
          return true;
        }
        return false;
      }},
      { name: 'aria-label', action: async () => {
        const ariaInput = this.dialog.locator(`input[aria-label*="${labelText}"], textarea[aria-label*="${labelText}"]`).first();
        if ((await ariaInput.count()) > 0) {
          await ariaInput.waitFor({ state: 'visible', timeout: 10000 });
          await ariaInput.fill(value);
          console.log(`✅ 通过aria-label填写 [${labelText}]: ${value}`);
          return true;
        }
        return false;
      }},
      { name: 'label for', action: async () => {
        const label = this.dialog.locator('label').filter({ hasText: labelText }).first();
        if ((await label.count()) > 0) {
          const forAttr = await label.getAttribute('for');
          if (forAttr) {
            const input = this.dialog.locator(`#${forAttr}`).first();
            if ((await input.count()) > 0) {
              await input.waitFor({ state: 'visible', timeout: 10000 });
              await input.fill(value);
              console.log(`✅ 通过label for填写 [${labelText}]: ${value}`);
              return true;
            }
          }
        }
        return false;
      }},
      { name: 'span label', action: async () => {
        const labelSpan = this.dialog.locator('span').filter({ hasText: labelText }).first();
        if ((await labelSpan.count()) > 0) {
          const parentForm = labelSpan.locator('..').locator('.el-form-item').first();
          if ((await parentForm.count()) > 0) {
            const input = parentForm.locator('.el-input__inner, input:not(.el-select__input), textarea').first();
            if ((await input.count()) > 0) {
              await input.waitFor({ state: 'visible', timeout: 10000 });
              await input.fill(value);
              console.log(`✅ 通过span标签填写 [${labelText}]: ${value}`);
              return true;
            }
          }
        }
        return false;
      }}
    ];

    for (const strategy of strategies) {
      const success = await strategy.action();
      if (success) return;
    }

    console.log(`⚠️ 未找到输入框 [${labelText}]`);
  }

  async selectByLabel(labelText: string, optionText: string): Promise<void> {
    await this.ensureDialogScope();
    await this.selectElOptionByLabel(labelText, optionText, this.dialog);
  }

  protected async waitForSubmitResult(): Promise<void> {
    // Wait for toast, form error, or dialog close (whichever comes first)
    const messageSelector = '.el-message, .el-notification__content, .el-message-box__message, .el-form-item__error';
    
    // 快速检测：等待消息或弹窗关闭，最多等3秒
    try {
      await Promise.race([
        this.page.waitForSelector(messageSelector, { state: 'visible', timeout: 3000 }),
        this.dialog.waitFor({ state: 'hidden', timeout: 3000 }),
      ]);
    } catch {
      // 如果都没出现，继续短时间等待
      await this.page.waitForTimeout(1000);
    }
    
    // 短暂缓冲区确保消息完全渲染
    await this.page.waitForTimeout(300);
  }

  async submit(): Promise<void> {
    const submitPatterns = [/确定/, /提交/, /确\s*定/, /提\s*交/, /保存/];

    for (const pattern of submitPatterns) {
      const button = this.dialog.locator('button').filter({ hasText: pattern }).first();
      if ((await button.count()) > 0 && await button.isVisible()) {
        await button.click({ force: true });
        console.log(`✅ 点击确定/提交按钮`);
        await this.waitForSubmitResult();
        return;
      }
    }

    const dialogPrimaryButton = this.dialog.locator('.el-button--primary').first();
    if ((await dialogPrimaryButton.count()) > 0 && await dialogPrimaryButton.isVisible()) {
      const text = await dialogPrimaryButton.textContent();
      if (text && (text.includes('确定') || text.includes('提交') || text.includes('保存'))) {
        await dialogPrimaryButton.click({ force: true });
        console.log(`✅ 通过弹窗内样式类定位点击主按钮: ${text}`);
        await this.waitForSubmitResult();
        return;
      }
    }

    const allDialogButtons = this.dialog.locator('button');
    const buttonCount = await allDialogButtons.count();
    for (let i = 0; i < buttonCount; i++) {
      const button = allDialogButtons.nth(i);
      const text = await button.textContent();
      if (text && (text.includes('确定') || text.includes('提交') || text.includes('保存'))) {
        await button.click({ force: true });
        console.log(`✅ 通过遍历弹窗按钮点击: ${text}`);
        await this.waitForSubmitResult();
        return;
      }
    }

    const submitTexts = ['确定', '提交', '保存', '新增'];
    
    const defaultButtons = this.page.locator('button.el-button--default');
    const defaultCount = await defaultButtons.count();
    
    for (let i = 0; i < defaultCount; i++) {
      const button = defaultButtons.nth(i);
      const text = await button.textContent();
      
      if (text && submitTexts.some(submit => text.includes(submit)) && 
          !text.includes('搜索') && !text.includes('查询') && !text.includes('跟进')) {
        await button.click({ force: true });
        console.log(`✅ 通过默认尺寸按钮定位点击: ${text}`);
        await this.waitForSubmitResult();
        return;
      }
    }
    
    const allButtons = this.page.locator('button');
    const allCount = await allButtons.count();
    
    for (let i = 0; i < allCount; i++) {
      const button = allButtons.nth(i);
      const text = await button.textContent();
      
      if (text && submitTexts.some(submit => text.includes(submit)) && 
          !text.includes('搜索') && !text.includes('查询') && !text.includes('跟进')) {
        await button.click({ force: true });
        console.log(`✅ 通过页面按钮定位点击: ${text}`);
        await this.waitForSubmitResult();
        return;
      }
    }

    console.log('⚠️ 未找到确定/提交按钮');
  }

  async close(): Promise<void> {
    const closePatterns = [/取消/, /关闭/, /取\s*消/, /关\s*闭/];

    for (const pattern of closePatterns) {
      const button = this.dialog.locator('button').filter({ hasText: pattern }).first();
      if ((await button.count()) > 0 && await button.isVisible()) {
        await button.click();
        console.log(`✅ 关闭弹窗`);
        return;
      }
    }

    const closeIcon = this.dialog.locator('.el-dialog__close, .el-drawer__close').first();
    if ((await closeIcon.count()) > 0 && await closeIcon.isVisible()) {
      await closeIcon.click();
      console.log(`✅ 点击关闭图标`);
      return;
    }

    console.log('⚠️ 未找到关闭按钮');
  }
}