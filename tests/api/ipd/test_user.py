# -*- coding: utf-8 -*-
"""test_user + 未授权 dashboard = AUTH 剩余 smoke
覆盖矩阵行 10-18（USER 部分）。REP-01 合并：dept/role/menu/build 403 三接口用 1 脚本
"""
from __future__ import annotations

import base64
import json
import re


def test_user_profile_manager_name_and_role(authed_session, api_base_url):
    """API-USER-001：赵经理 profile + roleGroup=项目经理。"""
    r = authed_session.get(f"{api_base_url}/system/user/profile", timeout=15)
    assert r.status_code == 200, r.text[:500]
    body = r.json()
    assert body.get("code") == 200, body.get("msg")
    user = (body.get("data") or {}).get("user") or {}
    assert user.get("userName") == "赵经理", f"userName={user.get('userName')}"
    role_group = (body.get("data") or {}).get("roleGroup") or user.get("roleGroup") or ""
    assert role_group == "项目经理" or ("项目经理" in role_group), (
        f"roleGroup 应=项目经理；实际={role_group}"
    )
    # 为 API-USER-009 (OM-07) 保存 userId (string 型)；pytest 函数不应 return 非 None（避免 warning）
    assert user.get("userId") is not None, "userId 缺失"


def test_jwt_userid_matches_profile_numeric_value(
    login_token, authed_session, api_base_url
):
    """API-USER-009（OM-07 新增）：JWT 中 userId（number）== profile userId（string）数值化相等。"""
    import base64
    import json

    # 从 JWT payload 解码 userId（number）
    parts = login_token["access_token"].split(".")
    payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4)))
    jwt_userid_value = None
    for k in ("userId", "user_id", "uid"):
        if k in payload:
            jwt_userid_value = payload[k]
            break
    assert jwt_userid_value is not None, f"JWT payload 无 userId/user_id/uid 字段；payload keys={list(payload.keys())}"
    # profile userId
    r = authed_session.get(f"{api_base_url}/system/user/profile", timeout=15).json()
    profile_userid = (r.get("data") or {}).get("user", {}).get("userId")
    assert profile_userid is not None
    assert int(jwt_userid_value) == int(profile_userid), (
        f"OM-07 JWT userId={jwt_userid_value}（type={type(jwt_userid_value).__name__}） "
        f"vs profile userId={profile_userid}（type={type(profile_userid).__name__}） 数值不一致"
    )
    print(
        f"[INFO API-USER-009] 类型差异 JWT={type(jwt_userid_value).__name__} "
        f"vs profile={type(profile_userid).__name__}，但数值相同 int={int(jwt_userid_value)}；"
        f"登记知识库：类型不一致但值相同（非缺陷）。"
    )


def test_menu_routers_3_first_level_titles(authed_session, api_base_url):
    """API-USER-002：3 一级菜单存在：统计分析看板 / 项目管理 / 工作流。"""
    r = authed_session.get(f"{api_base_url}/system/menu/getRouters", timeout=15)
    body = r.json()
    assert body.get("code") == 200
    data = body.get("data") or []
    assert isinstance(data, list) and len(data) == 3, f"一级菜单数应为 3；实际 len={len(data)}"
    titles = " ".join([json.dumps(x.get("meta") or {}, ensure_ascii=False) for x in data])
    for kw in ("看板", "项目管理", "工作流"):
        assert kw in titles, f"一级菜单缺 {kw}；titles={titles}"


def test_project_manager_dept_role_menu_build_are_403_REP01(
    authed_session, api_base_url
):
    """REP-01 合并三接口（对应 FUNC-ROLE-001/002/003）：项目经理访问 dept/role/menu/build 全 403。"""
    subpaths = [
        "/system/dept/list",
        "/system/role/list",
        "/system/menu/build",
    ]
    for p in subpaths:
        r = authed_session.get(f"{api_base_url}{p}", timeout=15)
        body = r.json()
        code = body.get("code")
        # 403 HTTP 或 业务 code=403（AGENTS.md 任一都算通过）
        ok403 = (r.status_code == 403) or (code == 403)
        assert ok403, (
            f"REP-01 项目经理越权 {p}：HTTP={r.status_code} code={code} msg={body.get('msg')}；"
            f"应 403，不然 = R1 水平越权缺陷"
        )


def test_dict_sys_yes_no_has_2_items(authed_session, api_base_url):
    """API-USER-006：sys_yes_no = {是 Y, 否 N}。"""
    r = authed_session.get(f"{api_base_url}/system/dict/data/type/sys_yes_no", timeout=15).json()
    assert r.get("code") == 200, r.get("msg")
    data = r.get("data") or []
    assert len(data) == 2, f"sys_yes_no 应 2 条；实际 {len(data)}"
    labels = {d.get("dictLabel") for d in data}
    values = {str(d.get("dictValue")) for d in data}
    assert labels == {"是", "否"}, labels
    assert "Y" in values and "N" in values, values


def test_dict_common_status_empty_array_ok(authed_session, api_base_url):
    """API-USER-007：common_status 空数组，不报错（IPD 为代码内枚举，不判缺陷）。"""
    r = authed_session.get(f"{api_base_url}/system/dict/data/type/common_status", timeout=15).json()
    assert r.get("code") == 200
    assert r.get("data") == [], f"common_status 预期空数组；实际={r.get('data')}"


def test_user_list_total_16_paginated(authed_session, api_base_url):
    """API-USER-008：user/list {total,rows} 结构 total=16。"""
    r = authed_session.get(f"{api_base_url}/system/user/list", timeout=15).json()
    assert r.get("code") == 200
    total = r.get("total")
    rows = r.get("rows")
    assert total == 16, f"user/list total={total}（预期 16，与实测基线一致）"
    assert isinstance(rows, list) and len(rows) <= 16, f"rows={len(rows)}"
    # 保存用于安全专项 SEC-R4-001 快照的证据样例（PII 脱敏/未脱敏证据，实际由 security 下脚本重复保存 JSON）
    import json as _json
    # 打印字段名（不打印实际值，避免 CI 日志 PII 泄漏）
    if rows:
        keys = sorted(list(rows[0].keys()))
        print(f"[INFO API-USER-008] user/list 单行字段 keys={keys}（给 R4 合规判断用）")


def test_dashboard_without_token_returns_401_or_403(api_base_url):
    """API-AUTH-008：未授权 dashboard 访问必须 401/403，绝不 200。"""
    import requests

    r = requests.get(f"{api_base_url}/idmp/dashboard/overview", timeout=15)
    # HTTP 401/403 直接通过
    if r.status_code in (401, 403):
        return
    # 若 HTTP=200 但业务 code=401/403 也通过
    try:
        body = r.json()
        assert body.get("code") in (401, 403), (
            f"API-AUTH-008 失败：HTTP={r.status_code} code={body.get('code')}，"
            f"未授权访问 dashboard 居然 200=高危（SEC-UNAUTH 中对应行失败，触发 stop）"
        )
    except Exception as e:
        raise AssertionError(f"dashboard 响应非 JSON：{e}; text={r.text[:500]}")
