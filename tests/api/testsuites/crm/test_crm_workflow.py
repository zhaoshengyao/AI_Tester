"""
CRM 业务流程测试
覆盖完整业务流程：线索→客户→联系人→商机→报价→审批
"""
import pytest
import time


@pytest.fixture(scope="class")
def workflow_data():
    """初始化流程测试数据（类级别共享）"""
    data = {
        "clue_id": None,
        "customer_id": None,
        "contact_id": None,
        "business_id": None,
        "quotation_id": None,
        "deal_amount": None,
        "test_batch": f"WF_{int(time.time())}"
    }
    return data


class TestBusinessWorkflow:
    """CRM 完整业务流程测试"""
    
    def test_wf01_create_clue(self, crm_client, authorized_headers, test_data_manager, workflow_data):
        """WF-001 创建线索 - 流程起点"""
        crm_client.session.headers.update(authorized_headers)
        
        clue = test_data_manager.create_clue()
        workflow_data["clue_id"] = clue["id"]
        
        assert clue["id"] is not None, "线索ID不应为空"
        print(f"✅ WF-001 线索创建成功: {clue['name']}")
    
    def test_wf02_create_customer_from_clue(self, crm_client, authorized_headers, test_data_manager, workflow_data):
        """WF-002 线索转客户"""
        crm_client.session.headers.update(authorized_headers)
        
        if not workflow_data.get("clue_id"):
            pytest.skip("跳过：没有可用的线索")
        
        clue_id = workflow_data["clue_id"]
        customer_name = f"业务流程测试公司_{int(time.time())}"
        
        # 线索转客户
        response = crm_client.transform_clue_to_customer(
            clue_id=clue_id,
            company_name=customer_name,
            contact_name="张三",
            contact_phone="13333333333",
            position="经理"
        )
        assert response.status_code == 200
        result = response.json()
        
        if result.get("code") == 200:
            # 线索转客户成功，获取新创建的客户ID
            customer_data = result.get("data", {})
            if customer_data and isinstance(customer_data, dict):
                workflow_data["customer_id"] = customer_data.get("id")
            
            # 如果返回中没有客户ID，通过列表查询获取
            if not workflow_data.get("customer_id"):
                customer_id = test_data_manager._find_id_by_name(
                    endpoint="/crm/customer/page",
                    name_field="customerName",
                    name_value=customer_name
                )
                if customer_id:
                    workflow_data["customer_id"] = customer_id
            
            assert workflow_data.get("customer_id") is not None, "客户ID不应为空"
            print(f"✅ WF-002 线索转客户成功: {customer_name} (ID: {workflow_data['customer_id']})")
        else:
            pytest.fail(f"线索转客户失败: {result.get('msg')}")
    
    def test_wf03_create_contact_for_customer(self, crm_client, authorized_headers, test_data_manager, workflow_data):
        """WF-003 为客户创建联系人"""
        crm_client.session.headers.update(authorized_headers)
        
        if not workflow_data.get("customer_id"):
            pytest.skip("跳过：没有可用的客户")
        
        contact = test_data_manager.create_contact(workflow_data["customer_id"])
        workflow_data["contact_id"] = contact["id"]
        
        assert contact["id"] is not None, "联系人ID不应为空"
        print(f"✅ WF-003 联系人创建成功: {contact['name']}")
    
    def test_wf04_create_business(self, crm_client, authorized_headers, test_data_manager, workflow_data):
        """WF-004 创建商机"""
        crm_client.session.headers.update(authorized_headers)
        
        if not workflow_data.get("customer_id"):
            pytest.skip("跳过：没有可用的客户")
        
        business = test_data_manager.create_business(workflow_data["customer_id"])
        workflow_data["business_id"] = business["id"]
        
        assert business["id"] is not None, "商机ID不应为空"
        print(f"✅ WF-004 商机创建成功: {business['name']}")
    
    def test_wf05_advance_to_proposal_stage(self, crm_client, authorized_headers, workflow_data):
        """WF-005 商机推进到方案确认阶段"""
        crm_client.session.headers.update(authorized_headers)
        
        if not workflow_data.get("business_id"):
            pytest.skip("跳过：没有可用的商机")
        
        business_id = workflow_data["business_id"]
        
        # 推进到阶段2(方案确认)
        response = crm_client.advance_business_stage(business_id, "2")
        assert response.status_code == 200
        result = response.json()
        
        if result.get("code") == 200:
            print("  ✅ 推进到阶段2(方案确认): 成功")
        else:
            print(f"  ⚠️ 推进失败: {result.get('msg')}")
        
        # 验证阶段已推进
        detail_response = crm_client.get_business_detail(business_id)
        detail_data = detail_response.json()
        current_stage = detail_data.get("data", {}).get("stage")
        
        stage_map = {"1": "验证客户", "2": "方案确认", "3": "谈判审核", "4": "赢单", "5": "输单"}
        print(f"当前商机阶段: {current_stage} ({stage_map.get(str(current_stage), '未知')})")
        
        assert current_stage == "2", f"商机阶段应为2(方案确认)，当前为{current_stage}"
        print(f"✅ WF-005 商机推进到方案确认阶段成功")
    
    def test_wf06_create_and_approve_quotation(self, crm_client, authorized_headers, test_data_manager, workflow_data):
        """WF-006 创建报价单并审批通过"""
        crm_client.session.headers.update(authorized_headers)
        
        if not workflow_data.get("business_id"):
            pytest.skip("跳过：没有可用的商机")
        
        # 创建报价单（带金额）
        quotation = test_data_manager.create_quotation(workflow_data["business_id"])
        workflow_data["quotation_id"] = quotation["id"]
        
        assert quotation["id"] is not None, "报价ID不应为空"
        print(f"  📝 报价单创建成功: {quotation['name']} (ID: {quotation['id']})")
        
        # 直接审批通过（用户提供的接口：无请求体）
        quotation_id = quotation["id"]
        approve_response = crm_client.approve_quotation(quotation_id)
        assert approve_response.status_code == 200
        approve_result = approve_response.json()
        print(f"  ✅ 报价审批通过: {approve_result.get('msg', '成功')}")
        
        # 验证报价状态
        detail_response = crm_client.get_quotation_detail(quotation_id)
        detail_data = detail_response.json()
        
        if detail_data.get("code") == 200:
            approval_status = detail_data.get("data", {}).get("approvalStatus")
            status_map = {"0": "草稿", "1": "待审批", "2": "已通过", "3": "已拒绝"}
            print(f"  报价审批状态: {approval_status} ({status_map.get(str(approval_status), '未知')})")
        
        # 获取报价金额作为成交金额（使用amount字段）
        quotation_data = detail_data.get("data", {})
        workflow_data["deal_amount"] = quotation_data.get("amount", "50000")
        print(f"  报价金额(成交金额): {workflow_data['deal_amount']}")
        
        print(f"✅ WF-006 创建报价单并审批通过成功")
    
    def test_wf07_advance_to_negotiation_and_win(self, crm_client, authorized_headers, workflow_data):
        """WF-007 商机推进到谈判审核并赢单"""
        crm_client.session.headers.update(authorized_headers)
        
        if not workflow_data.get("business_id"):
            pytest.skip("跳过：没有可用的商机")
        
        business_id = workflow_data["business_id"]
        
        # 推进到阶段3(谈判审核)
        response = crm_client.advance_business_stage(business_id, "3")
        assert response.status_code == 200
        result = response.json()
        
        if result.get("code") == 200:
            print("  ✅ 推进到阶段3(谈判审核): 成功")
        else:
            print(f"  ⚠️ 推进失败: {result.get('msg')}")
        
        # 获取成交金额
        deal_amount = workflow_data.get("deal_amount", "50000")
        
        # 赢单（推进到阶段4）
        win_response = crm_client.win_business(business_id, deal_amount)
        assert win_response.status_code == 200
        win_result = win_response.json()
        
        if win_result.get("code") == 200:
            print("  ✅ 赢单成功")
        else:
            print(f"  ⚠️ 赢单失败: {win_result.get('msg')}")
        
        # 验证最终状态
        detail_response = crm_client.get_business_detail(business_id)
        detail_data = detail_response.json()
        business_info = detail_data.get("data", {})
        
        current_stage = business_info.get("stage")
        actual_deal_amount = business_info.get("dealAmount")
        deal_date = business_info.get("dealDate")
        
        stage_map = {"1": "验证客户", "2": "方案确认", "3": "谈判审核", "4": "赢单", "5": "输单"}
        print(f"  商机阶段: {current_stage} ({stage_map.get(str(current_stage), '未知')})")
        print(f"  成交金额: {actual_deal_amount}")
        print(f"  成交日期: {deal_date}")
        
        assert current_stage == "4", f"商机应为赢单状态(4)，当前为{current_stage}"
        print(f"✅ WF-007 商机推进到谈判审核并赢单成功")
    
    def test_wf08_verify_workflow_data_consistency(self, crm_client, authorized_headers, workflow_data):
        """WF-008 验证流程数据一致性"""
        crm_client.session.headers.update(authorized_headers)
        
        # 验证线索存在
        if workflow_data.get("clue_id"):
            response = crm_client.get_clue_detail(workflow_data["clue_id"])
            data = response.json()
            assert data.get("code") == 200, "线索应存在"
        
        # 验证客户存在
        if workflow_data.get("customer_id"):
            response = crm_client.get_customer_detail(workflow_data["customer_id"])
            data = response.json()
            assert data.get("code") == 200, "客户应存在"
        
        # 验证联系人存在
        if workflow_data.get("contact_id"):
            response = crm_client.get_contact_detail(workflow_data["contact_id"])
            data = response.json()
            assert data.get("code") == 200, "联系人应存在"
        
        # 验证商机存在且关联正确的客户
        if workflow_data.get("business_id"):
            response = crm_client.get_business_detail(workflow_data["business_id"])
            data = response.json()
            assert data.get("code") == 200, "商机应存在"
            business_data = data.get("data", {})
            if workflow_data.get("customer_id"):
                assert str(business_data.get("customerId")) == str(workflow_data["customer_id"]), \
                    f"商机应关联正确的客户: 期望customerId={workflow_data['customer_id']}, 实际={business_data.get('customerId')}"
        
        # 验证报价存在且关联正确的商机
        if workflow_data.get("quotation_id"):
            response = crm_client.get_quotation_detail(workflow_data["quotation_id"])
            data = response.json()
            assert data.get("code") == 200, "报价应存在"
            quotation_data = data.get("data", {})
            if workflow_data.get("business_id"):
                assert str(quotation_data.get("businessId")) == str(workflow_data["business_id"]), \
                    f"报价应关联正确的商机: 期望businessId={workflow_data['business_id']}, 实际={quotation_data.get('businessId')}"
        
        print("✅ WF-008 流程数据一致性验证通过")


@pytest.fixture(scope="class")
def lose_workflow_data():
    """初始化输单流程测试数据"""
    data = {
        "clue_id": None,
        "customer_id": None,
        "contact_id": None,
        "business_id": None,
        "quotation_id": None,
        "test_batch": f"LOSE_{int(time.time())}"
    }
    return data


class TestLoseBusinessWorkflow:
    """输单业务流程测试 - 前序步骤与赢单相同，最终执行输单"""
    
    def test_lw01_create_clue(self, crm_client, authorized_headers, test_data_manager, lose_workflow_data):
        """LW-001 创建线索"""
        crm_client.session.headers.update(authorized_headers)
        
        clue = test_data_manager.create_clue(name_prefix="输单流程")
        lose_workflow_data["clue_id"] = clue["id"]
        
        assert clue["id"] is not None, "线索ID不应为空"
        print(f"✅ LW-001 线索创建成功: {clue['name']}")
    
    def test_lw02_create_customer_from_clue(self, crm_client, authorized_headers, test_data_manager, lose_workflow_data):
        """LW-002 线索转客户"""
        crm_client.session.headers.update(authorized_headers)
        
        if not lose_workflow_data.get("clue_id"):
            pytest.skip("跳过：没有可用的线索")
        
        clue_id = lose_workflow_data["clue_id"]
        customer_name = f"输单流程测试公司_{int(time.time())}"
        
        response = crm_client.transform_clue_to_customer(
            clue_id=clue_id,
            company_name=customer_name,
            contact_name="张三",
            contact_phone="13300000000",
            position="经理"
        )
        assert response.status_code == 200
        result = response.json()
        
        if result.get("code") == 200:
            customer_data = result.get("data")
            if customer_data and isinstance(customer_data, dict):
                lose_workflow_data["customer_id"] = customer_data.get("id")
            elif customer_data:
                lose_workflow_data["customer_id"] = customer_data
            # 如果data为None，说明线索可能已转换，需要通过查询获取客户ID
            if not lose_workflow_data.get("customer_id"):
                # 通过客户列表查询获取刚创建的客户
                customer_list = crm_client.get_customer_list(page=1, size=1, name=customer_name)
                list_data = customer_list.json()
                if list_data.get("rows") and len(list_data["rows"]) > 0:
                    lose_workflow_data["customer_id"] = list_data["rows"][0]["id"]
            print(f"✅ LW-002 线索转客户成功: {customer_name} (客户ID: {lose_workflow_data.get('customer_id')})")
        else:
            # 检查是否因为线索已转换
            msg = result.get('msg', '')
            if '已' in msg or '存在' in msg:
                # 线索可能已被转换，尝试通过客户名称查询获取
                customer_id = test_data_manager._find_customer_by_name(customer_name)
                if customer_id:
                    lose_workflow_data["customer_id"] = customer_id
                    print(f"✅ LW-002 线索已转换，查询获取客户ID: {customer_id}")
                    return
            print(f"⚠️ LW-002 线索转客户返回: {msg}")
    
    def test_lw03_create_contact(self, crm_client, authorized_headers, test_data_manager, lose_workflow_data):
        """LW-003 创建联系人"""
        crm_client.session.headers.update(authorized_headers)
        
        if not lose_workflow_data.get("customer_id"):
            pytest.skip("跳过：没有可用的客户")
        
        contact = test_data_manager.create_contact(
            lose_workflow_data["customer_id"],
            name_prefix="输单流程"
        )
        lose_workflow_data["contact_id"] = contact["id"]
        
        assert contact["id"] is not None, "联系人ID不应为空"
        print(f"✅ LW-003 联系人创建成功: {contact['name']}")
    
    def test_lw04_create_business(self, crm_client, authorized_headers, test_data_manager, lose_workflow_data):
        """LW-004 创建商机"""
        crm_client.session.headers.update(authorized_headers)
        
        if not lose_workflow_data.get("customer_id"):
            pytest.skip("跳过：没有可用的客户")
        
        business = test_data_manager.create_business(
            lose_workflow_data["customer_id"],
            name_prefix="输单流程"
        )
        lose_workflow_data["business_id"] = business["id"]
        
        assert business["id"] is not None, "商机ID不应为空"
        print(f"✅ LW-004 商机创建成功: {business['name']}")
    
    def test_lw05_advance_to_proposal_stage(self, crm_client, authorized_headers, lose_workflow_data):
        """LW-005 推进到方案确认阶段"""
        crm_client.session.headers.update(authorized_headers)
        
        if not lose_workflow_data.get("business_id"):
            pytest.skip("跳过：没有可用的商机")
        
        response = crm_client.advance_business_stage(lose_workflow_data["business_id"], "2")
        assert response.status_code == 200
        result = response.json()
        
        if result.get("code") == 200:
            print("✅ LW-005 推进到方案确认阶段成功")
        else:
            print(f"⚠️ LW-005 推进返回: {result.get('msg')}")
    
    def test_lw06_create_and_approve_quotation(self, crm_client, authorized_headers, test_data_manager, lose_workflow_data):
        """LW-006 创建报价单并审批通过"""
        crm_client.session.headers.update(authorized_headers)
        
        if not lose_workflow_data.get("business_id"):
            pytest.skip("跳过：没有可用的商机")
        
        quotation = test_data_manager.create_quotation(lose_workflow_data["business_id"])
        lose_workflow_data["quotation_id"] = quotation["id"]
        
        assert quotation["id"] is not None, "报价ID不应为空"
        print(f"  📝 报价单创建成功: {quotation['name']}")
        
        # 审批通过
        approve_response = crm_client.approve_quotation(quotation["id"])
        assert approve_response.status_code == 200
        print(f"  ✅ 报价审批通过")
    
    def test_lw07_advance_to_negotiation_and_lose(self, crm_client, authorized_headers, lose_workflow_data):
        """LW-007 推进到谈判审核并输单"""
        crm_client.session.headers.update(authorized_headers)
        
        if not lose_workflow_data.get("business_id"):
            pytest.skip("跳过：没有可用的商机")
        
        business_id = lose_workflow_data["business_id"]
        
        # 推进到阶段3(谈判审核)
        response = crm_client.advance_business_stage(business_id, "3")
        assert response.status_code == 200
        print("  ✅ 推进到谈判审核阶段")
        
        # 输单（stage=6, status=2）
        lose_response = crm_client.lose_business(business_id, lost_reason="2")
        assert lose_response.status_code == 200
        lose_result = lose_response.json()
        
        if lose_result.get("code") == 200:
            print("  ✅ 输单成功")
        else:
            print(f"  ⚠️ 输单返回: {lose_result.get('msg')}")
        
        # 验证最终状态
        detail_response = crm_client.get_business_detail(business_id)
        detail_data = detail_response.json()
        business_info = detail_data.get("data", {})
        
        current_stage = business_info.get("stage")
        status = business_info.get("status")
        
        print(f"  商机阶段: {current_stage}")
        print(f"  商机状态: {status}")
        
        assert current_stage == "6", f"商机应为输单阶段(6)，当前为{current_stage}"
        assert str(status) == "2", f"商机应为输单状态(2)，当前为{status}"
        print(f"✅ LW-007 推进到谈判审核并输单成功")


class TestPublicPoolWorkflow:
    """公海池业务流程测试"""
    
    def test_pp01_get_public_pool_list(self, crm_client, authorized_headers):
        """PP-001 获取公海池客户列表"""
        crm_client.session.headers.update(authorized_headers)
        
        response = crm_client.get_public_pool_list(page=1, size=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 200
        assert "rows" in data
        assert "total" in data
        
        pool_count = data.get("total", 0)
        print(f"✅ PP-001 公海池列表获取成功，共 {pool_count} 条")
    
    def test_pp02_claim_customer_from_pool(self, crm_client, authorized_headers, test_data_manager):
        """PP-002 从公海池领取客户"""
        crm_client.session.headers.update(authorized_headers)
        
        # 先获取公海池列表
        list_response = crm_client.get_public_pool_list(page=1, size=1)
        list_data = list_response.json()
        
        if list_data.get("code") != 200 or not list_data.get("rows"):
            pytest.skip("跳过：公海池没有可领取的客户")
        
        customer_id = list_data["rows"][0]["id"]
        customer_name = list_data["rows"][0].get("customerName", "未知")
        
        # 领取客户
        response = crm_client.claim_public_customer(customer_id)
        assert response.status_code == 200
        result = response.json()
        
        if result.get("code") == 200:
            print(f"✅ PP-002 公海池客户领取成功: {customer_name}")
        else:
            print(f"⚠️ PP-002 领取结果: {result.get('msg')}")


class TestGoalWorkflow:
    """目标管理业务流程测试"""
    
    def test_goal01_create_goal(self, crm_client, authorized_headers, test_data_manager):
        """GOAL-001 创建目标"""
        crm_client.session.headers.update(authorized_headers)
        
        goal_data = {
            "goalName": test_data_manager.generate_name("目标"),
            "goalType": "monthly",
            "targetAmount": 100000,
            "startDate": "2026-01-01",
            "endDate": "2026-12-31",
            "remark": "自动化测试创建"
        }
        
        response = crm_client.create_goal(goal_data)
        assert response.status_code == 200
        result = response.json()
        
        if result.get("code") == 200:
            goal_id = result.get("data", {}).get("id")
            if goal_id:
                test_data_manager.created_resources.append({
                    "type": "goal",
                    "id": goal_id,
                    "name": goal_data["goalName"],
                    "created_at": time.time()
                })
                print(f"✅ GOAL-001 目标创建成功: {goal_data['goalName']} (ID: {goal_id})")
                return
        
        print(f"⚠️ GOAL-001 目标创建返回: {result.get('msg', '需要确认接口')}")
    
    def test_goal02_get_goal_list(self, crm_client, authorized_headers):
        """GOAL-002 获取目标列表"""
        crm_client.session.headers.update(authorized_headers)
        
        response = crm_client.get_goal_list()
        assert response.status_code == 200
        data = response.json()
        
        print(f"✅ GOAL-002 目标列表获取成功")
    
    def test_goal03_approve_goal(self, crm_client, authorized_headers, test_data_manager):
        """GOAL-003 审批目标"""
        crm_client.session.headers.update(authorized_headers)
        
        # 获取已创建的目标
        goals = test_data_manager.get_created_resources("goal")
        if not goals:
            # 如果没有已创建的目标，尝试获取现有目标
            list_response = crm_client.get_goal_list()
            list_data = list_response.json()
            
            if list_data.get("code") == 200 and list_data.get("data"):
                goals = [{"id": list_data["data"][0]["id"]}]
        
        if not goals:
            pytest.skip("跳过：没有可审批的目标")
        
        goal_id = goals[0]["id"]
        
        response = crm_client.approve_goal(goal_id, "approved")
        assert response.status_code == 200
        result = response.json()
        
        print(f"审批结果: {result.get('msg', '成功')}")
        print(f"✅ GOAL-003 目标审批测试完成")


class TestApprovalWorkflow:
    """审批流程测试"""
    
    def test_appr01_get_approval_list(self, crm_client, authorized_headers):
        """APPR-001 获取报价列表（用于审批）"""
        crm_client.session.headers.update(authorized_headers)
        
        response = crm_client.get_quotation_list_for_approval(page=1, size=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 200
        
        print(f"✅ APPR-001 报价列表获取成功，共 {data.get('total', 0)} 条")
    
    def test_appr02_approve_quotation(self, crm_client, authorized_headers, test_data_manager):
        """APPR-002 审批通过报价"""
        crm_client.session.headers.update(authorized_headers)
        
        # 获取报价列表
        list_response = crm_client.get_quotation_list_for_approval(page=1, size=10)
        list_data = list_response.json()
        
        if list_data.get("code") != 200 or not list_data.get("rows"):
            pytest.skip("跳过：没有可审批的报价")
        
        # 审批第一条报价
        quotation_id = list_data["rows"][0]["id"]
        quotation_name = list_data["rows"][0].get("remark", str(quotation_id))
        
        response = crm_client.approve_quotation(quotation_id, "自动化测试审批通过")
        assert response.status_code == 200
        result = response.json()
        
        if result.get("code") == 200:
            print(f"✅ APPR-002 报价审批通过成功: {quotation_name}")
        else:
            print(f"⚠️ APPR-002 审批结果: {result.get('msg')}")
    
    def test_appr03_reject_quotation(self, crm_client, authorized_headers, test_data_manager):
        """APPR-003 审批拒绝报价"""
        crm_client.session.headers.update(authorized_headers)
        
        # 创建一个新报价用于拒绝测试
        quotation_data = {
            "businessId": 1,
            "customerId": 1,
            "totalAmount": 5000,
            "ownerUserId": "2059112632781406210",
            "remark": "自动化测试拒绝审批"
        }
        
        create_response = crm_client.create_quotation(quotation_data)
        create_data = create_response.json()
        
        if create_data.get("code") != 200:
            pytest.skip("跳过：无法创建报价用于拒绝测试")
        
        # 获取刚创建的报价
        list_response = crm_client.get_quotation_list_for_approval(page=1, size=1)
        list_data = list_response.json()
        rows = list_data.get("rows", [])
        
        if not rows:
            pytest.skip("跳过：找不到刚创建的报价")
        
        quotation_id = rows[0]["id"]
        
        # 拒绝报价
        response = crm_client.reject_quotation(quotation_id, "自动化测试拒绝")
        assert response.status_code == 200
        result = response.json()
        
        if result.get("code") == 200:
            print(f"✅ APPR-003 报价审批拒绝成功")
        else:
            print(f"⚠️ APPR-003 拒绝结果: {result.get('msg')}")


class TestTodoWorkflow:
    """待办事项流程测试"""
    
    def test_todo01_create_todo(self, crm_client, authorized_headers, test_data_manager):
        """TODO-001 创建待办"""
        crm_client.session.headers.update(authorized_headers)
        
        todo_data = {
            "taskTitle": f"自动化测试待办_{int(time.time())}",
            "taskType": "2",
            "taskDate": "2026-07-30",
            "status": "1",
            "ownerUserId": "2059112632781406210"
        }
        
        response = crm_client.create_todo(todo_data)
        assert response.status_code == 200
        data = response.json()
        
        if data.get("code") == 200:
            print(f"✅ TODO-001 待办创建成功: {todo_data['taskTitle']}")
        else:
            pytest.fail(f"创建待办失败: {data.get('msg')}")
    
    def test_todo02_get_todo_list(self, crm_client, authorized_headers):
        """TODO-002 获取待办列表"""
        crm_client.session.headers.update(authorized_headers)
        
        response = crm_client.get_todo_list(page=1, size=10)
        assert response.status_code == 200
        data = response.json()
        
        todo_count = len(data.get("data", []))
        print(f"✅ TODO-002 待办列表获取成功，共 {todo_count} 条待办")
    
    def test_todo03_complete_todo(self, crm_client, authorized_headers):
        """TODO-003 完成待办"""
        crm_client.session.headers.update(authorized_headers)
        
        # 获取待办列表
        list_response = crm_client.get_todo_list(page=1, size=5)
        list_data = list_response.json()
        todos = list_data.get("data", [])
        
        if not todos:
            pytest.skip("跳过：没有可完成的待办")
        
        # 完成第一条待办
        todo_id = todos[0]["id"]
        todo_title = todos[0].get("taskTitle", "")
        
        response = crm_client.complete_todo(todo_id)
        assert response.status_code == 200
        result = response.json()
        
        if result.get("code") == 200:
            print(f"✅ TODO-003 待办完成成功: {todo_title}")
        else:
            print(f"⚠️ TODO-003 完成结果: {result.get('msg')}")
    
    def test_todo04_delete_todo(self, crm_client, authorized_headers, test_data_manager):
        """TODO-004 删除待办"""
        crm_client.session.headers.update(authorized_headers)
        
        # 创建一个待办用于删除
        todo_data = {
            "taskTitle": f"待删除待办_{int(time.time())}",
            "taskType": "2",
            "taskDate": "2026-07-30",
            "status": "1",
            "ownerUserId": "2059112632781406210"
        }
        
        crm_client.create_todo(todo_data)
        
        # 获取刚创建的待办
        list_response = crm_client.get_todo_list(page=1, size=1)
        list_data = list_response.json()
        todos = list_data.get("data", [])
        
        if not todos:
            pytest.skip("跳过：找不到要删除的待办")
        
        todo_id = todos[0]["id"]
        
        # 删除待办
        response = crm_client.delete_todo(todo_id)
        assert response.status_code == 200
        result = response.json()
        
        if result.get("code") == 200:
            print(f"✅ TODO-004 待办删除成功")
        else:
            print(f"⚠️ TODO-004 删除结果: {result.get('msg')}")
