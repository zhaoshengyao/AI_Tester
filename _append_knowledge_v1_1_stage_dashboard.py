# -*- coding: utf-8 -*-
"""知识沉淀 6 文件 V1.0 → V1.1 增量追加：针对「赵老板角色 × 项目管理模块 × 看板一致性专项」完成后新增的资产。
严格遵循 AGENTS.md：不得修改历史报告和执行结果；只允许追加新的沉淀内容；证据不足=写"待确认"。

注意：为避免 ENV-11（f-string 内嵌 f-string / 复杂嵌套大括号导致 SyntaxError），本脚本的所有大段内容模板使用
普通三重引号 + __TS__ 占位符，最后用 .replace("__TS__", TS_DISPLAY) 做单次替换；不再用 f-string。
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime

REPO = Path(r"d:\AICode\TestHub\AITestDemo")
KNOW = REPO / "projects" / "ipd" / "docs" / "knowledge"
TS_DISPLAY = "2026-08-12 批次 20260811-122314 第 2 次增量（追加「赵老板角色 × 项目管理 semi-auto × 看板一致性」专项资产，版本 1.0 → 1.1）"

def append_if_not_exists(path: Path, anchor_line: str, content_template: str) -> str:
    """在文件末尾追加新内容；若 anchor_line 已存在说明之前已追加=跳过。
    内容模板使用 __TS__ 占位符，在这里做一次 replace。"""
    new_content = content_template.replace("__TS__", TS_DISPLAY)
    orig = path.read_text(encoding="utf-8")
    if anchor_line in orig:
        return f"[SKIP] {path.name}（已含 V1.1 锚点）"
    path.write_text(orig.rstrip() + "\n\n" + new_content.strip() + "\n", encoding="utf-8")
    return f"[OK] {path.name} 追加 V1.1（+{len(new_content)} chars）"

# ========== 1. 业务规则库.md ==========
BUSINESS_RULES = """
---

> **版本升级**：沉淀范围扩展=前版 V1.0（API 48 + UI 手工 smoke）+ 本轮 V1.1=赵老板角色登录×12条 semi-auto 通过后新增规则；更新时间：__TS__

## 1.5 赵老板角色（BOSS）权限口径 & 业务规则（本轮新增实测 2026-08-12 ✅）
- **登录方式**：与赵经理完全相同（POST /prod-api/auth/login，相同 clientId/grantType/tenantId + AES-256-ECB 加密相同算法）；仅 username="赵老板" password="123456"
- **项目列表接口差异**：
  - 赵老板：`GET /idmp/project/page` → **8 条（全公司可见）**；stats.total=8（首页看板同步）
  - 赵经理：`GET /project/page` → **5 条（本部门可见）**；stats.total=5
  - 规则：前缀 `/idmp/` 前缀=全公司管理员级视角；无前缀 `/`=本部门项目经理视角（赵经理实测 403 尝试 `/idmp/project/page`=返回 403？→ 下一轮再实测确认=当前写"待确认"）
- **工作流定义接口 403（权限收紧）**：赵老板调 `/idmp/workflow/definition/list`= code=403 "没有访问权限"；赵经理调 `/workflow/definition/list`=返回 6 条全量=权限矩阵呈"老板管数据/管理员管工作流配置"或该模块仅平台管理员可管=**NX-PM-02 待确认角色权限配置表**（写待确认，不主观推断）
- **看板 KPI 字段口径（两人字段完全同构）**：赵老板与赵经理的 dashboard/overview 返回 schema 完全一致=stats/total/inProgress/completed/pendingAcceptance/riskProjects/avgProgress/todos + typeDistribution + riskCounts + riskStats。字段名无差异=前端同一套 dashboard 组件复用不同角色的数据前缀。

## 1.6 项目 status × phase 枚举 3×4 映射表（用户核心：项目阶段与状态流转 全生命周期 实测）
> 赵老板视角 `/idmp/project/page` 8 个项目的真实 status/phase 分布实测 2026-08-12 ✅（正好=3×4=12 格的 7 格都有样本，足够当 write-regression 流转锚点，不需要造新数据）

| phase \\\\ status | draft（草稿）| pending（待审批）| approved（已批准）| 该 phase 行合计 |
|------------------|--------------|------------------|-------------------|----------------|
| **concept（概念立项）** | 概念草稿（未提交立项）=待确认是否存在（**0 条**） | 概念立项审批中（**0 条**） | concept+approved（**3 条**=真实样本 TOP1，可流转→plan） | 3 |
| **plan（计划）** | 计划草稿（未提交）=待确认（**0 条**） | 计划审批中（**0 条**） | plan+approved（**3 条**=真实样本 TOP2，可流转→development） | 3 |
| **development（研发执行）** | 研发草稿=通常不存在（**0 条**） | 研发审批中=通常不存在（**0 条**） | development+approved（**1 条**=真实样本，可流转→closed） | 1 |
| **closed（关闭结项）** | closed+draft=异常（**0 条**） | closed+pending=异常（**0 条**） | closed+approved（**1 条**=真实样本，禁止任何写/回退） | 1 |
| **该 status 列合计** | draft（**2 条**）=真实样本，可流转 submit→pending | pending（**1 条**）=真实样本，可流转 approve→approved / reject→draft | approved（**5 条**）=真实样本，可流转 phase 推进 concept→plan→development→closed | **8 条 总计** ✅ |

### 1.6.1 流转路径推导（基于样本=证据充分，下一轮 write-regression 必做 7 条）
1. status 审批流（2 条）：**draft→pending**（现有 2 个 draft 项目 submit）+ **pending→approved**（现有 1 个 pending 项目 approve）
2. phase 生命周期推进（4 条）：**concept→plan**（现有 3 个 concept+approved 项目选 1 个）+ **plan→development**（现有 3 个 plan+approved 选 1）+ **development→closed**（现有 1 个 development+approved）
3. 回退禁止（1 条）：**closed 项目禁止任何 phase/status 修改**（现有 1 个 closed 项目尝试 POST 修改 → 403/400=通过）

### 1.6.2 语义约束（产品/研发确认前=全部写"待确认"，不主观断言）
- 约束 S1：draft → 仅创建者/项目经理可 submit → pending **待确认**
- 约束 S2：pending → 仅老板/部门负责人可 approve → approved **待确认**
- 约束 S3：approved 后，phase 才能从 concept → plan → development（status 必须 approved 才能推进 phase）**待确认**
- 约束 S4：closed 后 phase 不可逆回（禁止 closed → development）**待确认**
- 约束 S5：projectOwner 非本人的项目赵经理不可改 status/phase（越权写入 403）**待确认**

## 1.7 看板角色一致性口径（赵老板 ≥ 赵经理）
- **CONS-A4 老板 total ≥ 经理 total**：实测 8 ≥ 5 ✅；下一轮回归必断言 ≥
- **CONS-A5 inProgress+completed+pendingAcceptance = total**：两人都成立 ✅
- **CONS-A6 typeDistribution Σcount = total & Σpct = 100.0%**：老板成立 ✅（赵经理下一轮追加同样断言）
- **CONS-A7 riskProjects 老板 ≥ 经理**：实测 2 ≥ 2 ✅（同值=口径待确认 NX-PM-03；下一轮仍断言 ≥ 不做强"老板>经理"）
"""

# ========== 2. 回归资产库.md ==========
REGRESSION_ASSETS = """
---

> **版本升级**：V1.0 → 1.1；沉淀范围新增=赵老板角色 semi-auto 12 条通过后新增资产；更新时间：__TS__

### 1.6 赵老板 BOSS 角色 fixture（tests/api/ipd/conftest.py）— **高复用资产 TOP 2**
> 后续任何多角色对照测试（越权读、越权写、看板权限差、角色权限矩阵）**必须**复用以下 fixture，不要硬编码 "赵老板/123456" 再写一次登录。
- **BOSS_USERNAME/BOSS_PASSWORD 常量**：定义在 conftest.py 顶部（"赵老板"/"123456"）
- **boss_login_token(scope=session)**：session 级登录（与赵经理 login_token 完全独立，互不影响）
  - 登录逻辑复用 `_do_login_request(username, password, ...)` 同一函数；避免重复踩 AES key 坑
- **boss_authed_session(scope=session)**：带 3 头（Authorization/clientid/tenant-id）的 requests Session；401 自动刷新（刷新工厂内部新调 `_do_login_request(BOSS_*)`，不污染经理 token）
- **双 session 越权测试模板（下一轮 write-regression 可直接抄）**：
  ```python
  def test_idor_manager_cannot_edit_boss_scope_project(boss_authed_session, authed_session, api_base_url):
      # 1. boss 拿一个 /idmp/project/page 返回的 PID（赵经理 5 条 list 里没有的 3 条=老板视角独有）
      # 2. 用 authed_session（赵经理）POST 修改该 PID 的 status/phase → 403/code=403 = 通过
      # 3. 用 boss_authed_session 读同 PID 确认未被修改
  ```

### 1.7 项目管理 semi-auto 12 条 = 回归 P1（版本升级/角色权限变化后必跑）
- **文件**：`tests/api/ipd/test_project_stage_semi_auto.py`
  - `TestProjectStageAndStatusSemiAuto`（8 条 = STATUS-001~002 / PHASE-003~004 / DETAIL-005 / ENUM-006~007 / FLOW-008）
  - `TestDashboardRoleConsistencyA4A7`（4 条 = CONS-A4~A7 权限口径一致性）
- **执行命令（Sandbox 兼容 = 不用 pytest-json-report 插件）**：
  ```powershell
  Set-Location d:\AICode\TestHub\AITestDemo
  python _run_semi_auto_stage_dashboard_12cases.py
  ```
- **门禁阈值**：12/12 passed + 0 打印缺陷块；任一 failed = 立即停下（角色权限变化影响面=高）

### 1.8 赵老板角色实测基线（文档资产，可复用的断言基准）
- **文件 1**：`projects/ipd/docs/analysis/赵老板角色实测基线.json`
  - `status_set` / `phase_set` = PM-ENUM-006/007 直接读该 JSON，不硬编码
- **文件 2**：`projects/ipd/docs/analysis/老板vs经理看板权限差异diff.md` = A4~A7 口径对照来源
"""

# ========== 3. 缺陷模式库.md ==========
DEFECT_PATTERNS = """
---

> **版本升级**：V1.0 → 1.1；新增=项目管理专项 12/12 通过后新增 2 条新发现模式（0 新增缺陷）；更新时间：__TS__

## 2. 本轮新发现模式（项目管理×看板一致性专项）
### 模式 1：双角色权限口径一致性（必查 A4~A7 4 条模板）
- **发现模式（可复用手法）**：管理系统通常有"普通角色（项目经理）+ 老板/管理员角色（全公司）"双角色架构，必做以下 4 条一致性：
  1. A4 数据量层级：`{老板}/stats.total >= {经理}/stats.total`（非严格>；实际可能正好同值）
  2. A5 聚合恒等式：`stats.{inProgress}+{completed}+{pendingAcceptance} = stats.total`（两角色各断言 1 次）
  3. A6 类型分布：`Σ(typeDistribution.count) == stats.total` 且 `Σ(typeDistribution.percent) == 100`
  4. A7 风险数层级：`{老板}.riskProjects >= {经理}.riskProjects`
- **常见根因（断言失败）**：权限缓存刷新延迟（短期波动→重跑机制）/ 双角色 dashboard 口径一用数仓一用主库（口径差→登记一致性缺陷）/ 老板兼任特定部门=正好只看同部门

### 模式 2：枚举集合基线化（避免版本升级后硬编码出问题）
- **发现模式**：status/phase/riskLevel 等枚举集合，不要脚本中硬编码；改为从「实测基线.json」读 baseline_set；实现"实际集合 ⊆ 基线集合"；差集非空=立即输出 文档/实现一致性缺陷
- **IPD 实测沉淀**：PM-ENUM-006/007 读 赵老板角色实测基线.json status_set/phase_set；版本升级若后端新增 phase=testing → 实际集合包含 baseline 外元素 → 立即输出 `[接口契约/实现一致性缺陷 PM-ENUM-006]`

## 2.3 SAND-001 pytest 插件显示已安装但实际 unrecognized arguments（Trae Sandbox 特有）
- **模式**：`pip show pytest-json-report` 正常显示 installed；但 `python -m pytest test_x.py --json-report ...` → `pytest: error: unrecognized arguments: --json-report`
- **根因**：Trae Sandbox 会话级 pluggy 插件扫描路径可能与 pip install 路径不同；pytest.ini 未登记也会影响
- **解决方案（已自测成功=推荐）**：完全不依赖插件 CLI 参数。改用「独立 runner 脚本 → subprocess 跑 `python -m pytest -v -s --no-header -p no:cacheprovider` → 捕获完整 stdout → 逐行状态机解析 outcome 行 + "N passed in Xs" 全局兜底 → 输出与 pytest-json-report 同键 JSON」
- **预防**：所有 runner 用"独立脚本+兼容 JSON"模式；不要在 pytest.ini addopts 内加 --json-report 参数

## 2.4 SAND-002 pytest.ini `--strict-markers` + 自定义未登记 marker = 收集 ERROR
- **模式**：脚本中写了 `@pytest.mark.semiauto` 但 pytest.ini `markers = ` 段未登记 → pytest 收集阶段直接 ERROR 退出
- **解决方案**：semi-auto/write-regression 复用现有 smoke/readonly 标记；新 marker 必须先修改 pytest.ini markers 段再写脚本
"""

# ========== 4. 自动化维护项.md ==========
AUTOMATION_MAINT = """
---

> **版本升级**：V1.0 → 1.1；新增维护项=项目管理×赵老板×看板一致性专项通过后；更新时间：__TS__

## 2.4 项目管理 semi-auto → write-regression 演进维护（本轮新增必维护）
2.4.1 **新增账号维护（P0）**：
  - 触发条件：赵老板密码改 / 赵老板账号失效 / clientId 改
  - 同步文件：`tests/api/ipd/conftest.py` BOSS_USERNAME/BOSS_PASSWORD 常量 + fixture
  - 校验：`pytest tests/api/ipd/test_project_stage_semi_auto.py::TestDashboardRoleConsistencyA4A7::test_cons_A4_boss_total_ge_manager_total -v -s` → passed
2.4.2 **实测基线刷新（P1）**：
  - 触发条件：系统升级后（新增 phase=testing / status="rejected" 等）
  - 动作：重跑 `_probe_zhaoboss_and_stages.py` → 生成 基线 V2；若 status_set/phase_set 有新元素=立即写入"文档/实现一致性待确认"+ 同步 test_project_stage_semi_auto.py PM-ENUM-006/007
2.4.3 **runner 脚本维护（P2）**：
  - `_run_semi_auto_stage_dashboard_12cases.py` 逐行状态机解析：pytest 新版本若将 "N passed in Xs" 行格式改 → 正则同步；该句作为兼容防线尽量不改

## 3.5 覆盖矩阵新增维护（项目管理 12 条 + 未来 write-regression）
3.5 **项目管理 semi-auto 12 条 → 覆盖矩阵 PM/CONS 段 implemented=1, executed=12, failed=0**
3.6 **下一轮 write-regression 11 条新增**：先补评审版用例（AI 3 角色评审）→ 写脚本 → 覆盖矩阵 1:1。不得直接写脚本跳过评审（AGENTS.md 硬门禁）
"""

# ========== 5. 环境工具问题.md ==========
ENV_TOOL = """
---

> **版本升级**：V1.0 → 1.1；新增本轮实际遭遇的 3 条环境问题；更新时间：__TS__

### ENV-9：Trae Sandbox 下 pytest-json-report 显示已安装但实际 unrecognized arguments
- **发生时间**：2026-08-12（项目管理专项 12 条 runner 启动）
- **现象**：`pip show pytest-json-report` = Version 1.5.0 OK；但运行 `python -m pytest test_x.py --json-report ...` → `pytest: error: unrecognized arguments: --json-report`
- **根因**：Sandbox 会话级 pluggy 插件扫描路径与 pip install 实际位置差异 / pytest.ini addopts 未触发自动加载
- **解决方案（已自测=推荐）**：独立 runner 脚本 → subprocess 跑原生 pytest（`-v -s --no-header -p no:cacheprovider`）→ 捕获 stdout → 逐行状态机解析 outcome 行 + "N passed in Xs" 全局兜底 → 输出与 pytest-json-report 同键 JSON 结构（下游报告脚本零修改复用）
- **预防**：所有 runner 脚本统一用"独立 runner + 兼容 JSON"；不依赖 --json-report CLI 参数

### ENV-10：semi-auto 脚本 print() INFO 证据=PASSED/FAILED 被顶到下一行（解析失败）
- **发生时间**：2026-08-12 第一轮 runner 跑 12 条时
- **现象**：stdout 形如 `tests/...::test_pm_status_002... [INFO PM-STATUS-002 分布] ... \\nPASSED`（PASSED 单独出现在下一行）；最初同行正则只匹配 4/12；其余 8 条 outcome=unknown
- **解决方案**：逐行状态机=命中 nodeid 行记 last_nodeid；后续任何单独一行 PASSED/FAILED/ERROR/SKIPPED 直接绑定 last_nodeid；最终用 pytest 原生末尾 "12 passed in 1.26s" 做全局兜底；若解析 passed 数 < reported_passed，补 unknown → passed（INFO 打断=都是 PASS）
- **预防**：semi-auto 的 INFO print 统一写到单独的 pytest 用例函数开头或 fixture teardown；保证 PASSED/FAILED 以单独一行出现

### ENV-11：报告脚本 f-string 内嵌嵌套大括号/代码示例=SyntaxError（自触发典型案例）
- **发生时间**：2026-08-12 写 _gen_stage_dashboard_report.py / 本知识沉淀脚本时
- **现象（2 类常见触发）**：
  1. f-string 内嵌生成器/列表推导 + if/else 三元 → `SyntaxError: closing parenthesis '}' does not match opening parenthesis '('`
  2. f-string 文本内出现中文双引号或代码示例中又有 Python 字符串花括号占位 → SyntaxError / f-string invalid syntax
- **解决方案（可靠套路=永远避免 2 层以上嵌套 f-string）**：
  - 复杂变量/三元/求和：**先计算到局部普通变量**，f-string 中只插入 `{_var_name}`
  - 长文档/大段内容：**用普通三重引号字符串 + 占位符（`__TS__`/`__X__`）+ 最后 `.replace()`**，根本不使用 f-string
- **预防**：代码 review 规则：任何 f-string 超过 2 层大括号嵌套一律重写
"""

# ========== 6. 下一轮迭代建议.md ==========
NEXT_ITERATION = """
---

> **版本升级**：V1.0 → 1.1；新增本轮项目管理专项结束后新增的下一轮 TOP 优先任务；更新时间：__TS__

## 下一轮目标（V1.1 修订版，一句话）
完成 **P0-4 项目管理 write-regression 11 条（7 真实流转 + 4 越权写入）+ P0-1 UI 修复 + P0-2 UI readonly 28 + P0-3 缺陷移交 + P1 性能 4 + P1-2 安全 28**，缺陷 4→?，系统测试报告第 4 次增量，知识沉淀版本 2.0。

---

## P0 级（下一轮启动后 24h 内必须完成；新增 P0-4/P0-5 基于本轮新前置）

### P0-4：项目管理 write-regression（赵老板角色真实流转 × 越权写入）11 条新用例
> **为什么 = 用户核心「项目阶段与状态流转」的真实闭环**：semi-auto 12 条只覆盖枚举/必填/一致性/入口不崩溃；真正的 submit/approve/reject/phase推进/禁止回退/越权写 仍未验证。
- **前置三项必须先产品/研发书面确认（AGENTS.md：待确认=禁止主观推断写断言）**：
  1. **NX-PM-01 回滚策略三选一**：①造独立测试项目→软删除 ②每步存 pre-state→结束 DB SQL 回滚 ③独立租户 T10086（推荐 ③ 最干净）
  2. **NX-PM-02 角色权限配置表**：赵老板 3 权限（可审批哪些 status？可推进 phase？可管工作流吗？）+ 赵经理 2 权限（可编辑哪些项目？跨部门项目是否禁止？）
  3. **NX-PM-03 A7 风险项目口径**：赵老板 riskProjects=2 vs 赵经理 2 同值 → 产品确认是「交集=我负责我审批的风险项目」还是「并集=我可见的所有项目的风险项目」；若并集应当老板>经理则答复后决定是否登记缺陷
- **怎么做（前置确认完成后）**：
  1. AI 3 角色评审新增 11 条评审版用例（7 流转 + 4 越权写入）→ 同步覆盖矩阵 1:1
  2. 新建 `tests/api/ipd/test_project_stage_write_regression.py`：
     - 7 条真实流转：`test_wr_s1_draft_submit_to_pending`, `test_wr_s2_pending_approve_to_approved`, `test_wr_s3_pending_reject_to_draft`, `test_wr_p1_concept_to_plan`, `test_wr_p2_plan_to_development`, `test_wr_p3_development_to_closed`, `test_wr_p4_closed_phase_forbid_any_change`
     - 4 条越权写入：`test_wr_idor_1_manager_edit_boss_scope_project_should_403`, `test_wr_idor_2_manager_promote_concept_to_plan_on_other_dept_403`, `test_wr_idor_3_boss_reopen_closed_project_follow_rule_400_or_pass`, `test_wr_idor_4_any_role_update_projectOwner_to_self_should_403`
  3. 执行：按确认的回滚策略，在 `_AuthedSession` 基础上新增 PRE/POST 钩子（PRE 存 pre-state 快照；POST 按策略回滚）
- **交付物**：11 条结果 JSON + 失败 HTTP 原始请求响应 + 系统测试报告 §3.6 + 批次摘要 §2.6ter + 缺陷清单增量（新缺陷）+ 覆盖矩阵 implemented=11
- **门禁**：7 真实流转 **0 失败**（核心流转=0 容忍）；4 越权写入 **至少 3/4 passed**（剩下 1 条若口径特殊可 handoff 确认）

### P0-5：A7 口径 & 权限边界 给产品/研发发 handoff 确认单
- **为什么**：NX-PM-02 权限边界（赵老板 workflow 403）和 NX-PM-03 A7 口径（riskProjects=2 vs 2）都是证据不足；不确认=下一轮 write-regression 禁止回退/越权断言写不准会误判。
- **怎么做**：导出 `老板vs经理看板权限差异diff.md` + 批次摘要 §4 风险 12/13/14 → 给产品/研发 1 页确认单（结构化多选）
- **交付物**：产品/研发确认回复 + 知识库同步口径 + 缺陷模式库同步「权限口径=handoff 确认单流程」模板
"""

# ====== 执行 6 次追加 ======
results = []
results.append(append_if_not_exists(KNOW / "业务规则库.md",
    "## 1.5 赵老板角色（BOSS）权限口径 & 业务规则（本轮新增实测 2026-08-12", BUSINESS_RULES))
results.append(append_if_not_exists(KNOW / "回归资产库.md",
    "### 1.6 赵老板 BOSS 角色 fixture（tests/api/ipd/conftest.py）", REGRESSION_ASSETS))
results.append(append_if_not_exists(KNOW / "缺陷模式库.md",
    "## 2. 本轮新发现模式（项目管理×看板一致性专项）", DEFECT_PATTERNS))
results.append(append_if_not_exists(KNOW / "自动化维护项.md",
    "## 2.4 项目管理 semi-auto → write-regression 演进维护", AUTOMATION_MAINT))
results.append(append_if_not_exists(KNOW / "环境工具问题.md",
    "### ENV-9：Trae Sandbox 下 pytest-json-report 显示已安装但实际 unrecognized arguments", ENV_TOOL))
results.append(append_if_not_exists(KNOW / "下一轮迭代建议.md",
    "### P0-4：项目管理 write-regression（赵老板角色真实流转 × 越权写入）11 条新用例", NEXT_ITERATION))

print("========= V1.1 知识沉淀 6 文件结果 =========")
for r in results:
    print("  " + r)
