from clients.base_client import BaseClient


class CrmClient(BaseClient):
    def get_customer_list(self, page: int = 1, size: int = 10, owner_user_id: int = None):
        params = {"pageNum": page, "pageSize": size}
        if owner_user_id:
            params["ownerUserId"] = owner_user_id
        return self.request("GET", "/crm/customer/page", params=params)

    def get_customer_simple_list(self):
        return self.request("GET", "/crm/customer/simple-list")

    def get_clue_simple_list(self):
        return self.request("GET", "/crm/clue/simple-list")

    def get_contact_simple_list(self):
        return self.request("GET", "/crm/contact/simple-list")

    def get_business_simple_list(self):
        return self.request("GET", "/crm/business/simple-list")

    def get_dict_data(self, dict_type: str):
        return self.request("GET", f"/system/dict/data/type/{dict_type}")
    
    def get_customer_detail(self, customer_id: int):
        return self.request("GET", f"/crm/customer/{customer_id}")
    
    def create_customer(self, customer_data: dict):
        return self.request("POST", "/crm/customer", json=customer_data)
    
    def update_customer(self, customer_id: int, customer_data: dict):
        return self.request("PUT", f"/crm/customer/{customer_id}", json=customer_data)
    
    def delete_customer(self, customer_id: int):
        return self.request("DELETE", f"/crm/customer/{customer_id}")
    
    def batch_delete_customer(self, customer_ids: list):
        return self.request("DELETE", "/crm/customer/batch", json=customer_ids)