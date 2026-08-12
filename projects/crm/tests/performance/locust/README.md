# CRM 性能测试 - Locust

基于 Locust 的 CRM 原型系统性能测试框架，支持 API 压测、业务流程压测和 UI 全链路压测。

## 目录结构

```
locust/
├── api/                           # API 压测脚本
│   ├── locustfile_smoke.py                # API 冒烟压测（高频只读接口）
│   ├── locustfile_crm_api.py              # CRM API 全量压测（所有核心接口）
│   └── locustfile_business_flow.py        # 业务流程压测（赢单/输单完整流程）
├── ui/                            # UI 压测脚本
│   └── locustfile_ui_smoke.py             # UI 冒烟压测脚本
├── utils/                         # 工具模块
│   ├── auth_helper.py                     # 认证辅助工具
│   ├── test_data_loader.py                # 测试数据加载器
│   ├── crm_helpers.py                     # CRM 业务辅助函数（核心）
│   └── report_generator.py                # 报告生成器
├── config/                        # 配置文件
│   └── load_profiles.yaml                 # 负载配置
├── results/                       # 测试结果输出目录
├── requirements.txt               # 依赖清单
└── README.md                      # 本文件
```

## 测试脚本说明

### 1. API 冒烟压测 (`locustfile_smoke.py`)

**用途**: 快速验证系统核心接口可用性

**覆盖接口**:
- 客户列表/详情查询
- 商机列表/详情查询
- 线索列表/详情查询
- 联系人列表/详情查询
- 报价单列表/详情查询
- 公海池查询
- 目标/待办/产品列表查询

**特点**: 只读操作，响应快速，适合 CI/CD 集成

### 2. CRM API 全量压测 (`locustfile_crm_api.py`)

**用途**: 覆盖所有 CRM 核心接口的常规压测

**覆盖接口**:
- 客户 CRUD
- 商机 CRUD
- 线索 CRUD
- 联系人 CRUD
- 报价单 CRUD + 审批
- 公海池查询 + 领取
- 目标/待办/产品管理

**特点**: 混合读写操作，模拟真实使用场景

### 3. 业务流程压测 (`locustfile_business_flow.py`)

**用途**: 模拟完整业务流程的端到端压测

**业务流程**:
```
线索创建 → 线索转客户 → 创建联系人 → 创建商机
→ 推进到方案确认 → 创建报价单 → 审批报价
→ 推进到谈判审核 → 赢单/输单
```

**用户类型**:
| 用户类 | 说明 | 权重 |
|--------|------|------|
| `CRMBusinessFlowUser` | 混合读写，执行业务流程 | 主要 |
| `CRMReadonlyUser` | 高频只读查询 | 辅助 |
| `CRMWriteUser` | 低频写操作 | 辅助 |

**特点**: 覆盖完整业务闭环，自动清理测试数据

### 4. UI 冒烟压测 (`locustfile_ui_smoke.py`)

**用途**: 验证页面加载和交互性能

## 环境搭建

### 1. 安装依赖

```bash
cd tests/performance/locust
pip install -r requirements.txt
```

### 2. 配置环境变量

**方式一：项目根目录 .env 文件（推荐，总控脚本自动加载）**

在项目根目录 `AutoTest Hub/.env` 中配置：

```env
BASE_URL=http://192.168.2.97:6089
API_BASE_URL=http://192.168.2.97:6089/prod-api
TEST_USERNAME=ZhaoShengYao
TEST_PASSWORD=123456
```

**方式二：临时环境变量（Windows PowerShell）**

```powershell
$env:BASE_URL="http://192.168.2.97:6089"
$env:API_BASE_URL="http://192.168.2.97:6089/prod-api"
$env:TEST_USERNAME="ZhaoShengYao"
$env:TEST_PASSWORD="123456"
```

### 3. 验证环境

```powershell
# 验证 Locust 安装
locust --version

# 验证服务连通性
curl http://192.168.2.97:6089/prod-api/api/devices/
```

## 快速开始

性能测试支持三种运行方式，按需选择：

| 方式 | 适用场景 | 入口脚本 |
|------|----------|----------|
| **方式一：分阶段执行**（推荐） | 完整性能评估，逐级加压 | `scripts/run_performance_staged.ps1` |
| **方式二：单独运行某阶段** | 针对性验证某个阶段 | locust 命令直接执行 |
| **方式三：总控脚本** | 集成到完整测试流程 | `scripts/run-full-test-flow.ps1` |

---

### 方式一：分阶段执行（推荐）

使用 `scripts/run_performance_staged.ps1` 一键执行所有阶段，自动逐级加压、评估通过标准、生成综合报告并归档。

```powershell
# 进入性能测试目录
cd d:\AICode\TestDemo\AutoTest-Hub\tests\performance\locust

# 执行全部分阶段（阶段1→阶段6，约 1.5 小时）
.\scripts\run_performance_staged.ps1
```

**执行流程**：
```
阶段1 冒烟 (5用户, 60s) → 评估 → 阶段2 业务流程 (10用户, 5min) → 评估
→ 阶段3 常规压测 (50用户, 5min) → 评估 → 阶段4 只读高压 (100用户, 5min) → 评估
→ 阶段5 压力测试 (200用户, 10min) → 评估 → 阶段6 稳定性测试 (30用户, 1小时)
→ 生成综合报告 → 自动归档到批次目录
```

**执行结果**：
- HTML报告：`results/*.html`
- 综合报告：`results/PERFORMANCE_REPORT_{date}.md`
- 归档目录：`docs/test-runs/{batch}/reports/性能测试报告.md`

---

### 方式二：单独运行某个阶段

如需针对性验证某个阶段，可单独执行对应的 locust 命令。所有命令需在 `tests/performance/locust/` 目录下执行。

#### 阶段1：冒烟测试（5用户，60秒）

```bash
# 用途：快速验证系统核心接口可用性
locust -f api/locustfile_smoke.py \
    --users=5 --spawn-rate=1 --run-time=60s --headless \
    --html=results/smoke_report.html
```

#### 阶段2：业务流程压测（10用户，5分钟）

```bash
# 用途：验证线索→客户→商机→报价→赢单完整业务流程
locust -f api/locustfile_business_flow.py \
    --users=10 --spawn-rate=2 --run-time=300s --headless \
    --html=results/business_flow_report.html
```

#### 阶段3：常规压测（50用户，5分钟）

```bash
# 用途：评估日常负载下的系统性能
locust -f api/locustfile_crm_api.py \
    --users=50 --spawn-rate=5 --run-time=300s --headless \
    --html=results/api_full_report.html
```

#### 阶段4：只读高压（100用户，5分钟）

```bash
# 用途：纯查询场景高频访问，测试只读接口承载能力
locust -f api/locustfile_crm_api.py \
    --users=100 --spawn-rate=10 --run-time=300s --headless \
    --html=results/readonly_heavy_report.html
```

#### 阶段5：压力测试（200用户，10分钟）

```bash
# 用途：寻找系统瓶颈，测试高并发下的稳定性
locust -f api/locustfile_crm_api.py \
    --users=200 --spawn-rate=10 --run-time=600s --headless \
    --html=results/stress_report.html
```

#### 阶段5c/5d/5b：临界点/退化/极限测试（可选）

```bash
# 临界点测试 - 300用户，寻找安全容量上限
locust -f api/locustfile_crm_api.py \
    --users=300 --spawn-rate=15 --run-time=300s --headless \
    --html=results/critical_point_report.html

# 退化测试 - 400用户，验证性能拐点
locust -f api/locustfile_crm_api.py \
    --users=400 --spawn-rate=20 --run-time=300s --headless \
    --html=results/degradation_report.html

# 极限测试 - 500用户，寻找系统崩溃点
locust -f api/locustfile_crm_api.py \
    --users=500 --spawn-rate=20 --run-time=600s --headless \
    --html=results/extreme_test_report.html
```

#### 阶段6：稳定性测试（30用户，1小时）

```bash
# 用途：验证长时间运行的稳定性，检测内存泄漏和性能衰减
locust -f api/locustfile_crm_api.py \
    --users=30 --spawn-rate=2 --run-time=3600s --headless \
    --html=results/stability_report.html
```

⚠️ **注意**：单独运行阶段6后，需手动生成综合报告或运行分阶段脚本触发归档。

---

### 方式三：通过总控脚本执行

将性能测试作为完整测试流程的一部分，由项目总控脚本统一编排。

```powershell
# 在项目根目录执行
cd d:\AICode\TestDemo\AutoTest-Hub

# 方式A：执行完整测试流程（含性能测试）
.\scripts\run-full-test-flow.ps1

# 方式B：只执行性能测试阶段
.\scripts\run-full-test-flow.ps1 -Stages performance

# 方式C：执行到性能测试阶段为止
.\scripts\run-full-test-flow.ps1 -EndStage performance
```

**总控脚本会自动**：
- 加载 `.env` 环境变量
- 调用 `scripts/run-perf-tests.ps1` 执行性能测试
- 归档综合报告到 `docs/test-runs/{batch}/`
- 更新阶段状态和批次摘要

---

### Web UI 模式（调试用）

如需实时查看压测过程，可使用 Web UI 模式：

```bash
# 启动 Web UI
locust -f api/locustfile_crm_api.py

# 浏览器访问 http://localhost:8089
# 在界面中配置：用户数、孵化率、运行时间，点击 Start swarming
```

## 分阶段执行配置

分阶段执行策略定义在 `config/load_profiles.yaml` → `staged_execution`，共 6 个阶段：

| 阶段 | 名称 | 脚本 | 用户 | 时长 | 成功标准 |
|------|------|------|------|------|----------|
| 1 | 冒烟测试 | `locustfile_smoke.py` | 5 | 60s | 错误率<1%, 平均<500ms, RPS≥5 |
| 2 | 业务流程压测 | `locustfile_business_flow.py` | 10 | 300s | 错误率<5%, 平均<1000ms, RPS≥5 |
| 3 | 常规压测 | `locustfile_crm_api.py` | 50 | 300s | 错误率<1%, 平均<500ms, RPS≥50 |
| 4 | 只读高压 | `locustfile_crm_api.py` | 100 | 300s | 错误率<5%, 平均<1000ms, RPS≥200 |
| 5 | 压力测试 | `locustfile_crm_api.py` | 200 | 600s | 错误率<10%, 平均<3000ms, RPS≥300 |
| 6 | 稳定性测试 | `locustfile_crm_api.py` | 30 | 3600s | 错误率<1%, 平均<500ms, RPS≥30 |

**降级策略**：某阶段失败时，按 `fallback_strategy` 配置处理（降级重试/跳过/停止）。

## 结果查看

### 1. 实时监控（Web UI 模式）

启动 Web UI 模式后，访问 `http://localhost:8089` 查看实时指标：

- **RPS**: 每秒请求数（吞吐量）
- **Response Time**: 响应时间（Avg/P50/P95/P99/Max）
- **Error Rate**: 错误率
- **Active Users**: 活跃用户数

### 2. HTML 报告（单次执行）

每次 locust 执行完成后，`--html` 参数指定的 HTML 报告包含：

- 请求统计表（各接口的请求数、失败数、响应时间分位数）
- 响应时间图表
- 吞吐量趋势图

```powershell
# 在浏览器中打开 HTML 报告
start results/stability_report.html
```

### 3. 综合性能测试报告（分阶段执行后）

稳定性测试结束后自动生成，汇总所有阶段结果：

```
文件路径：results/PERFORMANCE_REPORT_{date}.md
归档路径：docs/test-runs/{batch}/reports/性能测试报告.md
```

**必含内容**：
- 分阶段执行汇总表
- 各阶段详细指标分析
- 接口响应时间分布
- 系统性能评估（安全容量/拐点/崩溃点）
- 优化建议（按优先级排序）

### 4. 分阶段执行日志

```powershell
# 查看分阶段执行日志
Get-Content results/staged/staged_execution_log.txt

# 查看 summary_report.json
Get-Content results/staged/summary_report.json | ConvertFrom-Json
```

## 负载配置

参考 `config/load_profiles.yaml`，支持以下预设配置：

| 配置名 | 用户数 | 孵化率 | 持续时间 | 说明 |
|--------|--------|--------|----------|------|
| smoke | 5 | 1/s | 60s | 冒烟测试 |
| normal | 50 | 5/s | 300s | 常规压测 |
| stress | 200 | 10/s | 600s | 压力测试 |
| soak | 30 | 2/s | 3600s | 稳定性测试 |
| business_flow_smoke | 3 | 1/s | 60s | 业务流程冒烟 |
| business_flow_normal | 10 | 2/s | 300s | 业务流程常规 |
| readonly_heavy | 100 | 10/s | 300s | 只读高压 |
| write_mixed | 20 | 4/s | 300s | 读写混合 |

## 综合报告生成与归档规则

**强制规则**: 稳定性测试（soak/stage6）结束后，必须汇总生成一份综合性能测试报告，并同步归档到当前测试批次目录。

配置位置：`config/load_profiles.yaml` → `report_generation`

### 触发条件
- 主触发：稳定性测试（stage6_soak）执行完成后
- 执行脚本：`scripts/run_performance_staged.ps1` 会自动检测并触发
  - 自动调用 `New-ComprehensiveReport` 生成报告
  - 自动调用 `Archive-ComprehensiveReport` 归档到批次目录

### 总控脚本集成
- 项目总控脚本 `scripts/run-full-test-flow.ps1` → `scripts/run-perf-tests.ps1`
- `run-perf-tests.ps1` 内置 `Archive-ComprehensiveReportIfExist` 函数
- 执行完成（通过/失败）后自动检查 `tests/performance/locust/results/` 下是否存在综合报告
- 若存在则自动归档到当前批次目录，覆盖简化报告

### 报告要求

| 项目 | 要求 |
|------|------|
| 文件路径 | `results/PERFORMANCE_REPORT_{date}.md` |
| 更新方式 | 增量更新（若已存在则更新，不重复创建） |
| 数据来源 | 各阶段HTML报告、执行日志、summary_report.json |

### 必含章节（按顺序）
1. **一、分阶段执行汇总** - 所有阶段核心指标汇总表
2. **二、详细指标分析** - 各阶段详细指标和通过标准评估
3. **三、接口响应时间分布** - TOP慢接口、接口稳定性明细
4. **四、系统性能评估** - 优势、瓶颈、性能结论、系统容量评估
5. **五、后续建议** - 优化建议（按P0/P1/P2优先级排序）
6. **六、测试命令记录** - 可复现的执行命令

### 必含核心结论
- ✅ 系统安全容量（并发用户数上限）
- ✅ 性能拐点/退化区间
- ✅ 系统崩溃点
- ✅ 稳定性评估（长时间运行是否退化）
- ✅ 优化建议（按优先级排序）

### 归档规则

综合报告生成后，必须同步归档到当前测试批次目录 `docs/test-runs/YYYYMMDD-HHMMSS/`，与 API/UI/安全 报告保持统一归档结构。

| 归档项 | 源路径 | 目标路径 | 说明 |
|--------|--------|----------|------|
| 综合报告 | `results/PERFORMANCE_REPORT_{date}.md` | `docs/test-runs/{batch}/reports/性能测试报告.md` | 重命名为中文，符合项目规范 |
| HTML报告 | `results/*.html` | `docs/test-runs/{batch}/raw/performance/` | 各阶段原始HTML报告 |
| 分阶段日志 | `results/staged/*` | `docs/test-runs/{batch}/raw/performance/staged/` | 执行日志和summary_report.json |

#### 归档目录结构示例

```
docs/test-runs/20260729-091531/
├── reports/
│   ├── 系统测试报告.md
│   ├── API测试报告.md
│   ├── UI测试报告.md
│   ├── 安全测试报告.md
│   └── 性能测试报告.md          ← 综合性能测试报告归档于此
├── defects/
├── raw/
│   └── performance/              ← 性能测试原始结果归档目录
│       ├── stability_report_20260730.html
│       ├── api_full_report_20260730.html
│       ├── smoke_report_20260730.html
│       ├── business_flow_report_20260730.html
│       └── staged/
│           ├── summary_report.json
│           └── *.log
├── stage-status/
└── 批次摘要.md
```

#### 归档时机
- 综合报告生成后**立即归档**
- 同批次重复执行时**覆盖旧文件**
- 若批次目录不存在则**跳过归档并记录警告**

## 核心辅助函数 (`crm_helpers.py`)

### 业务流程函数

| 函数 | 说明 |
|------|------|
| `create_test_clue(client, name)` | 创建测试线索 |
| `transform_clue_to_customer(client, clue_id)` | 线索转客户 |
| `create_test_contact(client, customer_id)` | 创建联系人 |
| `create_test_business(client, customer_id)` | 创建商机 |
| `advance_business_stage(client, business_id, stage)` | 推进商机阶段 |
| `create_test_quotation(client, business_id)` | 创建报价单 |
| `approve_quotation(client, quotation_id)` | 审批报价单 |
| `win_business(client, business_id, deal_amount)` | 赢单 |
| `lose_business(client, business_id, lost_reason)` | 输单 |
| `get_public_pool_list(client)` | 查询公海池 |
| `claim_from_pool(client, customer_id)` | 领取公海池客户 |

### 工具函数

| 函数 | 说明 |
|------|------|
| `generate_name(type)` | 生成唯一测试名称 |
| `track_resource(type, id, name)` | 跟踪创建的资源（用于清理） |
| `cleanup_all_tracked(client)` | 清理所有跟踪的资源 |
| `safe_get(response, path)` | 安全获取响应数据 |
| `assert_api_success(response, context)` | 断言 API 调用成功 |
| `get_valid_id(client, type)` | 获取有效业务 ID |

## 最佳实践

1. **首次运行**: 先执行冒烟压测确认系统可用
2. **逐步加压**: 从 5 用户开始，逐步增加到目标用户数
3. **数据隔离**: 测试数据会自动标记和清理
4. **避免高峰**: 建议在非工作时间执行压力测试
5. **监控系统**: 压测时同步监控服务端 CPU、内存、数据库连接数

## 注意事项

1. 所有压测脚本会在 `on_stop` 时自动清理创建的测试数据
2. Token 会在 `on_start` 时获取，压测期间保持有效
3. 写操作权重较低，主要用于验证流程正确性
4. 如遇 Token 过期（长时间压测），需手动更新或重启
5. UI 压测资源消耗较高，建议从 5 并发开始

## 扩展示例

### 添加新的 API 压测任务

```python
# 在 locustfile 中添加
@task(weight)
def new_api_task(self):
    """新接口压测"""
    self.client.get("/crm/new-endpoint")
```

### 添加新的业务流程

```python
# 使用 crm_helpers 中的函数
from utils.crm_helpers import create_test_clue, track_resource

@task(1)
def custom_flow(self):
    clue = create_test_clue(self.client)
    if clue:
        # 执行业务逻辑
        pass
```