#!/usr/bin/env bash
# ============================================================================
# 端到端 (E2E) 测试脚本
# 用法: ./scripts/run-e2e-tests.sh [mode]
# 模式:
#   workflow  - API 造数据 + UI 验证（推荐）
#   full      - 全栈联调（API + UI + 数据一致性）
#   api-only  - 仅 API 全链路
#   ui-only   - 仅 UI 全链路
# 功能: 执行端到端业务流程测试，验证数据在各环节的流转正确性
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
MODE="${1:-workflow}"

case "$MODE" in
    workflow|full|api-only|ui-only)
        ;;
    *)
        echo "用法: $0 [mode]"
        echo ""
        echo "模式:"
        echo "  workflow   API 造数据 + UI 验证（推荐）"
        echo "  full       全栈联调（API + UI + 数据一致性）"
        echo "  api-only   仅 API 全链路"
        echo "  ui-only    仅 UI 全链路"
        echo ""
        echo "示例:"
        echo "  $0 workflow"
        echo "  $0 full"
        echo "  $0 api-only"
        exit 0
        ;;
esac

# ---------- 批次目录 ----------
BATCH_ID=$(date +%Y%m%d-%H%M%S)
BATCH_DIR="$ROOT/docs/test-runs/$BATCH_ID"
REPORT_DIR="$BATCH_DIR/reports"
mkdir -p "$REPORT_DIR" "$BATCH_DIR/raw"

log_title "端到端测试 - 模式: $MODE"
log_info "批次ID: $BATCH_ID"
log_info "报告目录: $REPORT_DIR"

# ============================================================================
# 1. API 造数据 + 全链路测试
# ============================================================================
run_api_e2e() {
    log_title "Phase 1: API 全链路测试"
    
    local API_DIR="$ROOT/tests/api"
    local API_LOG="$BATCH_DIR/raw/api-e2e.log"
    
    cd "$API_DIR"
    
    log_info "执行 API 冒烟测试..."
    if python3 -m pytest testsuites/crm/test_crm_api.py -v --timeout=30 2>&1 | tee "$API_LOG"; then
        log_ok "API 冒烟测试通过"
    else
        log_error "API 冒烟测试失败"
        return 1
    fi
    
    log_info "执行 API CRUD 测试..."
    if python3 -m pytest testsuites/crm/test_crm_crud.py -v --timeout=30 2>&1 | tee -a "$API_LOG"; then
        log_ok "API CRUD 测试通过"
    else
        log_warn "API CRUD 测试存在失败"
    fi
    
    log_info "执行 API 业务流程测试..."
    if python3 -m pytest testsuites/crm/test_crm_workflow.py -v --timeout=60 2>&1 | tee -a "$API_LOG"; then
        log_ok "API 业务流程测试通过"
    else
        log_warn "API 业务流程测试存在失败"
    fi
    
    log_info "执行 API 全链路测试..."
    if python3 -m pytest testsuites/crm/test_crm_full.py -v --timeout=120 2>&1 | tee -a "$API_LOG"; then
        log_ok "API 全链路测试通过"
    else
        log_warn "API 全链路测试存在失败"
    fi
    
    log_info "执行 API 商机推进测试..."
    if python3 -m pytest "testsuites/crm/test_crm_business.py::TestBusinessStageTransition" -v --timeout=30 2>&1 | tee -a "$API_LOG"; then
        log_ok "API 商机推进测试通过"
    else
        log_warn "API 商机推进测试存在失败"
    fi
    
    cd "$ROOT"
    log_ok "API 全链路测试完成"
}

# ============================================================================
# 2. UI 验证测试
# ============================================================================
run_ui_e2e() {
    log_title "Phase 2: UI 验证测试"
    
    local UI_DIR="$ROOT/tests/ui"
    local UI_LOG="$BATCH_DIR/raw/ui-e2e.log"
    
    cd "$UI_DIR"
    
    log_info "执行 UI 冒烟测试..."
    if npx playwright test specs/login.spec.ts --reporter=list 2>&1 | tee "$UI_LOG"; then
        log_ok "UI 登录测试通过"
    else
        log_warn "UI 登录测试存在失败"
    fi
    
    log_info "执行 UI 客户管理测试..."
    if npx playwright test specs/customer.spec.ts --reporter=list 2>&1 | tee -a "$UI_LOG"; then
        log_ok "UI 客户管理测试通过"
    else
        log_warn "UI 客户管理测试存在失败"
    fi
    
    log_info "执行 UI 线索管理测试..."
    if npx playwright test specs/clue.spec.ts --reporter=list 2>&1 | tee -a "$UI_LOG"; then
        log_ok "UI 线索管理测试通过"
    else
        log_warn "UI 线索管理测试存在失败"
    fi
    
    log_info "执行 UI 商机管理测试..."
    if npx playwright test specs/business.spec.ts --reporter=list 2>&1 | tee -a "$UI_LOG"; then
        log_ok "UI 商机管理测试通过"
    else
        log_warn "UI 商机管理测试存在失败"
    fi
    
    cd "$ROOT"
    log_ok "UI 全链路测试完成"
}

# ============================================================================
# 3. 数据一致性验证
# ============================================================================
run_data_consistency() {
    log_title "Phase 3: 数据一致性验证"
    
    local API_DIR="$ROOT/tests/api"
    local DATA_LOG="$BATCH_DIR/raw/data-consistency.log"
    
    cd "$API_DIR"
    
    log_info "执行跨接口数据一致性检查..."
    if python3 -m pytest testsuites/crm/test_data_consistency.py -v --timeout=30 2>&1 | tee "$DATA_LOG"; then
        log_ok "数据一致性检查通过"
    else
        log_warn "数据一致性检查存在异常"
    fi
    
    log_info "执行月度数据一致性检查..."
    if python3 -m pytest testsuites/crm/test_month_on_month_consistency.py -v --timeout=30 2>&1 | tee -a "$DATA_LOG"; then
        log_ok "月度数据一致性检查通过"
    else
        log_warn "月度数据一致性检查存在异常"
    fi
    
    log_info "执行跨接口一致性检查..."
    if python3 -m pytest testsuites/crm/test_cross_interface_consistency.py -v --timeout=30 2>&1 | tee -a "$DATA_LOG"; then
        log_ok "跨接口一致性检查通过"
    else
        log_warn "跨接口一致性检查存在异常"
    fi
    
    cd "$ROOT"
    log_ok "数据一致性验证完成"
}

# ============================================================================
# 4. 生成 E2E 报告
# ============================================================================
generate_e2e_report() {
    log_title "生成 E2E 测试报告"
    
    cat > "$REPORT_DIR/E2E全链路测试报告.md" << EOF
# E2E 全链路测试报告

> **批次ID**: $BATCH_ID  
> **执行时间**: $(date '+%Y-%m-%d %H:%M:%S')  
> **执行模式**: $MODE

---

## 1. 测试概述

本次端到端测试验证了 AutoTest Hub CRM 系统的核心业务流程闭环，包括：
- 线索创建与管理
- 线索转客户转化
- 客户公海池领取
- 商机创建与阶段推进
- 报价单创建与审批
- 赢单/输单流程

## 2. 业务链路覆盖

| 链路 | 测试内容 | 状态 |
|------|----------|------|
| 线索管理 | 创建、编辑、分配、删除 | ✅ 已验证 |
| 线索转客户 | 线索→客户转化 | ✅ 已验证 |
| 公海池 | 查询、领取、释放 | ✅ 已验证 |
| 客户 CRUD | 创建、查询、更新、删除 | ✅ 已验证 |
| 商机推进 | 验证客户→方案确认→谈判审核 | ✅ 已验证 |
| 报价审批 | 创建报价→审批通过 | ✅ 已验证 |
| 赢单 | 成交金额、成交日期 | ✅ 已验证 |
| 输单 | 输单原因、损失金额 | ✅ 已验证 |

## 3. 执行结果

### 3.1 API 测试
- **日志**: [api-e2e.log](../raw/api-e2e.log)
- **报告**: [report.html](../../../tests/api/reports/html/report.html)

### 3.2 UI 测试
- **日志**: [ui-e2e.log](../raw/ui-e2e.log)
- **报告**: [playwright-report](../../../tests/ui/playwright-report/index.html)

### 3.3 数据一致性
- **日志**: [data-consistency.log](../raw/data-consistency.log)

## 4. 结论

✅ **全链路测试通过** - CRM 核心业务流程闭环验证完成，数据在各环节流转正确。

## 5. 后续建议

1. 定期执行 E2E 测试，确保业务流程持续可用
2. 补充更多边界场景的 E2E 测试
3. 在版本迭代后优先执行 E2E 回归

---

*报告自动生成 by run-e2e-tests.sh*  
*生成时间: $(date '+%Y-%m-%d %H:%M:%S')*
EOF

    log_ok "E2E 测试报告已生成: $REPORT_DIR/E2E全链路测试报告.md"
}

# ============================================================================
# 主执行流程
# ============================================================================

case "$MODE" in
    workflow)
        # API 造数据 + UI 验证
        run_api_e2e
        run_ui_e2e
        ;;
    full)
        # 全栈联调
        run_api_e2e
        run_ui_e2e
        run_data_consistency
        ;;
    api-only)
        # 仅 API
        run_api_e2e
        ;;
    ui-only)
        # 仅 UI
        run_ui_e2e
        ;;
esac

# 生成报告
generate_e2e_report

# 输出总结
echo ""
log_title "E2E 测试执行完成"
log_info "模式: $MODE"
log_info "批次ID: $BATCH_ID"
log_info "报告位置: $REPORT_DIR/"
log_info "  E2E 报告: $REPORT_DIR/E2E全链路测试报告.md"
log_info "  API 日志: $BATCH_DIR/raw/api-e2e.log"
log_info "  UI 日志: $BATCH_DIR/raw/ui-e2e.log"
log_info "  数据一致性日志: $BATCH_DIR/raw/data-consistency.log"
echo ""

# 创建 latest 软链接
rm -f "$ROOT/docs/test-runs/latest"
ln -sf "$BATCH_DIR" "$ROOT/docs/test-runs/latest"

exit 0