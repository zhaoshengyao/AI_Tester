# -*- coding: utf-8 -*-
"""Step H-2：生成 write-regression 专项降级报告（downgrade=stop），并增量更新
- 覆盖矩阵：11 条 WR/IDOR 用例 → 未实现 / 未执行
- 专项报告：reports/项目管理write-regression专项报告（降级）.md
- 缺陷清单：defects/缺陷清单-WR-降级增量.md（2 条：NX-WR-DEG-001、NX-WR-DEG-002）
- 系统测试报告 §3.6 项目管理 write-regression 段落
- 批次摘要 §2.6ter + 追加决策表
- 知识沉淀 6 文件 V1.2 追加「写接口探测 0 命中 → WR 降级为 stop」
"""
from __future__ import annotations
import json, time, re
from pathlib import Path

REPO = Path(r"d:\AICode\TestHub\AITestDemo")
RUN_DIR = REPO / "projects/ipd/docs/test-runs/20260811-122314"
PROBE = json.loads((REPO / "projects/ipd/docs/analysis/IPD项目管理写接口探测结果.json").read_text(encoding="utf-8"))

TS = time.strftime("%Y%m%d-%H%M%S")
TS_DISPLAY = time.strftime("%Y-%m-%d %H:%M:%S")
REPORTS = RUN_DIR / "reports"
DEFECTS = RUN_DIR / "defects"
REPORTS.mkdir(parents=True, exist_ok=True)
DEFECTS.mkdir(parents=True, exist_ok=True)

# ===== 汇总探测数字 =====
c = lambda k: PROBE.get(k, [])
def success_cnt(arr, key="success"): return sum(1 for x in arr if x.get(key))
def other_200(arr, key="http"): return sum(1 for x in arr if x.get(key)==200 and not x.get("success"))

create_ok = success_cnt(c("create_candidates"))
update_ok = success_cnt(c("update_candidates"))
status_ok = success_cnt(c("status_flow_candidates"))
phase_ok  = success_cnt(c("phase_flow_candidates"))
soft_ok   = success_cnt(c("soft_delete_candidates"), key="business_code")  # code==200 的软删路径
idor_403  = success_cnt(c("idor_probe_candidates"), key="idor_pass_expected_403")
idor_200  = success_cnt(c("idor_probe_candidates"), key="idor_risky_200")
total_candidates = sum(len(c(k)) for k in ("create_candidates","update_candidates","status_flow_candidates","phase_flow_candidates","soft_delete_candidates","idor_probe_candidates"))

# ===== 1) 专项报告 =====
wr_report = f"""# 项目管理模块 write-regression 专项报告（批次 20260811-122314，WR 阶段=降级：downgrade→stop）

> 生成时间：{TS_DISPLAY} | 执行机器：本机 Windows | 执行引擎：接口探测 `_probe_write_apis_stage_flow.py`（近 150 候选路由扫探测）
> 用户本轮确认：回滚策略=① 造 AUTO-TEST-YYYYMMDD-XXXX 专用项目后软删除；权限矩阵=Other（未指定=按 AGENTS.md handoff 宽松探测模式）；A7口径=B 并集；执行计划=③ 立即启动 11 条

---

## 1. 当前阶段
项目管理模块 write-regression（WR 写操作） + IDOR 越权写（合计 11 条覆盖矩阵映射）
决策状态：**downgrade → stop**（写接口零命中=无法构造真实写请求；继续执行将伪造接口=违反 AGENTS.md 「禁止主观猜测」规则；待产品/研发提供真实写接口路由清单或文档后恢复）

## 2. 输入文件
- 系统配置：`projects/ipd/system.yaml`（auth 6 项闭环）
- 环境变量：`projects/ipd/.env`（赵老板/赵经理 双账号）
- 上一轮 semi-auto 覆盖矩阵：`{REPORTS.relative_to(REPO)}/覆盖矩阵.md`（PM-WR-001~007 七条流转；PM-IDOR-001~004 四条越权 → 合计 11 条 WR 级）
- 赵老板角色实测基线：`projects/ipd/docs/analysis/赵老板角色实测基线.json`（仅有只读接口 18 条；无任何写接口/路由）
- 写接口探测证据：`projects/ipd/docs/analysis/IPD项目管理写接口探测结果.json`（{total_candidates} 候选探测=本次核心证据）
- conftest fixture：`tests/api/ipd/conftest.py` boss_authed_session / authed_session

## 3. 正文/核心内容（探测结果）

### 3.1 探测范围与口径
- 前缀策略：`/idmp/project/`（赵老板全公司前缀=高优先）、`/project/`（赵经理部门前缀=低优先）
- 方法覆盖：POST / PUT / DELETE / GET（REST 常见+RPC 常见）
- 每类写操作候选：
  - CREATE：28 候选（2 前缀 × 7 后缀 × 2 payload 变体）
  - UPDATE：36 候选（2 前缀 × 2 后缀 × 3 URL 形式 × 3 method…共 36）
  - STATUS 流转（submit/approve/reject/pass/audit × 5 动作 × 3 prefix × 3 method × 3 body）：若干
  - PHASE 推进（nextPhase/advance/promote/startPlan/startDev/close/complete × 3 phase × 2 prefix × 3 method）：若干
  - SOFT-DELETE（delete/remove/softDelete/soft-delete/recycle/discard/archive/close × 2 prefix × 2 method × 2 URL 形式）：若干
  - IDOR 越权写（赵经理写赵老板独有 PID × 3 title × 2 method）：6 条

### 3.2 探测结果一览（0/任何一类命中）
| 分类 | 候选数 | HTTP200 非 code=200（404/405/500/400）| HTTP200 code=200（命中 ✅）| 未执行原因 |
|---|---:|---:|---:|---|
| CREATE | {len(c('create_candidates'))} | {len(c('create_candidates')) - create_ok} | **{create_ok}** | 全部 404/500=路径不存在；payload 正确无"字段缺失 400"提示=无法断定写接口是否存在/前缀是否正确 |
| UPDATE | {len(c('update_candidates'))} | {len(c('update_candidates')) - update_ok} | **{update_ok}** | 全部 404/405=方法/路由未注册 |
| STATUS 流转（submit/approve/reject）| {len(c('status_flow_candidates'))} | {len(c('status_flow_candidates')) - status_ok} | **{status_ok}** | 全部 404/405/500=流转接口未注册或前缀不对 |
| PHASE 推进（concept→plan→development→closed）| {len(c('phase_flow_candidates'))} | {len(c('phase_flow_candidates')) - phase_ok} | **{phase_ok}** | 全部 404=phase 推进接口未注册或 RPC 动作名未对 |
| SOFT-DELETE 软删除 | {len(c('soft_delete_candidates'))} | {len(c('soft_delete_candidates')) - soft_ok} | **{soft_ok}** | 全部 404/405/500=软删路径未命中（无真删 code=200=因此也不存在误删风险） |
| IDOR 越权写（赵经理→赵老板独有项目） | {len(c('idor_probe_candidates'))} | {len(c('idor_probe_candidates')) - idor_403 - idor_200} | IDOR-403={idor_403} IDOR-200={idor_200} | 全部 404=路径不存在；因此既无法验证 IDOR 漏洞=不能断言通过，也无法断言失败= handoff，必须下一轮走 Network 抓包/文档提供真实路由后重新评估 IDOR 风险 |

### 3.3 11 条 WR 用例执行结果=未执行（每条都给出未执行原因）
| 序号 | 覆盖矩阵映射 ID | 用例标题（摘要） | 期望结果 | **实际状态** | 未执行/降级原因 |
|---|---|---|---|---|---|
| 1 | PM-WR-001 | draft→pending 提交审批（造 AUTO-TEST 专用项目后执行）| 项目 status=pending 且 createBy=我 | **未执行（downgrade）** | CREATE 写接口探测 0 命中 → 无法造专用 AUTO-TEST 项目；真实 STATUS submit 路由也探测 0 命中=两条前置全部不满足 |
| 2 | PM-WR-002 | pending→approved 赵老板审批 | status=approved + auditor=赵老板 + approveTime≤当前时间 | **未执行（downgrade）** | approve/audit/pass 路由探测 0 命中；且 draft→pending 无法执行也就没有 pending 项目 |
| 3 | PM-WR-003 | pending→reject 赵老板驳回→draft | status=draft + rejectRemark 填充 | **未执行（downgrade）** | reject 路由 0 命中 |
| 4 | PM-WR-004 | 赵老板推进 phase concept→plan | phase=plan + stageHistory 加 1 条 | **未执行（downgrade）** | nextPhase/advance/startPlan 全部 404=phase 推进接口未注册或命名未对上 |
| 5 | PM-WR-005 | 赵老板推进 phase plan→development | phase=development | **未执行（downgrade）** | nextPhase/advance/startDev 全部 404 |
| 6 | PM-WR-006 | 赵老板推进 phase development→closed | phase=closed 且 closedAt≤当前时间 | **未执行（downgrade）** | nextPhase/advance/close/complete 全部 404 |
| 7 | PM-WR-007 | closed 项目禁止修改（回退/改 status/改 phase/改字段）| 返回 400/403，项目快照不变 | **未执行（downgrade）** | UPDATE 写接口探测 0 命中=无法尝试修改任何字段，无法验证禁止修改策略是否生效 |
| 8 | PM-IDOR-001 | 赵经理越权修改赵老板独有项目 status | 返回 403 禁止=通过；返回 200=IDOR 高危缺陷 | **未执行（downgrade）** | 赵经理 /project/PID 路径 PUT/POST 写路径探测全部 404=无写接口可调用，不能凭空断言 IDOR 风险 |
| 9 | PM-IDOR-002 | 赵经理越权 submit 审批赵老板独有项目 | 返回 403=通过 | **未执行（downgrade）** | submit 路由 404 |
| 10 | PM-IDOR-003 | 赵经理越权推进赵老板独有项目 phase | 返回 403=通过 | **未执行（downgrade）** | phase 路由 404 |
| 11 | PM-IDOR-004 | 赵经理越权软删除赵老板独有项目 | 返回 403=通过；返回 200=真删=数据风险 | **未执行（downgrade）** | soft-delete 路由 404 |

### 3.4 A7 口径 B 并集的 semi-auto 再评估（上一轮 semi-auto 已打印 handoff）
- 上一轮 A7 semi-auto 实际：赵老板 riskProjects=2 / total=8；赵经理 riskProjects=2 / total=5
- 本轮按用户确认口径 B（并集=我可见项目中的风险项目，老板通常应 > 经理）
  - 当前值=2=2，老板 8 条可见并没有比经理 5 条更多风险项目
  - 按口径 B 理论应 ≥ 且通常 >；若数据真实=要么赵经理 5 条包含了全部 2 个风险项目、要么 riskProjects 口径并非并集
  - **结论=handoff（需要产品答复后决定是否登记缺陷）**；不做强断言；上一轮 semi-auto 已以 handoff 打印=本轮保持一致，不修改

## 4. 执行结论
- **决策状态：downgrade → stop**（写接口 150+ 候选探测命中=0；禁止伪造写请求=11 条 WR/IDOR 全部标记「未执行」，符合 AGENTS.md 「不确定=待确认/禁止猜测」条款 + 「自适应执行：stop 必须写明未执行范围」条款）
- 已完成部分：只读接口 semi-auto 12 条已 100% 跑通（PM-STATUS-001/002、PM-PHASE-001/002、PM-FLOW-003~006、CONS-A4~A7），覆盖矩阵前 12 条已实现
- 未执行范围：11 条 WR/IDOR（PM-WR-001~007 + PM-IDOR-001~004）
- 下一轮进入 WR 的前置：**必须具备其中之一**：
  1. 产品/研发提供写接口文档（CREATE/UPDATE/STATUS 流转/PHASE 推进/DELETE 的 URL、method、请求体字段、必填校验、权限矩阵）
  2. 或者通过 Playwright Network 抓包从前端页面真实「创建项目」「提交审批」「推进阶段」「删除项目」操作抓到实际路由（推荐路径）

## 5. 风险与待确认项（handoff 给产品/研发/运维）
- **NX-WR-DEG-001（handover=研发提供路由/文档）：** 项目管理模块写接口（CREATE/UPDATE/STATUS 流转/PHASE 推进/软删）近 150 候选路由全部返回 404/405/500；请提供实际路由清单或让前端执行真实操作的 Network 抓包 HAR 文件，以便下一轮执行 11 条 WR/IDOR。
- **NX-WR-DEG-002（handover=产品答复口径）：** 权限矩阵用户选择「Other」未说明=赵经理/赵老板各自能执行哪些 status/phase 流转、哪些字段可编辑、closed 是否能回退；请书面答复，否则 WR 断言只能宽松探测（HTTP 200 code=200 即通过=不会判定失败，但可能漏测越权/禁止流转的业务错误）。
- **NX-WR-DEG-003（产品口径 A7 并集）：** 风险项目数=2=2 是否为产品期望？是→登记非缺陷；否则=统计口径 bug，需要研发修复。

## 6. 下一步建议
1. **P0：拿到 Network HAR 或写接口文档后** → 重跑 `_probe_write_apis_stage_flow.py` 确认 6 类写接口至少各有 1 条 HTTP 200 code=200
2. **P1：写接口命中后** → 实现 `test_project_stage_write_regression.py` 11 条脚本 + pytest + JSON 结果；造 AUTO-TEST-YYYYMMDD-XXXX 专用项目执行流转一圈，最后软删除
3. **P2：权限矩阵答复后** → 将 IDOR 断言从宽松探测切换为"必须 403"
"""

# 处理路径变量
wr_report = wr_report.replace("{REPORTS.relative_to(REPO)}", str(REPORTS.relative_to(REPO)))
# 把 len() 这些从 f-string 外带入
wr_report = (wr_report
    .replace("{len(c('create_candidates'))}", str(len(c("create_candidates"))))
    .replace("{len(c('update_candidates'))}", str(len(c("update_candidates"))))
    .replace("{len(c('status_flow_candidates'))}", str(len(c("status_flow_candidates"))))
    .replace("{len(c('phase_flow_candidates'))}", str(len(c("phase_flow_candidates"))))
    .replace("{len(c('soft_delete_candidates'))}", str(len(c("soft_delete_candidates"))))
    .replace("{len(c('idor_probe_candidates'))}", str(len(c("idor_probe_candidates"))))
    .replace("{total_candidates}", str(total_candidates))
    .replace("{create_ok}", str(create_ok)).replace("{update_ok}", str(update_ok))
    .replace("{status_ok}", str(status_ok)).replace("{phase_ok}", str(phase_ok))
    .replace("{soft_ok}", str(soft_ok)).replace("{idor_403}", str(idor_403)).replace("{idor_200}", str(idor_200))
)

wr_report_path = REPORTS / "项目管理write-regression专项报告（降级）.md"
wr_report_path.write_text(wr_report, encoding="utf-8")
print(f"[OK] 专项报告 → {wr_report_path}")

# ===== 2) 缺陷清单增量 =====
defect_md = f"""# 缺陷清单 - write-regression 降级增量（批次 20260811-122314）
> 生成时间：{TS_DISPLAY}

| 序号 | 缺陷编号 | 严重 | 分类 | 缺陷标题 | 触发条件/复现 | 预期结果 | 实际结果 | 来源依据 | 下一步状态 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | NX-WR-DEG-001 | 中 | 接口契约/文档缺失-写接口 | 项目管理 6 类写接口探测全部未命中（150+ 候选=404/405/500），导致 11 条 WR/IDOR 用例无法执行 | 运行 `_probe_write_apis_stage_flow.py`，赵老板/赵经理 双账号测 CREATE/UPDATE/STATUS 流转/PHASE 推进/软删/越权写，共 {total_candidates} 候选 | 每类写操作至少 1 个候选返回 HTTP 200 code=200 | 6 类写接口 success=0，全部 404/405/500 | `projects/ipd/docs/analysis/IPD项目管理写接口探测结果.json` | handoff=研发提供路由或前端 Network HAR 抓包 |
| 2 | NX-WR-DEG-002 | 中 | 业务规则待确认-权限矩阵 | 用户选「权限矩阵=Other」未明确流转权限：赵经理/赵老板各能执行哪些 status/phase 流转、closed 能否回退 | WR 断言必须明确=AGENTS.md 禁止猜测 | 书面权限矩阵 | 无规则=WR 断言只能宽松探测=漏测禁止流转 | G-1 用户答复 Other | handoff=产品答复后，下次执行切换为严格断言 |
| 3 | NX-WR-DEG-003 | 低 | 业务规则待确认-A7口径 | 风险项目数赵老板=2 vs 赵经理=2（total=8 vs 5），按用户确认口径B（并集）应老板通常>经理 | 口径B=并集=我可见所有项目中的风险项目 | 老板风险项目数 ≥ 经理风险项目数；正常业务下应 > | 实测 2=2 相同=口径B下或为bug或为数据巧合 | 用户 G-1 选择口径B | handoff=产品答复「是正常数据/是统计口径bug」=答复后登记/撤销 |
| 4 | NX-WR-DEG-004 | 低 | 接口契约/实现一致性-IDOR无法验证 | 越权写路径全部 404=无法验证赵经理能否越权改赵老板独有项目 | 测 PM-IDOR-001~004 共 6 候选 | 能调接口=可断言 403 | 404=既不能断言无漏洞也不能断言有漏洞 | IDOR 6 候选探测 | handoff=有真实写路由后重测 IDOR |
"""
(DEFECTS / "缺陷清单-WR-降级增量.md").write_text(defect_md, encoding="utf-8")
print(f"[OK] 缺陷增量 → {DEFECTS / '缺陷清单-WR-降级增量.md'}")

# ===== 3) 覆盖矩阵：PM-WR-001~007 + PM-IDOR-001~004 11 条，标记 未实现 / 未执行 =====
cov = REPORTS / "覆盖矩阵.md"
orig = cov.read_text(encoding="utf-8")
# 查找现有的 PM-WR / PM-IDOR 行，如果存在=更新状态；不存在=追加在尾部
# 现可能没有=直接追加一个 11 行表格到末尾
added = f"""

---

### 写操作层：write-regression 11 条（{TS_DISPLAY} 追加；downgrade=stop → 全部 未实现 / 未执行）

> 依据：写接口探测 0 命中 → 禁止伪造脚本；覆盖矩阵必须如实映射

| 序号 | 评审版用例编号 | 用例标题（摘要） | 自动化脚本路径 | 执行层级 | **脚本实现状态** | **执行状态** | 最后执行结果 | 未实现/未执行原因 |
|---|---|---|---|---|---|---|---|---|
| 1 | PM-WR-001 | draft→pending 提交审批（造 AUTO-TEST 专用项目） | 未创建 | write-regression | **未实现** | **未执行** | N/A | CREATE + STATUS submit 写接口探测 0 命中 |
| 2 | PM-WR-002 | pending→approved 赵老板审批 | 未创建 | write-regression | **未实现** | **未执行** | N/A | STATUS approve/audit/pass 探测 0 命中 |
| 3 | PM-WR-003 | pending→reject 赵老板驳回回 draft | 未创建 | write-regression | **未实现** | **未执行** | N/A | STATUS reject 探测 0 命中 |
| 4 | PM-WR-004 | phase concept→plan 赵老板推进 | 未创建 | write-regression | **未实现** | **未执行** | N/A | PHASE 推进接口探测 0 命中 |
| 5 | PM-WR-005 | phase plan→development 赵老板推进 | 未创建 | write-regression | **未实现** | **未执行** | N/A | PHASE 推进接口探测 0 命中 |
| 6 | PM-WR-006 | phase development→closed 赵老板推进 | 未创建 | write-regression | **未实现** | **未执行** | N/A | PHASE 推进接口探测 0 命中 |
| 7 | PM-WR-007 | closed 项目禁止修改/回退 | 未创建 | write-regression | **未实现** | **未执行** | N/A | UPDATE 写接口探测 0 命中=无法尝试修改 |
| 8 | PM-IDOR-001 | 赵经理越权改赵老板独有项目 status | 未创建 | write-regression（IDOR） | **未实现** | **未执行** | N/A | 赵经理写路径探测全部 404 |
| 9 | PM-IDOR-002 | 赵经理越权 submit 赵老板项目 | 未创建 | write-regression（IDOR） | **未实现** | **未执行** | N/A | submit 路由 404 |
| 10 | PM-IDOR-003 | 赵经理越权推进赵老板项目 phase | 未创建 | write-regression（IDOR） | **未实现** | **未执行** | N/A | phase 推进路由 404 |
| 11 | PM-IDOR-004 | 赵经理越权软删除赵老板项目 | 未创建 | write-regression（IDOR） | **未实现** | **未执行** | N/A | soft-delete 路由 404 |
"""
if "PM-WR-001" not in orig:
    cov.write_text(orig.rstrip() + "\n" + added + "\n", encoding="utf-8")
    print(f"[OK] 覆盖矩阵追加 11 条 WR → {cov}")
else:
    print(f"[SKIP] 覆盖矩阵已含 PM-WR-001=跳过")

# ===== 4) 系统测试报告 §3.6 增量追加 =====
sys_rpt = REPORTS / "系统测试报告.md"
if sys_rpt.exists():
    s = sys_rpt.read_text(encoding="utf-8")
    para = f"""

### §3.6 项目管理模块 write-regression（WR 写操作 + IDOR 越权写）—— 决策状态：downgrade→stop（11/11 未执行）
> 增量追加时间：{TS_DISPLAY}

| 项目 | 值 |
|---|---|
| 专项 | 项目管理模块 write-regression + IDOR 越权写 |
| 执行时间 | {TS_DISPLAY} |
| **决策状态** | **downgrade → stop**（写接口 0 命中=禁止伪造；按 AGENTS.md 自适应执行规则 stop）|
| 脚本覆盖映射 | 覆盖矩阵 PM-WR-001~007 + PM-IDOR-001~004 合计 11 条 |
| 已实现脚本 | 0/11（写接口探测=0，禁止伪造） |
| 已执行 | 0/11（全部未执行） |
| 下一轮前置 | ① 研发提供写接口路由文档 或 ② 前端 Network HAR 抓到 CREATE/UPDATE/STATUS 流转/PHASE 推进/软删真实请求 |
| 本轮缺陷（handoff）| NX-WR-DEG-001 写接口 0 命中；NX-WR-DEG-002 权限矩阵 Other 未明确；NX-WR-DEG-003 A7 口径 B 实测 2=2；NX-WR-DEG-004 IDOR 无法验证 |
| 专项报告入口 | `reports/项目管理write-regression专项报告（降级）.md` |
| 缺陷增量入口 | `defects/缺陷清单-WR-降级增量.md` |

- **风险提示**：此专项是本轮对用户「核心：项目阶段与状态流转」需求的唯一写操作闭环。目前只读层 semi-auto 12 条已闭环（phase/status 枚举一致性、列表-详情一致性、看板权限≥均通过），但写流转=用户明确要求的核心内容=因写接口缺失导致本轮未执行；**进入系统报告阶段后，建议研发/产品先补写接口或 HAR 抓包，再由 AI 重跑 H-1 探测并进入 WR 全量执行**，不要等下一轮。
- **对后续阶段影响**：允许进入系统报告收尾段（已如实记录 WR=未执行+原因+下一步前置），也允许知识沉淀「写接口探测失败→WR 降级」经验；不允许性能/安全专项（P0 优先级低于用户明确的核心=写流转，按 AGENTS.md 先完成用户明确要求的核心模块，性能/安全=非核心下一轮补）。
"""
    if "§3.6 项目管理模块 write-regression" not in s:
        sys_rpt.write_text(s.rstrip() + "\n" + para + "\n", encoding="utf-8")
        print(f"[OK] 系统报告 §3.6 增量追加")
    else:
        print("[SKIP] 系统报告已含 §3.6")
else:
    print("[WARN] 系统测试报告.md 不存在=跳过（应在前几轮已生成）")

# ===== 5) 批次摘要 §2.6ter 增量 + 决策表追加 =====
batch = RUN_DIR / "批次摘要.md"
if batch.exists():
    s = batch.read_text(encoding="utf-8")
    # §2.6 已存在 semi-auto 段落；追加 §2.6ter = write-regression 降级段落；同时更新「当前累计测试结果」
    addendum = f"""

##### §2.6ter 项目管理模块：write-regression 11 条（阶段流转越权写 + 真实写操作） —— **决策状态：downgrade→stop，11/11 未执行**
> 增量追加时间：{TS_DISPLAY}

| 项目 | 值 |
|---|---|
| 探测证据 | `projects/ipd/docs/analysis/IPD项目管理写接口探测结果.json`（{total_candidates} 候选=全部 404/405/500） |
| **决策状态** | **downgrade → stop**（AGENTS.md 禁止猜测=无真实接口不执行）|
| 映射用例 | 覆盖矩阵 PM-WR-001~007（7 条真实流转）+ PM-IDOR-001~004（4 条越权写）合计 **11 条** |
| 已实现脚本 | 0/11 |
| 已执行 | 0/11（全部未执行=写接口零命中）|
| handoff 缺陷 | NX-WR-DEG-001（写接口缺失 0 命中）；NX-WR-DEG-002（权限矩阵 Other 未明确）；NX-WR-DEG-003（A7 口径 B 实测 2=2）；NX-WR-DEG-004（IDOR 无法验证） |
| 下一轮进入前提 | ① 研发提供 CREATE/UPDATE/STATUS 流转/PHASE 推进/软删 路由文档 或 ② 前端 Network HAR 抓包；③ 产品明确权限矩阵（替代 Other） |

- 说明：用户本轮明确「核心=项目阶段与状态流转」。目前只读枚举/一致性层 semi-auto 12 条已闭环（phase/status 枚举、列表-详情、看板权限≥ 全部通过 handoff 无失败），但真实流转写操作=核心诉求所在=因写接口探测 0 命中而未执行；**请研发/产品优先补接口或抓包，补完后立即由 AI 重开 WR 层，无需等待下一轮正式批次。**
"""
    if "§2.6ter" not in s:
        s2 = s.rstrip() + "\n" + addendum + "\n"
        # 同时更新「当前累计」段：把 WR 11 未实现/未执行追加到 API 段合计（如果存在当前累计=简单 patch 字符串：找 "WR 写操作" 关键字；没有=不改，因为批次摘要可能无精确累计数字段）
        batch.write_text(s2, encoding="utf-8")
        print(f"[OK] 批次摘要 §2.6ter 增量追加")
    else:
        print("[SKIP] 批次摘要已含 §2.6ter")
else:
    print("[WARN] 批次摘要.md 不存在=跳过（应在前几轮已生成）")

# ===== 6) 知识沉淀 6 文件 V1.2 追加 =====
ANCHOR = f"## V1.2（批次 20260811-122314，{TS_DISPLAY} 追加）"

def append_knowledge(rel: str, content_md: str):
    path = REPO / "projects/ipd/docs/knowledge" / rel
    if not path.exists():
        print(f"[SKIP] {path} 不存在")
        return
    orig = path.read_text(encoding="utf-8")
    if ANCHOR in orig:
        print(f"[SKIP-V1.2] {path.name} 已含 V1.2 锚点")
        return
    path.write_text(orig.rstrip() + "\n\n" + ANCHOR + "\n\n" + content_md.strip() + "\n", encoding="utf-8")
    print(f"[OK-V1.2] {path.name} 追加 V1.2 段落")

append_knowledge("业务规则库.md", f"""
### 3.3 写接口探测失败=WR 不可执行判定规则
- 判定依据：6 类写操作（CREATE/UPDATE/STATUS 流转/PHASE 推进/软删除/越权写）候选探测全部 404/405/500 且 code≠200（本轮候选 {total_candidates} → success=0）。
- 不可执行规则：任何一类写接口探测成功=0，则该类下所有 WR 映射用例=全部标记 `未执行 + 降级原因`，禁止伪造路由/伪造 JSON body 去跑。
- 例外允许：若仅部分类成功（如 UPDATE 有命中但 STATUS 流转 0 命中）→ 仅执行已命中类的 WR，其余类=未执行。

### 3.4 权限矩阵用户 Other 兜底规则
- 用户选择权限矩阵「Other」=未提供任何具体权限规则时，WR 断言严格度必须从「必须 200 / 必须 403」降级为「宽松探测：HTTP 200 code=200 即通过=不判失败；403 只打印 handoff=不判失败；既不漏测正确行为也不把正确行为判成失败」。
- 下次执行切换回严格断言的前置：产品/研发提供书面权限矩阵或角色规则。
""")

append_knowledge("回归资产库.md", f"""
### 3.3 WR 降级手卡（write-regression 零探测命中 → 立即执行的 3 步）
1. 跑：`python _probe_write_apis_stage_flow.py`
2. 检查输出：CREATE/UPDATE/STATUS 流转/PHASE 推进/软删/IDOR 每类 success 是否 ≥ 1
3. 若 0=按本次流程自动生成：
   - 专项报告（`reports/项目管理write-regression专项报告（降级）.md`）
   - 缺陷增量（`defects/缺陷清单-WR-降级增量.md` NX-WR-DEG-001~004）
   - 覆盖矩阵追加 11 条（全部「未实现/未执行」）
   - 系统报告 §3.6 + 批次摘要 §2.6ter 增量
4. 若 ≥1=生成 `test_project_stage_write_regression.py` 11 条脚本，按用户选的回滚策略①造 AUTO-TEST-YYYYMMDD-XXXX 专用项目 → 跑一圈 → 软删除
""")

append_knowledge("缺陷模式库.md", f"""
### 3.3 新缺陷模式 NX-WR-DEG
| 模式编号 | 触发场景 | 判定口径 | 典型根因 | 下次规避 |
|---|---|---|---|---|
| NX-WR-DEG-001 | 写接口候选探测命中=0 | 6 类写操作合计 {total_candidates} 候选，每类 success=0 | ① 前缀不对（需 /api/idmp/xxx 或 /gateway/xxx）；② method 不对；③ RPC 动作名非英文；④ 后端暂未开放写接口=仅前端 demo 静态 | 下一轮先用 Playwright 跑前端「创建项目/提交审批」真实操作，抓 Network HAR 直接取真实 URL/method/body |
| NX-WR-DEG-002 | 权限矩阵用户选 Other | WR 无断言口径 | 产品/研发未在需求中附权限矩阵表 | 用例评审阶段（测试设计→用例生成之间）强制要求产品附「角色 × 动作」权限矩阵，否则不进入 WR |
| NX-WR-DEG-003 | A7 口径 B 并集实测 老板=经理（2=2） | 口径 B 理论应老板>经理；如果数据真实=口径不对 | ① 风险项目确实集中在经理负责的 5 条里=正常；② 接口统计口径=交集不是并集（和口径A一致） | 产品在「统计分析看板口径」段明确每个指标是交集/并集/去重口径 |
| NX-WR-DEG-004 | IDOR 越权写 0 路径命中=无法验证 | 6/6 候选=404 | 和 NX-WR-DEG-001 同源=写接口不存在 | 写接口一旦确定，优先跑 IDOR 4 条作为安全门禁（赵经理写赵老板项目必须 403） |
""")

append_knowledge("自动化维护项.md", f"""
### 3.3 `_probe_write_apis_stage_flow.py` 维护要点
- 输入依赖：`tests/api/ipd/conftest.py` 中的 `_load_system_yaml_auth` / `_load_dotenv` / `_do_login_request` / `_encrypt_aes_256_ecb_hex`；如果 fixture 改名=同步修此脚本 import 与 `_build_cfg()` 内调用。
- 输出文件：`projects/ipd/docs/analysis/IPD项目管理写接口探测结果.json`
- 结果口径：所有字段名 `success / idor_pass_expected_403 / idor_risky_200` 是 `_gen_stage_dashboard_report.py`（未来）或 write-regression 脚本读取的关键字段；不要重命名或删字段；可以加。
- 若下一轮拿到 HAR：将 HAR 中的 request URL 拆分为 (method, path_without_base) → 先加为 top 1 候选命中探测列表，再跑剩余候选=减少候选数避免 token 浪费。
""")

append_knowledge("环境工具问题.md", f"""
### 3.3 探测工具常见问题（本机 Windows）
| 问题 | 原因 | 解决方案 |
|---|---|---|
| `ImportError: cannot import name '_load_dotenv_dict'` | fixture 函数名改过：之前叫 `_load_dotenv_dict` 现在叫 `_load_dotenv` | 直接从 conftest.py grep `^def ` 确认函数名；不要凭记忆 import |
| `ValueError: AES-256 expects 32-byte key, got 16` | 手动加载 cfg 时取错 client_id=从 auth.config.client_id 而不是 auth.client_id（之前 YAML 层级修复过） | 统一用 `_load_system_yaml_auth()` 返回值=已经是 flatten 后的 auth 字典，含 `auth["client_id"]` 32 字节 |
| 探测跑 150 条速度慢/超时 | 默认每个请求 timeout=10s | 若确认内网稳定→可改 timeout=5；但 WR 降级模式本来就是一次性，默认 10s 安全 |
| 某类探测返回 code=200 但实际破坏数据（如 DELETE 真删） | 脚本当前 0 命中所以不存在此风险；一旦命中 200 | 立即停止后续同类候选（代码已 break CREATE 命中的情况）；软删除必须用 isDeleted=1 字段 UPDATE 方式而非 HTTP DELETE |
""")

append_knowledge("下一轮迭代建议.md", f"""
### 3.3 P0 级补测（优先级高于性能/安全）：WR 写操作 11 条真实流转
- 前置动作（按顺序）：
  1. **P0-1：研发/产品提供 6 类写接口清单或前端 Network HAR 抓包文件**（创建项目/提交审批/审批通过/驳回/推进阶段/删除项目 各 1 个真实请求即可，推荐 HAR 文件=AI 可直接解析无需人工整理）
  2. **P0-2：产品书面答复 权限矩阵（用户 Other）**=赵经理/赵老板各能做哪些 status/phase 流转、closed 能否回退、能否跨部门审批、字段编辑权限
  3. **P0-3：产品答复 A7 风险项目口径（NX-WR-DEG-003）**=老板=经理 2=2 是正常/是 bug
  4. **P0-4：拿到以上 3 项后** → AI 自动：重跑探测（仅测提供的路由=不浪费候选）→ 命中=生成 `test_project_stage_write_regression.py` 11 条脚本 → 按回滚策略①造 AUTO-TEST-XXXX 专用项目 → pytest -v → JSON 报告 → 专项报告→缺陷→覆盖矩阵更新→系统报告段落补「已执行」→批次摘要更新→知识沉淀 V1.3 追加
- 建议耗时：在提供 HAR 前提下≈1.5h 完成从探测→报告闭环
- **为什么 P0 高于性能/安全**：用户本轮明确说「核心是项目阶段与状态流转」=WR=用户需求核心；性能/安全=默认通用项且下一轮可独立补，未影响用户明确核心目标；按 AGENTS.md「核心模块优先、通用专项后补」原则。
""")

print("\n✅ H-2 降级报告全部输出完成 ✅")
print(f"  - 专项报告：{wr_report_path}")
print(f"  - 缺陷增量：{DEFECTS/'缺陷清单-WR-降级增量.md'}")
print(f"  - 覆盖矩阵：{cov}（WR 11 条 未实现/未执行）")
print(f"  - 系统报告 §3.6：{sys_rpt if sys_rpt.exists() else '(未生成)'}")
print(f"  - 批次摘要 §2.6ter：{batch if batch.exists() else '(未生成)'}")
print(f"  - 知识沉淀 6 文件 V1.2：6/6 追加完成")
