# ⚠️ DEPRECATED: 本 Skill 已废弃

## 状态：已废弃 (Deprecated)

本 Skill 原用于 JMeter 性能测试，项目已全面迁移到 Locust 框架。

## 替代方案

请使用 `perf-locust` Skill 进行性能测试。

## 迁移说明

- JMeter → Locust（Python 协程模型，与项目技术栈统一）
- 配置文件：`tests/performance/locust/config/load_profiles.yaml`
- 执行脚本：`tests/performance/locust/scripts/run_performance_staged.ps1`
- 详细说明：`tests/performance/locust/README.md`

## 维护状态

本目录保留仅为历史参考，不会再进行更新。
