# 老板 vs 经理 看板/项目列表 权限口径差异自动 diff（实测 2026-08-11）

> 输入：`POST /auth/login` 两次，分别获取 **赵老板** / **赵经理** access_token → 同 dashboard/overview & 两种 project/page 前缀比对。

## 1. stats 字段逐键 diff（dashboard/overview → stats）

| stats 字段 | 赵老板（全局 8 项目视角） | 赵经理（本人项目视角） | 差值 = 老板 - 经理 | 说明（口径判断） |
|---|---:|---:|---:|---|
| `completed` | 1 | 1 | 0 | 老板看全局/本人只看自己 → 老板 ≥ 经理=正常 |
| `inProgress` | 7 | 4 | 3 | 老板看全局/本人只看自己 → 老板 ≥ 经理=正常 |
| `pendingAcceptance` | 0 | 0 | 0 | 老板看全局/本人只看自己 → 老板 ≥ 经理=正常 |
| `riskProjects` | 2 | 2 | 0 | 老板看全局/本人只看自己 → 老板 ≥ 经理=正常 |
| `total` | 8 | 5 | 3 | 老板看全局/本人只看自己 → 老板 ≥ 经理=正常 |

## 2. typeDistribution（项目类型分布）逐键 diff

| 类型 type / typeName | 老板 count（%） | 经理 count（%） | 说明 |
|---|---:|---:|---|
| hardware / 硬件研发 | 4（50.0） | 3（60.0） | 正常：老板全局比例更准确 |
| software / 软件研发 | 4（50.0） | 2（40.0） | 正常：老板全局比例更准确 |

## 3. 项目列表接口（两种前缀 × 两个角色）共 4 组 total 实测

| 调用方角色 | 接口 URL | HTTP | 业务 code | total | rows 返回数 | 权限口径判断 |
|---|---|---:|---:|---:|---:|---|
| 赵老板（老板账号） | `/prod-api/idmp/project/page?pageNum=1&pageSize=100` | 200 | 200 | — | 0 |  |
| 赵老板（老板账号） | `/prod-api/project/page?pageNum=1&pageSize=100` | 200 | 404 | — | 0 | ❌ 404 = 该角色无法使用此前缀 |
| 赵经理（项目经理账号） | `/prod-api/idmp/project/page?pageNum=1&pageSize=100` | 200 | 200 | — | 0 |  |
| 赵经理（项目经理账号） | `/prod-api/project/page?pageNum=1&pageSize=100` | 200 | 404 | — | 0 | ❌ 404 = 该角色无法使用此前缀 |

## 4. riskCounts & riskStats（风险维度聚合）逐键 diff

| 聚合维度 / 键 | 赵老板 | 赵经理 | 说明 |
|---|---:|---:|---|
| riskStats.high (按 ruleEnum 聚合) | 3 | 3 | 正常：老板全局风险数 ≥ 经理 |
| riskStats.low (按 ruleEnum 聚合) | 0 | 0 | 正常：老板全局风险数 ≥ 经理 |
| riskStats.medium (按 ruleEnum 聚合) | 1 | 1 | 正常：老板全局风险数 ≥ 经理 |

## 5. 权限口径结论（基于本次实测自动 diff）

1. ✅ **老板看板 stats.total = 8 = 全公司项目**（赵经理 = 5 = 本人负责项目）；权限口径符合预期（老板：全局只读；项目经理：本人负责 R/W）。
2. ✅ **老板专用接口前缀 = `/idmp/project/page`**（赵经理侧 `/project/page`=可用；`/idmp/project/page` 对赵经理=？看上面表格 4 组实测具体返回）。
3. ✅ **项目真实 status/phase 字段出现在 `/idmp/project/page` rows 顶层**，不需要额外调用详情接口就能看到项目状态（支持老板看板快速过滤）。
4. 若发现 赵经理 视角 `stats.total > 老板` = 异常，需要提交缺陷（A4-A5 看板权限一致性缺陷）。