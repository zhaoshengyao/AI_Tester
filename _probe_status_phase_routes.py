# -*- coding: utf-8 -*-
"""P0-1c-2：已知 submit 路由=POST /idmp/project/submit/{pid}；
推测其他写路由也是 /idmp/project/{action}/{pid} 模式。
用 boss_authed_session 直接探测 approve/nextPhase/close 等路由。
"""
import sys, json, time, os
from pathlib import Path
REPO = Path(r"d:\AICode\TestHub\AITestDemo")
sys.path.insert(0, str(REPO / "tests" / "api" / "ipd"))

import requests

BASE = "http://192.168.2.97:6090/prod-api"
USERNAME = "赵老板"
PASSWORD = "123456"

# ---- 登录（复用 conftest 的加密逻辑）----
from conftest import _load_system_yaml_auth, _load_dotenv, _do_login_request, _encrypt_aes_256_ecb_hex

auth_cfg = _load_system_yaml_auth(REPO / "projects" / "ipd" / "system.yaml")
dotenv = _load_dotenv(REPO / "projects" / "ipd" / ".env")
ipd_config = {
    "base_url": dotenv.get("BASE_URL", "http://192.168.2.97:6090"),
    "api_base_url": dotenv.get("API_BASE_URL", "http://192.168.2.97:6090/prod-api"),
    "username": dotenv.get("TEST_USERNAME", "赵经理"),
    "password": dotenv.get("TEST_PASSWORD", "123456"),
    "client_id": dotenv.get("API_CLIENT_ID") or auth_cfg.get("client_id"),
    "auth": auth_cfg,
}
api_base = ipd_config["api_base_url"]

# 手动构建 encrypt_password 函数（不依赖 pytest fixture）
def encrypt_password(pw: str) -> str:
    key = ipd_config["client_id"]
    return _encrypt_aes_256_ecb_hex(pw, key)

# 登录赵老板
data = _do_login_request(USERNAME, PASSWORD, ipd_config, encrypt_password, api_base)
token = data["access_token"]
headers = {
    "Authorization": f"Bearer {token}",
    "clientid": ipd_config["client_id"],
    "tenant-id": "000000",
    "Content-Type": "application/json;charset=UTF-8",
}
print(f"[LOGIN OK] 赵老板 token len={len(token)}")

# ---- 1) 新建一个专用探测项目 ----
ts = time.strftime('%Y%m%d%H%M%S')
probe_code = f"PROBE-{ts}"
probe_name = f"探测项目-{ts}"
create_payload = {
    "projectCode": probe_code,
    "projectName": probe_name,
    "type": "hardware",
    "status": "draft",
    "phase": "concept",
    "managerId": 1,
    "client": "", "contractNo": "", "startDate": "", "endDate": "",
    "budget": 0, "spent": 0, "progress": 0, "profitRate": 0,
    "description": "WR探测专用", "cloudEnabled": "0", "cloudProject": ""
}
r = requests.post(f"{api_base}/idmp/project", json=create_payload, headers=headers, timeout=15)
body = r.json()
print(f"[CREATE] HTTP={r.status_code} code={body.get('code')} msg={body.get('msg')}")
assert body.get("code") == 200, f"CREATE 失败: {body}"

# 搜新项目拿 pid
r2 = requests.get(f"{api_base}/idmp/project/page", params={"projectCode": probe_code, "page": 1, "size": 5}, headers=headers, timeout=15)
body2 = r2.json()
# 兼容两种格式
if "data" in body2 and isinstance(body2["data"], dict):
    rows = body2["data"].get("rows") or body2["data"].get("list") or []
elif "rows" in body2:
    rows = body2.get("rows") or []
else:
    rows = body2.get("data") or []
assert len(rows) > 0, f"搜不到新项目 {probe_code}: {body2}"
pid = rows[0].get("id") or rows[0].get("projectId")
print(f"[FOUND] pid={pid} name={rows[0].get('projectName')} status={rows[0].get('status')} phase={rows[0].get('phase')}")

# ---- 2) 已知 submit 路由=POST /idmp/project/submit/{pid} → 先 submit ----
r3 = requests.post(f"{api_base}/idmp/project/submit/{pid}", json={}, headers=headers, timeout=15)
body3 = r3.json()
print(f"[SUBMIT] POST /idmp/project/submit/{pid} → HTTP={r3.status_code} code={body3.get('code')} msg={body3.get('msg')}")

# 验证 status 变化
r4 = requests.get(f"{api_base}/idmp/project/{pid}", headers=headers, timeout=15)
body4 = r4.json()
detail = body4.get("data") if isinstance(body4.get("data"), dict) else body4
print(f"[VERIFY] after submit: status={detail.get('status')} phase={detail.get('phase')}")

# ---- 3) 探测 approve/audit/pass 路由 ----
# 路由模式：POST /idmp/project/{action}/{pid}
approve_actions = ["approve", "audit", "pass", "review", "agree", "ratify", "confirm", "check"]
print("\n===== 探测 approve 路由（pending→approved）=====")
for action in approve_actions:
    r = requests.post(f"{api_base}/idmp/project/{action}/{pid}", json={}, headers=headers, timeout=10)
    try: body = r.json()
    except: body = {"_raw": r.text[:300]}
    code = body.get("code")
    msg = body.get("msg", "")
    hit = "✅ HIT" if code == 200 else ""
    print(f"  POST /idmp/project/{action}/{pid} → HTTP={r.status_code} code={code} msg={msg[:80]} {hit}")
    if code == 200:
        # 验证 status 变化
        r_v = requests.get(f"{api_base}/idmp/project/{pid}", headers=headers, timeout=10)
        b_v = r_v.json()
        d_v = b_v.get("data") if isinstance(b_v.get("data"), dict) else b_v
        print(f"    → after {action}: status={d_v.get('status')} phase={d_v.get('phase')}")
        if d_v.get("status") == "approved":
            print(f"  ✅✅✅ FOUND APPROVE ROUTE: POST /idmp/project/{action}/{pid}")
            break

# ---- 4) 探测 phase 推进路由 ----
phase_actions = ["nextPhase", "advance", "advancePhase", "phaseNext", "promote", "gotoPhase", "setPhase", "changePhase", "movePhase", "phase", "startPlan", "startDevelopment", "startDev", "complete", "close", "finish", "archive"]
print("\n===== 探测 phase 推进路由（concept→plan→dev→closed）=====")
for action in phase_actions:
    # 尝试无 payload 和带 payload 两种
    for payload in [{}, {"phase": "plan"}, {"targetPhase": "plan"}, {"nextPhase": "plan"}]:
        r = requests.post(f"{api_base}/idmp/project/{action}/{pid}", json=payload, headers=headers, timeout=10)
        try: body = r.json()
        except: body = {"_raw": r.text[:300]}
        code = body.get("code")
        msg = body.get("msg", "")
        if code == 200:
            r_v = requests.get(f"{api_base}/idmp/project/{pid}", headers=headers, timeout=10)
            b_v = r_v.json()
            d_v = b_v.get("data") if isinstance(b_v.get("data"), dict) else b_v
            print(f"  ✅ HIT: POST /idmp/project/{action}/{pid} payload={json.dumps(payload, ensure_ascii=False)} → code=200 after: status={d_v.get('status')} phase={d_v.get('phase')}")
            break
    else:
        # 只打印非 404 的
        if code != 404:
            print(f"  POST /idmp/project/{action}/{pid} → HTTP={r.status_code} code={code} msg={msg[:80]}")

# ---- 5) 探测 PATCH /idmp/project/{pid} ----
print("\n===== 探测 PATCH /idmp/project/{pid}（UPDATE）=====")
patch_payload = {"id": pid, "projectName": probe_name + "-EDITED", "budget": 100}
r = requests.patch(f"{api_base}/idmp/project/{pid}", json=patch_payload, headers=headers, timeout=10)
try: body = r.json()
except: body = {"_raw": r.text[:300]}
print(f"  PATCH /idmp/project/{pid} → HTTP={r.status_code} code={body.get('code')} msg={body.get('msg', '')[:80]}")
if body.get("code") == 200:
    r_v = requests.get(f"{api_base}/idmp/project/{pid}", headers=headers, timeout=10)
    b_v = r_v.json()
    d_v = b_v.get("data") if isinstance(b_v.get("data"), dict) else b_v
    print(f"    → after PATCH: projectName={d_v.get('projectName')} budget={d_v.get('budget')}")

# ---- 6) 探测 PUT /idmp/project/{pid} 带 _method=patch 或 X-HTTP-Method-Override ----
print("\n===== 探测 POST /idmp/project/{pid} 带 X-HTTP-Method-Override=PATCH =====")
r = requests.post(f"{api_base}/idmp/project/{pid}", json=patch_payload, headers={**headers, "X-HTTP-Method-Override": "PATCH"}, timeout=10)
try: body = r.json()
except: body = {"_raw": r.text[:300]}
print(f"  POST + Override PATCH → HTTP={r.status_code} code={body.get('code')} msg={body.get('msg', '')[:80]}")

# ---- 7) 探测 POST /idmp/project/update（body 带 id）----
print("\n===== 探测 POST /idmp/project/update（body 带 id）=====")
r = requests.post(f"{api_base}/idmp/project/update", json=patch_payload, headers=headers, timeout=10)
try: body = r.json()
except: body = {"_raw": r.text[:300]}
print(f"  POST /idmp/project/update → HTTP={r.status_code} code={body.get('code')} msg={body.get('msg', '')[:80]}")

# ---- 8) 清理：删除探测项目 ----
r_del = requests.delete(f"{api_base}/idmp/project/{pid}", headers=headers, timeout=10)
try: body_del = r_del.json()
except: body_del = {"_raw": r_del.text[:300]}
print(f"\n[CLEANUP] DELETE /idmp/project/{pid} → HTTP={r_del.status_code} code={body_del.get('code')} msg={body_del.get('msg', '')[:80]}")

print("\n===== 探测完成 =====")
