---
name: api-auto
description: 根据评审后的接口测试用例生成并执行基于 pytest 的接口自动化测试，输出脚本、报告和缺陷清单。
---

# 输入
- docs/AI执行最小规则.md
- docs/cases/接口测试用例-评审版.md
- docs/阶段执行检查清单.md
- docs/reports/API自动化覆盖矩阵.md
- docs/reports/参考资料索引.md
- docs/reports/自动化与专项执行阶段编排方案.md（仅在当前 SKILL 未覆盖细节或需追溯历史设计时按需读取）

# 输出
- tests/api/
- tests/api/reports/
- docs/reports/API自动化覆盖矩阵.md
- docs/reports/接口自动化测试报告.md
- docs/defects/接口缺陷清单.md
- docs/test-runs/YYYYMMDD-HHMMSS/

# 工作流
1. 先读取 `docs/AI执行最小规则.md`，再读取接口测试用例
2. 生成 API 自动化覆盖矩阵，逐条映射评审版用例到 pytest 脚本、执行层级和状态
3. 明确环境、认证、测试数据准备
4. 设计 clients、testdata、testsuites 分层结构
5. 按用例来源依据生成 pytest 脚本、fixture、环境配置和参数化测试数据，区分实测行为断言、文档差异核对和已确认契约断言
6. 静态校验脚本与覆盖矩阵，确认自动化范围与评审版一致
7. 先执行 API smoke，至少覆盖认证、服务基础连通和核心只读接口
8. 分析 API smoke 结果，区分连接级失败、认证失败、业务失败、已确认契约不一致、文档差异待确认、偶发失败和证据不足
9. 输出下一步决策：continue/retest/collect-evidence/downgrade/stop/handoff
10. 仅执行下一步决策允许的 readonly-regression、security、write-regression 或复测范围
10.1 API full 失败后的修复接回必须先执行 smoke，再执行 failed-retest 定向复测，最后执行 full；failed-retest 通过不能替代 full。
11. 汇总 HTML/XML 原始报告
12. 生成接口自动化测试报告和缺陷清单

# AI 读取优化
- 默认输入顺序：`docs/AI执行最小规则.md` -> 评审版用例 -> 覆盖矩阵 -> 阶段门禁清单。
- `自动化与专项执行阶段编排方案.md` 只作为参考资料，不作为默认输入。
- 静态收集用例时使用 `python -m pytest --collect-only -q -o addopts=''`，避免 pytest.ini 中的 HTML/JUnit 配置污染正式原始报告。

# 执行入口
- Windows: `pwsh -File scripts/run-api-tests.ps1`
- Bash: `bash scripts/run-api-tests.sh`
- API smoke: `pwsh -File scripts/run-api-tests.ps1 -Mode smoke`
- API 失败项定向复测: `pwsh -File scripts/run-api-tests.ps1 -Mode failed-retest`
- API full 回归: `pwsh -File scripts/run-api-tests.ps1 -Mode full`
- 单项定位复测: `pwsh -File scripts/run-api-tests.ps1 -Mode failed-retest -PytestKeyword "test_name"`

# 报告必须包含
- 执行命令、被测地址、认证方式和执行时间。
- 用例总数、执行数、通过数、失败数、跳过数、未实现数、阻塞数。
- API smoke 结果。
- 失败接口的请求、响应、状态码、错误信息。
- 文档与实际接口差异：实测行为、文档描述、当前处理方式和待确认结论。
- API full 失败项缺陷清单：所有失败项均须登记，文档与实际接口不一致登记为接口契约/文档一致性缺陷。
- 覆盖矩阵更新结果。
- 是否允许 UI、嵌入式、性能、安全继续。
- 冒烟后分析和下一步决策，说明为什么继续、复测、补资料、降级、停止或移交。
- 本轮测试时间目录和原始报告归档路径。

# 强制规则
- 优先按业务域拆分 clients 和 testsuites
- 测试数据与测试逻辑分离
- 不得只生成一次性 requests 脚本
- 接口自动化断言必须优先依据评审版用例中的实测接口基线和已确认业务规则。
- 有接口文档但真实接口不一致时，未确认的文档契约只能作为差异核对或待确认项，不得作为 smoke 阻断断言。
- 没有接口文档时，不得生成依赖“文档应返回”的断言；必须基于实测状态码、响应结构、字段存在性、业务一致性、鉴权表现和错误响应建立基线断言。
- 只有产品/研发确认文档契约为准，或评审版用例明确标记为“已确认契约”时，才允许按接口文档字段做硬断言。
- 登录认证类脚本必须先识别真实鉴权机制：JWT、session/cookie、token header 或其他方式；未确认前不得强制要求某一种鉴权返回字段。
- 执行前必须先生成或更新 `docs/reports/API自动化覆盖矩阵.md`
- 覆盖矩阵必须列出每条接口评审版用例的序号、用例编号、自动化结论、目标脚本、执行层级、当前状态
- 若评审版中标记为“自动化”的接口用例未落到 pytest 脚本，必须在覆盖矩阵和报告中写明“未实现”
- API smoke 必须优先执行，且结果必须写入报告
- API smoke 后不得默认继续；必须基于真实结果输出下一步决策。
- API full 失败后不得直接恢复嵌入式、性能或安全；必须先完成 smoke、failed-retest、full 三段复测恢复。
- failed-retest 仅用于缺陷修复验证和证据补充，不能作为 full-api 或后置专项放行依据。
- API full 失败项必须全部输出到 `docs/defects/接口缺陷清单.md`；不得因文档差异、契约不清或需要责任方判断关闭方式而暂不登记缺陷。
- API 连接级失败时，必须停止 UI、嵌入式端云联调、性能、安全，并在报告中写明阻断范围
- API 登录/认证 smoke 失败时必须先判断原因；真实认证不可用应阻断 UI 后续执行，未确认文档差异或断言口径问题不得直接阻断 UI
- API 与 UI 可受控并行，但 API 失败结果必须能中断 UI 后续执行
- 写操作、删除、触发同步、修改密码等没有回滚策略时，不得自动执行
- 未执行测试不得写成已完成
- 原始 HTML/XML/JSON/JUnit 报告必须保存到 `tests/api/reports/`，没有原始报告时必须说明原因
- 本轮接口自动化报告、覆盖矩阵、缺陷清单和原始报告必须同步归档到 `docs/test-runs/YYYYMMDD-HHMMSS/`
- 报告必须基于真实执行结果
- 评审版接口用例不存在或评审未通过时，不得执行接口自动化
- 下一步决策为 collect-evidence/handoff 时，不得做后端修复，只输出证据缺口、缺陷影响和复测条件。
- 输出必须按顺序包含：当前阶段、输入文件、产出文件、正文/核心内容、执行结论、风险与待确认项、下一步建议。正文/核心内容必须位于执行结论、风险与待确认项、下一步建议之前；执行结论、风险与待确认项、下一步建议必须作为文档收尾部分
