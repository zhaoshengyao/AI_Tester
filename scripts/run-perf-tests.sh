#!/usr/bin/env bash
# ============================================================================
# 性能测试 - 通用执行脚本
# 用法: ./scripts/run-perf-tests.sh [STAGE]
#   STAGE: smoke | regular | stress | stability | extreme | all (默认 all)
# 环境: 需要 Python 3.10+, locust
# 配置: 从 projects/<system>/system.yaml 动态读取，无需修改脚本
# ============================================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAGE="${1:-all}"

# ---------- 加载共享库 ----------
# shellcheck disable=SC1090
source "$ROOT/shared/lib/test_framework.sh"

# ---------- 加载 system.yaml 配置 ----------
load_system_config "$ROOT" "${TEST_SYSTEM_ID:-crm}"

# ---------- 从 system.yaml 获取配置 ----------
PERF_DIR="$ROOT/$(get_tests_dir performance "tests/performance/locust")"
API_BASE_URL="$(get_api_base_url "http://192.168.2.97:6089/prod-api")"

# 性能测试配置（从 system.yaml 读取，有默认值回退）
PERF_SMOKE_USERS="${PERF_SMOKE_USERS:-5}"
PERF_SMOKE_SPAWN_RATE="${PERF_SMOKE_SPAWN_RATE:-1}"
PERF_SMOKE_DURATION="${PERF_SMOKE_DURATION:-60s}"
PERF_FULL_USERS="${PERF_FULL_USERS:-50}"
PERF_FULL_SPAWN_RATE="${PERF_FULL_SPAWN_RATE:-5}"
PERF_FULL_DURATION="${PERF_FULL_DURATION:-300s}"

# ---------- Python 检查 ----------
detect_python || exit 1

# ---------- 检查/安装 locust ----------
if ! $PYTHON_BIN -c "import locust" &>/dev/null; then
    log_warn "Locust 未安装，尝试安装..."
    pip install locust locust-plugins PyYAML 2>&1 | tail -3
    if [ $? -ne 0 ]; then
        log_error "Locust 安装失败"
        exit 1
    fi
    log_ok "Locust 已安装"
else
    log_ok "Locust 已就绪 ($($PYTHON_BIN -c 'import locust; print(locust.__version__)'))"
fi

# ---------- 导出环境变量 ----------
export API_BASE_URL

# ---------- 分阶段执行 ----------
log_info "============================================"
log_info "性能测试 - $STAGE"
log_info "============================================"
log_info "系统:       ${SYS_ID:-crm}"
log_info "API 地址:   $API_BASE_URL"
log_info "测试目录:   $PERF_DIR"
log_info ""

cd "$PERF_DIR"

# 输出目录隔离：优先用 TEST_RUN_DIR（批次隔离），否则用本地 results/
if [ -n "${TEST_RUN_DIR:-}" ]; then
    PERF_RESULT_DIR="$TEST_RUN_DIR/raw/perf"
else
    PERF_RESULT_DIR="$PERF_DIR/results"
fi
mkdir -p "$PERF_RESULT_DIR"

run_stage() {
    local stage_name="$1"
    local script="$2"
    local users="$3"
    local spawn_rate="$4"
    local run_time="$5"
    local extra_args="${6:-}"

    log_info "--- 阶段: $stage_name ---"
    log_info "脚本: $script, 用户: $users, 增速: $spawn_rate/s, 时长: $run_time"

    local result_file="$PERF_RESULT_DIR/result_${stage_name}.html"
    $PYTHON_BIN -m locust \
        -f "$script" \
        --headless \
        -u "$users" \
        -r "$spawn_rate" \
        -t "$run_time" \
        --host "$API_BASE_URL" \
        --html "$result_file" \
        $extra_args 2>&1
    
    local ret=$?
    if [ $ret -eq 0 ]; then
        log_ok "阶段 [$stage_name] 完成 ✅"
    else
        log_error "阶段 [$stage_name] 失败 (退出码: $ret)"
    fi
    echo ""
    return $ret
}

case "$STAGE" in
    smoke)
        run_stage "smoke" "api/locustfile_smoke.py" "$PERF_SMOKE_USERS" "$PERF_SMOKE_SPAWN_RATE" "$PERF_SMOKE_DURATION"
        ;;
    regular)
        run_stage "regular" "api/locustfile_crm_api.py" "$PERF_FULL_USERS" "$PERF_FULL_SPAWN_RATE" "$PERF_FULL_DURATION"
        ;;
    stress)
        run_stage "stress" "api/locustfile_crm_api.py" 200 10 600s
        ;;
    stability)
        run_stage "stability" "api/locustfile_crm_api.py" 30 2 3600s
        ;;
    extreme)
        run_stage "extreme" "api/locustfile_crm_api.py" 500 20 600s
        ;;
    all)
        log_info "执行全部阶段..."
        run_stage "smoke" "api/locustfile_smoke.py" "$PERF_SMOKE_USERS" "$PERF_SMOKE_SPAWN_RATE" "$PERF_SMOKE_DURATION" || true
        run_stage "regular" "api/locustfile_crm_api.py" "$PERF_FULL_USERS" "$PERF_FULL_SPAWN_RATE" "$PERF_FULL_DURATION" || true
        run_stage "stress" "api/locustfile_crm_api.py" 200 10 600s || true
        run_stage "stability" "api/locustfile_crm_api.py" 30 2 3600s || true
        run_stage "extreme" "api/locustfile_crm_api.py" 500 20 600s || true
        ;;
    *)
        log_error "未知阶段: $STAGE"
        log_info "可选: smoke, regular, stress, stability, extreme, all"
        exit 1
esac

# ---------- 生成汇总报告 ----------
log_info "============================================"
log_info "性能测试执行完成"
log_info "============================================"
log_info "报告目录: $PERF_RESULT_DIR"

# 列出所有结果文件
if [ -d "$PERF_RESULT_DIR" ]; then
    log_info "结果文件:"
    find "$PERF_RESULT_DIR" -name "*.html" -type f 2>/dev/null | while read -r f; do
        log_info "  - $f"
    done
fi

log_ok "性能测试完成"
exit 0