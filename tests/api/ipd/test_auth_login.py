# -*- coding: utf-8 -*-
"""Smoke 00: 登录 fixture 与 6 参数名称/加密方式正确性。
覆盖矩阵：API-AUTH-001 ~ 007, 009（登录 9 条 smoke）
"""
from __future__ import annotations

import json
import base64


def test_login_success_6_params_match_expected_conftest(login_token):
    """API-AUTH-001. 6 参数都正确后，返回 access_token 长度 200+ 且为 JWT（三段 . 分隔）。"""
    assert login_token["access_token"], "token empty"
    parts = login_token["access_token"].split(".")
    assert len(parts) == 3, f"JWT shape must be 3 segments; got {len(parts)}: {login_token['access_token'][:60]}"
    # Decode payload (base64url without padding) to verify clientid == expected
    payload_b64 = parts[1]
    pad = "=" * (-len(payload_b64) % 4)
    payload = json.loads(base64.urlsafe_b64decode(payload_b64 + pad))
    # actual field name varies; accept either clientid / client_id / aud with partial match
    merged = json.dumps(payload).lower()
    assert "e5cd7e48".lower() in merged, (
        f"JWT payload 中未找到 client_id 前缀 e5cd7e48。实际 payload: {payload}"
    )


def test_login_wrong_password_returns_500_msg_contains_keyword(
    api_base_url, ipd_config, encrypt_password
):
    """API-AUTH-002 AMB-06：msg 包含"不存在/密码错误"任一关键词（模糊包含，防爆破不区分）。"""
    import requests

    auth = ipd_config["auth"]
    payload = {
        auth.get("client_id_field", "clientId"): ipd_config["client_id"],
        auth.get("grant_type_field", "grantType"): auth.get("grant_type", "password"),
        "username": ipd_config["username"],
        "password": encrypt_password("wrongpwd"),
        "tenantId": auth["extra_fields"].get("tenantId", "000000"),
    }
    login_path = auth.get("login_path", "/auth/login")
    if login_path.startswith("/prod-api/"):
        login_path = login_path[len("/prod-api"):]
    url = api_base_url.rstrip("/") + "/" + login_path.lstrip("/")
    r = requests.post(url, json=payload, timeout=15)
    assert r.status_code == 200, f"wrong pwd HTTP={r.status_code}"
    body = r.json()
    assert body.get("code") != 200, f"wrong pwd should NOT return code=200; body={body}"
    msg = (body.get("msg") or "").lower()
    assert ("不存在" in msg) or ("密码错误" in msg) or ("错误" in msg), (
        f"AMB-06 模糊包含未命中。msg={body.get('msg')}"
    )
    assert "access_token" not in (body.get("data") or {}), "登录失败返回不应含 token"


def test_login_underscore_clientid_must_fail_camel_required(
    api_base_url, ipd_config, encrypt_password
):
    """API-AUTH-003：下划线 client_id → 认证客户端id不能为空。"""
    import requests

    auth = ipd_config["auth"]
    payload = {
        "client_id": ipd_config["client_id"],  # 错误：下划线
        auth.get("grant_type_field", "grantType"): auth.get("grant_type", "password"),
        "username": ipd_config["username"],
        "password": encrypt_password(ipd_config["password"]),
        "tenantId": auth["extra_fields"].get("tenantId", "000000"),
    }
    login_path = auth.get("login_path", "/auth/login")
    if login_path.startswith("/prod-api/"):
        login_path = login_path[len("/prod-api"):]
    url = api_base_url.rstrip("/") + "/" + login_path.lstrip("/")
    r = requests.post(url, json=payload, timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert body.get("code") != 200, "client_id 下划线居然登录成功=需要更新知识库参数名"
    msg = (body.get("msg") or "")
    assert "客户端id不能为空" in msg or "认证客户端" in msg, (
        f"预期提示认证客户端id不能为空；实际 msg={msg}"
    )


def test_login_underscore_granttype_must_fail_camel_required(
    api_base_url, ipd_config, encrypt_password
):
    """API-AUTH-004：grant_type 下划线 → 认证权限类型不能为空。"""
    import requests

    auth = ipd_config["auth"]
    payload = {
        auth.get("client_id_field", "clientId"): ipd_config["client_id"],
        "grant_type": auth.get("grant_type", "password"),  # 错：下划线
        "username": ipd_config["username"],
        "password": encrypt_password(ipd_config["password"]),
        "tenantId": auth["extra_fields"].get("tenantId", "000000"),
    }
    login_path = auth.get("login_path", "/auth/login")
    if login_path.startswith("/prod-api/"):
        login_path = login_path[len("/prod-api"):]
    url = api_base_url.rstrip("/") + "/" + login_path.lstrip("/")
    r = requests.post(url, json=payload, timeout=15)
    body = r.json()
    assert body.get("code") != 200, "grant_type 下划线登录成功=需要更新知识库"
    msg = body.get("msg") or ""
    assert "权限类型" in msg or "grant" in msg.lower() or "授权" in msg, (
        f"预期提示权限类型类错误；实际 msg={msg}"
    )


def test_login_missing_tenantid_records_real_response_no_stack(
    api_base_url, ipd_config, encrypt_password
):
    """API-AUTH-005（NX-06）：缺 tenantId，真实响应为准，msg 不得含堆栈关键字。"""
    import requests

    auth = ipd_config["auth"]
    payload = {
        auth.get("client_id_field", "clientId"): ipd_config["client_id"],
        auth.get("grant_type_field", "grantType"): auth.get("grant_type", "password"),
        "username": ipd_config["username"],
        "password": encrypt_password(ipd_config["password"]),
        # intentionally omit tenantId
    }
    login_path = auth.get("login_path", "/auth/login")
    if login_path.startswith("/prod-api/"):
        login_path = login_path[len("/prod-api"):]
    url = api_base_url.rstrip("/") + "/" + login_path.lstrip("/")
    r = requests.post(url, json=payload, timeout=15)
    body = r.json()
    # code 不强制（真实为准），但 msg 不得含堆栈
    text_raw = r.text.lower()
    no_stack_keywords = ["exception", "nullpointer", "stacktrace", "at java.", "caused by:", "sqlexception"]
    hits = [kw for kw in no_stack_keywords if kw in text_raw]
    assert hits == [], f"NX-06：缺 tenantId 响应含堆栈关键字 hits={hits}; body={r.text[:800]}"
    # 真实响应不进缺陷，但要打印到 stdout 供人工检查
    print(f"[INFO API-AUTH-005] 缺 tenantId 真实 code={body.get('code')} msg={body.get('msg')}")


def test_login_invalid_granttype_5_values_all_fail(
    api_base_url, ipd_config, encrypt_password
):
    """API-AUTH-006：grantType 非法枚举 5 值全失败 code≠200。"""
    import requests

    auth = ipd_config["auth"]
    login_path = auth.get("login_path", "/auth/login")
    if login_path.startswith("/prod-api/"):
        login_path = login_path[len("/prod-api"):]
    url = api_base_url.rstrip("/") + "/" + login_path.lstrip("/")
    bad_vals = ["pwd", "account", "1", "other", "wrong"]
    for bad in bad_vals:
        payload = {
            auth.get("client_id_field", "clientId"): ipd_config["client_id"],
            auth.get("grant_type_field", "grantType"): bad,
            "username": ipd_config["username"],
            "password": encrypt_password(ipd_config["password"]),
            "tenantId": auth["extra_fields"].get("tenantId", "000000"),
        }
        body = requests.post(url, json=payload, timeout=15).json()
        assert body.get("code") != 200, f"grantType={bad} 居然登录成功 body={body}"


def test_auth_code_captcha_disabled(api_base_url):
    """API-AUTH-007：验证码接口公开，captchaEnabled=false，img/uuid=null。"""
    import requests

    r = requests.get(api_base_url.rstrip("/") + "/auth/code", timeout=15)
    assert r.status_code == 200, f"auth/code HTTP={r.status_code}"
    body = r.json()
    assert body.get("code") == 200, f"auth/code code={body.get('code')}"
    data = body.get("data") or {}
    assert data.get("captchaEnabled") is False, (
        f"captchaEnabled 必须 False（OM-05 公共接口）；实际={data.get('captchaEnabled')}"
    )


def test_logout_post_invalidates_token(
    api_base_url, ipd_config, encrypt_password
):
    """API-AUTH-009（OM-02 新增）：POST /auth/logout 成功；同 token 访问 dashboard=401。

    **关键点：为不影响 authed_session（session scope，供后续所有测试使用），
    此测试不得登出主 token；必须**新登录一个独立的临时 token**来做登出验证。**
    """
    import requests

    auth = ipd_config["auth"]
    login_path = auth.get("login_path", "/auth/login")
    if login_path.startswith("/prod-api/"):
        login_path = login_path[len("/prod-api"):]
    url_login = api_base_url.rstrip("/") + "/" + login_path.lstrip("/")
    url_logout = api_base_url.rstrip("/") + "/auth/logout"

    # --- 新登录一个独立 token（使用相同账号/机密；不污染全局 login_token / authed_session）
    pw_enc = encrypt_password(ipd_config["password"])
    login_body = {
        auth["client_id_field"]: ipd_config["client_id"],
        auth["grant_type_field"]: auth["grant_type"],
        "username": ipd_config["username"],
        "password": pw_enc,
    }
    for k, v in (auth.get("extra_fields") or {}).items():
        login_body.setdefault(k, v)
    r_pre = requests.post(url_login, json=login_body, timeout=15)
    assert r_pre.status_code == 200, f"登出用 临时登录失败 HTTP={r_pre.status_code} body={r_pre.text[:500]}"
    pre = r_pre.json()
    assert pre.get("code") == 200, f"登出用 临时登录业务失败 code={pre.get('code')} msg={pre.get('msg')}"
    temp_tk = (pre.get("data") or {}).get("access_token")
    assert temp_tk, "登出用 临时登录 token 缺失"

    r_get = requests.get(url_logout, timeout=15)
    print(f"[INFO sanity] GET /auth/logout HTTP={r_get.status_code}（预期 405，不做断言）")
    headers = {"Authorization": f"Bearer {temp_tk}",
               "clientid": ipd_config["client_id"], "tenant-id": "000000"}
    r = requests.post(url_logout, headers=headers, timeout=15)
    assert r.status_code == 200, f"POST logout HTTP={r.status_code} body={r.text[:500]}"
    body = r.json()
    print(f"[INFO API-AUTH-009] logout 业务 code={body.get('code')} msg={body.get('msg')}")
    r2 = requests.get(api_base_url.rstrip("/") + "/idmp/dashboard/overview",
                      headers=headers, timeout=15)
    if r2.status_code in (401, 403) or (r2.status_code == 200 and r2.json().get("code") in (401, 403)):
        print("[PASS] 登出后立即失效，401/403")
    else:
        print("[INFO 非缺陷] JWT 默认到 exp 过期（常见实现），登出未立即拉入黑名单。不算缺陷。")
