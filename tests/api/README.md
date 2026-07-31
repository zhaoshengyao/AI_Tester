# API 自动化测试

基于 **pytest** 框架的 CRM 系统接口自动化测试。

## 目录结构

```
tests/api/
├── conftest.py              # pytest fixtures（认证、数据管理）
├── pytest.ini               # pytest 配置
├── clients/                 # HTTP 客户端封装
│   ├── base_client.py       # 基础客户端
│   └── crm_client.py        # CRM 系统客户端
├── utils/                   # 工具模块
│   ├── auth.py              # Token 认证管理
│   └── test_data_manager.py # 测试数据管理
├── testsuites/              # 测试用例
│   └── crm/                 # CRM 模块测试
└── reports/                 # 测试报告输出
```

## 快速开始

### 环境准备

```bash
# 安装依赖
pip install -r ../../requirements.txt

# 或单独安装
pip install pytest requests python-dotenv
```

### 配置

在项目根目录 `.env` 文件中配置：

```env
API_BASE_URL=http://192.168.2.97:6089/prod-api
API_USERNAME=ZhaoShengYao
API_PASSWORD=123456
```

### 执行测试

```bash
# 进入目录
cd tests/api

# 收集用例（验证脚本可加载）
python -m pytest testsuites/ --collect-only -q

# 运行全部测试
python -m pytest testsuites/ -v

# 运行冒烟测试（快速验证核心接口）
python -m pytest testsuites/ -m smoke -v

# 运行指定模块
python -m pytest testsuites/crm/test_crm_workflow.py -v

# 运行指定用例（关键字过滤）
python -m pytest testsuites/crm/test_crm_api.py -k "test_auth" -v

# 生成报告
python -m pytest testsuites/ --html=reports/html/report.html --junitxml=reports/junit/report.xml -v
```

## 测试模块说明

| 模块 | 文件 | 说明 | 用例数 |
|------|------|------|--------|
| CRM 核心 API | `testsuites/crm/test_crm_api.py` | 基础接口列表、详情查询 | ~20 |
| CRM CRUD | `testsuites/crm/test_crm_crud.py` | 客户增删改查 | ~15 |
| CRM 业务 | `testsuites/crm/test_crm_business.py` | 商机 CRUD + 阶段推进 | ~15 |
| CRM 业务流程 | `testsuites/crm/test_crm_workflow.py` | 线索→客户→商机→报价→赢单 | ~20 |
| CRM 全量 | `testsuites/crm/test_crm_full.py` | 全量回归测试 | ~30 |
| 数据一致性 | `testsuites/crm/test_data_consistency.py` | 接口间数据一致性验证 | ~15 |
| 跨接口一致性 | `testsuites/crm/test_cross_interface_consistency.py` | 跨模块数据关联验证 | ~15 |
| 月度环比 | `testsuites/crm/test_month_on_month_consistency.py` | 月度统计数据环比 | ~10 |
| 目标一致性 | `testsuites/crm/test_target_consistency.py` | 目标数据一致性 | ~10 |

## 标记（Markers）

```python
# pytest.ini 中定义的标记
smoke:      # 冒烟测试 - 每次构建执行
regression: # 回归测试
crud:       # CRUD 操作测试
full:       # 全量测试
```

使用示例：
```bash
python -m pytest testsuites/ -m smoke -v        # 只跑冒烟
python -m pytest testsuites/ -m "not smoke" -v  # 排除冒烟
```

## 核心 Fixtures

| Fixture | 作用域 | 说明 |
|---------|--------|------|
| `api_base_url` | session | 从 .env 读取 API 基础地址 |
| `test_username` | session | 测试用户名 |
| `test_password` | session | 测试密码 |
| `authorized_headers` | session | 已认证的请求头（含 Token） |
| `crm_client` | session | CRM 客户端实例 |
| `test_data_manager` | session | 测试数据管理器（自动创建/清理数据） |
| `workflow_data` | function | 业务流程共享数据 |

## 测试数据管理

`TestDataManager` 提供自动化测试数据管理：

```python
# 自动创建测试数据
customer = test_data_manager.create_customer()
business = test_data_manager.create_business(customer_id=customer["id"])
quotation = test_data_manager.create_quotation(business_id=business["id"])

# 测试结束后自动清理（通过 cleanup_all_tracked 方法）
```

## 结果查看

```
tests/api/reports/html/report.html      # HTML 可视化报告
tests/api/reports/junit/report.xml      # JUnit XML（CI 集成）
docs/test-runs/{batch}/reports/接口自动化测试报告.md  # 归档报告
docs/test-runs/{batch}/defects/接口缺陷清单.md       # 归档缺陷
```

## 故障排查

| 问题 | 排查方法 |
|------|----------|
| 认证失败 | 检查 .env 中 API_USERNAME/API_PASSWORD 配置 |
| 连接超时 | 验证 API_BASE_URL 可达性：`curl $API_BASE_URL` |
| 401 未授权 | Token 可能过期，删除 `.env` 中缓存的 Token |
| 数据不存在 | 检查 TestDataManager 是否正确创建了前置数据 |

## 与总控脚本集成

```bash
# 方式一：直接执行（推荐日常使用）
python -m pytest testsuites/ -m smoke -v

# 方式二：通过项目总控脚本
pwsh -File ../../scripts/run-api-tests.ps1 -Mode smoke
pwsh -File ../../scripts/run-api-tests.ps1 -Mode full
pwsh -File ../../scripts/run-api-tests.ps1 -Mode failed-retest
```
