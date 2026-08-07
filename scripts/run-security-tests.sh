#!/usr/bin/env bash
# ============================================================================
# 安全测试 - Linux 原生执行脚本
# 用法: ./scripts/run-security-tests.sh
# 环境: 需要 Python 3.10+
# ============================================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SEC_DIR="$ROOT/tests/security"

# 系统标识（由 run-full-test-flow.sh 通过环境变量传入）
SYSTEM_ID="${TEST_SYSTEM_ID:-crm}"

# ---------- 颜色输出 ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()  { echo -e "${CYAN}[INFO]${NC} $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ---------- Python 检查 ----------
PYTHON_BIN="python3"
if ! command -v $PYTHON_BIN &>/dev/null; then
    PYTHON_BIN="python"
fi

if ! command -v $PYTHON_BIN &>/dev/null; then
    log_error "Python 未找到，请安装 Python 3.10+"
    exit 1
fi

# ---------- 环境变量 ----------
export API_BASE_URL="${API_BASE_URL:-http://192.168.2.97:6089/prod-api}"

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
log_info "目标: $API_BASE_URL"
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

scanner = SecurityScanner(base_url='$API_BASE_URL')
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
