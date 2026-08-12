import { FullConfig, chromium } from '@playwright/test';
import dotenv from 'dotenv';
import { mkdirSync } from 'fs';

dotenv.config({ path: '../.env' });

const TEST_USERNAME = process.env.TEST_USERNAME || 'ZhaoShengYao';
const TEST_PASSWORD = process.env.TEST_PASSWORD || '123456';
const API_CLIENT_ID = process.env.API_CLIENT_ID || 'e5cd7e4891bf95d1d19206ce24a7b32e';

async function globalSetup(config: FullConfig) {
  const { baseURL } = config.projects[0].use;
  
  mkdirSync('.auth', { recursive: true });
  
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    console.log(`🔍 开始全局登录，目标地址: ${baseURL}/login`);
    console.log(`👤 使用用户名: ${TEST_USERNAME}`);
    await page.goto(`${baseURL}/login`, { waitUntil: 'domcontentloaded' });
    
    await page.waitForTimeout(1500);
    
    const crypto = require('crypto');
    const fs = require('fs');
    const key = Buffer.from(API_CLIENT_ID, 'utf-8');
    const cipher = crypto.createCipheriv('aes-256-ecb', key, null);
    const encrypted = Buffer.concat([cipher.update(TEST_PASSWORD, 'utf-8'), cipher.final()]);
    const encryptedPassword = encrypted.toString('base64');
    
    console.log(`🔐 加密后的密码: ${encryptedPassword}`);

    let capturedToken = '';
    
    await page.route('**/prod-api/auth/login', async (route) => {
      const request = route.request();
      const postData = JSON.parse(request.postData() || '{}');
      
      postData.username = TEST_USERNAME;
      postData.password = encryptedPassword;
      postData.clientId = API_CLIENT_ID;
      postData.grant_type = 'password';
      postData.grantType = 'password';
      
      console.log(`📤 修改登录请求: username=${postData.username}`);
      
      const response = await route.fetch({
        method: request.method(),
        postData: JSON.stringify(postData),
        headers: request.headers()
      });
      
      const responseText = await response.text();
      console.log(`📥 登录响应: ${response.status()} - ${responseText.substring(0, 200)}`);
      
      // 从响应中提取 token
      try {
        const responseJson = JSON.parse(responseText);
        if (responseJson.data && responseJson.data.access_token) {
          capturedToken = responseJson.data.access_token;
          console.log(`🔑 从响应中提取Token: ${capturedToken.substring(0, 20)}...`);
        }
      } catch (e) {
        console.log('⚠️ 响应解析失败');
      }
      
      await route.fulfill({
        response,
        body: responseText
      });
    });

    await page.locator('input[type="text"]:not(.el-select__input)').first().fill(TEST_USERNAME);
    await page.locator('input[type="password"]').first().fill(TEST_PASSWORD);
    await page.getByRole('button', { name: /登\s*录/ }).first().click();
    
    console.log('⏳ 等待页面跳转...');
    
    try {
      await page.waitForURL('**/index**', { timeout: 15000 });
      console.log('✅ 页面跳转到首页成功');
    } catch (e) {
      const currentUrl = page.url();
      console.log(`⚠️ 未跳转到 /index，当前URL: ${currentUrl}`);
      
      if (currentUrl.includes('/login')) {
        console.log('❌ 登录失败，仍在登录页面');
        throw new Error(`登录失败，当前页面: ${currentUrl}`);
      }
      
      console.log(`ℹ️ 页面已跳转至 ${currentUrl}，继续保存状态`);
    }
    
    // 保存 storage state
    await context.storageState({ path: '.auth/user.json' });
    console.log('✅ 全局登录成功，已保存认证状态');

    // 保存 token（从响应中捕获的优先）
    if (capturedToken) {
      fs.writeFileSync('.auth/token.txt', capturedToken, 'utf-8');
      console.log('✅ Token已保存到 .auth/token.txt（来自API响应）');
    } else {
      // 尝试从 cookies 获取
      const cookies = await context.cookies();
      const tokenCookie = cookies.find(c => c.name === 'token' || c.name.includes('token'));
      
      if (tokenCookie) {
        fs.writeFileSync('.auth/token.txt', tokenCookie.value, 'utf-8');
        console.log('✅ Token已保存到 .auth/token.txt（来自cookie）');
      } else {
        // 尝试从 localStorage 获取
        try {
          const state = await context.storageState();
          let tokenFound = false;
          
          for (const origin of state.origins || []) {
            for (const item of origin.localStorage || []) {
              if (item.name === 'token' || item.name === 'access_token') {
                fs.writeFileSync('.auth/token.txt', item.value, 'utf-8');
                console.log('✅ Token已保存到 .auth/token.txt（来自localStorage）');
                tokenFound = true;
                break;
              }
            }
            if (tokenFound) break;
          }
          
          if (!tokenFound) {
            console.log('⚠️ 未找到Token，但认证状态已保存，测试仍可继续');
          }
        } catch (e) {
          console.log('⚠️ 读取localStorage失败，但认证状态已保存');
        }
      }
    }
  } catch (error) {
    console.error('❌ 全局登录失败:', error);
    
    try {
      const screenshotPath = '.auth/login-failure.png';
      await page.screenshot({ path: screenshotPath, fullPage: true });
      console.log(`📷 已保存失败截图: ${screenshotPath}`);
    } catch (e) {
      console.error('📷 截图保存失败:', e);
    }
    
    throw error;
  } finally {
    await page.close().catch(() => {});
    await context.close().catch(() => {});
    await browser.close().catch(() => {});
  }
}

export default globalSetup;