from locust import HttpUser, task, between
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.auth_helper import get_auth_token
from utils.test_data_loader import get_api_base_url

class CRMApiSmokeUser(HttpUser):
    """CRM API 冒烟压测用户"""
    
    host = os.getenv("API_BASE_URL", get_api_base_url())
    wait_time = between(1, 3)
    
    def on_start(self):
        token = get_auth_token(self.client)
        self.client.headers.update({"Authorization": f"Bearer {token}"})
    
    @task(5)
    def test_customer_list(self):
        """高频：查询客户列表"""
        self.client.get("/crm/customer/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(3)
    def test_business_list(self):
        """中频：查询商机列表"""
        self.client.get("/crm/business/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(2)
    def test_clue_list(self):
        """低频：查询线索列表"""
        self.client.get("/crm/clue/page", params={"pageNum": 1, "pageSize": 10})