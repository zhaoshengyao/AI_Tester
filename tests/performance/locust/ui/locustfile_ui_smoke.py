from locust import task, between
from locust_plugins.users.playwright import PlaywrightUser, pw
from utils.auth_helper import get_env_config
import os

class CRMUIUser(PlaywrightUser):
    """CRM UI 冒烟压测用户"""

    host = os.getenv("BASE_URL", get_env_config("BASE_URL", "http://192.168.2.97:6089"))
    username = os.getenv("TEST_USERNAME", get_env_config("TEST_USERNAME", "admin"))
    password = os.getenv("TEST_PASSWORD", get_env_config("TEST_PASSWORD", "admin123"))
    wait_time = between(2, 5)

    @task(5)
    @pw
    async def login_and_browse_dashboard(self, page):
        """高频：登录并浏览首页"""
        await page.goto("/")
        await page.fill("input[placeholder='用户名']", self.username)
        await page.fill("input[placeholder='密码']", self.password)
        await page.click("button:has-text('登录')")
        await page.wait_for_selector(".dashboard-content")
        await page.wait_for_timeout(2000)

    @task(3)
    @pw
    async def navigate_customer_management(self, page):
        """中频：访问客户管理页面"""
        await page.goto("/")
        await page.fill("input[placeholder='用户名']", self.username)
        await page.fill("input[placeholder='密码']", self.password)
        await page.click("button:has-text('登录')")
        await page.click("text=客户管理")
        await page.wait_for_selector(".customer-list")
        await page.wait_for_timeout(2000)

    @task(2)
    @pw
    async def navigate_business_management(self, page):
        """低频：访问商机管理页面"""
        await page.goto("/")
        await page.fill("input[placeholder='用户名']", self.username)
        await page.fill("input[placeholder='密码']", self.password)
        await page.click("button:has-text('登录')")
        await page.click("text=商机管理")
        await page.wait_for_selector(".business-list")
        await page.wait_for_timeout(2000)