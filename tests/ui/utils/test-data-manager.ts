import * as fs from 'fs';
import * as path from 'path';

interface TestDataRecord {
  type: string;
  id: number;
  info: Record<string, any>;
  createdAt: string;
}

interface CleanupResult {
  type: string;
  id: number;
  deleted: boolean;
  error?: string;
}

export class TestDataManager {
  private apiBaseUrl: string;
  private authToken: string;
  private headers: Record<string, string>;
  private dataDir: string;
  private createdData: TestDataRecord[] = [];

  constructor(apiBaseUrl?: string, authToken?: string) {
    this.apiBaseUrl = apiBaseUrl || process.env.API_BASE_URL || 'http://192.168.2.97:6089/prod-api';
    this.authToken = authToken || '';
    this.headers = this.authToken ? { Authorization: `Bearer ${this.authToken}` } : {};
    this.dataDir = path.join(__dirname, '../../data');
    this.ensureDataDir();
  }

  private ensureDataDir(): void {
    if (!fs.existsSync(this.dataDir)) {
      fs.mkdirSync(this.dataDir, { recursive: true });
    }
  }

  loadTestData(dataType: string): Record<string, any> {
    const dataFile = path.join(this.dataDir, `${dataType}.json`);
    if (fs.existsSync(dataFile)) {
      const content = fs.readFileSync(dataFile, 'utf-8');
      return JSON.parse(content);
    }
    return this.generateDefaultData(dataType);
  }

  private generateDefaultData(dataType: string): Record<string, any> {
    const timestamp = Date.now().toString();
    const uniqueId = Math.random().toString(36).substring(2, 10);

    const templates: Record<string, Record<string, any>> = {
      customer: {
        customerName: `test_customer_${uniqueId}`,
        contactName: `Contact_${uniqueId}`,
        phone: `13800${timestamp.slice(-8)}`,
        email: `test_${uniqueId}@example.com`,
        address: `Test Address ${uniqueId}`,
        industry: 'IT',
        scale: '1-10人',
        source: '线上',
        status: '正常'
      },
      business: {
        businessName: `test_business_${uniqueId}`,
        customerId: 1,
        customerName: `test_customer_${uniqueId}`,
        amount: 10000.00,
        probability: 50,
        stage: '需求确认',
        expectedCloseDate: new Date().toISOString().split('T')[0],
        responsible: '测试用户'
      },
      clue: {
        name: `Clue_${uniqueId}`,
        phone: `13900${timestamp.slice(-8)}`,
        company: `Company_${uniqueId}`,
        source: '线上',
        status: '待领取'
      },
      product: {
        productName: `test_product_${uniqueId}`,
        productCode: `PRO_${uniqueId}`,
        category: '默认分类',
        price: 1000.00,
        status: '启用',
        description: '自动化测试产品'
      }
    };

    return templates[dataType] || {};
  }

  saveCreatedData(dataType: string, dataId: number, dataInfo?: Record<string, any>): void {
    const record: TestDataRecord = {
      type: dataType,
      id: dataId,
      info: dataInfo || {},
      createdAt: new Date().toISOString()
    };
    this.createdData.push(record);

    const historyFile = path.join(this.dataDir, 'created_data_history.json');
    let history: TestDataRecord[] = [];
    if (fs.existsSync(historyFile)) {
      history = JSON.parse(fs.readFileSync(historyFile, 'utf-8'));
    }
    history.push(record);
    fs.writeFileSync(historyFile, JSON.stringify(history, null, 2), 'utf-8');
  }

  async cleanupCreatedData(): Promise<CleanupResult[]> {
    const results: CleanupResult[] = [];

    for (const record of [...this.createdData].reverse()) {
      try {
        const deleted = await this.deleteData(record.type, record.id);
        results.push({
          type: record.type,
          id: record.id,
          deleted
        });
      } catch (error) {
        results.push({
          type: record.type,
          id: record.id,
          deleted: false,
          error: error instanceof Error ? error.message : String(error)
        });
      }
    }

    this.createdData = [];

    const cleanupLog = path.join(this.dataDir, 'cleanup_log.json');
    fs.writeFileSync(cleanupLog, JSON.stringify({
      cleanupTime: new Date().toISOString(),
      results
    }, null, 2), 'utf-8');

    return results;
  }

  async cleanupTestDataByPattern(): Promise<CleanupResult[]> {
    const results: CleanupResult[] = [];

    const cleanupConfigs = [
      { type: 'customer', endpoint: '/crm/customer/page', nameField: 'customerName', deleteEndpoint: '/crm/customer/' },
      { type: 'business', endpoint: '/crm/business/page', nameField: 'businessName', deleteEndpoint: '/crm/business/' },
      { type: 'clue', endpoint: '/crm/clue/page', nameField: 'name', deleteEndpoint: '/crm/clue/' },
      { type: 'product', endpoint: '/product/page', nameField: 'productName', deleteEndpoint: '/product/' }
    ];

    for (const config of cleanupConfigs) {
      try {
        const response = await fetch(`${this.apiBaseUrl}${config.endpoint}?pageNum=1&pageSize=100`, {
          headers: this.headers
        });

        if (response.ok) {
          const data = await response.json();
          const items = data.data?.rows || data.rows || [];

          for (const item of items) {
            const name = item[config.nameField];
            if (name && (name.includes('AutoTest') || name.includes('test_') || name.includes('测试'))) {
              const deleteResult = await this.deleteDataByEndpoint(config.deleteEndpoint, item.id);
              results.push({
                type: config.type,
                id: item.id,
                deleted: deleteResult
              });
            }
          }
        }
      } catch (error) {
        console.log(`清理${config.type}数据时出错: ${error}`);
      }
    }

    return results;
  }

  private async deleteData(dataType: string, dataId: number): Promise<boolean> {
    const endpoints: Record<string, string> = {
      customer: `/crm/customer/${dataId}`,
      business: `/crm/business/${dataId}`,
      clue: `/crm/clue/${dataId}`,
      product: `/product/${dataId}`
    };

    const endpoint = endpoints[dataType];
    if (!endpoint) return false;

    try {
      const url = `${this.apiBaseUrl}${endpoint}`;
      const options: RequestInit = {
        method: 'DELETE',
        headers: this.headers
      };
      const response = await fetch(url, options);
      return response.status === 200 || response.status === 204;
    } catch {
      return false;
    }
  }

  private async deleteDataByEndpoint(endpoint: string, dataId: number): Promise<boolean> {
    try {
      const url = `${this.apiBaseUrl}${endpoint}${dataId}`;
      const options: RequestInit = {
        method: 'DELETE',
        headers: this.headers
      };
      const response = await fetch(url, options);
      return response.status === 200 || response.status === 204;
    } catch {
      return false;
    }
  }

  async initTestData(): Promise<Record<string, any>> {
    const initData: Record<string, any> = {};

    const customerData = this.loadTestData('customer');
    const customerId = await this.createCustomer(customerData);
    if (customerId) {
      initData.customer = { id: customerId, ...customerData };
    }

    const businessData = this.loadTestData('business');
    businessData.customerId = customerId || 1;
    businessData.customerName = customerData.customerName || '';
    const businessId = await this.createBusiness(businessData);
    if (businessId) {
      initData.business = { id: businessId, ...businessData };
    }

    const clueData = this.loadTestData('clue');
    const clueId = await this.createClue(clueData);
    if (clueId) {
      initData.clue = { id: clueId, ...clueData };
    }

    const productData = this.loadTestData('product');
    const productId = await this.createProduct(productData);
    if (productId) {
      initData.product = { id: productId, ...productData };
    }

    return initData;
  }

  private async createCustomer(data: Record<string, any>): Promise<number> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/crm/customer`, {
        method: 'POST',
        headers: { ...this.headers, 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        const result = await response.json();
        const customerId = result.data?.id;
        if (customerId) {
          this.saveCreatedData('customer', customerId, data);
          return customerId;
        }
      }
    } catch {
      // ignore
    }
    return 0;
  }

  private async createBusiness(data: Record<string, any>): Promise<number> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/crm/business`, {
        method: 'POST',
        headers: { ...this.headers, 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        const result = await response.json();
        const businessId = result.data?.id;
        if (businessId) {
          this.saveCreatedData('business', businessId, data);
          return businessId;
        }
      }
    } catch {
      // ignore
    }
    return 0;
  }

  private async createClue(data: Record<string, any>): Promise<number> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/crm/clue`, {
        method: 'POST',
        headers: { ...this.headers, 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        const result = await response.json();
        const clueId = result.data?.id;
        if (clueId) {
          this.saveCreatedData('clue', clueId, data);
          return clueId;
        }
      }
    } catch {
      // ignore
    }
    return 0;
  }

  private async createProduct(data: Record<string, any>): Promise<number> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/product`, {
        method: 'POST',
        headers: { ...this.headers, 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        const result = await response.json();
        const productId = result.data?.id;
        if (productId) {
          this.saveCreatedData('product', productId, data);
          return productId;
        }
      }
    } catch {
      // ignore
    }
    return 0;
  }
}

export function getTestDataManager(apiBaseUrl?: string, authToken?: string): TestDataManager {
  return new TestDataManager(apiBaseUrl, authToken);
}
