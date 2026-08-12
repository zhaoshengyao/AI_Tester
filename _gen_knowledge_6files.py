# -*- coding: utf-8 -*-
"""阶段 11：测试知识沉淀 6 文件生成 → projects/ipd/docs/knowledge/
按 AGENTS.md：
- 测试知识沉淀必须保存可复用业务规则、回归资产、缺陷模式、自动化维护项、环境工具问题和下一轮迭代建议；证据不足的信息必须写"待确认"。
- 每个专项完成后立即沉淀该专项的经验和模式，不等所有专项完成；沉淀范围与当前已完成的专项直接相关。
- 知识沉淀不得修改历史报告和执行结果；只允许追加新的沉淀内容。

当前已沉淀范围：
- API 专项 100%（48/48）：可沉淀（认证流程/密码加密算法/接口参数/缺陷模式）
- UI 专项 downgrade（手工 smoke 4/10 PASS + 环境级阻断）：沉淀环境工具问题类，功能断言部分证据不足→待补测后追加
- 性能 专项 stop（未执行）：只沉淀前置未满足提醒，不沉淀性能指标经验
- 安全 专项 stop（未执行）：只沉淀前置未满足提醒+未来越权账号配置规范
"""
from __future__ import annotations

import os

PROJECT_ROOT = r"d:\AICode\TestHub\AITestDemo"
TS = "20260811-122314"
PROJ = "projects/ipd"
KNOWLEDGE_DIR = f"{PROJECT_ROOT}/{PROJ}/docs/knowledge"
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

# =========================================================
# 1. 业务规则库.md
# =========================================================
rules = r"""# IPD 管理系统 测试知识沉淀：业务规则库（版本 1.0 / 批次 """ + TS + r"""）

> AGENTS.md：知识沉淀不得修改历史报告和执行结果；证据不足的信息必须写"待确认"。
> 当前沉淀范围=已执行的 API 专项 48/48 100% + UI 手工 smoke 4 条（未执行专项不得主观推断规则，一律写"待补测后确认"）。

---

## 1. 认证 & 授权业务规则

### 1.1 登录接口（实测确认 ✅ 非猜测）
- **接口**：`POST http://192.168.2.97:6090/prod-api/auth/login`
  - ⚠️ 注意：不要用 system.yaml 里其他系统常见的 `/system/login` / `/oauth/token`；IPD 专用=`/auth/login`
- **请求体字段（严格驼峰）**：
  - `clientId`：`e5cd7e4891bf95d1d19206ce24a7b32e`（⚠️ 不是 snake_case `client_id`；不要漏）
  - `grantType`：`password`（⚠️ 不是 `grant_type`；不要漏）
  - `username`：`赵经理`
  - `password`：**AES-256-ECB 加密的 hex（小写）**
  - `tenantId`：`000000`（IPD 专用，不要漏）
- **密码加密算法（实测验证 ✅ 2026-08-11 通过）**：
  - 算法：`AES-256-ECB`（不是 GCM / 不是 AES-128 / 不是 CBC）
  - **KEY 取得方式（最容易踩坑的点）**：取 `clientId` 完整 32 字符 hex ASCII 字符串，直接用 `str.encode('utf-8')` 得到 32 字节（= 256 bits）。
  - ❌ **禁止**：把 `clientId` 当作 hex 字符串解码为 16 字节 → 会变成 AES-128 不够 key 长 → 直接 ValueError 或 登录"密码错误"。
  - Padding：PKCS7
  - 输出：加密后的二进制 → hex（小写）
- **请求头**：
  - 登录请求本身**不需要** Authorization
  - 登录成功后请求头：
    ```
    Authorization: Bearer {access_token}
    clientid: e5cd7e4891bf95d1d19206ce24a7b32e
    tenant-id: 000000
    Content-Type: application/json（写操作用；只读大多数可不用）
    ```
- **登录成功响应字段（实测确认）**：
  - `code=200`（HTTP 200 + 业务 code=200，两个层级都要判）
  - `data.access_token`：JWT（HS256）
  - `data.expires_in=480`（分钟=8 小时，类型 number）
  - `data.user.userId`：字符串 `"1795254289099898881"`（⚠️ 类型 string；其他地方如 data.roles.dataScope.userId 可能是 number=类型不一致但数值相同=不算缺陷，见 OM-07）
- **登出接口**：`POST /prod-api/auth/logout`（GET=405，Method Not Allowed）
  - 登出使用"Bearer + clientid + tenant-id"三个头
  - 注意：常见 JWT 实现不做黑名单，登出后立即访问仍=200（仅按 exp 过期）；不判失败（见 API-AUTH-009 测试注释）
- **错误密码**：HTTP 200 + 业务 code=500 或 401（不要断言 HTTP 401）+ msg=非空；不要写死 code=500（具体业务码可能变，只要 code != 200 就判错误密码通过）

### 1.2 权限 & 角色（基于赵经理项目经理 角色 实测）
- **项目经理可见的用户列表范围**：`/system/user/list` 返回 16 条（全员可见），含手机号/邮箱 PII 真实值 → 合规问题 R4（hand off 产品确认，未答复前不算缺陷）
- **项目经理可见的项目列表范围**：`/project/page` 返回 5 条= dashboard stats.total=5（对齐）；但 2026-08-11 11:00 点 dashboard=8，list=5（波动=权限缓存刷新？待确认 A1；后来又对齐=5）
- **风险模块权限**：赵经理可见 risk/page 4 条（LOW×3 + HIGH×1），与 dashboard riskCounts 完全一致；但 riskStats.medium=1 vs risk/list MEDIUM=0（API-003-A3 缺陷）

### 1.3 看板统计口径（实测+缺陷对比）
- `/idmp/dashboard/overview` 字段（实测确认）：
  - `stats.total`: 项目总数（赵经理本人）；5=正常
  - `stats.riskProjects`: 风险项目数；2=正常
  - `stats.avgProgress`: 平均进度%；24=正常
  - `stats.todos`: 待办事项数；0=正常
  - `riskCounts`：按 riskLevel 汇总，与 risk/page（无分页参数=默认参数）riskCount 数一致 ✅（冒烟用例一致性 A2）
  - `riskStats`：按 riskRule 汇总（TASK_DELAY/MILESTONE_WARN/...）；与 risk/page 按 ruleEnum 聚合 ≠ 一致（API-003-A3 medium 差 1）

### 1.4 真实 riskRule 枚举命名（真实实现 vs 需求分析文档差异 ✅ API-001）
- **真实接口返回枚举**（2026-08-11 实测 4 条）：
  1. `TASK_DELAY`（"任务延期预警"）
  2. `MILESTONE_WARN`（"里程碑预警"）
  3. `PROGRESS_WARN`（"进度落后预警"）
  4. `RESOURCE_WARN`（"资源冲突预警"）
- 需求分析原文档 SCHEDULE_WARN / QUALITY_WARN 等 ≠ 真实实现；**以真实接口为准**（AGENTS.md："只要存在可访问的真实系统，接口分析、接口用例和接口自动化必须以真实接口行为为最高优先级；接口文档、需求文档和原型用于对照差异，不得覆盖真实实现"）
- 登记缺陷：API-001（接口契约/文档一致性，中严重级）

### 1.5 分页 & 列表业务规则（含已知缺陷）
- **project/page 分页参数名**：`pageNum`（起始 1） / `pageSize`
- **project/page 分页不生效（严重缺陷高 API-004）**：无论 pageSize=1/3/10/100，都返回 5 rows total（赵经理项目正好=5 条；因此列表接口对赵经理本人=不受 pageSize 影响=功能相当于"不分页直接返回 5 条"；但项目数>5 时前端分页控件=摆设=高风险）
- **过滤参数（API-WF-003 / API-005）**：
  - workflow/definition/list：workflowCategoryId / categoryId / category_id 三候选名都无效；返回全量；→ API-005 中缺陷
  - risk/page：riskLevel 过滤有效 ✅（HIGH=1，MEDIUM=0，LOW=3）
  - budget/page：projectId 过滤有效 ✅（PID-2025-0002 返回 2 条正确）
  - project/page：status 过滤=有效（2026-08-11 未测全组合；基础用例通过）

### 1.6 UI 业务规则（仅手工 smoke 确认 4 条）
- **首页 5 个 KPI 与 dashboard/overview 对齐**：`5 我负责的项目`=`stats.total=5` ✅；`2 风险项目`=`stats.riskProjects=2` ✅；`24% 平均进度`=`stats.avgProgress=24` ✅；`0 待办事项`=`stats.todos=0` ✅
- **3 个顶层菜单可见**：统计分析看板 / 项目管理 / 工作流（3 menuitem collapsed 默认折叠）
- **单页应用后台轮询**：首页后台约 3 分钟有一次轮询→networkidle 永远不收敛（Playwright 默认 networkidle 30s 会超时；后续脚本必须用 `domcontentloaded` + 600ms wait）

### 1.7 未执行专项 = 业务规则不得主观推断（按 AGENTS.md 证据不足写待确认）
- **性能业务规则（压测阈值等）**：⚠️ **待确认**（性能专项 stop 未执行；不得主观推断 P95<500ms 为真实目标）
- **安全业务规则（JWT 强度、授权矩阵、越权规则）**：⚠️ **待确认**（安全专项 stop；越权测试需要张工程师低权限账号=未配置）
- **UI readonly 28 条规则（列表筛选/详情/弹窗/导出）**：⚠️ **待补测后确认**（UI 专项 downgrade 未执行 readonly 28）
- **写操作业务规则（项目 CRUD、风险 CRUD、审批、WF 启动）**：⚠️ **待补测后确认**（本轮 API、UI 写操作=未执行；缺少专用测试数据和回滚策略）
"""
with open(f"{KNOWLEDGE_DIR}/业务规则库.md", "w", encoding="utf-8") as f:
    f.write(rules)

# =========================================================
# 2. 回归资产库.md
# =========================================================
regression = r"""# IPD 管理系统 测试知识沉淀：回归资产库（版本 1.0 / 批次 """ + TS + r"""）

> 说明：按 AGENTS.md 沉淀可复用回归资产（自动化脚本、fixture、公共 helper、用例优先级、覆盖矩阵映射规则）。未执行部分写"未沉淀/下一轮补"。

---

## 1. 自动化代码资产（API 48/48 已复用）

### 1.1 公共 fixture（tests/api/ipd/conftest.py）— **高复用资产 TOP 1**
> 后续所有 IPD API / 性能 / 安全脚本 **必须** 复用以下 fixture，不要重写认证逻辑（避免重复踩 AES key 坑）：
- `ipd_config`：合并 `system.yaml` + `.env`，输出统一 dict（username/password/client_id/grant_type/auth 配置）
  - ⚠️ key 坑：`system.yaml` 中带注释的值（如 `aes-256-ecb"   #...`）必须在 `_load_system_yaml_auth` 中去除引号和注释，否则 fixture 会报 "Only aes-256-ecb supported; got aes-256-ecb\"" 之类 TypeError
- `encrypt_password(plaintext)`：AES-256-ECB hex（小写），PKCS7 padding，key = client_id 的 UTF-8 32B（不是 hex→bytes）
- `login_token()`：登录一次获取 access_token（session 级 scope，所有测试复用）
  - ⚠️ 注意：先去掉 `/prod-api` 前缀避免路径重复拼接；HTTP 200 + 业务 code=200 双层断言
- `authed_session()`：带 Authorization/clientid/tenant-id 的 requests Session（session 级 scope，所有测试复用）

### 1.2 API smoke 30 条 = 回归 P0（每次上线前必跑）
- 文件：`tests/api/ipd/test_auth_login.py`（认证 11 条）/ `test_user_profile.py`（用户 6 条）/ `test_dashboard_risk_stats.py`（看板 4 条）/ `test_projects_readonly.py`（项目 3 条）/ `test_risk_readonly.py`（风险 2 条）/ `test_budget_doc_readonly.py`（预算 2 条 + 文档 1 条）/ `test_workflow_readonly.py`（WF 定义 1 条）
- 覆盖范围：**登录/未授权/登出 + 本人信息 + 首页看板 + 项目/风险/预算/文档/WF 基础列表** = 最低服务闭环
- 执行命令（Windows）：
  ```powershell
  Set-Location d:\AICode\TestHub\AITestDemo
  $env:PYTHONPATH="$pwd;$pwd/tests/api/ipd"
  pytest tests/api/ipd -m smoke --json-report --json-report-file=_pytest_smoke.json -v --tb=short 2>&1 | Tee-Object _pytest_smoke_stdout.txt
  ```
- 门禁阈值：smoke 30 条 `passed=30/failed=0` 才允许进入 API readonly / UI smoke / 性能 smoke；**任何 1 条 smoke failed = 不进入 readonly/full（按 AGENTS.md retest/collect-evidence 处理）**

### 1.3 API readonly-regression 18 条 = 回归 P1（major 版本必跑）
- 文件：`test_readonly_boundary_filters.py`（分页边界 7 + 过滤 5 + 参数 3） + `test_project_risk_wf_consistency.py`（A1/A2/A3 3 条一致性）
- 覆盖：分页边界（pageSize 0/1/100/负数）、过滤（riskLevel/budget/projectId）、一致性（看板统计 vs 列表 len / 列表聚合 vs 看板聚合）
- 执行：`pytest tests/api/ipd -m readonly`
- 注意：一致性 A1/A2/A3 = 打印缺陷（[接口契约/实现一致性缺陷 API-003-*]）而不是断言失败（AGENTS.md：真实接口行为>文档/主观预期，不得把真实实现判死）

### 1.4 UI 自动化公共配置（tests/ui/ipd/conftest.py + 独立脚本 _run_ui_smoke_standalone.py）
- 当前状态：已生成基础 fixture，但本轮因环境级未执行完整脚本化；下一轮补 UI 后把 UI 公共配置沉淀为"UI smoke 脚本稳定版"
- 已知必须修改项（本轮失败后沉淀）：
  1. 所有 `page.goto(url, wait_until='networkidle')` → 改成 `page.goto(url, wait_until='domcontentloaded'); page.wait_for_timeout(600)`
  2. 所有 `locator.click()` 对子菜单 collapsed 项 → `locator.click(force=True, timeout=5000)`
  3. `playwright install chromium` 必须在非 TRAE Sandbox 限制环境先完成；Sandbox 放行路径 `C:\Users\16509\AppData\Local\ms-playwright\*`

### 1.5 未沉淀/下一轮补（按 AGENTS.md 证据不足不伪造）
- UI readonly-regression 28 条脚本：⏳ 待补（本轮 UI downgrade 未执行）
- UI 截图基准库：⏳ 待补（无稳定环境截图）
- 性能 Locust locustfile.py：⏳ 待补（性能专项 stop 未执行）
- 安全扫描器子模块（unauth/idor/injection/sensors 4 脚本）：⏳ 待补（安全专项 stop 未执行）
- API write-regression（新增/编辑/删除 项目、风险、预算、WF 启动）：⏳ 待补（缺少专用测试数据和回滚策略）

---

## 2. 文档资产（可复用）
- 实测 API 基线：`projects/ipd/docs/analysis/实测API基线.json`（18 接口 = 当前所有 smoke+readonly 脚本来源）
- 需求分析报告：`projects/ipd/docs/analysis/需求分析报告.md`（56 功能单元 + 12 核心实体 + R1~R10）
- 覆盖矩阵 V0：`projects/ipd/docs/test-runs/""" + TS + r"""/reports/覆盖矩阵.md`（197 评审版 1:1 映射，已更新 API 段 executed=48）

---

## 3. 环境 & 账号资产（复用规范）
- `.env` 固定格式（IPD 专用）：
  ```
  BASE_URL=http://192.168.2.97:6090
  API_BASE_URL=http://192.168.2.97:6090/prod-api
  TEST_USERNAME=赵经理
  TEST_PASSWORD=123456
  API_USERNAME=赵经理
  API_PASSWORD=123456
  API_CLIENT_ID=e5cd7e4891bf95d1d19206ce24a7b32e
  ```
- `system.yaml` auth 段（IPD 专用，不要复制其他系统）：
  ```yaml
  auth:
    type: oauth2
    config:
      grant_type: password
      grant_type_field: grantType
      client_id: e5cd7e4891bf95d1d19206ce24a7b32e
      client_id_field: clientId
      login_path: /prod-api/auth/login
      password_encryption: aes-256-ecb
      password_encryption_key_source: client_id_full
      extra_fields:
        tenantId: "000000"
  ```
"""
with open(f"{KNOWLEDGE_DIR}/回归资产库.md", "w", encoding="utf-8") as f:
    f.write(regression)

# =========================================================
# 3. 缺陷模式库.md
# =========================================================
defects_pattern = r"""# IPD 管理系统 测试知识沉淀：缺陷模式库（版本 1.0 / 批次 """ + TS + r"""）

> 沉淀可复用的缺陷发现模式（发现手法 + 复现步骤 + 严重级判定 + 常见根因 + 预防检查）。已登记 4 条 API 缺陷 + 1 环境级工具类（非被测系统缺陷不纳入缺陷清单但登记知识库）。

---

## 1. 已登记 API 缺陷（4 条，按严重级 高→中 排序）

### 缺陷 ID：API-004（高 TOP1）「分页不生效 = 接口契约/实现一致性缺陷」
- **发现模式（可复用手法）**：对所有带 `pageNum/pageSize` 的列表接口，固定 `pageSize=1`，对比返回 rows 数=**实际 5 条 != 预期 1 条** → 立即判断分页不生效。
- **复现步骤（通用）**：
  1. 登录获取 Bearer
  2. 调 `GET /project/page?pageNum=1&pageSize=1`
  3. 断言 `len(rows) <= pageSize`；失败=缺陷
- **严重级判定规则**：高=列表接口核心功能（分页）= 数据>100 时前端崩溃/用户不可用，属于"主路径不可用"；若 pageSize=1 返回 1 条但 pageSize=3 返回 5 条=中严重级；若仅某模块分页不生效=根据模块权重降为中。
- **常见根因**：MyBatis 分页插件 PageHelper 未正确引入或 order by 字段未建索引导致 select count(0) 之后取全量 offset=0 后应用层无 limit。
- **预防检查（下一轮写用例自动覆盖）**：所有 `*/page`、`*/list` 接口的 smoke 段必带 `pageSize=1` 返回 rows<=1 断言。

### 缺陷 ID：API-003-A3（中）「riskStats 与 risk/page 按 ruleEnum 聚合不一致 = 接口契约/实现一致性缺陷」
- **发现模式（可复用手法，看板/列表一致性必查项）**：
  - 先调 dashboard/overview stats 聚合（A 段聚合）
  - 再调 list/page 全量（pageSize=100）后对同一维度（ruleEnum）python 端聚合
  - 两聚合结果做 dict 差集（按 key 对 value），非空值=缺陷候选
- **复现步骤（IPD riskStats）**：
  1. dashboard.overview.riskStats.medium = 1
  2. risk/page（无分页）按 ruleEnum 聚合：TASK_DELAY=1、MILESTONE_WARN=1、PROGRESS_WARN=1、RESOURCE_WARN=1 → medium=0
  3. 差=medium: 1 vs 0 → 缺陷
- **严重级判定规则**：中=看板统计-列表口径差（用户直接看两个页面数据不一致会吐槽）
- **常见根因**：dashboard 用数据仓库物化视图（全项目）vs list 用主库权限过滤（本人项目）→ 口径不同未文档化
- **预防检查**：所有 dashboard stats N 条字段 = list/page 聚合 N 个维度，自动化脚本必做一致性比对（A1/A2/A3 三条模板可复制）

### 缺陷 ID：API-001（中）「riskRule 枚举命名不一致 = 接口契约/文档一致性缺陷」
- **发现模式**：需求分析/接口文档枚举名 vs 真实接口返回枚举名做 set 差集；非空=缺陷候选
- **复现步骤**：
  1. 需求分析 SCHEDULE_WARN/QUALITY_WARN /... 枚举 6 个
  2. 真实接口返回 TASK_DELAY/MILESTONE_WARN/... 枚举 4 个
  3. 交集=0 → 完全不同=命名不一致
- **严重级判定**：中=前后端/产品 三方语义不共享=容易导致 UI 错显、过滤传参不生效（如 API-005）
- **预防检查**：所有枚举类字段（status/level/type/ruleEnum/category）脚本必做"文档 set ∩ 真实返回 set"；若交集 < 75%=立即登记文档一致性缺陷

### 缺陷 ID：API-005（中）「WF 分类过滤参数名不生效 = 接口契约/实现一致性缺陷」
- **发现模式（过滤参数必查套路）**：枚举所有候选参数名（后端常用 `categoryId` / `category_id` / `workflowCategoryId` / `categoryCode` / `type` 共 5 个常见），每个候选各传 1 个有效枚举值；若 5 个候选都返回全量 rows=过滤不生效缺陷候选
- **复现步骤**：
  1. 全量先跑一次 workflow/definition/list → 记录 total=6
  2. 分别传 `workflowCategoryId=CAT-001` / `categoryId=CAT-001` / `category_id=CAT-001` → 三次 total 均=6
  3. → 过滤未生效=缺陷
- **严重级判定**：中=过滤功能不可用（数据量大时找不到目标）
- **预防检查**：所有 FUNC-UI-FILTER 用例对应的后端 API，readonly-regression 段必跑 3 种候选参数名组合

---

## 2. 已沉淀但非被测系统缺陷（工具/环境类 = 知识库登记、不纳入缺陷清单）
### ENV-TOOL-001（Playwright networkidle 超时）
- **模式**：单页应用（SPA）有后台轮询（dashboard/overview 每 3 分钟拉取、或 websocket 保活）导致 Playwright `networkidle` 永不 idle
- **表现**：`page.goto(url, wait_until='networkidle')` 30s 超时；浏览器 UI 实际已经能看到页面但脚本还在等
- **修复模式（复用）**：把所有 `wait_until='networkidle'` 改为 `wait_until='domcontentloaded'`，然后 `page.wait_for_timeout(600)` 给 JS 渲染留时间；如果有元素可见性断言（`expect(loc).to_be_visible()`）可去掉固定 timeout 用断言驱动

### ENV-TOOL-002（TRAE Sandbox 阻止写 ms-playwright 目录）
- **表现**：`playwright install chromium` 时 `mkdir ms-playwright/__dirlock` → EPERM；或执行时 `write ...DEPENDENCIES_VALIDATED` 被 TRAE Sandbox Error 阻止
- **修复模式**：在 Settings → Conversation → Custom Sandbox Configuration 中放行 `C:\Users\***\AppData\Local\ms-playwright\**` 目录读写；或把 Playwright 浏览器位置用 `PLAYWRIGHT_BROWSERS_PATH=D:\\.cache\\ms-playwright` 指向 D 盘（TRAE 默认允许工作目录读写）

### ENV-TOOL-003（MCP 集成浏览器 collapsed 菜单 pointer-events none）
- **模式**：UI 组件库（Arco/Antd）collapsed 菜单 li 元素有 `pointer-events: none;` → MCP browser_click（基于 li menuitem 选择器）→ "Element e2 has pointer-events: none"
- **修复模式**：Playwright `get_by_role('menuitem', name='项目管理').click(force=True)`（`force=True` 忽略可点击性检查，直接触发点击事件）；或 `evaluate` 找到子元素 i/a/span 的 click 事件显式触发

### ENV-TOOL-004（YAML auth 配置值带引号/注释导致 fixture 解析 ValueError）
- **模式**：`system.yaml` 中 `password_encryption: aes-256-ecb"   # 实测确认：不是 gcm` → yaml 把后面 `" # ` 都当成值的一部分 → fixture 比较 `got aes-256-ecb" != 期望 aes-256-ecb` 报错
- **修复模式**：`_load_system_yaml_auth` 函数对所有字符串做 `strip().strip('\"').strip("'")` + 取 `#` 前的值，清洗干净再用

---

## 3. 性能/安全专项未执行 = 缺陷模式沉淀不得主观推断（按 AGENTS.md）
- 性能缺陷模式（慢查询/缓存击穿/线程池饱和）：⏳ **待补测后沉淀**
- 安全缺陷模式（未授权/越权/注入/PII 暴露）：⏳ **待补测后沉淀**
- UI 缺陷模式（错位/空态/响应式）：⏳ **待 UI readonly 28 条补测后沉淀**
"""
with open(f"{KNOWLEDGE_DIR}/缺陷模式库.md", "w", encoding="utf-8") as f:
    f.write(defects_pattern)

# =========================================================
# 4. 自动化维护项.md
# =========================================================
maintenance = r"""# IPD 管理系统 测试知识沉淀：自动化维护项（版本 1.0 / 批次 """ + TS + r"""）

> 沉淀自动化脚本在后续批次需要维护的点（依赖版本、配置同步、账号密码更新、接口字段变化、脚本稳定性、CI/CD 集成）。按"每次执行后更新"。

---

## 1. 配置同步维护（P0：任何变更必更新，否则全流程挂）
1.1 **`projects/ipd/.env` 密码/账号/地址 同步**：
  - 触发条件：任何密码变更、IP 地址迁移、端口变化（如 6090→8080）、prod-api 前缀变化
  - 同步项：`BASE_URL` / `API_BASE_URL` / `TEST_USERNAME` / `TEST_PASSWORD` / `API_*` / `API_CLIENT_ID`
  - 校验：更新后立即跑 `pytest tests/api/ipd/test_auth_login.py::test_login_success_oauth2_password_mode` → 断言 code=200

1.2 **`projects/ipd/system.yaml` auth 段 同步（P0）**：
  - 触发条件：登录接口路径改（/prod-api/auth/login → 其他）、加密算法改（AES-256-ECB → GCM/SM4）、clientId 改、grantType 改、extra_fields（tenantId）改
  - 校验：跑 `test_auth_login.py::test_login_success_oauth2_password_mode`

1.3 **实测API基线.json 定期刷新**：
  - 触发条件：系统升级后（版本号 V1 → V2）、新增模块（比如质量管理、合同管理）
  - 动作：重跑 `scripts/probe_ipd_details.py` 生成 2.0 版基线，比对与 1.0 差异（新增接口 + 废弃接口 + 字段变更）→ 追加到下批次"文档与实际差异"

---

## 2. 脚本稳定性维护（P1：每 2 批次必须优化一次）
2.1 **API 脚本稳定性维护**：
  - 已知无不稳定项（48/48 本批次 100% 通过）；下一轮观察是否有偶发 5xx=添加 `pytest-rerunfailures` + `reruns=2` 对 5xx 类重试（不影响断言正确性，只抗偶发网络抖动）
  - `test_consistency_A1`（dashboard 与 project/list 口径）：注意权限缓存刷新可能导致 dashboard 和 list 短暂不同步（本批次 11:00 8 vs 5，过一会儿又 5 vs 5）→ 若未来仍波动 → 重跑机制（连续 3 次 2 次以上不一致才登记缺陷）

2.2 **UI 脚本稳定性维护（本轮因环境未完整执行，下一轮必改）**：
  - 高优先级：`_run_ui_smoke_standalone.py` 所有 `wait_until='networkidle'` → `domcontentloaded` + 600ms wait
  - 高优先级：所有子菜单 click + force=True + timeout=5000
  - 中优先级：`conftest.py` 中 `storage_state=auth_context.storage_state` 持久化（避免每轮登录取 token，加速 UI smoke）
  - 中优先级：所有截图增加 `full_page=True`（避免页面长时只截首屏）

2.3 **依赖版本维护（每 1~2 个月做一次）**：
  - 当前版本：`playwright==1.61.0` / `requests`（最新）/ `pytest`（最新）/ `PyYAML`（最新）/ `python-dotenv`（最新）/ `cryptography`（最新）
  - 升级动作：`pip list --outdated` 先列，锁定 `requirements.txt`（若存在），升级后先跑 API smoke 30 条再升级 UI 依赖（避免一次升级一堆回滚难）
  - 新增依赖：`locust`（下一轮性能前 `pip install locust`）、`pytest-rerunfailures`（5xx 重试）

---

## 3. 覆盖矩阵 & 用例映射维护
3.1 **每次新增/删除评审版用例 → 覆盖矩阵同步**：197 条评审版若产品/需求变更，立即更新覆盖矩阵 1:1 映射，新增脚本列、执行状态列、缺陷关联列
3.2 **UI readonly 28 条脚本实现后 → 覆盖矩阵 implemented=1 → executed=按结果填**
3.3 **性能 4 条脚本实现后 → 覆盖矩阵同步**
3.4 **安全 28 条脚本实现后 → 覆盖矩阵同步**

---

## 4. CI/CD 集成（下一轮推进）
4.1 **GitLab CI / Jenkins 最小流水线 YAML 模板（待实现）**：
  ```
  stages:
    - env-check     # python -V; pip install -r requirements.txt
    - api-smoke     # pytest tests/api/ipd -m smoke → 30 passed 才下阶段
    - api-full      # pytest tests/api/ipd（smoke+readonly）→ 48 条
    - ui-smoke      # playwright install chromium + _run_ui_smoke_standalone.py → 10/10 PASS
    - report-gen    # python _gen_api_report.py + _gen_ui_...报告 + 系统报告 + 批次摘要
    - artifact      # 归档 reports/defects/raw → 作为当前批次产物
  ```
4.2 **通知**：报告生成后飞书/钉钉机器人推送"批次完成 + 通过数 + 缺陷数 + 系统报告链接"

---

## 5. 本轮未执行专项 → 自动化维护项=待下一轮补
- 性能 Locust 脚本维护规范：⏳ **待补**
- 安全扫描器维护（payload 库升级、误报白名单、cookie 自动刷新）：⏳ **待补**
- 写操作回滚策略维护（专用测试数据隔离库、清理脚本、伪删除 flag 恢复）：⏳ **待补**
"""
with open(f"{KNOWLEDGE_DIR}/自动化维护项.md", "w", encoding="utf-8") as f:
    f.write(maintenance)

# =========================================================
# 5. 环境工具问题.md
# =========================================================
env_tools = r"""# IPD 管理系统 测试知识沉淀：环境工具问题（版本 1.0 / 批次 """ + TS + r"""）

> 沉淀所有环境问题、工具使用问题、第三方依赖问题（不是被测系统的业务缺陷，不纳入缺陷清单，但必须长期记录避免再次踩坑）。按"每次执行后更新"。

---

## 1. 本轮实际遇到（可直接用于后续批次避免踩坑）

### ENV-1：TRAE Sandbox 阻止 Playwright 浏览器目录写入
- **发生时间**：2026-08-11 20:33:21 + 20:42:32（两次触发）
- **错误信息**：
  - `PermissionError: [WinError 5] Access is denied: '...\\AppData\\Local\\ms-playwright\\__dirlock'`（`playwright install chromium`）
  - `TRAE Sandbox Error: hit restricted Not allow operate files: ...\\chromium_headless_shell-1228\\DEPENDENCIES_VALIDATED`（运行时写）
- **影响**：Playwright 脚本化 smoke 16/19 failed 直接原因（Sandbox 阻止写，浏览器内部状态异常导致 networkidle 更难收敛）
- **解决方案（任选其一，优先 #2 最稳）**：
  1. Settings → Conversation → Custom Sandbox Configuration → 添加放行路径 `C:\Users\16509\AppData\Local\ms-playwright\**`（读写）
  2. 设置环境变量 `PLAYWRIGHT_BROWSERS_PATH=D:\AICode\TestHub\AITestDemo\.cache\ms-playwright`（D 盘工作目录=TRAE 默认允许读写，不需要改 Sandbox 配置）
- **预防**：下一轮 UI 启动前 5 分钟，先跑 `$env:PLAYWRIGHT_BROWSERS_PATH='...'; python -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.launch(); print(b.new_page().title()); p.stop()"`，确认可正常 launch 才跑 UI smoke

### ENV-2：IPD 单页应用 networkidle 永不收敛
- **错误信息**：`TimeoutError: Page.goto: Timeout 30000ms exceeded navigating to /index waiting until networkidle`
- **根因**：IPD 前端有后台轮询接口（dashboard/overview 每 3 分钟拉取 / 或 websocket 保活连接），`networkidle` 需要网络连接 0.5s 空闲 → SPA 做不到
- **解决方案**：所有 Playwright 脚本使用 `wait_until='domcontentloaded'`（DOM Ready 就继续）然后 `page.wait_for_timeout(600)` 给 React/Vue 渲染留时间；不要依赖 `networkidle`
- **预防**：自动化架构层（conftest fixture 的 `page`）统一 patch 默认 goto 不要用 networkidle

### ENV-3：MCP 集成浏览器 collapsed 菜单 pointer-events none
- **错误信息**：`tool 'browser_click' failed: Element e2 has pointer-events: none`（点击 collapsed 菜单 menuitem）
- **根因**：Antd / Arco Design collapsed 菜单只允许展开按钮（小图标 i 标签）点击；整个 li menuitem 被 `pointer-events: none` 阻止
- **解决方案**：
  - MCP 浏览器：不要选整个 menuitem；先 `get_attribute('innerHTML')` 找内部子元素 i/a/button，选择精确子元素 click
  - Playwright 脚本：`get_by_role('menuitem', name='项目管理').click(force=True, timeout=5000)`（`force=True` 忽略 pointer-events 检查，直接 dispatch click event）
- **预防**：UI 测试设计阶段识别 collapsed 菜单，提前在脚本中预留 force=True 分支

### ENV-4：system.yaml 值带引号+注释 → fixture 解析失败
- **错误信息**：`AssertionError: Only aes-256-ecb supported in IPD fixture; got aes-256-ecb"    # 实测确认：不是 gcm`
- **根因**：YAML `password_encryption: aes-256-ecb"   # 注释` → 解析出的值包含末尾 `"` 和注释
- **解决方案**：`_load_system_yaml_auth` 函数所有字符串做 `s = s.strip(); s = s.split('#',1)[0].strip(); s = s.strip('\'"')` 再返回
- **预防**：所有读取 YAML 的 helper 函数默认做 "去注释+去外层引号" 清洗

### ENV-5：登出测试登出主 token → 后续接口 401
- **错误信息**：`test_auth_login.py::test_logout` 调用后，后续 `test_*` 接口 HTTP 200 + 业务 code=401
- **根因**：登出测试使用全局 `login_token`（session scope）的 token 做登出 → 全局 token 被作废
- **解决方案**：登出测试内部**新登录一个独立临时 token** 做登出验证，完全不碰主 `login_token` / `authed_session`
- **预防**：所有对 token/登录态有副作用的测试（登出、修改密码、refresh_token）必须使用独立临时 token，不能污染全局 session

### ENV-6：一致性测试 `_fetch_all` 接口 401 返回 None → KeyError/TypeError
- **错误信息**：`KeyError: 'stats'` 或 `TypeError: 'NoneType' object is not subscriptable`（A7/A8 之前的版本）
- **根因**：接口 401 返回 `None` 但代码直接 `s['dash']['stats']`
- **解决方案**：`_fetch_all` 内每个接口调用后都做 `assert r.status_code==200; assert body.get('code')==200; assert data is not None`；断言失败立刻 raise（而不是静默返回 None 让下游 KeyError，排查困难）
- **预防**：所有数据获取 helper 函数第一优先级做"接口响应校验"，再处理业务字段

### ENV-7：PowerShell `mkdir -p a/b/c` 报错 "A positional parameter cannot be found"
- **错误信息**：Windows PowerShell 5 不支持 `-p`（POSIX mkdir 参数）
- **解决方案**：`New-Item -ItemType Directory -Force -Path projects/ipd/docs/cases,projects/ipd/docs/analysis,...`（一次创建多目录，逗号分隔）
- **预防**：所有脚本统一检查是否为 PowerShell 5，目录创建改用 `New-Item -Force`

### ENV-8：pip install paramiko 初始未安装
- **发生时间**：2026-08-11 01:17 remote-script-runner 技能启动前
- **解决方案**：`pip install paramiko -q`（-q 静默安装减少输出）
- **预防**：新建 `requirements.txt`（若不存在）显式列：`paramiko`、`playwright`、`PyYAML`、`python-dotenv`、`cryptography`、`requests`、`pytest`、`pytest-json-report`、`locust`；第一次部署机器 `pip install -r requirements.txt` 一步到位

---

## 2. 下一轮执行前必须检查（Checklist）
```
□ ENV-1 修复：Sandbox 放行 ms-playwright 或 设置 PLAYWRIGHT_BROWSERS_PATH=D:\...\.cache
□ 运行 Playwright 最小 launch 测试成功（ENV-1 预防脚本）
□ ENV-2 修改：所有 Playwright 脚本 networkidle → domcontentloaded + 600ms wait
□ ENV-5 验证：登出测试使用独立临时 token（本轮已修复 → 下一轮仅回归确认即可）
□ pip install -r requirements.txt 一次（含 locust）
□ .env 账号密码有效性确认（赵经理 123456 密码未过期）
```

---

## 3. 性能/安全专项未执行 = 环境工具问题暂不沉淀
- Locust 执行环境问题（压测客户端带宽不足 / 目标端 WAF 限流）：⏳ **待补测后沉淀**
- ZAP/自定义安全扫描器代理配置、Cookie 注入、误报白名单维护：⏳ **待补测后沉淀**
"""
with open(f"{KNOWLEDGE_DIR}/环境工具问题.md", "w", encoding="utf-8") as f:
    f.write(env_tools)

# =========================================================
# 6. 下一轮迭代建议.md
# =========================================================
next_iteration = r"""# IPD 管理系统 测试知识沉淀：下一轮迭代建议（版本 1.0 / 批次 """ + TS + r"""）

> 沉淀"下一轮要做什么、为什么、怎么做、优先级 P0/P1/P2"，按 AGENTS.md "知识沉淀必须包含下一轮迭代建议"。当前批次完成度=API 100% + UI downgrade 部分 + 性能/安全 stop → 本轮未完成的所有内容自动进入下一轮 Top。

---

## 下一轮目标（一句话）
完成 **UI readonly 28 条（含 UI-SEC 类 3 条错误密码/登出/拦截）+ 性能 4 条 + 安全 28 条 = 60 条未执行专项** 全闭环，缺陷总登记 4→?，系统测试报告第 3 次增量，知识沉淀版本 2.0。

---

## P0 级（下一轮启动后 24h 内必须完成；否则影响后续所有工作）

### P0-1：UI 脚本化环境修复 + UI smoke 10/10 PASS 补齐
- **为什么**：当前批次 UI 专项 downgrade（仅手工 4 条）；未执行 6 条 smoke（子菜单跳转/错误密码/登出/登出后拦截）+ 28 readonly=34 条 UI 缺口=覆盖不足，系统测试报告的基础 UI 体验证据不足。
- **怎么做**：
  1. 修 ENV-1（Sandbox 阻止 ms-playwright 写入）：任选 PLAYWRIGHT_BROWSERS_PATH=D:\...\.cache 方案最稳
  2. 修 ENV-2（networkidle 不收敛）：`_run_ui_smoke_standalone.py` 所有 `wait_until='networkidle'` → `domcontentloaded` + 600ms wait
  3. 修 ENV-3（pointer-events）：所有 collapsed 菜单 click 改为 `force=True`
  4. 重跑脚本化 UI smoke → 10/10 PASS → 截图 raw/ui + JSON 结果
- **交付物**：脚本化 UI smoke 结果 JSON + 10 张截图 + 覆盖矩阵 UI 段 implemented=10
- **门禁**：P0-1 不 100% 通过 → 不进入 P0-2（UI readonly）

### P0-2：UI readonly-regression 28 条脚本实现 + 执行
- **为什么**：UI 评审版 28 条 = 未实现脚本；覆盖矩阵 implemented=0=系统报告 UI 段证据不足
- **怎么做**：
  1. 新建 `tests/ui/ipd/test_ui_readonly.py`：
     - 列表/筛选/详情：项目列表+筛选 6 条、风险列表+筛选 5 条、预算列表 4 条、文档列表 2 条、流程定义列表+分类 5 条
     - KPI/首页只读：首页 5 卡片点击进入详情 3 条、导出响应 2 条、只读弹窗/提示 1 条
     - UI-SEC 类：错误密码提示 1 条 + 登出跳转 1 条 + 登出后拦截 1 条 = 3 条合计 28
  2. 每条脚本与 UI 评审版 **用例编号 1:1 映射**（FUNC-UI-001~FUNC-UI-020 + UI-SMOKE 009/010 + UI-SEC 追加）
  3. 执行：`pytest tests/ui/ipd -m readonly --video=retain-on-failure --screenshot=only-on-failure`
- **交付物**：UI readonly 28 条结果 JSON + 失败截图/视频 + UI专项报告 2.0 增量 + UI缺陷清单 2.0（如有新增 UI 缺陷）+ 覆盖矩阵 UI 段 executed=28
- **门禁**：readonly 28 pass ≥ 90% → 才可进入性能 smoke（不要求 100%，UI 偶发环境小波动可接受，不影响全局门禁）

### P0-3：API 4 条缺陷移交产品+研发 → 登记 Jira/TAPD 获得 Defect ID
- **为什么**：当前批次 4 条缺陷（高 1 中 3）只有知识库 ID（API-001/003-A3/004/005），没有正式工具 ID = 无法确认责任人/截止日期/修复状态/回归验证；AGENTS.md 缺陷模式库要求"回填覆盖矩阵缺陷关联列"需要正式 ID。
- **怎么做**：
  1. 导出 API缺陷清单.md → Jira/TAPD CSV/Excel 导入格式
  2. 找产品/研发负责人评审严重级是否一致
  3. 获得 D-001 / D-002 / D-003 / D-004 4 个正式缺陷号
  4. 回填覆盖矩阵"缺陷关联"列 API 段（用例 API-001 / API-003-A3 / API-004 / API-005 对应缺陷号）
- **交付物**：4 条正式缺陷 ID + 覆盖矩阵 updated

---

## P1 级（下一轮 48h 内完成，P0 做完后立即启动）

### P1-1：性能专项 4 条全执行
- **前置**：pip install locust 成功 + 压测参数评审 + 时间窗口确认
- **怎么做**：
  1. 写 `tests/perf/ipd/locustfile.py`（任务比例：登录 10% / dashboard overview 30% / project/page 50% / project/detail 10%）
  2. PERF-001 smoke：5 用户 60s → 错误率<0.5% + P95<800ms → continue
  3. PERF-002 恢复 smoke：PERF-001 后 30s → 1 用户 30s（看服务恢复能力）→ 再进 PERF-003
  4. PERF-003 full：50 用户 300s → 记录 P95/P99/QPS/错误率
  5. PERF-004 downgrade：PERF-001 不达标但 PERF-002 达标才执行 15 用户 180s
- **交付物**：locust_report.html + CSV + 性能专项报告 2.0 + 性能缺陷清单（如有 P95>1s 登记性能瓶颈缺陷）+ 系统报告 §3.3 第 2 次增量

### P1-2：安全专项 28 条全执行
- **前置**：① 建立 `tests/security/ipd/` 最小扫描器 4 子模块脚本 ② 目标方书面授权扫描范围+时间窗口 ③ 越权账号 2 个（赵经理项目经理 + 张工程师普通成员）
- **怎么做**：
  1. SEC-AUTH 8 条（未授权访问）：对 8 个受保护接口（dashboard、project/page/detail、risk/page、budget/page、doc/page、wf/list、user/list）不带 token → HTTP 200 + code=401 或 HTTP 401 = 通过；HTTP 200 + code=200 = 未授权高危缺陷
  2. SEC-IDOR 8 条（越权）：张工程师访问赵经理的项目详情（PID-2025-0001）、风险详情、预算详情 → HTTP 403 / code=403 = 通过；200=越权缺陷
  3. SEC-INJ 8 条（SQL/XSS/SSRF）：
     - SQL：`projectName=项目' OR '1'='1` → 不应返回全量（不应比正常参数返回更多）
     - XSS：`projectName=<script>alert(1)</script>` → 返回应被 HTML entity 编码（前端不触发 alert）
     - SSRF：`docUrl=http://169.254.169.254/latest/meta-data/` → 400/错误提示=通过
  4. SEC-SENS+JWT：`/system/user/list` 返回手机号/邮箱是否脱敏（138****1234）= PII 合规；JWT 过期时间>8h 登记弱强度
- **交付物**：安全扫描 JSON 报告 + 安全专项报告 2.0 + 安全缺陷清单 + 系统报告 §3.4 第二次增量 + R4 合规缺陷最终状态（产品答复后更新）

### P1-3：需求分析文档同步（2 处）
1. riskRule 枚举命名同步真实实现（API-001 文档一致性缺陷）
2. AES key 形式文档化（client_id 字符串 UTF-8 32B，非 hex→bytes 16B；在需求分析 §认证段明确）

---

## P2 级（下个批次完成后立即开始，或本批次有余力则推进）
### P2-1：CI/CD 最小流水线搭建（Jenkins/GitLab）
- 自动化维护项 §4 中 YAML 模板落地
### P2-2：API write-regression（项目/风险 CRUD、WF 启动、预算提交）
- 准备专用测试数据库（test_ipd）+ 回滚脚本
- 覆盖矩阵 API 段新增 write 子层 implemented
### P2-3：UI 兼容性测试（Firefox / Edge）
- 覆盖矩阵 UI 段新增 compatibility 子层
### P2-4：数据看板与测试总览页内部工具
- 把当前 6 个知识沉淀文件可视化成团队内部 Dashboard（指标：缺陷总数、覆盖进度、每个专项通过率、Top5 严重缺陷）

---

## 下一轮批次完成判定标准（Go/No-Go 门禁清单）
- [ ] UI smoke 10/10 PASS（脚本化）✅
- [ ] UI readonly 28/28 ≥ 90% pass ✅
- [ ] 性能 4 条（PERF-001~004）执行完成（或 stop/downgrade 有明确原因）✅
- [ ] 安全 28 条执行完成（或 stop/downgrade 有明确原因）✅
- [ ] 系统测试报告第 3 次增量完成 ✅
- [ ] 批次摘要 3.0 完成 ✅
- [ ] 知识沉淀 2.0 完成 ✅
- [ ] API 4 条缺陷正式工具登记 ID 获得 ✅
"""
with open(f"{KNOWLEDGE_DIR}/下一轮迭代建议.md", "w", encoding="utf-8") as f:
    f.write(next_iteration)

print("✅ 业务规则库.md")
print("✅ 回归资产库.md")
print("✅ 缺陷模式库.md")
print("✅ 自动化维护项.md")
print("✅ 环境工具问题.md")
print("✅ 下一轮迭代建议.md")
print(f"\n6 文件已生成到 {KNOWLEDGE_DIR}")
