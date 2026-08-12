# IPD 管理系统 UI 测试用例（初稿）

> **说明**: 共 28 条（测试计划预估 28）。编号前缀 `UI-`，分层严格对应 AGENTS.md：**smoke（6+登录）、readonly-regression（14）、semi-auto（8）**。每个用例记录对应 Playwright spec 文件名建议。截图点位列表在备注栏。

| 序号 | 用例编号 | 分层 | 页面/路由 | 优先级 | 场景类型 | 测试步骤 | 预期结果 | 截图点位 / Spec 建议 |
|------|----------|------|-----------|--------|----------|----------|----------|---------------------|
| 1 | UI-AUTH-001 | smoke | 登录页 `/login` | P0 | 正常 | 1. 访问首页未登录跳 /login；2. 输入赵经理/123456；3. 点登录 | 3s 内跳转 `/dashboard/overview`；顶部显示"赵经理"或"项目经理" | `specs/ipd/login.spec.ts` → screenshot: login-success.png |
| 2 | UI-AUTH-002 | smoke | 登录页 | P0 | 异常 | 1. 账号正确密码错；2. 登录按钮 | 页面顶部/表单下方红色 toast："用户不存在/密码错误" | login-wrong-pwd.png |
| 3 | UI-AUTH-003 | smoke | 登录页 | P0 | 边界验证码 | 1. 未输入任何内容点击登录；2. 验证码区域是否展示 | captchaEnabled=false → 页面无 canvas 图片验证码；账号空/密码空必填红色错误 | login-empty.png |
| 4 | UI-DASH-001 | smoke | 看板 `/dashboard/overview` | P0 | 正常 | 1. 登录后默认看板；2. 检查 5 卡片渲染；3. 饼图/进度条 canvas 有内容；4. 页面无 404 空态 | 5 卡数值 5/4/1/0/2 全部显示；饼图有硬件 2 块/软件 1 块颜色区分 | dashboard-overview.png |
| 5 | UI-IDMP-PRJ-001 | smoke | 项目列表 `/idmp/project` | P0 | 正常 | 1. 左侧菜单点"项目管理→项目列表"；2. 表格加载 5 行；3. 列项目编号/名称/类型/状态/阶段/负责人/预算/进度 | 5 行；列标题与需求一致；表格无空白占位符 | project-list.png |
| 6 | UI-IDMP-APR-001 | smoke | 审批中心 `/idmp/approval` | P1 | 正常 | 1. 菜单点"审批中心"；2. 4 Tab（我的待办/已办/我发起的/抄送）显示；3. Tab 切换不崩溃 | 无 404；Tab 存在；即使 API 未抓到，UI 应有空态或加载态 | approval-empty.png |
| 7 | UI-IDMP-RR-001 | smoke | 风险预警配置 `/idmp/riskRule` | P0 | 正常 | 1. 菜单点"风险预警配置"；2. 表格 5 行规则；3. 开关列全启用 | 5 行与接口一致；level 颜色中/高正确 | risk-rule-list.png |
| 8 | UI-WF-CAT-001 | smoke | 流程分类 `/workflow/category` | P1 | 正常 | 1. 菜单工作流→流程分类；2. 11 行分类 3 级树形展开；3. "考勤/测试/SPEL"父子展开按钮 | 3 级嵌套正确；展开无 JS 异常 | wf-category-list.png |
| 9 | UI-WF-FM-001 | smoke | 表单管理 `/workflow/formManage` | P2 | 正常（R3） | 1. 菜单工作流→表单管理；2. 页面 200（非 404） | 若 404 → 直接登记"菜单/路由不一致"缺陷（R3），UI smoke 不算通过 | wf-form-manage.png（或 404 证据图） |
| 10 | UI-WF-SPEL-001 | smoke | SPEL `/workflow/spel` | P2 | 正常（R3） | 1. 菜单工作流→SPEL；2. 页面 200 | 同上 R3；若 404 登记缺陷 | wf-spel.png |
| 11 | UI-DASH-002 | readonly-regression | 看板 | P0 | 数据一致性 | 1. hover 饼图查看 tooltip；2. 点击硬件 3 卡片 → 跳转项目列表 + type=hardware 过滤（如果 UI 支持） | tooltip 显示硬件 3 / 60%；跳转后列表 3 条正确显示 hardware | dashboard-drilldown-hardware.png |
| 12 | UI-DASH-003 | readonly-regression | 看板 | P1 | 一致性 | 1. 检查 5 条项目进度条：statusName 中文（已立项/草稿等）；2. riskLevel 标签颜色（高=红/中=橙） | 5 条中，回路监控箱设备 status=已立项/phase=已结项/progress=100%/riskLevel=高 完全对应接口值 | dashboard-progress.png |
| 13 | UI-IDMP-PRJ-002 | readonly-regression | 项目列表 | P0 | 正常 | 1. 点击"回路监控箱设备"名称 → 进入详情 /idmp/project/2086985374914007042；2. 27 字段区域：基本信息/管理信息/禅道集成/云集成；3. 返回列表 | 详情完全展示；phase=closed 显示"已结项"；禅道字段显示"未启用"或标签（即使 null） | project-detail.png |
| 14 | UI-IDMP-PRJ-003 | readonly-regression | 项目列表 | P0 | 过滤 | 1. 类型下拉选择"软件研发"；2. 列表变为 2 条"智慧文档管理系统/智慧合规系统" | 过滤正确；分页控件 total=2 | project-filter-software.png |
| 15 | UI-IDMP-PRJ-004 | readonly-regression | 项目列表 | P1 | 分页 | 1. 点击分页控件 pageSize=2；2. 第一页 2 条；3. 下一页 2 条；4. 第 3 页 1 条（5 条合计） | 3 页合计 5；分页 total=5 始终不变 | project-pagination-2each.png |
| 16 | UI-IDMP-PRJ-005 | readonly-regression | 项目列表 | P1 | 搜索 | 1. 搜索框输入"蓝牙"；2. 结果=智能蓝牙门锁（id=2085617546210209793） | 仅 1 条正确命中；模糊搜索有效 | project-search-lanya.png |
| 17 | UI-IDMP-PRJ-006 | readonly-regression | 项目列表 | P2 | 边界 | 1. 搜索不存在关键词"不存在此项目abc"；2. 空态显示"暂无数据" | 空态文案存在；不显示 null | project-search-empty.png |
| 18 | UI-IDMP-RR-002 | readonly-regression | 风险规则配置 | P0 | 详情 | 1. 点击 BUDGET_WARN "成本超预算预警"名称或"编辑"按钮 → 详情页/弹窗；2. 显示 12 字段 | 字段完全与 riskRule/1 接口一致：触发条件 90、级别中、enabled=开；描述完整显示 | risk-rule-detail-budget-warn.png |
| 19 | UI-IDMP-RISK-001 | readonly-regression | 风险记录列表（如 UI 有独立页或项目详情 Tab） | P0 | 过滤 | 1. 进入风险列表（全局视角或项目 1 视角）；2. 筛选 level=高 → 3 条；3. 筛选状态=未处理 → 3 条 | 过滤正确；描述完整 | risk-list-filter-high.png |
| 20 | UI-IDMP-BUDG-001 | readonly-regression | 预算列表 | P1 | 正常 | 1. 预算 Tab/模块；2. 3 条；3. status=draft 显示"草稿"；spent=null 显示"-"不显示 null | 列：项目名/总预算/实际支出/状态；字段正确显示 | budget-list.png |
| 21 | UI-IDMP-DOC-001 | readonly-regression | 文档列表 | P1 | 正常 | 1. 文档 Tab；2. 文件名 3 条（docx）；3. fileSize 显示 KB 换算；4. 文件名点击（若跳转 OSS） | 下载若 OSS 403 正常（需签名），只要不导致页面崩溃即通过 | doc-list-3files.png |
| 22 | UI-WF-CAT-002 | readonly-regression | 工作流分类 | P1 | 嵌套 | 1. 展开"考勤（parentId=190049...）"二级；2. 展开"spel（parentId=190049...）"三级；3. 测试新增可见 | 3 级祖先路径 ancestors 完全对应；展开不跳回默认态 | wf-category-3level.png |
| 23 | UI-WF-DEF-001 | readonly-regression | 流程定义列表 | P1 | 过滤 | 1. 分类选择"IDMP审批"（id=2099...）；2. 流程定义显示只属于此分类；3. 若 UI 调用了 3 种参数名其中一种生效，应返回匹配的流程数；否则（R10）过滤不生效 = 登记缺陷 | 若生效：流程数 = 分类对应的流程定义数；若不生效 = R10 缺陷；截图前后作为证据 | wf-def-filter-idmp.png |
| 24 | UI-MENU-001 | readonly-regression | 全局菜单 | P1 | 菜单跳转 | 1. 依次点击 10 个可访问子菜单（overview/project/approval/riskRule/category/formManage/spel + 可能的 4 个 Tab）；2. 每次跳转后 URL 正确，无 404 空白 | 每次面包屑正确；历史记录可前进后退；无内存飙升 | no-crash-all-menus.png |
| 25 | UI-IDMP-PRJ-011 | semi-auto | 项目列表 | P0 | 新建弹窗必填 | 1. 点新建项目；2. 不填项目名称 → 点保存；3. 看"项目名称 必填"提示；4. 取消关闭；5. 确认无脏数据（后台查 list 仍 5 条） | 必填提示；无脏数据写入 | project-create-empty-cancel.png |
| 26 | UI-IDMP-PRJ-012 | semi-auto | 项目列表 | P0 | 编辑弹窗只读锁 | 1. 选择"智慧合规系统"（type=software status=approved）→ 编辑；2. 项目类型字段不可编辑（若产品要求创建后锁定）；3. 取消关闭 | 只读字段锁定（灰化/无输入框）；取消后列表值不变 | project-edit-locked-type.png |
| 27 | UI-IDMP-RR-011 | semi-auto | 风险规则配置 | P0 | 编辑阈值弹窗 | 1. BUDGET_WARN 点编辑 → 触发条件改为 101 → 保存（semi-auto：只触发请求不确认，或保存后立即改回 90，若操作不影响现有数据） | 保存确认弹窗存在；若实际 PUT 成功立即回滚为 90（避免影响风险联动）；否则取消不真正提交 | risk-rule-edit-trigger-cancel.png |
| 28 | UI-IDMP-DOC-011 | semi-auto | 文档 | P1 | 上传弹窗校验 | 1. 点上传文档；2. 选择 exe 文件；3. 校验提示"不允许此类型文件"；4. 取消；5. 再选 ≤50KB 的 txt 或 docx（实际上传不超过 50KB，文件名前缀 TEST-AUTO-XXXX） | 类型拦截正确；小文件上传成功 → 随后立即删除（若有删除接口）；否则文档列表保留 1 条 TEST-AUTO- 前缀，列入批次清理清单 | doc-upload-reject-exe.png、doc-upload-small-ok.png |
