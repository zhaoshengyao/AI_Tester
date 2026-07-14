---
name: ui-auto-playwright
description: 根据评审后的功能测试用例生成并执行 Playwright UI 自动化和兼容性测试，输出脚本、报告和缺陷清单。
---

# 输入
- docs/AI执行最小规则.md
- docs/cases/功能测试用例-评审版.md
- docs/阶段执行检查清单.md
- docs/reports/UI自动化覆盖矩阵.md
- docs/reports/参考资料索引.md
- docs/reports/自动化与专项执行阶段编排方案.md（仅在当前 SKILL 未覆盖细节或需追溯历史设计时按需读取）

# 输出
- tests/ui/
- tests/ui/reports/
- docs/reports/UI自动化覆盖矩阵.md
- docs/reports/UI自动化测试报告.md
- docs/reports/UI兼容性测试报告.md
- docs/defects/UI缺陷清单.md
- docs/test-runs/YYYYMMDD-HHMMSS/

# 工作流
1. 先读取 `docs/AI执行最小规则.md`，再读取评审版功能测试用例
2. 生成 UI 自动化覆盖矩阵，逐条映射评审版用例到脚本、执行层级和状态
3. 按执行层级拆分：smoke、readonly-regression、semi-auto、write-regression、compatibility
4. 设计页面对象、选择器、断言、测试数据和可回滚数据策略
5. 生成或补齐 Playwright 脚本
6. 静态校验脚本与覆盖矩阵，确认不遗漏已标记“自动化”的用例
7. 检查 API smoke 或服务/API 基础门禁结果
8. 先执行 UI smoke，覆盖登录、首页、一级菜单和核心页面可达性
9. 分析 UI smoke 结果，区分页面阻断、认证阻断、选择器问题、数据问题、偶发超时和覆盖缺口
10. 输出下一步决策：continue/retest/collect-evidence/downgrade/stop/handoff
11. 仅执行下一步决策允许的 readonly-regression、semi-auto、compatibility、write-regression 或复测范围
12. 收集截图、日志、失败信息
13. 输出报告和缺陷清单

# AI 读取优化
- 默认输入顺序：`docs/AI执行最小规则.md` -> 评审版用例 -> 覆盖矩阵 -> 阶段门禁清单。
- `自动化与专项执行阶段编排方案.md` 只作为参考资料，不作为默认输入。
- `docs/reports/UI兼容性测试报告.md` 和 `docs/defects/UI缺陷清单.md` 为正式产物名；历史别名如需保留，只能作为同步副本，不作为系统汇总主输入。

# 执行入口
- Windows: `pwsh -File scripts/run-ui-tests.ps1`
- Bash: `bash scripts/run-ui-tests.sh`

# 报告必须包含
- 执行命令、浏览器、视口、被测地址、账号角色和执行时间。
- 用例总数、执行数、通过数、失败数、跳过数、未实现数、阻塞数。
- API smoke 或服务/API 基础门禁引用。
- 失败截图、trace、错误堆栈、页面 URL。
- 覆盖矩阵更新结果。
- 未覆盖页面和未实现用例说明。
- UI smoke 后分析和下一步决策，说明为什么继续、复测、补资料、降级、停止或移交。
- 本轮测试时间目录和原始报告归档路径。

# 强制规则
- 评审版功能用例不存在或评审未通过时，不得执行 UI 自动化
- 执行前必须先生成或更新 `docs/reports/UI自动化覆盖矩阵.md`
- Node.js 门禁只设置最低版本要求：低于 Node.js 18 时停止并写“未执行”；Node.js 18 及以上不得仅因非 LTS 或较新主版本停止，必须以 Playwright 真实执行结果判断。
- 覆盖矩阵必须列出每条功能评审版用例的序号、用例编号、自动化结论、目标脚本、执行层级、当前状态
- 若评审版中标记为“自动化”的用例未落到 Playwright 脚本，必须在覆盖矩阵和报告中写明“未实现”，不得只执行已有 smoke 后宣称 UI 自动化完成
- 默认执行 full-ui 前，必须完成所有“自动化”用例的脚本实现；否则只能执行 smoke/partial，并明确未覆盖范围
- UI smoke 后不得默认继续 full-ui；必须基于真实结果和覆盖矩阵输出下一步决策。
- UI 可与 API 受控并行执行 smoke、readonly-regression、semi-auto
- API 连接级失败时，UI 必须停止并写“未执行/阻塞”
- API 登录/认证 smoke 失败且确认为真实认证不可用时，UI 后续执行应停止；若只是未确认文档差异或 API 断言口径问题，UI 可继续基础自动化并在报告中标记联动风险
- UI write-regression 不默认与 API 并行；必须有数据隔离和回滚策略
- 写操作类用例没有数据回滚策略时，不得真实提交；只能做 semi-auto 入口、弹窗、必填校验
- 页面对象必须按业务页面拆分，不得把所有页面流程堆在一个 login/spec 文件中
- 每个一级菜单至少应有页面可达性用例；每个核心列表至少应有展示用例；核心筛选和详情入口应优先自动化
- 未实际执行 Playwright 时，报告必须写“未执行”并说明原因
- 原始 HTML、trace、截图或视频必须保存到 `tests/ui/reports/` 或说明未生成原因
- 本轮 UI 自动化报告、覆盖矩阵、缺陷清单和原始报告必须同步归档到 `docs/test-runs/YYYYMMDD-HHMMSS/`
- 报告必须基于真实执行结果，不得虚构通过率
- 下一步决策为 downgrade 时，必须写明只执行哪些页面/用例，哪些页面/用例未执行。
- 输出必须按顺序包含：当前阶段、输入文件、产出文件、正文/核心内容、执行结论、风险与待确认项、下一步建议。正文/核心内容必须位于执行结论、风险与待确认项、下一步建议之前；执行结论、风险与待确认项、下一步建议必须作为文档收尾部分

# 执行层级
| 层级 | 含义 | 是否默认执行 |
|------|------|--------------|
| smoke | 登录、首页、核心导航、每个一级菜单可达性 | 是 |
| readonly-regression | 列表展示、筛选、详情查看、只读弹窗 | 是 |
| semi-auto | 写操作入口、弹窗、必填校验，不提交真实数据 | 是 |
| write-regression | 新增、编辑、删除、处理、同步等真实写操作 | 否，需回滚策略 |
| compatibility | Chromium/Firefox/Edge 等浏览器兼容性 | 按需 |
