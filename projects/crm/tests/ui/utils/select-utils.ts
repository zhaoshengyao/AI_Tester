import { Page, Locator } from '@playwright/test';

/**
 * Element UI 下拉框选择工具
 * 用于处理 Element UI 的 el-select 组件
 */
export class SelectUtils {
  private page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * 通过标签查找并选择下拉框选项
   * @param parentElement - 父元素（通常是 dialog 或 form）
   * @param labelText - 标签文本（如"角色"）
   * @param validOptions - 有效的选项列表（用于过滤无效选项）
   * @returns 是否选择成功
   */
  async selectByLabel(
    parentElement: Locator,
    labelText: string,
    validOptions: string[]
  ): Promise<boolean> {
    console.log(`🔍 查找${labelText}选择框...`);

    // 查找所有表单项
    const formItems = parentElement.locator('.el-form-item');
    const formItemCount = await formItems.count();
    console.log(`找到 ${formItemCount} 个表单项`);

    for (let i = 0; i < formItemCount; i++) {
      const formItem = formItems.nth(i);

      // 查找标签文本
      const label = formItem.locator('.el-form-item__label');
      const currentLabelText = await label.textContent() || '';

      if (currentLabelText.includes(labelText)) {
        console.log(`✅ 找到${labelText}表单项（第 ${i + 1} 个）`);

        // 在这个表单项中查找选择框
        const selectBox = formItem.locator('.el-select');
        if (await selectBox.count() > 0) {
          await selectBox.click();
          console.log(`✅ 点击${labelText}选择框`);

          // 等待下拉框出现
          await this.page.waitForTimeout(300);

          // 查找并选择选项
          const success = await this.selectOption(validOptions);
          if (success) {
            console.log(`✅ 已选择${labelText}`);
            return true;
          }
        }
        break;
      }
    }

    console.log(`⚠️ 未找到${labelText}选择框`);
    return false;
  }

  /**
   * 选择下拉框选项
   * @param validOptions - 有效的选项列表
   * @returns 是否选择成功
   */
  async selectOption(validOptions: string[]): Promise<boolean> {
    const options = this.page.locator('.el-select-dropdown__item');
    const optionCount = await options.count();
    console.log(`找到 ${optionCount} 个选项`);

    if (optionCount === 0) {
      console.log('⚠️ 下拉框中没有选项');
      return false;
    }

    // 获取所有选项的文本
    const optionTexts = await Promise.all(
      Array.from({ length: optionCount }, (_, i) => options.nth(i).textContent())
    );
    console.log(`选项列表: ${optionTexts.join(', ')}`);

    // 找到第一个有效的选项
    let selectedIndex = -1;
    for (let i = 0; i < optionTexts.length; i++) {
      if (optionTexts[i] && validOptions.includes(optionTexts[i]!.trim())) {
        selectedIndex = i;
        break;
      }
    }

    if (selectedIndex >= 0) {
      const selectedText = optionTexts[selectedIndex];
      console.log(`选择第 ${selectedIndex + 1} 个选项: ${selectedText}`);

      // 使用 JavaScript 触发完整的选择流程并关闭下拉框
      await this.page.evaluate((index: number) => {
        const items = document.querySelectorAll('.el-select-dropdown__item');
        if (items.length > index) {
          const item = items[index] as HTMLElement;

          // 触发鼠标事件（Element UI 需要这些事件）
          const mouseDown = new MouseEvent('mousedown', { bubbles: true });
          const mouseUp = new MouseEvent('mouseup', { bubbles: true });
          const click = new MouseEvent('click', { bubbles: true });

          item.dispatchEvent(mouseDown);
          item.dispatchEvent(mouseUp);
          item.dispatchEvent(click);

          // 关闭所有相关的下拉框容器
          const dropdowns = document.querySelectorAll('.el-select-dropdown, .el-popper-container');
          dropdowns.forEach((dropdown) => {
            (dropdown as HTMLElement).style.display = 'none';
          });
        }
      }, selectedIndex);

      return true;
    } else {
      console.log('⚠️ 未找到有效的选项');
      return false;
    }
  }

  /**
   * 直接通过选择框定位器选择选项
   * @param selectLocator - 选择框定位器
   * @param validOptions - 有效的选项列表
   * @returns 是否选择成功
   */
  async selectFromLocator(selectLocator: Locator, validOptions: string[]): Promise<boolean> {
    await selectLocator.click();
    console.log('✅ 点击选择框');

    // 等待下拉框出现
    await this.page.waitForTimeout(300);

    return this.selectOption(validOptions);
  }
}

/**
 * 预设的选项列表
 */
export const PresetOptions = {
  // 用户角色
  UserRoles: ['erp', '测试超管', 'crm', '企微', 'erp用户'],
  // 用户状态
  UserStatus: ['正常', '停用'],
  // 性别
  Gender: ['男', '女', '未知'],
};
