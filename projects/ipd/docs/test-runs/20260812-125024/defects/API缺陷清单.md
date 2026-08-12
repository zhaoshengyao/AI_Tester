# 阶段 06：API 缺陷清单（IPD 管理系统，批次 20260812-125024）

## 1. 当前阶段
API 自动化缺陷登记（接口契约/文档一致性 & 接口契约/实现一致性 两类分开）

## 2. 输入文件
- `projects/ipd/docs/test-runs/20260812-125024/raw/api-results/pytest-full-api-stdout.txt`（缺陷 stdout 证据源）
- `projects/ipd/docs/cases/API测试用例-评审版.md`
- 需求分析阶段 §KAN §M3 §WF 对应功能/命名/参数名的"产品/研发/测试口径预期"

## 3. 产出文件
- `projects/ipd/docs/test-runs/20260812-125024/defects/API缺陷清单.md`（本文件）

## 4. 正文/核心内容

### 4.1 缺陷统计
| 类别 | 数量 | 高 | 中 | 低 |
| --- | ---: | ---: | ---: | ---: |
| 接口契约/文档一致性（命名/参数名/字段预期 与真实实现不符） | 1 | 0 | 1 | 0 |
| 接口契约/实现一致性（功能/行为未达预期但非文档问题） | 3 | 1 | 2 | 0 |
| 接口契约/业务校验 & 权限越权一致性（写操作必填校验缺失/IDOR 越权） | 3 | 1 | 2 | 0 |
| **合计** | **7** | **2** | **5** | **0** |

> 说明：按 AGENTS.md 硬规则——"API full 执行中出现失败项时，必须全部进入接口缺陷清单；其中实际接口与文档、路由、方法或字段契约不一致的失败项，登记为 **接口契约/文档一致性缺陷** 或 **接口契约/实现一致性缺陷**，不得因需要责任方决定修实现、修文档或调整契约而暂不登记缺陷。" 本清单严格按该规则。

### 4.2 缺陷登记总表（分序号）
| 序号 | 缺陷编号 | 类别 | 严重级 | 来源用例/脚本 | 标题 | 证据入口 | 复测建议 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | API-DOC-001 | 接口契约/文档一致性 | 中 | 见 stdout | API-001 | `20260812-125024/raw/api-results/pytest-full-api-stdout.txt` | 研发/产品确认最终命名或参数名，更新文档或兼容旧名。 |
| 2 | API-IMP-001 | 接口契约/实现一致性 | 高 | 见 stdout | API-004 分页参数未生效 | `20260812-125024/raw/api-results/pytest-full-api-stdout.txt` | 研发修复实现或补充过滤参数名；修复后按原用例复测。 |
| 3 | API-IMP-002 | 接口契约/实现一致性 | 中 | 见 stdout | API-003-A3（AMB-01 状态2/3） | `20260812-125024/raw/api-results/pytest-full-api-stdout.txt` | 研发修复实现或补充过滤参数名；修复后按原用例复测。 |
| 4 | API-IMP-003 | 接口契约/实现一致性 | 中 | 见 stdout | API-005 R10(AMB-03) | `20260812-125024/raw/api-results/pytest-full-api-stdout.txt` | 研发修复实现或补充过滤参数名；修复后按原用例复测。 |
| 5 | DEF-BIZ-001 | 接口契约/业务校验或权限越权一致性 | 高 | 见 stdout | WR-11-HIGH | `20260812-125024/raw/api-results/pytest-full-api-stdout.txt` | 按 AGENTS.md 责任方（研发/产品）自主决定是否修复；复测用例对应 stdout 缺陷标题中的 WR/API 编号。 |
| 6 | DEF-BIZ-002 | 接口契约/业务校验或权限越权一致性 | 中 | 见 stdout | WR-14 | `20260812-125024/raw/api-results/pytest-full-api-stdout.txt` | 按 AGENTS.md 责任方（研发/产品）自主决定是否修复；复测用例对应 stdout 缺陷标题中的 WR/API 编号。 |
| 7 | DEF-BIZ-003 | 接口契约/业务校验或权限越权一致性 | 中 | 见 stdout | WR-15 | `20260812-125024/raw/api-results/pytest-full-api-stdout.txt` | 按 AGENTS.md 责任方（研发/产品）自主决定是否修复；复测用例对应 stdout 缺陷标题中的 WR/API 编号。 |

### 4.3 缺陷明细（stdout 原文证据逐件粘贴）

#### DOC-001 接口契约/文档一致性缺陷（原文）
```
[接口契约/文档一致性缺陷 API-001] riskRule/5 条 ruleCode 与需求分析预测不一致。
  需求分析原预测名=['BUDGET_WARN', 'PROGRESS_STALE', 'RISK_CASCADE', 'SCHEDULE_WARN', 'TEAM_SIZE']
  真实实现 ruleCode   =['BUDGET_CRITICAL', 'BUDGET_WARN', 'MILESTONE_CRITICAL', 'MILESTONE_WARN', 'TASK_DELAY']
  预测中不存在的=实际实现: ['BUDGET_CRITICAL', 'MILESTONE_CRITICAL', 'MILESTONE_WARN', 'TASK_DELAY']
  预测中存在而实现没有: ['PROGRESS_STALE', 'RISK_CASCADE', 'SCHEDULE_WARN', 'TEAM_SIZE']
  → 缺陷类型登记为【接口契约/文档一致性缺陷】，不是实现失败，需产品/研发确认最终命名。
```

#### IMP-001 接口契约/实现一致性缺陷（原文）
```
[接口契约/实现一致性缺陷 API-004 分页参数未生效] project/page 接口：
  请求 pageNum=99 pageSize=10；实际返回 rows.len=6，total=6
  预期 rows=[]（页码超过 ceil(total/10) 时），实现可能忽略 pageNum/pageSize 或 未做偏移处理。
缺陷分类=接口契约/实现一致性（不判失败，按 AGENTS.md 直接登记缺陷）。
```

#### IMP-002 接口契约/实现一致性缺陷（原文）
```
[接口契约/实现一致性缺陷 API-003-A3（AMB-01 状态2/3）] dashboard/riskStats 与 risk/list level 聚合不一致（=口径差风险）：
  riskStats 统计（总览口径）= {'high': 3, 'medium': 1, 'low': 0}
  risk/list 默认聚合（列表明细口径） = {'high': 3, 'medium': 0, 'low': 0}
  风险：riskStats 有 medium=1 但 risk/list 仅 medium=0，可能是：① list 按项目范围/用户权限过滤，总览未按同口径 或 ② 有 medium 风险项目 list 对赵经理不可见。
  补充证据（不同参数的 risk/list） = [({}, 3, {'high': 3, 'medium': 0, 'low': 0}), ({'level': 'medium'}, 0, {'high': 0, 'medium': 0, 'low': 0}), ({'level': 'high'}, 3, {'high': 3, 'medium': 0, 'low': 0}), ({'level': 'low'}, 0, {'high': 0, 'medium': 0, 'low': 0})]
 → 缺陷分类=接口契约/实现一致性。移交研发澄清：riskStats 与 risk/list 的过滤口径（全量/本人）是否应保持一致。
```

#### IMP-003 接口契约/实现一致性缺陷（原文）
```
[接口契约/实现一致性缺陷 API-005 R10(AMB-03)] workflow/definition/list 分类过滤未生效：
  被测参数名集合（categoryId/category_id/category）全部传值 cat_id=2099000000000000001 后，
  返回 total 仍=23（全量），或 rows 全部与分类名无匹配。
  → 两种可能：① 实际生效参数名并非上述 3 个（遗漏未测，属于接口契约/文档一致性——文档名与实现名不符）；或 ② 该接口完全不支持按分类过滤（属于功能缺失 = 实现一致性缺陷）。  → 按 AGENTS.md 不直接断言 fail，登记缺陷移交研发确认实际支持的过滤参数名或功能范围。缺陷分类=接口契约/实现一致性。
```

#### BIZ-001 接口契约/业务校验 & 权限越权一致性缺陷（原文）
```
[接口契约/权限一致性缺陷 WR-11-HIGH] 赵经理POST /idmp/project/approve/2087402878807265282 返回 code=200！可能为 IDOR 高危越权写！resp={"code": 200, "msg": "操作成功", "data": null}
[接口契约/权限一致性缺陷 WR-11-HIGH] 赵经理POST /idmp/project/phase/2087402878807265282?toPhase=closed 返回 code=200！可能为 IDOR 高危越权写！resp={"code": 200, "msg": "操作成功", "data": null}
[WR11] attempt log: [{"method": "PUT", "path": "/idmp/project", "HTTP": 200, "biz_code": 500}, {"method": "POST", "path": "/idmp/project/submit/2087402878807265282", "HTTP": 200, "biz_code": 500}, {"method": "POST", "path": "/idmp/project/approve/2087402878807265282", "HTTP": 200, "biz_code": 200}, {"method": "POST", "path": "/idmp/project/phase/2087402878807265282?toPhase=closed", "HTTP": 200, "biz_code": 200}, {"method": "PUT", "path": "/idmp/project/2087402878807265282", "HTTP": 200, "biz_code": 405}, {"method": "DELETE", "path": "/idmp/project/2087402878807265282", "HTTP": 200, "biz_code": 500}]
```

#### BIZ-002 接口契约/业务校验 & 权限越权一致性缺陷（原文）
```
[接口契约/业务校验一致性缺陷 WR-14] CREATE budget=null(budget未传字段) 返回 code=200 未拦截（预算未做非空/非负数校验）
[接口契约/业务校验一致性缺陷 WR-14] CREATE budget=negative(budget=-999负数) 返回 code=200 未拦截（预算未做非空/非负数校验）
[接口契约/业务校验一致性缺陷 WR-14] CREATE budget=empty_str(budget=''空字符串) 返回 code=200 未拦截（预算未做非空/非负数校验）
```

#### BIZ-003 接口契约/业务校验 & 权限越权一致性缺陷（原文）
```
[接口契约/业务校验一致性缺陷 WR-15] CREATE managerId=null(managerId未传字段) 返回 code=200 未拦截（负责人未做非空校验）
[接口契约/业务校验一致性缺陷 WR-15] CREATE managerId=zero(managerId=0) 返回 code=200 未拦截（负责人未做非空校验）
```

## 5. 执行结论
- 共登记 **7 条缺陷**：文档一致性 1、实现一致性 3、业务校验&权限越权一致性 3。
- 所有缺陷均来源于 pytest full-api stdout 显式 `print()` 块，与对应 JSON 报告中 48 passed 无断言失败=不矛盾，符合 AGENTS.md "文档/实现/业务不一致登记缺陷、不主观断言实现失败"策略。
- 按 AGENTS.md 缺陷策略：所有缺陷 = 证据交付与缺陷登记完成，**由责任方（研发/产品）自主决定是否修复**；测试侧仅在下一轮按修复结论回归对应用例，不强制执行修复动作。

## 6. 风险与待确认项
1. 高危类（越权/IDOR/结项）DEF-WR-07/08/09/11：移交产品 + 研发确认是否需要在权限模型中补充"角色×项目阶段×状态"的写入权限矩阵；如确认需修复，修复后需在下一轮把 WR-07~WR-11 作为 P0 full-api 必测回归项。
2. API-004 分页不生效（如 IMP 有）：当数据量增长到超过前端分页单页容量时，前端交互不可用，建议优先修复并在修复后列入下一轮 smoke 作为必测项。
3. 口径差（A1/A2/A3）移交产品确认：需要产品明确 dashboard 与 list 接口的数据权限边界，避免出现"总览 8 个项目，列表我只看到 5 个但不提示'数据口径=仅本人项目'"而让项目经理误以为系统丢失数据。
4. 业务校验必填缺失 WR-14（预算） / WR-15（负责人）：如产品侧要求 CREATE 必须校验，需在后端 service 层 + database NOT NULL 双层补约束；若允许为空，需要在需求文档中写明"预算/负责人允许为空"，并更新评审版用例预期。
5. 风险规则命名 API-001（如 DOC 有）：需求分析中 SCHEDULE_WARN/TEAM_SIZE 等名与真实 ruleCode 不一致，若产品/前端按 SCHEDULE_WARN 命名实现页面文字或联动，会出现"配置了 SCHEDULE_WARN 但后台未定义 ruleCode"的级联 bug。建议需求分析 §M3 的风险规则枚举部分**在下一轮立即与真实实现对齐更新**（TR-002 文档更新）。

## 7. 下一步建议
1. 产品/研发责任方按缺陷清单 §4.2 总表中的标题和证据认领缺陷，并自主决定是否修复（测试侧仅交付证据，不强制修复）。
2. 若确认修复 → 修复后在新批次重跑 pytest-full-api，确认对应 stdout 的缺陷登记块消失。
3. 将正式缺陷 ID（如 Jira/TAPD）回填到覆盖矩阵的"缺陷关联"列。
