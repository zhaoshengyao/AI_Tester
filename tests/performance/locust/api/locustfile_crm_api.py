from locust import HttpUser, task, between, events
import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.auth_helper import get_auth_token, get_env_config
from utils.test_data_loader import load_test_data, get_api_base_url
from utils.crm_helpers import (
    generate_name, track_resource, safe_get, assert_api_success,
    get_valid_id, cleanup_all_tracked, create_test_clue,
    transform_clue_to_customer, create_test_contact, create_test_business,
    advance_business_stage, create_test_quotation, approve_quotation,
    win_business, lose_business, get_public_pool_list, claim_from_pool
)


class CRMApiUser(HttpUser):
    """CRM API 全量压测用户 - 覆盖所有核心接口"""
    
    host = os.getenv("API_BASE_URL", get_api_base_url())
    wait_time = between(1, 3)
    
    def on_start(self):
        token = get_auth_token(self.client)
        self.client.headers.update({"Authorization": f"Bearer {token}"})
    
    def on_stop(self):
        cleanup_all_tracked(self.client)
    
    # ============ 客户管理 ============
    
    @task(5)
    def query_customer_list(self):
        self.client.get("/crm/customer/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(3)
    def query_customer_detail(self):
        customer_id = get_valid_id(self.client, "customer")
        if customer_id:
            self.client.get(f"/crm/customer/{customer_id}")
    
    @task(2)
    def create_customer(self):
        test_data = load_test_data("customer")
        test_data["customerName"] = generate_name("客户")
        resp = self.client.post("/crm/customer", json=test_data)
        assert_api_success(resp, "create_customer")
    
    # ============ 商机管理 ============
    
    @task(4)
    def query_business_list(self):
        self.client.get("/crm/business/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(2)
    def query_business_detail(self):
        business_id = get_valid_id(self.client, "business")
        if business_id:
            self.client.get(f"/crm/business/{business_id}")
    
    @task(1)
    def create_business(self):
        customer_id = get_valid_id(self.client, "customer")
        if customer_id:
            create_test_business(self.client, customer_id)
    
    # ============ 线索管理 ============
    
    @task(3)
    def query_clue_list(self):
        self.client.get("/crm/clue/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(1)
    def query_clue_detail(self):
        clue_id = get_valid_id(self.client, "clue")
        if clue_id:
            self.client.get(f"/crm/clue/{clue_id}")
    
    # ============ 联系人管理 ============
    
    @task(1)
    def query_contact_list(self):
        self.client.get("/crm/contact/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(1)
    def query_contact_detail(self):
        contact_id = get_valid_id(self.client, "contact")
        if contact_id:
            self.client.get(f"/crm/contact/{contact_id}")
    
    # ============ 报价单管理 ============
    
    @task(2)
    def query_quotation_list(self):
        self.client.get("/crm/quotation/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(1)
    def query_quotation_detail(self):
        quotation_id = get_valid_id(self.client, "quotation")
        if quotation_id:
            self.client.get(f"/crm/quotation/{quotation_id}")
    
    @task(1)
    def create_and_approve_quotation(self):
        business_id = get_valid_id(self.client, "business")
        if business_id:
            quotation = create_test_quotation(self.client, business_id)
            if quotation:
                approve_quotation(self.client, quotation["id"])
    
    # ============ 公海池管理 ============
    
    @task(2)
    def query_public_pool(self):
        self.client.get("/crm/customer/page", params={
            "pageNum": 1, "pageSize": 10, "isQueryPool": "true"
        })
    
    @task(1)
    def claim_from_public_pool(self):
        resp = get_public_pool_list(self.client, page=1, size=1)
        rows = safe_get(resp, "data.rows", [])
        if rows:
            customer_id = rows[0].get("id")
            if customer_id:
                claim_from_pool(self.client, customer_id)
    
    # ============ 目标管理 ============
    
    @task(1)
    def query_goal_list(self):
        self.client.get("/crm/goal/page", params={"pageNum": 1, "pageSize": 10})
    
    # ============ 待办事项 ============
    
    @task(1)
    def query_todo_list(self):
        self.client.get("/crm/todo/page", params={"pageNum": 1, "pageSize": 10})
    
    # ============ 产品管理 ============
    
    @task(1)
    def query_product_list(self):
        self.client.get("/crm/product/page", params={"pageNum": 1, "pageSize": 10})


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("\n📊 CRM API 压测完成")