#!/usr/bin/env bash
# ============================================================================
# 安全测试 - 通用执行脚本
# 用法: ./scripts/run-security-tests.sh
# 环境: 需要 Python 3.10+
# 配置: 从 projects/<system>/system.yaml 动态读取，无需修改脚本
# ============================================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ---------- 加载共享库 ----------
# shellcheck disable=SC1090
source "$ROOT/shared/lib/test_framework.sh"

# ---------- 加载 system.yaml 配置 ----------
load_system_config "$ROOT" "${TEST_SYSTEM_ID:-crm}"

# ---------- 从 system.yaml 获取配置 ----------
SEC_DIR="$ROOT/$(get_tests_dir security "tests/security")"
SEC_TARGET_URL="${SEC_TARGET_URL:-$(get_api_base_url "http://192.168.2.97:6089")}"

# ---------- Python 检查 ----------
detect_python || exit 1

# ---------- 检查安全扫描器 ----------
if [ ! -d "$SEC_DIR" ]; then
    log_warn "安全测试目录不存在: $SEC_DIR"
    log_info "安全测试未执行（环境不满足）"
    exit 0
fi

if ! $PYTHON_BIN -c "import sys; sys.path.insert(0, '$SEC_DIR'); from scanner.security_scanner import SecurityScanner" 2>/dev/null; then
    log_warn "安全扫描器模块未就绪"
    log_info "安全测试未执行"
    exit 0
fi

# ---------- 执行安全扫描 ----------
log_info "============================================"
log_info "安全测试扫描"
log_info "============================================"
log_info "系统:       ${SYS_ID:-crm}"
log_info "目标:       $SEC_TARGET_URL"
log_info "扫描器目录: $SEC_DIR"
log_info ""

cd "$SEC_DIR"

# 输出目录隔离：优先用 TEST_RUN_DIR（批次隔离），否则用本地 reports/
if [ -n "${TEST_RUN_DIR:-}" ]; then
    REPORT_DIR="$TEST_RUN_DIR/raw/security"
else
    REPORT_DIR="$SEC_DIR/reports"
fi
mkdir -p "$REPORT_DIR"

REPORT_FILE="$REPORT_DIR/security-report-$(date +%Y%m%d-%H%M%S).md"

# 执行扫描
$PYTHON_BIN -c "
import sys
sys.path.insert(0, '$SEC_DIR')
from scanner.security_scanner import SecurityScanner
import json

scanner = SecurityScanner(base_url='$SEC_TARGET_URL')
results = scanner.run()
print(json.dumps(results, indent=2, ensure_ascii=False))
" 2>&1 | tee "$REPORT_FILE"

EXIT_CODE=${PIPESTATUS[0]}

echo ""
log_info "============================================"
log_info "安全测试完成"
log_info "============================================"
log_info "报告: $REPORT_FILE"

log_ok "安全测试完成"
exit $EXIT_CODE