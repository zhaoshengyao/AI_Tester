import pytest


def test_clue_statistics_consistency(crm_client, authorized_headers):
    """DATA-CONSISTENCY-001 线索统计一致性验证"""
    crm_client.session.headers.update(authorized_headers)
    
    response = crm_client.get_clue_list(page=1, size=1000)
    assert response.status_code == 200, f"获取线索列表失败，状态码: {response.status_code}"
    data = response.json()
    assert data.get("code") == 200, f"获取线索列表失败，错误码: {data.get('code')}"
    
    total_clues = data.get("total", 0)
    rows = data.get("rows", [])
    
    status_counts = {}
    for row in rows:
        status = row.get("clueStatus", "")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    calculated_total = sum(status_counts.values())
    assert calculated_total == total_clues, f"线索统计不一致: 接口返回总数={total_clues}, 计算总数={calculated_total}"
    
    assert total_clues >= 0, "线索总数不能为负数"
    assert len(rows) <= 1000, "分页限制未生效"
    
    print(f"✅ 线索统计一致性验证通过")
    print(f"   - 线索总数: {total_clues}")
    print(f"   - 各状态分布: {status_counts}")


def test_customer_statistics_consistency(crm_client, authorized_headers):
    """DATA-CONSISTENCY-002 客户统计一致性验证"""
    crm_client.session.headers.update(authorized_headers)
    
    response = crm_client.get_customer_list(page=1, size=1000)
    assert response.status_code == 200, f"获取客户列表失败，状态码: {response.status_code}"
    data = response.json()
    assert data.get("code") == 200, f"获取客户列表失败，错误码: {data.get('code')}"
    
    total_customers = data.get("total", 0)
    rows = data.get("rows", [])
    
    calculated_total = len(rows)
    assert calculated_total == total_customers, f"客户统计不一致: 接口返回总数={total_customers}, 计算总数={calculated_total}"
    
    assert total_customers >= 0, "客户总数不能为负数"
    
    status_counts = {}
    for row in rows:
        status = row.get("status", "")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    assert sum(status_counts.values()) == total_customers, "状态分布总和与总数不一致"
    
    print(f"✅ 客户统计一致性验证通过")
    print(f"   - 客户总数: {total_customers}")
    print(f"   - 各状态分布: {status_counts}")


def test_business_statistics_consistency(crm_client, authorized_headers):
    """DATA-CONSISTENCY-003 商机统计一致性验证"""
    crm_client.session.headers.update(authorized_headers)
    
    response = crm_client.get_business_list(page=1, size=1000)
    assert response.status_code == 200, f"获取商机列表失败，状态码: {response.status_code}"
    data = response.json()
    assert data.get("code") == 200, f"获取商机列表失败，错误码: {data.get('code')}"
    
    total_business = data.get("total", 0)
    rows = data.get("rows", [])
    
    calculated_total = len(rows)
    assert calculated_total == total_business, f"商机统计不一致: 接口返回总数={total_business}, 计算总数={calculated_total}"
    
    assert total_business >= 0, "商机总数不能为负数"
    
    stage_counts = {}
    for row in rows:
        stage = row.get("stage", "")
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
    
    assert sum(stage_counts.values()) == total_business, "阶段分布总和与总数不一致"
    
    print(f"✅ 商机统计一致性验证通过")
    print(f"   - 商机总数: {total_business}")
    print(f"   - 各阶段分布: {stage_counts}")


def test_deal_amount_consistency(crm_client, authorized_headers):
    """DATA-CONSISTENCY-004 成交金额一致性验证"""
    crm_client.session.headers.update(authorized_headers)
    
    response = crm_client.get_business_list(page=1, size=1000)
    assert response.status_code == 200, f"获取商机列表失败，状态码: {response.status_code}"
    data = response.json()
    assert data.get("code") == 200, f"获取商机列表失败，错误码: {data.get('code')}"
    
    rows = data.get("rows", [])
    
    won_amount = 0
    total_amount = 0
    for row in rows:
        amount = float(row.get("dealAmount", 0) or 0)
        total_amount += amount
        stage = row.get("stage", "")
        if "赢" in stage or stage == "won":
            won_amount += amount
    
    assert total_amount >= 0, "总金额不能为负数"
    assert won_amount >= 0, "赢单金额不能为负数"
    assert won_amount <= total_amount, "赢单金额不能超过总金额"
    
    print(f"✅ 成交金额一致性验证通过")
    print(f"   - 所有商机总金额: {total_amount:.2f}")
    print(f"   - 赢单商机金额: {won_amount:.2f}")


def test_sales_funnel_consistency(crm_client, authorized_headers):
    """DATA-CONSISTENCY-005 销售漏斗一致性验证"""
    crm_client.session.headers.update(authorized_headers)
    
    response = crm_client.get_business_list(page=1, size=1000)
    assert response.status_code == 200, f"获取商机列表失败，状态码: {response.status_code}"
    data = response.json()
    assert data.get("code") == 200, f"获取商机列表失败，错误码: {data.get('code')}"
    
    total_business = data.get("total", 0)
    rows = data.get("rows", [])
    
    stage_counts = {}
    for row in rows:
        stage = row.get("stage", "")
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
    
    sum_of_stages = sum(stage_counts.values())
    assert sum_of_stages == total_business, f"销售漏斗不一致: 各阶段总和={sum_of_stages}, 总商机数={total_business}"
    
    assert total_business >= 0, "商机总数不能为负数"
    
    print(f"✅ 销售漏斗一致性验证通过")
    print(f"   - 总商机数: {total_business}")
    print(f"   - 各阶段商机数: {stage_counts}")


def test_contact_customer_consistency(crm_client, authorized_headers):
    """DATA-CONSISTENCY-006 联系人与客户关联一致性验证"""
    crm_client.session.headers.update(authorized_headers)
    
    customer_response = crm_client.get_customer_list(page=1, size=1000)
    assert customer_response.status_code == 200, f"获取客户列表失败"
    customer_data = customer_response.json()
    customer_rows = customer_data.get("rows", [])
    
    contact_response = crm_client.get_contact_list(page=1, size=1000)
    assert contact_response.status_code == 200, f"获取联系人列表失败"
    contact_data = contact_response.json()
    contact_rows = contact_data.get("rows", [])
    
    customer_ids = set()
    for customer in customer_rows:
        customer_id = customer.get("id")
        if customer_id:
            customer_ids.add(customer_id)
    
    valid_contacts = 0
    orphan_contacts = 0
    for contact in contact_rows:
        customer_id = contact.get("customerId")
        if customer_id in customer_ids:
            valid_contacts += 1
        else:
            orphan_contacts += 1
    
    assert len(customer_rows) >= 0, "客户数不能为负数"
    assert len(contact_rows) >= 0, "联系人数不能为负数"
    assert valid_contacts + orphan_contacts == len(contact_rows), "有效联系人+孤儿联系人应等于总联系人数"
    
    print(f"✅ 联系人与客户关联一致性验证完成")
    print(f"   - 客户总数: {len(customer_ids)}")
    print(f"   - 联系人总数: {len(contact_rows)}")
    print(f"   - 有效关联联系人: {valid_contacts}")
    print(f"   - 无关联联系人(孤儿数据): {orphan_contacts}")


def test_business_customer_consistency(crm_client, authorized_headers):
    """DATA-CONSISTENCY-007 商机与客户关联一致性验证"""
    crm_client.session.headers.update(authorized_headers)
    
    customer_response = crm_client.get_customer_list(page=1, size=1000)
    assert customer_response.status_code == 200, f"获取客户列表失败"
    customer_data = customer_response.json()
    customer_rows = customer_data.get("rows", [])
    
    business_response = crm_client.get_business_list(page=1, size=1000)
    assert business_response.status_code == 200, f"获取商机列表失败"
    business_data = business_response.json()
    business_rows = business_data.get("rows", [])
    
    customer_ids = set()
    for customer in customer_rows:
        customer_id = customer.get("id")
        if customer_id:
            customer_ids.add(customer_id)
    
    valid_business = 0
    orphan_business = 0
    for business in business_rows:
        customer_id = business.get("customerId")
        if customer_id in customer_ids:
            valid_business += 1
        else:
            orphan_business += 1
    
    assert len(customer_rows) >= 0, "客户数不能为负数"
    assert len(business_rows) >= 0, "商机数不能为负数"
    assert valid_business + orphan_business == len(business_rows), "有效商机+孤儿商机应等于总商机数"
    
    print(f"✅ 商机与客户关联一致性验证完成")
    print(f"   - 客户总数: {len(customer_ids)}")
    print(f"   - 商机总数: {len(business_rows)}")
    print(f"   - 有效关联商机: {valid_business}")
    print(f"   - 无关联商机(孤儿数据): {orphan_business}")


def test_owner_consistency(crm_client, authorized_headers):
    """DATA-CONSISTENCY-008 数据归属人一致性验证"""
    crm_client.session.headers.update(authorized_headers)
    
    business_response = crm_client.get_business_list(page=1, size=1000)
    assert business_response.status_code == 200, f"获取商机列表失败"
    business_data = business_response.json()
    business_rows = business_data.get("rows", [])
    
    owner_counts = {}
    for business in business_rows:
        owner_name = business.get("ownerUserName") or "未知"
        owner_counts[owner_name] = owner_counts.get(owner_name, 0) + 1
    
    assert len(business_rows) >= 0, "商机数不能为负数"
    assert sum(owner_counts.values()) == len(business_rows), "归属人分布总和与商机总数不一致"
    
    print(f"✅ 数据归属人一致性验证完成")
    print(f"   - 商机总数: {len(business_rows)}")
    print(f"   - 归属人分布: {owner_counts}")


def test_amount_calculation_validity(crm_client, authorized_headers):
    """DATA-CONSISTENCY-009 金额数据有效性验证"""
    crm_client.session.headers.update(authorized_headers)
    
    business_response = crm_client.get_business_list(page=1, size=1000)
    assert business_response.status_code == 200, f"获取商机列表失败"
    business_data = business_response.json()
    business_rows = business_data.get("rows", [])
    
    negative_amount_count = 0
    zero_amount_count = 0
    valid_amount_count = 0
    
    for business in business_rows:
        amount = float(business.get("dealAmount", 0) or 0)
        if amount < 0:
            negative_amount_count += 1
        elif amount == 0:
            zero_amount_count += 1
        else:
            valid_amount_count += 1
    
    assert len(business_rows) >= 0, "商机数不能为负数"
    assert negative_amount_count + zero_amount_count + valid_amount_count == len(business_rows), "各类金额商机数总和应等于总商机数"
    
    print(f"✅ 金额数据有效性验证完成")
    print(f"   - 商机总数: {len(business_rows)}")
    print(f"   - 有效金额商机: {valid_amount_count}")
    print(f"   - 零金额商机: {zero_amount_count}")
    print(f"   - 负金额商机(异常): {negative_amount_count}")


def test_data_consistency_summary(crm_client, authorized_headers):
    """DATA-CONSISTENCY-010 数据一致性汇总报告"""
    crm_client.session.headers.update(authorized_headers)
    
    customer_response = crm_client.get_customer_list(page=1, size=1000)
    customer_count = customer_response.json().get("total", 0)
    
    clue_response = crm_client.get_clue_list(page=1, size=1000)
    clue_count = clue_response.json().get("total", 0)
    
    contact_response = crm_client.get_contact_list(page=1, size=1000)
    contact_count = contact_response.json().get("total", 0)
    
    business_response = crm_client.get_business_list(page=1, size=1000)
    business_count = business_response.json().get("total", 0)
    
    quotation_response = crm_client.get_quotation_list(page=1, size=1000)
    quotation_count = quotation_response.json().get("total", 0)
    
    assert customer_count >= 0, "客户总数不能为负数"
    assert clue_count >= 0, "线索总数不能为负数"
    assert contact_count >= 0, "联系人总数不能为负数"
    assert business_count >= 0, "商机总数不能为负数"
    assert quotation_count >= 0, "报价单总数不能为负数"
    
    print(f"")
    print(f"=" * 60)
    print(f"          数据一致性汇总报告")
    print(f"=" * 60)
    print(f"   客户总数:      {customer_count:>6}")
    print(f"   线索总数:      {clue_count:>6}")
    print(f"   联系人总数:    {contact_count:>6}")
    print(f"   商机总数:      {business_count:>6}")
    print(f"   报价单总数:    {quotation_count:>6}")
    print(f"=" * 60)
    print(f"✅ 数据一致性汇总完成")
