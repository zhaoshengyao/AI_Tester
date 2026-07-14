import { Page, expect } from '@playwright/test';
import { encryptPassword } from '../utils/crypto';

export class LoginPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/');
    await this.page.waitForLoadState('domcontentloaded');
  }

  async login(username: string, password: string) {
    const usernameInput = this.page.locator('input[type="text"]').filter({ not: { hasClass: 'el-select__input' } }).first();
    const passwordInput = this.page.locator('input[type="password"]').first();
    const loginButton = this.page.getByRole('button', { name: /登\s*录/ }).first();
    
    await usernameInput.fill(username);
    await passwordInput.fill(password);
    await loginButton.click();
  }

  async loginWithEncryptedPassword(username: string, plainPassword: string, clientId: string) {
    const encryptedPassword = encryptPassword(plainPassword);
    
    await this.page.route('**/auth/login', async (route) => {
      const request = route.request();
      const postData = JSON.parse(request.postData() || '{}');
      
      postData.username = username;
      postData.password = encryptedPassword;
      postData.clientId = clientId;
      postData.grant_type = 'password';
      postData.grantType = 'password';
      
      await route.continue({
        postData: JSON.stringify(postData)
      });
    });

    const usernameInput = this.page.locator('input[type="text"]').filter({ not: { hasClass: 'el-select__input' } }).first();
    const passwordInput = this.page.locator('input[type="password"]').first();
    const loginButton = this.page.getByRole('button', { name: /登\s*录/ }).first();
    
    await usernameInput.fill(username);
    await passwordInput.fill('dummy');
    await loginButton.click();
  }

  async assertLoginSuccess() {
    await this.page.waitForTimeout(3000);
    await this.page.waitForLoadState('domcontentloaded', { timeout: 15000 }).catch(() => {});
    
    const currentUrl = this.page.url();
    console.log(`当前 URL: ${currentUrl}`);
    
    const isStillOnLogin = currentUrl.includes('/login');
    
    if (isStillOnLogin) {
      const errorMsg = this.page.locator('.el-message-error, .el-message--error, [role="alert"], .am-alert');
      const errorCount = await errorMsg.count();
      if (errorCount > 0) {
        const errorText = await errorMsg.first().textContent();
        throw new Error(`登录失败: ${errorText}`);
      }
      throw new Error(`登录失败: 页面仍停留在登录页 (${currentUrl})`);
    }
    
    expect(isStillOnLogin).toBe(false);
    console.log('✅ 登录成功，已跳转到首页');
  }
}