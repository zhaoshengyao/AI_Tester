import os
import sys
import pytest
from dotenv import load_dotenv
from clients.crm_client import CrmClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

from utils.auth import get_env_config, get_auth_token
from utils.test_data_manager import get_test_data_manager


@pytest.fixture(scope="session")
def api_base_url():
    return get_env_config('API_BASE_URL', 'http://192.168.2.97:6089/prod-api')


@pytest.fixture(scope="session")
def test_username():
    return get_env_config('TEST_USERNAME', 'ZhaoShengYao')


@pytest.fixture(scope="session")
def test_password():
    return get_env_config('TEST_PASSWORD', '123456')


@pytest.fixture(scope="session")
def api_username():
    return get_env_config('API_USERNAME', 'ZhaoShengYao')


@pytest.fixture(scope="session")
def api_password():
    return get_env_config('API_PASSWORD', '123456')


@pytest.fixture(scope="session")
def api_client_id():
    return get_env_config('API_CLIENT_ID', 'e5cd7e4891bf95d1d19206ce24a7b32e')


@pytest.fixture(scope="session")
def authorized_headers(api_client_id):
    try:
        token = get_auth_token()
        return {"Authorization": f"Bearer {token}", "clientid": api_client_id}
    except Exception as e:
        print(f"登录失败: {e}")
        pytest.skip(f"登录失败，跳过测试: {e}")


@pytest.fixture(scope="session")
def crm_client():
    return CrmClient()


@pytest.fixture(scope="session")
def test_data_manager(api_base_url, authorized_headers):
    token = authorized_headers.get('Authorization', '').replace('Bearer ', '')
    manager = get_test_data_manager(api_base_url, token)
    yield manager
    manager.cleanup_created_data()
