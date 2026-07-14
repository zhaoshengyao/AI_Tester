import pytest


@pytest.mark.smoke
def test_get_customer_list(crm_client, authorized_headers):
    """API-CRM-001 获取客户列表"""
    crm_client.session.headers.update(authorized_headers)
    response = crm_client.get_customer_list(page=1, size=10)
    assert response.status_code == 200, f"获取客户列表失败，状态码: {response.status_code}"
    data = response.json()
    assert data.get("code") == 200, f"获取客户列表失败，错误码: {data.get('code')}"
    assert "total" in data, "响应中缺少total字段"
    assert "rows" in data, "响应中缺少rows字段"
    print(f"获取客户列表成功，总数: {data.get('total', 0)}")


@pytest.mark.smoke
def test_get_customer_simple_list(crm_client, authorized_headers):
    """API-CRM-002 获取客户简单列表"""
    crm_client.session.headers.update(authorized_headers)
    response = crm_client.get_customer_simple_list()
    assert response.status_code == 200, f"获取客户简单列表失败，状态码: {response.status_code}"
    data = response.json()
    assert data.get("code") == 200, f"获取客户简单列表失败，错误码: {data.get('code')}"
    print("获取客户简单列表成功")


@pytest.mark.smoke
def test_get_clue_simple_list(crm_client, authorized_headers):
    """API-CRM-003 获取线索简单列表"""
    crm_client.session.headers.update(authorized_headers)
    response = crm_client.get_clue_simple_list()
    assert response.status_code == 200, f"获取线索简单列表失败，状态码: {response.status_code}"
    data = response.json()
    assert data.get("code") == 200, f"获取线索简单列表失败，错误码: {data.get('code')}"
    print("获取线索简单列表成功")


@pytest.mark.smoke
def test_get_contact_simple_list(crm_client, authorized_headers):
    """API-CRM-004 获取联系人简单列表"""
    crm_client.session.headers.update(authorized_headers)
    response = crm_client.get_contact_simple_list()
    assert response.status_code == 200, f"获取联系人简单列表失败，状态码: {response.status_code}"
    data = response.json()
    assert data.get("code") == 200, f"获取联系人简单列表失败，错误码: {data.get('code')}"
    print("获取联系人简单列表成功")


@pytest.mark.smoke
def test_get_business_simple_list(crm_client, authorized_headers):
    """API-CRM-005 获取商机简单列表"""
    crm_client.session.headers.update(authorized_headers)
    response = crm_client.get_business_simple_list()
    assert response.status_code == 200, f"获取商机简单列表失败，状态码: {response.status_code}"
    data = response.json()
    assert data.get("code") == 200, f"获取商机简单列表失败，错误码: {data.get('code')}"
    print("获取商机简单列表成功")


def test_get_dict_data_customer_source(crm_client, authorized_headers):
    """API-CRM-006 获取客户来源字典"""
    crm_client.session.headers.update(authorized_headers)
    response = crm_client.get_dict_data("crm_customer_source")
    assert response.status_code == 200, f"获取客户来源字典失败，状态码: {response.status_code}"
    data = response.json()
    assert data.get("code") == 200, f"获取客户来源字典失败，错误码: {data.get('code')}"
    print("获取客户来源字典成功")


def test_get_dict_data_customer_level(crm_client, authorized_headers):
    """API-CRM-007 获取客户级别字典"""
    crm_client.session.headers.update(authorized_headers)
    response = crm_client.get_dict_data("crm_customer_level")
    assert response.status_code == 200, f"获取客户级别字典失败，状态码: {response.status_code}"
    data = response.json()
    assert data.get("code") == 200, f"获取客户级别字典失败，错误码: {data.get('code')}"
    print("获取客户级别字典成功")


def test_get_dict_data_clue_source(crm_client, authorized_headers):
    """API-CRM-008 获取线索来源字典"""
    crm_client.session.headers.update(authorized_headers)
    response = crm_client.get_dict_data("crm_clue_source")
    assert response.status_code == 200, f"获取线索来源字典失败，状态码: {response.status_code}"
    data = response.json()
    assert data.get("code") == 200, f"获取线索来源字典失败，错误码: {data.get('code')}"
    print("获取线索来源字典成功")


def test_get_customer_list_pagination(crm_client, authorized_headers):
    """API-CRM-009 客户列表分页测试"""
    crm_client.session.headers.update(authorized_headers)
    
    # 测试不同分页参数
    for page in [1, 2]:
        for size in [5, 10, 20]:
            response = crm_client.get_customer_list(page=page, size=size)
            assert response.status_code == 200, f"分页测试失败 page={page}, size={size}"
            data = response.json()
            assert data.get("code") == 200, f"分页测试失败，错误码: {data.get('code')}"
    
    print("客户列表分页测试通过")


def test_get_customer_list_with_filter(crm_client, authorized_headers):
    """API-CRM-010 客户列表筛选测试"""
    crm_client.session.headers.update(authorized_headers)
    
    # 测试带用户ID筛选
    response = crm_client.get_customer_list(page=1, size=10, owner_user_id=1)
    assert response.status_code == 200, f"筛选测试失败，状态码: {response.status_code}"
    data = response.json()
    assert data.get("code") == 200, f"筛选测试失败，错误码: {data.get('code')}"
    print("客户列表筛选测试通过")
