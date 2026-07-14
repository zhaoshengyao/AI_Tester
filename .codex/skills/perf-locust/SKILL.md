---
name: perf-locust
description: 根据评审后的性能测试用例生成 Locust 脚本并执行性能测试，输出性能报告和缺陷清单。支持 API 压测和 UI 全链路压测。
---

# 输入
- docs/AI执行最小规则.md
- docs/cases/性能测试用例-评审版.md
- docs/阶段执行检查清单.md
- docs/reports/接口自动化测试报告.md
- docs/reports/UI自动化测试报告.md
- docs/reports/参考资料索引.md
- docs/reports/参考资料/JMeter转Locust改造方案.md

# 输出
- tests/performance/locust/
- tests/performance/results/locust/
- docs/reports/性能测试报告.md
- docs/test-runs/YYYYMMDD-HHMMSS/defects/性能缺陷清单.md

# 工作流
1. 先读取 `docs/AI执行最小规则.md`，再读取性能测试用例
2. 检查 API/UI 自动化是否已完成或明确未执行原因
3. 检查是否存在 API/UI 连接级失败未处理
4. 检查 Locust 配置、执行入口和压测授权
5. 提炼场景、并发、时长、指标
6. 生成 Locust 脚本（API 压测 + UI 全链路压测）
7. 静态校验脚本与压测参数
8. 先执行性能 smoke，不直接执行大并发或综合压测
9. 压测后执行 smoke/API 恢复验证
10. 分析性能 smoke 结果：错误率、P95/P99、吞吐、超时类型、成功/失败分层、时间窗口退化、恢复 smoke
11. 输出下一步决策：continue/retest/collect-evidence/downgrade/stop/handoff
12. 仅在下一步决策为 continue 且风险可接受时，才执行更高并发、综合场景或长稳场景
13. 汇总吞吐、响应时间、错误率、资源瓶颈、证据缺口
14. 输出报告与缺陷

# AI 读取优化
- 默认输入顺序：`docs/AI执行最小规则.md` -> 评审版用例 -> API/UI 正式报告 -> 阶段门禁清单 -> 改造方案参考。

# 执行入口
- Windows: `pwsh -File scripts/run-perf-tests.ps1`
- Bash: `bash scripts/run-perf-tests.sh`
- 直接执行: `locust -f tests/performance/locust/api/locustfile_smoke.py --host=http://localhost:5173`

# 报告必须包含
- Locust 版本信息：`locust --version`。
- 执行命令、执行时间、被测地址。
- 场景、用户数、孵化率、持续时间、吞吐目标、停止条件。
- RPS/TPS、响应时间、P95/P99、错误率、吞吐量。
- 压测前 API/UI 状态。
- 压测后 smoke/API 恢复验证结果。
- 原始报告（HTML）、日志路径。
- 性能 smoke 后分析和下一步决策，说明为什么继续加压、复测、补资料、降级、停止或移交。
- 证据缺口：后端日志、慢 SQL、CPU/内存、线程池/连接池、数据规模等缺失项。
- 未执行或中止原因。

# 性能自适应决策
| 决策 | 触发条件 | 后续动作 |
|------|----------|----------|
| continue | smoke 错误率、P95/P99、恢复 smoke 达标，且服务稳定 | 可继续单场景加深、综合场景或更高并发 |
| retest | 结果疑似偶发、样本不足、环境波动或与历史不一致 | 原条件或缩小范围复测，不直接加压 |
| collect-evidence | 已超阈值、超时或吞吐异常，但缺少服务端证据 | 暂停加压，补后端日志、慢 SQL、资源监控、数据规模 |
| downgrade | 综合场景不具备条件，但单接口 smoke 可执行 | 只执行单接口或低并发子集 |
| stop | 服务不可用、连接级失败、压测后恢复失败或风险不可接受 | 停止性能深化和后续安全主动扫描 |
| handoff | 性能缺陷需研发/环境确认 | 输出缺陷证据、影响和复测条件 |

# UI 压测特别规则
- UI 压测资源消耗远高于 API 压测，初始并发从 5 开始
- 必须使用 `locust-plugins` 的 `PlaywrightUser` 和 `@pw` 装饰器
- 每个任务使用独立浏览器上下文，会话隔离
- UI 压测重点关注 TPS、任务耗时、错误率
- UI 压测失败时优先检查元素选择器、页面加载时间

# 强制规则
- 性能测试必须在 API 自动化和 UI 自动化之后执行
- API/UI 自动化尚未完成且未明确未执行原因时，不得执行性能测试
- 未确认压测授权、目标环境或性能指标时，不得执行压测
- 未确认 Locust 可执行、并发数、运行时间、孵化率、停止条件时，不得执行压测
- 若 API/UI 阶段存在连接级失败，性能测试必须标记"未执行"，不得继续压测
- 生成 Locust 脚本不等于已执行性能测试；报告必须区分"已生成""已执行""未执行"
- 未实际执行 Locust 时，报告必须写"未执行"并说明原因
- 原始 HTML 报告、日志必须保存到 `tests/performance/results/locust/`，没有原始结果时必须说明原因
- 报告必须基于真实 Locust 结果，不得虚构 TPS、响应时间或错误率
- 性能 smoke 未达标时，不得默认直接执行 50 并发、长稳或更高压力；必须先判断 retest、collect-evidence、downgrade、stop 或 handoff。
- collect-evidence 时必须列出需要补充的服务端证据和用途，不得把"性能分析"停留在结果摘要。
- 性能测试完成或明确未执行原因后，才允许进入安全测试
- 输出必须按顺序包含：当前阶段、输入文件、产出文件、正文/核心内容、执行结论、风险与待确认项、下一步建议。正文/核心内容必须位于执行结论、风险与待确认项、下一步建议之前；执行结论、风险与待确认项、下一步建议必须作为文档收尾部分