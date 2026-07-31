#!/usr/bin/env bash
# ============================================================================
# Linux 环境检查与初始化脚本
# 用法: ./scripts/setup-linux.sh
# 功能: 检查系统依赖，安装 Python/Node/Locust/Playwright 等测试所需环境
# ============================================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

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

PASS=0
FAIL=0
WARN=0

check_pass() { PASS=$((PASS + 1)); log_ok "✅ $*"; }
check_fail() { FAIL=$((FAIL + 1)); log_error "❌ $*"; }
check_warn() { WARN=$((WARN + 1)); log_warn "⚠️  $*"; }

# ---------- 分隔线 ----------
section() { echo ""; log_info "===== $* ====="; }

# ============================================================================
# 1. 操作系统信息
# ============================================================================
section "操作系统信息"
log_info "系统: $(uname -srm)"
log_info "架构: $(uname -m)"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    log_info "发行版: $PRETTY_NAME"
fi

# ============================================================================
# 2. Python 环境
# ============================================================================
section "Python 环境"

PYTHON_BIN="python3"
if ! command -v $PYTHON_BIN &>/dev/null; then
    PYTHON_BIN="python"
fi

if command -v $PYTHON_BIN &>/dev/null; then
    PYTHON_VERSION=$($PYTHON_BIN --version 2>&1)
    PY_MAJOR=$($PYTHON_BIN -c 'import sys; print(sys.version_info.major)')
    PY_MINOR=$($PYTHON_BIN -c 'import sys; print(sys.version_info.minor)')
    
    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 10 ]; then
        check_pass "Python 版本: $PYTHON_VERSION (>= 3.10)"
    else
        check_fail "Python 版本过低: $PYTHON_VERSION (需要 >= 3.10)"
    fi
    
    # 检查 pip
    if $PYTHON_BIN -m pip --version &>/dev/null; then
        check_pass "pip 已安装"
    else
        check_fail "pip 未安装"
    fi
    
    # 检查 venv
    if $PYTHON_BIN -m venv --help &>/dev/null; then
        check_pass "python3-venv 可用"
    else
        check_warn "python3-venv 不可用 (建议安装: apt install python3-venv)"
    fi
    
    # 检查核心依赖
    for pkg in pytest requests PyYAML locust; do
        if $PYTHON_BIN -c "import $pkg" &>/dev/null; then
            check_pass "Python 依赖: $pkg"
        else
            check_warn "Python 依赖未安装: $pkg"
        fi
    done
else
    check_fail "Python 未找到，请安装 Python 3.10+"
    log_info "Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    log_info "CentOS/RHEL:   sudo yum install python3 python3-pip"
fi

# ============================================================================
# 3. Node.js 环境
# ============================================================================
section "Node.js 环境"

if command -v node &>/dev/null; then
    NODE_VERSION=$(node --version)
    NODE_MAJOR=$(echo "$NODE_VERSION" | sed 's/v//' | cut -d. -f1)
    
    if [ "$NODE_MAJOR" -ge 18 ]; then
        check_pass "Node.js 版本: $NODE_VERSION (>= 18)"
    else
        check_warn "Node.js 版本: $NODE_VERSION (建议 >= 18, 推荐 v20 LTS)"
    fi
    
    if command -v npm &>/dev/null; then
        NPM_VERSION=$(npm --version)
        check_pass "npm 版本: $NPM_VERSION"
    else
        check_fail "npm 未找到"
    fi
    
    # 检查 Playwright
    if $PYTHON_BIN -c "import playwright" &>/dev/null 2>&1 || npx playwright --version &>/dev/null 2>&1; then
        check_pass "Playwright 可用"
    else
        check_warn "Playwright 未安装 (UI 测试需要)"
        log_info "  安装: cd tests/ui && npm install && npx playwright install chromium"
    fi
else
    check_warn "Node.js 未安装 (UI 测试需要)"
    log_info "安装方式:"
    log_info "  Ubuntu/Debian: curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
    log_info "                 sudo apt install nodejs"
    log_info "  或使用 nvm:    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash"
fi

# ============================================================================
# 4. 可选工具
# ============================================================================
section "可选工具"

for tool in git curl wget make gcc; do
    if command -v $tool &>/dev/null; then
        check_pass "$tool 已安装"
    else
        check_warn "$tool 未安装"
    fi
done

# ============================================================================
# 5. 项目文件检查
# ============================================================================
section "项目文件完整性"

REQUIRED_FILES=(
    "requirements.txt"
    ".env"
    "tests/api/pytest.ini"
    "tests/api/conftest.py"
    "tests/ui/package.json"
    "tests/ui/playwright.config.ts"
    "tests/performance/locust/config/load_profiles.yaml"
    "scripts/run-api-tests.sh"
    "scripts/run-ui-tests.sh"
    "scripts/run-perf-tests.sh"
    "scripts/run-security-tests.sh"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$ROOT/$file" ]; then
        check_pass "$file"
    else
        check_warn "$file 缺失"
    fi
done

# ============================================================================
# 6. 网络连通性
# ============================================================================
section "网络连通性"

TEST_URL="${API_BASE_URL:-http://192.168.2.97:6089/prod-api}"
if curl -s --connect-timeout 5 "$TEST_URL" -o /dev/null -w '%{http_code}' 2>/dev/null | grep -q '200\|301\|401\|403'; then
    check_pass "API 服务可达: $TEST_URL"
else
    check_warn "API 服务不可达: $TEST_URL (请确认服务已启动或网络可访问)"
fi

# ============================================================================
# 7. 权限检查
# ============================================================================
section "执行权限"

SCRIPTS=(
    "scripts/run-api-tests.sh"
    "scripts/run-ui-tests.sh"
    "scripts/run-perf-tests.sh"
    "scripts/run-security-tests.sh"
)

for script in "${SCRIPTS[@]}"; do
    if [ -f "$ROOT/$script" ]; then
        if [ -x "$ROOT/$script" ]; then
            check_pass "$script (可执行)"
        else
            log_warn "$script (需添加执行权限)"
            log_info "  执行: chmod +x $script"
        fi
    fi
done

# ============================================================================
# 汇总
# ============================================================================
echo ""
log_info "============================================"
log_info "环境检查汇总"
log_info "============================================"
log_ok "通过: $PASS"
[ $WARN -gt 0 ] && log_warn "警告: $WARN"
[ $FAIL -gt 0 ] && log_error "失败: $FAIL"

if [ $FAIL -gt 0 ]; then
    echo ""
    log_error "存在必需依赖缺失，请根据上方提示安装后重试。"
    exit 1
elif [ $WARN -gt 3 ]; then
    echo ""
    log_warn "警告项较多，部分功能可能受限。建议补齐后再运行测试。"
else
    echo ""
    log_ok "环境检查基本通过，可以开始测试！"
    log_info "快速开始:"
    log_info "  API 测试:   ./scripts/run-api-tests.sh smoke"
    log_info "  UI 测试:    ./scripts/run-ui-tests.sh smoke"
    log_info "  性能测试:   ./scripts/run-perf-tests.sh smoke"
    log_info "  安全测试:   ./scripts/run-security-tests.sh"
fi

exit 0
