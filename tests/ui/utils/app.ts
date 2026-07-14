import { Page, expect, Locator, BrowserContext } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import accounts from '../fixtures/accounts';

const CLIENT_ID = process.env.API_CLIENT_ID || 'e5cd7e4891bf95d1d19206ce24a7b32e';

/**
 * 创建带登录的浏览器上下文
 */
export async function createLoggedInContext(browser: any): Promise<{ context: BrowserContext; page: Page }> {
  const context = await browser.newContext({
    acceptDownloads: true,
    viewport: { width: 1920, height: 1080 },
  });
  const page = await context.newPage();
  
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.loginWithEncryptedPassword(accounts.ui.username, accounts.ui.password, CLIENT_ID);
  await loginPage.assertLoginSuccess();
  
  console.log('✅ 登录成功，当前URL:', page.url());
  
  return { context, page };
}

/**
 * 导航到指定页面并等待加载完成
 */
export async function navigateToPage(page: Page, url: string): Promise<void> {
  console.log(`🔄 导航到 ${url}...`);
  await page.goto(url);
  await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
  await page.waitForTimeout(2000);
  console.log(`✅ 页面加载完成: ${page.url()}`);
}

/**
 * 查找并点击按钮
 */
export async function clickButtonByText(page: Page, textPattern: RegExp | string): Promise<void> {
  const button = page.locator('button').filter({ hasText: textPattern }).first();
  await button.waitFor({ state: 'visible', timeout: 10000 });
  await button.click();
  console.log(`✅ 点击按钮: ${textPattern}`);
}

/**
 * 等待并获取弹窗
 */
export async function waitForDialog(page: Page, titlePattern?: RegExp | string): Promise<Locator> {
  let dialog: Locator;
  if (titlePattern) {
    dialog = page.locator('.el-dialog').filter({ hasText: titlePattern }).first();
  } else {
    dialog = page.locator('.el-dialog').first();
  }
  await dialog.waitFor({ state: 'visible', timeout: 15000 });
  console.log(`✅ 弹窗已打开`);
  return dialog;
}

/**
 * 打开新增弹窗的完整流程
 */
export async function openAddDialog(page: Page, dialogTitle: string): Promise<Locator> {
  await clickButtonByText(page, /新增|添加/);
  return waitForDialog(page, new RegExp(dialogTitle));
}

/**
 * 填写表单字段
 */
export async function fillFormField(dialog: Locator, placeholder: string, value: string): Promise<void> {
  const input = dialog.locator(`input[placeholder="${placeholder}"]`);
  await input.waitFor({ state: 'visible', timeout: 5000 });
  await input.fill(value);
  console.log(`✅ 已填写: ${placeholder} = ${value}`);
}

/**
 * 通过标签填写表单字段
 */
export async function fillFormFieldByLabel(dialog: Locator, labelText: string, value: string): Promise<void> {
  const formItems = dialog.locator('.el-form-item');
  const count = await formItems.count();
  
  for (let i = 0; i < count; i++) {
    const formItem = formItems.nth(i);
    const label = formItem.locator('.el-form-item__label');
    const labelContent = await label.textContent() || '';
    
    if (labelContent.includes(labelText)) {
      const input = formItem.locator('input').first();
      await input.fill(value);
      console.log(`✅ 已填写: ${labelText} = ${value}`);
      return;
    }
  }
  console.log(`⚠️ 未找到标签: ${labelText}`);
}

/**
 * 通过 JavaScript 选择下拉框选项
 */
export async function selectDropdownOption(page: Page, validOptions: string[]): Promise<boolean> {
  const options = page.locator('.el-select-dropdown__item');
  const optionCount = await options.count();
  
  if (optionCount === 0) {
    console.log('⚠️ 下拉框中没有选项');
    return false;
  }
  
  const optionTexts = await Promise.all(
    Array.from({ length: optionCount }, (_, i) => options.nth(i).textContent())
  );
  
  let selectedIndex = -1;
  for (let i = 0; i < optionTexts.length; i++) {
    if (optionTexts[i] && validOptions.includes(optionTexts[i]!.trim())) {
      selectedIndex = i;
      break;
    }
  }
  
  if (selectedIndex >= 0) {
    const selectedText = optionTexts[selectedIndex];
    console.log(`选择: ${selectedText}`);
    
    await page.evaluate((index) => {
      const items = document.querySelectorAll('.el-select-dropdown__item');
      if (items.length > index) {
        const item = items[index] as HTMLElement;
        item.click();
        // 关闭下拉框
        const dropdowns = document.querySelectorAll('.el-select-dropdown, .el-popper-container');
        dropdowns.forEach(d => (d as HTMLElement).style.display = 'none');
      }
    }, selectedIndex);
    
    return true;
  }
  
  return false;
}

/**
 * 选择下拉框（通过标签）
 */
export async function selectDropdownByLabel(dialog: Locator, page: Page, labelText: string, validOptions: string[]): Promise<boolean> {
  const formItems = dialog.locator('.el-form-item');
  const count = await formItems.count();
  
  for (let i = 0; i < count; i++) {
    const formItem = formItems.nth(i);
    const label = formItem.locator('.el-form-item__label');
    const labelContent = await label.textContent() || '';
    
    if (labelContent.includes(labelText)) {
      const selectBox = formItem.locator('.el-select');
      if (await selectBox.count() > 0) {
        await selectBox.click();
        await page.waitForTimeout(300);
        const success = await selectDropdownOption(page, validOptions);
        if (success) {
          console.log(`✅ 已选择: ${labelText}`);
        }
        return success;
      }
    }
  }
  return false;
}

/**
 * 点击确定按钮提交表单
 */
export async function submitDialog(dialog: Locator, page: Page): Promise<void> {
  const confirmButton = dialog.locator('button').filter({ hasText: /确\s*定/ }).first();
  await confirmButton.click();
  console.log(`✅ 点击确定按钮`);
  
  await page.waitForTimeout(2000);
  
  // 检查错误
  const errorMessage = page.locator('.el-message--error, .el-form-item__error').first();
  if (await errorMessage.count() > 0 && await errorMessage.isVisible()) {
    const errorText = await errorMessage.textContent();
    console.log(`⚠️ 提交失败: ${errorText}`);
  } else {
    console.log(`✅ 表单提交成功`);
  }
}

/**
 * 关闭弹窗
 */
export async function closeDialog(dialog: Locator): Promise<void> {
  const closeBtn = dialog.locator('.el-dialog__close, button:has-text("取消")').first();
  if (await closeBtn.count() > 0 && await closeBtn.isVisible()) {
    await closeBtn.click();
    console.log(`✅ 已关闭弹窗`);
  }
}

// ==================== 原有函数保持兼容 ====================

export async function loginAsAdmin(page: Page, maxRetries: number = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const loginPage = new LoginPage(page);
      await loginPage.goto();
      await loginPage.loginWithEncryptedPassword(accounts.ui.username, accounts.ui.password, CLIENT_ID);
      await loginPage.assertLoginSuccess();
      return;
    } catch (error) {
      console.log(`登录尝试 ${attempt}/${maxRetries} 失败: ${(error as Error).message}`);
      if (attempt === maxRetries) {
        throw error;
      }
      await page.waitForTimeout(2000);
    }
  }
}

export async function refreshPage(page: Page, maxRetries: number = 2): Promise<boolean> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      await page.reload();
      await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
      return true;
    } catch (error) {
      console.log(`页面刷新失败 (尝试 ${attempt + 1}/${maxRetries}):`, error);
      if (attempt < maxRetries - 1) {
        await page.waitForTimeout(2000);
      }
    }
  }
  return false;
}

export async function navigateToHomeAndRefresh(page: Page): Promise<void> {
  try {
    await page.goto('/', { timeout: 30000 });
    await page.waitForLoadState('domcontentloaded');
  } catch (error) {
    console.log('导航到首页失败，尝试刷新:', error);
    await refreshPage(page);
  }
}

export async function gotoMenuSafe(page: Page, menuPath: string[], maxRetries: number = 2): Promise<boolean> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      for (let i = 0; i < menuPath.length; i++) {
        const menuName = menuPath[i];
        
        let subMenuLocator = page.locator(`.el-sub-menu:has-text("${menuName}")`).first();
        let menuItemLocator = page.locator(`.menu-title:has-text("${menuName}")`).first();
        let elMenuItemLocator = page.locator(`.el-menu-item:has-text("${menuName}")`).first();
        
        const subMenuCount = await subMenuLocator.count();
        const menuItemCount = await menuItemLocator.count();
        const elMenuItemCount = await elMenuItemLocator.count();
        
        let targetLocator: Locator;
        
        if (subMenuCount > 0) {
          targetLocator = subMenuLocator;
        } else if (menuItemCount === 1) {
          targetLocator = menuItemLocator;
        } else if (menuItemCount > 1 && i > 0) {
          const parentMenu = menuPath[i - 1];
          targetLocator = page.locator(`.el-sub-menu:has-text("${parentMenu}")`).locator(`.menu-title:has-text("${menuName}")`).first();
        } else if (elMenuItemCount > 0) {
          targetLocator = elMenuItemLocator;
        } else {
          throw new Error(`无法找到菜单: ${menuName}`);
        }
        
        await targetLocator.click({ timeout: 10000 });
        await page.waitForTimeout(1000);
      }
      
      await page.waitForLoadState('networkidle', { timeout: 15000 });
      return true;
    } catch (error) {
      console.log(`菜单导航失败 (尝试 ${attempt + 1}/${maxRetries}):`, error);
      if (attempt < maxRetries - 1) {
        await navigateToHomeAndRefresh(page);
        await page.waitForTimeout(2000);
      }
    }
  }
  return false;
}

export async function gotoMenu(page: Page, name: string) {
  const menuLink = page.locator(`.menu-title:has-text("${name}"), .el-menu-item:has-text("${name}")`).first();
  await menuLink.click();
  await page.waitForTimeout(1500);
}

export async function assertTexts(page: Page, texts: Array<string | RegExp>) {
  for (const text of texts) {
    await expect(page.getByText(text).first()).toBeVisible({ timeout: 10000 });
  }
}

export async function clickFirstText(page: Page, text: string | RegExp) {
  await page.getByText(text).first().click();
}

export async function clickButton(page: Page, name: string | RegExp) {
  await page.getByRole('button', { name }).first().click();
}

export async function closeOverlay(page: Page) {
  const closeCandidates = [
    page.getByRole('button', { name: /取消|关闭/ }).first(),
    page.getByText(/取消|关闭|×/).first()
  ];

  for (const locator of closeCandidates) {
    if (await locator.count()) {
      await locator.click({ timeout: 3000 }).catch(() => undefined);
      return;
    }
  }
}

export async function selectOptionIfAvailable(page: Page, selectIndex: number, preferredLabels: string[]) {
  const select = page.locator('select').nth(selectIndex);
  await expect(select).toBeVisible({ timeout: 10000 });
  const labels = (await select.locator('option').allTextContents()).map((label) => label.trim());
  const target = preferredLabels.find((label) => labels.includes(label)) || labels.find((label) => !/全部/.test(label));
  if (target) {
    await select.selectOption({ label: target });
  }
}