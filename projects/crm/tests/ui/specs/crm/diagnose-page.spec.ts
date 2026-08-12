import { test } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

test('诊断新增线索弹窗结构', async ({ page }) => {
  await page.goto('/index');
  await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
  await page.waitForTimeout(3000);
  
  await page.goto('/marketing/clue');
  await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
  await page.waitForTimeout(5000);
  
  const reportLines: string[] = [];
  
  // 截图当前页面
  await page.screenshot({ path: path.join(__dirname, '../../diagnose-output/before-click.png'), fullPage: true });
  reportLines.push('✅ 点击前截图已保存');
  
  // 查找所有包含"新增"的按钮
  const addButtons = await page.locator('button').filter({ hasText: /新增/ }).all();
  reportLines.push(`\n找到包含"新增"的按钮数量: ${addButtons.length}`);
  
  for (let i = 0; i < addButtons.length; i++) {
    const btn = addButtons[i];
    const text = (await btn.textContent()) || '';
    const className = await btn.getAttribute('class') || '';
    const rect = await btn.boundingBox();
    const isVisible = await btn.isVisible();
    const isEnabled = await btn.isEnabled();
    reportLines.push(`  按钮${i}: text="${text}", class=${className}, visible=${isVisible}, enabled=${isEnabled}, rect=${JSON.stringify(rect)}`);
  }
  
  // 点击第一个可见的新增按钮
  const firstAddButton = page.locator('button').filter({ hasText: /新增/ }).first();
  if ((await firstAddButton.count()) > 0 && await firstAddButton.isVisible()) {
    reportLines.push('\n✅ 准备点击第一个新增按钮');
    
    // 等待弹窗出现的Promise
    const dialogPromise = page.waitForSelector('.el-dialog', { timeout: 15000 }).catch(() => null);
    
    // 点击按钮
    await firstAddButton.click();
    reportLines.push('✅ 已点击新增按钮');
    
    // 等待弹窗出现
    const dialog = await dialogPromise;
    if (dialog) {
      reportLines.push('✅ 弹窗已出现');
      
      await page.waitForTimeout(3000);
      
      // 截图弹窗
      await page.screenshot({ path: path.join(__dirname, '../../diagnose-output/after-click.png'), fullPage: true });
      reportLines.push('✅ 点击后截图已保存');
      
      // 检查弹窗标题
      const title = await dialog.locator('.el-dialog__title').first().textContent();
      reportLines.push(`弹窗标题: "${title || ''}"`);
      
      // 检查弹窗内的表单结构
      const formItems = await dialog.locator('.el-form-item').all();
      reportLines.push(`\n弹窗内el-form-item数量: ${formItems.length}`);
      
      for (let i = 0; i < formItems.length; i++) {
        const item = formItems[i];
        const label = await item.locator('.el-form-item__label').first().textContent();
        const labelText = label ? label.replace(/[\s:*]/g, '') : '';
        
        // 检查输入框
        const input = item.locator('input').first();
        const inputType = await input.getAttribute('type') || '';
        const inputPlaceholder = await input.getAttribute('placeholder') || '';
        
        // 检查下拉选择器
        const select = item.locator('.el-select').first();
        const selectPlaceholder = await select.locator('.el-select__placeholder').first().textContent();
        
        // 检查文本域
        const textarea = item.locator('textarea').first();
        const textareaPlaceholder = await textarea.getAttribute('placeholder') || '';
        
        // 判断字段类型
        let fieldType = 'unknown';
        let placeholder = '';
        if ((await input.count()) > 0) {
          fieldType = 'input';
          placeholder = inputPlaceholder;
        } else if ((await select.count()) > 0) {
          fieldType = 'select';
          placeholder = selectPlaceholder || '';
        } else if ((await textarea.count()) > 0) {
          fieldType = 'textarea';
          placeholder = textareaPlaceholder;
        }
        
        reportLines.push(`  字段${i}: label="${labelText}", type=${fieldType}, placeholder="${placeholder}"`);
      }
      
      // 检查按钮
      const buttons = await dialog.locator('button').all();
      reportLines.push(`\n弹窗内按钮数量: ${buttons.length}`);
      for (let i = 0; i < buttons.length; i++) {
        const btn = buttons[i];
        const text = (await btn.textContent()) || '';
        const className = await btn.getAttribute('class') || '';
        reportLines.push(`  按钮${i}: text="${text}", class=${className}`);
      }
      
    } else {
      reportLines.push('❌ 等待弹窗超时');
      
      // 检查所有可能的弹窗元素
      reportLines.push('\n=== 检查所有可能的弹窗元素 ===');
      
      const allOverlays = await page.locator('.el-overlay').all();
      reportLines.push(`el-overlay数量: ${allOverlays.length}`);
      for (let i = 0; i < allOverlays.length; i++) {
        const el = allOverlays[i];
        const className = await el.getAttribute('class') || '';
        const isVisible = await el.isVisible();
        const rect = await el.boundingBox();
        reportLines.push(`  overlay${i}: class=${className}, visible=${isVisible}, rect=${JSON.stringify(rect)}`);
      }
      
      const allDialogs = await page.locator('[role="dialog"]').all();
      reportLines.push(`\n[role="dialog"]数量: ${allDialogs.length}`);
      for (let i = 0; i < allDialogs.length; i++) {
        const el = allDialogs[i];
        const className = await el.getAttribute('class') || '';
        const isVisible = await el.isVisible();
        const rect = await el.boundingBox();
        reportLines.push(`  dialog${i}: class=${className}, visible=${isVisible}, rect=${JSON.stringify(rect)}`);
      }
      
      const bodyChildren = await page.locator('body > *').all();
      reportLines.push(`\nbody子元素数量: ${bodyChildren.length}`);
      for (let i = 0; i < bodyChildren.length; i++) {
        const child = bodyChildren[i];
        const tagName = await child.evaluate(el => el.tagName);
        const className = await child.getAttribute('class') || '';
        const id = await child.getAttribute('id') || '';
        const isVisible = await child.isVisible();
        reportLines.push(`  ${tagName}: id="${id}", class="${className}", visible=${isVisible}`);
      }
      
      // 截图
      await page.screenshot({ path: path.join(__dirname, '../../diagnose-output/no-dialog.png'), fullPage: true });
      reportLines.push('✅ 无弹窗截图已保存');
    }
  } else {
    reportLines.push('❌ 未找到可见的新增按钮');
  }
  
  const reportPath = path.join(__dirname, '../../diagnose-output/dialog-report.txt');
  fs.writeFileSync(reportPath, reportLines.join('\n'));
  console.log(`\n诊断报告已保存到: ${reportPath}`);
});
