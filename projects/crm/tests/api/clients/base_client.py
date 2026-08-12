import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../../../.env'))


class BaseClient:
    def __init__(self):
        self.base_url = os.getenv('API_BASE_URL', 'http://192.168.2.97:6089/prod-api')
        self.session = requests.Session()
        self.timeout = int(os.getenv('API_TIMEOUT_SECONDS', 10))
        self.api_username = os.getenv('API_USERNAME', 'ZhaoShengYao')
        self.api_password = os.getenv('API_PASSWORD', 'V+GwtuX+DsY4rxGNZ9hZSg==')
        self.api_client_id = os.getenv('API_CLIENT_ID', 'e5cd7e4891bf95d1d19206ce24a7b32e')
        self._auth_token = None

    def _login(self):
        if self._auth_token:
            return
        
        login_url = f"{self.base_url}/auth/login"
        payload = {
            "username": self.api_username,
            "password": self.api_password,
            "clientId": self.api_client_id,
            "grant_type": "password",
            "grantType": "password"
        }
        
        response = self.session.post(login_url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        
        data = response.json()
        self._auth_token = data.get("data", {}).get("access_token")
        
        if self._auth_token:
            self.session.headers.update({
                "Authorization": f"Bearer {self._auth_token}",
                "clientid": self.api_client_id
            })
        else:
            raise Exception("登录失败，未能获取令牌")

    def request(self, method: str, endpoint: str, **kwargs):
        if not self._auth_token:
            self._login()
            
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault('timeout', self.timeout)
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            if response.status_code == 401:
                self._auth_token = None
                self._login()
                response = self.session.request(method, url, **kwargs)
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            raise