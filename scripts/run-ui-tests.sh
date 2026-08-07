#!/usr/bin/env bash
# ============================================================================
# UI 自动化测试 - Linux 原生执行脚本
# 用法: ./scripts/run-ui-tests.sh
# 环境: 需要 Node.js 18+, npm, Playwright browsers
# ============================================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UI_DIR="$ROOT/tests/ui"

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

# ---------- Node.js 检查 ----------
if ! command -v node &>/dev/null; then
    log_error "Node.js 未找到，请安装 Node.js 18+ (推荐 v20 LTS)"
    exit 1
fi

NODE_VERSION=$(node --version | sed 's/v//')
NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d. -f1)
if [ "$NODE_MAJOR" -lt 18 ]; then
    log_error "Node.js 版本过低: v$NODE_VERSION (需要 >= 18)"
    exit 1
fi
log_info "Node.js 版本: v$NODE_VERSION"

# ---------- 检查/安装 npm 依赖 ----------
cd "$UI_DIR"

if [ ! -d "node_modules" ]; then
    log_info "npm 依赖未安装，执行 npm install..."
    npm install 2>&1 | tail -5
    if [ $? -ne 0 ]; then
        log_error "npm install 失败"
        exit 1
    fi
    log_ok "依赖已安装"
else
    log_ok "依赖已就绪 (node_modules 存在)"
fi

# ---------- 检查系统依赖（关键！）----------
log_info "检查 Playwright 系统依赖..."
MISSING_DEPS=()

check_lib() {
    if ! ldconfig -p 2>/dev/null | grep -q "$1"; then
        MISSING_DEPS+=("$1")
        return 1
    fi
    return 0
}

check_lib "libgbm" || log_warn "缺少 libgbm (需要 mesa-libgbm 包)"
check_lib "libnss3" || log_warn "缺少 libnss3"
check_lib "libatk-1.0" || log_warn "缺少 libatk1.0"
check_lib "libatk-bridge" || log_warn "缺少 libatk-bridge"
check_lib "libcups" || log_warn "缺少 libcups"
check_lib "libpango-1.0" || log_warn "缺少 libpango"
check_lib "libasound" || log_warn "缺少 libasound"

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    log_warn "检测到缺失的系统依赖，尝试安装..."
    log_info "正在安装 mesa-libgbm 等依赖..."
    
    # openEuler/CentOS 系统
    if command -v yum &>/dev/null; then
        yum install -y mesa-libgbm mesa-libgbm-devel 2>&1 | tail -3
    # Ubuntu/Debian 系统
    elif command -v apt-get &>/dev/null; then
        apt-get update -qq && apt-get install -y libgbm1 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libpango-1.0-0 libasound2 2>&1 | tail -3
    fi
    
    log_ok "依赖安装完成"
else
    log_ok "系统依赖已就绪"
fi

# ---------- 检查 Playwright 浏览器 ----------
if ! npx playwright install --dry-run &>/dev/null 2>&1; then
    log_warn "Playwright 浏览器可能未安装，尝试安装..."
    npx playwright install chromium 2>&1 | tail -5
    if [ $? -ne 0 ]; then
        log_error "Playwright Chromium 安装失败"
        exit 1
    fi
    log_ok "Playwright Chromium 已安装"
else
    log_ok "Playwright 浏览器已就绪"
fi

# ---------- 执行 UI 测试 ----------
log_info "============================================"
log_info "UI 自动化测试 (Playwright)"
log_info "============================================"
log_info "项目目录: $UI_DIR"
log_info "浏览器:   Chromium"
log_info ""

START_TIME=$(date +%s)

# 支持参数: smoke 模式或全量
if [ "${1:-}" = "smoke" ]; then
    log_info "执行模式: 冒烟测试 (仅 crm-smoke)"
    npx playwright test specs/crm/crm-smoke.spec.ts --reporter=html,json 2>&1
else
    log_info "执行模式: 全量测试"
    npx playwright test --reporter=html,json 2>&1
fi

EXIT_CODE=$?
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
log_info "============================================"
log_info "执行完成 (耗时 ${DURATION}s)"
log_info "============================================"

# ---------- 结果汇总 ----------
REPORT_DIR="$UI_DIR/playwright-report"
HTML_REPORT="$REPORT_DIR/index.html"
JSON_REPORT="$UI_DIR/test-results.json"

if [ $EXIT_CODE -eq 0 ]; then
    log_ok "UI 测试全部通过 ✅"
else
    log_error "UI 测试存在失败 (退出码: $EXIT_CODE) ❌"
fi

log_info "HTML 报告: $HTML_REPORT"
log_info "JSON 报告: $JSON_REPORT"

# ---------- 归档报告 ----------
BATCH_DIR=$(ls -dt "$ROOT/docs/test-runs"/*/ 2>/dev/null | head -1)
if [ -n "$BATCH_DIR" ]; then
    mkdir -p "$BATCH_DIR/reports" "$BATCH_DIR/defects"
    REPORT_MD="$BATCH_DIR/reports/UI自动化测试报告.md"
    
    {
        echo "# UI自动化测试报告"
        echo ""
        echo "## 当前阶段"
        echo "UI 自动化执行"
        echo ""
        echo "## 输入文件"
        echo "- scripts/run-ui-tests.sh"
        echo ""
        echo "## 产出文件"
        echo "- tests/ui/reports/"
        echo "- $REPORT_MD"
        echo ""
        echo "## 正文/核心内容"
        echo "- 执行模式：${1:-full}"
        echo "- 执行耗时：${DURATION}s"
        echo "- 退出码：$EXIT_CODE"
        echo "- 执行命令: npx playwright test ${1:-}"
        echo "- 原始结果路径："
        echo "  - tests/ui/reports/html/index.html"
        echo "  - tests/ui/reports/raw/result.json"
        echo ""
        echo "## 执行结论"
        if [ $EXIT_CODE -eq 0 ]; then
            echo "- 本轮 UI 自动化状态：通过。"
            echo "- 下一步决策：continue"
        else
            echo "- 本轮 UI 自动化状态：失败。"
            echo "- 下一步决策：handoff"
        fi
        echo ""
        echo "## 风险与待确认项"
        if [ $EXIT_CODE -ne 0 ]; then
            echo "- 存在失败用例，需检查页面结构是否变更、元素定位是否有效。"
        else
            echo "- 待结合覆盖矩阵确认执行范围和未实现项。"
        fi
        echo ""
        echo "## 下一步建议"
        if [ $EXIT_CODE -eq 0 ]; then
            echo "- 继续确认兼容性测试和回归覆盖。"
        else
            echo "- 优先检查失败用例的元素定位和页面加载策略。"
        fi
    } > "$REPORT_MD"
    
    log_ok "报告已归档: $REPORT_MD"
fi

exit $EXIT_CODE
