import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

export class TodoPage extends BasePage {
  private todoList: Locator;

  constructor(page: Page) {
    super(page);
    this.todoList = page.locator('.todo-list, .el-timeline, [class*="todo"]');
  }

  async navigate(): Promise<void> {
    await super.navigate('/myAgenda');
  }

  async navigateFromHome(): Promise<void> {
    console.log('📝 从首页导航到待办');
    
    const todoMenu = this.page.locator('a[href*="myAgenda"], a[href*="agenda"]').first();
    if ((await todoMenu.count()) > 0) {
      await todoMenu.click();
      await this.page.waitForTimeout(3000);
      console.log('✅ 已导航到待办页面');
      return;
    }
    
    const todoMenuText = this.page.locator('a, span, div').filter({ hasText: /待办/ }).first();
    if ((await todoMenuText.count()) > 0) {
      await todoMenuText.click();
      await this.page.waitForTimeout(3000);
      console.log('✅ 通过文字匹配导航到待办');
      return;
    }
    
    console.log('⚠️ 未找到待办菜单');
  }

  async isPageAvailable(): Promise<boolean> {
    try {
      void this.todoList;
      await this.page.waitForSelector('.el-main, main, .todo-list', { state: 'attached', timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  async getTodoCount(): Promise<number> {
    const todoItems = this.page.locator('.el-timeline-item, .todo-item, [class*="todo-item"]');
    return await todoItems.count();
  }

  async getTodoList(): Promise<Array<{ title: string; status: string }>> {
    const todos: Array<{ title: string; status: string }> = [];
    
    const todoItems = this.page.locator('.el-timeline-item, .todo-item, [class*="todo-item"]');
    const count = await todoItems.count();
    
    for (let i = 0; i < count; i++) {
      const item = todoItems.nth(i);
      const text = await item.textContent();
      todos.push({
        title: text?.split('\n')[0].trim() || '未知待办',
        status: 'pending'
      });
    }
    
    return todos;
  }

  async processTodo(keyword: string): Promise<boolean> {
    console.log(`🔍 处理待办: ${keyword}`);
    
    const todoItems = this.page.locator('.el-timeline-item, .todo-item, [class*="todo-item"]');
    const count = await todoItems.count();
    
    for (let i = 0; i < count; i++) {
      const item = todoItems.nth(i);
      const text = await item.textContent();
      if (text?.includes(keyword)) {
        // 点击处理按钮
        const processBtn = item.locator('button').filter({ hasText: /处理|完成|关闭/ }).first();
        if ((await processBtn.count()) > 0) {
          await processBtn.click();
          console.log(`✅ 点击处理按钮`);
          await this.page.waitForTimeout(2000);
          return true;
        }
      }
    }
    
    console.log(`⚠️ 未找到待办: ${keyword}`);
    return false;
  }

  async closeTodo(keyword: string): Promise<boolean> {
    console.log(`🔍 关闭待办: ${keyword}`);
    
    const closeButtons = this.page.locator('button').filter({ hasText: /关闭/ });
    const count = await closeButtons.count();
    
    for (let i = 0; i < count; i++) {
      const btn = closeButtons.nth(i);
      if (await btn.isVisible()) {
        await btn.click();
        console.log('✅ 点击关闭按钮');
        await this.page.waitForTimeout(1000);
        return true;
      }
    }
    
    return false;
  }

  async verifyTodoExists(keyword: string): Promise<boolean> {
    const pageText = await this.page.textContent('body');
    return pageText?.includes(keyword) ?? false;
  }
}
