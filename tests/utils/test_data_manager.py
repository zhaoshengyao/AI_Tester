import os
import json
import uuid
import time
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


class TestDataManager:
    def __init__(self, api_base_url: Optional[str] = None, auth_token: Optional[str] = None):
        self.api_base_url = api_base_url or os.environ.get('API_BASE_URL', 'http://192.168.2.97:6089/prod-api')
        self.auth_token = auth_token
        self.headers = {'Authorization': f'Bearer {auth_token}'} if auth_token else {}
        self.data_dir = os.path.join(os.path.dirname(__file__), '../data')
        self.created_data: List[Dict[str, Any]] = []
        self._ensure_data_dir()
        self._max_retries = 3
        self._retry_delay = 1.0
    
    def _ensure_data_dir(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir, exist_ok=True)
    
    def load_test_data(self, data_type: str) -> Dict[str, Any]:
        data_file = os.path.join(self.data_dir, f'{data_type}.json')
        if os.path.exists(data_file):
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self._generate_default_data(data_type)
    
    def _generate_default_data(self, data_type: str) -> Dict[str, Any]:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        data_templates = {
            'customer': {
                'customerName': f'test_customer_{unique_id}',
                'contactName': f'Contact_{unique_id}',
                'phone': f'13800{timestamp[-8:]}',
                'email': f'test_{unique_id}@example.com',
                'address': f'Test Address {unique_id}',
                'industry': 'IT',
                'scale': '1-10人',
                'source': '线上',
                'status': '正常'
            },
            'business': {
                'businessName': f'test_business_{unique_id}',
                'customerId': 1,
                'customerName': f'test_customer_{unique_id}',
                'amount': 10000.00,
                'probability': 50,
                'stage': '需求确认',
                'expectedCloseDate': datetime.now().strftime('%Y-%m-%d'),
                'responsible': '测试用户'
            },
            'clue': {
                'name': f'Clue_{unique_id}',
                'phone': f'13900{timestamp[-8:]}',
                'company': f'Company_{unique_id}',
                'source': '线上',
                'status': '待领取'
            },
            'product': {
                'productName': f'test_product_{unique_id}',
                'category': '软件',
                'price': 999.00,
                'description': f'Test product {unique_id}',
                'status': '正常'
            },
            'quotation': {
                'quotationNo': f'QT{timestamp}',
                'customerId': 1,
                'customerName': f'test_customer_{unique_id}',
                'validDate': datetime.now().strftime('%Y-%m-%d'),
                'items': [{
                    'productName': f'test_product_{unique_id}',
                    'quantity': 1,
                    'unitPrice': 999.00,
                    'amount': 999.00
                }],
                'totalAmount': 999.00,
                'status': '草稿'
            }
        }
        
        return data_templates.get(data_type, {})
    
    def save_created_data(self, data_type: str, data_id: int, data_info: Optional[Dict[str, Any]] = None):
        record = {
            'type': data_type,
            'id': data_id,
            'info': data_info or {},
            'created_at': datetime.now().isoformat()
        }
        self.created_data.append(record)
        
        history_file = os.path.join(self.data_dir, 'created_data_history.json')
        history = []
        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        history.append(record)
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    
    def cleanup_created_data(self) -> List[Dict[str, Any]]:
        cleanup_results = []
        
        for record in reversed(self.created_data):
            try:
                data_type = record['type']
                data_id = record['id']
                deleted, error = self._delete_data_with_retry(data_type, data_id)
                result = {
                    'type': data_type,
                    'id': data_id,
                    'deleted': deleted
                }
                if error:
                    result['error'] = error
                cleanup_results.append(result)
            except Exception as e:
                cleanup_results.append({
                    'type': record['type'],
                    'id': record['id'],
                    'deleted': False,
                    'error': str(e)
                })
        
        self.created_data = []
        
        cleanup_log = os.path.join(self.data_dir, 'cleanup_log.json')
        with open(cleanup_log, 'w', encoding='utf-8') as f:
            json.dump({
                'cleanup_time': datetime.now().isoformat(),
                'results': cleanup_results
            }, f, ensure_ascii=False, indent=2)
        
        return cleanup_results
    
    def _delete_data_with_retry(self, data_type: str, data_id: int) -> Tuple[bool, Optional[str]]:
        delete_endpoints = {
            'customer': f'/crm/customer/{data_id}',
            'business': f'/crm/business/{data_id}',
            'clue': f'/crm/clue/{data_id}',
            'product': f'/product/{data_id}',
            'quotation': f'/crm/quotation/{data_id}'
        }
        
        endpoint = delete_endpoints.get(data_type)
        if not endpoint:
            return False, f"Unknown data type: {data_type}"
        
        last_error = None
        for attempt in range(self._max_retries):
            try:
                response = requests.delete(
                    f'{self.api_base_url}{endpoint}',
                    headers=self.headers,
                    timeout=10
                )
                if response.status_code in [200, 204, 404]:
                    return True, None
                last_error = f"HTTP {response.status_code}: {response.text}"
            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection error: {str(e)}"
            except requests.exceptions.Timeout as e:
                last_error = f"Timeout: {str(e)}"
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
            
            if attempt < self._max_retries - 1:
                time.sleep(self._retry_delay * (attempt + 1))
        
        return False, last_error
    
    def init_test_data(self) -> Dict[str, Any]:
        init_data = {}
        
        customer_data = self.load_test_data('customer')
        customer_id = self._create_customer(customer_data)
        if customer_id:
            init_data['customer'] = {'id': customer_id, **customer_data}
        
        business_data = self.load_test_data('business')
        business_data['customerId'] = customer_id or 1
        business_data['customerName'] = customer_data.get('customerName', '')
        business_id = self._create_business(business_data)
        if business_id:
            init_data['business'] = {'id': business_id, **business_data}
        
        clue_data = self.load_test_data('clue')
        clue_id = self._create_clue(clue_data)
        if clue_id:
            init_data['clue'] = {'id': clue_id, **clue_data}
        
        return init_data
    
    def _create_customer(self, data: Dict[str, Any]) -> int:
        try:
            response = requests.post(
                f'{self.api_base_url}/crm/customer',
                headers=self.headers,
                json=data,
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                customer_id = result.get('data', {}).get('id')
                if customer_id:
                    self.save_created_data('customer', customer_id, data)
                    return customer_id
        except Exception:
            pass
        return 0
    
    def _create_business(self, data: Dict[str, Any]) -> int:
        try:
            response = requests.post(
                f'{self.api_base_url}/crm/business',
                headers=self.headers,
                json=data,
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                business_id = result.get('data', {}).get('id')
                if business_id:
                    self.save_created_data('business', business_id, data)
                    return business_id
        except Exception:
            pass
        return 0
    
    def _create_clue(self, data: Dict[str, Any]) -> int:
        try:
            response = requests.post(
                f'{self.api_base_url}/crm/clue',
                headers=self.headers,
                json=data,
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                clue_id = result.get('data', {}).get('id')
                if clue_id:
                    self.save_created_data('clue', clue_id, data)
                    return clue_id
        except Exception:
            pass
        return 0


def get_test_data_manager(api_base_url: Optional[str] = None, auth_token: Optional[str] = None) -> TestDataManager:
    return TestDataManager(api_base_url, auth_token)