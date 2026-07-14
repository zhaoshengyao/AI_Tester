import os
import base64
import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def get_env_config(key, default=None):
    return os.environ.get(key, default)

def encrypt_password(password, key):
    backend = default_backend()
    cipher = Cipher(algorithms.AES(key.encode('utf-8')), modes.ECB(), backend=backend)
    encryptor = cipher.encryptor()
    
    padding_length = 16 - (len(password) % 16)
    padded_password = password + chr(padding_length) * padding_length
    
    encrypted = encryptor.update(padded_password.encode('utf-8')) + encryptor.finalize()
    return base64.b64encode(encrypted).decode('utf-8')

def is_encrypted(password):
    if not password:
        return False
    return '=' in password and len(password) > 20

def get_encrypted_password():
    password = get_env_config("API_PASSWORD", "")
    test_password = get_env_config("TEST_PASSWORD", "123456")
    client_id = get_env_config("API_CLIENT_ID", "e5cd7e4891bf95d1d19206ce24a7b32e")
    
    if is_encrypted(password):
        return password
    else:
        return encrypt_password(test_password, client_id)

def get_auth_token(client=None):
    username = get_env_config("API_USERNAME", get_env_config("TEST_USERNAME", "ZhaoShengYao"))
    encrypted_password = get_encrypted_password()
    client_id = get_env_config("API_CLIENT_ID", "e5cd7e4891bf95d1d19206ce24a7b32e")
    
    payload = {
        "username": username,
        "password": encrypted_password,
        "clientId": client_id,
        "grant_type": "password",
        "grantType": "password"
    }
    
    try:
        if client is None:
            api_base_url = get_env_config("API_BASE_URL", "http://192.168.2.97:6089/prod-api")
            login_url = f"{api_base_url}/auth/login"
            response = requests.post(login_url, json=payload, timeout=10)
        else:
            response = client.post("/auth/login", json=payload)
        
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == 200 or data.get("code") == 0:
            token = data.get("data", {}).get("token")
            if token:
                return token
            access_token = data.get("data", {}).get("accessToken") or data.get("data", {}).get("access_token")
            if access_token:
                return access_token
            refresh_token = data.get("data", {}).get("refreshToken") or data.get("data", {}).get("refresh_token")
            if refresh_token:
                return refresh_token
        
        token = data.get("access_token") or data.get("token")
        if token:
            return token
        
        raise Exception(f"Login failed: {data}")
    except Exception as e:
        raise Exception(f"Authentication failed: {str(e)}")
