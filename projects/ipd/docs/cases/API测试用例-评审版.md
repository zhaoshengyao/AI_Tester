# IPD 管理系统 API 测试用例（评审版）

> **评审版标记**: 🟡 **已按评审记录修订（新增 2 条 + 删除 3 条重复 + 拆分 1 条为 8 条 = 合计 42 + 2 - 3 + 7 = 48 条）**
> 修订依据：`测试用例评审记录.md` 中 OM-02/03/07、REP-01/03、AMB-03、NX-06

| 序号 | 用例编号 | 模块 | 接口 | 优先级 | 场景类型 | 测试步骤 | 预期结果 | 断言要点 |
|------|----------|------|------|--------|----------|----------|----------|----------|
| 1 | API-AUTH-001 | AUTH | POST /auth/login | P0 | smoke 正常 | 1. clientId + grantType(驼峰) + AES-256-ECB(key=client_id) + tenantId=000000 | 200；code=200；data.access_token 长度 > 200；JWT 解码 payload.clientid=e5cd7e48... | 见需求分析 4.4.1；token 可解码 |
| 2 | API-AUTH-002 | AUTH | POST /auth/login | P0 | 异常 | password=wrongpwd（同样加密）POST | code=500；msg 包含"不存在/密码错误"任一（AMB-06 模糊包含）；无 token | 防爆破 |
| 3 | API-AUTH-003 | AUTH | POST /auth/login | P0 | 异常 | client_id 下划线（非驼峰）POST | code=500；msg="认证客户端id不能为空" | 证明必须驼峰（知识库沉淀） |
| 4 | API-AUTH-004 | AUTH | POST /auth/login | P0 | 异常 | grant_type 下划线 POST | code=500；msg="认证权限类型不能为空" | 证明 grantType 驼峰 |
| 5 | **API-AUTH-005（NX-06 修正）** | AUTH | POST /auth/login | P1 | 边界（缺 tenantId） | 1. 不传 tenantId POST；2. 记录真实响应 | **真实为准（NX-06）**：<br>✅ code=500 + msg="缺少必填字段 tenantId"（或等价清晰）→ 参数校验通过<br>❌ code=500 + msg 含 NPE/NullPointer 堆栈 → 登记"校验缺失，NPE 泄漏"缺陷<br>所有情况以真实返回为准，不主观推断 |
| 6 | API-AUTH-006 | AUTH | POST /auth/login | P1 | 边界 grantType 非法枚举 | grantType=wrong/pwd/1/account/other 5 种值 | 全部 code=500，msg 含"认证权限类型"错误 |
| 7 | API-AUTH-007 | AUTH | GET /auth/code | P0 | smoke | GET /auth/code | code=200；captchaEnabled=false；uuid/img=null | 验证码默认关 |
| 8 | **API-AUTH-009（OM-02 新增）** | AUTH | POST /auth/logout | P0 | smoke | 1. 登录拿 token；2. POST /auth/logout（带 token header）；3. 再用同一 token 立即访问 GET /idmp/dashboard/overview | logout 返回 code=200；再访问 dashboard：返回 401/403 或 code≠200（token 已失效） | 已知 GET /auth/logout 返回 405，所以必须用 POST |
| 9 | API-AUTH-008 | AUTH | GET /idmp/dashboard/overview 未授权 | P0 | 权限 | 不带 header 访问 dashboard | 401/403；无业务数据 |
| 10 | API-USER-001 | AUTH | GET /system/user/profile | P0 | smoke | 带正确 header | code=200；data.user.userName="赵经理"；roleGroup="项目经理" |
| 11 | **API-USER-009（OM-07 新增）** | AUTH | JWT userId 与 profile 一致性 | P0 | 一致性 OM-07 | 1. 解码 JWT payload.userId（number 类型）；2. 读取 profile.data.user.userId（string 类型）；3. 数值化对比 | 两者数值相等（= 2086985374914007041 左右） | **类型差异不影响一致性**：JWT number vs profile string 是实现差异，登记为"待确认：类型不一致但值相同"不算缺陷 |
| 12 | API-USER-002 | AUTH | GET /system/menu/getRouters | P0 | smoke | 带正确 header | code=200；data 长度 3；meta.title 含"统计分析看板/项目管理/工作流" |
| 13 | **API-USER-003（REP-01 合并）** | —— | —— | —— | 已删除重复 | 与 FUNC-ROLE-001 完全同 | 脚本只写 1 份 pytest，用例保留在功能测试评审版中 | **REP-01 去重：共用同一份 API 测试脚本（pytest:test_dept_list_403）** 不重复执行 2 次 |
| 14 | **API-USER-004（REP-01 合并）** | —— | —— | —— | 已删除重复 | 与 FUNC-ROLE-002 同 | 同上 | 同上，脚本 test_role_list_403 |
| 15 | **API-USER-005（REP-01 合并）** | —— | —— | —— | 已删除重复 | 与 FUNC-ROLE-003 同 | 同上 | 同上，脚本 test_menu_build_403 |
| 16 | API-USER-006 | AUTH | GET /system/dict/data/type/sys_yes_no | P1 | smoke | 请求 | code=200；data 长度 2；label=是 value=Y/否=N |
| 17 | API-USER-007 | AUTH | GET /system/dict/data/type/common_status | P2 | 边界空 | 请求 | code=200；data=[]（空数组不报错） |
| 18 | API-USER-008 | AUTH | GET /system/user/list | P1 | smoke | 请求 | code=200；total=16；rows.length ≤ 16（默认分页） |
| 19 | **API-DASH-001（OM-03 结构断言明确）** | DASH | GET /idmp/dashboard/overview | P0 | smoke + 结构断言 | 正常请求 | code=200；data 顶层有 stats/typeDistribution/riskStats/projectProgress 4 子键；stats 含 total/inProgress/completed/pendingAcceptance/riskProjects 5 数字键；typeDistribution 长度 2 | OM-03：结构精确断言（防止后续重构把结构改成 {total, rows}） |
| 20 | API-DASH-002 | DASH | GET /idmp/dashboard/overview 连续请求稳定性 | P0 | 边界 | 连续 3 次请求 | stats/typeDistribution/riskStats/projectProgress 内容完全一致 |
| 21 | **API-PRJ-001（OM-03 明确 list 结构数组）** | PRJ | GET /idmp/project/list | P0 | smoke + 结构断言 | 请求 | code=200；**顶层返回结构 = {code, msg, data: []}**（data 直接是数组，不含 total/rows 顶层键）；data.length=5 | **结构断言 A：project/list ≠ page 结构，list 是纯数组 data** |
| 22 | **API-PRJ-002（OM-03 明确 page 结构 {total,rows}）** | PRJ | GET /idmp/project/page | P0 | smoke + 结构断言 | pageNum=1 pageSize=3 | code=200；**顶层返回结构 = {code, msg, total: 5, rows: []}**（total 和 rows 是 code/msg 同级键，不是 data 子键！）；rows.length=3；total=5 | **结构断言 B：project/page ≠ list 结构，{total,rows} 同级** |
| 23 | API-PRJ-003 | PRJ | GET /idmp/project/{id} 已存在 | P0 | smoke 详情 | id=2086985374914007042 | code=200；data.projectName="回路监控箱设备"；data.type="hardware"；data.phase="closed"；**data 对象键数 ≥ 27**（全字段检查） |
| 24 | API-PRJ-004 | PRJ | GET /idmp/project/{id} 不存在 | P1 | 异常 | id=9999999999999999999 | code=500/404/空对象任一；msg 不出现 SQL 堆栈 |
| 25 | API-PRJ-005 | PRJ | GET /idmp/project/page?type=hardware 过滤 | P0 | 过滤 | pageNum=1 pageSize=10 type=hardware | rows 全 type=hardware；total=3（若存在 total 字段） |
| 26 | API-PRJ-006 | PRJ | GET /idmp/project/page?type=software 过滤 | P0 | 过滤 | rows 全 software；total=2 |
| 27 | API-PRJ-007 | PRJ | GET /idmp/project/page?type=invalid_type | P1 | 异常过滤 | type=xxxinvalid → code=200；rows 可能=[] 或 5 | 不允许 500（参数校验失败必须 400/200 不抛） |
| 28 | API-PRJ-008 | PRJ | GET /idmp/project/page?pageNum=-1 | P1 | 边界非法页码 | pageNum=-1 | code=400/500/200 任一；无 SQL 堆栈；不除 0 |
| 29 | API-PRJ-009 | PRJ | GET /idmp/project/page?pageSize=0 | P1 | 边界非法 size | pageSize=0 | 无除 0 错误；msg 无堆栈 |
| 30 | API-PRJ-010 | PRJ | GET /idmp/project/page?pageNum=99 | P1 | 边界末页后 | rows=[]；total=5 |
| 31 | API-RISK-001 | RISK | GET /idmp/risk/list | P0 | smoke | code=200；data.length=3；每条 level=high |
| 32 | API-RISK-002 | RISK | GET /idmp/risk/list?level=high 过滤 | P0 | 过滤 | data 全 high；length=3 |
| 33 | API-RISK-003 | RISK | GET /idmp/risk/list?level=medium（A3 一致性 三态） | P1 | A3 关键证据 | 1. 不传 projectId（或传 projectId=all/global）→ 记录 length | **三态判定（同 AMB-01）**：<br>1=全局 medium=1 且 riskStats.medium=1 → ✅<br>0=按项目过滤默认（仅本人）→ 再试 projectId=all 看是否=1 → ✅ 也通过<br>all 后仍 0 且 riskStats.medium=1 → ❌ 不一致 |
| 34 | API-RISK-004 | RISK | GET /idmp/riskRule/list | P0 | smoke | code=200；data.length=5；ruleCode BUDGET_WARN/SCHEDULE_WARN/TEAM_SIZE/PROGRESS_STALE/RISK_CASCADE 全存在 |
| 35 | API-RISK-005 | RISK | GET /idmp/riskRule/1 详情 | P0 | 详情 | id=1 → ruleCode=BUDGET_WARN；enabled=1；triggerCondition=90 |
| 36 | API-BUDG-001 | BUDG | GET /idmp/budget/list | P1 | smoke | code=200；data.length=3；每条 totalBudget/spent/status 非空 |
| 37 | API-BUDG-002 | BUDG | GET /idmp/change/list?projectId=2086985374914007042 | P1 | 正常 | code=200；数组或空 |
| 38 | API-BUDG-003 | BUDG | GET /idmp/change/list 缺参 | P1 | 异常 | 不传 projectId → code=500；msg 不含堆栈 |
| 39 | API-DOC-001 | DOC | GET /idmp/document/list | P1 | smoke | code=200；data.length=3；fileName/fileUrl/fileSize 非空 |
| 40 | API-WF-001 | WF | GET /workflow/category/list | P1 | smoke | code=200；data.length=11；至少 1 条 ancestors 包含多段（3 级嵌套证明） |
| 41 | API-WF-002 | WF | GET /workflow/definition/list | P1 | smoke | code=200；total=23；rows.length ≥ 1；flowCode/flowName/categoryName/version/isPublish 全非空 |
| 42 | **API-WF-003（AMB-03 两档判据）** | WF | GET /workflow/definition/list 分类过滤 R10 参数名矩阵 | P1 | R10 参数名 | 1. 分别用 categoryId / category_id / category 3 种参数名传 IDMP审批 分类 id；2. 记录哪种 total=实际该分类下的流程数量（或 rows 全 category 匹配） | **两档判定（AMB-03）**：<br>✅ 通过：至少 1 种生效且结果正确<br>⚠️ 小缺陷（R10）：生效名≠规范 categoryId（登记"接口命名不一致"，不阻塞其他用例） |
| 43 | API-WF-004 | WF | GET /workflow/definition/list 分页边界 | P1 | 边界最后页 | pageNum=2 pageSize=20 → rows.length=3；total=23（20+3=23） |
| --- 以下 API-CONSIST-001a~h（REP-03 拆分：原 1 条拆 8 条，每 1 条独立覆盖矩阵行） --- |
| 44 | API-CONSIST-001a | CONSIST | A1 stats.total == list.length | P0 | A1 一致性 | 1. 同时请求 dashboard/overview + project/list；2. assert stats.total == list.length | 5 == 5 → ✅ 100% 通过 | 若不通过 = 登记 P0 一致性缺陷 |
| 45 | API-CONSIST-001b | CONSIST | A2 typeDistribution 按类型分组 == list 分组 | P0 | A2 一致性 | 1. 取 typeDistribution hardware count 与 list 过滤 type=hardware 长度对比；2. software 同理；3. assert 全相等 | 3 == 3, 2 == 2 → ✅ |
| 46 | API-CONSIST-001c | CONSIST | A3 riskStats vs risk/list 全局 level | P0 | A3 一致性（AMB-01） | 1. dashboard riskStats 3 level count；2. risk/list（projectId=all）按 level 聚合对比；3. assert 相等 | 3 高/1 中/0 低 → ✅ 或按三态 AMB-01 判定 |
| 47 | API-CONSIST-001d | CONSIST | A4 riskProjects == project.progress 中 riskLevel∈{med,high} ∧ status≠closed 去重数量（AMB-02 口径） | P0 | A4 一致性 | 按统一口径计算 dashboard projectProgress riskLevel=high/medium ∧ status≠closed 去重数量 == stats.riskProjects | 按 AMB-02 口径一致 = ✅ |
| 48 | API-CONSIST-001e | CONSIST | A5 文档按 projectId 分组 == project 5 条各自数量 | P1 | A5 一致性 | 1. document/list 按 projectId 分组计数；2. 预期：1 条项目有 3 条文档 + 其他 4 条项目 0 条 → 总计 3 | 一致 = ✅；不通过 = 输出明细（TR-005：collect-evidence 不直接判失败） |
| 49 | API-CONSIST-001f | CONSIST | A6 list 数组 length == page total | P0 | A6 一致性 | 1. project/list.length == project/page?pageSize=999.total | 5 == 5（或 3+2 拆分）→ ✅ |
| 50 | API-CONSIST-001g | CONSIST | A7 user list total == rows 累计 | P1 | A7 一致性 | 1. user/page 所有页 rows.length 求和 == total | 16 == 16 → ✅ |
| 51 | API-CONSIST-001h | CONSIST | A8 流程定义 categoryName 外键匹配分类 | P1 | A8 一致性 | 1. 取 workflow/definition/list 所有 categoryName；2. 与 workflow/category/list 全 categoryName 集合匹配；3. 无额外 categoryName 不在分类表 | 全在 categoryName 集合内 = ✅；若有 1 个额外 → 外键不一致缺陷（脏数据） |
