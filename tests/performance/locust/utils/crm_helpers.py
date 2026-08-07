import os
import sys
import time
import random
import string
import threading
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from utils.auth import get_env_config, get_auth_token, encrypt_password


_resource_tracker = defaultdict(list)
_tracker_lock = threading.Lock()
_login_semaphore = threading.Semaphore(3)
_login_retries = 3
_login_base_delay = 1.0


def generate_unique_id(prefix="perf"):
    timestamp = int(time.time() * 1000)
    rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}_{timestamp}_{rand_str}"


def generate_name(entity_type):
    unique_id = generate_unique_id(entity_type)
    return f"性能测试_{entity_type}_{unique_id[-8:]}"


def track_resource(resource_type, resource_id, name=""):
    with _tracker_lock:
        _resource_tracker[resource_type].append({
            "id": resource_id,
            "name": name,
            "created_at": time.time()
        })


def get_tracked_resources(resource_type=None):
    with _tracker_lock:
        if resource_type:
            return _resource_tracker.get(resource_type, [])
        result = {}
        for rtype, resources in _resource_tracker.items():
            result[rtype] = [r["id"] for r in resources]
        return result


def cleanup_resources(client, resource_type, resource_ids):
    for resource_id in resource_ids:
        try:
            if resource_type == "quotation":
                client.delete(f"/crm/quotation/{resource_id}")
            elif resource_type == "business":
                client.delete(f"/crm/business/{resource_id}")
            elif resource_type == "contact":
                client.delete(f"/crm/contact/{resource_id}")
            elif resource_type == "customer":
                client.delete(f"/crm/customer/{resource_id}")
            elif resource_type == "clue":
                client.delete(f"/crm/clue/{resource_id}")
        except Exception:
            pass


def safe_get(response, key_path, default=None):
    try:
        data = response.json()
        for key in key_path.split("."):
            if isinstance(data, dict):
                data = data.get(key)
            else:
                return default
            if data is None:
                return default
        return data
    except Exception:
        return default


def assert_api_success(response, context=""):
    data = response.json()
    code = data.get("code")
    if code not in [200, 0]:
        raise AssertionError(f"{context} API returned non-success code: {code}, msg: {data.get('msg')}")
    return True


def safe_login(user, max_retries=None):
    """
    安全登录：带并发限速 + 指数退避重试。
    token 同时存储在 user 和 client 上，确保各 helper 函数可访问。
    """
    if max_retries is None:
        max_retries = _login_retries
    
    for attempt in range(max_retries):
        acquired = _login_semaphore.acquire(timeout=30)
        if not acquired:
            if attempt < max_retries - 1:
                delay = _login_base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                time.sleep(delay)
            continue
        
        try:
            token = get_auth_token(user.client)
            user.token = token
            user.token_expire_time = time.time() + 3600
            user.client._perf_token = token
            return token
        except Exception as e:
            err_str = str(e)
            if "401" in err_str or "429" in err_str or "认证" in err_str or "失败" in err_str:
                if attempt < max_retries - 1:
                    delay = _login_base_delay * (2 ** attempt) + random.uniform(0.5, 1.5)
                    time.sleep(delay)
                    continue
            print(f"[!] Login failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise
        finally:
            _login_semaphore.release()
    
    return None


def get_or_refresh_token(user, force_refresh=False):
    if force_refresh or not hasattr(user, 'token') or not getattr(user, 'token', None) or user.token_expire_time < time.time():
        return safe_login(user)
    return user.token


def _get_client_headers(client):
    """获取 client 上存储的 token headers"""
    token = getattr(client, '_perf_token', None)
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def get_auth_headers(user):
    """获取当前用户的认证 headers（供 locustfile 直接调用）"""
    token = get_or_refresh_token(user)
    return {"Authorization": f"Bearer {token}"} if token else {}


def _request_with_retry(client, method, url, max_retries=2, **kwargs):
    """
    带 401 重试的请求封装。
    服务端并发瓶颈时可能误返回 401，短暂延迟后重试可缓解。
    """
    for attempt in range(max_retries + 1):
        resp = method(url, **kwargs)
        if resp.status_code != 401 or attempt == max_retries:
            return resp
        time.sleep(0.3)
    return resp


def get_valid_id(client, entity_type, fallback_id=None):
    if entity_type == "customer":
        resp = client.get("/crm/customer/page", params={"pageNum": 1, "pageSize": 1})
        rows = safe_get(resp, "data.rows", [])
        if rows:
            return rows[0].get("id")
    elif entity_type == "business":
        resp = client.get("/crm/business/page", params={"pageNum": 1, "pageSize": 1})
        rows = safe_get(resp, "data.rows", [])
        if rows:
            return rows[0].get("id")
    elif entity_type == "clue":
        resp = client.get("/crm/clue/page", params={"pageNum": 1, "pageSize": 1})
        rows = safe_get(resp, "data.rows", [])
        if rows:
            return rows[0].get("id")
    elif entity_type == "contact":
        resp = client.get("/crm/contact/page", params={"pageNum": 1, "pageSize": 1})
        rows = safe_get(resp, "data.rows", [])
        if rows:
            return rows[0].get("id")
    elif entity_type == "quotation":
        resp = client.get("/crm/quotation/page", params={"pageNum": 1, "pageSize": 1})
        rows = safe_get(resp, "data.rows", [])
        if rows:
            return rows[0].get("id")
    return fallback_id


def create_test_clue(client, name=None):
    clue_name = name or generate_name("线索")
    payload = {
        "clueName": clue_name,
        "clueSource": "1",
        "clueLevel": "1",
        "contactName": "张三",
        "contactPhone": "133" + str(random.randint(10000000, 99999999)),
        "companyName": f"性能测试公司_{random.randint(1000, 9999)}",
        "remark": "性能测试自动创建"
    }
    resp = _request_with_retry(client, client.post, "/crm/clue", json=payload, headers=_get_client_headers(client))
    if assert_api_success(resp, "create_clue"):
        data = safe_get(resp, "data")
        clue_id = None
        if data and isinstance(data, dict):
            clue_id = data.get("id")
        elif isinstance(data, int):
            clue_id = data
        if not clue_id:
            clue_id = get_valid_id(client, "clue")
        if clue_id:
            track_resource("clue", clue_id, clue_name)
            return {"id": clue_id, "name": clue_name}
    return None


def transform_clue_to_customer(client, clue_id, company_name=None):
    if not company_name:
        company_name = generate_name("客户")
    payload = {
        "clueId": str(clue_id),
        "companyName": company_name,
        "contactName": "张三",
        "contactPhone": "133" + str(random.randint(10000000, 99999999)),
        "position": "经理"
    }
    resp = _request_with_retry(client, client.put, "/crm/clue/transform", json=payload, headers=_get_client_headers(client))
    if assert_api_success(resp, "transform_clue"):
        data = safe_get(resp, "data")
        customer_id = None
        if data and isinstance(data, dict):
            customer_id = data.get("id")
        elif isinstance(data, int):
            customer_id = data
        if not customer_id:
            time.sleep(0.5)
            list_resp = client.get("/crm/customer/page", params={"pageNum": 1, "pageSize": 1, "customerName": company_name})
            rows = safe_get(list_resp, "data.rows", [])
            if rows:
                customer_id = rows[0].get("id")
        if customer_id:
            track_resource("customer", customer_id, company_name)
            return {"id": customer_id, "name": company_name}
    return None


def create_test_contact(client, customer_id, name=None):
    contact_name = name or generate_name("联系人")
    payload = {
        "customerId": str(customer_id),
        "contactName": contact_name,
        "contactPhone": "134" + str(random.randint(10000000, 99999999)),
        "email": f"perf_{random.randint(1000, 9999)}@test.com",
        "position": "工程师",
        "remark": "性能测试自动创建"
    }
    resp = _request_with_retry(client, client.post, "/crm/contact", json=payload, headers=_get_client_headers(client))
    if assert_api_success(resp, "create_contact"):
        data = safe_get(resp, "data")
        contact_id = None
        if data and isinstance(data, dict):
            contact_id = data.get("id")
        elif isinstance(data, int):
            contact_id = data
        if not contact_id:
            contact_id = get_valid_id(client, "contact")
        if contact_id:
            track_resource("contact", contact_id, contact_name)
            return {"id": contact_id, "name": contact_name}
    return None


def create_test_business(client, customer_id, name=None):
    business_name = name or generate_name("商机")
    payload = {
        "businessName": business_name,
        "customerId": str(customer_id),
        "amount": str(random.randint(10000, 500000)),
        "probability": str(random.randint(10, 100)),
        "stage": "1",
        "nextAction": "跟进客户需求",
        "ownerUserId": str(get_env_config("TEST_USER_ID", "2059112632781406210")),
        "remark": "性能测试自动创建"
    }
    resp = _request_with_retry(client, client.post, "/crm/business", json=payload, headers=_get_client_headers(client))
    if assert_api_success(resp, "create_business"):
        data = safe_get(resp, "data")
        business_id = None
        if data and isinstance(data, dict):
            business_id = data.get("id")
        elif isinstance(data, int):
            business_id = data
        if not business_id:
            business_id = get_valid_id(client, "business")
        if business_id:
            track_resource("business", business_id, business_name)
            return {"id": business_id, "name": business_name}
    return None


def advance_business_stage(client, business_id, target_stage):
    detail_resp = client.get(f"/crm/business/{business_id}")
    business_data = safe_get(detail_resp, "data", {})
    
    payload = {
        "id": str(business_id),
        "businessName": business_data.get("businessName", ""),
        "customerId": business_data.get("customerId"),
        "stage": target_stage,
        "remark": business_data.get("remark", ""),
        "dealAmount": business_data.get("dealAmount", "0"),
        "winRate": business_data.get("winRate", 30),
        "currency": business_data.get("currency", "人民币"),
        "discountRate": business_data.get("discountRate", "100"),
        "productTotal": business_data.get("productTotal", "0")
    }
    
    resp = _request_with_retry(client, client.put, "/crm/business", json=payload, headers=_get_client_headers(client))
    assert_api_success(resp, f"advance_stage_{target_stage}")
    return resp


def create_test_quotation(client, business_id):
    detail_resp = client.get(f"/crm/business/{business_id}")
    business_data = safe_get(detail_resp, "data", {})
    customer_id = business_data.get("customerId")
    
    quotation_name = generate_name("报价")
    amount = str(random.randint(10000, 100000))
    
    payload = {
        "businessId": str(business_id),
        "customerId": str(customer_id) if customer_id else None,
        "quotationName": quotation_name,
        "amount": amount,
        "discountRate": "100",
        "ownerUserId": str(get_env_config("TEST_USER_ID", "2059112632781406210")),
        "remark": quotation_name
    }
    
    resp = _request_with_retry(client, client.post, "/crm/quotation", json=payload, headers=_get_client_headers(client))
    if assert_api_success(resp, "create_quotation"):
        data = safe_get(resp, "data")
        quotation_id = None
        if data and isinstance(data, dict):
            quotation_id = data.get("id")
        elif isinstance(data, int):
            quotation_id = data
        if not quotation_id:
            quotation_id = get_valid_id(client, "quotation")
        if quotation_id:
            track_resource("quotation", quotation_id, quotation_name)
            return {"id": quotation_id, "name": quotation_name, "amount": amount}
    return None


def approve_quotation(client, quotation_id):
    resp = _request_with_retry(client, client.put, f"/crm/quotation/approve/{quotation_id}", headers=_get_client_headers(client))
    assert_api_success(resp, "approve_quotation")
    return resp


def win_business(client, business_id, deal_amount=None):
    import datetime
    deal_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    detail_resp = client.get(f"/crm/business/{business_id}")
    business_data = safe_get(detail_resp, "data", {})
    
    if not deal_amount:
        quotation_resp = client.get("/crm/quotation/page", params={"pageNum": 1, "pageSize": 1, "businessId": business_id})
        quotations = safe_get(quotation_resp, "data.rows", [])
        if quotations:
            deal_amount = quotations[0].get("amount")
        if not deal_amount:
            deal_amount = str(random.randint(10000, 500000))
    
    payload = {
        "id": str(business_id),
        "stage": "4",
        "dealAmount": str(deal_amount),
        "dealDate": deal_date
    }
    
    resp = _request_with_retry(client, client.put, "/crm/business", json=payload, headers=_get_client_headers(client))
    assert_api_success(resp, "win_business")
    return resp


def lose_business(client, business_id, lost_reason="2"):
    detail_resp = client.get(f"/crm/business/{business_id}")
    business_data = safe_get(detail_resp, "data", {})
    
    payload = {
        "id": str(business_id),
        "stage": "6",
        "status": "2",
        "businessName": business_data.get("businessName", ""),
        "lostReason": lost_reason
    }
    
    resp = _request_with_retry(client, client.put, "/crm/business", json=payload, headers=_get_client_headers(client))
    assert_api_success(resp, "lose_business")
    return resp


def get_public_pool_list(client, page=1, size=10):
    resp = client.get("/crm/customer/page", params={"pageNum": page, "pageSize": size, "isQueryPool": "true"})
    return resp


def claim_from_pool(client, customer_id):
    resp = _request_with_retry(client, client.put, "/crm/customer/receive-from-pool", json=[str(customer_id)], headers=_get_client_headers(client))
    assert_api_success(resp, "claim_from_pool")
    return resp


def cleanup_all_tracked(client):
    with _tracker_lock:
        resources = dict(_resource_tracker)
        _resource_tracker.clear()
    
    for resource_type in ["quotation", "business", "contact", "customer", "clue"]:
        ids = [r["id"] for r in resources.get(resource_type, [])]
        for rid in ids:
            try:
                if resource_type == "quotation":
                    client.delete(f"/crm/quotation/{rid}")
                elif resource_type == "business":
                    client.delete(f"/crm/business/{rid}")
                elif resource_type == "contact":
                    client.delete(f"/crm/contact/{rid}")
                elif resource_type == "customer":
                    client.delete(f"/crm/customer/{rid}")
                elif resource_type == "clue":
                    client.delete(f"/crm/clue/{rid}")
            except Exception:
                pass


__all__ = [
    "generate_unique_id", "generate_name",
    "track_resource", "get_tracked_resources", "cleanup_resources", "cleanup_all_tracked",
    "safe_get", "assert_api_success",
    "safe_login", "get_or_refresh_token",
    "get_valid_id",
    "create_test_clue", "transform_clue_to_customer",
    "create_test_contact", "create_test_business",
    "advance_business_stage", "create_test_quotation",
    "approve_quotation", "win_business", "lose_business",
    "get_public_pool_list", "claim_from_pool"
]