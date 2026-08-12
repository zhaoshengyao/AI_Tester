# -*- coding: utf-8 -*-
"""Step A+B：赵老板账号登录基线探测 + 项目阶段/状态流转接口清单探测。
输出：projects/ipd/docs/analysis/赵老板角色实测基线.json（含登录态+权限+看板+项目列表+阶段详情候选接口）。
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# ============= 配置（复用 system.yaml + .env 的真实算法）=============
BASE_URL = "http://192.168.2.97:6090"
API = BASE_URL + "/prod-api"
CLIENT_ID = "e5cd7e4891bf95d1d19206ce24a7b32e"
CLIENT_ID_FIELD = "clientId"
GRANT_TYPE = "password"
GRANT_TYPE_FIELD = "grantType"
TENANT_ID = "000000"


def encrypt_pw(pw: str) -> str:
    key = CLIENT_ID.encode("utf-8")  # AES-256: 32B（不是 hex decode）
    if len(key) < 32:
        key = key + b"\x00" * (32 - len(key))
    key = key[:32]
    cipher = AES.new(key, AES.MODE_ECB)
    ct = cipher.encrypt(pad(pw.encode("utf-8"), AES.block_size, style="pkcs7"))
    return ct.hex().lower()


def login(username: str, password: str) -> dict:
    url = API + "/auth/login"
    body = {
        CLIENT_ID_FIELD: CLIENT_ID,
        GRANT_TYPE_FIELD: GRANT_TYPE,
        "username": username,
        "password": encrypt_pw(password),
        "tenantId": TENANT_ID,
    }
    r = requests.post(url, json=body, timeout=20)
    print(f"[login] {username} → HTTP={r.status_code}; body={r.text[:400]}")
    assert r.status_code == 200
    data = r.json()
    assert data.get("code") == 200, f"登录失败 code={data.get('code')} msg={data.get('msg')}"
    return data


def authed_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "clientid": CLIENT_ID,
        "tenant-id": TENANT_ID,
    }


def _get(url: str, token: str, timeout=20):
    r = requests.get(url, headers=authed_headers(token), timeout=timeout)
    print(f"[GET] {url.replace(API,'/api')} → HTTP={r.status_code}; {r.text[:240]}")
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, {"_raw": r.text[:800]}


# =================== Step A：赵老板登录 + 个人信息 + 看板 + 项目列表 ===================
def step_a_zhaoboss_baseline():
    r_login = login("赵老板", "123456")
    tk = r_login["data"]["access_token"]
    expires_in = r_login["data"].get("expires_in")
    user = r_login["data"].get("user") or {}

    # 本人信息接口
    _, user_info = _get(API + "/system/user/profile/info", tk)

    # 角色 / 权限 接口（候选）
    role_info_list = [
        _get(API + "/system/user/profile/roles", tk),
        _get(API + "/system/role/get-select", tk),
        _get(API + "/system/menu/build", tk),  # 动态菜单树（权限判断最准）
    ]

    # 首页看板（统计分析看板模块 = 用户重点）
    _, dash_overview = _get(API + "/idmp/dashboard/overview", tk)
    dash_candidates = [
        _get(API + "/idmp/dashboard/stats", tk),
        _get(API + "/idmp/dashboard/project-status", tk),
        _get(API + "/idmp/dashboard/project-stage", tk),
        _get(API + "/idmp/dashboard/risk-trend", tk),
        _get(API + "/idmp/dashboard/budget-usage", tk),
    ]

    # 项目列表（分页 + 状态/阶段候选筛选）
    proj_base_candidates = [
        _get(API + "/project/page?pageNum=1&pageSize=100", tk),
        _get(API + "/project/list", tk),
        _get(API + "/idmp/project/page?pageNum=1&pageSize=100", tk),
    ]

    # 项目状态 / 阶段 字典（候选，枚举定义类接口）
    enum_candidates = [
        _get(API + "/dict/data/type/project_status", tk),
        _get(API + "/dict/data/type/project_stage", tk),
        _get(API + "/dict/data/type/pm_project_status", tk),
        _get(API + "/system/dict/data/type/project_status", tk),
        _get(API + "/system/dict/data/type/project_stage", tk),
        _get(API + "/project/enum/status", tk),
        _get(API + "/project/enum/stage", tk),
        _get(API + "/idmp/project/enum/status", tk),
        _get(API + "/idmp/project/enum/stage", tk),
        _get(API + "/common/enum/project-status", tk),
        _get(API + "/common/enum/project-stage", tk),
    ]

    return {
        "login": r_login,
        "token": tk,
        "expires_in": expires_in,
        "user": user,
        "user_profile_info": user_info,
        "role_menu_candidates": role_info_list,
        "dashboard_overview": dash_overview,
        "dashboard_candidates": dash_candidates,
        "project_lists": proj_base_candidates,
        "enum_candidates": enum_candidates,
    }


# =================== Step B：针对每个项目探测阶段/状态流转类接口 ===================
def step_b_probe_stage_flow(token: str, project_ids: list[str]):
    """对于赵老板可见的项目ID列表，暴力尝试一批状态流转候选接口。"""
    flow_candidates = []
    for pid in project_ids[:5]:  # 最多探 5 个项目避免太长
        # 详情、阶段、状态流转、审批流
        urls = [
            f"{API}/project/{pid}",
            f"{API}/project/detail/{pid}",
            f"{API}/idmp/project/{pid}",
            f"{API}/idmp/project/detail/{pid}",
            # 阶段相关
            f"{API}/project/{pid}/stage",
            f"{API}/project/{pid}/stages",
            f"{API}/project/{pid}/stage/list",
            f"{API}/idmp/project/{pid}/stage",
            f"{API}/idmp/project/{pid}/stages",
            # 状态/日志
            f"{API}/project/{pid}/status-log",
            f"{API}/project/{pid}/status/history",
            f"{API}/idmp/project/{pid}/status-log",
            # 可用流转动作
            f"{API}/project/{pid}/actions",
            f"{API}/project/{pid}/next-statuses",
            f"{API}/idmp/project/{pid}/actions",
            # 工作流实例（若有的话挂在项目上）
            f"{API}/project/{pid}/workflow/instances",
            f"{API}/idmp/project/{pid}/workflow/instances",
        ]
        for u in urls:
            sc, body = _get(u, token, timeout=10)
            if sc == 200 and (isinstance(body, dict) and body.get("code") in (200, None)) and body.get("data") not in (None, [], {}):
                flow_candidates.append({"project_id": pid, "url": u.replace(API, "/prod-api"), "http_status": sc, "preview": body})

    return flow_candidates


def main():
    out_dir = r"d:\AICode\TestHub\AITestDemo\projects\ipd\docs\analysis"
    os.makedirs(out_dir, exist_ok=True)
    out_file = Path(out_dir) / "赵老板角色实测基线.json"

    step_a = step_a_zhaoboss_baseline()
    tk = step_a["token"]

    # 收集赵老板可见的项目 id（来自 project_lists 第一个成功返回 total 的）
    proj_ids = []
    proj_list_data = None
    for sc, body in step_a["project_lists"]:
        if sc == 200 and isinstance(body, dict) and body.get("code") == 200:
            rows = body.get("data")
            if isinstance(rows, dict):
                r = rows.get("rows") or rows.get("list") or rows.get("records")
                total = rows.get("total")
                if isinstance(r, list):
                    proj_list_data = {"total": total, "count": len(r), "rows": r}
                    for p in r:
                        pid = p.get("projectId") or p.get("id") or p.get("projId")
                        if pid:
                            proj_ids.append(str(pid))
                    if proj_ids:
                        break

    step_b = step_b_probe_stage_flow(tk, proj_ids)

    # 同时把赵经理的看板拿来对比（Step D 基础）
    r_mgr = login("赵经理", "123456")
    tk_mgr = r_mgr["data"]["access_token"]
    _, mgr_dash = _get(API + "/idmp/dashboard/overview", tk_mgr)
    _, mgr_proj = _get(API + "/project/page?pageNum=1&pageSize=100", tk_mgr)

    result = {
        "probe_time": "2026-08-11",
        "actor": "赵老板/123456",
        "step_a_baseline": {
            "login_ok": True,
            "expires_in": step_a.get("expires_in"),
            "user_snapshot": step_a.get("user"),
            "user_profile_info": step_a.get("user_profile_info"),
            "role_menu_candidates_summary": [
                {"preview": str(r)[:500]} for _, r in step_a.get("role_menu_candidates", [])
            ],
            "dashboard_overview": step_a.get("dashboard_overview"),
            "dashboard_candidates": step_a.get("dashboard_candidates"),
            "project_list_summary": proj_list_data,
            "enum_candidates": step_a.get("enum_candidates"),
        },
        "step_b_stage_flow_candidates": step_b,
        "step_d_role_comparison": {
            "赵经理_dashboard_overview": mgr_dash,
            "赵经理_project_list_summary": (lambda b: (isinstance(b, dict) and {"total": ((b.get("data") or {}).get("total")), "count": len(((b.get("data") or {}).get("rows") or []))}) if isinstance(b.get("data"), dict) else {"raw": str(b)[:400]})(mgr_proj),
            "赵老板_vs_赵经理_dashboard_diff_note": "——请人工肉眼对比 overview.stats 与 overview.riskCounts/riskStats 每一项——（脚本后续自动 diff）",
        },
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n✅ 输出：{out_file}（大小 ≈ {out_file.stat().st_size/1024:.1f} KB）")


if __name__ == "__main__":
    main()
