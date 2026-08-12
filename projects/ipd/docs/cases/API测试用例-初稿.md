# IPD 管理系统 API 测试用例（初稿）

> **说明**: 共 42 条（测试计划预估 42）。编号前缀 `API-`，模块分为 AUTH(认证)、DASH(看板)、PRJ(项目)、RISK(风险)、BUDG(预算)、DOC(文档)、WF(工作流)、CONSIST(一致性 A1-A8)。**所有断言基于实测接口行为**（TR-001/TR-004）。未确认参数名处使用参数名矩阵断言（R10/R5），不按主观判断。

| 序号 | 用例编号 | 模块 | 接口 | 优先级 | 场景类型 | 测试步骤 | 预期结果 | 断言要点 |
|------|----------|------|------|--------|----------|----------|----------|----------|
| 1 | API-AUTH-001 | AUTH | POST /auth/login | P0 | smoke 正常 | 1. clientId + grantType(驼峰) + AES-256-ECB(key=client_id) + tenantId=000000；2. POST /prod-api/auth/login | HTTP 200；code=200；data.access_token 存在且长度 > 200 | 6 项登录参数正确（见需求分析 4.4.1）；token JWT.io 可解码且 payload.clientid = e5cd7e48... |
| 2 | API-AUTH-002 | AUTH | POST /auth/login | P0 | 异常（错误密码） | 1. password=wrongpwd（同样加密）；2. POST | code=500；msg="用户不存在/密码错误"；不返回 token | 不区分用户名还是密码错（防暴力破解） |
| 3 | API-AUTH-003 | AUTH | POST /auth/login | P0 | 异常（clientId 写成下划线 client_id） | 1. 下划线字段名：`client_id=xxx`；2. POST | code=500；msg="认证客户端id不能为空" | 证明 IPD 必须用驼峰 clientId（≠ CRM 默认，记录到知识库） |
| 4 | API-AUTH-004 | AUTH | POST /auth/login | P0 | 异常（grantType 写成 grant_type 下划线） | 1. `grant_type=password`；2. POST | code=500；msg="认证权限类型不能为空" | 同上，证明 grantType 驼峰 |
| 5 | API-AUTH-005 | AUTH | POST /auth/login | P0 | 异常（缺少 tenantId） | 1. 不传 tenantId；2. POST | 记录真实返回码/msg（如果必填校验失败，记录 msg） | 真实返回为准；不对比文档 |
| 6 | API-AUTH-006 | AUTH | POST /auth/login | P1 | 边界（grantType=非 password 枚举） | 1. grantType=pwd/account/1 等 5 个值；2. POST | 全部 code=500，msg="认证权限类型错误" | 防止绕过认证类型 |
| 7 | API-AUTH-007 | AUTH | GET /auth/code | P0 | smoke | 1. GET /auth/code | code=200；captchaEnabled=false；uuid/img=null | 验证默认关闭验证码 |
| 8 | API-AUTH-008 | AUTH | GET /idmp/dashboard/overview（未授权） | P0 | 权限 | 1. 不带任何 header 访问 dashboard | 401/403；code≠200；无业务数据 | 与 SEC-AUTH-001 重复但此用例做断言细节 |
| 9 | API-USER-001 | AUTH | GET /system/user/profile | P0 | smoke | 1. 带正确 header | code=200；data.user.userName="赵经理"；roleGroup="项目经理"；user.userId 与 JWT 中 userId 一致 | 数值/字符串类型差异记录（JWT 中 number vs profile 中 string） |
| 10 | API-USER-002 | AUTH | GET /system/menu/getRouters | P0 | smoke | 1. 带正确 header | code=200；data 长度 3；meta.title 含"统计分析看板/项目管理/工作流"三一级菜单 | 三个一级菜单同时存在且顺序或存在性校验 |
| 11 | API-USER-003 | AUTH | GET /system/dept/list | P0 | 权限边界（正确行为=403） | 1. 带赵经理 token | code=403；msg="没有访问权限，请联系管理员授权" | ✅ 这是通过，不进缺陷 |
| 12 | API-USER-004 | AUTH | GET /system/role/list | P0 | 权限边界 403 | 同上 | 同上 | ✅ 通过 |
| 13 | API-USER-005 | AUTH | GET /system/menu/build | P0 | 权限边界 403 | 同上 | 同上 | ✅ 通过 |
| 14 | API-USER-006 | AUTH | GET /system/dict/data/type/sys_yes_no | P1 | smoke | 1. 请求 | code=200；data 长度 2；dictLabel=是 dictValue=Y 和 否=N | sys_yes_no 字典正确 |
| 15 | API-USER-007 | AUTH | GET /system/dict/data/type/common_status | P2 | 边界空数据 | 1. 请求 | code=200；data=[] | 空数组不报错（IPD 专用枚举未在此字典，属于代码内枚举，不判缺陷） |
| 16 | API-USER-008 | AUTH | GET /system/user/list | P1 | smoke | 1. 请求 | code=200；total=16；rows length ≤ 16（默认分页） | user/list 可访问，移交 R4 安全专项（见 SEC-R4-001） |
| 17 | API-DASH-001 | DASH | GET /idmp/dashboard/overview | P0 | smoke | 1. 正常请求 | code=200；data.stats 含 5 字段；data.typeDistribution.length=2；data.riskStats 含 3 字段；data.projectProgress.length=5 | 5 块统计结构齐全 |
| 18 | API-DASH-002 | DASH | GET /idmp/dashboard/overview | P0 | 边界 | 1. 连续 3 次请求（间隔 1s）统计值；2. 断言 stable | 3 次 stats 完全一致；projectProgress 5 条顺序一致 | 防并发读导致漂移 |
| 19 | API-PRJ-001 | PRJ | GET /idmp/project/list | P0 | smoke | code=200；data 数组长度=5 | 数组结构（非 total/rows） |
| 20 | API-PRJ-002 | PRJ | GET /idmp/project/page | P0 | smoke 分页第一页 | pageNum=1 pageSize=3 → code=200；total=5；rows.length=3 | {total, rows} 结构；第一页 rows 3 条 id 与 list 前 3 条相同 |
| 21 | API-PRJ-003 | PRJ | GET /idmp/project/{已存在id} | P0 | smoke 详情 | id=2086985374914007042 → code=200；data.projectName="回路监控箱设备"；data.type="hardware"；data.phase="closed" | 27 字段全存在（检查 key 集合数量 ≥ 27） |
| 22 | API-PRJ-004 | PRJ | GET /idmp/project/{不存在id} | P1 | 异常 | id=9999999999999999999 | 返回 code=500 或 404 或空对象（记录真实 msg，不按推测）；不出现 SQL 堆栈 |
| 23 | API-PRJ-005 | PRJ | GET /idmp/project/page?type=hardware | P0 | 过滤 | pageNum=1 pageSize=10 type=hardware → rows 全 type=hardware；长度 = 3（如果 total 字段存在则 total=3） | 过滤正确 |
| 24 | API-PRJ-006 | PRJ | GET /idmp/project/page?type=software | P0 | 过滤 | rows 全 software；长度=2 | 同上 |
| 25 | API-PRJ-007 | PRJ | GET /idmp/project/page?type=invalid_type | P1 | 异常过滤 | type=xxxinvalid → code=200；rows 可能=[] 或全部（记录真实返回，若返回 500 算参数校验缺陷） | 不出现 500 |
| 26 | API-PRJ-008 | PRJ | GET /idmp/project/page?pageNum=-1 | P1 | 边界非法页码 | pageNum=-1 pageSize=10 → 记录真实返回（code 400/500/200）；不允许 SQL 异常堆栈 |
| 27 | API-PRJ-009 | PRJ | GET /idmp/project/page?pageSize=0 | P1 | 边界非法 size | pageSize=0 → 记录真实返回（200 或 400）；不出现除 0 错误 |
| 28 | API-PRJ-010 | PRJ | GET /idmp/project/page?pageNum=99&pageSize=100 | P1 | 边界末页之后 | rows=[]；total=5（仍存在） | 空数组不报错 |
| 29 | API-RISK-001 | RISK | GET /idmp/risk/list | P0 | smoke | code=200；data.length=3；每条含 level=high | 结构齐全 |
| 30 | API-RISK-002 | RISK | GET /idmp/risk/list?level=high | P0 | 过滤 level | code=200；data 全 level=high；length=3 | 过滤正确 |
| 31 | API-RISK-003 | RISK | GET /idmp/risk/list?level=medium | P1 | 过滤 + A3 一致性 | 查询 level=medium；记录 length：若=1 → A3 中缺失的那条 medium 风险因默认 projectId 过滤排除；若=0 → 需验证传 projectId=all 或不传 | 这是 A3/R5 关键证据 |
| 32 | API-RISK-004 | RISK | GET /idmp/riskRule/list | P0 | smoke | code=200；data.length=5；5 条 ruleCode 与需求一致（BUDGET_WARN 等） | 5 条预置规则存在 |
| 33 | API-RISK-005 | RISK | GET /idmp/riskRule/1 | P0 | 详情 | id=1 → code=200；data.ruleCode="BUDGET_WARN"；data.enabled=1 | 规则详情 |
| 34 | API-BUDG-001 | BUDG | GET /idmp/budget/list | P1 | smoke | code=200；data.length=3；每条含 totalBudget/spent/status | 3 条预算存在 |
| 35 | API-BUDG-002 | BUDG | GET /idmp/change/list?projectId=2086985374914007042 | P1 | 正常 | code=200；空或数组 | 带 projectId 200 通过 |
| 36 | API-BUDG-003 | BUDG | GET /idmp/change/list | P1 | 异常缺参 | 不传 projectId → code=500；msg 不含堆栈信息（防信息泄漏）； |
| 37 | API-DOC-001 | DOC | GET /idmp/document/list | P1 | smoke | code=200；data.length=3；每条含 fileName/fileUrl/fileSize | fileUrl 非空指向 OSS |
| 38 | API-WF-001 | WF | GET /workflow/category/list | P1 | smoke | code=200；data.length=11；每条 categoryId/parentId/categoryName 非空；嵌套 3 级可通过 ancestors 路径长度验证 | 至少 1 条 ancestors 含多段（不是"0"） |
| 39 | API-WF-002 | WF | GET /workflow/definition/list | P1 | smoke | code=200；total=23；rows.length ≥ 1；每条 flowCode/flowName/categoryName/version/isPublish 非空 | 结构 {total, rows} 正确 |
| 40 | API-WF-003 | WF | GET /workflow/definition/list?categoryId=2099000000000000001 | P1 | R10 参数名矩阵 | 1. 分别用 categoryId / category_id / category 3 种参数名传 IDMP审批 分类 id；2. 记录哪种返回 rows 全 category=2099... | 至少 1 种生效；若 3 种都 total=23（未过滤）→ 登记过滤参数 Bug（R10） |
| 41 | API-WF-004 | WF | GET /workflow/definition/list?pageNum=2&pageSize=20 | P1 | 边界最后页 | rows.length=3；total=23 | 23 = 20 + 3 分页正确 |
| 42 | API-CONSIST-001 | CONSIST | A1-A8 8 条一致性 | P0 | 数据一致性 | 1. 同时执行 18 条接口；2. 执行 A1(stats.total==list.length)/A2(typeDistribution count==list 分组)/A3(riskStats vs global risk list 按 level)/A4(riskProjects vs progress.riskLevel 去重)/A5(文档按 projectId 分组)/A6(list length==page total)/A7(user list total vs rows length)/A8(流程定义 categoryName 外键匹配分类) | A1/A2/A6 必须 100% 通过（P0）；A3/A4/A5 若不通过 → collect-evidence 打印明细，不直接判失败（TR-005 策略） | 同测试方案 §5.5 |
