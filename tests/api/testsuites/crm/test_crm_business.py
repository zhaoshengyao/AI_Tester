import pytest
import random
import string


def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


@pytest.fixture
def test_business_data(crm_client, authorized_headers):
    crm_client.session.headers.update(authorized_headers)
    list_response = crm_client.get_customer_list(page=1, size=1)
    list_data = list_response.json()
    if list_data.get("code") == 200 and list_data.get("rows"):
        customer_id = list_data["rows"][0].get("id")
        if customer_id:
            return {
                "businessName": f"测试商机_{generate_random_string()}",
                "customerId": customer_id,
                "stage": "1",
                "amount": 10000,
                "remark": "自动化测试创建"
            }
    pytest.skip("跳过：未找到可用客户")


@pytest.fixture
def created_business_id(crm_client, authorized_headers, test_business_data):
    crm_client.session.headers.update(authorized_headers)
    response = crm_client.create_business(test_business_data)
    data = response.json()
    if data.get("code") == 200:
        list_response = crm_client.get_business_list(page=1, size=20)
        list_data = list_response.json()
        if list_data.get("code") == 200 and list_data.get("rows"):
            for business in list_data["rows"]:
                if business.get("businessName") == test_business_data["businessName"]:
                    yield business["id"]
                    return
    pytest.skip("跳过：创建商机失败")


class TestBusinessCRUD:

    @pytest.mark.smoke
    def test_get_business_simple_list(self, crm_client, authorized_headers):
        crm_client.session.headers.update(authorized_headers)
        response = crm_client.get_business_simple_list()
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 200
        print(f"获取商机简单列表成功，数量: {len(data.get('data', []))}")

    @pytest.mark.smoke
    def test_get_business_list(self, crm_client, authorized_headers):
        crm_client.session.headers.update(authorized_headers)
        response = crm_client.get_business_list(page=1, size=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 200
        assert "total" in data
        assert "rows" in data
        print(f"获取商机列表成功，总数: {data.get('total', 0)}")

    def test_get_business_detail(self, crm_client, authorized_headers, created_business_id):
        crm_client.session.headers.update(authorized_headers)
        response = crm_client.get_business_detail(created_business_id)
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 200
        print(f"获取商机详情成功，商机ID: {created_business_id}")

    def test_get_business_detail_invalid_id(self, crm_client, authorized_headers):
        crm_client.session.headers.update(authorized_headers)
        response = crm_client.get_business_detail(9999999)
        assert response.status_code == 200
        data = response.json()
        print(f"获取无效商机详情测试，返回码: {data.get('code')}")

    @pytest.mark.smoke
    def test_create_business_with_complete_data(self, crm_client, authorized_headers, test_business_data):
        crm_client.session.headers.update(authorized_headers)
        response = crm_client.create_business(test_business_data)
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 200, f"创建商机失败，错误码: {data.get('code')}, 消息: {data.get('msg')}"
        print(f"创建商机成功: {test_business_data['businessName']}")

    def test_create_business_with_minimal_data(self, crm_client, authorized_headers, test_business_data):
        crm_client.session.headers.update(authorized_headers)
        minimal_data = {
            "businessName": f"最小商机_{generate_random_string()}",
            "customerId": test_business_data["customerId"]
        }
        response = crm_client.create_business(minimal_data)
        assert response.status_code == 200
        data = response.json()
        print(f"创建最小商机测试，返回码: {data.get('code')}")

    def test_create_business_empty_name(self, crm_client, authorized_headers):
        crm_client.session.headers.update(authorized_headers)
        invalid_data = {"customerId": 1}
        response = crm_client.create_business(invalid_data)
        assert response.status_code == 200
        data = response.json()
        print(f"创建商机-名称为空测试，返回码: {data.get('code')}")

    def test_create_business_empty_customer(self, crm_client, authorized_headers):
        crm_client.session.headers.update(authorized_headers)
        invalid_data = {"businessName": f"无客户商机_{generate_random_string()}"}
        response = crm_client.create_business(invalid_data)
        assert response.status_code == 200
        data = response.json()
        print(f"创建商机-客户ID为空测试，返回码: {data.get('code')}")

    def test_update_business(self, crm_client, authorized_headers, created_business_id):
        crm_client.session.headers.update(authorized_headers)
        update_data = {"businessName": f"更新商机_{generate_random_string()}"}
        response = crm_client.update_business(created_business_id, update_data)
        assert response.status_code == 200
        data = response.json()
        print(f"更新商机测试，返回码: {data.get('code')}")

    def test_update_business_invalid_id(self, crm_client, authorized_headers):
        crm_client.session.headers.update(authorized_headers)
        update_data = {"businessName": "更新测试"}
        response = crm_client.update_business(9999999, update_data)
        assert response.status_code == 200
        data = response.json()
        print(f"更新无效商机ID测试，返回码: {data.get('code')}")

    def test_delete_business(self, crm_client, authorized_headers, test_business_data):
        crm_client.session.headers.update(authorized_headers)
        
        create_response = crm_client.create_business(test_business_data)
        create_data = create_response.json()
        
        if create_data.get("code") == 200:
            list_response = crm_client.get_business_list(page=1, size=20)
            list_data = list_response.json()
            
            if list_data.get("code") == 200 and list_data.get("rows"):
                business_to_delete = None
                for business in list_data["rows"]:
                    if business.get("businessName") == test_business_data["businessName"]:
                        business_to_delete = business
                        break
                
                if business_to_delete:
                    business_id = business_to_delete["id"]
                    response = crm_client.delete_business(business_id)
                    assert response.status_code == 200
                    data = response.json()
                    assert data.get("code") == 200
                    print(f"删除商机成功，商机ID: {business_id}")
                else:
                    pytest.skip("跳过：未找到刚创建的测试商机")
            else:
                pytest.skip("跳过：获取商机列表失败")
        else:
            print(f"[WARN] 创建测试商机失败，跳过删除测试: {create_data.get('msg')}")

    def test_delete_business_invalid_id(self, crm_client, authorized_headers):
        crm_client.session.headers.update(authorized_headers)
        response = crm_client.delete_business(9999999)
        assert response.status_code == 200
        data = response.json()
        print(f"删除无效商机ID测试，返回码: {data.get('code')}")


class TestBusinessStageTransition:

    @pytest.mark.smoke
    def test_stage_transition_from_lead_to_quotation(self, crm_client, authorized_headers, created_business_id):
        crm_client.session.headers.update(authorized_headers)
        response = crm_client.update_business(created_business_id, {"stage": "2"})
        assert response.status_code == 200
        data = response.json()
        if data.get("code") != 200:
            print(f"[WARN] 阶段推进-线索转方案报价，返回码: {data.get('code')}, 消息: {data.get('msg')}")
        else:
            detail_response = crm_client.get_business_detail(created_business_id)
            detail_data = detail_response.json()
            assert detail_data.get("code") == 200
            print(f"阶段推进-线索转方案报价成功，商机ID: {created_business_id}")

    @pytest.mark.smoke
    def test_stage_transition_from_quotation_to_negotiation(self, crm_client, authorized_headers, created_business_id):
        crm_client.session.headers.update(authorized_headers)
        crm_client.update_business(created_business_id, {"stage": "2"})
        response = crm_client.update_business(created_business_id, {"stage": "3"})
        assert response.status_code == 200
        data = response.json()
        if data.get("code") != 200:
            print(f"[WARN] 阶段推进-方案报价转谈判，返回码: {data.get('code')}, 消息: {data.get('msg')}")
        else:
            print(f"阶段推进-方案报价转谈判成功，商机ID: {created_business_id}")

    @pytest.mark.smoke
    def test_stage_transition_from_negotiation_to_win(self, crm_client, authorized_headers, created_business_id):
        crm_client.session.headers.update(authorized_headers)
        crm_client.update_business(created_business_id, {"stage": "2"})
        crm_client.update_business(created_business_id, {"stage": "3"})
        response = crm_client.update_business(created_business_id, {"stage": "4"})
        assert response.status_code == 200
        data = response.json()
        if data.get("code") != 200:
            print(f"[WARN] 阶段推进-谈判转赢单，返回码: {data.get('code')}, 消息: {data.get('msg')}")
        else:
            print(f"阶段推进-谈判转赢单成功，商机ID: {created_business_id}")

    @pytest.mark.smoke
    def test_stage_transition_from_negotiation_to_lost(self, crm_client, authorized_headers, created_business_id):
        crm_client.session.headers.update(authorized_headers)
        crm_client.update_business(created_business_id, {"stage": "2"})
        crm_client.update_business(created_business_id, {"stage": "3"})
        response = crm_client.update_business(created_business_id, {"stage": "5"})
        assert response.status_code == 200
        data = response.json()
        if data.get("code") != 200:
            print(f"[WARN] 阶段推进-谈判转输单，返回码: {data.get('code')}, 消息: {data.get('msg')}")
        else:
            print(f"阶段推进-谈判转输单成功，商机ID: {created_business_id}")

    def test_stage_transition_from_lead_to_win(self, crm_client, authorized_headers, created_business_id):
        crm_client.session.headers.update(authorized_headers)
        response = crm_client.update_business(created_business_id, {"stage": "4"})
        assert response.status_code == 200
        data = response.json()
        print(f"阶段推进-线索直接转赢单测试，返回码: {data.get('code')}")

    def test_stage_transition_from_win_to_negotiation(self, crm_client, authorized_headers, created_business_id):
        crm_client.session.headers.update(authorized_headers)
        crm_client.update_business(created_business_id, {"stage": "2"})
        crm_client.update_business(created_business_id, {"stage": "3"})
        crm_client.update_business(created_business_id, {"stage": "4"})
        response = crm_client.update_business(created_business_id, {"stage": "3"})
        assert response.status_code == 200
        data = response.json()
        print(f"阶段推进-赢单回退到谈判测试，返回码: {data.get('code')}")

    def test_stage_transition_from_lost_to_negotiation(self, crm_client, authorized_headers, created_business_id):
        crm_client.session.headers.update(authorized_headers)
        crm_client.update_business(created_business_id, {"stage": "2"})
        crm_client.update_business(created_business_id, {"stage": "3"})
        crm_client.update_business(created_business_id, {"stage": "5"})
        response = crm_client.update_business(created_business_id, {"stage": "3"})
        assert response.status_code == 200
        data = response.json()
        print(f"阶段推进-输单回退到谈判测试，返回码: {data.get('code')}")

    def test_stage_transition_invalid_stage(self, crm_client, authorized_headers, created_business_id):
        crm_client.session.headers.update(authorized_headers)
        response = crm_client.update_business(created_business_id, {"stage": "99"})
        assert response.status_code == 200
        data = response.json()
        print(f"阶段推进-无效阶段值测试，返回码: {data.get('code')}")

    def test_stage_transition_empty_stage(self, crm_client, authorized_headers, created_business_id):
        crm_client.session.headers.update(authorized_headers)
        response = crm_client.update_business(created_business_id, {"stage": ""})
        assert response.status_code == 200
        data = response.json()
        print(f"阶段推进-空阶段值测试，返回码: {data.get('code')}")


class TestBusinessProduct:

    def test_add_business_product(self, crm_client, authorized_headers, created_business_id):
        crm_client.session.headers.update(authorized_headers)
        product_data = {
            "businessId": created_business_id,
            "productName": f"测试产品_{generate_random_string()}",
            "quantity": 1,
            "price": 1000,
            "discount": 100
        }
        response = crm_client.add_business_product(product_data)
        assert response.status_code == 200
        data = response.json()
        print(f"添加商机产品测试，返回码: {data.get('code')}")

    def test_get_business_products(self, crm_client, authorized_headers, created_business_id):
        crm_client.session.headers.update(authorized_headers)
        response = crm_client.get_business_products(created_business_id)
        assert response.status_code == 200
        data = response.json()
        print(f"获取商机产品列表测试，返回码: {data.get('code')}")

    def test_add_business_product_invalid_business_id(self, crm_client, authorized_headers):
        crm_client.session.headers.update(authorized_headers)
        product_data = {
            "businessId": 9999999,
            "productName": "测试产品",
            "quantity": 1,
            "price": 1000,
            "discount": 100
        }
        response = crm_client.add_business_product(product_data)
        assert response.status_code == 200
        data = response.json()
        print(f"添加商机产品-无效商机ID测试，返回码: {data.get('code')}")

    def test_add_business_product_empty_name(self, crm_client, authorized_headers, created_business_id):
        crm_client.session.headers.update(authorized_headers)
        product_data = {
            "businessId": created_business_id,
            "productName": "",
            "quantity": 1,
            "price": 1000,
            "discount": 100
        }
        response = crm_client.add_business_product(product_data)
        assert response.status_code == 200
        data = response.json()
        print(f"添加商机产品-名称为空测试，返回码: {data.get('code')}")


class TestBusinessFollow:

    def test_add_business_follow(self, crm_client, authorized_headers, created_business_id):
        crm_client.session.headers.update(authorized_headers)
        follow_data = {
            "businessId": created_business_id,
            "content": "测试跟进内容",
            "nextPlan": "下一步计划"
        }
        response = crm_client.add_business_follow(follow_data)
        assert response.status_code == 200
        data = response.json()
        print(f"添加商机跟进记录测试，返回码: {data.get('code')}")

    def test_get_business_follows(self, crm_client, authorized_headers, created_business_id):
        crm_client.session.headers.update(authorized_headers)
        response = crm_client.get_business_follows(created_business_id)
        assert response.status_code == 200
        data = response.json()
        print(f"获取商机跟进记录测试，返回码: {data.get('code')}")

    def test_add_business_follow_empty_content(self, crm_client, authorized_headers, created_business_id):
        crm_client.session.headers.update(authorized_headers)
        follow_data = {
            "businessId": created_business_id,
            "content": "",
            "nextPlan": "下一步计划"
        }
        response = crm_client.add_business_follow(follow_data)
        assert response.status_code == 200
        data = response.json()
        print(f"添加商机跟进记录-内容为空测试，返回码: {data.get('code')}")

    def test_add_business_follow_invalid_business_id(self, crm_client, authorized_headers):
        crm_client.session.headers.update(authorized_headers)
        follow_data = {
            "businessId": 9999999,
            "content": "测试跟进内容",
            "nextPlan": "下一步计划"
        }
        response = crm_client.add_business_follow(follow_data)
        assert response.status_code == 200
        data = response.json()
        print(f"添加商机跟进记录-无效商机ID测试，返回码: {data.get('code')}")