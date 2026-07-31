#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CRM测试数据清理脚本
清理所有自动化测试创建的历史数据

API响应格式:
- code: 200 表示成功
- rows: 列表数据
- total: 总数
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clients.crm_client import CrmClient


class TestDataCleaner:
    """测试数据清理器"""
    
    # 测试数据标识前缀
    TEST_PREFIXES = ['自动化测试_', '全链路测试_', '流程测试', '测试_', 'AutoTest']
    
    def __init__(self):
        self.client = CrmClient()
        self.stats = {
            'quotations': 0,
            'businesses': 0,
            'contacts': 0,
            'customers': 0,
            'clues': 0,
            'products': 0
        }
    
    def is_test_data(self, name: str) -> bool:
        """判断是否为测试数据"""
        if not name:
            return False
        return any(prefix in name for prefix in self.TEST_PREFIXES)
    
    def clean_clues(self):
        """清理线索数据"""
        print("\n🔍 扫描线索数据...")
        deleted = 0
        page = 1
        
        while True:
            response = self.client.get_clue_list(page=page, size=50)
            data = response.json()
            
            if data.get('code') != 200:
                print(f"⚠️ 获取线索列表失败: {data.get('msg')}")
                break
            
            records = data.get('rows', [])
            if not records:
                break
            
            for record in records:
                name = record.get('clueName', '')  # 线索名称字段是 clueName
                if self.is_test_data(name):
                    clue_id = record.get('id')
                    try:
                        resp = self.client.delete_clue(clue_id)
                        if resp.json().get('code') == 200:
                            deleted += 1
                            print(f"  🗑️  删除线索: {name} (ID: {clue_id})")
                        else:
                            print(f"  ⚠️ 删除线索返回失败: {name} - {resp.json().get('msg')}")
                    except Exception as e:
                        print(f"  ❌ 删除线索失败: {name} - {e}")
            
            total = data.get('total', 0)
            if page * 50 >= total:
                break
            page += 1
        
        self.stats['clues'] = deleted
        print(f"✅ 已清理 {deleted} 条线索数据")
        return deleted
    
    def clean_contacts(self):
        """清理联系人数据"""
        print("\n🔍 扫描联系人数据...")
        deleted = 0
        page = 1
        
        while True:
            response = self.client.get_contact_list(page=page, size=50)
            data = response.json()
            
            if data.get('code') != 200:
                print(f"⚠️ 获取联系人列表失败: {data.get('msg')}")
                break
            
            records = data.get('rows', [])
            if not records:
                break
            
            for record in records:
                name = record.get('name', '')
                if self.is_test_data(name):
                    contact_id = record.get('id')
                    try:
                        resp = self.client.delete_contact(contact_id)
                        if resp.json().get('code') == 200:
                            deleted += 1
                            print(f"  🗑️  删除联系人: {name} (ID: {contact_id})")
                        else:
                            print(f"  ⚠️ 删除联系人返回失败: {name} - {resp.json().get('msg')}")
                    except Exception as e:
                        print(f"  ❌ 删除联系人失败: {name} - {e}")
            
            total = data.get('total', 0)
            if page * 50 >= total:
                break
            page += 1
        
        self.stats['contacts'] = deleted
        print(f"✅ 已清理 {deleted} 条联系人数据")
        return deleted
    
    def clean_businesses(self):
        """清理商机数据"""
        print("\n🔍 扫描商机数据...")
        deleted = 0
        page = 1
        
        while True:
            response = self.client.get_business_list(page=page, size=50)
            data = response.json()
            
            if data.get('code') != 200:
                print(f"⚠️ 获取商机列表失败: {data.get('msg')}")
                break
            
            records = data.get('rows', [])
            if not records:
                break
            
            for record in records:
                name = record.get('businessName', '')  # 商机名称字段是 businessName
                if self.is_test_data(name):
                    business_id = record.get('id')
                    try:
                        resp = self.client.delete_business(business_id)
                        if resp.json().get('code') == 200:
                            deleted += 1
                            print(f"  🗑️  删除商机: {name} (ID: {business_id})")
                        else:
                            print(f"  ⚠️ 删除商机返回失败: {name} - {resp.json().get('msg')}")
                    except Exception as e:
                        print(f"  ❌ 删除商机失败: {name} - {e}")
            
            total = data.get('total', 0)
            if page * 50 >= total:
                break
            page += 1
        
        self.stats['businesses'] = deleted
        print(f"✅ 已清理 {deleted} 条商机数据")
        return deleted
    
    def clean_quotations(self):
        """清理报价数据"""
        print("\n🔍 扫描报价数据...")
        deleted = 0
        page = 1
        
        while True:
            response = self.client.get_quotation_list(page=page, size=50)
            data = response.json()
            
            if data.get('code') != 200:
                print(f"⚠️ 获取报价列表失败: {data.get('msg')}")
                break
            
            records = data.get('rows', [])
            if not records:
                break
            
            for record in records:
                name = record.get('quotationName', '') or record.get('name', '')
                if self.is_test_data(name):
                    quotation_id = record.get('id')
                    try:
                        resp = self.client.delete_quotation(quotation_id)
                        if resp.json().get('code') == 200:
                            deleted += 1
                            print(f"  🗑️  删除报价: {name} (ID: {quotation_id})")
                        else:
                            print(f"  ⚠️ 删除报价返回失败: {name} - {resp.json().get('msg')}")
                    except Exception as e:
                        print(f"  ❌ 删除报价失败: {name} - {e}")
            
            total = data.get('total', 0)
            if page * 50 >= total:
                break
            page += 1
        
        self.stats['quotations'] = deleted
        print(f"✅ 已清理 {deleted} 条报价数据")
        return deleted
    
    def clean_customers(self):
        """清理客户数据"""
        print("\n🔍 扫描客户数据...")
        deleted = 0
        page = 1
        
        while True:
            response = self.client.get_customer_list(page=page, size=50)
            data = response.json()
            
            if data.get('code') != 200:
                print(f"⚠️ 获取客户列表失败: {data.get('msg')}")
                break
            
            records = data.get('rows', [])
            if not records:
                break
            
            for record in records:
                name = record.get('customerName', '')  # 客户名称字段是 customerName
                if self.is_test_data(name):
                    customer_id = record.get('id')
                    try:
                        resp = self.client.delete_customer(customer_id)
                        if resp.json().get('code') == 200:
                            deleted += 1
                            print(f"  🗑️  删除客户: {name} (ID: {customer_id})")
                        else:
                            print(f"  ⚠️ 删除客户返回失败: {name} - {resp.json().get('msg')}")
                    except Exception as e:
                        print(f"  ❌ 删除客户失败: {name} - {e}")
            
            total = data.get('total', 0)
            if page * 50 >= total:
                break
            page += 1
        
        self.stats['customers'] = deleted
        print(f"✅ 已清理 {deleted} 条客户数据")
        return deleted
    
    def clean_products(self):
        """清理产品数据"""
        print("\n🔍 扫描产品数据...")
        deleted = 0
        page = 1
        
        while True:
            response = self.client.get_product_list(page=page, size=50)
            data = response.json()
            
            if data.get('code') != 200:
                print(f"⚠️ 获取产品列表失败: {data.get('msg')}")
                break
            
            records = data.get('rows', [])
            if not records:
                break
            
            for record in records:
                name = record.get('productName', '') or record.get('name', '')
                if self.is_test_data(name):
                    product_id = record.get('id')
                    try:
                        resp = self.client.delete_product(product_id)
                        if resp.json().get('code') == 200:
                            deleted += 1
                            print(f"  🗑️  删除产品: {name} (ID: {product_id})")
                        else:
                            print(f"  ⚠️ 删除产品返回失败: {name} - {resp.json().get('msg')}")
                    except Exception as e:
                        print(f"  ❌ 删除产品失败: {name} - {e}")
            
            total = data.get('total', 0)
            if page * 50 >= total:
                break
            page += 1
        
        self.stats['products'] = deleted
        print(f"✅ 已清理 {deleted} 条产品数据")
        return deleted
    
    def run_full_clean(self):
        """执行完整清理"""
        print("=" * 60)
        print("🧹 CRM测试数据清理工具")
        print("=" * 60)
        print(f"\n清理规则: 名称包含 {self.TEST_PREFIXES} 的数据")
        
        # 按依赖顺序清理：报价 -> 商机 -> 联系人 -> 客户 -> 线索 -> 产品
        # 因为报价依赖商机，商机依赖客户，联系人依赖客户
        try:
            self.clean_quotations()      # 1. 先删报价（依赖商机）
            self.clean_businesses()      # 2. 再删商机（依赖客户）
            self.clean_contacts()        # 3. 再删联系人（依赖客户）
            self.clean_customers()       # 4. 再删客户
            self.clean_clues()           # 5. 最后删线索
            self.clean_products()        # 6. 删产品
        except Exception as e:
            print(f"\n❌ 清理过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
        
        # 打印统计
        print("\n" + "=" * 60)
        print("📊 清理统计报告")
        print("=" * 60)
        print(f"  线索:     {self.stats['clues']} 条")
        print(f"  客户:     {self.stats['customers']} 条")
        print(f"  联系人:   {self.stats['contacts']} 条")
        print(f"  商机:     {self.stats['businesses']} 条")
        print(f"  报价:     {self.stats['quotations']} 条")
        print(f"  产品:     {self.stats['products']} 条")
        total = sum(self.stats.values())
        print(f"\n  总计清理: {total} 条数据")
        print("=" * 60)
        
        return self.stats


if __name__ == '__main__':
    cleaner = TestDataCleaner()
    cleaner.run_full_clean()
