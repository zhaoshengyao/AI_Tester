"""
HR 系统冒烟测试 - 第二被测系统示例
演示多系统隔离：本测试只会在 --system hr-demo 时被收集执行
"""
import os
import pytest
import requests


BASE_URL = os.getenv("HR_BASE_URL", "http://192.168.2.97:7080")


@pytest.mark.smoke
def test_hr_service_reachable():
    """验证 HR 系统服务可达"""
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/health", timeout=10)
        # 只要能连通即可（不要求 200，因为示例系统可能未部署）
        assert resp.status_code < 500
    except requests.exceptions.ConnectionError:
        pytest.skip("HR 示例系统未部署，跳过连接测试")


@pytest.mark.smoke
def test_hr_login_endpoint_exists():
    """验证 HR 系统登录接口存在"""
    try:
        resp = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"username": "test", "password": "test"},
            timeout=10
        )
        # 期望返回 401/400（接口存在但认证失败），而不是 404（接口不存在）
        assert resp.status_code != 404, "登录接口不存在"
    except requests.exceptions.ConnectionError:
        pytest.skip("HR 示例系统未部署，跳过接口测试")
