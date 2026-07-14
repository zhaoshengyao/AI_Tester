/**
 * 规则验证引擎 - 多维度交叉验证
 * 预留LLM扩展接口
 */

export interface ValidationRule {
  id: string;
  description: string;
  condition: (data: ScanResult) => boolean;
  weight: number; // 权重 0-1
}

export interface ScanResult {
  text: string;
  url: string;
  elements: string[];
  pageTitle: string;
  responseCode?: number;
}

export interface ValidationResult {
  overallConfidence: number;
  ruleResults: RuleResult[];
  isConfirmed: boolean;
}

export interface RuleResult {
  ruleId: string;
  description: string;
  passed: boolean;
  weight: number;
  contribution: number;
}

export class ValidationEngine {
  private rules: ValidationRule[];
  private threshold: number; // 确认阈值
  private useLLM: boolean;
  
  constructor(threshold: number = 0.7) {
    this.threshold = threshold;
    this.useLLM = false;
    this.rules = this.initializeRules();
  }
  
  /**
   * 初始化验证规则
   */
  private initializeRules(): ValidationRule[] {
    return [
      // URL有效性验证 (30%)
      {
        id: 'url-valid',
        description: 'URL格式有效',
        condition: (data) => {
          if (!data.url) return false;
          return data.url.startsWith('/') || 
                 data.url.startsWith('#') || 
                 data.url.startsWith('http');
        },
        weight: 0.3
      },
      // 页面响应验证 (25%)
      {
        id: 'page-accessible',
        description: '页面可访问',
        condition: (data) => {
          // 如果有响应码，检查是否为200
          if (data.responseCode !== undefined) {
            return data.responseCode === 200;
          }
          // 没有响应码时，检查页面标题是否存在
          return !!(data.pageTitle && data.pageTitle.length > 0);
        },
        weight: 0.25
      },
      // 内容存在验证 (20%)
      {
        id: 'content-exists',
        description: '页面包含内容',
        condition: (data) => {
          return data.elements.length > 0;
        },
        weight: 0.2
      },
      // 关键词验证 (15%)
      {
        id: 'keyword-present',
        description: '包含业务关键词',
        condition: (data) => {
          const businessKeywords = ['管理', '列表', '新增', '编辑', '删除', '报表'];
          return businessKeywords.some(k => data.text.includes(k));
        },
        weight: 0.15
      },
      // 文本长度验证 (10%)
      {
        id: 'text-reasonable',
        description: '文本长度合理',
        condition: (data) => {
          return data.text.length >= 2 && data.text.length <= 50;
        },
        weight: 0.1
      }
    ];
  }
  
  /**
   * 执行验证
   */
  validate(scanResult: ScanResult): ValidationResult {
    let totalConfidence = 0;
    const ruleResults: RuleResult[] = [];
    
    for (const rule of this.rules) {
      const passed = rule.condition(scanResult);
      const contribution = passed ? rule.weight : 0;
      totalConfidence += contribution;
      
      ruleResults.push({
        ruleId: rule.id,
        description: rule.description,
        passed,
        weight: rule.weight,
        contribution
      });
    }
    
    // 如果启用LLM，进行二次验证
    if (this.useLLM) {
      totalConfidence = this.enhanceWithLLM(scanResult, totalConfidence);
    }
    
    return {
      overallConfidence: totalConfidence,
      ruleResults,
      isConfirmed: totalConfidence >= this.threshold
    };
  }
  
  /**
   * 预留LLM增强接口
   */
  private enhanceWithLLM(_scanResult: ScanResult, baseConfidence: number): number {
    // TODO: 调用LLM进行语义分析
    // 根据LLM分析结果调整置信度
    // 示例：如果LLM确认内容合理，增加置信度
    return baseConfidence * 1.1; // 模拟LLM增强效果
  }
  
  /**
   * 添加自定义验证规则
   */
  addRule(rule: ValidationRule) {
    this.rules.push(rule);
    // 添加后统一归一化权重
    const totalWeight = this.rules.reduce((sum, r) => sum + r.weight, 0);
    this.rules.forEach(r => r.weight /= totalWeight);
  }
  
  /**
   * 设置阈值
   */
  setThreshold(threshold: number) {
    this.threshold = threshold;
  }
  
  /**
   * 设置LLM模式
   */
  setLLMEnabled(enabled: boolean) {
    this.useLLM = enabled;
  }
  
  /**
   * 获取所有规则
   */
  getRules(): ValidationRule[] {
    return this.rules;
  }
  
  /**
   * 获取阈值
   */
  getThreshold(): number {
    return this.threshold;
  }
}