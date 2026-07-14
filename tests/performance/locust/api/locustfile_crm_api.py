from locust import HttpUser, task, between
from utils.auth_helper import get_auth_token
from utils.test_data_loader import load_test_data, get_api_base_url
import random
import os

class CRMApiUser(HttpUser):
    """CRM API 全量压测用户"""
    
    host = os.getenv("API_BASE_URL", get_api_base_url())
    wait_time = between(1, 3)
    
    def on_start(self):
        token = get_auth_token(self.client)
        self.client.headers.update({"Authorization": f"Bearer {token}"})
    
    @task(5)
    def query_customer_list(self):
        """高频：查询客户列表"""
        self.client.get("/crm/customer/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(3)
    def query_customer_detail(self):
        """中频：查看客户详情"""
        customer_id = random.choice([1, 2, 3, 4, 5])
        self.client.get(f"/crm/customer/{customer_id}")
    
    @task(1)
    def create_customer(self):
        """低频：创建客户"""
        test_data = load_test_data("customer")
        self.client.post("/crm/customer", json=test_data)
    
    @task(4)
    def query_business_list(self):
        """高频：查询商机列表"""
        self.client.get("/crm/business/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(2)
    def query_business_detail(self):
        """中频：查看商机详情"""
        business_id = random.choice([1, 2, 3])
        self.client.get(f"/crm/business/{business_id}")
    
    @task(1)
    def create_business(self):
        """低频：创建商机"""
        test_data = load_test_data("business")
        self.client.post("/crm/business", json=test_data)
    
    @task(3)
    def query_clue_list(self):
        """中频：查询线索列表"""
        self.client.get("/crm/clue/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(1)
    def query_contact_list(self):
        """低频：查询联系人列表"""
        self.client.get("/crm/contact/page", params={"pageNum": 1, "pageSize": 10})