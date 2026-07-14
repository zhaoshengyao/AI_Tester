import os
import pytest
import requests
from dotenv import load_dotenv
from clients.crm_client import CrmClient

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))


@pytest.fixture(scope="session")
def api_base_url():
    return os.getenv('API_BASE_URL', 'http://192.168.2.97:6089/prod-api')


@pytest.fixture(scope="session")
def test_username():
    return os.getenv('TEST_USERNAME', 'ZhaoShengYao')


@pytest.fixture(scope="session")
def test_password():
    return os.getenv('TEST_PASSWORD', '123456')


@pytest.fixture(scope="session")
def api_username():
    return os.getenv('API_USERNAME', 'ZhaoShengYao')


@pytest.fixture(scope="session")
def api_password():
    return os.getenv('API_PASSWORD', '123456')


@pytest.fixture(scope="session")
def api_client_id():
    return os.getenv('API_CLIENT_ID', 'e5cd7e4891bf95d1d19206ce24a7b32e')


@pytest.fixture(scope="session")
def authorized_headers(api_base_url, api_username, api_password, api_client_id):
    login_url = f"{api_base_url}/auth/login"
    payload = {
        "username": api_username,
        "password": api_password,
        "clientId": api_client_id,
        "grant_type": "password",
        "grantType": "password"
    }
    
    try:
        response = requests.post(login_url, json=payload, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print(f"Login response code: {data.get('code')}")
        
        token = data.get("data", {}).get("access_token") or data.get("access_token") or data.get("token")
        
        if token:
            return {"Authorization": f"Bearer {token}", "clientid": api_client_id}
        else:
            print(f"Login response: {data}")
            pytest.skip("未能获取登录令牌")
    except Exception as e:
        print(f"登录失败: {e}")
        pytest.skip(f"登录失败，跳过测试: {e}")


@pytest.fixture(scope="session")
def crm_client():
    return CrmClient()