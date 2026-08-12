#!/usr/bin/env bash
# ============================================================================
# 测试框架共享库 - system.yaml 解析与通用工具函数
# 用法: source "$ROOT/shared/lib/test_framework.sh"
# 功能: 为各子脚本提供统一的 system.yaml 解析、颜色输出、日志等工具
# ============================================================================

# 防止重复 source
if [ -n "${_TEST_FRAMEWORK_SH_LOADED:-}" ]; then
    return 0 2>/dev/null || true
fi
_TEST_FRAMEWORK_SH_LOADED=1

# ---------- 颜色输出 ----------
if [ -z "${RED:-}" ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    NC='\033[0m'
fi

log_info()  { echo -e "${CYAN}[INFO]${NC} $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_title() { echo -e "\n${BOLD}${CYAN}==== $* ====${NC}\n"; }

# ---------- Python 检测 ----------
# 设置全局 PYTHON_BIN 变量
detect_python() {
    if [ -n "${PYTHON_BIN:-}" ]; then
        return 0
    fi
    PYTHON_BIN="python3"
    if ! command -v $PYTHON_BIN &>/dev/null; then
        PYTHON_BIN="python"
    fi
    if ! command -v $PYTHON_BIN &>/dev/null; then
        log_error "Python 未找到，请安装 Python 3.10+"
        return 1
    fi
    return 0
}

# ---------- system.yaml 配置加载 ----------
# 将 system.yaml 中的配置导出为 shell 变量，供子脚本使用
# 用法: load_system_config
# 导出变量:
#   SYS_ID, SYS_NAME, SYS_BASE_URL, SYS_API_BASE_PATH, SYS_TIMEOUT
#   SYS_AUTH_TYPE, SYS_LOGIN_PATH, SYS_TOKEN_FIELD, SYS_TOKEN_TYPE
#   SYS_USERNAME_FIELD, SYS_PASSWORD_FIELD, SYS_PASSWORD_ENCRYPTION
#   API_TESTS_DIR, UI_TESTS_DIR, PERF_TESTS_DIR, SEC_TESTS_DIR
#   SMOKE_MARKER, UI_BASE_URL, UI_GLOBAL_SETUP
#   PERF_SMOKE_USERS, PERF_SMOKE_SPAWN_RATE, PERF_SMOKE_DURATION
#   PERF_FULL_USERS, PERF_FULL_SPAWN_RATE, PERF_FULL_DURATION
#   SEC_TARGET_URL
#   SYS_OUTPUT_DIR, SYS_TEST_CASES_DIR, SYS_TEST_DATA_DIR
load_system_config() {
    local root="${1:-$ROOT}"
    local system_id="${2:-${TEST_SYSTEM_ID:-crm}}"
    
    SYS_YAML="$root/projects/$system_id/system.yaml"
    
    # 系统项目目录（相对路径，子脚本会拼接 $ROOT 前缀）
    SYS_PROJECT_DIR="projects/$system_id"

    # 设置默认值（相对于 SYS_PROJECT_DIR）
    SYS_ID="$system_id"
    SYS_NAME="$system_id"
    SYS_BASE_URL=""
    SYS_API_BASE_PATH="/prod-api"
    SYS_TIMEOUT=30
    SYS_AUTH_TYPE=""
    SYS_LOGIN_PATH=""
    SYS_TOKEN_FIELD="access_token"
    SYS_TOKEN_TYPE="Bearer"
    SYS_USERNAME_FIELD="username"
    SYS_PASSWORD_FIELD="password"
    SYS_PASSWORD_ENCRYPTION="plaintext"
    API_TESTS_DIR="tests/api/testsuites"
    UI_TESTS_DIR="tests/ui/specs"
    PERF_TESTS_DIR="tests/performance/locust"
    SEC_TESTS_DIR="tests/security"
    SMOKE_MARKER="smoke"
    UI_BASE_URL=""
    UI_GLOBAL_SETUP=""
    PERF_SMOKE_USERS=5
    PERF_SMOKE_SPAWN_RATE=1
    PERF_SMOKE_DURATION="30s"
    PERF_FULL_USERS=50
    PERF_FULL_SPAWN_RATE=5
    PERF_FULL_DURATION="120s"
    SEC_TARGET_URL=""
    SYS_OUTPUT_DIR="test-runs"
    SYS_TEST_CASES_DIR="docs/cases"
    SYS_TEST_DATA_DIR="tests/data"
    
    if [ ! -f "$SYS_YAML" ]; then
        log_warn "system.yaml 不存在: $SYS_YAML，使用默认配置"
        # 拼接系统项目目录前缀
        API_TESTS_DIR="$SYS_PROJECT_DIR/$API_TESTS_DIR"
        UI_TESTS_DIR="$SYS_PROJECT_DIR/$UI_TESTS_DIR"
        PERF_TESTS_DIR="$SYS_PROJECT_DIR/$PERF_TESTS_DIR"
        SEC_TESTS_DIR="$SYS_PROJECT_DIR/$SEC_TESTS_DIR"
        SYS_OUTPUT_DIR="$SYS_PROJECT_DIR/$SYS_OUTPUT_DIR"
        SYS_TEST_CASES_DIR="$SYS_PROJECT_DIR/$SYS_TEST_CASES_DIR"
        SYS_TEST_DATA_DIR="$SYS_PROJECT_DIR/$SYS_TEST_DATA_DIR"
        return 0
    fi
    
    detect_python || return 1
    
    # 用 Python 解析 yaml，导出为 shell sourceable 格式
    local config_tmp
    config_tmp=$(mktemp /tmp/system_config_XXXXXX.sh)
    
    $PYTHON_BIN -c "
import yaml
import sys

try:
    with open('$SYS_YAML') as f:
        config = yaml.safe_load(f)
    
    if config is None:
        config = {}
    
    def safe_get(d, *keys, default=''):
        for k in keys:
            if not isinstance(d, dict) or k not in d:
                return default
            d = d[k]
        return d if d is not None else default
    
    def print_val(name, val):
        if val is None:
            val = ''
        # 转义单引号
        val_str = str(val).replace(\"'\", \"'\\\\\\\\''\")
        print(f\"{name}='{val_str}'\")
    
    # 基本信息
    print_val('SYS_ID', safe_get(config, 'id', default='$system_id'))
    print_val('SYS_NAME', safe_get(config, 'name', default='$system_id'))
    
    # 协议配置
    proto = safe_get(config, 'protocols', 'default', default={})
    if isinstance(proto, dict):
        print_val('SYS_BASE_URL', safe_get(proto, 'config', 'base_url'))
        print_val('SYS_API_BASE_PATH', safe_get(proto, 'config', 'api_base_path', default='/prod-api'))
        timeout = safe_get(proto, 'config', 'timeout')
        if timeout:
            print_val('SYS_TIMEOUT', timeout)
    
    # 认证配置
    auth = safe_get(config, 'auth', default={})
    if isinstance(auth, dict):
        print_val('SYS_AUTH_TYPE', safe_get(auth, 'type'))
        auth_cfg = safe_get(auth, 'config', default={})
        if isinstance(auth_cfg, dict):
            print_val('SYS_LOGIN_PATH', safe_get(auth_cfg, 'login_path'))
            print_val('SYS_TOKEN_FIELD', safe_get(auth_cfg, 'token_field', default='access_token'))
            print_val('SYS_TOKEN_TYPE', safe_get(auth_cfg, 'token_type', default='Bearer'))
            print_val('SYS_USERNAME_FIELD', safe_get(auth_cfg, 'username_field', default='username'))
            print_val('SYS_PASSWORD_FIELD', safe_get(auth_cfg, 'password_field', default='password'))
            print_val('SYS_PASSWORD_ENCRYPTION', safe_get(auth_cfg, 'password_encryption', default='plaintext'))
    
    # 测试范围 - API
    scope = safe_get(config, 'test_scope', default={})
    if isinstance(scope, dict):
        api_scope = safe_get(scope, 'api', default={})
        if isinstance(api_scope, dict):
            print_val('API_TESTS_DIR', safe_get(api_scope, 'tests_dir', default='tests/api/testsuites'))
            print_val('SMOKE_MARKER', safe_get(api_scope, 'smoke_marker', default='smoke'))
        
        ui_scope = safe_get(scope, 'ui', default={})
        if isinstance(ui_scope, dict):
            print_val('UI_TESTS_DIR', safe_get(ui_scope, 'tests_dir', default='tests/ui/specs'))
            print_val('UI_BASE_URL', safe_get(ui_scope, 'base_url'))
            print_val('UI_GLOBAL_SETUP', safe_get(ui_scope, 'global_setup'))
        
        perf_scope = safe_get(scope, 'performance', default={})
        if isinstance(perf_scope, dict):
            print_val('PERF_TESTS_DIR', safe_get(perf_scope, 'tests_dir', default='tests/performance/locust'))
            smoke_cfg = safe_get(perf_scope, 'smoke', default={})
            if isinstance(smoke_cfg, dict):
                print_val('PERF_SMOKE_USERS', safe_get(smoke_cfg, 'users', default=5))
                print_val('PERF_SMOKE_SPAWN_RATE', safe_get(smoke_cfg, 'spawn_rate', default=1))
                print_val('PERF_SMOKE_DURATION', safe_get(smoke_cfg, 'duration', default='30s'))
            full_cfg = safe_get(perf_scope, 'full', default={})
            if isinstance(full_cfg, dict):
                print_val('PERF_FULL_USERS', safe_get(full_cfg, 'users', default=50))
                print_val('PERF_FULL_SPAWN_RATE', safe_get(full_cfg, 'spawn_rate', default=5))
                print_val('PERF_FULL_DURATION', safe_get(full_cfg, 'duration', default='120s'))
        
        sec_scope = safe_get(scope, 'security', default={})
        if isinstance(sec_scope, dict):
            print_val('SEC_TESTS_DIR', safe_get(sec_scope, 'tests_dir', default='tests/security'))
            print_val('SEC_TARGET_URL', safe_get(sec_scope, 'target_url'))
    
    # 路径映射
    paths = safe_get(config, 'paths', default={})
    if isinstance(paths, dict):
        print_val('SYS_OUTPUT_DIR', safe_get(paths, 'output_dir', default='test-runs'))
        print_val('SYS_TEST_CASES_DIR', safe_get(paths, 'test_cases', default='docs/cases'))
        print_val('SYS_TEST_DATA_DIR', safe_get(paths, 'test_data', default='tests/data'))

except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(0)
" > "$config_tmp" 2>/dev/null
    
    if [ -f "$config_tmp" ]; then
        # shellcheck disable=SC1090
        source "$config_tmp" 2>/dev/null
        rm -f "$config_tmp"

        # 拼接系统项目目录前缀（system.yaml 中的路径相对于系统目录）
        API_TESTS_DIR="$SYS_PROJECT_DIR/$API_TESTS_DIR"
        UI_TESTS_DIR="$SYS_PROJECT_DIR/$UI_TESTS_DIR"
        PERF_TESTS_DIR="$SYS_PROJECT_DIR/$PERF_TESTS_DIR"
        SEC_TESTS_DIR="$SYS_PROJECT_DIR/$SEC_TESTS_DIR"
        SYS_OUTPUT_DIR="$SYS_PROJECT_DIR/$SYS_OUTPUT_DIR"
        SYS_TEST_CASES_DIR="$SYS_PROJECT_DIR/$SYS_TEST_CASES_DIR"
        SYS_TEST_DATA_DIR="$SYS_PROJECT_DIR/$SYS_TEST_DATA_DIR"

        log_info "已加载 system.yaml 配置 (系统: $SYS_ID)"
    else
        log_warn "解析 system.yaml 失败，使用默认配置"
    fi
}

# ---------- 从 system.yaml 获取 API 基础 URL ----------
# 优先级: 环境变量 > system.yaml > 默认值
get_api_base_url() {
    local default_url="${1:-http://192.168.2.97:6089/prod-api}"
    
    if [ -n "${API_BASE_URL:-}" ]; then
        echo "$API_BASE_URL"
        return
    fi
    
    if [ -n "${SYS_BASE_URL:-}" ]; then
        local api_path="${SYS_API_BASE_PATH:-/prod-api}"
        # 确保 base_url 和 api_base_path 之间只有一个斜杠
        local clean_base="${SYS_BASE_URL%/}"
        local clean_path="${api_path#/}"
        echo "${clean_base}/${clean_path}"
        return
    fi
    
    echo "$default_url"
}

# ---------- 获取测试目录 ----------
# 用法: get_tests_dir <test_type> <default_dir>
# test_type: api | ui | performance | security
get_tests_dir() {
    local test_type="$1"
    local default_dir="${2:-}"
    
    case "$test_type" in
        api)
            echo "${API_TESTS_DIR:-$default_dir}"
            ;;
        ui)
            echo "${UI_TESTS_DIR:-$default_dir}"
            ;;
        performance)
            echo "${PERF_TESTS_DIR:-$default_dir}"
            ;;
        security)
            echo "${SEC_TESTS_DIR:-$default_dir}"
            ;;
        *)
            echo "$default_dir"
            ;;
    esac
}

# ---------- 获取批次输出目录 ----------
# 优先使用 TEST_RUN_DIR，否则使用最新的批次目录
get_batch_dir() {
    local root="${1:-$ROOT}"
    
    # 优先级 1: TEST_RUN_DIR 环境变量（由 run-full-test-flow.sh 注入）
    if [ -n "${TEST_RUN_DIR:-}" ]; then
        echo "$TEST_RUN_DIR"
        return
    fi
    
    # 优先级 2: 创建当前系统的新批次目录（避免复用其他系统的旧批次）
    local output_dir="${SYS_OUTPUT_DIR:-projects/${TEST_SYSTEM_ID:-crm}/test-runs}"
    local system_id="${SYS_ID:-${TEST_SYSTEM_ID:-crm}}"
    local batch_id
    batch_id=$(get_or_create_batch_id "$system_id")
    local batch_dir="$root/$output_dir/$batch_id"
    mkdir -p "$batch_dir/reports" "$batch_dir/defects" "$batch_dir/raw"
    echo "$batch_dir"
}

# ---------- 检查 Python 依赖 ----------
check_python_deps() {
    local deps=("$@")
    local missing=()
    
    for dep in "${deps[@]}"; do
        if ! $PYTHON_BIN -c "import $dep" &>/dev/null; then
            missing+=("$dep")
        fi
    done
    
    if [ ${#missing[@]} -gt 0 ]; then
        return 1
    fi
    return 0
}

# ---------- 安装 Python 依赖 ----------
install_python_deps() {
    local root="${1:-$ROOT}"
    
    if [ ! -d "$root/.venv" ]; then
        log_info "创建 Python 虚拟环境..."
        $PYTHON_BIN -m venv "$root/.venv" 2>/dev/null || {
            log_error "虚拟环境创建失败，请安装 python3-venv"
            return 1
        }
    fi
    
    # shellcheck disable=SC1091
    source "$root/.venv/bin/activate"
    
    if [ -f "$root/requirements.txt" ]; then
        log_info "安装依赖..."
        pip install -q -r "$root/requirements.txt" 2>/dev/null || {
            log_error "依赖安装失败，请手动执行: pip install -r requirements.txt"
            return 1
        }
    fi
    
    return 0
}

# ---------- 确保输出目录存在 ----------
ensure_output_dirs() {
    local batch_dir="${1:-}"
    
    if [ -z "$batch_dir" ]; then
        batch_dir=$(get_batch_dir)
    fi
    
    if [ -n "$batch_dir" ]; then
        mkdir -p "$batch_dir/reports" "$batch_dir/defects" "$batch_dir/raw"
        echo "$batch_dir"
    fi
}

# ---------- 获取/创建批次 ID ----------
get_or_create_batch_id() {
    local system_id="${1:-${TEST_SYSTEM_ID:-crm}}"
    
    if [ -n "${TEST_RUN_ID:-}" ]; then
        echo "$TEST_RUN_ID"
        return
    fi
    
    local short_uuid
    short_uuid=$(uuidgen 2>/dev/null | cut -c1-8 || $PYTHON_BIN -c "import uuid; print(uuid.uuid4().hex[:8])" 2>/dev/null || echo "local")
    echo "$(date +%Y%m%d-%H%M%S)-${system_id}-${short_uuid}"
}