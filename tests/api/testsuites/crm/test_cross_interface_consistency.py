import pytest
import datetime


def get_current_month():
    now = datetime.datetime.now()
    return f"{now.year}-{str(now.month).zfill(2)}"


def get_current_user_goal(crm_client, authorized_headers):
    crm_client.session.headers.update(authorized_headers)
    
    response = crm_client.get_goal_list()
    data = response.json()
    
    if data.get("code") != 200:
        pytest.skip(f"目标管理接口返回错误: {data.get('msg')}")
    
    goals = data.get("data", [])
    current_month = get_current_month()
    
    for goal in goals:
        if goal.get("targetMonth") == current_month:
            return goal
    
    pytest.skip(f"未找到当前月份({current_month})的目标数据")


def get_performance_report(crm_client, authorized_headers):
    crm_client.session.headers.update(authorized_headers)
    
    response = crm_client.request("GET", "/crm/statistics/performance/report")
    data = response.json()
    
    if data.get("code") != 200:
        pytest.skip(f"绩效报表接口返回错误: {data.get('msg')}")
    
    return data.get("data", [])


def get_current_user_performance(performance_data, user_id):
    for record in performance_data:
        if record.get("userId") == user_id:
            return record
    return None


def test_cross_interface_sign_amount_consistency(crm_client, authorized_headers):
    """CROSS-CONSISTENCY-001 签约额跨接口一致性验证（目标管理接口 vs 报表中心接口）"""
    crm_client.session.headers.update(authorized_headers)
    
    goal = get_current_user_goal(crm_client, authorized_headers)
    performance_data = get_performance_report(crm_client, authorized_headers)
    
    current_month = goal.get("targetMonth")
    user_id = goal.get("userId")
    user_name = goal.get("userName")
    
    performance = get_current_user_performance(performance_data, user_id)
    assert performance is not None, f"未找到用户 {user_id} 的绩效数据"
    
    sign_item = None
    for item in goal.get("items", []):
        if item.get("itemCode") == "signAmount":
            sign_item = item
            break
    
    assert sign_item is not None, "未找到签约额目标项"
    
    goal_sign_target = float(sign_item.get("targetValue", 0) or 0)
    goal_sign_actual = float(sign_item.get("actualValue", 0) or 0)
    goal_sign_rate = float(sign_item.get("completionRate", 0) or 0)
    
    report_sign_target = float(performance.get("signAmountTarget", 0) or 0)
    report_sign_actual = float(performance.get("signAmountActual", 0) or 0)
    report_sign_rate = float(performance.get("signAmountRate", 0) or 0)
    
    print(f"\n=== 签约额跨接口一致性验证 ({user_name} - {current_month}) ===")
    print(f"目标管理接口: 目标={goal_sign_target}万元, 实际={goal_sign_actual}万元, 完成率={goal_sign_rate}%")
    print(f"报表中心接口: 目标={report_sign_target}万元, 实际={report_sign_actual}万元, 完成率={report_sign_rate}%")
    
    assert abs(goal_sign_target - report_sign_target) < 0.01, f"签约额目标不一致: 目标管理={goal_sign_target}, 报表中心={report_sign_target}"
    assert abs(goal_sign_actual - report_sign_actual) < 0.01, f"签约额实际不一致: 目标管理={goal_sign_actual}, 报表中心={report_sign_actual}"
    assert abs(goal_sign_rate - report_sign_rate) < 0.01, f"签约额完成率不一致: 目标管理={goal_sign_rate}, 报表中心={report_sign_rate}"
    
    print(f"✅ 签约额跨接口数据一致")


def test_cross_interface_payment_amount_consistency(crm_client, authorized_headers):
    """CROSS-CONSISTENCY-002 回款额跨接口一致性验证（目标管理接口 vs 报表中心接口）"""
    crm_client.session.headers.update(authorized_headers)
    
    goal = get_current_user_goal(crm_client, authorized_headers)
    performance_data = get_performance_report(crm_client, authorized_headers)
    
    current_month = goal.get("targetMonth")
    user_id = goal.get("userId")
    user_name = goal.get("userName")
    
    performance = get_current_user_performance(performance_data, user_id)
    assert performance is not None, f"未找到用户 {user_id} 的绩效数据"
    
    payment_item = None
    for item in goal.get("items", []):
        if item.get("itemCode") == "paymentAmount":
            payment_item = item
            break
    
    assert payment_item is not None, "未找到回款额目标项"
    
    goal_payment_target = float(payment_item.get("targetValue", 0) or 0)
    goal_payment_actual = float(payment_item.get("actualValue", 0) or 0)
    goal_payment_rate = float(payment_item.get("completionRate", 0) or 0)
    
    report_payment_target = float(performance.get("paymentAmountTarget", 0) or 0)
    report_payment_actual = float(performance.get("paymentAmountActual", 0) or 0)
    report_payment_rate = float(performance.get("paymentAmountRate", 0) or 0)
    
    print(f"\n=== 回款额跨接口一致性验证 ({user_name} - {current_month}) ===")
    print(f"目标管理接口: 目标={goal_payment_target}万元, 实际={goal_payment_actual}万元, 完成率={goal_payment_rate}%")
    print(f"报表中心接口: 目标={report_payment_target}万元, 实际={report_payment_actual}万元, 完成率={report_payment_rate}%")
    
    assert abs(goal_payment_target - report_payment_target) < 0.01, f"回款额目标不一致: 目标管理={goal_payment_target}, 报表中心={report_payment_target}"
    assert abs(goal_payment_actual - report_payment_actual) < 0.01, f"回款额实际不一致: 目标管理={goal_payment_actual}, 报表中心={report_payment_actual}"
    assert abs(goal_payment_rate - report_payment_rate) < 0.01, f"回款额完成率不一致: 目标管理={goal_payment_rate}, 报表中心={report_payment_rate}"
    
    print(f"✅ 回款额跨接口数据一致")


def test_cross_interface_lead_count_consistency(crm_client, authorized_headers):
    """CROSS-CONSISTENCY-003 新增线索跨接口一致性验证（目标管理接口 vs 报表中心接口）"""
    crm_client.session.headers.update(authorized_headers)
    
    goal = get_current_user_goal(crm_client, authorized_headers)
    performance_data = get_performance_report(crm_client, authorized_headers)
    
    current_month = goal.get("targetMonth")
    user_id = goal.get("userId")
    user_name = goal.get("userName")
    
    performance = get_current_user_performance(performance_data, user_id)
    assert performance is not None, f"未找到用户 {user_id} 的绩效数据"
    
    lead_item = None
    for item in goal.get("items", []):
        if item.get("itemCode") == "leadCount":
            lead_item = item
            break
    
    assert lead_item is not None, "未找到新增线索目标项"
    
    goal_lead_target = float(lead_item.get("targetValue", 0) or 0)
    goal_lead_actual = float(lead_item.get("actualValue", 0) or 0)
    goal_lead_rate = float(lead_item.get("completionRate", 0) or 0)
    
    report_lead_target = float(performance.get("leadCountTarget", 0) or 0)
    report_lead_actual = float(performance.get("leadCountActual", 0) or 0)
    report_lead_rate = float(performance.get("leadCountRate", 0) or 0)
    
    print(f"\n=== 新增线索跨接口一致性验证 ({user_name} - {current_month}) ===")
    print(f"目标管理接口: 目标={goal_lead_target}条, 实际={goal_lead_actual}条, 完成率={goal_lead_rate}%")
    print(f"报表中心接口: 目标={report_lead_target}条, 实际={report_lead_actual}条, 完成率={report_lead_rate}%")
    
    assert abs(goal_lead_target - report_lead_target) < 0.01, f"新增线索目标不一致: 目标管理={goal_lead_target}, 报表中心={report_lead_target}"
    assert abs(goal_lead_actual - report_lead_actual) < 0.01, f"新增线索实际不一致: 目标管理={goal_lead_actual}, 报表中心={report_lead_actual}"
    assert abs(goal_lead_rate - report_lead_rate) < 0.01, f"新增线索完成率不一致: 目标管理={goal_lead_rate}, 报表中心={report_lead_rate}"
    
    print(f"✅ 新增线索跨接口数据一致")


def test_cross_interface_visit_count_consistency(crm_client, authorized_headers):
    """CROSS-CONSISTENCY-004 有效拜访跨接口一致性验证（目标管理接口 vs 报表中心接口）"""
    crm_client.session.headers.update(authorized_headers)
    
    goal = get_current_user_goal(crm_client, authorized_headers)
    performance_data = get_performance_report(crm_client, authorized_headers)
    
    current_month = goal.get("targetMonth")
    user_id = goal.get("userId")
    user_name = goal.get("userName")
    
    performance = get_current_user_performance(performance_data, user_id)
    assert performance is not None, f"未找到用户 {user_id} 的绩效数据"
    
    visit_item = None
    for item in goal.get("items", []):
        if item.get("itemCode") == "visitCount":
            visit_item = item
            break
    
    assert visit_item is not None, "未找到有效拜访目标项"
    
    goal_visit_target = float(visit_item.get("targetValue", 0) or 0)
    goal_visit_actual = float(visit_item.get("actualValue", 0) or 0)
    goal_visit_rate = float(visit_item.get("completionRate", 0) or 0)
    
    report_visit_target = float(performance.get("visitCountTarget", 0) or 0)
    report_visit_actual = float(performance.get("visitCountActual", 0) or 0)
    report_visit_rate = float(performance.get("visitCountRate", 0) or 0)
    
    print(f"\n=== 有效拜访跨接口一致性验证 ({user_name} - {current_month}) ===")
    print(f"目标管理接口: 目标={goal_visit_target}次, 实际={goal_visit_actual}次, 完成率={goal_visit_rate}%")
    print(f"报表中心接口: 目标={report_visit_target}次, 实际={report_visit_actual}次, 完成率={report_visit_rate}%")
    
    assert abs(goal_visit_target - report_visit_target) < 0.01, f"有效拜访目标不一致: 目标管理={goal_visit_target}, 报表中心={report_visit_target}"
    assert abs(goal_visit_actual - report_visit_actual) < 0.01, f"有效拜访实际不一致: 目标管理={goal_visit_actual}, 报表中心={report_visit_actual}"
    assert abs(goal_visit_rate - report_visit_rate) < 0.01, f"有效拜访完成率不一致: 目标管理={goal_visit_rate}, 报表中心={report_visit_rate}"
    
    print(f"✅ 有效拜访跨接口数据一致")


def test_cross_interface_overall_completion_consistency(crm_client, authorized_headers):
    """CROSS-CONSISTENCY-005 整体完成率跨接口一致性验证（目标管理接口 vs 报表中心接口）"""
    crm_client.session.headers.update(authorized_headers)
    
    goal = get_current_user_goal(crm_client, authorized_headers)
    performance_data = get_performance_report(crm_client, authorized_headers)
    
    current_month = goal.get("targetMonth")
    user_id = goal.get("userId")
    user_name = goal.get("userName")
    
    performance = get_current_user_performance(performance_data, user_id)
    assert performance is not None, f"未找到用户 {user_id} 的绩效数据"
    
    goal_overall_rate = float(goal.get("scoreTotal", 0) or 0)
    report_overall_rate = float(performance.get("overallCompletionRate", 0) or 0)
    
    print(f"\n=== 整体完成率跨接口一致性验证 ({user_name} - {current_month}) ===")
    print(f"目标管理接口: 总分={goal_overall_rate}")
    print(f"报表中心接口: 整体完成率={report_overall_rate}")
    
    assert abs(goal_overall_rate - report_overall_rate) < 0.01, f"整体完成率不一致: 目标管理={goal_overall_rate}, 报表中心={report_overall_rate}"
    
    print(f"✅ 整体完成率跨接口数据一致")


def test_cross_interface_summary_report(crm_client, authorized_headers):
    """CROSS-CONSISTENCY-006 跨接口一致性汇总报告"""
    crm_client.session.headers.update(authorized_headers)
    
    goal = get_current_user_goal(crm_client, authorized_headers)
    performance_data = get_performance_report(crm_client, authorized_headers)
    
    current_month = goal.get("targetMonth")
    user_id = goal.get("userId")
    user_name = goal.get("userName")
    
    performance = get_current_user_performance(performance_data, user_id)
    
    print(f"\n{'='*90}")
    print(f"          跨接口数据一致性汇总报告")
    print(f"          ({user_name} - {current_month})")
    print(f"{'='*90}")
    print(f"{'指标名称':<15} {'目标管理接口(目标)':<20} {'目标管理接口(实际)':<20} {'报表中心接口(目标)':<20} {'报表中心接口(实际)':<20} {'一致性':<10}")
    print(f"{'='*90}")
    
    item_mapping = {
        "signAmount": {"name": "签约额", "report_target": "signAmountTarget", "report_actual": "signAmountActual"},
        "paymentAmount": {"name": "回款额", "report_target": "paymentAmountTarget", "report_actual": "paymentAmountActual"},
        "leadCount": {"name": "新增线索", "report_target": "leadCountTarget", "report_actual": "leadCountActual"},
        "visitCount": {"name": "有效拜访", "report_target": "visitCountTarget", "report_actual": "visitCountActual"},
        "winRate": {"name": "赢单率", "report_target": None, "report_actual": None},
        "followUpCount": {"name": "跟进次数", "report_target": None, "report_actual": None},
        "newCustomerCount": {"name": "新增客户", "report_target": None, "report_actual": None}
    }
    
    all_consistent = True
    for item in goal.get("items", []):
        item_code = item.get("itemCode")
        item_info = item_mapping.get(item_code, {})
        item_name = item_info.get("name", item_code)
        
        goal_target = float(item.get("targetValue", 0) or 0)
        goal_actual = float(item.get("actualValue", 0) or 0)
        
        report_target = "N/A"
        report_actual = "N/A"
        consistent = "✅"
        
        if performance and item_info.get("report_target"):
            report_target = float(performance.get(item_info["report_target"], 0) or 0)
            report_actual = float(performance.get(item_info["report_actual"], 0) or 0)
            
            if abs(goal_target - report_target) >= 0.01 or abs(goal_actual - report_actual) >= 0.01:
                consistent = "⚠️"
                all_consistent = False
        else:
            consistent = "🔄"
        
        print(f"{item_name:<15} {str(goal_target):<20} {str(goal_actual):<20} {str(report_target):<20} {str(report_actual):<20} {consistent:<10}")
    
    print(f"{'='*90}")
    if performance:
        goal_overall = float(goal.get("scoreTotal", 0) or 0)
        report_overall = float(performance.get("overallCompletionRate", 0) or 0)
        overall_consistent = "✅" if abs(goal_overall - report_overall) < 0.01 else "⚠️"
        print(f"{'整体完成率':<15} {'-':<20} {str(goal_overall):<20} {'-':<20} {str(report_overall):<20} {overall_consistent:<10}")
    
    print(f"{'='*90}")
    if all_consistent:
        print(f"✅ 所有指标跨接口数据一致")
    else:
        print(f"⚠️ 部分指标跨接口数据不一致")
    print(f"{'='*90}")
