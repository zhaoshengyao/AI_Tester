import { Page, Locator } from '@playwright/test';
import { BasePage, DialogBase } from './BasePage';

export class ProductManagementPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async navigate(): Promise<void> {
    await super.navigate('/product/ProductList');
  }

  async clickAddButton(): Promise<ProductAddDialog> {
    console.log('🔍 查找产品管理新增按钮');
    
    // 先清理可能存在的遗留对话框/抽屉
    try {
      const legacyDrawers = this.page.locator('.el-drawer:visible');
      const legacyDialogs = this.page.locator('.el-dialog:visible');
      void legacyDialogs;
      for (let i = 0; i < Math.min(await legacyDrawers.count(), 10); i++) {
        const closeBtn = legacyDrawers.nth(i).locator('.el-drawer__close-btn, .el-dialog__close').first();
        if ((await closeBtn.count()) > 0 && await closeBtn.isVisible()) {
          await closeBtn.click().catch(() => {});
          await this.page.waitForTimeout(300);
        }
      }
      await this.page.keyboard.press('Escape').catch(() => {});
      await this.page.waitForTimeout(500);
    } catch {}
    
    // 等待页面完全加载
    await this.page.waitForTimeout(3000);
    
    // 截图保存当前页面状态
    await this.page.screenshot({ path: `test-results/product-page-${Date.now()}.png`, fullPage: false });
    
    // 深入分析页面结构
    console.log('🔍 深入分析页面结构...');
    
    // 1. 查找所有包含"新增"的文本节点
    const allElements = this.page.locator('*:visible');
    void allElements;
    const bodyText = await this.page.evaluate(() => {
      const elements = document.querySelectorAll('*');
      const results: Array<{tag: string, text: string, class: string, x: number, y: number}> = [];
      for (const el of elements) {
        if (el.children.length === 0 || ['BUTTON', 'A', 'SPAN', 'DIV', 'I', 'STRONG', 'EM'].includes(el.tagName)) {
          const text = el.textContent?.trim() || '';
          if (text.includes('新增') || text.includes('添加')) {
            const rect = el.getBoundingClientRect();
            results.push({
              tag: el.tagName.toLowerCase(),
              text: text.substring(0, 30),
              class: (el.className || '').toString().substring(0, 60),
              x: Math.round(rect.x),
              y: Math.round(rect.y)
            });
          }
        }
      }
      return results;
    });
    console.log(`📊 包含"新增/添加"文本的元素数: ${bodyText.length}`);
    for (const item of bodyText.slice(0, 20)) {
      console.log(`  [${item.tag}] "${item.text}" pos=(${item.x},${item.y}) class="${item.class}"`);
    }
    
    // 2. 查找所有el-button元素
    const elButtons = this.page.locator('.el-button:visible');
    const elButtonCount = await elButtons.count();
    console.log(`📊 .el-button元素数: ${elButtonCount}`);
    for (let i = 0; i < elButtonCount; i++) {
      const btn = elButtons.nth(i);
      const text = await btn.textContent();
      const rect = await btn.evaluate(el => {
        const r = el.getBoundingClientRect();
        return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
      });
      if (text && text.trim()) {
        console.log(`  el-button${i}: "${text.trim()}" pos=(${rect.x},${rect.y}) size=(${rect.w}x${rect.h})`);
      }
    }
    
    // 3. 查找所有<a>标签
    const links = this.page.locator('a:visible');
    const linkCount = await links.count();
    console.log(`📊 <a>标签数: ${linkCount}`);
    for (let i = 0; i < Math.min(linkCount, 30); i++) {
      const link = links.nth(i);
      const text = await link.textContent();
      const href = await link.getAttribute('href');
      if (text && text.trim()) {
        const rect = await link.evaluate(el => {
          const r = el.getBoundingClientRect();
          return { x: Math.round(r.x), y: Math.round(r.y) };
        });
        console.log(`  link${i}: "${text.trim()}" href="${href}" pos=(${rect.x},${rect.y})`);
      }
    }
    
    // 4. 查找所有<button>标签
    const buttons = this.page.locator('button:visible');
    const buttonCount = await buttons.count();
    console.log(`📊 <button>标签数: ${buttonCount}`);
    for (let i = 0; i < buttonCount; i++) {
      const btn = buttons.nth(i);
      const text = await btn.textContent();
      const rect = await btn.evaluate(el => {
        const r = el.getBoundingClientRect();
        return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
      });
      if (text && text.trim()) {
        console.log(`  button${i}: "${text.trim()}" pos=(${rect.x},${rect.y}) size=(${rect.w}x${rect.h})`);
      }
    }
    
    // 策略: 查找页面内容区的"新增产品"或"新增"按钮
    let foundButton: Locator | null = null;
    const buttonSelector = 'button, .el-button';
    
    // 策略1: 使用getByText精确匹配"新增产品"
    console.log('🔍 尝试策略1: getByText匹配"新增产品"');
    const addProductByText = this.page.getByText('新增产品', { exact: true }).first();
    if ((await addProductByText.count()) > 0) {
      const rect = await addProductByText.evaluate(el => el.getBoundingClientRect());
      console.log(`  找到精确匹配"新增产品": y=${Math.round(rect.y)}`);
      foundButton = addProductByText;
    }
    
    // 策略2: 使用包含匹配
    if (!foundButton) {
      console.log('🔍 尝试策略2: getByText包含匹配"新增产品"');
      const addProductByTextInclude = this.page.getByText('新增产品', { exact: false }).first();
      if ((await addProductByTextInclude.count()) > 0) {
        const rect = await addProductByTextInclude.evaluate(el => el.getBoundingClientRect());
        console.log(`  找到包含匹配"新增产品": y=${Math.round(rect.y)}`);
        foundButton = addProductByTextInclude;
      }
    }
    
    // 策略3: 查找所有el-button，过滤出业务区域的按钮
    if (!foundButton) {
      console.log('🔍 尝试策略3: 过滤业务区域按钮');
      const buttons = this.page.locator(buttonSelector);
      const count = await buttons.count();
      
      for (let i = 0; i < count; i++) {
        const button = buttons.nth(i);
        const text = await button.textContent();
        if (text && (text.includes('新增产品') || text.includes('新增'))) {
          const rect = await button.evaluate(el => {
            const r = el.getBoundingClientRect();
            return { x: r.x, y: r.y };
          });
          
          // 检查父元素
          const parentInfo = await button.evaluate(el => {
            const parent = el.parentElement;
            const parentClass = parent ? parent.className : '';
            const grandParent = parent ? parent.parentElement : null;
            const grandParentClass = grandParent ? grandParent.className : '';
            return { parentClass, grandParentClass };
          });
          
          const isInQuickActions = parentInfo.parentClass.includes('quick-actions') || 
                                   parentInfo.grandParentClass.includes('quick-actions');
          
          console.log(`  检查按钮[${text.trim()}]: y=${Math.round(rect.y)}, inQuickActions=${isInQuickActions}`);
          
          // 排除快捷操作栏的按钮
          if (!isInQuickActions) {
            foundButton = button;
            console.log(`✅ 找到[${text.trim()}]按钮 (位置: y=${Math.round(rect.y)})`);
            break;
          }
        }
      }
    }
    
    // 策略4: 回退 - 查找y坐标最大的按钮
    if (!foundButton) {
      console.log('🔍 尝试策略4: 查找y坐标最大的按钮');
      const buttons = this.page.locator(buttonSelector);
      const count = await buttons.count();
      
      let maxY = 0;
      for (let i = 0; i < count; i++) {
        const button = buttons.nth(i);
        const text = await button.textContent();
        if (text && text.includes('新增')) {
          const rect = await button.evaluate(el => el.getBoundingClientRect());
          console.log(`  检查按钮${i}: "${text.trim()}" y=${Math.round(rect.y)}`);
          if (rect.y > maxY) {
            maxY = rect.y;
            foundButton = button;
          }
        }
      }
    }
    
    if (!foundButton) {
      console.log('⚠️ 未找到新增产品按钮，当前页面可能不是产品列表页');
      console.log('📄 当前页面URL:', this.page.url());
      throw new Error('未找到新增产品按钮');
    }
    
    await foundButton.waitFor({ state: 'visible', timeout: 10000 });
    await foundButton.click();
    console.log('✅ 点击新增产品按钮');
    
    // 等待抽屉或弹窗加载
    await this.page.waitForTimeout(3000);
    
    // 查找新的抽屉（选择最后一个，因为它是最新打开的）
    const drawers = this.page.locator('.el-drawer:visible');
    const drawerCount = await drawers.count();
    console.log(`📊 可见抽屉数量: ${drawerCount}`);
    
    // 从最后一个开始检查（最新打开的）
    for (let i = drawerCount - 1; i >= 0; i--) {
      const drawer = drawers.nth(i);
      try {
        const rect = await drawer.evaluate(el => {
          const r = el.getBoundingClientRect();
          const hasBody = el.querySelector('.el-drawer__body') !== null;
          return { width: r.width, height: r.height, hasBody };
        });
        
        if (rect.width > 100 && rect.height > 100 && rect.hasBody) {
          console.log(`✅ 找到有效抽屉 (索引: ${i}, 尺寸: ${Math.round(rect.width)}x${Math.round(rect.height)})`);
          return new ProductAddDialog(this.page, drawer);
        }
      } catch {}
    }
    
    // 查找对话框
    const dialogs = this.page.locator('.el-dialog:visible');
    const dialogCount = await dialogs.count();
    console.log(`📊 可见对话框数量: ${dialogCount}`);
    
    for (let i = dialogCount - 1; i >= 0; i--) {
      const dialog = dialogs.nth(i);
      try {
        const rect = await dialog.evaluate(el => {
          const r = el.getBoundingClientRect();
          const hasBody = el.querySelector('.el-dialog__body') !== null;
          return { width: r.width, height: r.height, hasBody };
        });
        
        if (rect.width > 100 && rect.height > 100 && rect.hasBody) {
          console.log(`✅ 找到有效对话框 (索引: ${i}, 尺寸: ${Math.round(rect.width)}x${Math.round(rect.height)})`);
          return new ProductAddDialog(this.page, dialog);
        }
      } catch {}
    }
    
    // 如果还是没找到，使用 waitForDialog
    console.log('⚠️ 直接查找对话框失败，使用waitForDialog');
    const dialogLocator = await this.waitForDialog();
    return new ProductAddDialog(this.page, dialogLocator);
  }

  async searchProduct(keyword: string): Promise<void> {
    await this.search(keyword);
  }

  async goToPage(pageNumber: number): Promise<void> {
    await super.goToPage(pageNumber);
  }
}

export class ProductAddDialog extends DialogBase {
  constructor(page: Page, dialog: Locator) {
    super(page, dialog);
  }

  async fillProductName(value: string): Promise<void> {
    await this.fillByLabel('产品名称', value);
  }

  async fillProductCode(value: string): Promise<void> {
    await this.fillByLabel('产品编码', value);
  }

  // 产品分类选择 - 使用搜索+回退策略
  async fillCategory(value: string): Promise<void> {
    const labelText = '产品分类';
    const targetContainer = this.dialog;
    
    const labelSelector = targetContainer.locator('.el-form-item__label').filter({ hasText: labelText }).first();
    if ((await labelSelector.count()) === 0) {
      console.log(`⚠️ 未找到标签 [${labelText}]`);
      return;
    }

    const formItem = labelSelector.locator('..').first();
    const selectInForm = formItem.locator('.el-select').first();

    if ((await selectInForm.count()) === 0) {
      console.log(`⚠️ 未找到下拉框 [${labelText}]`);
      return;
    }

    // 使用键盘导航方式选择选项
    // 步骤1: 点击下拉框
    await selectInForm.click();
    console.log(`✅ 点击${labelText}下拉框`);
    await this.page.waitForTimeout(1000);

    // 步骤2: 输入搜索关键词（如果有）
    if (value) {
      const searchInput = this.page.locator('.el-select-dropdown input').first();
      if ((await searchInput.count()) > 0 && await searchInput.isVisible()) {
        await searchInput.fill(value);
        console.log(`✅ 输入搜索: ${value}`);
        await this.page.waitForTimeout(2000);
      }
    }

    // 步骤3: 等待选项出现
    let optionCount = 0;
    let allOptions = this.page.locator('.el-select-dropdown__item');
    
    try {
      await this.page.waitForSelector('.el-select-dropdown__item', { state: 'visible', timeout: 8000 });
      optionCount = await allOptions.count();
      console.log(`📊 ${labelText}选项数: ${optionCount}`);
    } catch {
      console.log('⚠️ 等待选项超时，尝试直接获取');
      optionCount = await allOptions.count();
      console.log(`📊 直接获取选项数: ${optionCount}`);
    }

    if (optionCount === 0) {
      console.log('⚠️ 没有选项，按Escape关闭');
      await this.page.keyboard.press('Escape');
      return;
    }

    // 步骤4: 打印选项
    for (let i = 0; i < Math.min(optionCount, 5); i++) {
      const text = (await allOptions.nth(i).textContent() || '').trim();
      console.log(`  选项${i}: "${text}"`);
    }

    // 步骤5: 使用键盘导航到目标选项
    // 第一个选项默认高亮，所以需要按 targetIndex 次 ArrowDown
    // 如果有搜索值，可能只有匹配的选项
    // 默认选择第一个选项（跳过"全部"如果存在）
    
    // 判断第一个选项是否是"全部"
    const firstOptionText = (await allOptions.nth(0).textContent() || '').trim();
    let targetIndex = 0;
    
    if (firstOptionText === '全部' && optionCount > 1) {
      targetIndex = 1; // 跳过"全部"
      console.log('📊 跳过"全部"选项，选择第一个实际分类');
    }
    
    // 如果有搜索值，查找匹配的选项
    if (value) {
      // 重新获取选项列表进行匹配
      const currentOptions = this.page.locator('.el-select-dropdown__item');
      const currentCount = await currentOptions.count();
      for (let i = 0; i < currentCount; i++) {
        const text = (await currentOptions.nth(i).textContent() || '').trim();
        if (text.includes(value) || value.includes(text)) {
          targetIndex = i;
          break;
        }
      }
    }

    console.log(`📊 目标索引: ${targetIndex}`);

    // 使用ArrowDown导航到目标选项
    for (let i = 0; i < targetIndex; i++) {
      await this.page.keyboard.press('ArrowDown');
      await this.page.waitForTimeout(100);
    }
    
    // 按Enter选择
    await this.page.keyboard.press('Enter');
    await this.page.waitForTimeout(500);
    
    // 验证选择结果
    const selectedText = (await selectInForm.textContent() || '').trim();
    console.log(`✅ 选择${labelText}: ${selectedText || '未显示'}`);
  }

  async fillUnit(value: string): Promise<void> {
    await this.fillByLabel('单位', value);
  }

  async fillSalePrice(value: string): Promise<void> {
    // 销售价(元) - 可能需要特殊处理
    const labelText = '销售价';
    const labelSelector = this.dialog.locator('.el-form-item__label').filter({ hasText: labelText }).first();
    if ((await labelSelector.count()) > 0) {
      const formItem = labelSelector.locator('..').first();
      const input = formItem.locator('input').first();
      if ((await input.count()) > 0) {
        await input.fill(value);
        console.log(`✅ 填写销售价: ${value}`);
      }
    }
  }

  async fillCostPrice(value: string): Promise<void> {
    const labelText = '成本价';
    const labelSelector = this.dialog.locator('.el-form-item__label').filter({ hasText: labelText }).first();
    if ((await labelSelector.count()) > 0) {
      const formItem = labelSelector.locator('..').first();
      const input = formItem.locator('input').first();
      if ((await input.count()) > 0) {
        await input.fill(value);
        console.log(`✅ 填写成本价: ${value}`);
      }
    }
  }

  async fillStatus(value: string): Promise<void> {
    // 状态可能是radio button组
    const statusRadios = this.dialog.locator('.el-radio').filter({ hasText: value });
    if ((await statusRadios.count()) > 0) {
      await statusRadios.first().click();
      console.log(`✅ 选择状态: ${value}`);
      return;
    }
    // 回退：使用selectByLabel
    await this.selectByLabel('状态', value);
  }

  async fillRemark(value: string): Promise<void> {
    await this.fillByLabel('备注', value);
  }

  async fillDescription(value: string): Promise<void> {
    await this.fillByLabel('描述', value);
  }

  async completeCreateProduct(): Promise<void> {
    const timestamp = Date.now();
    
    await this.fillProductName(`测试产品_${timestamp}`);
    await this.fillProductCode(`PRO_${timestamp}`);
    // 分类传空字符串，让回退策略自动选择第一个可用分类
    await this.fillCategory('');
    await this.fillUnit('个');
    await this.fillSalePrice('100');
    await this.fillCostPrice('50');
    await this.fillRemark('自动化测试创建');
    await this.fillStatus('上架');
    
    await this.submit();
  }
}