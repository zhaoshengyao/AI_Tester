import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

test('诊断amis框架表单结构', async ({ page }) => {
  await page.goto('/index');
  await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
  await page.waitForTimeout(3000);
  
  await page.goto('/marketing/clue');
  await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
  await page.waitForTimeout(5000);
  
  const reportLines: string[] = [];
  
  const addButton = page.locator('button').filter({ hasText: /新增|添加/ }).first();
  reportLines.push(`新增按钮存在: ${(await addButton.count()) > 0}`);
  reportLines.push(`新增按钮可见: ${(await addButton.isVisible())}`);
  
  if ((await addButton.count()) > 0 && await addButton.isVisible()) {
    await addButton.click();
    await page.waitForTimeout(8000);
    
    reportLines.push('\n=== 查找所有弹窗相关元素 ===');
    const overlayElements = await page.locator('.el-overlay, .el-modal, .el-modal-dialog, .amis-modal').all();
    reportLines.push(`overlay元素数量: ${overlayElements.length}`);
    
    for (let i = 0; i < overlayElements.length; i++) {
      const el = overlayElements[i];
      const className = await el.getAttribute('class') || '';
      const style = await el.getAttribute('style') || '';
      const isVisible = await el.isVisible();
      const innerText = (await el.textContent()) || '';
      reportLines.push(`元素${i}: class=${className}, visible=${isVisible}, style=${style.substring(0, 100)}, text="${innerText.substring(0, 50)}"`);
    }
    
    reportLines.push('\n=== 查找所有iframe ===');
    const iframes = await page.locator('iframe').all();
    reportLines.push(`iframe数量: ${iframes.length}`);
    
    for (let i = 0; i < iframes.length; i++) {
      const iframe = iframes[i];
      const src = await iframe.getAttribute('src') || '';
      const name = await iframe.getAttribute('name') || '';
      const id = await iframe.getAttribute('id') || '';
      const className = await iframe.getAttribute('class') || '';
      reportLines.push(`iframe${i}: src=${src}, name=${name}, id=${id}, class=${className}`);
      
      if (src) {
        try {
          const frame = await iframe.contentFrame();
          if (frame) {
            const frameContent = await frame.content();
            reportLines.push(`  iframe内容长度: ${frameContent.length}`);
            if (frameContent.length > 0) {
              reportLines.push(`  iframe内容前300字符: ${frameContent.substring(0, 300)}`);
            }
          }
        } catch (error) {
          reportLines.push(`  无法获取iframe内容: ${error}`);
        }
      }
    }
    
    reportLines.push('\n=== 查找所有input元素（全局）===');
    const allInputs = await page.locator('input').all();
    reportLines.push(`全局输入框数量: ${allInputs.length}`);
    
    for (let i = 0; i < Math.min(allInputs.length, 10); i++) {
      const input = allInputs[i];
      const type = await input.getAttribute('type') || '';
      const name = await input.getAttribute('name') || '';
      const placeholder = await input.getAttribute('placeholder') || '';
      const className = await input.getAttribute('class') || '';
      const dataName = await input.getAttribute('data-name') || '';
      const parentClass = await input.locator('..').getAttribute('class') || '';
      reportLines.push(`输入框${i}: type=${type}, name=${name}, data-name=${dataName}, placeholder=${placeholder}, class=${className}, parentClass=${parentClass}`);
    }
    
    reportLines.push('\n=== 查找所有button元素（全局）===');
    const allButtons = await page.locator('button').all();
    reportLines.push(`全局按钮数量: ${allButtons.length}`);
    
    for (let i = 0; i < Math.min(allButtons.length, 15); i++) {
      const button = allButtons[i];
      const text = (await button.textContent()) || '';
      const className = await button.getAttribute('class') || '';
      const type = await button.getAttribute('type') || '';
      reportLines.push(`按钮${i}: text="${text}", class=${className}, type=${type}`);
    }
    
    reportLines.push('\n=== 页面完整HTML（前3000字符）===');
    const pageContent = await page.content();
    reportLines.push(pageContent.substring(0, 3000));
    
    await page.screenshot({ path: path.join(__dirname, '../../diagnose-output/amis-form-diagnose.png') });
    reportLines.push('\n✅ 截图已保存');
  }
  
  const reportPath = path.join(__dirname, '../../diagnose-output/amis-form-report.txt');
  fs.writeFileSync(reportPath, reportLines.join('\n'));
  console.log(`\n诊断报告已保存到: ${reportPath}`);
});