/**
 * 测试数据管理器
 * 用于生成唯一的测试数据名称，跟踪创建的数据，便于清理
 */

export interface TestDataItem {
  type: string; // 数据类型：clue, customer, contact, business, quotation, product
  name: string; // 数据名称
  createdAt: number; // 创建时间戳
  metadata?: Record<string, string>; // 附加元数据
}

export class TestDataManager {
  private static instance: TestDataManager;
  private dataStore: TestDataItem[] = [];
  private testPrefix: string;
  private testTimestamp: number;

  private constructor(prefix: string = '自动化测试') {
    this.testPrefix = prefix;
    this.testTimestamp = Date.now();
  }

  /**
   * 获取单例实例
   */
  static getInstance(prefix?: string): TestDataManager {
    if (!TestDataManager.instance) {
      TestDataManager.instance = new TestDataManager(prefix);
    }
    return TestDataManager.instance;
  }

  /**
   * 重置实例（用于新测试会话）
   */
  static resetInstance(): void {
    TestDataManager.instance = new TestDataManager();
  }

  /**
   * 生成唯一测试数据名称
   */
  generateName(type: string, customSuffix?: string): string {
    const shortTimestamp = String(this.testTimestamp).slice(-6);
    const suffix = customSuffix || shortTimestamp;
    return `${this.testPrefix}_${type}_${suffix}`;
  }

  /**
   * 记录创建的数据
   */
  recordData(type: string, name: string, metadata?: Record<string, string>): void {
    const item: TestDataItem = {
      type,
      name,
      createdAt: this.testTimestamp,
      metadata
    };
    this.dataStore.push(item);
    console.log(`📝 记录测试数据: [${type}] ${name}`);
  }

  /**
   * 获取所有记录的数据
   */
  getAllData(): TestDataItem[] {
    return [...this.dataStore];
  }

  /**
   * 按类型获取数据
   */
  getDataByType(type: string): TestDataItem[] {
    return this.dataStore.filter(item => item.type === type);
  }

  /**
   * 获取最后创建的指定类型数据
   */
  getLastData(type: string): TestDataItem | undefined {
    const items = this.getDataByType(type);
    return items.length > 0 ? items[items.length - 1] : undefined;
  }

  /**
   * 获取测试统计信息
   */
  getStats(): Record<string, number> {
    const stats: Record<string, number> = {
      total: this.dataStore.length
    };
    
    const types = [...new Set(this.dataStore.map(item => item.type))];
    types.forEach(type => {
      stats[type] = this.getDataByType(type).length;
    });
    
    return stats;
  }

  /**
   * 清理所有记录
   */
  clearAll(): void {
    console.log(`🗑️ 清理 ${this.dataStore.length} 条测试数据记录`);
    this.dataStore = [];
  }

  /**
   * 打印所有记录
   */
  printAll(): void {
    console.log('📊 测试数据记录:');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    
    const stats = this.getStats();
    console.log(`  总计: ${stats.total} 条`);
    
    const types = [...new Set(this.dataStore.map(item => item.type))];
    types.forEach(type => {
      const items = this.getDataByType(type);
      console.log(`  ${type}: ${items.length} 条`);
      items.forEach(item => {
        console.log(`    - ${item.name}`);
      });
    });
    
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  }

  /**
   * 生成电话号码
   */
  generatePhone(): string {
    const shortTimestamp = String(this.testTimestamp).slice(-8);
    return `138${shortTimestamp}`;
  }

  /**
   * 生成邮箱
   */
  generateEmail(domain: string = 'test.com'): string {
    const shortTimestamp = String(this.testTimestamp).slice(-6);
    return `auto_${shortTimestamp}@${domain}`;
  }

  /**
   * 生成随机字符串（用于唯一ID等）
   */
  generateRandomString(length: number = 8): string {
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  }

  /**
   * 获取测试前缀
   */
  getTestPrefix(): string {
    return this.testPrefix;
  }

  /**
   * 获取测试时间戳
   */
  getTestTimestamp(): number {
    return this.testTimestamp;
  }

  /**
   * 检查名称是否为测试数据
   */
  static isTestDataName(name: string, prefix?: string): boolean {
    const checkPrefix = prefix || '自动化测试';
    return name.startsWith(checkPrefix) || name.startsWith('全链路测试') || name.startsWith('测试');
  }
}