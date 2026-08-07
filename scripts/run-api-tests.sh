#!/usr/bin/env bash
# ============================================================================
# API 自动化测试 - Linux 原生执行脚本
# 用法: ./scripts/run-api-tests.sh [MODE] [KEYWORD]
#   MODE: smoke | full | failed-retest (默认 full)
#   KEYWORD: pytest -k 过滤关键字 (可选)
# 环境: 需要 Python 3.10+, pip, 可选 python3-venv
# ============================================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-full}"
KEYWORD="${2:-}"

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

# ---------- 目录与文件 ----------
# 优先用 TEST_RUN_DIR（由 run-full-test-flow.sh 注入），实现批次隔离与并行安全
TEST_DIR="$ROOT/tests/api"
if [ -n "${TEST_RUN_DIR:-}" ]; then
    REPORT_DIR="$TEST_RUN_DIR/raw/api"
else
    REPORT_DIR="$TEST_DIR/reports"
fi
RAW_DIR="$REPORT_DIR/raw"
JUNIT_DIR="$REPORT_DIR/junit"
HTML_DIR="$REPORT_DIR/html"
LOG_FILE="$RAW_DIR/api-test.log"
JUNIT_FILE="$JUNIT_DIR/report.xml"
HTML_FILE="$HTML_DIR/report.html"

mkdir -p "$RAW_DIR" "$JUNIT_DIR" "$HTML_DIR"

# ---------- 环境变量 ----------
export API_BASE_URL="${API_BASE_URL:-http://192.168.2.97:6089/prod-api}"
export API_USERNAME="${API_USERNAME:-${TEST_USERNAME:-ZhaoShengYao}}"
export API_TIMEOUT_SECONDS="${API_TIMEOUT_SECONDS:-10}"

# ---------- Python 检查与虚拟环境 ----------
PYTHON_BIN="python3"
if ! command -v $PYTHON_BIN &>/dev/null; then
    PYTHON_BIN="python"
fi

if ! command -v $PYTHON_BIN &>/dev/null; then
    log_error "Python 未找到，请安装 Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_BIN -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
log_info "Python 版本: $PYTHON_VERSION ($($PYTHON_BIN --version 2>&1))"

# 检查依赖
if ! $PYTHON_BIN -c "import pytest, requests, yaml, pytest_html" &>/dev/null; then
    log_warn "Python 依赖未就绪，尝试创建虚拟环境..."
    
    if [ ! -d "$ROOT/.venv" ]; then
        $PYTHON_BIN -m venv "$ROOT/.venv" 2>/dev/null || {
            log_error "虚拟环境创建失败，请安装 python3-venv"
            exit 1
        }
    fi
    
    # shellcheck disable=SC1091
    source "$ROOT/.venv/bin/activate"
    
    pip install -q -r "$ROOT/requirements.txt" 2>/dev/null || {
        log_error "依赖安装失败，请手动执行: pip install -r requirements.txt"
        exit 1
    }
    log_ok "依赖已安装"
else
    log_ok "依赖已就绪"
fi

# ---------- 构造 pytest 参数 ----------
PYTEST_ARGS=()
case "$MODE" in
    smoke)
        PYTEST_ARGS+=("-m" "smoke" "--maxfail=1")
        ;;
    full)
        # 不加过滤，跑全部
        ;;
    failed-retest)
        PYTEST_ARGS+=("-m" "retest")
        ;;
    *)
        log_error "未知模式: $MODE (可选: smoke, full, failed-retest)"
        exit 1
        ;;
esac

if [ -n "$KEYWORD" ]; then
    PYTEST_ARGS+=("-k" "$KEYWORD")
fi

PYTEST_ARGS+=("--junitxml=$JUNIT_FILE" "--html=$HTML_FILE" "--self-contained-html" "-v")

# ---------- 执行测试 ----------
log_info "============================================"
log_info "API 自动化测试"
log_info "============================================"
log_info "模式:       $MODE"
log_info "关键字:     ${KEYWORD:-无}"
log_info "API 地址:   $API_BASE_URL"
log_info "超时(s):    $API_TIMEOUT_SECONDS"
log_info "报告目录:   $REPORT_DIR"
log_info ""

cd "$TEST_DIR"

COMMAND_LINE="$PYTHON_BIN -m pytest ${PYTEST_ARGS[*]}"
log_info "执行命令: $COMMAND_LINE"
echo ""

# 记录开始时间
START_TIME=$(date +%s)

# 执行测试，同时输出到日志文件
$PYTHON_BIN -m pytest "${PYTEST_ARGS[@]}" 2>&1 | tee "$LOG_FILE"
EXIT_CODE=${PIPESTATUS[0]}

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
log_info "============================================"
log_info "执行完成 (耗时 ${DURATION}s)"
log_info "============================================"

# ---------- 结果汇总 ----------
if [ $EXIT_CODE -eq 0 ]; then
    log_ok "API 测试全部通过 ✅"
    log_info "HTML 报告: $HTML_FILE"
    log_info "JUnit 报告: $JUNIT_FILE"
    log_info "运行日志: $LOG_FILE"
else
    log_error "API 测试存在失败 (退出码: $EXIT_CODE) ❌"
    log_info "HTML 报告: $HTML_FILE"
    log_info "JUnit 报告: $JUNIT_FILE"
    log_info "运行日志: $LOG_FILE"
    
    # 解析 JUnit 统计失败数
    if [ -f "$JUNIT_FILE" ]; then
        FAILURES=$(grep -o 'failures="[^"]*"' "$JUNIT_FILE" | head -1 | grep -o '"[0-9]*"' | tr -d '"')
        ERRORS=$(grep -o 'errors="[^"]*"' "$JUNIT_FILE" | head -1 | grep -o '"[0-9]*"' | tr -d '"')
        TESTS=$(grep -o 'tests="[^"]*"' "$JUNIT_FILE" | head -1 | grep -o '"[0-9]*"' | tr -d '"')
        log_info "统计: 总计 $TESTS 用例, 失败 $FAILURES, 错误 $ERRORS"
    fi
fi

# ---------- 生成 Markdown 报告 ----------
# 优先用 TEST_RUN_DIR（由 run-full-test-flow.sh 注入），避免并行时 ls -dt 找到错误批次
if [ -n "${TEST_RUN_DIR:-}" ]; then
    BATCH_DIR="$TEST_RUN_DIR"
else
    BATCH_DIR=$(ls -dt "$ROOT/docs/test-runs"/*/ 2>/dev/null | head -1)
fi
if [ -n "$BATCH_DIR" ]; then
    mkdir -p "$BATCH_DIR/reports" "$BATCH_DIR/defects"
    REPORT_MD="$BATCH_DIR/reports/接口自动化测试报告.md"
    
    {
        echo "# 接口自动化测试报告"
        echo ""
        echo "## 当前阶段"
        echo "接口自动化执行"
        echo ""
        echo "## 输入文件"
        echo "- docs/cases/接口测试用例-评审版.md"
        echo "- scripts/run-api-tests.sh"
        echo ""
        echo "## 产出文件"
        echo "- tests/api/reports/"
        echo "- $REPORT_MD"
        echo ""
        echo "## 正文/核心内容"
        echo "- 执行模式：$MODE"
        echo "- pytest 关键字过滤：${KEYWORD:-未设置}"
        echo "- 接口地址：$API_BASE_URL"
        echo "- 请求超时秒数：$API_TIMEOUT_SECONDS"
        echo "- 执行耗时：${DURATION}s"
        echo "- 退出码：$EXIT_CODE"
        echo "- 执行命令：$COMMAND_LINE"
        echo "- 原始结果路径："
        echo "  - tests/api/reports/html/report.html"
        echo "  - tests/api/reports/junit/report.xml"
        echo "  - tests/api/reports/raw/api-test.log"
        echo ""
        echo "## 执行结论"
        if [ $EXIT_CODE -eq 0 ]; then
            echo "- 本轮接口自动化状态：通过。"
            echo "- 下一步决策：continue"
        else
            echo "- 本轮接口自动化状态：失败。"
            echo "- 下一步决策：handoff"
        fi
        echo ""
        echo "## 风险与待确认项"
        if [ $EXIT_CODE -ne 0 ]; then
            echo "- 存在失败用例，需检查评审版输入、覆盖矩阵、服务连通性与登录态。"
        else
            echo "- 待结合覆盖矩阵确认执行范围和未实现项。"
        fi
        echo ""
        echo "## 下一步建议"
        if [ $EXIT_CODE -eq 0 ]; then
            echo "- 继续结合覆盖矩阵和原始报告确认是否可进入下一专项。"
        else
            echo "- 优先检查失败用例的断言逻辑和测试数据有效性。"
        fi
    } > "$REPORT_MD"
    
    log_ok "报告已归档: $REPORT_MD"
fi

exit $EXIT_CODE
