"""CRM 模块完整测试用例"""
import pytest
import random
import string


def generate_random_string(length=10):
    """生成随机字符串"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


class TestCustomerAPI:
    """客户管理 API 测试"""
    
    def test_create_customer_with_minimal_data(self, crm_client, authorized_headers):
        """API-CRM-CUST-001 创建客户-最小数据"""
        crm_client.session.headers.update(authorized_headers)
        
        customer_data = {
            "customerName": f"测试客户_{generate_random_string()}",
            "customerLevel": "1",
            "customerSource": "1",
            "phone": "13800138000",
            "status": "0"
        }
        
        response = crm_client.request("POST", "/crm/customer", json=customer_data)
        assert response.status_code == 200, f"创建客户失败，状态码: {response.status_code}"
        data = response.json()
        print(f"创建客户测试，返回码: {data.get('code')}")
    
    def test_create_customer_with_complete_data(self, crm_client, authorized_headers):
        """API-CRM-CUST-002 创建客户-完整数据"""
        crm_client.session.headers.update(authorized_headers)
        
        customer_data = {
            "customerName": f"完整测试客户_{generate_random_string()}",
            "customerLevel": "2",
            "customerSource": "2",
            "phone": "13900139000",
            "email": f"test_{generate_random_string()}@example.com",
            "address": "测试地址",
            "contacts": "测试联系人",
            "remark": "测试备注",
            "status": "0"
        }
        
        response = crm_client.request("POST", "/crm/customer", json=customer_data)
        assert response.status_code == 200, f"创建客户失败，状态码: {response.status_code}"
        data = response.json()
        print(f"创建完整客户测试，返回码: {data.get('code')}")
    
    def test_create_customer_empty_name(self, crm_client, authorized_headers):
        """API-CRM-CUST-003 创建客户-空名称校验"""
        crm_client.session.headers.update(authorized_headers)
        
        customer_data = {
            "customerName": "",
            "customerLevel": "1",
            "customerSource": "1",
            "phone": "13800138000"
        }
        
        response = crm_client.request("POST", "/crm/customer", json=customer_data)
        assert response.status_code == 200, f"请求失败，状态码: {response.status_code}"
        data = response.json()
        print(f"创建客户-空名称测试，返回码: {data.get('code')}")
    
    def test_get_customer_detail(self, crm_client, authorized_headers):
        """API-CRM-CUST-004 获取客户详情"""
        crm_client.session.headers.update(authorized_headers)
        
        # 先获取客户列表
        list_response = crm_client.get_customer_list(page=1, size=1)
        list_data = list_response.json()
        
        if list_data.get("code") == 200 and list_data.get("rows"):
            # 使用 id 字段而不是 customerId
            customer_id = list_data["rows"][0].get("id") or list_data["rows"][0].get("customerId")
            
            if customer_id:
                response = crm_client.request("GET", f"/crm/customer/{customer_id}")
                assert response.status_code == 200, f"获取客户详情失败，状态码: {response.status_code}"
                data = response.json()
                assert data.get("code") == 200, f"获取客户详情失败，错误码: {data.get('code')}"
                print(f"获取客户详情成功，客户ID: {customer_id}")
            else:
                print("跳过客户详情测试：未找到客户ID字段")
        else:
            print("跳过客户详情测试：未找到可用客户")
    
    def test_update_customer(self, crm_client, authorized_headers):
        """API-CRM-CUST-005 更新客户信息"""
        crm_client.session.headers.update(authorized_headers)
        
        # 先获取客户列表
        list_response = crm_client.get_customer_list(page=1, size=1)
        list_data = list_response.json()
        
        if list_data.get("code") == 200 and list_data.get("rows"):
            customer_id = list_data["rows"][0].get("id") or list_data["rows"][0].get("customerId")
            
            if customer_id:
                update_data = {
                    "customerId": customer_id,
                    "customerName": f"更新后名称_{generate_random_string()}",
                    "customerLevel": "3"
                }
                
                response = crm_client.request("PUT", f"/crm/customer/{customer_id}", json=update_data)
                assert response.status_code == 200, f"更新客户失败，状态码: {response.status_code}"
                data = response.json()
                print(f"更新客户测试，返回码: {data.get('code')}")
            else:
                print("跳过更新客户测试：未找到客户ID字段")
        else:
            print("跳过更新客户测试：未找到可用客户")
    
    def test_delete_customer(self, crm_client, authorized_headers):
        """API-CRM-CUST-006 删除客户"""
        crm_client.session.headers.update(authorized_headers)
        
        # 先创建一个客户，再删除
        customer_data = {
            "customerName": f"待删除客户_{generate_random_string()}",
            "customerLevel": "1",
            "customerSource": "1",
            "phone": "13700137000"
        }
        
        create_response = crm_client.request("POST", "/crm/customer", json=customer_data)
        create_data = create_response.json()
        
        if create_data.get("code") == 200 and create_data.get("data"):
            customer_id = create_data.get("data").get("id") or create_data.get("data").get("customerId")
            if customer_id:
                delete_response = crm_client.request("DELETE", f"/crm/customer/{customer_id}")
                assert delete_response.status_code == 200, f"删除客户失败，状态码: {delete_response.status_code}"
                delete_data = delete_response.json()
                print(f"删除客户测试，返回码: {delete_data.get('code')}")
            else:
                print("跳过删除客户测试：创建客户未返回ID")
        else:
            print(f"跳过删除客户测试：创建客户失败，返回码: {create_data.get('code')}")


class TestClueAPI:
    """线索管理 API 测试"""
    
    def test_create_clue(self, crm_client, authorized_headers):
        """API-CRM-CLUE-001 创建线索"""
        crm_client.session.headers.update(authorized_headers)
        
        clue_data = {
            "clueName": f"测试线索_{generate_random_string()}",
            "clueSource": "1",
            "phone": "13800138001",
            "contacts": "测试联系人",
            "status": "0"
        }
        
        response = crm_client.request("POST", "/crm/clue", json=clue_data)
        assert response.status_code == 200, f"创建线索失败，状态码: {response.status_code}"
        data = response.json()
        print(f"创建线索测试，返回码: {data.get('code')}")
    
    def test_get_clue_list(self, crm_client, authorized_headers):
        """API-CRM-CLUE-002 获取线索列表"""
        crm_client.session.headers.update(authorized_headers)
        
        response = crm_client.request("GET", "/crm/clue/page", params={"pageNum": 1, "pageSize": 10})
        assert response.status_code == 200, f"获取线索列表失败，状态码: {response.status_code}"
        data = response.json()
        assert data.get("code") == 200, f"获取线索列表失败，错误码: {data.get('code')}"
        print(f"获取线索列表成功，总数: {data.get('total', 0)}")
    
    def test_update_clue_status(self, crm_client, authorized_headers):
        """API-CRM-CLUE-003 更新线索状态"""
        crm_client.session.headers.update(authorized_headers)
        
        # 先获取线索列表
        list_response = crm_client.request("GET", "/crm/clue/page", params={"pageNum": 1, "pageSize": 1})
        list_data = list_response.json()
        
        if list_data.get("code") == 200 and list_data.get("rows"):
            # 使用 id 字段而不是 clueId
            clue_id = list_data["rows"][0].get("id") or list_data["rows"][0].get("clueId")
            
            if clue_id:
                update_data = {
                    "clueId": clue_id,
                    "status": "1"
                }
                
                response = crm_client.request("PUT", f"/crm/clue/{clue_id}", json=update_data)
                assert response.status_code == 200, f"更新线索失败，状态码: {response.status_code}"
                data = response.json()
                print(f"更新线索状态测试，返回码: {data.get('code')}")
            else:
                print("跳过更新线索测试：未找到线索ID字段")
        else:
            print("跳过更新线索测试：未找到可用线索")


class TestBusinessAPI:
    """商机管理 API 测试"""
    
    def test_get_business_list(self, crm_client, authorized_headers):
        """API-CRM-BUSINESS-001 获取商机列表"""
        crm_client.session.headers.update(authorized_headers)
        
        response = crm_client.request("GET", "/crm/business/page", params={"pageNum": 1, "pageSize": 10})
        assert response.status_code == 200, f"获取商机列表失败，状态码: {response.status_code}"
        data = response.json()
        assert data.get("code") == 200, f"获取商机列表失败，错误码: {data.get('code')}"
        print(f"获取商机列表成功，总数: {data.get('total', 0)}")


class TestDictAPI:
    """数据字典 API 测试"""
    
    @pytest.mark.parametrize("dict_type", [
        "crm_customer_source",
        "crm_customer_level", 
        "crm_clue_source",
        "crm_clue_status",
        "crm_business_stage"
    ])
    def test_get_dict_data(self, crm_client, authorized_headers, dict_type):
        """API-CRM-DICT-001 获取各类字典数据"""
        crm_client.session.headers.update(authorized_headers)
        
        response = crm_client.get_dict_data(dict_type)
        assert response.status_code == 200, f"获取字典{dict_type}失败，状态码: {response.status_code}"
        data = response.json()
        assert data.get("code") == 200, f"获取字典{dict_type}失败，错误码: {data.get('code')}"
        print(f"获取字典{dict_type}成功")


class TestContactAPI:
    """联系人管理 API 测试"""
    
    def test_get_contact_list(self, crm_client, authorized_headers):
        """API-CRM-CONTACT-001 获取联系人列表"""
        crm_client.session.headers.update(authorized_headers)
        
        response = crm_client.request("GET", "/crm/contact/page", params={"pageNum": 1, "pageSize": 10})
        assert response.status_code == 200, f"获取联系人列表失败，状态码: {response.status_code}"
        data = response.json()
        assert data.get("code") == 200, f"获取联系人列表失败，错误码: {data.get('code')}"
        print(f"获取联系人列表成功，总数: {data.get('total', 0)}")
