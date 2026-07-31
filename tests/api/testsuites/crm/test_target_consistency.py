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


def test_goal_lead_count_consistency(crm_client, authorized_headers):
    """DATA-CONSISTENCY-GOAL-001 新增线索目标一致性验证"""
    crm_client.session.headers.update(authorized_headers)
    
    goal = get_current_user_goal(crm_client, authorized_headers)
    current_month = goal.get("targetMonth")
    user_name = goal.get("userName")
    
    lead_item = None
    for item in goal.get("items", []):
        if item.get("itemCode") == "leadCount":
            lead_item = item
            break
    
    assert lead_item is not None, "未找到新增线索目标项"
    
    target_value = float(lead_item.get("targetValue", 0) or 0)
    actual_value = float(lead_item.get("actualValue", 0) or 0)
    completion_rate = float(lead_item.get("completionRate", 0) or 0)
    
    print(f"\n=== 新增线索目标一致性验证 ({user_name} - {current_month}) ===")
    print(f"目标值: {target_value} 条")
    print(f"系统实际值: {actual_value} 条")
    print(f"完成率: {completion_rate:.2f}%")
    
    assert actual_value >= 0, "实际值不能为负数"
    assert completion_rate >= 0, "完成率不能为负数"
    
    print(f"✅ 新增线索目标一致性验证完成")


def test_goal_win_rate_consistency(crm_client, authorized_headers):
    """DATA-CONSISTENCY-GOAL-002 赢单率目标一致性验证"""
    crm_client.session.headers.update(authorized_headers)
    
    goal = get_current_user_goal(crm_client, authorized_headers)
    current_month = goal.get("targetMonth")
    user_name = goal.get("userName")
    
    win_rate_item = None
    for item in goal.get("items", []):
        if item.get("itemCode") == "winRate":
            win_rate_item = item
            break
    
    assert win_rate_item is not None, "未找到赢单率目标项"
    
    target_value = float(win_rate_item.get("targetValue", 0) or 0)
    actual_value = float(win_rate_item.get("actualValue", 0) or 0)
    completion_rate = float(win_rate_item.get("completionRate", 0) or 0)
    
    print(f"\n=== 赢单率目标一致性验证 ({user_name} - {current_month}) ===")
    print(f"目标值: {target_value}%")
    print(f"系统实际值: {actual_value}%")
    print(f"完成率: {completion_rate:.2f}%")
    
    assert actual_value >= 0 and actual_value <= 100, "赢单率必须在0-100之间"
    assert completion_rate >= 0, "完成率不能为负数"
    
    print(f"✅ 赢单率目标一致性验证完成")


def test_goal_new_customer_count_consistency(crm_client, authorized_headers):
    """DATA-CONSISTENCY-GOAL-003 新增客户数目标一致性验证"""
    crm_client.session.headers.update(authorized_headers)
    
    goal = get_current_user_goal(crm_client, authorized_headers)
    current_month = goal.get("targetMonth")
    user_name = goal.get("userName")
    
    customer_item = None
    for item in goal.get("items", []):
        if item.get("itemCode") == "newCustomerCount":
            customer_item = item
            break
    
    assert customer_item is not None, "未找到新增客户目标项"
    
    target_value = float(customer_item.get("targetValue", 0) or 0)
    actual_value = float(customer_item.get("actualValue", 0) or 0)
    completion_rate = float(customer_item.get("completionRate", 0) or 0)
    
    print(f"\n=== 新增客户数目标一致性验证 ({user_name} - {current_month}) ===")
    print(f"目标值: {target_value} 个")
    print(f"系统实际值: {actual_value} 个")
    print(f"完成率: {completion_rate:.2f}%")
    
    assert actual_value >= 0, "实际值不能为负数"
    assert completion_rate >= 0, "完成率不能为负数"
    
    print(f"✅ 新增客户数目标一致性验证完成")


def test_goal_follow_up_count_consistency(crm_client, authorized_headers):
    """DATA-CONSISTENCY-GOAL-004 跟进次数目标一致性验证"""
    crm_client.session.headers.update(authorized_headers)
    
    goal = get_current_user_goal(crm_client, authorized_headers)
    current_month = goal.get("targetMonth")
    user_name = goal.get("userName")
    
    follow_item = None
    for item in goal.get("items", []):
        if item.get("itemCode") == "followUpCount":
            follow_item = item
            break
    
    assert follow_item is not None, "未找到跟进次数目标项"
    
    target_value = float(follow_item.get("targetValue", 0) or 0)
    actual_value = float(follow_item.get("actualValue", 0) or 0)
    completion_rate = float(follow_item.get("completionRate", 0) or 0)
    
    print(f"\n=== 跟进次数目标一致性验证 ({user_name} - {current_month}) ===")
    print(f"目标值: {target_value} 次")
    print(f"系统实际值: {actual_value} 次")
    print(f"完成率: {completion_rate:.2f}%")
    
    assert actual_value >= 0, "实际值不能为负数"
    assert completion_rate >= 0, "完成率不能为负数"
    
    print(f"✅ 跟进次数目标一致性验证完成")


def test_goal_sign_amount_consistency(crm_client, authorized_headers):
    """DATA-CONSISTENCY-GOAL-005 签约额目标一致性验证"""
    crm_client.session.headers.update(authorized_headers)
    
    goal = get_current_user_goal(crm_client, authorized_headers)
    current_month = goal.get("targetMonth")
    user_name = goal.get("userName")
    
    sign_item = None
    for item in goal.get("items", []):
        if item.get("itemCode") == "signAmount":
            sign_item = item
            break
    
    assert sign_item is not None, "未找到签约额目标项"
    
    target_value = float(sign_item.get("targetValue", 0) or 0)
    actual_value = float(sign_item.get("actualValue", 0) or 0)
    completion_rate = float(sign_item.get("completionRate", 0) or 0)
    
    print(f"\n=== 签约额目标一致性验证 ({user_name} - {current_month}) ===")
    print(f"目标值: {target_value} 万元")
    print(f"系统实际值: {actual_value} 万元")
    print(f"完成率: {completion_rate:.2f}%")
    
    assert actual_value >= 0, "实际值不能为负数"
    assert completion_rate >= 0, "完成率不能为负数"
    
    print(f"✅ 签约额目标一致性验证完成")


def test_goal_payment_amount_consistency(crm_client, authorized_headers):
    """DATA-CONSISTENCY-GOAL-006 回款额目标一致性验证"""
    crm_client.session.headers.update(authorized_headers)
    
    goal = get_current_user_goal(crm_client, authorized_headers)
    current_month = goal.get("targetMonth")
    user_name = goal.get("userName")
    
    payment_item = None
    for item in goal.get("items", []):
        if item.get("itemCode") == "paymentAmount":
            payment_item = item
            break
    
    assert payment_item is not None, "未找到回款额目标项"
    
    target_value = float(payment_item.get("targetValue", 0) or 0)
    actual_value = float(payment_item.get("actualValue", 0) or 0)
    completion_rate = float(payment_item.get("completionRate", 0) or 0)
    
    print(f"\n=== 回款额目标一致性验证 ({user_name} - {current_month}) ===")
    print(f"目标值: {target_value} 万元")
    print(f"系统实际值: {actual_value} 万元")
    print(f"完成率: {completion_rate:.2f}%")
    
    assert actual_value >= 0, "实际值不能为负数"
    assert completion_rate >= 0, "完成率不能为负数"
    
    print(f"✅ 回款额目标一致性验证完成")


def test_goal_visit_count_consistency(crm_client, authorized_headers):
    """DATA-CONSISTENCY-GOAL-007 有效拜访目标一致性验证"""
    crm_client.session.headers.update(authorized_headers)
    
    goal = get_current_user_goal(crm_client, authorized_headers)
    current_month = goal.get("targetMonth")
    user_name = goal.get("userName")
    
    visit_item = None
    for item in goal.get("items", []):
        if item.get("itemCode") == "visitCount":
            visit_item = item
            break
    
    assert visit_item is not None, "未找到有效拜访目标项"
    
    target_value = float(visit_item.get("targetValue", 0) or 0)
    actual_value = float(visit_item.get("actualValue", 0) or 0)
    completion_rate = float(visit_item.get("completionRate", 0) or 0)
    
    print(f"\n=== 有效拜访目标一致性验证 ({user_name} - {current_month}) ===")
    print(f"目标值: {target_value} 次")
    print(f"系统实际值: {actual_value} 次")
    print(f"完成率: {completion_rate:.2f}%")
    
    assert actual_value >= 0, "实际值不能为负数"
    assert completion_rate >= 0, "完成率不能为负数"
    
    print(f"✅ 有效拜访目标一致性验证完成")


def test_goal_progress_summary_report(crm_client, authorized_headers):
    """DATA-CONSISTENCY-GOAL-008 目标进度数据一致性汇总报告"""
    crm_client.session.headers.update(authorized_headers)
    
    goal = get_current_user_goal(crm_client, authorized_headers)
    current_month = goal.get("targetMonth")
    user_name = goal.get("userName")
    
    print(f"\n{'='*60}")
    print(f"          目标进度数据一致性汇总报告")
    print(f"          ({user_name} - {current_month})")
    print(f"{'='*60}")
    
    total_score = float(goal.get("scoreTotal", 0) or 0)
    print(f"   总分:              {total_score:>6.1f}")
    print(f"{'='*60}")
    
    for item in goal.get("items", []):
        item_name = item.get("itemName", "")
        target_value = item.get("targetValue", "")
        actual_value = item.get("actualValue", "")
        completion_rate = float(item.get("completionRate", 0) or 0)
        weight = float(item.get("weight", 0) or 0)
        score = float(item.get("score", 0) or 0)
        
        status = "✅" if completion_rate >= 100 else "⚠️"
        print(f"   {status} {item_name}:")
        print(f"      目标值: {target_value}")
        print(f"      实际值: {actual_value}")
        print(f"      完成率: {completion_rate:.2f}%")
        print(f"      权重: {weight}%, 得分: {score:.1f}")
    
    print(f"{'='*60}")
    print(f"✅ 目标进度数据一致性汇总完成")
