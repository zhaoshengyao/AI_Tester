from locust import HttpUser, task, between, events
import sys
import os
import random
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.test_data_loader import get_api_base_url
from utils.crm_helpers import (
    safe_get, assert_api_success, get_valid_id,
    get_public_pool_list, get_or_refresh_token
)


class CRMApiSmokeUser(HttpUser):
    """CRM API 冒烟压测用户 - 覆盖核心高频接口"""
    
    host = os.getenv("API_BASE_URL", get_api_base_url())
    wait_time = between(1, 2)
    
    def on_start(self):
        time.sleep(random.uniform(0.3, 2.0))
        token = get_or_refresh_token(self)
        if not token:
            self.environment.runner.quit()
    
    def _ensure_token(self):
        if not hasattr(self, 'token_expire_time') or self.token_expire_time < time.time():
            token = get_or_refresh_token(self, force_refresh=True)
            if token:
                pass
    
    # ============ 客户接口 ============
    
    @task(5)
    def query_customer_list(self):
        self._ensure_token()
        self.client.get("/crm/customer/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(3)
    def query_customer_detail(self):
        self._ensure_token()
        customer_id = get_valid_id(self.client, "customer")
        if customer_id:
            self.client.get(f"/crm/customer/{customer_id}")
    
    # ============ 商机接口 ============
    
    @task(4)
    def query_business_list(self):
        self._ensure_token()
        self.client.get("/crm/business/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(2)
    def query_business_detail(self):
        self._ensure_token()
        business_id = get_valid_id(self.client, "business")
        if business_id:
            self.client.get(f"/crm/business/{business_id}")
    
    # ============ 线索接口 ============
    
    @task(3)
    def query_clue_list(self):
        self._ensure_token()
        self.client.get("/crm/clue/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(2)
    def query_clue_detail(self):
        self._ensure_token()
        clue_id = get_valid_id(self.client, "clue")
        if clue_id:
            self.client.get(f"/crm/clue/{clue_id}")
    
    # ============ 联系人接口 ============
    
    @task(2)
    def query_contact_list(self):
        self._ensure_token()
        self.client.get("/crm/contact/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(1)
    def query_contact_detail(self):
        self._ensure_token()
        contact_id = get_valid_id(self.client, "contact")
        if contact_id:
            self.client.get(f"/crm/contact/{contact_id}")
    
    # ============ 报价单接口 ============
    
    @task(2)
    def query_quotation_list(self):
        self._ensure_token()
        self.client.get("/crm/quotation/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(1)
    def query_quotation_detail(self):
        self._ensure_token()
        quotation_id = get_valid_id(self.client, "quotation")
        if quotation_id:
            self.client.get(f"/crm/quotation/{quotation_id}")
    
    # ============ 公海池接口 ============
    
    @task(2)
    def query_public_pool(self):
        self._ensure_token()
        self.client.get("/crm/customer/page", params={
            "pageNum": 1, "pageSize": 10, "isQueryPool": "true"
        })
    
    # ============ 其他接口 ============
    
    @task(1)
    def query_goal_list(self):
        self._ensure_token()
        self.client.get("/crm/goal/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(1)
    def query_todo_list(self):
        self._ensure_token()
        self.client.get("/crm/todo/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(1)
    def query_product_list(self):
        self._ensure_token()
        self.client.get("/crm/product/page", params={"pageNum": 1, "pageSize": 10})


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("\n✅ CRM API 冒烟压测完成")