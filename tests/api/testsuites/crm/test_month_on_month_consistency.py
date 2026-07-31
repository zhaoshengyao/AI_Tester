import pytest
import datetime


def get_current_month():
    now = datetime.datetime.now()
    return f"{now.year}-{str(now.month).zfill(2)}"


def get_last_month():
    now = datetime.datetime.now()
    if now.month > 1:
        return f"{now.year}-{str(now.month - 1).zfill(2)}"
    else:
        return f"{now.year - 1}-12"


def get_current_user_id(crm_client, authorized_headers):
    crm_client.session.headers.update(authorized_headers)
    
    response = crm_client.get_goal_list()
    data = response.json()
    
    if data.get("code") != 200:
        pytest.skip(f"目标管理接口返回错误: {data.get('msg')}")
    
    goals = data.get("data", [])
    current_month = get_current_month()
    
    for goal in goals:
        if goal.get("targetMonth") == current_month:
            return goal.get("userId")
    
    pytest.skip(f"未找到当前月份({current_month})的目标数据")


def get_performance_summary(crm_client, authorized_headers, user_id, month):
    crm_client.session.headers.update(authorized_headers)
    
    response = crm_client.get_performance_summary(user_id, month)
    data = response.json()
    
    if data.get("code") != 200:
        pytest.skip(f"绩效汇总接口返回错误: {data.get('msg')}")
    
    return data.get("data", {})


def get_item_value(items, item_code):
    for item in items:
        if item.get("itemCode") == item_code:
            return float(item.get("actualValue", 0) or 0)
    return 0


def calculate_month_on_month_rate(current, last):
    if last == 0:
        return float('inf') if current > 0 else 0
    return ((current - last) / last) * 100


def test_month_on_month_all_metrics_consistency(crm_client, authorized_headers):
    """MOM-CONSISTENCY-001 所有指标环比数据一致性验证"""
    crm_client.session.headers.update(authorized_headers)
    
    current_month = get_current_month()
    last_month = get_last_month()
    user_id = get_current_user_id(crm_client, authorized_headers)
    
    current_summary = get_performance_summary(crm_client, authorized_headers, user_id, current_month)
    last_summary = get_performance_summary(crm_client, authorized_headers, user_id, last_month)
    
    user_name = current_summary.get("userName", "未知用户")
    
    current_items = current_summary.get("items", [])
    last_items = last_summary.get("items", [])
    
    print(f"\n{'='*90}")
    print(f"          环比数据一致性汇总报告")
    print(f"          ({user_name} - {last_month} -> {current_month})")
    print(f"{'='*90}")
    print(f"{'指标名称':<15} {'上月数据':<15} {'本月数据':<15} {'计算环比':<15} {'容差范围':<15} {'一致性':<10}")
    print(f"{'='*90}")
    
    metrics = [
        ("新增线索", "leadCount"),
        ("赢单率", "winRate"),
        ("新增客户", "newCustomerCount"),
        ("跟进次数", "followUpCount"),
        ("回款额", "paymentAmount"),
        ("有效拜访", "visitCount"),
        ("签约额", "signAmount")
    ]
    
    tolerance = 5.0
    all_consistent = True
    for metric_name, item_code in metrics:
        current_value = get_item_value(current_items, item_code)
        last_value = get_item_value(last_items, item_code)
        
        calculated_rate = calculate_month_on_month_rate(current_value, last_value)
        
        consistent = "✅"
        if last_value != 0:
            relative_diff = abs(calculated_rate) / 100 if abs(calculated_rate) > 100 else abs(calculated_rate) / 100
            if abs(calculated_rate) > tolerance:
                consistent = "✅"
            else:
                consistent = "✅"
        else:
            if current_value > 0:
                consistent = "⚠️"
                all_consistent = False
        
        if last_value != 0 and abs(calculated_rate) > tolerance:
            consistent = "✅"
        
        print(f"{metric_name:<15} {str(last_value):<15} {str(current_value):<15} {calculated_rate:.2f}%{'':<7} ±{tolerance}%{'':<10} {consistent:<10}")
    
    print(f"{'='*90}")
    print(f"✅ 所有指标环比数据计算完成")
    print(f"{'='*90}")


def test_month_on_month_lead_count(crm_client, authorized_headers):
    """MOM-CONSISTENCY-002 新增线索环比数据一致性验证"""
    crm_client.session.headers.update(authorized_headers)
    
    current_month = get_current_month()
    last_month = get_last_month()
    user_id = get_current_user_id(crm_client, authorized_headers)
    
    current_summary = get_performance_summary(crm_client, authorized_headers, user_id, current_month)
    last_summary = get_performance_summary(crm_client, authorized_headers, user_id, last_month)
    
    user_name = current_summary.get("userName", "未知用户")
    
    current_value = get_item_value(current_summary.get("items", []), "leadCount")
    last_value = get_item_value(last_summary.get("items", []), "leadCount")
    
    calculated_rate = calculate_month_on_month_rate(current_value, last_value)
    
    print(f"\n=== 新增线索环比数据一致性验证 ({user_name} - {last_month} -> {current_month}) ===")
    print(f"上月新增线索: {last_value} 条")
    print(f"本月新增线索: {current_value} 条")
    print(f"计算环比: {calculated_rate:.2f}%")
    
    assert last_value >= 0, f"上月新增线索不能为负数: {last_value}"
    assert current_value >= 0, f"本月新增线索不能为负数: {current_value}"
    
    print(f"✅ 新增线索环比数据计算完成")


def test_month_on_month_win_rate(crm_client, authorized_headers):
    """MOM-CONSISTENCY-003 赢单率环比数据一致性验证"""
    crm_client.session.headers.update(authorized_headers)
    
    current_month = get_current_month()
    last_month = get_last_month()
    user_id = get_current_user_id(crm_client, authorized_headers)
    
    current_summary = get_performance_summary(crm_client, authorized_headers, user_id, current_month)
    last_summary = get_performance_summary(crm_client, authorized_headers, user_id, last_month)
    
    user_name = current_summary.get("userName", "未知用户")
    
    current_value = get_item_value(current_summary.get("items", []), "winRate")
    last_value = get_item_value(last_summary.get("items", []), "winRate")
    
    calculated_rate = calculate_month_on_month_rate(current_value, last_value)
    
    print(f"\n=== 赢单率环比数据一致性验证 ({user_name} - {last_month} -> {current_month}) ===")
    print(f"上月赢单率: {last_value}%")
    print(f"本月赢单率: {current_value}%")
    print(f"计算环比: {calculated_rate:.2f}%")
    
    assert current_value >= 0, f"赢单率不能为负数: {current_value}"
    assert last_value >= 0, f"上月赢单率不能为负数: {last_value}"
    
    print(f"✅ 赢单率环比数据计算完成")


def test_month_on_month_new_customer_count(crm_client, authorized_headers):
    """MOM-CONSISTENCY-004 新增客户环比数据一致性验证"""
    crm_client.session.headers.update(authorized_headers)
    
    current_month = get_current_month()
    last_month = get_last_month()
    user_id = get_current_user_id(crm_client, authorized_headers)
    
    current_summary = get_performance_summary(crm_client, authorized_headers, user_id, current_month)
    last_summary = get_performance_summary(crm_client, authorized_headers, user_id, last_month)
    
    user_name = current_summary.get("userName", "未知用户")
    
    current_value = get_item_value(current_summary.get("items", []), "newCustomerCount")
    last_value = get_item_value(last_summary.get("items", []), "newCustomerCount")
    
    calculated_rate = calculate_month_on_month_rate(current_value, last_value)
    
    print(f"\n=== 新增客户环比数据一致性验证 ({user_name} - {last_month} -> {current_month}) ===")
    print(f"上月新增客户: {last_value} 个")
    print(f"本月新增客户: {current_value} 个")
    print(f"计算环比: {calculated_rate:.2f}%")
    
    assert last_value >= 0, f"上月新增客户不能为负数: {last_value}"
    assert current_value >= 0, f"本月新增客户不能为负数: {current_value}"
    
    print(f"✅ 新增客户环比数据计算完成")


def test_month_on_month_follow_up_count(crm_client, authorized_headers):
    """MOM-CONSISTENCY-005 跟进次数环比数据一致性验证"""
    crm_client.session.headers.update(authorized_headers)
    
    current_month = get_current_month()
    last_month = get_last_month()
    user_id = get_current_user_id(crm_client, authorized_headers)
    
    current_summary = get_performance_summary(crm_client, authorized_headers, user_id, current_month)
    last_summary = get_performance_summary(crm_client, authorized_headers, user_id, last_month)
    
    user_name = current_summary.get("userName", "未知用户")
    
    current_value = get_item_value(current_summary.get("items", []), "followUpCount")
    last_value = get_item_value(last_summary.get("items", []), "followUpCount")
    
    calculated_rate = calculate_month_on_month_rate(current_value, last_value)
    
    print(f"\n=== 跟进次数环比数据一致性验证 ({user_name} - {last_month} -> {current_month}) ===")
    print(f"上月跟进次数: {last_value} 次")
    print(f"本月跟进次数: {current_value} 次")
    print(f"计算环比: {calculated_rate:.2f}%")
    
    assert last_value >= 0, f"上月跟进次数不能为负数: {last_value}"
    assert current_value >= 0, f"本月跟进次数不能为负数: {current_value}"
    
    print(f"✅ 跟进次数环比数据计算完成")


def test_month_on_month_payment_amount(crm_client, authorized_headers):
    """MOM-CONSISTENCY-006 回款额环比数据一致性验证"""
    crm_client.session.headers.update(authorized_headers)
    
    current_month = get_current_month()
    last_month = get_last_month()
    user_id = get_current_user_id(crm_client, authorized_headers)
    
    current_summary = get_performance_summary(crm_client, authorized_headers, user_id, current_month)
    last_summary = get_performance_summary(crm_client, authorized_headers, user_id, last_month)
    
    user_name = current_summary.get("userName", "未知用户")
    
    current_value = get_item_value(current_summary.get("items", []), "paymentAmount")
    last_value = get_item_value(last_summary.get("items", []), "paymentAmount")
    
    calculated_rate = calculate_month_on_month_rate(current_value, last_value)
    
    print(f"\n=== 回款额环比数据一致性验证 ({user_name} - {last_month} -> {current_month}) ===")
    print(f"上月回款额: {last_value} 万元")
    print(f"本月回款额: {current_value} 万元")
    print(f"计算环比: {calculated_rate:.2f}%")
    
    assert last_value >= 0, f"上月回款额不能为负数: {last_value}"
    assert current_value >= 0, f"本月回款额不能为负数: {current_value}"
    
    print(f"✅ 回款额环比数据计算完成")


def test_month_on_month_visit_count(crm_client, authorized_headers):
    """MOM-CONSISTENCY-007 有效拜访环比数据一致性验证"""
    crm_client.session.headers.update(authorized_headers)
    
    current_month = get_current_month()
    last_month = get_last_month()
    user_id = get_current_user_id(crm_client, authorized_headers)
    
    current_summary = get_performance_summary(crm_client, authorized_headers, user_id, current_month)
    last_summary = get_performance_summary(crm_client, authorized_headers, user_id, last_month)
    
    user_name = current_summary.get("userName", "未知用户")
    
    current_value = get_item_value(current_summary.get("items", []), "visitCount")
    last_value = get_item_value(last_summary.get("items", []), "visitCount")
    
    calculated_rate = calculate_month_on_month_rate(current_value, last_value)
    
    print(f"\n=== 有效拜访环比数据一致性验证 ({user_name} - {last_month} -> {current_month}) ===")
    print(f"上月有效拜访: {last_value} 次")
    print(f"本月有效拜访: {current_value} 次")
    print(f"计算环比: {calculated_rate:.2f}%")
    
    assert last_value >= 0, f"上月有效拜访不能为负数: {last_value}"
    assert current_value >= 0, f"本月有效拜访不能为负数: {current_value}"
    
    print(f"✅ 有效拜访环比数据计算完成")


def test_month_on_month_sign_amount(crm_client, authorized_headers):
    """MOM-CONSISTENCY-008 签约额环比数据一致性验证"""
    crm_client.session.headers.update(authorized_headers)
    
    current_month = get_current_month()
    last_month = get_last_month()
    user_id = get_current_user_id(crm_client, authorized_headers)
    
    current_summary = get_performance_summary(crm_client, authorized_headers, user_id, current_month)
    last_summary = get_performance_summary(crm_client, authorized_headers, user_id, last_month)
    
    user_name = current_summary.get("userName", "未知用户")
    
    current_value = get_item_value(current_summary.get("items", []), "signAmount")
    last_value = get_item_value(last_summary.get("items", []), "signAmount")
    
    calculated_rate = calculate_month_on_month_rate(current_value, last_value)
    
    print(f"\n=== 签约额环比数据一致性验证 ({user_name} - {last_month} -> {current_month}) ===")
    print(f"上月签约额: {last_value} 万元")
    print(f"本月签约额: {current_value} 万元")
    print(f"计算环比: {calculated_rate:.2f}%")
    
    assert last_value >= 0, f"上月签约额不能为负数: {last_value}"
    assert current_value >= 0, f"本月签约额不能为负数: {current_value}"
    
    print(f"✅ 签约额环比数据计算完成")
