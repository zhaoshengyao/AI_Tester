# IPD 管理系统 UI 测试用例（评审版）

> **评审版标记**: 🟡 **已按评审记录修订（修改 8 条 + 分层标注，合计 28 条）**
> 修订依据：OM-08（UI-27 回滚保障）、AMB-05（断言优先级）、AMB-06（UI-2 模糊匹配）、NX-07（UI smoke 不被 P2 阻断）

| 序号 | 用例编号 | 分层 | 页面/路由 | 优先级 | 场景类型 | 测试步骤 | 预期结果 | 截图点位 / Spec 建议 |
|------|----------|------|-----------|--------|----------|----------|----------|---------------------|
| 1 | UI-AUTH-001 | smoke | 登录页 `/login` | P0 | 正常 | 1. 访问首页未登录跳 /login；2. 输入赵经理/123456；3. 点登录 | 3s 内跳转 `/dashboard/overview`；顶部显示"赵经理"或"项目经理" | `specs/ipd/login.spec.ts` → login-success.png |
| 2 | **UI-AUTH-002（AMB-06 模糊）** | smoke | 登录页 | P0 | 异常 | 1. 账号正确密码错；2. 登录 | toast 包含"用户不存在" **或** "密码错误" **任一关键词**（AMB-06 不再精确匹配"用户不存在/密码错误"整句，防止版本变化导致失败） | login-wrong-pwd.png |
| 3 | UI-AUTH-003 | smoke | 登录页 | P0 | 边界验证码 | 1. 未输入任何内容点击登录；2. 验证码区域是否展示 | captchaEnabled=false → 页面无 canvas 图片验证码；账号空/密码空必填红色错误提示（AMB-05：前端 inline 提示优先） | login-empty.png |
| 4 | UI-DASH-001 | smoke | 看板 `/dashboard/overview` | P0 | 正常 | 1. 登录后默认看板；2. 检查 5 卡片渲染；3. 饼图/进度条 canvas 有内容 | 5 卡数值 5/4/1/0/2 全部显示；饼图有颜色区分 hardware/software | dashboard-overview.png |
| 5 | UI-IDMP-PRJ-001 | smoke | 项目列表 `/idmp/project` | P0 | 正常 | 1. 左侧菜单点"项目管理→项目列表"；2. 表格加载 5 行；3. 8 列齐全 | 5 行；列齐全；无空白占位符 | project-list.png |
| 6 | UI-IDMP-APR-001 | smoke | 审批中心 `/idmp/approval` | P1 | 正常 | 1. 菜单点"审批中心"；2. 4 Tab 显示；3. Tab 切换不崩溃 | 无 404；即使空也有空态 | approval-empty.png |
| 7 | UI-IDMP-RR-001 | smoke | 风险预警配置 `/idmp/riskRule` | P0 | 正常 | 1. 菜单点"风险预警配置"；2. 5 行规则；3. 开关列全启用 | 5 行；level 颜色中/高正确 | risk-rule-list.png |
| 8 | UI-WF-CAT-001 | smoke | 流程分类 `/workflow/category` | P1 | 正常 | 1. 菜单工作流→流程分类；2. 11 行分类 3 级树形展开；3. 嵌套正确 | 3 级嵌套正确；无 JS 异常 | wf-category-list.png |
| 9 | **UI-WF-FM-001（NX-07 放宽）** | smoke（**但属 P2 非核心，失败不阻断**） | 表单管理 `/workflow/formManage` | P2 | 正常（R3） | 1. 菜单工作流→表单管理；2. 页面 200（非 404） | 若 404 → 直接登记"菜单/路由不一致"R3 缺陷；**UI smoke continue 判定 = 不看此项（NX-07 明确，仅 6 个 P0 看，此项 P2）** | wf-form-manage.png 或 404 证据图 |
| 10 | **UI-WF-SPEL-001（NX-07 放宽）** | smoke（P2 非核心，失败不阻断） | SPEL `/workflow/spel` | P2 | 正常（R3） | 1. 菜单工作流→SPEL；2. 页面 200 | 同上；若 404 登记 R3 缺陷，不影响 smoke continue 决策 | wf-spel.png |
| 11 | UI-DASH-002 | readonly-regression | 看板 | P0 | 一致性 | 1. hover 饼图查看 tooltip；2. 点击硬件卡片 → 跳转项目列表 type=hardware 过滤（若 UI 支持） | tooltip 显示 hardware 3；跳转后列表 3 条 hardware 正确 | dashboard-drilldown-hardware.png |
| 12 | UI-DASH-003 | readonly-regression | 看板 | P1 | 一致性 | 1. 检查 5 条项目进度条：statusName 中文；2. riskLevel 标签颜色 | 回路监控箱设备：status=已立项 phase=已结项 progress=100 riskLevel=高 完全对应接口值 | dashboard-progress.png |
| 13 | UI-IDMP-PRJ-002 | readonly-regression | 项目列表 | P0 | 正常 | 1. 点击"回路监控箱设备"→ 详情；2. 27 字段；3. 禅道区域不显示 null（OM-04 功能侧已改，UI 同步此断言）；4. 返回列表 | 禅道/云集成空态显示"未启用集成"卡或整块隐藏，**不显示 null 字段**（OM-04 UI 侧断言） | project-detail.png |
| 14 | UI-IDMP-PRJ-003 | readonly-regression | 项目列表 | P0 | 过滤 | 1. 软件研发下拉；2. 列表变为 2 条 | 2 条智慧文档管理/智慧合规正确显示；total=2 | project-filter-software.png |
| 15 | UI-IDMP-PRJ-004 | readonly-regression | 项目列表 | P1 | 分页 | 1. pageSize=2；2. 第一页 2/第二 2/第三 1；合计 5 条 | 合计 5；total=5 不变 | project-pagination-2each.png |
| 16 | UI-IDMP-PRJ-005 | readonly-regression | 项目列表 | P1 | 搜索 | 1. 搜索"蓝牙"→ 结果=智能蓝牙门锁 | 仅 1 条命中；模糊搜索可用 | project-search-lanya.png |
| 17 | UI-IDMP-PRJ-006 | readonly-regression | 项目列表 | P2 | 边界空态 | 1. 搜索"不存在此项目abc" | 空态"暂无数据"；不显示 null | project-search-empty.png |
| 18 | UI-IDMP-RR-002 | readonly-regression | 风险规则配置 | P0 | 详情 | 1. BUDGET_WARN 点名称/编辑 → 12 字段 | 触发条件 90、级别中、enabled=开；描述完整 | risk-rule-detail-budget-warn.png |
| 19 | UI-IDMP-RISK-001 | readonly-regression | 风险记录列表（独立页或详情 Tab） | P0 | 过滤 | 1. 过滤 level=高 → 3 条；2. 状态未处理 → 3 条 | 过滤正确；描述完整 | risk-list-filter-high.png |
| 20 | UI-IDMP-BUDG-001 | readonly-regression | 预算列表 | P1 | 正常 | 1. 预算 Tab；2. 3 条；3. status=draft 显示"草稿"；spent=null 显示"-" | 列正确；不显示 null | budget-list.png |
| 21 | UI-IDMP-DOC-001 | readonly-regression | 文档列表 | P1 | 正常 | 1. 文档 Tab；2. 3 条文件名 docx；3. fileSize 显示 KB；4. 点击文件名跳转 OSS（若 OSS 403 签名问题，只要页面不崩溃即通过） | OSS 403 属于外部依赖签名 = 不判 UI 失败；但截图作为证据列到报告 | doc-list-3files.png |
| 22 | UI-WF-CAT-002 | readonly-regression | 工作流分类 | P1 | 嵌套展开 | 1. 展开考勤→spel 3 级；2. 3 级祖先路径 ancestors 完全对应 | 3 级嵌套；展开不跳回默认态 | wf-category-3level.png |
| 23 | UI-WF-DEF-001 | readonly-regression | 流程定义列表 | P1 | 过滤（R10） | 1. 分类选 IDMP 审批；2. 抓包看参数名；3. 断言过滤生效（AMB-03 两档） | ✅ 任一参数名生效=通过；⚠️ 若生效名≠categoryId=登记 R10 小缺陷 | wf-def-filter-idmp.png |
| 24 | UI-MENU-001 | readonly-regression | 全局菜单 10+ 子菜单跳转 | P1 | 菜单跳转无 404 崩溃 | 1. 依次点击 10+ 子菜单；2. 每次 URL 正确；3. 面包屑；4. 前进后退 | 无 404 空白；无内存飙升；历史记录可用 | no-crash-all-menus.png |
| 25 | UI-IDMP-PRJ-011 | semi-auto | 项目列表 | P0 | 新建弹窗必填校验 | 1. 点新建项目；2. 不填项目名称 → 点保存 → 前端红 inline "项目名称 必填"（AMB-05：前端提示优先）；3. 取消关闭；4. 查 list 仍 5 条（无脏数据） | 必填提示；取消后无脏数据；**断言优先级：前端 inline > 后端返回 400/500（但两者任一有效均算通过，AMB-05）** | project-create-empty-cancel.png |
| 26 | UI-IDMP-PRJ-012 | semi-auto | 项目列表 | P0 | 编辑弹窗只读锁（type 字段） | 1. 选 software status=approved 的"智慧合规系统"→ 编辑；2. 项目类型字段 disabled 灰化（无输入框或 disabled=true）；3. 取消 | 只读锁定；取消后列表值不变；AMB-05 前端断言 | project-edit-locked-type.png |
| 27 | **UI-IDMP-RR-011（OM-08 回滚保障）** | semi-auto | 风险规则配置 | P0 | 编辑阈值弹窗 + 误操作回滚保障 | 1. BUDGET_WARN 点编辑 → 触发条件改为 101 → **点取消（正常 semi-auto 路径）**；2. **自动化脚本额外加回滚保障分支（OM-08）**：一旦由于脚本误点保存（误操作），立即在关闭弹窗后追加一步：`await request.get('/idmp/riskRule/1')` → 若 triggerCondition!=90 立即 `await request.put('/idmp/riskRule/1', {triggerCondition:90})` 回滚 + 登记"UI 自动化误操作触发实际写入"缺陷（脚本实现幂等回滚） | 取消 → triggerCondition 仍=90；即使误点保存也能在 1s 内恢复 90 原值（OM-08 强制要求，防影响其他用例风险联动） | risk-rule-edit-trigger-cancel.png、**rollback-trigger-90-restored.png（若触发回滚时截图存证）** |
| 28 | UI-IDMP-DOC-011 | semi-auto | 文档上传 | P1 | 上传弹窗校验 | 1. 点上传文档 → 选 exe → "不允许此类型文件"提示；2. 取消；3. 再选 ≤ 50KB 的 TEST-AUTO-XXXX.docx 实际上传；4. 若实际上传成功 → 立即调用删除接口（若存在）删除；若不存在删除接口 → 文档列表保留 TEST-AUTO- 前缀，列入批次清理清单 | 类型拦截正确；小文件上传成功 → 删除或列入批次清理；AMB-05 前端拦截优先 | doc-upload-reject-exe.png、doc-upload-small-ok.png |

### UI 自动化分层说明（与覆盖矩阵映射准备）

| 分层 | 数量（共 28） | 覆盖矩阵脚本实现方式建议 |
|------|-------------|-------------------------|
| smoke（P0+P1）核心 6 项 | UI-AUTH-001/002/003 + UI-DASH-001 + UI-IDMP-PRJ-001 + UI-IDMP-RR-001 = 6 条（P2 项不计入门禁，NX-07） | `smoke.spec.ts`：6 条合 1 个 spec，失败即 stop UI full；99% 的 P0 覆盖 |
| readonly-regression | 第 11–24 条 = 14 条 | `readonly-regression/` 目录下按页面分 6 个 spec（dashboard、project、risk、budget、doc、workflow） |
| semi-auto（写操作为主，不实际提交或提交后立即回滚） | 第 25–28 条 = 4 条 | `semi-auto/` 目录下 4 个 spec，每个含回滚保障断言（同 OM-08 机制） |
