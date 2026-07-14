---
name: coverage-matrix
description: 用于生成和更新 API、UI、嵌入式协议/端云联调覆盖矩阵。Use when Codex must map reviewed test cases to automation scripts, execution layers, implementation status, execution status, blocked reasons, and decide whether full-api, full-ui, or first-version full-embedded can be claimed.
---

# 输入
- `docs/AI执行最小规则.md`
- `docs/cases/接口测试用例-评审版.md`
- `docs/cases/功能测试用例-评审版.md`
- `docs/cases/嵌入式测试用例-评审版.md`
- `tests/api/testsuites/`
- `tests/ui/specs/`
- `tests/embedded/testsuites/`
- 必要配置文件：`tests/api/pytest.ini`、`tests/ui/playwright.config.ts`
- `docs/阶段执行检查清单.md`
- `docs/reports/参考资料索引.md`
- `docs/reports/完整测试流程重构方案.md`（仅在当前 SKILL 未覆盖细节或需追溯历史设计时按需读取）
- `docs/reports/自动化与专项执行阶段编排方案.md`（仅在当前 SKILL 未覆盖细节或需追溯历史设计时按需读取）

# 输出
- `docs/reports/API自动化覆盖矩阵.md`
- `docs/reports/UI自动化覆盖矩阵.md`
- `docs/reports/嵌入式覆盖矩阵.md`

# 工作流
1. 先读取 `docs/AI执行最小规则.md`，再读取对应专项的评审版测试用例。
2. 逐条提取序号、用例编号、模块/接口/场景、自动化结论、执行层级。
3. 扫描对应测试套件目录，识别已有脚本和测试用例；不得扫描依赖、虚拟环境、报告、缓存和历史归档目录。
4. 将每条评审版用例映射到目标脚本、当前状态、执行状态和阻塞原因。
5. 对没有脚本覆盖的自动化用例写“未实现”，不得省略。
6. 对没有门禁条件的用例写“阻塞”或“待确认”。
7. 汇总总用例数、自动化候选数、已实现数、已执行数、未实现数、阻塞数。
8. 标记当前用例是否允许进入并行执行、串行执行或必须阻塞。
9. 明确当前只能称为 smoke、partial、full-api、full-ui、first-version full-embedded 或 flow-closed-with-exceptions。

# AI 读取优化
- 默认输入顺序：`docs/AI执行最小规则.md` -> 评审版用例 -> 对应测试套件目录 -> 阶段门禁清单。
- 扫描脚本时默认排除 `node_modules/`、`.venv/`、`__pycache__/`、`.pytest_cache/`、`reports/`、`test-results/`、`playwright-report/` 和 `docs/test-runs/`。
- `完整测试流程重构方案.md`、`自动化与专项执行阶段编排方案.md` 只作为参考资料，不作为默认输入。

# 覆盖矩阵字段
| 字段 | 要求 |
|------|------|
| 序号 | 保留评审版序号 |
| 用例编号 | 保留评审版编号 |
| 模块/接口/场景 | 可追溯到评审版用例 |
| 用例标题 | 简明描述 |
| 断言来源 | 实测接口基线、文档差异核对、已确认契约、页面行为、协议样例或待确认 |
| 评审自动化结论 | 自动化、半自动、不自动化、阻塞 |
| 执行层级 | smoke、readonly-regression、semi-auto、write-regression、protocol-cloud、performance、security、manual、blocked |
| 目标脚本 | 已有脚本路径或计划脚本路径 |
| 当前状态 | 已实现、未实现、阻塞、待确认 |
| 执行状态 | 已执行、未执行、跳过、失败、通过 |
| 执行编排 | 可并行、需串行、阻塞、后置执行 |
| 说明 | 未实现原因、阻塞原因或执行证据 |

# 专项规则
- API 覆盖矩阵必须映射接口评审版用例到 pytest 脚本。
- API 覆盖矩阵必须标明断言来源；真实接口可访问时优先使用“实测接口基线”，未确认文档差异只能标为“文档差异核对/待确认”。
- UI 覆盖矩阵必须映射功能评审版用例到 Playwright 脚本。
- 嵌入式覆盖矩阵第一版只映射协议/端云联调用例，包括协议、设备身份、上报样例、平台接收、API 查询、UI 展示。
- 嵌入式第一版不得把固件、硬件、OTA、HIL、串口日志标记为已完成；这些只能写后续范围、未执行或阻塞。

# 执行编排规则
- API/UI 的 smoke、readonly-regression、semi-auto 可标记为“可并行”。
- API/UI 的 write-regression 默认标记为“需串行”，除非明确有数据隔离和回滚策略。
- 嵌入式 protocol-cloud 依赖 API 查询能力和协议/设备门禁；满足时可与 API/UI 只读层级并行。
- 性能用例必须标记为“后置执行”，依赖 API/UI 完成。
- 安全用例必须标记为“后置执行”，依赖性能完成。
- 被 API 连接级失败影响的 UI、嵌入式、性能、安全用例应标记“阻塞”或“未执行”。

# 强制规则
- 覆盖矩阵必须逐条覆盖评审版用例，不得只列已有脚本。
- 存在“自动化但未实现”的用例时，只能执行 partial 或 smoke，不得宣称完整自动化完成。
- full-api/full-ui 只在所有可自动化用例已实现并按计划执行后允许使用。
- first-version full-embedded 只代表协议/端云联调范围完成，不代表完整嵌入式端侧测试完成。
- 不得将性能或安全标记为与 API/UI 同阶段并行执行。
- 未执行的内容必须明确写“未执行”。
- 不得把未确认接口文档契约映射为 smoke 硬断言；只能映射为差异核对、待确认或自动化维护项。
- 输出必须按顺序包含：当前阶段、输入文件、产出文件、正文/核心内容、执行结论、风险与待确认项、下一步建议。正文/核心内容必须位于执行结论、风险与待确认项、下一步建议之前；执行结论、风险与待确认项、下一步建议必须作为文档收尾部分。
