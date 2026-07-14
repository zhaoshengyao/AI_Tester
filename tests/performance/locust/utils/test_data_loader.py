import json
import os
import random

def load_test_data(data_type):
    """加载测试数据"""
    data_dir = os.path.join(os.path.dirname(__file__), "../testdata")
    data_file = os.path.join(data_dir, f"{data_type}.json")
    
    if not os.path.exists(data_file):
        return generate_default_data(data_type)
    
    with open(data_file, "r", encoding="utf-8") as f:
        data_list = json.load(f)
    
    return random.choice(data_list)

def generate_default_data(data_type):
    """生成默认测试数据"""
    random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
    
    if data_type == "customer":
        return {
            "customerName": f"压测客户_{random_suffix}",
            "customerCode": f"PRESS_{random_suffix.upper()}",
            "customerLevel": "1",
            "customerSource": "1",
            "industry": "IT行业",
            "address": "测试地址",
            "contactName": "联系人",
            "contactPhone": "13800138000",
            "email": f"test_{random_suffix}@example.com",
            "remark": "测试客户数据"
        }
    elif data_type == "business":
        return {
            "businessName": f"压测商机_{random_suffix}",
            "customerId": 1,
            "amount": random.randint(10000, 1000000),
            "probability": random.randint(10, 100),
            "stage": "1",
            "nextAction": "跟进客户需求",
            "remark": "测试商机数据"
        }
    else:
        return {"name": f"test_{random_suffix}"}

def get_base_url():
    """获取基础URL，优先环境变量"""
    return os.getenv("BASE_URL", os.getenv("LOCUST_HOST", "http://192.168.2.97:6089"))

def get_api_base_url():
    """获取API基础URL，优先环境变量"""
    return os.getenv("API_BASE_URL", os.getenv("BASE_URL", "http://192.168.2.97:6089") + "/prod-api")