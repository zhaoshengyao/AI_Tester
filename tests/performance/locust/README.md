# CRM 性能测试 - Locust

基于 Locust 的 CRM 原型系统性能测试框架，支持 API 压测和 UI 全链路压测。

## 目录结构

```
locust/
├── api/                    # API 压测脚本
│   ├── locustfile_crm_api.py      # CRM API 压测脚本
│   └── locustfile_smoke.py        # API 冒烟压测脚本
├── ui/                     # UI 压测脚本
│   └── locustfile_ui_smoke.py     # UI 冒烟压测脚本
├── utils/                  # 工具模块
│   ├── auth_helper.py             # 认证辅助工具（含统一配置读取）
│   ├── test_data_loader.py        # 测试数据加载器
│   └── report_generator.py        # 报告生成器
├── config/                 # 配置文件
│   └── load_profiles.yaml         # 负载配置
├── requirements.txt        # 依赖清单
└── README.md               # 本文件
```

## 环境搭建

```bash
# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器内核
playwright install chromium

# 配置环境变量（Windows）
.\scripts\set-test-env.ps1
```

## 配置说明

### 统一配置入口

项目采用 **环境变量优先 + 配置文件兜底** 的统一配置策略：

| 优先级 | 配置来源 | 说明 |
|--------|----------|------|
| 1 | 环境变量 | 运行时动态设置，优先级最高 |
| 2 | `tests/config/env.yaml` | 统一配置文件，作为默认值 |

### 环境变量

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| BASE_URL | http://192.168.2.97:6089 | 被测系统地址（UI） |
| API_BASE_URL | http://192.168.2.97:6089/prod-api | API 基础地址 |
| TEST_USERNAME | admin | 测试账号 |
| TEST_PASSWORD | admin123 | 测试密码 |
| LOCUST_HOST | $BASE_URL | Locust 目标地址 |
| LOCUST_USERS | 5 | 并发用户数 |
| LOCUST_SPAWN_RATE | 1 | 孵化率（每秒启动用户数） |
| LOCUST_RUN_TIME | 120s | 运行时间 |

### 配置文件

- `tests/config/env.yaml`: 项目统一环境配置文件（所有测试框架共享）
- `config/load_profiles.yaml`: 负载配置（冒烟/常规/压力/稳定性）

## 执行命令

### API 冒烟压测

```bash
# 启动 Web UI 模式
locust -f api/locustfile_smoke.py

# 无 Web UI 模式
locust -f api/locustfile_smoke.py \
    --users=5 --spawn-rate=1 --run-time=60s --headless \
    --html=results/api_smoke_report.html
```

### API 全量压测

```bash
locust -f api/locustfile_crm_api.py \
    --users=50 --spawn-rate=5 --run-time=300s --headless \
    --html=results/api_full_report.html
```

### UI 冒烟压测

```bash
locust -f ui/locustfile_ui_smoke.py \
    --users=5 --spawn-rate=1 --run-time=120s --headless \
    --html=results/ui_smoke_report.html
```

## 监控面板

启动后访问 `http://localhost:8089` 查看实时监控：

- **RPS**: 每秒请求数
- **Response Time**: 响应时间（Avg/P95/P99）
- **Error Rate**: 错误率
- **Active Users**: 活跃用户数

## 注意事项

1. UI 压测资源消耗较高，建议从 5 并发开始
2. 确保被测系统有足够的测试数据
3. 压测前确认网络环境稳定
4. 建议在非工作时间执行压力测试
5. 配置修改后需重新运行 `set-test-env.ps1` 生效

## 扩展指南

### 添加新的 API 压测任务

在 `api/locustfile_crm_api.py` 中添加新的 `@task` 方法：

```python
@task(weight)
def new_task(self):
    """新任务描述"""
    self.client.get("/api/endpoint")
```

### 添加新的 UI 压测任务

在 `ui/locustfile_ui_smoke.py` 中添加新的 `@task` 方法，使用 `@pw` 装饰器：

```python
@task(weight)
@pw
async def new_ui_task(self, page):
    """新 UI 任务描述"""
    await page.goto("/path")
```

### 修改环境配置

统一修改 `tests/config/env.yaml`，或通过环境变量覆盖：

```powershell
$env:BASE_URL="http://new-host:8080"
$env:TEST_USERNAME="testuser"
```