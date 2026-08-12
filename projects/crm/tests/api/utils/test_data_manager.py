import os
import time
import uuid
import requests
from typing import Optional


class TestDataManager:
    """测试数据管理器 - 负责创建、跟踪和清理测试数据"""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "clientid": "e5cd7e4891bf95d1d19206ce24a7b32e",
            "Content-Type": "application/json"
        }
        self.created_resources = []
        self.test_batch_id = str(uuid.uuid4())[:8]
        self.test_prefix = f"TEST_{int(time.time())}_{self.test_batch_id}"
    
    def generate_name(self, entity_type: str) -> str:
        """生成唯一的测试数据名称"""
        return f"{self.test_prefix}_{entity_type}"
    
    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """发送HTTP请求"""
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault('headers', self.headers)
        kwargs.setdefault('timeout', 10)
        response = requests.request(method, url, **kwargs)
        return response
    
    def create_customer(self, name: Optional[str] = None, **kwargs) -> dict:
        """创建测试客户"""
        customer_name = name or self.generate_name("客户")
        payload = {
            "customerName": customer_name,
            "customerLevel": kwargs.get("customerLevel", "1"),
            "customerSource": kwargs.get("customerSource", "1"),
            "phone": kwargs.get("phone", "13800138000"),
            "email": kwargs.get("email", f"{self.test_batch_id}@test.com"),
            "remark": "自动化测试创建"
        }
        
        response = self._request("POST", "/crm/customer", json=payload)
        result = response.json()
        
        customer_id = None
        
        if result.get("code") == 200:
            data = result.get("data")
            
            # 尝试从响应直接获取ID
            if data and isinstance(data, dict):
                customer_id = data.get("id") or data.get("customerId")
            elif isinstance(data, int):
                customer_id = data
            
            # 如果响应没有返回ID，通过列表查询获取
            if not customer_id:
                customer_id = self._find_customer_by_name(customer_name)
            
            if customer_id:
                self.created_resources.append({
                    "type": "customer",
                    "id": customer_id,
                    "name": customer_name,
                    "created_at": time.time()
                })
                print(f"📝 创建测试客户: {customer_name} (ID: {customer_id})")
            else:
                print(f"⚠️ 创建客户成功但未能获取ID: {customer_name}")
            
            return {"id": customer_id, "name": customer_name, "data": data}
        
        raise Exception(f"创建客户失败: {result.get('msg')}")
    
    def _find_customer_by_name(self, customer_name: str) -> Optional[int]:
        """通过列表查询获取客户ID"""
        return self._find_id_by_name("/crm/customer/page", "customerName", customer_name)
    
    def create_contact(self, customer_id: int, name: Optional[str] = None, **kwargs) -> dict:
        """创建测试联系人"""
        contact_name = name or self.generate_name("联系人")
        payload = {
            "contactName": contact_name,
            "customerId": customer_id,
            "phone": kwargs.get("phone", "13900139000"),
            "email": kwargs.get("email", f"{self.test_batch_id}@test.com"),
            "position": kwargs.get("position", "测试职位"),
            "remark": "自动化测试创建"
        }
        
        response = self._request("POST", "/crm/contact", json=payload)
        result = response.json()
        
        if result.get("code") == 200:
            data = result.get("data")
            contact_id = None
            
            # 尝试从响应获取ID
            if data and isinstance(data, dict):
                contact_id = data.get("id") or data.get("contactId")
            elif isinstance(data, int):
                contact_id = data
            
            # 如果响应没有返回ID，通过列表查询获取
            if not contact_id:
                contact_id = self._find_id_by_name("/crm/contact/page", "contactName", contact_name, extra_params={"customerId": customer_id})
            
            if contact_id:
                self.created_resources.append({
                    "type": "contact",
                    "id": contact_id,
                    "name": contact_name,
                    "parent_id": customer_id,
                    "created_at": time.time()
                })
                print(f"📝 创建测试联系人: {contact_name} (ID: {contact_id}, 客户ID: {customer_id})")
            else:
                print(f"⚠️ 创建联系人成功但未能获取ID")
            
            return {"id": contact_id, "name": contact_name, "data": data, "parent_id": customer_id}
        
        raise Exception(f"创建联系人失败: {result.get('msg')}")
    
    def _find_contact_by_name(self, contact_name: str, customer_id: int = None) -> Optional[int]:
        """通过列表查询获取联系人ID"""
        extra_params = {}
        if customer_id:
            extra_params["customerId"] = customer_id
        
        return self._find_id_by_name("/crm/contact/page", "name", contact_name, extra_params=extra_params)
    
    def _find_id_by_name(self, endpoint: str, name_field: str, name_value: str, 
                        extra_params: dict = None) -> Optional[int]:
        """通用通过列表查询获取ID的方法
        
        Args:
            endpoint: 列表接口路径
            name_field: 实体的名称字段名（如 customerName, businessName 等）
            name_value: 要查找的名称值
            extra_params: 额外的查询参数
        """
        params = {"pageNum": 1, "pageSize": 100}
        if extra_params:
            params.update(extra_params)
        
        # 使用实体的名称字段作为查询参数
        params[name_field] = name_value
        
        response = self._request("GET", endpoint, params=params)
        result = response.json()
        
        # 处理不同的响应格式
        rows = result.get("rows", [])
        if not rows:
            rows = result.get("data", [])
            if isinstance(rows, dict):
                rows = [rows] if rows else []
        
        # 先尝试精确匹配
        for row in rows:
            if isinstance(row, dict) and row.get(name_field) == name_value:
                return row.get("id")
        
        # 如果精确匹配没找到，尝试模糊匹配
        for row in rows:
            if isinstance(row, dict) and name_value in str(row.get(name_field, "")):
                return row.get("id")
        
        return None
    
    def create_clue(self, name: Optional[str] = None, **kwargs) -> dict:
        """创建测试线索"""
        clue_name = name or self.generate_name("线索")
        payload = {
            "clueName": clue_name,
            "clueSource": kwargs.get("clueSource", "1"),
            "phone": kwargs.get("phone", "13700137000"),
            "contacts": kwargs.get("contacts", "测试联系人"),
            "remark": "自动化测试创建"
        }
        
        response = self._request("POST", "/crm/clue", json=payload)
        result = response.json()
        
        if result.get("code") == 200:
            data = result.get("data")
            clue_id = None
            
            if data and isinstance(data, dict):
                clue_id = data.get("id")
            elif isinstance(data, int):
                clue_id = data
            
            if not clue_id:
                clue_id = self._find_id_by_name("/crm/clue/page", "clueName", clue_name)
            
            if clue_id:
                self.created_resources.append({
                    "type": "clue",
                    "id": clue_id,
                    "name": clue_name,
                    "created_at": time.time()
                })
                print(f"📝 创建测试线索: {clue_name} (ID: {clue_id})")
            else:
                print(f"⚠️ 创建线索成功但未能获取ID")
            
            return {"id": clue_id, "name": clue_name, "data": data}
        
        raise Exception(f"创建线索失败: {result.get('msg')}")
    
    def create_business(self, customer_id: int, name: Optional[str] = None, **kwargs) -> dict:
        """创建测试商机"""
        business_name = name or self.generate_name("商机")
        payload = {
            "businessName": business_name,
            "customerId": customer_id,
            "stage": kwargs.get("stage", "1"),
            "amount": kwargs.get("amount", 10000),
            "remark": "自动化测试创建"
        }
        
        response = self._request("POST", "/crm/business", json=payload)
        result = response.json()
        
        if result.get("code") == 200:
            data = result.get("data")
            business_id = None
            
            if data and isinstance(data, dict):
                business_id = data.get("id")
            elif isinstance(data, int):
                business_id = data
            
            if not business_id:
                business_id = self._find_id_by_name("/crm/business/page", "businessName", business_name)
            
            if business_id:
                self.created_resources.append({
                    "type": "business",
                    "id": business_id,
                    "name": business_name,
                    "parent_id": customer_id,
                    "created_at": time.time()
                })
                print(f"📝 创建测试商机: {business_name} (ID: {business_id}, 客户ID: {customer_id})")
            else:
                print(f"⚠️ 创建商机成功但未能获取ID")
            
            return {"id": business_id, "name": business_name, "data": data, "parent_id": customer_id}
        
        raise Exception(f"创建商机失败: {result.get('msg')}")
    
    def create_quotation(self, business_id: int, name: Optional[str] = None, **kwargs) -> dict:
        """创建测试报价"""
        quotation_name = name or self.generate_name("报价")
        
        # 先获取商机信息以获取对应的客户ID
        customer_id = kwargs.get("customerId")
        if not customer_id:
            try:
                business_resp = self._request("GET", f"/crm/business/{business_id}")
                business_data = business_resp.json().get("data") or {}
                customer_id = business_data.get("customerId")
            except Exception as e:
                print(f"⚠️ 获取商机信息失败: {e}")
        
        payload = {
            "businessId": str(business_id),
            "customerId": str(customer_id) if customer_id else None,
            "quotationName": quotation_name,
            "amount": str(kwargs.get("totalAmount", 50000)),
            "discountRate": str(kwargs.get("discountRate", 100)),
            "ownerUserId": str(kwargs.get("ownerUserId", "2059112632781406210")),
            "remark": quotation_name
        }
        
        response = self._request("POST", "/crm/quotation", json=payload)
        result = response.json()
        
        if result.get("code") == 200:
            data = result.get("data")
            quotation_id = None
            
            if data and isinstance(data, dict):
                quotation_id = data.get("id")
            elif isinstance(data, int):
                quotation_id = data
            
            # 如果响应没有返回ID，通过业务ID查找最新创建的报价
            if not quotation_id:
                quotation_id = self._find_quotation_by_business(business_id)
            
            if quotation_id:
                self.created_resources.append({
                    "type": "quotation",
                    "id": quotation_id,
                    "name": quotation_name,
                    "parent_id": business_id,
                    "created_at": time.time()
                })
                print(f"📝 创建测试报价: {quotation_name} (ID: {quotation_id}, 商机ID: {business_id})")
            else:
                print(f"⚠️ 创建报价成功但未能获取ID")
            
            return {"id": quotation_id, "name": quotation_name, "data": data, "parent_id": business_id}
        
        raise Exception(f"创建报价失败: {result.get('msg')}")
    
    def _find_quotation_by_business(self, business_id: int) -> Optional[int]:
        """通过商机ID查找最新创建的报价"""
        response = self._request("GET", "/crm/quotation/page", params={
            "pageNum": 1,
            "pageSize": 50,
            "businessId": business_id
        })
        result = response.json()
        rows = result.get("rows", [])
        
        if rows:
            # 返回最新的一条（按createTime倒序）
            return rows[0].get("id")
        
        return None
    
    def get_created_resources(self, resource_type: Optional[str] = None) -> list:
        """获取已创建的资源列表"""
        if resource_type:
            return [r for r in self.created_resources if r["type"] == resource_type]
        return self.created_resources
    
    def get_resource_by_type(self, resource_type: str) -> Optional[dict]:
        """获取指定类型的第一个资源"""
        resources = self.get_created_resources(resource_type)
        return resources[0] if resources else None
    
    def cleanup_created_data(self):
        """清理所有已创建的测试数据"""
        print(f"\n🧹 开始清理测试数据 (批次: {self.test_batch_id})...")
        
        deleted_count = 0
        errors = []
        
        # 按依赖顺序清理
        cleanup_order = [
            ("quotation", "/crm/quotation"),
            ("business", "/crm/business"),
            ("contact", "/crm/contact"),
            ("customer", "/crm/customer"),
            ("clue", "/crm/clue")
        ]
        
        for resource_type, endpoint in cleanup_order:
            resources = self.get_created_resources(resource_type)
            for resource in resources:
                try:
                    resource_id = resource["id"]
                    if resource_id:
                        response = self._request("DELETE", f"{endpoint}/{resource_id}")
                        result = response.json()
                        if result.get("code") == 200:
                            deleted_count += 1
                            print(f"  🗑️ 删除 {resource_type}: {resource['name']} (ID: {resource_id})")
                        else:
                            errors.append(f"删除 {resource_type} 失败: {result.get('msg')}")
                except Exception as e:
                    errors.append(f"删除 {resource_type} 异常: {str(e)}")
        
        print(f"✅ 清理完成: 成功删除 {deleted_count} 条数据")
        if errors:
            print(f"⚠️ 清理警告: {len(errors)} 条错误")
            for error in errors[:5]:
                print(f"  - {error}")
        
        self.created_resources = []
        return deleted_count
    
    def get_stats(self) -> dict:
        """获取测试数据统计"""
        stats = {}
        for resource in self.created_resources:
            rtype = resource["type"]
            stats[rtype] = stats.get(rtype, 0) + 1
        return stats


def get_test_data_manager(base_url: str, token: str) -> TestDataManager:
    """获取测试数据管理器实例"""
    return TestDataManager(base_url, token)
