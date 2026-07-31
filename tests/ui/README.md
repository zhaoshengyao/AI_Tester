# UI 自动化测试

基于 **Playwright + TypeScript** 框架的 CRM 系统 UI 自动化测试。

## 目录结构

```
tests/ui/
├── package.json             # npm 依赖与脚本
├── playwright.config.ts      # Playwright 配置
├── tsconfig.json             # TypeScript 配置
├── pages/                    # Page Objects
│   ├── BasePage.ts           # 基础页面类
│   ├── LoginPage.ts          # 登录页
│   ├── HomePage.ts           # 首页
│   ├── CustomerManagementPage.ts
│   ├── ClueManagementPage.ts
│   ├── BusinessManagementPage.ts
│   ├── QuotationManagementPage.ts
│   ├── ProductManagementPage.ts
│   ├── PublicPoolPage.ts     # 公海池
│   ├── SystemManagementPage.ts
│   ├── GoalPage.ts           # 目标管理
│   └── TodoPage.ts           # 待办
├── specs/                    # 测试用例
│   ├── crm/                  # CRM 模块
│   ├── system/               # 系统管理模块
│   ├── report/               # 报表
│   ├── target/               # 目标
│   ├── workspace/            # 工作台
│   ├── performance/          # 性能页面
│   ├── prototype/            # 原型分析
│   ├── diagnose/             # 诊断
│   └── ...
├── tests/ui/.auth/user.json  # 全局登录状态（复用登录）
└── tests/ui/test-results/    # 测试结果
```

## 快速开始

### 环境准备

```bash
# 1. 确保 Node.js LTS（推荐 v20+）
node --version

# 2. 安装依赖
cd tests/ui
npm install

# 3. 安装浏览器（首次）
npx playwright install chromium

# 4. 配置项目根目录 .env
# BASE_URL=http://192.168.2.97:6089
# TEST_USERNAME=ZhaoShengYao
# TEST_PASSWORD=123456
```

### 执行测试

```bash
# 进入目录
cd tests/ui

# 运行全部测试
npm run test

# 运行冒烟测试（核心页面可达性）
npm run test:smoke

# 运行兼容性测试（多浏览器）
npm run test:compat

# 查看报告
npm run report

# 指定浏览器
npx playwright test --project=chromium
npx playwright test --project=firefox

# 指定测试文件
npx playwright test specs/crm/crm-smoke.spec.ts
npx playwright test specs/crm/crm-crud.spec.ts

# 指定关键字
npx playwright test -g "smoke"

# 调试模式（单步执行）
npx playwright test --debug

# 带截图和视频
npx playwright test --screenshots=on --videos=on
```

## Page Object 模式

所有页面继承 `BasePage`，提供统一的元素定位和操作方法：

```typescript
// 示例：使用客户管理页
import { CustomerManagementPage } from '../pages/CustomerManagementPage';

test('创建客户', async ({ page }) => {
    const customerPage = new CustomerManagementPage(page);
    await customerPage.navigate();
    await customerPage.createCustomer({ name: '测试客户', phone: '13800000000' });
    await expect(page.getByText('测试客户')).toBeVisible();
});
```

### 多策略元素定位

表单字段采用多策略定位（按优先级）：
1. `el-form-item` 标签
2. `placeholder` 属性
3. `aria-label` 属性
4. `label for` 属性
5. `span label` 文本

### 动态弹窗处理

使用 `waitForDialog()` 方法处理异步弹窗：
```typescript
await page.waitForDialog({ title: '确认删除', timeout: 5000 });
```

## 测试模块说明

| 模块 | 文件 | 说明 |
|------|------|------|
| CRM 冒烟 | `specs/crm/crm-smoke.spec.ts` | 登录、首页、核心导航可达性 |
| CRM 结构 | `specs/crm/crm-structure.spec.ts` | 页面结构验证 |
| CRM CRUD | `specs/crm/crm-crud.spec.ts` | 客户增删改查 |
| 线索管理 | `specs/crm/clue-crud.spec.ts` | 线索增删改查 |
| 商机管理 | `specs/crm/business-crud.spec.ts` | 商机增删改查 |
| 商机流程 | `specs/crm/business-process.spec.ts` | 商机阶段推进 |
| 产品管理 | `specs/crm/product-crud.spec.ts` | 产品增删改查 |
| 报价管理 | `specs/crm/quotation-crud.spec.ts` | 报价增删改查 |
| 系统管理 | `specs/system/*.spec.ts` | 用户/角色/菜单/部门 |
| 报表 | `specs/report/report.spec.ts` | 报表查看与筛选 |
| 目标管理 | `specs/target/target.spec.ts` | 目标设置与查看 |
| 工作台 | `specs/workspace/workspace.spec.ts` | 首页工作台 |
| 性能页面 | `specs/performance/performance.spec.ts` | 性能指标页面 |
| 原型分析 | `specs/prototype/*.spec.ts` | 原型与实际对比 |
| 诊断 | `specs/diagnose*.spec.ts` | 系统诊断功能 |

## 全局登录状态

项目采用 **globalSetup + storageState** 机制复用登录：

```
tests/ui/.auth/user.json   # 存储登录后的 Cookie/LocalStorage
```

- 首次执行会自动登录并保存状态
- 后续执行直接复用，避免重复登录
- Token 过期时自动重新登录

## Playwright 配置

```typescript
// playwright.config.ts 关键配置
export default defineConfig({
    projects: [
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
        { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    ],
    use: {
        baseURL: process.env.BASE_URL,
        storageState: '.auth/user.json',
        trace: 'retain-on-failure',
        screenshot: 'only-on-failure',
    },
});
```

## 结果查看

```
tests/ui/test-results/         # Playwright 原始结果
tests/ui/playwright-report/    # HTML 报告（npx playwright show-report）
docs/test-runs/{batch}/reports/UI自动化测试报告.md    # 归档报告
docs/test-runs/{batch}/defects/UI缺陷清单.md          # 归档缺陷
```

## 故障排查

| 问题 | 排查方法 |
|------|----------|
| `spawn EPERM` 错误 | Node 版本问题，使用 Node.js LTS |
| 登录失败 | 检查 .env 中 TEST_USERNAME/TEST_PASSWORD |
| 页面超时 | 增加 `actionTimeout` 和 `navigationTimeout` |
| 元素找不到 | 使用多策略定位或添加等待 |
| 浏览器未安装 | `npx playwright install chromium` |
| 登录状态失效 | 删除 `.auth/user.json` 重新登录 |

## 测试分层

| 层级 | 说明 | 示例 |
|------|------|------|
| smoke | 登录 + 首页 + 核心导航 | crm-smoke.spec.ts |
| readonly-regression | 列表/筛选/详情（只读） | report.spec.ts |
| semi-auto | 写操作入口/弹窗/校验（不提交） | 各模块 CRUD 冒烟 |
| write-regression | 真实写操作（需回滚策略） | business-crud.spec.ts |
| compatibility | 多浏览器兼容性 | test:compat |

## 与总控脚本集成

```bash
# 方式一：直接执行
npm run test:smoke

# 方式二：通过项目总控脚本
pwsh -File ../../scripts/run-ui-tests.ps1

# 标记未执行（环境不满足时）
pwsh -File ../../scripts/run-ui-tests.ps1 -ForceNotExecutedReason "Node 版本非 LTS"
```
