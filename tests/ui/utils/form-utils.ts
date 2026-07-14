import { Page, Locator } from '@playwright/test';
import { SelectUtils, PresetOptions } from './select-utils';

/**
 * Element UI 表单填写工具
 * 用于处理弹窗中的表单填写操作
 */
export class FormUtils {
  private page: Page;
  private selectUtils: SelectUtils;

  constructor(page: Page) {
    this.page = page;
    this.selectUtils = new SelectUtils(page);
  }

  /**
   * 打开新增弹窗
   * @param dialogTitle - 弹窗标题（如"新增用户"）
   * @param buttonText - 按钮文本（如"新增"）
   * @returns 弹窗定位器
   */
  async openAddDialog(dialogTitle: string, buttonText: string = '新增'): Promise<Locator> {
    console.log(`🔍 查找${buttonText}按钮...`);
    
    // 查找新增按钮
    const addButton = this.page.locator('button').filter({ hasText: new RegExp(buttonText) }).first();
    await addButton.waitFor({ state: 'visible', timeout: 10000 });
    await addButton.click();
    console.log(`✅ 点击${buttonText}按钮`);
    
    // 等待弹窗出现
    const dialog = this.page.locator('.el-dialog').filter({ hasText: new RegExp(dialogTitle) }).first();
    await dialog.waitFor({ state: 'visible', timeout: 15000 });
    console.log(`✅ ${dialogTitle}弹窗已打开`);
    
    return dialog;
  }

  /**
   * 填写文本输入框
   * @param dialog - 弹窗定位器
   * @param placeholder - 输入框占位符文本
   * @param value - 要填写的值
   */
  async fillInput(dialog: Locator, placeholder: string, value: string): Promise<void> {
    const input = dialog.locator(`input[placeholder="${placeholder}"]`);
    await input.waitFor({ state: 'visible', timeout: 5000 });
    await input.fill(value);
    console.log(`✅ 已填写${placeholder}: ${value}`);
  }

  /**
   * 通过标签查找并填写输入框
   * @param dialog - 弹窗定位器
   * @param labelText - 标签文本
   * @param value - 要填写的值
   */
  async fillInputByLabel(dialog: Locator, labelText: string, value: string): Promise<void> {
    const formItems = dialog.locator('.el-form-item');
    const count = await formItems.count();
    
    for (let i = 0; i < count; i++) {
      const formItem = formItems.nth(i);
      const label = formItem.locator('.el-form-item__label');
      const labelContent = await label.textContent() || '';
      
      if (labelContent.includes(labelText)) {
        const input = formItem.locator('input').first();
        await input.fill(value);
        console.log(`✅ 已填写${labelText}: ${value}`);
        return;
      }
    }
    console.log(`⚠️ 未找到${labelText}对应的输入框`);
  }

  /**
   * 选择下拉框选项
   * @param dialog - 弹窗定位器
   * @param labelText - 标签文本（如"角色"、"状态"）
   * @param validOptions - 有效的选项列表
   * @returns 是否选择成功
   */
  async selectByLabel(dialog: Locator, labelText: string, validOptions: string[]): Promise<boolean> {
    return this.selectUtils.selectByLabel(dialog, labelText, validOptions);
  }

  /**
   * 提交表单
   * @param dialog - 弹窗定位器
   * @param buttonText - 按钮文本（默认"确定"）
   */
  async submitForm(dialog: Locator, buttonText: string = '确定'): Promise<void> {
    const confirmButton = dialog.locator('button').filter({ hasText: new RegExp(buttonText) }).first();
    await confirmButton.click();
    console.log(`✅ 已点击${buttonText}按钮`);
    
    // 等待处理
    await this.page.waitForTimeout(2000);
    
    // 检查是否有错误提示
    const errorMessage = this.page.locator('.el-message--error, .el-form-item__error').first();
    if (await errorMessage.count() > 0 && await errorMessage.isVisible()) {
      const errorText = await errorMessage.textContent();
      console.log(`⚠️ 提交失败，错误信息: ${errorText}`);
    } else {
      console.log(`✅ 表单提交成功`);
    }
  }

  /**
   * 关闭弹窗
   * @param dialog - 弹窗定位器
   */
  async closeDialog(dialog: Locator): Promise<void> {
    const closeBtn = dialog.locator('.el-dialog__close, button:has-text("取消"), button:has-text("关闭")').first();
    if (await closeBtn.count() > 0 && await closeBtn.isVisible()) {
      await closeBtn.click();
      console.log('✅ 已关闭弹窗');
    }
  }

  /**
   * 完整的创建流程（适用于用户、客户等）
   * @param options - 创建选项
   */
  async completeCreateFlow(options: {
    pageTitle: string;
    dialogTitle: string;
    buttonText?: string;
    fields: {
      placeholder?: string;
      label?: string;
      value: string;
    }[];
    selects?: {
      label: string;
      options: string[];
    }[];
  }): Promise<void> {
    const { pageTitle, dialogTitle, buttonText = '新增', fields, selects = [] } = options;
    
    // 导航到目标页面
    console.log(`🔄 导航到${pageTitle}...`);
    await this.page.goto(pageTitle);
    await this.page.waitForLoadState('domcontentloaded');
    await this.page.waitForTimeout(2000);
    
    // 打开弹窗
    const dialog = await this.openAddDialog(dialogTitle, buttonText);
    
    // 填写文本字段
    for (const field of fields) {
      if (field.placeholder) {
        await this.fillInput(dialog, field.placeholder, field.value);
      } else if (field.label) {
        await this.fillInputByLabel(dialog, field.label, field.value);
      }
    }
    
    // 选择下拉框
    for (const select of selects) {
      await this.selectByLabel(dialog, select.label, select.options);
    }
    
    // 提交表单
    await this.submitForm(dialog);
  }
}

/**
 * 用户管理相关操作
 */
export class UserFormUtils extends FormUtils {
  /**
   * 创建用户 - 填写完整信息
   */
  async createUser(dialog: Locator): Promise<void> {
    const timestamp = Date.now();
    
    // 用户名称
    await this.fillInput(dialog, '请输入用户名称', `测试用户_${timestamp}`);
    
    // 手机号码
    await this.fillInput(dialog, '请输入手机号码', `138${String(timestamp).slice(-8)}`);
    
    // 用户账号
    await this.fillInput(dialog, '请输入用户账号', `test_${timestamp % 10000000000}`);
    
    // 用户密码
    await this.fillInput(dialog, '请输入用户密码', 'Test@123456');
    
    // 选择角色
    await this.selectByLabel(dialog, '角色', PresetOptions.UserRoles);
  }
}
