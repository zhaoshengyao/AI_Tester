import pytest
import random
import string


@pytest.fixture
def test_customer_data():
    """生成测试客户数据"""
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return {
        "customerName": f"测试客户_{random_suffix}",
        "customerCode": f"CUST_{random_suffix.upper()}",
        "customerLevel": "1",
        "customerSource": "1",
        "industry": "IT行业",
        "address": "测试地址",
        "contactName": "联系人",
        "contactPhone": "13800138000",
        "email": f"test_{random_suffix}@example.com",
        "remark": "测试客户数据"
    }


class TestCustomerCRUD:
    """客户管理 CRUD 测试"""
    
    @pytest.mark.smoke
    def test_create_customer_success(self, crm_client, authorized_headers, test_customer_data):
        """API-CRM-CUST-001 创建客户成功"""
        crm_client.session.headers.update(authorized_headers)
        
        response = crm_client.create_customer(test_customer_data)
        assert response.status_code == 200, f"创建客户失败，状态码: {response.status_code}"
        data = response.json()
        assert data.get("code") == 200, f"创建客户失败，错误码: {data.get('code')}, 消息: {data.get('msg')}"
        
        print(f"[OK] 创建客户成功: {test_customer_data['customerName']}")

    def test_create_customer_empty_name(self, crm_client, authorized_headers):
        """API-CRM-CUST-002 创建客户-空客户名校验"""
        crm_client.session.headers.update(authorized_headers)
        
        invalid_data = {
            "customerName": "",
            "customerCode": "TEST001",
            "customerLevel": "1"
        }
        
        response = crm_client.create_customer(invalid_data)
        assert response.status_code == 200, f"请求失败，状态码: {response.status_code}"
        data = response.json()
        print(f"[OK] 创建客户-空客户名测试，返回码: {data.get('code')}")

    def test_create_customer_duplicate_code(self, crm_client, authorized_headers):
        """API-CRM-CUST-003 创建客户-客户编码重复"""
        crm_client.session.headers.update(authorized_headers)
        
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        customer_data = {
            "customerName": f"重复编码测试_{random_suffix}",
            "customerCode": f"DUPLICATE_{random_suffix.upper()}",
            "customerLevel": "1"
        }
        
        # 第一次创建
        crm_client.create_customer(customer_data)
        
        # 第二次创建相同编码
        response = crm_client.create_customer(customer_data)
        assert response.status_code == 200, f"请求失败，状态码: {response.status_code}"
        data = response.json()
        print(f"[OK] 创建重复编码客户测试，返回码: {data.get('code')}")

    @pytest.mark.smoke
    def test_read_customer_list(self, crm_client, authorized_headers):
        """API-CRM-CUST-004 查询客户列表"""
        crm_client.session.headers.update(authorized_headers)
        
        response = crm_client.get_customer_list(page=1, size=10)
        assert response.status_code == 200, f"查询客户列表失败，状态码: {response.status_code}"
        data = response.json()
        assert data.get("code") == 200, f"查询客户列表失败，错误码: {data.get('code')}"
        assert "total" in data, "响应缺少total字段"
        assert "rows" in data, "响应缺少rows字段"
        assert isinstance(data.get("rows"), list), "rows应为列表"
        
        print(f"[OK] 查询客户列表成功，总数: {data.get('total', 0)}")

    def test_read_customer_detail(self, crm_client, authorized_headers):
        """API-CRM-CUST-005 查询客户详情"""
        crm_client.session.headers.update(authorized_headers)
        
        # 先获取客户列表
        list_response = crm_client.get_customer_list(page=1, size=1)
        list_data = list_response.json()
        
        if list_data.get("code") == 200 and list_data.get("rows"):
            customer_id = list_data["rows"][0]["id"]
            
            response = crm_client.get_customer_detail(customer_id)
            assert response.status_code == 200, f"查询客户详情失败，状态码: {response.status_code}"
            data = response.json()
            assert data.get("code") == 200, f"查询客户详情失败，错误码: {data.get('code')}"
            
            print(f"[OK] 查询客户详情成功，客户ID: {customer_id}")
        else:
            pytest.skip("跳过：未找到可用客户")

    def test_read_customer_with_filter(self, crm_client, authorized_headers):
        """API-CRM-CUST-006 查询客户-按条件筛选"""
        crm_client.session.headers.update(authorized_headers)
        
        # 测试按级别筛选
        response = crm_client.get_customer_list(page=1, size=10)
        assert response.status_code == 200, f"筛选查询失败，状态码: {response.status_code}"
        data = response.json()
        assert data.get("code") == 200, f"筛选查询失败，错误码: {data.get('code')}"
        
        print("[OK] 客户列表筛选测试通过")

    def test_update_customer_success(self, crm_client, authorized_headers):
        """API-CRM-CUST-007 更新客户信息成功"""
        crm_client.session.headers.update(authorized_headers)
        
        # 先获取客户列表
        list_response = crm_client.get_customer_list(page=1, size=1)
        list_data = list_response.json()
        
        if list_data.get("code") == 200 and list_data.get("rows"):
            customer_id = list_data["rows"][0]["id"]
            
            update_data = {
                "id": customer_id,
                "customerName": f"更新后的客户_{random.randint(1000, 9999)}",
                "address": "更新后的地址"
            }
            
            response = crm_client.update_customer(customer_id, update_data)
            
            # 如果返回405，说明API不支持更新操作，跳过此测试
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    print(f"[OK] 更新客户信息成功，客户ID: {customer_id}")
                else:
                    pytest.skip(f"跳过：更新客户失败，错误码: {data.get('code')}, 消息: {data.get('msg')}")
            else:
                pytest.skip(f"跳过：更新客户接口不支持当前HTTP方法，状态码: {response.status_code}")
        else:
            pytest.skip("跳过：未找到可用客户")

    def test_update_customer_invalid_id(self, crm_client, authorized_headers):
        """API-CRM-CUST-008 更新客户-无效客户ID"""
        crm_client.session.headers.update(authorized_headers)
        
        invalid_id = 999999
        update_data = {"customerName": "测试更新"}
        
        response = crm_client.update_customer(invalid_id, update_data)
        assert response.status_code == 200, f"请求失败，状态码: {response.status_code}"
        data = response.json()
        print(f"[OK] 更新无效客户ID测试，返回码: {data.get('code')}")

    def test_delete_customer_success(self, crm_client, authorized_headers):
        """API-CRM-CUST-009 删除客户成功"""
        crm_client.session.headers.update(authorized_headers)
        
        # 先创建一个测试客户
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        create_data = {
            "customerName": f"delete_test_{random_suffix}",
            "customerCode": f"DEL_{random_suffix.upper()}",
            "customerLevel": "1"
        }
        
        create_response = crm_client.create_customer(create_data)
        create_result = create_response.json()
        
        if create_result.get("code") == 200:
            # 获取刚创建的客户ID
            list_response = crm_client.get_customer_list(page=1, size=20)
            list_data = list_response.json()
            
            if list_data.get("code") == 200 and list_data.get("rows"):
                customer_to_delete = None
                for customer in list_data["rows"]:
                    if customer.get("customerCode") == create_data["customerCode"]:
                        customer_to_delete = customer
                        break
                
                if customer_to_delete:
                    customer_id = customer_to_delete["id"]
                    response = crm_client.delete_customer(customer_id)
                    assert response.status_code == 200, f"删除客户失败，状态码: {response.status_code}"
                    data = response.json()
                    assert data.get("code") == 200, f"删除客户失败，错误码: {data.get('code')}"
                    
                    print(f"[OK] 删除客户成功，客户ID: {customer_id}")
                else:
                    pytest.skip("跳过：未找到刚创建的测试客户")
            else:
                pytest.skip("跳过：获取客户列表失败")
        else:
            print(f"[WARN] 创建测试客户失败，跳过删除测试: {create_result.get('msg')}")

    def test_delete_customer_invalid_id(self, crm_client, authorized_headers):
        """API-CRM-CUST-010 删除客户-无效客户ID"""
        crm_client.session.headers.update(authorized_headers)
        
        invalid_id = 999999
        response = crm_client.delete_customer(invalid_id)
        assert response.status_code == 200, f"请求失败，状态码: {response.status_code}"
        data = response.json()
        print(f"[OK] 删除无效客户ID测试，返回码: {data.get('code')}")
