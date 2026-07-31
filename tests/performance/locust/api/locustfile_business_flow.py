from locust import HttpUser, task, between, events
import os
import sys
import random
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.auth_helper import get_auth_token, get_env_config
from utils.test_data_loader import get_api_base_url
from utils.crm_helpers import (
    generate_name, track_resource, safe_get, assert_api_success,
    get_valid_id, create_test_clue, transform_clue_to_customer,
    create_test_contact, create_test_business, advance_business_stage,
    create_test_quotation, approve_quotation, win_business, lose_business,
    get_public_pool_list, claim_from_pool, cleanup_all_tracked,
    get_or_refresh_token
)


class CRMBusinessFlowUser(HttpUser):
    """CRM 完整业务流程压测用户"""
    
    host = os.getenv("API_BASE_URL", get_api_base_url())
    wait_time = between(2, 5)
    
    def on_start(self):
        token = get_auth_token(self.client)
        self.client.headers.update({"Authorization": f"Bearer {token}"})
        self.business_context = {}
    
    def on_stop(self):
        cleanup_all_tracked(self.client)
    
    # ============ 高频只读接口 ============
    
    @task(10)
    def query_customer_list(self):
        self.client.get("/crm/customer/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(8)
    def query_business_list(self):
        self.client.get("/crm/business/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(6)
    def query_clue_list(self):
        self.client.get("/crm/clue/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(4)
    def query_contact_list(self):
        self.client.get("/crm/contact/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(3)
    def query_quotation_list(self):
        self.client.get("/crm/quotation/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(5)
    def query_customer_detail(self):
        customer_id = get_valid_id(self.client, "customer")
        if customer_id:
            self.client.get(f"/crm/customer/{customer_id}")
    
    @task(4)
    def query_business_detail(self):
        business_id = get_valid_id(self.client, "business")
        if business_id:
            self.client.get(f"/crm/business/{business_id}")
    
    # ============ 公海池接口 ============
    
    @task(3)
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
    
    # ============ 业务流程：赢单 ============
    
    @task(2)
    def flow_clue_to_customer(self):
        clue = create_test_clue(self.client)
        if clue:
            customer = transform_clue_to_customer(self.client, clue["id"])
            if customer:
                self.business_context["customer_id"] = customer["id"]
    
    @task(2)
    def flow_create_contact_and_business(self):
        customer_id = self.business_context.get("customer_id") or get_valid_id(self.client, "customer")
        if customer_id:
            contact = create_test_contact(self.client, customer_id)
            business = create_test_business(self.client, customer_id)
            if business:
                self.business_context["business_id"] = business["id"]
    
    @task(1)
    def flow_advance_and_win(self):
        business_id = self.business_context.get("business_id") or get_valid_id(self.client, "business")
        if business_id:
            advance_business_stage(self.client, business_id, "2")
            quotation = create_test_quotation(self.client, business_id)
            if quotation:
                approve_quotation(self.client, quotation["id"])
            advance_business_stage(self.client, business_id, "3")
            win_business(self.client, business_id)
    
    # ============ 业务流程：输单 ============
    
    @task(1)
    def flow_lose_business(self):
        business_id = get_valid_id(self.client, "business")
        if business_id:
            advance_business_stage(self.client, business_id, "2")
            quotation = create_test_quotation(self.client, business_id)
            if quotation:
                approve_quotation(self.client, quotation["id"])
            advance_business_stage(self.client, business_id, "3")
            lose_business(self.client, business_id)
    
    # ============ 目标管理 ============
    
    @task(2)
    def query_goal_list(self):
        self.client.get("/crm/goal/page", params={"pageNum": 1, "pageSize": 10})
    
    # ============ 待办事项 ============
    
    @task(2)
    def query_todo_list(self):
        self.client.get("/crm/todo/page", params={"pageNum": 1, "pageSize": 10})
    
    # ============ 产品管理 ============
    
    @task(2)
    def query_product_list(self):
        self.client.get("/crm/product/page", params={"pageNum": 1, "pageSize": 10})


class CRMReadonlyUser(HttpUser):
    """CRM 只读压测用户 - 高频查询，无写操作"""
    
    host = os.getenv("API_BASE_URL", get_api_base_url())
    wait_time = between(0.5, 2)
    
    def on_start(self):
        token = get_auth_token(self.client)
        self.client.headers.update({"Authorization": f"Bearer {token}"})
    
    @task(10)
    def query_customer_list(self):
        self.client.get("/crm/customer/page", params={"pageNum": 1, "pageSize": 20})
    
    @task(8)
    def query_business_list(self):
        self.client.get("/crm/business/page", params={"pageNum": 1, "pageSize": 20})
    
    @task(6)
    def query_clue_list(self):
        self.client.get("/crm/clue/page", params={"pageNum": 1, "pageSize": 20})
    
    @task(4)
    def query_contact_list(self):
        self.client.get("/crm/contact/page", params={"pageNum": 1, "pageSize": 20})
    
    @task(3)
    def query_quotation_list(self):
        self.client.get("/crm/quotation/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(3)
    def query_public_pool(self):
        self.client.get("/crm/customer/page", params={
            "pageNum": 1, "pageSize": 10, "isQueryPool": "true"
        })
    
    @task(5)
    def query_customer_detail(self):
        customer_id = get_valid_id(self.client, "customer")
        if customer_id:
            self.client.get(f"/crm/customer/{customer_id}")
    
    @task(4)
    def query_business_detail(self):
        business_id = get_valid_id(self.client, "business")
        if business_id:
            self.client.get(f"/crm/business/{business_id}")
    
    @task(3)
    def query_clue_detail(self):
        clue_id = get_valid_id(self.client, "clue")
        if clue_id:
            self.client.get(f"/crm/clue/{clue_id}")
    
    @task(2)
    def query_contact_detail(self):
        contact_id = get_valid_id(self.client, "contact")
        if contact_id:
            self.client.get(f"/crm/contact/{contact_id}")
    
    @task(2)
    def query_quotation_detail(self):
        quotation_id = get_valid_id(self.client, "quotation")
        if quotation_id:
            self.client.get(f"/crm/quotation/{quotation_id}")
    
    @task(2)
    def query_goal_list(self):
        self.client.get("/crm/goal/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(2)
    def query_todo_list(self):
        self.client.get("/crm/todo/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(2)
    def query_product_list(self):
        self.client.get("/crm/product/page", params={"pageNum": 1, "pageSize": 10})


class CRMWriteUser(HttpUser):
    """CRM 写操作压测用户 - 低频写操作"""
    
    host = os.getenv("API_BASE_URL", get_api_base_url())
    wait_time = between(5, 15)
    
    def on_start(self):
        token = get_auth_token(self.client)
        self.client.headers.update({"Authorization": f"Bearer {token}"})
    
    def on_stop(self):
        cleanup_all_tracked(self.client)
    
    @task(3)
    def create_clue_and_list(self):
        clue = create_test_clue(self.client)
        if clue:
            self.client.get("/crm/clue/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(2)
    def create_customer_and_list(self):
        customer_id = get_valid_id(self.client, "customer")
        if customer_id:
            clue = create_test_clue(self.client)
            if clue:
                customer = transform_clue_to_customer(self.client, clue["id"])
                if customer:
                    self.client.get("/crm/customer/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(2)
    def create_business_and_list(self):
        customer_id = get_valid_id(self.client, "customer")
        if customer_id:
            business = create_test_business(self.client, customer_id)
            if business:
                self.client.get("/crm/business/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(1)
    def create_quotation_and_approve(self):
        business_id = get_valid_id(self.client, "business")
        if business_id:
            quotation = create_test_quotation(self.client, business_id)
            if quotation:
                approve_quotation(self.client, quotation["id"])
                self.client.get("/crm/quotation/page", params={"pageNum": 1, "pageSize": 10})
    
    @task(1)
    def full_win_flow(self):
        clue = create_test_clue(self.client)
        if not clue:
            return
        customer = transform_clue_to_customer(self.client, clue["id"])
        if not customer:
            return
        business = create_test_business(self.client, customer["id"])
        if not business:
            return
        advance_business_stage(self.client, business["id"], "2")
        quotation = create_test_quotation(self.client, business["id"])
        if quotation:
            approve_quotation(self.client, quotation["id"])
        advance_business_stage(self.client, business["id"], "3")
        win_business(self.client, business["id"])
    
    @task(1)
    def full_lose_flow(self):
        clue = create_test_clue(self.client)
        if not clue:
            return
        customer = transform_clue_to_customer(self.client, clue["id"])
        if not customer:
            return
        business = create_test_business(self.client, customer["id"])
        if not business:
            return
        advance_business_stage(self.client, business["id"], "2")
        quotation = create_test_quotation(self.client, business["id"])
        if quotation:
            approve_quotation(self.client, quotation["id"])
        advance_business_stage(self.client, business["id"], "3")
        lose_business(self.client, business["id"])


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    try:
        base_url = os.getenv("API_BASE_URL", get_api_base_url())
        print(f"\n🧹 压测结束，清理测试数据...")
        print(f"   目标地址: {base_url}")
        print(f"   清理完成")
    except Exception:
        pass