import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../../../../.env'))


_token_cache = None


def get_env_config(key: str, default: str = None) -> str:
    """获取环境变量配置"""
    return os.getenv(key, default)


def get_auth_token() -> str:
    """获取认证Token"""
    global _token_cache
    
    if _token_cache:
        return _token_cache
    
    base_url = get_env_config('API_BASE_URL', 'http://192.168.2.97:6089/prod-api')
    username = get_env_config('API_USERNAME', 'ZhaoShengYao')
    password = get_env_config('API_PASSWORD', 'V+GwtuX+DsY4rxGNZ9hZSg==')
    client_id = get_env_config('API_CLIENT_ID', 'e5cd7e4891bf95d1d19206ce24a7b32e')
    
    login_url = f"{base_url}/auth/login"
    payload = {
        "username": username,
        "password": password,
        "clientId": client_id,
        "grant_type": "password",
        "grantType": "password"
    }
    
    response = requests.post(login_url, json=payload, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    token = data.get("data", {}).get("access_token")
    
    if not token:
        raise Exception(f"登录失败: {data.get('msg', '未知错误')}")
    
    _token_cache = token
    return token


def invalidate_token():
    """使Token缓存失效"""
    global _token_cache
    _token_cache = None


def get_authorized_headers() -> dict:
    """获取带认证的请求头"""
    token = get_auth_token()
    client_id = get_env_config('API_CLIENT_ID', 'e5cd7e4891bf95d1d19206ce24a7b32e')
    return {
        "Authorization": f"Bearer {token}",
        "clientid": client_id
    }
