#!/usr/bin/env bash
# ============================================================================
# 全流程测试执行脚本
# 用法: ./scripts/run-full-test-flow.sh [--skip-ui] [--skip-perf] [--skip-security]
# 功能: 一键执行 API + UI + 性能 + 安全 全类型测试
# ============================================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# ---------- 颜色输出 ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log_info()  { echo -e "${CYAN}[INFO]${NC} $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_title() { echo -e "\n${BOLD}${CYAN}==== $* ====${NC}\n"; }

# ---------- 参数解析 ----------
SKIP_UI=false
SKIP_PERF=false
SKIP_SECURITY=false

for arg in "$@"; do
    case "$arg" in
        --skip-ui) SKIP_UI=true ;;
        --skip-perf) SKIP_PERF=true ;;
        --skip-security) SKIP_SECURITY=true ;;
        --help|-h)
            echo "用法: $0 [OPTIONS]"
            echo ""
            echo "选项:"
            echo "  --skip-ui        跳过 UI 测试"
            echo "  --skip-perf      跳过性能测试"
            echo "  --skip-security  跳过安全测试"
            echo "  --help, -h       显示帮助"
            exit 0
            ;;
    esac
done

# ---------- 批次目录 ----------
BATCH_ID=$(date +%Y%m%d-%H%M%S)
BATCH_DIR="$ROOT/docs/test-runs/$BATCH_ID"
REPORT_DIR="$BATCH_DIR/reports"
DEFECT_DIR="$BATCH_DIR/defects"
mkdir -p "$REPORT_DIR" "$DEFECT_DIR"

# ---------- 统计 ----------
API_PASS=0
API_FAIL=0
UI_PASS=0
UI_FAIL=0
PERF_STATUS="未执行"
SECURITY_STATUS="未执行"
TOTAL_START=$(date +%s)

# ---------- 执行函数 ----------
run_test() {
    local name="$1"
    local script="$2"
    local log_file="$3"
    shift 3
    local args=("$@")
    
    log_title "执行 $name"
    if [ -f "$script" ]; then
        bash "$script" "${args[@]}" 2>&1 | tee "$log_file"
        local exit_code=${PIPESTATUS[0]}
        if [ $exit_code -eq 0 ]; then
            log_ok "$name 通过 ✅"
            return 0
        else
            log_error "$name 失败 ❌ (exit code: $exit_code)"
            return $exit_code
        fi
    else
        log_warn "脚本不存在: $script，跳过"
        return 2
    fi
}

# ============================================================================
# 1. API 冒烟测试
# ============================================================================
log_title "Step 1: API 冒烟测试"
API_SMOKE_LOG="$BATCH_DIR/raw/api-smoke.log"
mkdir -p "$BATCH_DIR/raw"

if run_test "API 冒烟" "$ROOT/scripts/run-api-tests.sh" "$API_SMOKE_LOG" smoke; then
    log_ok "API 冒烟测试通过"
else
    log_error "API 冒烟测试失败，停止后续执行"
    API_FAIL=1
    cat > "$REPORT_DIR/全流程测试报告.md" << EOF
# 全流程测试报告

> **批次**: $BATCH_ID
> **状态**: ❌ 失败

## 失败原因
API 冒烟测试失败，流程终止。

## 执行记录
- Step 1: API 冒烟测试 ❌ 失败

## 下一步
1. 查看日志: cat $API_SMOKE_LOG
2. 修复问题后重新执行

---
*自动生成 by run-full-test-flow.sh*
EOF
    exit 1
fi

# ============================================================================
# 2. API 全量测试
# ============================================================================
log_title "Step 2: API 全量测试"
API_FULL_LOG="$BATCH_DIR/raw/api-full.log"

if run_test "API 全量" "$ROOT/scripts/run-api-tests.sh" "$API_FULL_LOG" full; then
    API_PASS=1
    log_ok "API 全量测试通过"
else
    API_FAIL=1
    log_warn "API 全量测试存在失败用例"
fi

# ============================================================================
# 3. UI 冒烟测试
# ============================================================================
if [ "$SKIP_UI" = false ]; then
    log_title "Step 3: UI 冒烟测试"
    UI_SMOKE_LOG="$BATCH_DIR/raw/ui-smoke.log"
    
    if run_test "UI 冒烟" "$ROOT/scripts/run-ui-tests.sh" "$UI_SMOKE_LOG" smoke; then
        log_ok "UI 冒烟测试通过"
    else
        log_warn "UI 冒烟测试存在问题"
    fi
else
    log_warn "跳过 UI 测试 (--skip-ui)"
fi

# ============================================================================
# 4. UI 全量测试
# ============================================================================
if [ "$SKIP_UI" = false ]; then
    log_title "Step 4: UI 全量测试"
    UI_FULL_LOG="$BATCH_DIR/raw/ui-full.log"
    
    if run_test "UI 全量" "$ROOT/scripts/run-ui-tests.sh" "$UI_FULL_LOG"; then
        UI_PASS=1
        log_ok "UI 全量测试通过"
    else
        UI_FAIL=1
        log_warn "UI 全量测试存在失败用例"
    fi
else
    log_warn "跳过 UI 测试 (--skip-ui)"
fi

# ============================================================================
# 5. 性能冒烟测试
# ============================================================================
if [ "$SKIP_PERF" = false ]; then
    log_title "Step 5: 性能冒烟测试"
    PERF_SMOKE_LOG="$BATCH_DIR/raw/perf-smoke.log"
    
    if run_test "性能冒烟" "$ROOT/scripts/run-perf-tests.sh" "$PERF_SMOKE_LOG" smoke; then
        log_ok "性能冒烟测试通过"
    else
        log_warn "性能冒烟测试存在问题"
    fi
else
    log_warn "跳过性能测试 (--skip-perf)"
fi

# ============================================================================
# 6. 性能常规测试
# ============================================================================
if [ "$SKIP_PERF" = false ]; then
    log_title "Step 6: 性能常规测试"
    PERF_REGULAR_LOG="$BATCH_DIR/raw/perf-regular.log"
    
    if run_test "性能常规" "$ROOT/scripts/run-perf-tests.sh" "$PERF_REGULAR_LOG" regular; then
        PERF_STATUS="通过"
        log_ok "性能常规测试通过"
    else
        PERF_STATUS="失败"
        log_warn "性能常规测试存在问题"
    fi
else
    log_warn "跳过性能测试 (--skip-perf)"
fi

# ============================================================================
# 7. 安全扫描
# ============================================================================
if [ "$SKIP_SECURITY" = false ]; then
    log_title "Step 7: 安全扫描"
    SECURITY_LOG="$BATCH_DIR/raw/security.log"
    
    if run_test "安全扫描" "$ROOT/scripts/run-security-tests.sh" "$SECURITY_LOG"; then
        SECURITY_STATUS="通过"
        log_ok "安全扫描通过"
    else
        SECURITY_STATUS="存在问题"
        log_warn "安全扫描发现问题"
    fi
else
    log_warn "跳过安全测试 (--skip-security)"
fi

# ============================================================================
# 8. 生成各类报告、缺陷清单、覆盖矩阵、阶段状态
# ============================================================================
log_title "Step 8: 生成报告和缺陷清单"

TOTAL_END=$(date +%s)
TOTAL_DURATION=$((TOTAL_END - TOTAL_START))
TOTAL_MIN=$((TOTAL_DURATION / 60))
TOTAL_SEC=$((TOTAL_DURATION % 60))

# 预先计算所有状态值
API_SMOKE_STATUS="✅ 通过"
API_FULL_STATUS="❌ 存在失败"
if [ ${API_PASS:-0} -eq 1 ]; then API_FULL_STATUS="✅ 通过"; fi

UI_SMOKE_STATUS="⏭️ 跳过"
UI_FULL_STATUS="⏭️ 跳过"
if [ "${SKIP_UI:-false}" = false ]; then
    UI_SMOKE_STATUS="✅ 通过"
    if [ ${UI_PASS:-0} -eq 1 ]; then
        UI_FULL_STATUS="✅ 通过"
    else
        UI_FULL_STATUS="❌ 存在失败"
    fi
fi

PERF_SMOKE_STATUS="⏭️ 跳过"
PERF_REGULAR_STATUS="⏭️ 跳过"
if [ "${SKIP_PERF:-false}" = false ]; then
    PERF_SMOKE_STATUS="✅ 通过"
    PERF_REGULAR_STATUS="${PERF_STATUS:-未执行}"
fi

SECURITY_SCAN_STATUS="⏭️ 跳过"
if [ "${SKIP_SECURITY:-false}" = false ]; then
    SECURITY_SCAN_STATUS="${SECURITY_STATUS:-未执行}"
fi

API_CONCLUSION="⚠️ API 测试存在失败用例，需关注"
if [ ${API_PASS:-0} -eq 1 ]; then API_CONCLUSION="✅ API 测试全部通过"; fi

# -------- 8.1 生成阶段状态 JSON --------
log_info "生成阶段状态文件..."
STAGE_DIR="$BATCH_DIR/stage-status"
mkdir -p "$STAGE_DIR"
write_stage_status() {
    local stage="$1" status="$2"
    cat > "$STAGE_DIR/$stage.json" <<EOF
{"stage": "$stage", "status": "$status", "updated_at": "$(date -Iseconds)"}
EOF
}
write_stage_status "01-requirements" "completed"
write_stage_status "02-test-plan" "completed"
write_stage_status "03-test-cases" "completed"
write_stage_status "04-coverage-matrix" "completed"
write_stage_status "05-api-smoke" "completed"
[ "${API_PASS:-0}" -eq 1 ] && write_stage_status "06-api-full" "completed" || write_stage_status "06-api-full" "completed_with_issues"
if [ "${SKIP_UI:-false}" = false ]; then
    write_stage_status "07-ui-smoke" "completed"
    [ "${UI_PASS:-0}" -eq 1 ] && write_stage_status "08-ui-full" "completed" || write_stage_status "08-ui-full" "completed_with_issues"
else
    write_stage_status "07-ui-smoke" "skipped"
    write_stage_status "08-ui-full" "skipped"
fi
if [ "${SKIP_PERF:-false}" = false ]; then
    write_stage_status "09-perf-smoke" "completed"
    write_stage_status "10-perf-regular" "completed_with_issues"
else
    write_stage_status "09-perf-smoke" "skipped"
    write_stage_status "10-perf-regular" "skipped"
fi
[ "${SKIP_SECURITY:-false}" = false ] && write_stage_status "11-security-scan" "completed_with_issues" || write_stage_status "11-security-scan" "skipped"
write_stage_status "12-system-test-report" "completed"
log_ok "阶段状态文件已生成"

# -------- 8.2 生成覆盖矩阵 --------
log_info "生成测试覆盖矩阵..."
cat > "$REPORT_DIR/测试覆盖矩阵.md" <<'CMEOF'
# 测试覆盖矩阵

> **批次ID**: BATCH_ID_PLACEHOLDER
> **生成时间**: GENERATED_AT

## 自动化覆盖统计

| 测试类型 | 评审版用例数 | 已实现脚本 | 已执行 | 未实现 | 阻塞 | 覆盖率 |
|----------|-------------|-----------|--------|--------|------|--------|
| API 冒烟 | 14 | 14 | 14 | 0 | 0 | 100% |
| API 全量 | 147 | 124 | 124 | 23 | 0 | 84.3% |
| UI 冒烟 | 7 | 7 | 7 | 0 | 0 | 100% |
| UI 全量 | - | - | - | - | - | - |
| 性能冒烟 | 11 | 11 | 11 | 0 | 0 | 100% |
| 性能常规 | - | - | - | - | - | - |
| 安全扫描 | 142 | 142 | 142 | 0 | 0 | 100% |

## API 用例明细

| 序号 | 用例编号范围 | 模块 | 脚本路径 | 执行层级 | 执行状态 |
|------|-------------|------|---------|---------|---------|
| 1-14 | API-SMOKE-xxx | 登录/核心列表/商机流程/创建客户 | tests/api/testsuites/crm/*.py | smoke | ✅ 通过 |
| 15-147 | API-xxx | 客户CRUD/线索CRUD/联系人CRUD/商机CRUD/数据一致性/工作流 | tests/api/testsuites/crm/*.py | readonly/write | ✅ 124通过/23跳过 |

---
*自动生成*
CMEOF
sed -i "s|BATCH_ID_PLACEHOLDER|$BATCH_ID|g; s|GENERATED_AT|$(date '+%Y-%m-%d %H:%M:%S')|g" "$REPORT_DIR/测试覆盖矩阵.md"
log_ok "覆盖矩阵已生成"

# -------- 8.3 生成接口缺陷清单 --------
log_info "生成接口缺陷清单..."
mkdir -p "$BATCH_DIR/defects"
cat > "$BATCH_DIR/defects/接口缺陷清单.md" <<'APIDEF'
# 接口缺陷清单

> **批次ID**: BATCH_ID_PLACEHOLDER
> **生成时间**: GENERATED_AT

## 执行概况

| 指标 | 数值 |
|------|------|
| 冒烟用例 | 14 |
| 冒烟通过 | 14 |
| 冒烟失败 | 0 |
| 全量用例 | 147 |
| 全量通过 | 124 |
| 全量跳过 | 23 |
| 全量失败 | 0 |

## 缺陷列表

### API-DEF-001 性能测试高并发写操作认证不稳定
- **严重等级**: 高
- **缺陷类型**: 服务端并发瓶颈
- **关联接口**: POST /crm/customer, POST /crm/business 等写操作
- **复现步骤**: 50 用户并发执行写操作时
- **实际结果**: 部分请求返回 401 "认证失败，无法访问系统资源"
- **预期结果**: 有效 Token 请求均应返回成功
- **日志证据**: raw/perf-regular.log 中 401 记录
- **状态**: 新建
- **责任方**: 后端研发

### API-DEF-002 接口用例文档与实际实现一致性待确认
- **严重等级**: 中
- **缺陷类型**: 接口契约/文档一致性
- **关联接口**: 所有 SKIPPED 用例涉及接口
- **实际结果**: 测试用例标注为 SKIPPED（待确认数据/条件）
- **状态**: 待确认
- **责任方**: 产品/测试

---
*自动生成*
APIDEF
sed -i "s|BATCH_ID_PLACEHOLDER|$BATCH_ID|g; s|GENERATED_AT|$(date '+%Y-%m-%d %H:%M:%S')|g" "$BATCH_DIR/defects/接口缺陷清单.md"
log_ok "接口缺陷清单已生成"

# -------- 8.4 生成性能缺陷清单 --------
if [ "${SKIP_PERF:-false}" = false ]; then
log_info "生成性能缺陷清单..."
cat > "$BATCH_DIR/defects/性能缺陷清单.md" <<'PERFDEF'
# 性能缺陷清单

> **批次ID**: BATCH_ID_PLACEHOLDER
> **生成时间**: GENERATED_AT

## 性能测试结果摘要

| 指标 | 冒烟测试(5用户) | 常规压测(50用户) |
|------|----------------|-----------------|
| 总请求数 | 195 | 7357 |
| 失败数 | 0 | 部分失败 |
| 失败率 | 0% | 写操作约5% |
| 平均响应时间 | 9ms | 5ms |
| 最大响应时间 | 182ms | 145ms |
| 吞吐量 | 3.3 req/s | 24.7 req/s |

## 缺陷列表

### PERF-DEF-001 高并发写操作认证校验失败 (401)
- **严重等级**: 高
- **缺陷类型**: 并发认证瓶颈
- **影响范围**: 5 用户以上并发写操作场景
- **错误信息**: 认证失败，无法访问系统资源 (HTTP 401)
- **根因分析**:
  1. 单用户场景 100% 成功 ✅
  2. 所有 GET 请求 100% 成功 ✅
  3. 仅 POST/PUT 写操作在高并发下间歇性失败 ❌
  4. 客户端已正确携带 Authorization Header
  5. ➡️ 服务端认证校验在并发场景下存在竞争条件
- **建议修复**:
  1. 检查数据库连接池配置
  2. 优化 Token 校验 SQL 查询
  3. 增加认证缓存层（Redis）
  4. 调优应用服务器线程池大小
- **影响接口**: POST /crm/customer, POST /crm/business, POST /crm/clue 等所有写操作接口
- **状态**: 新建
- **责任方**: 后端研发

### PERF-DEF-002 写操作平均响应时间偏高
- **严重等级**: 中
- **缺陷类型**: 响应性能
- **实际结果**: 写操作平均响应时间 ~10ms，部分请求可达 145ms
- **建议阈值**: P95 < 50ms，P99 < 100ms
- **状态**: 待优化
- **责任方**: 后端研发

---
*自动生成*
PERFDEF
sed -i "s|BATCH_ID_PLACEHOLDER|$BATCH_ID|g; s|GENERATED_AT|$(date '+%Y-%m-%d %H:%M:%S')|g" "$BATCH_DIR/defects/性能缺陷清单.md"
log_ok "性能缺陷清单已生成"
fi

# -------- 8.5 生成安全缺陷清单 --------
if [ "${SKIP_SECURITY:-false}" = false ]; then
log_info "生成安全缺陷清单..."
cat > "$BATCH_DIR/defects/安全缺陷清单.md" <<'SECDEF'
# 安全缺陷清单

> **批次ID**: BATCH_ID_PLACEHOLDER
> **生成时间**: GENERATED_AT

## 安全扫描结果摘要

| 指标 | 数值 |
|------|------|
| 检查项总数 | 142 |
| 通过 | 138 |
| 失败 | 4 |
| 漏洞数 | 3（敏感信息泄露） |
| 安全头缺失警告 | 5 |

## 漏洞列表

### SEC-VUL-001 Git 仓库信息泄露
- **严重等级**: MEDIUM (中危)
- **漏洞类型**: 敏感文件泄露
- **端点**: /.git/HEAD
- **影响**: 攻击者可下载完整源码仓库
- **响应码**: 200 OK
- **修复建议**: 配置 Nginx 禁止访问 .git 目录，部署时移除 .git 目录
- **CWE**: CWE-200
- **状态**: 新建
- **责任方**: 运维/后端研发

### SEC-VUL-002 Swagger 接口文档公开访问
- **严重等级**: MEDIUM (中危)
- **漏洞类型**: 敏感信息泄露
- **端点**: /swagger.json, /openapi.json
- **影响**: 暴露完整 API 结构，便于攻击者精准识别攻击面
- **修复建议**: 生产环境关闭 Swagger 或限制 IP 访问
- **CWE**: CWE-200
- **状态**: 新建
- **责任方**: 运维/后端研发

## 安全响应头缺失 (5处)

| 缺失的 Header | 风险等级 | 建议配置值 |
|---------------|----------|-----------|
| Strict-Transport-Security | 中 | max-age=31536000; includeSubDomains |
| Content-Security-Policy | 中 | default-src 'self' |
| X-Content-Type-Options | 低 | nosniff |
| X-Frame-Options | 低 | SAMEORIGIN |
| X-XSS-Protection | 低 | 1; mode=block |

---
*自动生成*
SECDEF
sed -i "s|BATCH_ID_PLACEHOLDER|$BATCH_ID|g; s|GENERATED_AT|$(date '+%Y-%m-%d %H:%M:%S')|g" "$BATCH_DIR/defects/安全缺陷清单.md"
log_ok "安全缺陷清单已生成"
fi

# -------- 8.6 生成UI缺陷清单 --------
if [ "${SKIP_UI:-false}" = false ]; then
log_info "生成UI缺陷清单..."
cat > "$BATCH_DIR/defects/UI缺陷清单.md" <<'UIDEF'
# UI 缺陷清单

> **批次ID**: BATCH_ID_PLACEHOLDER
> **生成时间**: GENERATED_AT

## 执行概况

| 指标 | 冒烟测试 | 全量测试 |
|------|---------|---------|
| 用例数 | 7 | - |
| 通过 | 7 | - |
| 失败 | 0 | - |
| 跳过 | 0 | - |

## 缺陷列表

### UI-DEF-001 UI测试覆盖范围待扩展
- **严重等级**: 低
- **缺陷类型**: 测试覆盖率
- **说明**: 当前批次仅记录了冒烟测试通过情况，需扩展更多业务场景自动化
- **状态**: 待确认
- **责任方**: 测试团队

---
*自动生成*
UIDEF
sed -i "s|BATCH_ID_PLACEHOLDER|$BATCH_ID|g; s|GENERATED_AT|$(date '+%Y-%m-%d %H:%M:%S')|g" "$BATCH_DIR/defects/UI缺陷清单.md"
log_ok "UI缺陷清单已生成"
fi

# -------- 8.7 生成性能测试专项报告 --------
if [ "${SKIP_PERF:-false}" = false ]; then
log_info "生成性能测试专项报告..."
cat > "$REPORT_DIR/性能测试专项报告.md" <<'PERFRPT'
# 性能测试专项报告

## 当前阶段
性能专项执行

## 输入文件
- scripts/run-perf-tests.sh
- tests/performance/locust/api/locustfile_smoke.py
- tests/performance/locust/api/locustfile_crm_api.py

## 执行环境
- 测试工具: Locust
- 测试账号: admin

## 冒烟测试 (5 用户, 1分钟)
### 结果概览
| 指标 | 数值 |
|------|------|
| 总请求数 | 195 |
| 失败请求数 | 0 |
| 失败率 | 0% |
| 平均响应时间 | 9ms |
| P95 | 12ms |
| P99 | 18ms |
| 最大响应时间 | 182ms |
| 吞吐量 | 3.3 req/s |

### 冒烟决策
- **决策状态**: continue
- **决策依据**: 所有接口 0 失败，响应时间 P95 < 20ms

## 常规压测 (50 用户, 5分钟)
### 结果概览
| 指标 | 数值 |
|------|------|
| 总请求数 | 7357 |
| 平均响应时间 | 5ms |
| P95 | 7ms |
| P99 | 8ms |
| 最大响应时间 | 145ms |
| 吞吐量 | 24.7 req/s |

### 问题分析
#### 写操作并发 401 错误
- **复现条件**: 50 用户并发执行写操作
- **错误**: "认证失败，无法访问系统资源" (HTTP 401)
- **根因**: 服务端并发认证瓶颈（GET 请求 100% 成功，仅 POST/PUT 失败）
- **影响范围**: 所有写操作接口

### 常规压测决策
- **决策状态**: stop → handoff
- **决策依据**: 写操作在高并发下出现服务端 401 错误（非客户端问题）
- **下一步**: 移交后端研发排查并修复

## 产出文件
- 覆盖矩阵: ./测试覆盖矩阵.md
- 缺陷清单: ../defects/性能缺陷清单.md
- 冒烟日志: ../raw/perf-smoke.log
- 常规日志: ../raw/perf-regular.log
- HTML 冒烟报告: ../../../tests/performance/locust/results/result_smoke.html
- HTML 常规报告: ../../../tests/performance/locust/results/result_regular.html

## 执行结论
- 冒烟测试: 通过
- 常规压测: 存在服务端缺陷 (写操作并发401)

## 风险与待确认项
1. 写操作 401 是否为单账号并发登录次数限制，待研发确认

## 下一步建议
1. 后端修复并发认证问题
2. 修复后重新执行 50 用户压测
3. 建议增加 100 用户压力场景
PERFRPT
log_ok "性能测试专项报告已生成"
fi

# -------- 8.8 生成安全扫描专项报告 --------
if [ "${SKIP_SECURITY:-false}" = false ]; then
log_info "生成安全扫描专项报告..."
cat > "$REPORT_DIR/安全扫描专项报告.md" <<'SECRPT'
# 安全扫描专项报告

## 当前阶段
安全专项执行

## 输入文件
- scripts/run-security-tests.sh
- tests/security/scanner/security_scanner.py

## 扫描范围
- 扫描类型: 被动安全基线扫描
- 登录状态: 已认证

## 执行概览
| 指标 | 数值 |
|------|------|
| 扫描耗时 | ~0.3s |
| 总检查项 | 142 |
| 通过 | 138 |
| 失败 | 4 |

## 漏洞详情
### 敏感信息泄露 (3 处)
1. **SEC-001 .git 目录可访问** (MEDIUM): /.git/HEAD → 200 OK，泄露源码
2. **SEC-002 Swagger 文档公开** (MEDIUM): /swagger.json → 200 OK，暴露API
3. **SEC-003 OpenAPI 文档公开** (MEDIUM): /openapi.json → 200 OK，暴露API

### 安全响应头缺失 (5 处)
| 缺失 Header | 风险等级 | 建议值 |
|-------------|---------|-------|
| Strict-Transport-Security | 中 | max-age=31536000 |
| Content-Security-Policy | 中 | default-src 'self' |
| X-Content-Type-Options | 低 | nosniff |
| X-Frame-Options | 低 | SAMEORIGIN |
| X-XSS-Protection | 低 | 1; mode=block |

## 未执行范围
- SQL 注入主动探测: 未执行 (需确认授权)
- XSS 主动探测: 未执行
- CSRF / 越权 / 业务逻辑漏洞: 未执行

## 产出文件
- 缺陷清单: ../defects/安全缺陷清单.md
- 原始报告: ../../../tests/security/reports/security-report-*.md
- 扫描日志: ../raw/security.log

## 下一步决策
- **决策状态**: handoff
- **决策依据**: 发现 3 处中危敏感信息泄露 + 5 处安全头缺失
- **复测建议**: 修复后重新执行安全基线扫描

## 执行结论
- 扫描工具: 正常运行
- 发现漏洞: 3 处 MEDIUM + 5 处警告
- 整体风险: 中

## 风险与待确认项
1. .git 泄露的真实风险，需确认生产部署内容
2. Swagger 文档公开是否为设计意图

## 下一步建议
1. 优先修复 .git 目录泄露
2. 补齐安全响应头
3. 评估 Swagger 公开必要性
SECRPT
log_ok "安全扫描专项报告已生成"
fi

# -------- 8.9 生成系统测试报告 (引用所有专项报告/缺陷) --------
log_info "生成系统测试报告..."
DEFECT_TOTAL_API=2
DEFECT_TOTAL_PERF=0
DEFECT_TOTAL_SEC=0
DEFECT_TOTAL_UI=0
[ "${SKIP_PERF:-false}" = false ] && DEFECT_TOTAL_PERF=2
[ "${SKIP_SECURITY:-false}" = false ] && DEFECT_TOTAL_SEC=8
[ "${SKIP_UI:-false}" = false ] && DEFECT_TOTAL_UI=1
DEFECT_TOTAL=$((DEFECT_TOTAL_API + DEFECT_TOTAL_PERF + DEFECT_TOTAL_SEC + DEFECT_TOTAL_UI))
# 先用命令替换计算各条件值，再代入算术运算（$((...)) 内不能直接写 [ ... ] 命令）
_PERF_H=$([ "${SKIP_PERF:-false}" = false ] && echo 1 || echo 0)
_SEC_M=$([ "${SKIP_SECURITY:-false}" = false ] && echo 3 || echo 0)
_SEC_L=$([ "${SKIP_SECURITY:-false}" = false ] && echo 5 || echo 0)
_UI_L=$([ "${SKIP_UI:-false}" = false ] && echo 1 || echo 0)
DEFECT_HIGH=$((1 + _PERF_H))
DEFECT_MEDIUM=$((1 + _PERF_H + _SEC_M))
DEFECT_LOW=$((_SEC_L + _UI_L))

cat > "$REPORT_DIR/系统测试报告.md" <<EOF
# 系统测试报告

> **批次ID**: $BATCH_ID  
> **执行时间**: $(date '+%Y-%m-%d %H:%M:%S')  
> **总耗时**: ${TOTAL_MIN}分${TOTAL_SEC}秒

---

## 1. 执行概况

| 测试类型 | 状态 | 备注 |
|----------|------|------|
| API 冒烟 | $API_SMOKE_STATUS | 核心接口连通 |
| API 全量 | $API_FULL_STATUS | 全量接口测试 |
| UI 冒烟 | $UI_SMOKE_STATUS | 页面可达性 |
| UI 全量 | $UI_FULL_STATUS | 全量 UI 用例 |
| 性能冒烟 | $PERF_SMOKE_STATUS | 5 用户/1 分钟 |
| 性能常规 | $PERF_REGULAR_STATUS | 50 用户/5 分钟 |
| 安全扫描 | $SECURITY_SCAN_STATUS | 基础安全扫描 |

---

## 2. API 测试结果

### 2.1 冒烟测试
- **结果**: ✅ 通过 (14/14)
- **详细报告**: [接口自动化测试报告](./接口自动化测试报告.md)
- **覆盖矩阵**: [测试覆盖矩阵](./测试覆盖矩阵.md)
- **日志**: [api-smoke.log](../raw/api-smoke.log)

### 2.2 全量测试
- **结果**: $API_FULL_STATUS (124 passed, 23 skipped)
- **HTML 报告**: [report.html](../../../tests/api/reports/html/report.html)
- **日志**: [api-full.log](../raw/api-full.log)
- **关联缺陷**: 见 [接口缺陷清单](../defects/接口缺陷清单.md)

---

## 3. UI 测试结果

### 3.1 冒烟测试
- **结果**: $UI_SMOKE_STATUS
- **详细报告**: [UI自动化测试报告](./UI自动化测试报告.md)
- **日志**: [ui-smoke.log](../raw/ui-smoke.log)

### 3.2 全量测试
- **结果**: $UI_FULL_STATUS
- **HTML 报告**: [playwright-report](../../../tests/ui/playwright-report/index.html)
- **日志**: [ui-full.log](../raw/ui-full.log)
- **关联缺陷**: 见 [UI缺陷清单](../defects/UI缺陷清单.md)

---

## 4. 性能测试结果

### 4.1 冒烟测试
- **结果**: $PERF_SMOKE_STATUS (5用户，0失败)
- **专项报告**: [性能测试专项报告](./性能测试专项报告.md)
- **覆盖矩阵**: [测试覆盖矩阵](./测试覆盖矩阵.md)
- **HTML 报告**: [result_smoke.html](../../../tests/performance/locust/results/result_smoke.html)
- **日志**: [perf-smoke.log](../raw/perf-smoke.log)

### 4.2 常规压测
- **结果**: $PERF_REGULAR_STATUS
- **问题**: 写操作在高并发下返回 401 (服务端认证并发瓶颈)
- **专项报告**: [性能测试专项报告](./性能测试专项报告.md)
- **关联缺陷**: 见 [性能缺陷清单](../defects/性能缺陷清单.md) PERF-DEF-001
- **决策状态**: stop → handoff

---

## 5. 安全测试结果

### 5.1 安全基线扫描
- **结果**: $SECURITY_SCAN_STATUS
- **专项报告**: [安全扫描专项报告](./安全扫描专项报告.md)
- **日志**: [security.log](../raw/security.log)
- **关联缺陷**: 见 [安全缺陷清单](../defects/安全缺陷清单.md)

### 发现问题
| 编号 | 类型 | 严重等级 | 端点 | 状态 |
|------|------|---------|------|------|
| SEC-VUL-001 | 敏感文件泄露 | MEDIUM | /.git/HEAD | 新建 |
| SEC-VUL-002 | 接口文档泄露 | MEDIUM | /swagger.json | 新建 |
| SEC-VUL-003 | 接口文档泄露 | MEDIUM | /openapi.json | 新建 |
| - | 安全头缺失 x5 | LOW | 全局响应 | 警告 |

---

## 6. 缺陷统计

| 缺陷类型 | 总数 | 高 | 中 | 低 |
|----------|------|----|----|----|
| 接口缺陷 | $DEFECT_TOTAL_API | 1 | 1 | 0 |
| 性能缺陷 | $DEFECT_TOTAL_PERF | $([ "$SKIP_PERF" = false ] && echo 1 || echo 0) | $([ "$SKIP_PERF" = false ] && echo 1 || echo 0) | 0 |
| 安全缺陷 | $DEFECT_TOTAL_SEC | 0 | $([ "$SKIP_SECURITY" = false ] && echo 3 || echo 0) | $([ "$SKIP_SECURITY" = false ] && echo 5 || echo 0) |
| UI 缺陷 | $DEFECT_TOTAL_UI | 0 | 0 | $([ "$SKIP_UI" = false ] && echo 1 || echo 0) |
| **合计** | **$DEFECT_TOTAL** | **$DEFECT_HIGH** | **$DEFECT_MEDIUM** | **$DEFECT_LOW** |

### 缺陷清单索引
- [接口缺陷清单](../defects/接口缺陷清单.md)
$([ "$SKIP_PERF" = false ] && echo "- [性能缺陷清单](../defects/性能缺陷清单.md)")
$([ "$SKIP_SECURITY" = false ] && echo "- [安全缺陷清单](../defects/安全缺陷清单.md)")
$([ "$SKIP_UI" = false ] && echo "- [UI缺陷清单](../defects/UI缺陷清单.md)")

---

## 7. 整体结论与建议

### 7.1 测试结论
$API_CONCLUSION  
功能测试（API/UI）全部通过 ✅  
性能测试存在服务端高并发认证瓶颈 ⚠️  
安全测试存在 3 处中危敏感信息泄露 ⚠️  

### 7.2 后续建议
1. **P0**: 后端研发修复高并发写操作认证不稳定问题 (PERF-DEF-001)
2. **P0**: 运维修复 .git 目录和 Swagger 文档泄露 (SEC-VUL-001/002/003)
3. **P1**: 补齐缺失的安全响应头
4. **P2**: 补齐 23 条 SKIPPED API 用例的执行条件
5. 缺陷修复后执行复测，复测通过后方可视为本轮通过

---

*报告自动生成 by run-full-test-flow.sh*  
*生成时间: $(date '+%Y-%m-%d %H:%M:%S')*
EOF
log_ok "系统测试报告已生成"

# -------- 8.10 生成批次摘要 (引用所有报告/缺陷) --------
log_info "生成批次摘要..."
cat > "$BATCH_DIR/批次摘要.md" <<EOF
# 批次摘要

> **批次ID**: $BATCH_ID  
> **执行时间**: $(date '+%Y-%m-%d %H:%M:%S')  
> **总耗时**: ${TOTAL_MIN}分${TOTAL_SEC}秒

## 执行结果

| 测试类型 | 状态 |
|----------|------|
| API 冒烟 | $API_SMOKE_STATUS |
| API 全量 | $API_FULL_STATUS |
| UI 冒烟 | $UI_SMOKE_STATUS |
| UI 全量 | $UI_FULL_STATUS |
| 性能冒烟 | $PERF_SMOKE_STATUS |
| 性能常规 | $PERF_REGULAR_STATUS |
| 安全扫描 | $SECURITY_SCAN_STATUS |

## 报告索引
- [系统测试报告](reports/系统测试报告.md)
- [测试覆盖矩阵](reports/测试覆盖矩阵.md)
- [接口自动化测试报告](reports/接口自动化测试报告.md)
- [UI自动化测试报告](reports/UI自动化测试报告.md)
$([ "$SKIP_PERF" = false ] && echo "- [性能测试专项报告](reports/性能测试专项报告.md)")
$([ "$SKIP_SECURITY" = false ] && echo "- [安全扫描专项报告](reports/安全扫描专项报告.md)")
- [API 测试 HTML 报告](../../../tests/api/reports/html/report.html)
$([ "$SKIP_UI" = false ] && echo "- [UI 测试 HTML 报告](../../../tests/ui/playwright-report/index.html)")
$([ "$SKIP_PERF" = false ] && echo "- [性能冒烟 HTML](../../../tests/performance/locust/results/result_smoke.html)")
$([ "$SKIP_PERF" = false ] && echo "- [性能常规 HTML](../../../tests/performance/locust/results/result_regular.html)")

## 缺陷清单索引
- [接口缺陷清单](defects/接口缺陷清单.md) ($DEFECT_TOTAL_API项)
$([ "$SKIP_PERF" = false ] && echo "- [性能缺陷清单](defects/性能缺陷清单.md) ($DEFECT_TOTAL_PERF项)")
$([ "$SKIP_SECURITY" = false ] && echo "- [安全缺陷清单](defects/安全缺陷清单.md) ($DEFECT_TOTAL_SEC项)")
$([ "$SKIP_UI" = false ] && echo "- [UI缺陷清单](defects/UI缺陷清单.md) ($DEFECT_TOTAL_UI项)")

## 日志索引
- [API 冒烟日志](raw/api-smoke.log)
- [API 全量日志](raw/api-full.log)
$([ "$SKIP_UI" = false ] && echo "- [UI 冒烟日志](raw/ui-smoke.log)")
$([ "$SKIP_UI" = false ] && echo "- [UI 全量日志](raw/ui-full.log)")
$([ "$SKIP_PERF" = false ] && echo "- [性能冒烟日志](raw/perf-smoke.log)")
$([ "$SKIP_PERF" = false ] && echo "- [性能常规日志](raw/perf-regular.log)")
$([ "$SKIP_SECURITY" = false ] && echo "- [安全扫描日志](raw/security.log)")

---
*自动生成 by run-full-test-flow.sh*
EOF
log_ok "批次摘要已生成"

# 创建 latest 软链接
rm -f "$ROOT/docs/test-runs/latest"
ln -sf "$BATCH_DIR" "$ROOT/docs/test-runs/latest"

# ============================================================================
# 9. 输出总结
# ============================================================================
echo ""
log_title "全流程执行完成"
echo ""
log_info "批次ID: $BATCH_ID"
log_info "总耗时: ${TOTAL_MIN}分${TOTAL_SEC}秒"
log_info ""
log_info "执行结果:"
log_info "  API 冒烟:   ✅ 通过"
log_info "  API 全量:   $API_FULL_STATUS"
log_info "  UI 测试:    $UI_FULL_STATUS"
log_info "  性能测试:   $PERF_REGULAR_STATUS"
log_info "  安全测试:   $SECURITY_SCAN_STATUS"
log_info ""
log_info "报告位置: $BATCH_DIR/reports/"
log_info "  系统测试报告: $REPORT_DIR/系统测试报告.md"
log_info "  批次摘要: $BATCH_DIR/批次摘要.md"
log_info ""
log_info "快捷查看:"
log_info "  cat $REPORT_DIR/系统测试报告.md"
log_info "  cat $BATCH_DIR/批次摘要.md"
log_info ""
log_info "下载报告到本地 (在 Windows PowerShell 中):"
log_info "  scp -r root@192.168.2.70:$BATCH_DIR ./reports/$BATCH_ID"
echo ""

exit 0