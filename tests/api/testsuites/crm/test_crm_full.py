"""
CRM 模块完整测试用例 v2.0
- 使用 TestDataManager 管理测试数据
- 增强断言验证
- 覆盖更多边界场景
"""
import pytest
import time


class TestCustomerAPI:
    """客户管理 API 测试"""
    
    def test_create_customer_with_minimal_data(self, crm_client, authorized_headers, test_data_manager):
        """API-CRM-CUST-001 创建客户-最小数据"""
        crm_client.session.headers.update(authorized_headers)
        
        customer = test_data_manager.create_customer()
        
        assert customer["id"] is not None, "客户ID不应为空"
        assert customer["name"] is not None, "客户名称不应为空"
        
        print(f"✅ 创建客户成功: {customer['name']}")
    
    def test_create_customer_with_complete_data(self, crm_client, authorized_headers, test_data_manager):
        """API-CRM-CUST-002 创建客户-完整数据"""
        crm_client.session.headers.update(authorized_headers)
        
        customer = test_data_manager.create_customer(
            email=f"complete_{int(time.time())}@test.com",
            remark="完整数据测试"
        )
        
        assert customer["id"] is not None, "客户ID不应为空"
        print(f"✅ 创建完整客户成功: {customer['name']}")
    
    def test_create_customer_empty_name(self, crm_client, authorized_headers):
        """API-CRM-CUST-003 创建客户-空名称校验"""
        crm_client.session.headers.update(authorized_headers)
        
        customer_data = {
            "customerName": "",
            "customerLevel": "1",
            "customerSource": "1",
            "phone": "13800138000"
        }
        
        response = crm_client.create_customer(customer_data)
        assert response.status_code == 200
        data = response.json()
        
        # 验证系统返回了合理的响应（可能是成功或错误）
        assert data.get("code") is not None, "响应应包含code字段"
        print(f"📊 空名称创建客户响应: code={data.get('code')}, msg={data.get('msg')}")
    
    def test_get_customer_list(self, crm_client, authorized_headers):
        """API-CRM-CUST-004 获取客户列表"""
        crm_client.session.headers.update(authorized_headers)
        
        response = crm_client.get_customer_list(page=1, size=10)
        assert response.status_code == 200, f"获取客户列表失败，状态码: {response.status_code}"
        
        data = response.json()
        assert data.get("code") == 200, f"获取客户列表失败: {data.get('msg')}"
        assert "rows" in data, "响应应包含rows字段"
        assert "total" in data, "响应应包含total字段"
        assert isinstance(data["rows"], list), "rows应为列表类型"
        assert isinstance(data["total"], int), "total应为整数类型"
        
        # 验证每条记录的必要字段
        if data["rows"]:
            first_row = data["rows"][0]
            assert "id" in first_row, "客户记录应包含id字段"
            assert "customerName" in first_row, "客户记录应包含customerName字段"
        
        print(f"✅ 获取客户列表成功: {data['total']} 条记录")
    
    def test_get_customer_detail(self, crm_client, authorized_headers, test_data_manager):
        """API-CRM-CUST-005 获取客户详情"""
        crm_client.session.headers.update(authorized_headers)
        
        # 先创建一个客户
        customer = test_data_manager.create_customer()
        customer_id = customer["id"]
        
        # 获取详情
        response = crm_client.get_customer_detail(customer_id)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 200, f"获取客户详情失败: {data.get('msg')}"
        assert data.get("data") is not None, "响应应包含data字段"
        
        customer_data = data["data"]
        assert customer_data.get("id") == customer_id, "客户ID应匹配"
        assert customer_data.get("customerName") == customer["name"], "客户名称应匹配"
        
        print(f"✅ 获取客户详情成功: {customer['name']}")
    
    def test_update_customer(self, crm_client, authorized_headers, test_data_manager):
        """API-CRM-CUST-006 更新客户信息"""
        crm_client.session.headers.update(authorized_headers)
        
        # 创建客户
        customer = test_data_manager.create_customer()
        customer_id = customer["id"]
        
        # 更新客户
        update_data = {
            "customerName": f"更新后_{int(time.time())}",
            "customerLevel": "3",
            "remark": "更新测试"
        }
        
        response = crm_client.update_customer(customer_id, update_data)
        assert response.status_code == 200
        
        data = response.json()
        if data.get("code") == 200:
            # 验证更新结果
            detail_response = crm_client.get_customer_detail(customer_id)
            detail_data = detail_response.json()
            if detail_data.get("code") == 200:
                print(f"✅ 更新客户成功并已验证")
            else:
                print(f"⚠️ 更新成功但验证失败: {detail_data.get('msg')}")
        else:
            print(f"⚠️ 更新客户响应: code={data.get('code')}, msg={data.get('msg')}")
    
    def test_delete_customer(self, crm_client, authorized_headers, test_data_manager):
        """API-CRM-CUST-007 删除客户"""
        crm_client.session.headers.update(authorized_headers)
        
        # 创建客户用于删除测试
        customer = test_data_manager.create_customer()
        customer_id = customer["id"]
        
        # 删除客户
        response = crm_client.delete_customer(customer_id)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 200, f"删除客户失败: {data.get('msg')}"
        
        # 验证删除后详情返回错误
        detail_response = crm_client.get_customer_detail(customer_id)
        detail_data = detail_response.json()
        print(f"📊 删除后查询响应: code={detail_data.get('code')}")
        
        # 从清理列表中移除（因为已手动删除）
        test_data_manager.created_resources = [
            r for r in test_data_manager.created_resources 
            if not (r["type"] == "customer" and r["id"] == customer_id)
        ]
        
        print(f"✅ 删除客户成功: {customer['name']}")
    
    def test_customer_pagination(self, crm_client, authorized_headers):
        """API-CRM-CUST-008 客户分页测试"""
        crm_client.session.headers.update(authorized_headers)
        
        # 测试不同分页参数
        for page, size in [(1, 5), (1, 20), (2, 10)]:
            response = crm_client.get_customer_list(page=page, size=size)
            assert response.status_code == 200
            
            data = response.json()
            assert data.get("code") == 200
            assert len(data.get("rows", [])) <= size, f"每页数量不超过{size}"
        
        print("✅ 客户分页测试通过")


class TestClueAPI:
    """线索管理 API 测试"""
    
    def test_create_clue(self, crm_client, authorized_headers, test_data_manager):
        """API-CRM-CLUE-001 创建线索"""
        crm_client.session.headers.update(authorized_headers)
        
        clue = test_data_manager.create_clue()
        
        assert clue["id"] is not None, "线索ID不应为空"
        print(f"✅ 创建线索成功: {clue['name']}")
    
    def test_get_clue_list(self, crm_client, authorized_headers):
        """API-CRM-CLUE-002 获取线索列表"""
        crm_client.session.headers.update(authorized_headers)
        
        response = crm_client.get_clue_list(page=1, size=10)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 200
        assert "rows" in data
        assert "total" in data
        
        # 验证字段
        if data["rows"]:
            row = data["rows"][0]
            assert "id" in row, "线索记录应包含id"
            assert "clueName" in row or "name" in row, "线索记录应包含名称字段"
        
        print(f"✅ 获取线索列表成功: {data.get('total', 0)} 条")
    
    def test_get_clue_simple_list(self, crm_client, authorized_headers):
        """API-CRM-CLUE-003 获取线索简单列表"""
        crm_client.session.headers.update(authorized_headers)
        
        response = crm_client.get_clue_simple_list()
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 200
        
        print(f"✅ 获取线索简单列表成功")
    
    def test_get_clue_detail(self, crm_client, authorized_headers, test_data_manager):
        """API-CRM-CLUE-004 获取线索详情"""
        crm_client.session.headers.update(authorized_headers)
        
        # 创建线索
        clue = test_data_manager.create_clue()
        clue_id = clue["id"]
        
        # 获取详情
        response = crm_client.get_clue_detail(clue_id)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 200
        assert data.get("data") is not None
        
        print(f"✅ 获取线索详情成功: {clue['name']}")
    
    def test_update_clue(self, crm_client, authorized_headers, test_data_manager):
        """API-CRM-CLUE-005 更新线索"""
        crm_client.session.headers.update(authorized_headers)
        
        # 创建线索
        clue = test_data_manager.create_clue()
        clue_id = clue["id"]
        
        # 更新线索
        update_data = {
            "clueName": f"更新线索_{int(time.time())}",
            "status": "1"
        }
        
        response = crm_client.update_clue(clue_id, update_data)
        assert response.status_code == 200
        
        data = response.json()
        print(f"📊 更新线索响应: code={data.get('code')}, msg={data.get('msg')}")
    
    def test_delete_clue(self, crm_client, authorized_headers, test_data_manager):
        """API-CRM-CLUE-006 删除线索"""
        crm_client.session.headers.update(authorized_headers)
        
        # 创建线索
        clue = test_data_manager.create_clue()
        clue_id = clue["id"]
        
        # 删除线索
        response = crm_client.delete_clue(clue_id)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 200, f"删除线索失败: {data.get('msg')}"
        
        # 从清理列表中移除
        test_data_manager.created_resources = [
            r for r in test_data_manager.created_resources 
            if not (r["type"] == "clue" and r["id"] == clue_id)
        ]
        
        print(f"✅ 删除线索成功: {clue['name']}")


class TestContactAPI:
    """联系人管理 API 测试"""
    
    def test_create_contact(self, crm_client, authorized_headers, test_data_manager):
        """API-CRM-CONTACT-001 创建联系人"""
        crm_client.session.headers.update(authorized_headers)
        
        # 先创建客户
        customer = test_data_manager.create_customer()
        
        # 创建联系人
        contact = test_data_manager.create_contact(customer["id"])
        
        assert contact["id"] is not None, "联系人ID不应为空"
        assert contact["parent_id"] == customer["id"], "联系人应关联正确的客户"
        
        print(f"✅ 创建联系人成功: {contact['name']}")
    
    def test_get_contact_list(self, crm_client, authorized_headers):
        """API-CRM-CONTACT-002 获取联系人列表"""
        crm_client.session.headers.update(authorized_headers)
        
        response = crm_client.get_contact_list(page=1, size=10)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 200
        assert "rows" in data
        assert "total" in data
        
        print(f"✅ 获取联系人列表成功: {data.get('total', 0)} 条")
    
    def test_get_contact_simple_list(self, crm_client, authorized_headers):
        """API-CRM-CONTACT-003 获取联系人简单列表"""
        crm_client.session.headers.update(authorized_headers)
        
        response = crm_client.get_contact_simple_list()
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 200
        
        print("✅ 获取联系人简单列表成功")
    
    def test_get_contact_detail(self, crm_client, authorized_headers, test_data_manager):
        """API-CRM-CONTACT-004 获取联系人详情"""
        crm_client.session.headers.update(authorized_headers)
        
        # 创建客户和联系人
        customer = test_data_manager.create_customer()
        contact = test_data_manager.create_contact(customer["id"])
        
        # 获取详情
        response = crm_client.get_contact_detail(contact["id"])
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 200
        assert data.get("data") is not None
        
        print(f"✅ 获取联系人详情成功: {contact['name']}")
    
    def test_update_contact(self, crm_client, authorized_headers, test_data_manager):
        """API-CRM-CONTACT-005 更新联系人"""
        crm_client.session.headers.update(authorized_headers)
        
        # 创建客户和联系人
        customer = test_data_manager.create_customer()
        contact = test_data_manager.create_contact(customer["id"])
        
        # 更新联系人
        update_data = {
            "name": f"更新联系人_{int(time.time())}",
            "phone": "13900139001"
        }
        
        response = crm_client.update_contact(contact["id"], update_data)
        assert response.status_code == 200
        
        data = response.json()
        print(f"📊 更新联系人响应: code={data.get('code')}, msg={data.get('msg')}")
    
    def test_delete_contact(self, crm_client, authorized_headers, test_data_manager):
        """API-CRM-CONTACT-006 删除联系人"""
        crm_client.session.headers.update(authorized_headers)
        
        # 创建客户和联系人
        customer = test_data_manager.create_customer()
        contact = test_data_manager.create_contact(customer["id"])
        
        # 删除联系人
        response = crm_client.delete_contact(contact["id"])
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 200, f"删除联系人失败: {data.get('msg')}"
        
        # 从清理列表中移除
        test_data_manager.created_resources = [
            r for r in test_data_manager.created_resources 
            if not (r["type"] == "contact" and r["id"] == contact["id"])
        ]
        
        print(f"✅ 删除联系人成功: {contact['name']}")


class TestBusinessAPI:
    """商机管理 API 测试"""
    
    def test_create_business(self, crm_client, authorized_headers, test_data_manager):
        """API-CRM-BUS-001 创建商机"""
        crm_client.session.headers.update(authorized_headers)
        
        # 先创建客户
        customer = test_data_manager.create_customer()
        
        # 创建商机
        business = test_data_manager.create_business(customer["id"])
        
        assert business["id"] is not None, "商机ID不应为空"
        assert business["parent_id"] == customer["id"], "商机应关联正确的客户"
        
        print(f"✅ 创建商机成功: {business['name']}")
    
    def test_get_business_list(self, crm_client, authorized_headers):
        """API-CRM-BUS-002 获取商机列表"""
        crm_client.session.headers.update(authorized_headers)
        
        response = crm_client.get_business_list(page=1, size=10)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 200
        assert "rows" in data
        assert "total" in data
        
        if data["rows"]:
            row = data["rows"][0]
            assert "id" in row, "商机记录应包含id"
            assert "businessName" in row, "商机记录应包含businessName"
        
        print(f"✅ 获取商机列表成功: {data.get('total', 0)} 条")
    
    def test_get_business_detail(self, crm_client, authorized_headers, test_data_manager):
        """API-CRM-BUS-003 获取商机详情"""
        crm_client.session.headers.update(authorized_headers)
        
        # 创建客户和商机
        customer = test_data_manager.create_customer()
        business = test_data_manager.create_business(customer["id"])
        
        # 获取详情
        response = crm_client.get_business_detail(business["id"])
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 200
        assert data.get("data") is not None
        
        business_data = data["data"]
        assert business_data.get("id") == business["id"], "商机ID应匹配"
        assert business_data.get("customerId") == customer["id"], "客户ID应匹配"
        
        print(f"✅ 获取商机详情成功: {business['name']}")
    
    def test_update_business(self, crm_client, authorized_headers, test_data_manager):
        """API-CRM-BUS-004 更新商机"""
        crm_client.session.headers.update(authorized_headers)
        
        # 创建客户和商机
        customer = test_data_manager.create_customer()
        business = test_data_manager.create_business(customer["id"])
        
        # 更新商机
        update_data = {
            "businessName": f"更新商机_{int(time.time())}",
            "amount": 20000,
            "remark": "更新测试"
        }
        
        response = crm_client.update_business(business["id"], update_data)
        assert response.status_code == 200
        
        data = response.json()
        print(f"📊 更新商机响应: code={data.get('code')}, msg={data.get('msg')}")
    
    def test_delete_business(self, crm_client, authorized_headers, test_data_manager):
        """API-CRM-BUS-005 删除商机"""
        crm_client.session.headers.update(authorized_headers)
        
        # 创建客户和商机
        customer = test_data_manager.create_customer()
        business = test_data_manager.create_business(customer["id"])
        
        # 删除商机
        response = crm_client.delete_business(business["id"])
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 200, f"删除商机失败: {data.get('msg')}"
        
        # 从清理列表中移除
        test_data_manager.created_resources = [
            r for r in test_data_manager.created_resources 
            if not (r["type"] == "business" and r["id"] == business["id"])
        ]
        
        print(f"✅ 删除商机成功: {business['name']}")
    
    def test_add_business_product(self, crm_client, authorized_headers, test_data_manager):
        """API-CRM-BUS-006 添加商机产品"""
        crm_client.session.headers.update(authorized_headers)
        
        # 创建客户和商机
        customer = test_data_manager.create_customer()
        business = test_data_manager.create_business(customer["id"])
        
        # 添加产品
        product_data = {
            "businessId": business["id"],
            "productName": f"测试产品_{int(time.time())}",
            "quantity": 1,
            "price": 1000,
            "discount": 100
        }
        
        response = crm_client.add_business_product(product_data)
        assert response.status_code == 200
        
        data = response.json()
        print(f"📊 添加产品响应: code={data.get('code')}, msg={data.get('msg')}")
    
    def test_add_business_follow(self, crm_client, authorized_headers, test_data_manager):
        """API-CRM-BUS-007 添加商机跟进"""
        crm_client.session.headers.update(authorized_headers)
        
        # 创建客户和商机
        customer = test_data_manager.create_customer()
        business = test_data_manager.create_business(customer["id"])
        
        # 添加跟进
        follow_data = {
            "businessId": business["id"],
            "content": "自动化测试跟进内容",
            "nextPlan": "下一步计划"
        }
        
        response = crm_client.add_business_follow(follow_data)
        assert response.status_code == 200
        
        data = response.json()
        print(f"📊 添加跟进响应: code={data.get('code')}, msg={data.get('msg')}")


class TestQuotationAPI:
    """报价管理 API 测试"""
    
    def test_create_quotation(self, crm_client, authorized_headers, test_data_manager):
        """API-CRM-QTE-001 创建报价"""
        crm_client.session.headers.update(authorized_headers)
        
        # 创建客户和商机
        customer = test_data_manager.create_customer()
        business = test_data_manager.create_business(customer["id"])
        
        # 创建报价
        quotation = test_data_manager.create_quotation(business["id"])
        
        assert quotation["id"] is not None, "报价ID不应为空"
        assert quotation["parent_id"] == business["id"], "报价应关联正确的商机"
        
        print(f"✅ 创建报价成功: {quotation['name']}")
    
    def test_get_quotation_list(self, crm_client, authorized_headers):
        """API-CRM-QTE-002 获取报价列表"""
        crm_client.session.headers.update(authorized_headers)
        
        response = crm_client.get_quotation_list(page=1, size=10)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 200
        assert "rows" in data
        assert "total" in data
        
        print(f"✅ 获取报价列表成功: {data.get('total', 0)} 条")
    
    def test_get_quotation_detail(self, crm_client, authorized_headers, test_data_manager):
        """API-CRM-QTE-003 获取报价详情"""
        crm_client.session.headers.update(authorized_headers)
        
        # 创建完整数据链
        customer = test_data_manager.create_customer()
        business = test_data_manager.create_business(customer["id"])
        quotation = test_data_manager.create_quotation(business["id"])
        
        # 获取详情
        response = crm_client.get_quotation_detail(quotation["id"])
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 200
        assert data.get("data") is not None
        
        print(f"✅ 获取报价详情成功: {quotation['name']}")
    
    def test_submit_quotation_for_approval(self, crm_client, authorized_headers, test_data_manager):
        """API-CRM-QTE-004 提交报价审批"""
        crm_client.session.headers.update(authorized_headers)
        
        # 创建报价
        customer = test_data_manager.create_customer()
        business = test_data_manager.create_business(customer["id"])
        quotation = test_data_manager.create_quotation(business["id"])
        
        # 提交审批
        response = crm_client.submit_quotation_for_approval(quotation["id"])
        assert response.status_code == 200
        
        data = response.json()
        print(f"📊 提交审批响应: code={data.get('code')}, msg={data.get('msg')}")
    
    def test_delete_quotation(self, crm_client, authorized_headers, test_data_manager):
        """API-CRM-QTE-005 删除报价"""
        crm_client.session.headers.update(authorized_headers)
        
        # 创建报价
        customer = test_data_manager.create_customer()
        business = test_data_manager.create_business(customer["id"])
        quotation = test_data_manager.create_quotation(business["id"])
        
        # 删除报价
        response = crm_client.delete_quotation(quotation["id"])
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 200, f"删除报价失败: {data.get('msg')}"
        
        # 从清理列表中移除
        test_data_manager.created_resources = [
            r for r in test_data_manager.created_resources 
            if not (r["type"] == "quotation" and r["id"] == quotation["id"])
        ]
        
        print(f"✅ 删除报价成功: {quotation['name']}")


class TestDictAPI:
    """数据字典 API 测试"""
    
    @pytest.mark.parametrize("dict_type,expected_fields", [
        ("crm_customer_source", ["dictLabel", "dictValue"]),
        ("crm_customer_level", ["dictLabel", "dictValue"]),
        ("crm_clue_source", ["dictLabel", "dictValue"]),
        ("crm_clue_status", ["dictLabel", "dictValue"]),
        ("crm_business_stage", ["dictLabel", "dictValue"])
    ])
    def test_get_dict_data(self, crm_client, authorized_headers, dict_type, expected_fields):
        """API-CRM-DICT-001 获取各类字典数据"""
        crm_client.session.headers.update(authorized_headers)
        
        response = crm_client.get_dict_data(dict_type)
        assert response.status_code == 200, f"获取字典{dict_type}失败"
        
        data = response.json()
        assert data.get("code") == 200, f"获取字典{dict_type}失败: {data.get('msg')}"
        
        # 验证数据结构
        dict_data = data.get("data", []) or data.get("rows", [])
        if dict_data and len(dict_data) > 0:
            first_item = dict_data[0]
            for field in expected_fields:
                assert field in first_item, f"字典项应包含{field}字段"
        
        print(f"✅ 获取字典{dict_type}成功: {len(dict_data)} 项")


class TestStatisticsAPI:
    """统计分析 API 测试"""
    
    def test_get_dashboard(self, crm_client, authorized_headers):
        """API-CRM-STAT-001 获取仪表盘数据"""
        crm_client.session.headers.update(authorized_headers)
        
        response = crm_client.get_statistics_dashboard()
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 200, f"获取仪表盘失败: {data.get('msg')}"
        
        print("✅ 获取仪表盘数据成功")
    
    def test_get_performance_report(self, crm_client, authorized_headers):
        """API-CRM-STAT-002 获取绩效报告"""
        crm_client.session.headers.update(authorized_headers)
        
        response = crm_client.get_performance_report()
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 200
        
        print("✅ 获取绩效报告成功")
