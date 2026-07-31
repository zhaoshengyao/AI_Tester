import { Page, expect, Locator } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import accounts from '../fixtures/accounts';
import * as fs from 'fs';
import * as path from 'path';

const CLIENT_ID = process.env.API_CLIENT_ID || 'e5cd7e4891bf95d1d19206ce24a7b32e';

export function getAuthToken(): string | null {
  const tokenFile = path.join(__dirname, '../.auth/token.txt');
  if (fs.existsSync(tokenFile)) {
    return fs.readFileSync(tokenFile, 'utf-8').trim();
  }
  return null;
}

export async function createLoggedInContext(browser: any): Promise<{ page: Page }> {
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

  return { page };
}

export async function navigateToPage(page: Page, url: string): Promise<void> {
  console.log(`🔄 导航到 ${url}...`);

  if (!url.startsWith('http') && !url.startsWith('/')) {
    url = '/' + url;
  }

  // 不再强制转换为hash模式，直接使用history模式路由
  await page.goto(url);
  await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
  await page.waitForTimeout(2000);
  console.log(`✅ 页面加载完成: ${page.url()}`);
}

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

export async function gotoMenuSafe(page: Page, menuPath: string[], maxRetries: number = 2): Promise<boolean> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      for (let i = 0; i < menuPath.length; i++) {
        const menuName = menuPath[i];

        const subMenuLocator = page.locator(`.el-sub-menu:has-text("${menuName}")`).first();
        const elMenuItemLocator = page.locator(`.el-menu-item:has-text("${menuName}")`).first();

        const subMenuCount = await subMenuLocator.count();
        const elMenuItemCount = await elMenuItemLocator.count();

        let targetLocator: Locator;

        if (subMenuCount > 0) {
          targetLocator = subMenuLocator;
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
        await page.waitForTimeout(2000);
      }
    }
  }
  return false;
}

export async function assertTexts(page: Page, texts: Array<string | RegExp>) {
  for (const text of texts) {
    await expect(page.getByText(text).first()).toBeVisible({ timeout: 10000 });
  }
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