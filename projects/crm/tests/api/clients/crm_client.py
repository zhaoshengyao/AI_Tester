from clients.base_client import BaseClient


class CrmClient(BaseClient):
    # ============ 线索管理 ============
    def get_clue_list(self, page=1, size=10, name=None):
        params = {"pageNum": page, "pageSize": size}
        if name:
            params["clueName"] = name
        return self.request("GET", "/crm/clue/page", params=params)
    
    def get_clue_simple_list(self):
        return self.request("GET", "/crm/clue/simple-list")
    
    def get_clue_detail(self, clue_id: int):
        return self.request("GET", f"/crm/clue/{clue_id}")
    
    def create_clue(self, clue_data: dict):
        return self.request("POST", "/crm/clue", json=clue_data)
    
    def update_clue(self, clue_id: int, clue_data: dict):
        payload = {"id": clue_id}
        payload.update(clue_data)
        return self.request("PUT", "/crm/clue", json=payload)
    
    def delete_clue(self, clue_id: int):
        return self.request("DELETE", f"/crm/clue/{clue_id}")
    
    def batch_delete_clue(self, clue_ids: list):
        return self.request("DELETE", "/crm/clue/batch", json=clue_ids)
    
    def transform_clue_to_customer(self, clue_id, company_name: str, contact_name: str = "", 
                                     contact_phone: str = "", position: str = ""):
        """线索转客户
        
        Args:
            clue_id: 线索ID
            company_name: 公司名称（客户名称）
            contact_name: 联系人姓名
            contact_phone: 联系人电话
            position: 职位
        """
        payload = {
            "clueId": str(clue_id),
            "companyName": company_name,
            "contactName": contact_name,
            "contactPhone": contact_phone,
            "position": position
        }
        return self.request("PUT", "/crm/clue/transform", json=payload)

    # ============ 客户管理 ============
    def get_customer_list(self, page: int = 1, size: int = 10, owner_user_id: int = None, name: str = None):
        params = {"pageNum": page, "pageSize": size}
        if owner_user_id:
            params["ownerUserId"] = owner_user_id
        if name:
            params["customerName"] = name
        return self.request("GET", "/crm/customer/page", params=params)

    def get_customer_simple_list(self):
        return self.request("GET", "/crm/customer/simple-list")

    def get_customer_detail(self, customer_id: int):
        return self.request("GET", f"/crm/customer/{customer_id}")
    
    def create_customer(self, customer_data: dict):
        return self.request("POST", "/crm/customer", json=customer_data)
    
    def update_customer(self, customer_id: int, customer_data: dict):
        # 更新接口使用 PUT /crm/customer，通过请求体中的 id 字段识别
        payload = {"id": customer_id}
        payload.update(customer_data)
        return self.request("PUT", "/crm/customer", json=payload)
    
    def delete_customer(self, customer_id: int):
        return self.request("DELETE", f"/crm/customer/{customer_id}")
    
    def batch_delete_customer(self, customer_ids: list):
        return self.request("DELETE", "/crm/customer/batch", json=customer_ids)

    # ============ 联系人管理 ============
    def get_contact_simple_list(self):
        return self.request("GET", "/crm/contact/simple-list")

    def get_contact_list(self, page: int = 1, size: int = 10, customer_id: int = None):
        params = {"pageNum": page, "pageSize": size}
        if customer_id:
            params["customerId"] = customer_id
        return self.request("GET", "/crm/contact/page", params=params)
    
    def get_contact_detail(self, contact_id: int):
        return self.request("GET", f"/crm/contact/{contact_id}")
    
    def create_contact(self, contact_data: dict):
        return self.request("POST", "/crm/contact", json=contact_data)
    
    def update_contact(self, contact_id: int, contact_data: dict):
        payload = {"id": contact_id}
        payload.update(contact_data)
        return self.request("PUT", "/crm/contact", json=payload)
    
    def delete_contact(self, contact_id: int):
        return self.request("DELETE", f"/crm/contact/{contact_id}")
    
    def batch_delete_contact(self, contact_ids: list):
        return self.request("DELETE", "/crm/contact/batch", json=contact_ids)

    # ============ 商机管理 ============
    def get_business_list(self, page: int = 1, size: int = 10, name: str = None):
        params = {"pageNum": page, "pageSize": size}
        if name:
            params["businessName"] = name
        return self.request("GET", "/crm/business/page", params=params)

    def get_business_simple_list(self):
        return self.request("GET", "/crm/business/simple-list")

    def get_business_detail(self, business_id: int):
        return self.request("GET", f"/crm/business/{business_id}")

    def create_business(self, business_data: dict):
        return self.request("POST", "/crm/business", json=business_data)

    def update_business(self, business_id: int, business_data: dict):
        payload = {"id": business_id}
        payload.update(business_data)
        return self.request("PUT", "/crm/business", json=payload)

    def delete_business(self, business_id: int):
        return self.request("DELETE", f"/crm/business/{business_id}")
    
    def batch_delete_business(self, business_ids: list):
        return self.request("DELETE", "/crm/business/batch", json=business_ids)

    def add_business_product(self, product_data: dict):
        return self.request("POST", "/crm/business/product", json=product_data)

    def get_business_products(self, business_id: int):
        return self.request("GET", f"/crm/business/product/{business_id}")

    def add_business_follow(self, follow_data: dict):
        return self.request("POST", "/crm/business/follow", json=follow_data)

    def get_business_follows(self, business_id: int):
        return self.request("GET", f"/crm/business/follow/{business_id}")
    
    def advance_business_stage(self, business_id, target_stage: str):
        """推进商机阶段
        
        Args:
            business_id: 商机ID
            target_stage: 目标阶段 (1-验证客户, 2-方案确认, 3-谈判审核, 4-赢单, 5-输单)
        """
        detail_response = self.get_business_detail(business_id)
        detail_data = detail_response.json()
        business_data = detail_data.get("data", {})
        
        import datetime
        deal_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # 构造完整的更新请求体
        payload = {
            "id": str(business_id),
            "businessName": business_data.get("businessName", ""),
            "customerId": business_data.get("customerId"),
            "stage": target_stage,
            "remark": business_data.get("remark", ""),
            "dealAmount": business_data.get("dealAmount", "0"),
            "dealDate": business_data.get("dealDate") or deal_date,
            "winRate": business_data.get("winRate", 30),
            "currency": business_data.get("currency", "人民币"),
            "discountRate": business_data.get("discountRate", "100"),
            "productTotal": business_data.get("productTotal", "0")
        }
        
        return self.request("PUT", "/crm/business", json=payload)
    
    def win_business(self, business_id, deal_amount=None, deal_date=None):
        """赢单
        
        Args:
            business_id: 商机ID
            deal_amount: 成交金额（可选，默认使用报价金额）
            deal_date: 成交日期（可选，默认今天）
        """
        import datetime
        if not deal_date:
            deal_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        detail_response = self.get_business_detail(business_id)
        detail_data = detail_response.json()
        business_data = detail_data.get("data", {})
        
        # 从报价获取成交金额，如果没有则使用默认值
        if not deal_amount:
            deal_amount = business_data.get("dealAmount") or "100000"
        
        payload = {
            "id": str(business_id),
            "businessName": business_data.get("businessName", ""),
            "customerId": business_data.get("customerId"),
            "stage": "4",
            "remark": business_data.get("remark", ""),
            "dealAmount": deal_amount,
            "dealDate": deal_date,
            "winRate": 100,
            "currency": business_data.get("currency", "人民币"),
            "discountRate": business_data.get("discountRate", "100"),
            "productTotal": business_data.get("productTotal", "0")
        }
        
        return self.request("PUT", "/crm/business", json=payload)
    
    def lose_business(self, business_id, lost_reason="2"):
        """输单
        
        Args:
            business_id: 商机ID
            lost_reason: 输单原因（默认"2"）
        """
        detail_response = self.get_business_detail(business_id)
        detail_data = detail_response.json()
        business_data = detail_data.get("data", {})
        
        payload = {
            "id": str(business_id),
            "stage": "6",
            "status": "2",
            "businessName": business_data.get("businessName", ""),
            "lostReason": lost_reason
        }
        
        return self.request("PUT", "/crm/business", json=payload)
    
    def get_business_stage_history(self, business_id: int):
        """获取商机阶段变更历史"""
        return self.request("GET", f"/crm/business/{business_id}/stage-history")

    # ============ 报价管理 ============
    def get_quotation_list(self, page: int = 1, size: int = 10, name: str = None, status: str = None):
        params = {"pageNum": page, "pageSize": size}
        if name:
            params["quotationName"] = name
        if status:
            params["status"] = status
        return self.request("GET", "/crm/quotation/page", params=params)
    
    def get_quotation_detail(self, quotation_id: int):
        return self.request("GET", f"/crm/quotation/{quotation_id}")
    
    def create_quotation(self, quotation_data: dict):
        return self.request("POST", "/crm/quotation", json=quotation_data)
    
    def update_quotation(self, quotation_id: int, quotation_data: dict):
        payload = {"id": quotation_id}
        payload.update(quotation_data)
        return self.request("PUT", "/crm/quotation", json=payload)
    
    def delete_quotation(self, quotation_id: int):
        return self.request("DELETE", f"/crm/quotation/{quotation_id}")
    
    def batch_delete_quotation(self, quotation_ids: list):
        return self.request("DELETE", "/crm/quotation/batch", json=quotation_ids)
    
    def submit_quotation_for_approval(self, quotation_id: int):
        """提交报价审批（草稿→待审批）
        
        PUT /crm/quotation/approve/{id} 无请求体
        注意：用户确认报价单创建后就是待审批状态，此接口可选
        """
        return self.request("PUT", f"/crm/quotation/approve/{quotation_id}")
    
    def approve_quotation(self, quotation_id: int, remark: str = ""):
        """审批通过报价
        
        PUT /crm/quotation/approve/{id} 无请求体
        用户提供的审批接口，调用后报价单直接审批通过
        """
        return self.request("PUT", f"/crm/quotation/approve/{quotation_id}")
    
    def reject_quotation(self, quotation_id: int, remark: str = ""):
        """审批拒绝报价"""
        return self.request("PUT", f"/crm/quotation/reject/{quotation_id}")

    # ============ 产品管理 ============
    def get_product_list(self, page: int = 1, size: int = 10, name: str = None):
        params = {"pageNum": page, "pageSize": size}
        if name:
            params["productName"] = name
        return self.request("GET", "/crm/product/page", params=params)
    
    def get_product_detail(self, product_id: int):
        return self.request("GET", f"/crm/product/{product_id}")
    
    def create_product(self, product_data: dict):
        return self.request("POST", "/crm/product", json=product_data)
    
    def update_product(self, product_id: int, product_data: dict):
        payload = {"id": product_id}
        payload.update(product_data)
        return self.request("PUT", "/crm/product", json=payload)
    
    def delete_product(self, product_id: int):
        return self.request("DELETE", f"/crm/product/{product_id}")
    
    def batch_delete_product(self, product_ids: list):
        return self.request("DELETE", "/crm/product/batch", json=product_ids)

    # ============ 字典与统计 ============
    def get_dict_data(self, dict_type: str):
        return self.request("GET", f"/system/dict/data/type/{dict_type}")

    def get_target_list(self, page: int = 1, size: int = 10):
        return self.request("GET", "/crm/target/page", params={"pageNum": page, "pageSize": size})

    def get_goal_list(self):
        return self.request("GET", "/crm/goalManage/list")

    def get_goal_detail(self, goal_id: int):
        return self.request("GET", f"/crm/goalManage/{goal_id}")

    def get_statistics_dashboard(self):
        return self.request("GET", "/crm/statistics/dashboard")

    def get_performance_summary(self, user_id: str, month: str):
        return self.request("GET", "/crm/goalManage/performance/summary", params={"userId": user_id, "month": month})

    def get_performance_report(self):
        return self.request("GET", "/crm/statistics/performance/report")
    
    # ============ 公海池管理 ============
    def get_public_pool_list(self, page: int = 1, size: int = 10, name: str = None):
        """获取公海池客户列表"""
        params = {"pageNum": page, "pageSize": size, "isQueryPool": "true"}
        if name:
            params["customerName"] = name
        return self.request("GET", "/crm/customer/page", params=params)
    
    def claim_public_customer(self, customer_id):
        """领取公海池客户（单个）
        
        Args:
            customer_id: 客户ID，可以是字符串或整数
        """
        return self.request("PUT", "/crm/customer/receive-from-pool", json=[str(customer_id)])
    
    def batch_claim_public_customers(self, customer_ids: list):
        """批量领取公海池客户
        
        Args:
            customer_ids: 客户ID列表
        """
        id_list = [str(cid) for cid in customer_ids]
        return self.request("PUT", "/crm/customer/receive-from-pool", json=id_list)
    
    # ============ 目标管理 ============
    def create_goal(self, goal_data: dict):
        """创建目标"""
        return self.request("POST", "/crm/goalManage", json=goal_data)
    
    def update_goal(self, goal_id: int, goal_data: dict):
        """更新目标"""
        payload = {"id": goal_id}
        payload.update(goal_data)
        return self.request("PUT", "/crm/goalManage", json=payload)
    
    def delete_goal(self, goal_id: int):
        """删除目标"""
        return self.request("DELETE", f"/crm/goalManage/{goal_id}")
    
    def approve_goal(self, goal_id: int, status: str = "approved"):
        """审批目标"""
        payload = {"status": status}
        return self.request("PUT", f"/crm/goalManage/approve/{goal_id}", json=payload)
    
    # ============ 待办事项 ============
    def create_todo(self, todo_data: dict):
        """创建待办"""
        return self.request("POST", "/crm/task", json=todo_data)
    
    def get_todo_list(self, page: int = 1, size: int = 10, status: str = None):
        """获取待办列表"""
        params = {"pageNum": page, "pageSize": size}
        if status:
            params["status"] = status
        return self.request("GET", "/crm/task/list", params=params)
    
    def update_todo(self, todo_id: int, todo_data: dict):
        """更新待办"""
        payload = {"id": todo_id}
        payload.update(todo_data)
        return self.request("PUT", "/crm/task", json=payload)
    
    def complete_todo(self, todo_id: int):
        """完成待办"""
        payload = {"id": todo_id, "status": "2"}
        return self.request("PUT", "/crm/task", json=payload)
    
    def delete_todo(self, todo_id: int):
        """删除待办"""
        return self.request("DELETE", f"/crm/task/{todo_id}")
    
    # ============ 审批流程 ============
    def get_quotation_list_for_approval(self, page: int = 1, size: int = 10):
        """获取待审批报价列表"""
        params = {"pageNum": page, "pageSize": size}
        return self.request("GET", "/crm/quotation/page", params=params)
    
    def approve_quotation(self, quotation_id: int, remark: str = ""):
        """审批通过报价"""
        payload = {"remark": remark}
        return self.request("PUT", f"/crm/quotation/approve/{quotation_id}", json=payload)
    
    def reject_quotation(self, quotation_id: int, remark: str = ""):
        """审批拒绝报价"""
        payload = {"remark": remark}
        return self.request("PUT", f"/crm/quotation/reject/{quotation_id}", json=payload)
    
    def approve_record(self, approval_id: int, remark: str = ""):
        """审批通过"""
        return self.approve_quotation(approval_id, remark)
    
    def reject_record(self, approval_id: int, remark: str = ""):
        """审批拒绝"""
        return self.reject_quotation(approval_id, remark)