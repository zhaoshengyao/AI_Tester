import os
import yaml
import base64
from Crypto.Cipher import AES

def encrypt_password(password, key):
    key_bytes = key.encode('utf-8')
    cipher = AES.new(key_bytes, AES.MODE_ECB)
    padded_password = password + (16 - len(password) % 16) * chr(16 - len(password) % 16)
    encrypted = cipher.encrypt(padded_password.encode('utf-8'))
    return base64.b64encode(encrypted).decode('utf-8')

def get_env_config(env_key, default_value=None):
    """获取环境变量配置，优先读取环境变量，其次从统一配置文件读取"""
    # 优先读取环境变量
    env_value = os.getenv(env_key)
    if env_value is not None:
        return env_value
    
    # 从统一配置文件读取默认值
    config_path = os.path.join(os.path.dirname(__file__), "../../../config/env.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        env_mapping = {
            "BASE_URL": "test.base_url",
            "API_BASE_URL": "test.api_base_url",
            "TEST_USERNAME": "test.username",
            "TEST_PASSWORD": "test.password"
        }
        if env_key in env_mapping:
            keys = env_mapping[env_key].split(".")
            value = config
            for key in keys:
                value = value.get(key)
                if value is None:
                    break
            if value is not None:
                return value
    
    return default_value

def get_auth_token(client):
    """获取认证 Token"""
    username = get_env_config("API_USERNAME", get_env_config("TEST_USERNAME", "ZhaoShengYao"))
    password = get_env_config("API_PASSWORD", "")
    test_password = get_env_config("TEST_PASSWORD", "123456")
    client_id = get_env_config("API_CLIENT_ID", "e5cd7e4891bf95d1d19206ce24a7b32e")
    
    if password and "=" in password and len(password) > 20:
        encrypted_password = password
    else:
        encrypted_password = encrypt_password(test_password, client_id)
    
    response = client.post("/auth/login", json={
        "username": username,
        "password": encrypted_password,
        "clientId": client_id,
        "grant_type": "password",
        "grantType": "password"
    })
    
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token", data.get("token", ""))
    
    raise Exception(f"认证失败，状态码: {response.status_code}, 响应: {response.text}")