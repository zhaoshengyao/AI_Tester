# AutoTest Hub Linux 测试执行操作说明

> **版本**: v1.0  
> **更新日期**: 2026-07-31  
> **适用环境**: Linux 服务器 (openEuler / CentOS / Ubuntu)

---

## 目录

- [1. 前置准备](#1-前置准备)
- [2. API 测试](#2-api-测试)
- [3. UI 测试](#3-ui-测试)
- [4. 性能测试](#4-性能测试)
- [5. 安全测试](#5-安全测试)
- [6. 全链路测试](#6-全链路测试)
- [7. 全流程执行](#7-全流程执行)
- [8. 报告查看与归档](#8-报告查看与归档)
- [9. 常见问题排查](#9-常见问题排查)
- [附录：命令速查表](#附录命令速查表)

---

## 1. 前置准备

### 1.1 连接服务器

```bash
# SSH 连接
ssh root@192.168.2.70

# 进入项目目录
cd /home/zhiwei/AutoTestHub
```

### 1.2 环境验证

```bash
# 检查 Python
python3 --version
# 预期: Python 3.9.9 或更高

# 检查 Node.js
node --version
# 预期: v20.11.0 或更高

# 检查核心工具
python3 -m pytest --version      # 预期: pytest 8.4.2
python3 -m locust --version      # 预期: locust 2.34.0
npx playwright --version         # 预期: 1.62.1
```

### 1.3 代码同步

```bash
# 拉取最新代码
cd /home/zhiwei/AutoTestHub
git pull

# 如果有冲突
git stash
git pull
git stash pop
```

### 1.4 环境变量

```bash
# 检查 .env 文件
cat /home/zhiwei/AutoTestHub/.env

# 如果不存在，创建默认配置
cat > /home/zhiwei/AutoTestHub/.env << 'EOF'
# 测试环境配置
BASE_URL=http://192.168.2.97:6089
API_BASE_URL=http://192.168.2.97:6089/prod-api

# 认证凭证
API_USERNAME=ZhaoShengYao
API_PASSWORD=V+GwtuX+DsY4rxGNZ9hZSg==
API_CLIENT_ID=e5cd7e4891bf95d1d19206ce24a7b32e
EOF
```

### 1.5 首次初始化

如果是首次部署，执行初始化脚本：

```bash
cd /home/zhiwei/AutoTestHub
chmod +x scripts/setup-linux.sh
./scripts/setup-linux.sh
```

---

## 2. API 测试

### 2.1 快速执行

#### 冒烟测试（推荐首次执行）

```bash
cd /home/zhiwei/AutoTestHub
./scripts/run-api-tests.sh smoke
```

**输出示例**：
```
===========================================
API 冒烟测试
===========================================
testsuites/crm/test_crm_crud.py::TestCustomerCRUD::test_read_customer_list PASSED
testsuites/crm/test_crm_api.py::test_get_customer_list PASSED
...
================ 14 passed, 0 failed in 0.87s =================

[OK] API 测试全部通过 ✅
[INFO] HTML 报告: tests/api/reports/html/report.html
[INFO] JUnit 报告: tests/api/reports/junit/report.xml
```

#### 全量测试

```bash
cd /home/zhiwei/AutoTestHub
./scripts/run-api-tests.sh full
```

### 2.2 手动执行

#### 基本执行

```bash
# 进入 API 测试目录
cd /home/zhiwei/AutoTestHub/tests/api

# 执行所有测试
python3 -m pytest testsuites/ -v

# 执行指定文件
python3 -m pytest testsuites/crm/test_crm_crud.py -v

# 执行指定测试类
python3 -m pytest testsuites/crm/test_crm_crud.py::TestCustomerCRUD -v

# 执行指定测试方法
python3 -m pytest testsuites/crm/test_crm_crud.py::TestCustomerCRUD::test_create_customer_success -v

# 关键字过滤
python3 -m pytest testsuites/ -k "customer" -v
python3 -m pytest testsuites/ -k "smoke" -v
```

#### 分层执行

```bash
# 冒烟层：核心接口可达性
python3 -m pytest testsuites/ -m "smoke" -v

# 回归层：只读操作
python3 -m pytest testsuites/ -m "regression" -v

# CRUD 层：增删改查
python3 -m pytest testsuites/ -m "crud" -v

# 全量层：所有用例
python3 -m pytest testsuites/ -m "full" -v
```

#### 报告生成

```bash
# 默认报告路径（已在 pytest.ini 配置）
python3 -m pytest testsuites/ -v
# 报告输出:
#   tests/api/reports/html/report.html
#   tests/api/reports/junit/report.xml

# 自定义报告路径
python3 -m pytest testsuites/ -v \
  --html=reports/html/custom_report.html \
  --junitxml=reports/junit/custom_report.xml \
  --self-contained-html

# 生成到批次目录
BATCH_DIR=../../docs/test-runs/$(date +%Y%m%d-%H%M%S)/reports
mkdir -p $BATCH_DIR
python3 -m pytest testsuites/ -v \
  --html=$BATCH_DIR/API测试报告.html \
  --junitxml=$BATCH_DIR/junit-report.xml
```

### 2.3 常用参数

```bash
# 超时设置
python3 -m pytest testsuites/ --timeout=30 -v

# 并发执行（需要 pytest-xdist）
python3 -m pytest testsuites/ -n auto -v

# 详细输出
python3 -m pytest testsuites/ -vv --tb=long

# 静默成功输出
python3 -m pytest testsuites/ -q

# 仅运行失败的用例
python3 -m pytest testsuites/ --lf -v

# 跳过某些测试
python3 -m pytest testsuites/ --ignore=testsuites/performance -v
```

### 2.4 测试套件列表

| 文件 | 说明 | 用例数 |
|------|------|--------|
| `testsuites/crm/test_crm_crud.py` | 客户增删改查 | 10 |
| `testsuites/crm/test_crm_api.py` | 基础接口测试 | 8 |
| `testsuites/crm/test_crm_business.py` | 商机管理 | 12 |
| `testsuites/crm/test_crm_workflow.py` | 业务流程 | 6 |
| `testsuites/crm/test_crm_full.py` | 全流程测试 | 4 |
| `testsuites/crm/test_data_consistency.py` | 数据一致性 | 5 |
| `testsuites/crm/test_cross_interface_consistency.py` | 跨接口一致性 | 4 |
| `testsuites/crm/test_month_on_month_consistency.py` | 月度一致性 | 3 |
| `testsuites/crm/test_target_consistency.py` | 目标一致性 | 3 |

---

## 3. UI 测试

> ⚠️ **重要**: UI 测试依赖 Playwright 浏览器，而 Playwright 需要系统级图形库支持。如果遇到 `libgbm.so.1` 或其他 `.so` 文件找不到的错误，请先安装系统依赖。

### 3.1 前置条件

#### 安装系统依赖（首次必须执行）

```bash
# openEuler/CentOS 系统
yum install -y mesa-libgbm mesa-libgbm-devel

# Ubuntu/Debian 系统
apt-get install -y libgbm1 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libpango-1.0-0 libasound2

# 验证依赖已安装
ldconfig -p | grep libgbm
# 预期输出: libgbm.so.1 (libc6,x86-64) => /usr/lib64/libgbm.so.1
```

#### 安装 Playwright 浏览器

```bash
cd /home/zhiwei/AutoTestHub/tests/ui
npx playwright install chromium

# 如果安装过，检查版本
npx playwright --version
# 预期输出: 1.62.1
```

#### 完整初始化（推荐）

```bash
# 使用封装脚本自动检查和安装所有依赖
cd /home/zhiwei/AutoTestHub
./scripts/run-ui-tests.sh smoke
# 此脚本会自动检查并安装缺失的系统依赖
```

### 3.2 快速执行

#### 冒烟测试

```bash
cd /home/zhiwei/AutoTestHub
./scripts/run-ui-tests.sh smoke
```

#### 全量测试

```bash
cd /home/zhiwei/AutoTestHub
./scripts/run-ui-tests.sh
```

### 3.3 手动执行

#### 基本执行

```bash
# 进入 UI 测试目录
cd /home/zhiwei/AutoTestHub/tests/ui

# 执行所有测试
npx playwright test

# 执行 CRM 模块测试
npx playwright test specs/crm/

# 执行指定文件
npx playwright test specs/crm/crm-crud.spec.ts
npx playwright test specs/crm/business-process.spec.ts

# 执行冒烟测试
npx playwright test specs/crm/crm-smoke.spec.ts

# 关键字过滤
npx playwright test -g "login"
npx playwright test -g "customer"
```

#### 浏览器选择

```bash
# Chromium（默认）
npx playwright test --project=chromium

# Firefox
npx playwright test --project=firefox

# WebKit (Safari)
npx playwright test --project=webkit

# 同时执行多个浏览器
npx playwright test --project=chromium --project=firefox
```

#### 执行模式

```bash
# 有头模式（显示浏览器窗口）
npx playwright test --headed

# 无头模式（默认，服务器推荐）
npx playwright test --headless

# 调试模式
npx playwright test --debug

# 并发执行
npx playwright test --workers=4

# 单线程执行
npx playwright test --workers=1
```

#### 报告生成

```bash
# HTML 报告
npx playwright test --reporter=html
# 报告路径: tests/ui/playwright-report/index.html

# 多格式报告
npx playwright test --reporter=html,junit
# 报告路径:
#   tests/ui/playwright-report/index.html
#   tests/ui/test-results.xml

# 自定义报告路径
npx playwright test \
  --reporter=html \
  --output=../../docs/test-runs/latest/reports/ui-report

# 截图保存
npx playwright test \
  --screenshot=on \
  --video=retain-on-failure
```

### 3.4 UI 测试用例列表

| 文件 | 说明 | 用例数 |
|------|------|--------|
| `specs/login.spec.ts` | 登录功能 | 5 |
| `specs/dashboard.spec.ts` | 首页仪表盘 | 3 |
| `specs/customer.spec.ts` | 客户管理 | 6 |
| `specs/clue.spec.ts` | 线索管理 | 4 |
| `specs/business.spec.ts` | 商机管理 | 5 |

---

## 4. 性能测试

### 4.1 前置条件

```bash
# 确保 Locust 已安装
python3 -m locust --version

# 如果未安装
pip3 install locust
```

### 4.2 快速执行

#### 冒烟测试（5 用户，1 分钟）

```bash
cd /home/zhiwei/AutoTestHub
./scripts/run-perf-tests.sh smoke
```

**输出示例**：
```
===========================================
性能冒烟测试 (5 用户, 1 分钟)
===========================================
[INFO] 目标: http://192.168.2.97:6089
[INFO] 并发用户: 5
[INFO] 爬升率: 1 user/s
[INFO] 持续时间: 1m

Name                          # Users  # Requests  # Fails  Avg   Min   Max   Med   Failures/s
--------------------------------------------------------------------------------------------
GET /crm/customer/list          5        150        0       45ms  12ms  120ms  38ms  0.00
GET /crm/clue/list              5        145        0       52ms  15ms  135ms  44ms  0.00
--------------------------------------------------------------------------------------------
Aggregated                      5        295        0       48ms  12ms  135ms  40ms  0.00

[OK] 冒烟测试通过 ✅
[INFO] 平均响应时间: 48ms
[INFO] 错误率: 0%
[INFO] 吞吐量: 295 req/min
```

#### 常规压测（50 用户，5 分钟）

```bash
cd /home/zhiwei/AutoTestHub
./scripts/run-perf-tests.sh regular
```

#### 压力测试（200 用户，10 分钟）

```bash
cd /home/zhiwei/AutoTestHub
./scripts/run-perf-tests.sh stress
```

#### 稳定性测试（100 用户，30 分钟）

```bash
cd /home/zhiwei/AutoTestHub
./scripts/run-perf-tests.sh stability
```

### 4.3 手动执行

#### 基本执行

```bash
# 进入性能测试目录
cd /home/zhiwei/AutoTestHub/tests/performance/locust

# 冒烟测试
python3 -m locust -f api/locustfile_smoke.py \
  --headless -u 5 -r 1 -t 1m

# 常规压测
python3 -m locust -f api/locustfile_crm_api.py \
  --headless -u 50 -r 5 -t 5m

# 压力测试
python3 -m locust -f api/locustfile_crm_api.py \
  --headless -u 200 -r 10 -t 10m

# 极限测试
python3 -m locust -f api/locustfile_crm_api.py \
  --headless -u 500 -r 20 -t 15m
```

#### Locustfile 列表

| 文件 | 说明 | 适用场景 |
|------|------|----------|
| `api/locustfile_smoke.py` | 冒烟测试 | 验证基础性能 |
| `api/locustfile_crm_api.py` | CRM API 测试 | 核心接口压测 |
| `api/locustfile_readonly.py` | 只读接口测试 | 查询类接口压测 |
| `api/locustfile_write.py` | 写操作测试 | 创建/更新/删除压测 |

#### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `-f` | Locustfile 路径 | `api/locustfile_crm_api.py` |
| `--headless` | 无头模式（无 UI） | `-` |
| `-u` | 总用户数 | `50` |
| `-r` | 每秒启动用户数 | `5` |
| `-t` | 持续时间 | `5m` |
| `-H` | 目标主机 | `http://192.168.2.97:6089` |
| `--html` | HTML 报告路径 | `reports/perf.html` |
| `--csv` | CSV 报告前缀 | `reports/perf` |

#### 自定义配置

```bash
# 使用配置文件
python3 -m locust -f api/locustfile_crm_api.py \
  --config config/default.conf \
  --headless

# 分步加压
python3 -m locust -f api/locustfile_crm_api.py \
  --headless -u 10 -r 2 -t 2m \
  --step-users 10 --step-time 10s

# 指定 API 地址
API_URL=http://192.168.2.97:6089/prod-api \
  python3 -m locust -f api/locustfile_crm_api.py --headless
```

### 4.4 性能指标解读

| 指标 | 说明 | 目标值 |
|------|------|--------|
| **Avg Response Time** | 平均响应时间 | < 500ms |
| **P95 Response Time** | 95 分位响应时间 | < 1000ms |
| **P99 Response Time** | 99 分位响应时间 | < 2000ms |
| **RPS (Requests/sec)** | 每秒请求数 | 根据业务需求 |
| **Error Rate** | 错误率 | < 1% |
| **Failures/s** | 每秒失败数 | 0 |

### 4.5 报告生成

```bash
# HTML 报告
python3 -m locust -f api/locustfile_crm_api.py \
  --headless -u 50 -r 5 -t 5m \
  --html reports/perf_report.html

# CSV 报告（多个文件）
python3 -m locust -f api/locustfile_crm_api.py \
  --headless -u 50 -r 5 -t 5m \
  --csv reports/perf

# 生成的文件:
#   reports/perf_stats.csv      # 统计数据
#   reports/perf_stats_failures.csv  # 失败统计
#   reports/perf_users.csv      # 用户数变化
```

---

## 5. 安全测试

### 5.1 快速执行

```bash
cd /home/zhiwei/AutoTestHub
./scripts/run-security-tests.sh
```

### 5.2 手动执行

```bash
# 进入安全测试目录
cd /home/zhiwei/AutoTestHub/tests/security

# 执行完整扫描
python3 -m scanner.main --target http://192.168.2.97:6089

# 指定扫描范围
python3 -m scanner.main \
  --target http://192.168.2.97:6089 \
  --scope "/prod-api/crm/*"

# 深度扫描
python3 -m scanner.main \
  --target http://192.168.2.97:6089 \
  --deep \
  --threads 10

# 生成报告
python3 -m scanner.main \
  --target http://192.168.2.97:6089 \
  --report reports/security_report.html \
  --format html
```

### 5.3 扫描类型

| 扫描类型 | 说明 | 命令 |
|----------|------|------|
| **认证测试** | 检查未授权访问 | `--test auth` |
| **注入测试** | SQL 注入、XSS 等 | `--test injection` |
| **越权测试** | 水平/垂直越权 | `--test privilege` |
| **敏感信息** | 信息泄露检查 | `--test info-leak` |
| **配置检查** | 安全配置审计 | `--test config` |
| **完整扫描** | 以上所有 | `--test all` |

### 5.4 报告生成

```bash
# HTML 报告
python3 -m scanner.main --target URL --report security_report.html

# JSON 报告（方便二次处理）
python3 -m scanner.main --target URL --report security_report.json --format json

# 报告内容:
#   - 漏洞列表
#   - 风险等级 (Critical/High/Medium/Low)
#   - 复现步骤
#   - 修复建议
```

---

## 6. 全链路测试

### 6.1 什么是全链路测试

全链路测试是 **端到端（E2E）** 的业务流程验证，贯穿从前端 UI 到后端 API 的完整业务闭环，验证数据在各个环节的流转正确性。

**CRM 全链路业务流程**：
```
线索创建 → 线索转客户 → 客户公海池领取 → 创建商机 → 推进阶段 
→ 创建报价单 → 提交审批 → 审批通过 → 赢单/输单
```

### 6.2 快速执行

```bash
cd /home/zhiwei/AutoTestHub

# 执行业务流程全链路测试
./scripts/run-api-tests.sh full

# 全链路专项测试（包含业务流程验证）
cd tests/api
python3 -m pytest testsuites/crm/test_crm_workflow.py -v --timeout=60
python3 -m pytest testsuites/crm/test_crm_full.py -v --timeout=120
```

### 6.3 业务流程链路测试

#### 完整业务流程

```bash
cd /home/zhiwei/AutoTestHub/tests/api

# 执行完整 CRM 业务链路测试
python3 -m pytest testsuites/crm/test_crm_full.py -v --timeout=120

# 测试覆盖:
# 1. 创建线索
# 2. 线索转客户
# 3. 客户公海池领取
# 4. 创建联系人
# 5. 创建商机（验证客户阶段）
# 6. 推进到方案确认阶段
# 7. 创建报价单
# 8. 审批通过报价单
# 9. 推进到谈判审核阶段
# 10. 赢单（设置成交金额）
# 11. 全流程数据验证
```

#### 业务流程推进测试

```bash
# 商机阶段推进链路
python3 -m pytest testsuites/crm/test_crm_business.py::TestBusinessStageTransition -v --timeout=30

# 测试覆盖:
# 验证客户 → 方案确认 → 谈判审核 → 赢单/输单
```

### 6.4 API + UI 联合联调

#### 方式一：API 造数据 + UI 验证

```bash
# Step 1: 通过 API 准备测试数据
cd /home/zhiwei/AutoTestHub/tests/api
python3 -m pytest testsuites/crm/test_crm_crud.py::TestCustomerCRUD::test_create_customer_success -v

# Step 2: 通过 UI 验证数据可见性
cd /home/zhiwei/AutoTestHub/tests/ui
npx playwright test specs/customer.spec.ts -g "customer list"

# Step 3: API 验证 UI 操作结果
cd /home/zhiwei/AutoTestHub/tests/api
python3 -m pytest testsuites/crm/test_crm_crud.py::TestCustomerCRUD::test_read_customer_list -v
```

#### 方式二：UI 全流程操作

```bash
# 完整 UI 业务流程测试
cd /home/zhiwei/AutoTestHub/tests/ui
npx playwright test specs/customer.spec.ts
npx playwright test specs/clue.spec.ts
npx playwright test specs/business.spec.ts
```

#### 方式三：自动化联调脚本

```bash
# 使用封装的联调脚本
cd /home/zhiwei/AutoTestHub

# API 造数据 + UI 验证
./scripts/run-e2e-tests.sh workflow

# 全栈联调（API + UI + 数据一致性）
./scripts/run-e2e-tests.sh full
```

### 6.5 数据一致性链路验证

#### 跨接口数据一致性

```bash
cd /home/zhiwei/AutoTestHub/tests/api

# 客户数据一致性（列表 vs 详情）
python3 -m pytest testsuites/crm/test_data_consistency.py -v --timeout=30

# 月度数据一致性
python3 -m pytest testsuites/crm/test_month_on_month_consistency.py -v --timeout=30

# 目标数据一致性
python3 -m pytest testsuites/crm/test_target_consistency.py -v --timeout=30

# 跨接口一致性（创建→查询→更新→删除）
python3 -m pytest testsuites/crm/test_cross_interface_consistency.py -v --timeout=30
```

#### 业务流程数据回溯

```bash
# 商机数据回溯验证
python3 -m pytest testsuites/crm/test_crm_business.py::TestBusinessCRUD -v --timeout=30

# 报价单与商机关联验证
python3 -m pytest testsuites/crm/test_crm_business.py -k "quotation" -v --timeout=30
```

### 6.6 分层全链路执行

#### 第一层：API 全链路（核心）

```bash
cd /home/zhiwei/AutoTestHub

# API 全量测试（包含业务流程）
./scripts/run-api-tests.sh full

# 执行内容:
#   ✅ CRUD 基础操作
#   ✅ 业务流程链路
#   ✅ 数据一致性
#   ✅ 接口契约验证
```

#### 第二层：UI 全链路（界面）

```bash
# UI 全量测试
./scripts/run-ui-tests.sh

# 执行内容:
#   ✅ 页面可达性
#   ✅ 表单操作
#   ✅ 流程页面跳转
#   ✅ 数据展示正确性
```

#### 第三层：API + UI 联合（端到端）

```bash
# 先执行 API 造数据
./scripts/run-api-tests.sh full

# 再执行 UI 验证
./scripts/run-ui-tests.sh

# 最后数据一致性验证
cd tests/api && python3 -m pytest testsuites/crm/test_data_consistency.py -v
```

#### 第四层：全栈压测（性能链路）

```bash
# 常规压测
./scripts/run-perf-tests.sh regular

# 压力测试
./scripts/run-perf-tests.sh stress

# 稳定性测试
./scripts/run-perf-tests.sh stability
```

### 6.7 全链路测试清单

| 序号 | 链路名称 | 测试内容 | 执行命令 |
|------|----------|----------|----------|
| 1 | 线索管理链路 | 创建、编辑、分配、删除 | `pytest testsuites/crm/test_crm_api.py` |
| 2 | 线索转客户链路 | 线索→客户转化 | `pytest testsuites/crm/test_crm_workflow.py` |
| 3 | 公海池链路 | 公海池查询、领取、释放 | `pytest -k "pool"` |
| 4 | 客户 CRUD 链路 | 创建、查询、更新、删除 | `pytest testsuites/crm/test_crm_crud.py` |
| 5 | 商机推进链路 | 验证客户→方案确认→谈判审核→赢单 | `pytest TestBusinessStageTransition` |
| 6 | 报价审批链路 | 创建报价→审批→关联商机 | `pytest -k "quotation"` |
| 7 | 赢单链路 | 成交金额、成交日期、负责人 | `pytest -k "win"` |
| 8 | 输单链路 | 输单原因、损失金额 | `pytest -k "lost"` |
| 9 | 数据一致性链路 | 跨接口、跨时段数据校验 | `pytest test_data_consistency.py` |
| 10 | UI 操作链路 | 页面跳转、表单填写、数据展示 | `npx playwright test` |

### 6.8 全链路报告生成

```bash
# 生成全链路测试报告
cd /home/zhiwei/AutoTestHub

# 执行全链路测试并生成报告
BATCH_DIR=docs/test-runs/$(date +%Y%m%d-%H%M%S)/reports
mkdir -p $BATCH_DIR

# 1. API 全链路报告
cd tests/api
python3 -m pytest testsuites/ -v \
  --html=../../$BATCH_DIR/API全链路测试报告.html \
  --junitxml=../../$BATCH_DIR/api-junit.xml \
  --self-contained-html

# 2. UI 全链路报告
cd ../../tests/ui
npx playwright test \
  --reporter=html \
  --output=../../$BATCH_DIR/UI全链路测试报告

# 3. 汇总报告
cat > ../../$BATCH_DIR/全链路测试总结.md << 'EOF'
# 全链路测试报告

## 执行时间
$(date '+%Y-%m-%d %H:%M:%S')

## 测试范围
- [x] 线索管理链路
- [x] 线索转客户链路
- [x] 公海池链路
- [x] 客户 CRUD 链路
- [x] 商机推进链路
- [x] 报价审批链路
- [x] 赢单/输单链路
- [x] 数据一致性链路
- [x] UI 操作链路

## 报告索引
- API 报告: [API全链路测试报告.html](./API全链路测试报告.html)
- UI 报告: [UI全链路测试报告/index.html](./UI全链路测试报告/index.html)

## 结论
✅ 全链路测试通过
EOF
```

---

## 7. 全流程执行

### 7.1 一键执行

```bash
cd /home/zhiwei/AutoTestHub
./scripts/run-full-test-flow.sh
```

**执行顺序**：
1. API 冒烟测试
2. API 全量测试（含全链路）
3. UI 冒烟测试
4. UI 全量测试（含全链路）
5. 性能冒烟测试
6. 性能常规测试
7. 安全扫描
8. 生成系统测试报告

### 7.2 分阶段执行

```bash
# 第一阶段：冒烟测试（验证基础连通性）
cd /home/zhiwei/AutoTestHub
./scripts/run-api-tests.sh smoke
./scripts/run-ui-tests.sh smoke
./scripts/run-perf-tests.sh smoke

# 第二阶段：全链路测试（验证业务闭环）
./scripts/run-api-tests.sh full
./scripts/run-ui-tests.sh

# 第三阶段：性能专项（验证系统容量）
./scripts/run-perf-tests.sh regular
./scripts/run-perf-tests.sh stress

# 第四阶段：安全专项（验证安全基线）
./scripts/run-security-tests.sh

# 第五阶段：生成综合报告
./scripts/run-system-report.sh
```

### 7.3 选择性执行

```bash
# 只执行全链路（API + UI）
./scripts/run-api-tests.sh full && ./scripts/run-ui-tests.sh

# 只执行冒烟 + 全链路
./scripts/run-api-tests.sh smoke && ./scripts/run-api-tests.sh full

# 跳过 UI（无浏览器环境）
./scripts/run-api-tests.sh full && ./scripts/run-perf-tests.sh regular && ./scripts/run-security-tests.sh

# 只执行数据一致性验证
cd tests/api && python3 -m pytest testsuites/crm/test_data_consistency.py -v
```

### 7.4 后台执行

```bash
# 使用 nohup 后台执行全流程
nohup ./scripts/run-full-test-flow.sh > test_output.log 2>&1 &

# 查看执行状态
tail -f test_output.log

# 查看进程
ps aux | grep test

# 查看已生成报告
find docs/test-runs -name "*.md" -newer test_output.log | head -10
```

---

## 8. 报告查看与归档

### 8.1 报告位置

| 报告类型 | 路径 | 格式 |
|----------|------|------|
| API HTML 报告 | `tests/api/reports/html/report.html` | HTML |
| API JUnit 报告 | `tests/api/reports/junit/report.xml` | XML |
| UI HTML 报告 | `tests/ui/playwright-report/index.html` | HTML |
| 性能 HTML 报告 | `tests/performance/locust/reports/*.html` | HTML |
| 安全报告 | `tests/security/reports/*` | HTML/JSON |
| 系统测试报告 | `docs/test-runs/latest/reports/` | Markdown |

### 8.2 查看报告

```bash
# 在服务器上查看
cat docs/test-runs/latest/reports/API测试报告.md
cat docs/test-runs/latest/reports/UI测试报告.md
cat docs/test-runs/latest/reports/性能测试报告.md
cat docs/test-runs/latest/reports/安全测试报告.md
cat docs/test-runs/latest/reports/系统测试报告.md

# 列出所有报告
find docs/test-runs -name "*.md" -o -name "*.html" | sort
```

### 8.3 报告回传

```bash
# 从服务器复制到本地
# 在 Windows PowerShell 中执行:

# 复制单个报告
scp root@192.168.2.70:/home/zhiwei/AutoTestHub/docs/test-runs/latest/reports/API测试报告.md ./reports/

# 复制整个批次
scp -r root@192.168.2.70:/home/zhiwei/AutoTestHub/docs/test-runs/20260731-120000/ ./reports/

# 复制 HTML 报告
scp root@192.168.2.70:/home/zhiwei/AutoTestHub/tests/api/reports/html/report.html ./reports/api.html
scp root@192.168.2.70:/home/zhiwei/AutoTestHub/tests/ui/playwright-report/index.html ./reports/ui.html
```

### 8.4 批次归档

```bash
# 查看所有批次
ls -la docs/test-runs/

# 查看特定批次
cat docs/test-runs/20260731-120000/批次摘要.md

# 清理历史批次（保留最近 5 个）
cd docs/test-runs && ls -d */ | head -n -5 | xargs rm -rf
```

---

## 9. 常见问题排查

### 9.1 API 测试问题

#### Q1: 认证失败 (401 Unauthorized)

```bash
# 检查 .env 文件
cat /home/zhiwei/AutoTestHub/.env

# 手动测试认证
curl -X POST http://192.168.2.97:6089/prod-api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"ZhaoShengYao","password":"V+GwtuX+DsY4rxGNZ9hZSg=="}'

# 如果密码错误，更新 .env
```

#### Q2: 连接超时

```bash
# 检查网络
ping 192.168.2.97

# 检查端口
telnet 192.168.2.97 6089

# 检查防火墙
iptables -L -n | grep 6089
```

#### Q3: 报告未生成

```bash
# 检查 pytest.ini 配置
cat /home/zhiwei/AutoTestHub/tests/api/pytest.ini
# 确认包含 addopts 行

# 手动指定报告参数
cd tests/api
python3 -m pytest testsuites/ -v \
  --html=reports/html/test.html \
  --junitxml=reports/junit/test.xml

# 检查目录权限
ls -la reports/html/
ls -la reports/junit/
```

### 9.2 UI 测试问题

#### Q4: 浏览器无法启动 / libgbm.so.1 找不到

**这是最常见的问题！** Playwright 依赖系统图形库，需要手动安装。

```bash
# 错误信息: error while loading shared libraries: libgbm.so.1

# openEuler/CentOS 解决方案
yum install -y mesa-libgbm mesa-libgbm-devel

# Ubuntu/Debian 解决方案
apt-get install -y libgbm1 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libpango-1.0-0 libasound2

# 验证安装
ldconfig -p | grep libgbm
# 预期输出: libgbm.so.1 (libc6,x86-64) => /usr/lib64/libgbm.so.1

# 安装后重新运行
cd /home/zhiwei/AutoTestHub
./scripts/run-ui-tests.sh smoke
```

#### Q5: 其他系统库缺失

```bash
# 检查所有缺失的库
CHROME_PATH=$(find /root/.cache/ms-playwright -name 'chrome-headless-shell' -type f 2>/dev/null | head -1)
if [ -n "$CHROME_PATH" ]; then
  ldd "$CHROME_PATH" 2>&1 | grep "not found"
fi

# 一次性安装所有依赖
# openEuler/CentOS
yum install -y mesa-libgbm libnss3 libatk1.0 libatk-bridge libcups libpango libasound libxkbcommon libdrm

# Ubuntu/Debian
apt-get install -y libgbm1 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libpango-1.0-0 libasound2 libxkbcommon0 libdrm2
```

#### Q6: 页面加载超时

```bash
# 增加超时时间
cd /home/zhiwei/AutoTestHub/tests/ui
npx playwright test --timeout=60000

# 检查网络
curl -I http://192.168.2.97:6089

# 查看浏览器日志
npx playwright test --debug
```

### 9.3 性能测试问题

#### Q6: Locust 启动失败

```bash
# 检查 Python 版本
python3 --version

# 重新安装 Locust
pip3 uninstall locust -y
pip3 install locust

# 检查配置文件
cat tests/performance/locust/config/default.conf
```

#### Q7: 端口被占用

```bash
# 检查端口占用
lsof -i :8089

# 杀进程
kill -9 $(lsof -t -i:8089)

# 更换端口
python3 -m locust -f locustfile.py --port 8090
```

### 9.4 权限问题

#### Q8: 脚本无法执行

```bash
# 添加执行权限
chmod +x scripts/*.sh

# 使用 bash 执行
bash scripts/run-api-tests.sh smoke
```

#### Q9: 目录无法写入

```bash
# 检查目录权限
ls -la docs/test-runs/
ls -la tests/api/reports/

# 修改权限
chmod -R 755 docs/test-runs/
chmod -R 755 tests/api/reports/
```

---

## 附录：命令速查表

### 一、快速开始

```bash
# 连接服务器
ssh root@192.168.2.70

# 进入项目
cd /home/zhiwei/AutoTestHub

# 拉取最新代码
git pull
```

### 二、API 测试

```bash
# 冒烟测试
./scripts/run-api-tests.sh smoke

# 全量测试
./scripts/run-api-tests.sh full

# 手动执行
cd tests/api
python3 -m pytest testsuites/ -v
```

### 三、UI 测试

```bash
# 冒烟测试
./scripts/run-ui-tests.sh smoke

# 全量测试
./scripts/run-ui-tests.sh

# 手动执行
cd tests/ui
npx playwright test
```

### 四、性能测试

```bash
# 冒烟测试
./scripts/run-perf-tests.sh smoke

# 常规压测
./scripts/run-perf-tests.sh regular

# 压力测试
./scripts/run-perf-tests.sh stress

# 手动执行
cd tests/performance/locust
python3 -m locust -f api/locustfile_smoke.py --headless -u 5 -r 1 -t 1m
```

### 五、安全测试

```bash
# 执行扫描
./scripts/run-security-tests.sh
```

### 六、全链路测试

```bash
# 业务流程全链路
cd tests/api && python3 -m pytest testsuites/crm/test_crm_full.py -v --timeout=120

# 商机阶段推进链路
python3 -m pytest testsuites/crm/test_crm_business.py::TestBusinessStageTransition -v

# 数据一致性链路
python3 -m pytest testsuites/crm/test_data_consistency.py -v

# API + UI 联合联调
./scripts/run-api-tests.sh full && ./scripts/run-ui-tests.sh
```

### 七、全流程

```bash
# 一键全流程（含全链路）
./scripts/run-full-test-flow.sh

# 后台执行
nohup ./scripts/run-full-test-flow.sh > output.log 2>&1 &

# 分阶段执行
./scripts/run-api-tests.sh smoke && ./scripts/run-api-tests.sh full
```

### 八、报告操作

```bash
# 查看报告
cat docs/test-runs/latest/reports/API测试报告.md

# 列出所有批次
ls docs/test-runs/

# 清理历史
cd docs/test-runs && ls -d */ | head -n -5 | xargs rm -rf
```

---

**文档版本**: v1.1  
**最后更新**: 2026-07-31  
**适用服务器**: 192.168.2.70  
**项目路径**: /home/zhiwei/AutoTestHub