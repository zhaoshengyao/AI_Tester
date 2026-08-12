# -*- coding: utf-8 -*-
"""P0-1c-3：验证 PHASE 路由 POST /idmp/project/phase/{pid}?toPhase=xxx
已知：
  submit=POST /idmp/project/submit/{pid} ✅
  approve=POST /idmp/project/approve/{pid} ✅ (auto phase concept→plan)
  phase=POST /idmp/project/phase/{pid} 路由存在（缺 toPhase 参数）
"""
import sys, json, time, requests
from pathlib import Path
REPO = Path(r"d:\AICode\TestHub\AITestDemo")
sys.path.insert(0, str(REPO / "tests" / "api" / "ipd"))
from conftest import _load_system_yaml_auth, _load_dotenv, _do_login_request, _encrypt_aes_256_ecb_hex

auth_cfg = _load_system_yaml_auth(REPO / "projects" / "ipd" / "system.yaml")
dotenv = _load_dotenv(REPO / "projects" / "ipd" / ".env")
ipd_config = {"base_url": dotenv.get("BASE_URL"), "api_base_url": dotenv.get("API_BASE_URL"),
              "username": "赵老板", "password": "123456",
              "client_id": dotenv.get("API_CLIENT_ID") or auth_cfg.get("client_id"), "auth": auth_cfg}
api_base = ipd_config["api_base_url"]
def encrypt_password(pw): return _encrypt_aes_256_ecb_hex(pw, ipd_config["client_id"])

data = _do_login_request("赵老板", "123456", ipd_config, encrypt_password, api_base)
token = data["access_token"]
headers = {"Authorization": f"Bearer {token}", "clientid": ipd_config["client_id"],
           "tenant-id": "000000", "Content-Type": "application/json;charset=UTF-8"}
print(f"[LOGIN OK]")

# 1) 新建+submit+approve
ts = time.strftime('%Y%m%d%H%M%S')
code = f"PHASE-{ts}"
r = requests.post(f"{api_base}/idmp/project", json={"projectCode": code, "projectName": f"阶段探测-{ts}",
    "type": "hardware", "status": "draft", "phase": "concept", "managerId": 1,
    "client": "", "contractNo": "", "startDate": "", "endDate": "",
    "budget": 0, "spent": 0, "progress": 0, "profitRate": 0,
    "description": "phase探测", "cloudEnabled": "0", "cloudProject": ""}, headers=headers, timeout=15)
assert r.json().get("code") == 200
r2 = requests.get(f"{api_base}/idmp/project/page", params={"projectCode": code, "page": 1, "size": 5}, headers=headers, timeout=15)
b2 = r2.json()
rows = b2.get("data", {}).get("rows") if isinstance(b2.get("data"), dict) else b2.get("rows", [])
pid = rows[0]["id"]
print(f"[CREATE+FOUND] pid={pid} status=draft phase=concept")

# submit
r3 = requests.post(f"{api_base}/idmp/project/submit/{pid}", json={}, headers=headers, timeout=15)
print(f"[SUBMIT] code={r3.json().get('code')}")
# approve
r4 = requests.post(f"{api_base}/idmp/project/approve/{pid}", json={}, headers=headers, timeout=15)
print(f"[APPROVE] code={r4.json().get('code')}")

# verify
r_v = requests.get(f"{api_base}/idmp/project/{pid}", headers=headers, timeout=10)
b_v = r_v.json()
d_v = b_v.get("data") if isinstance(b_v.get("data"), dict) else b_v
print(f"[AFTER APPROVE] status={d_v.get('status')} phase={d_v.get('phase')}")

# 2) 探测 phase 路由=POST /idmp/project/phase/{pid}?toPhase=development
print("\n===== 探测 PHASE 路由（plan→development）=====")
for toPhase in ["development", "dev", "开发", "开发中"]:
    # 方式1：query param
    r = requests.post(f"{api_base}/idmp/project/phase/{pid}", params={"toPhase": toPhase}, json={}, headers=headers, timeout=10)
    body = r.json()
    print(f"  POST /idmp/project/phase/{pid}?toPhase={toPhase} → code={body.get('code')} msg={body.get('msg', '')[:100]}")
    if body.get("code") == 200:
        r_v = requests.get(f"{api_base}/idmp/project/{pid}", headers=headers, timeout=10)
        b_v = r_v.json()
        d_v = b_v.get("data") if isinstance(b_v.get("data"), dict) else b_v
        print(f"    → after phase: status={d_v.get('status')} phase={d_v.get('phase')}")
        break
    # 方式2：body param
    r = requests.post(f"{api_base}/idmp/project/phase/{pid}", json={"toPhase": toPhase}, headers=headers, timeout=10)
    body = r.json()
    print(f"  POST /idmp/project/phase/{pid} body={{toPhase:{toPhase}}} → code={body.get('code')} msg={body.get('msg', '')[:100]}")
    if body.get("code") == 200:
        r_v = requests.get(f"{api_base}/idmp/project/{pid}", headers=headers, timeout=10)
        b_v = r_v.json()
        d_v = b_v.get("data") if isinstance(b_v.get("data"), dict) else b_v
        print(f"    → after phase: status={d_v.get('status')} phase={d_v.get('phase')}")
        break

# 3) 探测 phase development→closed
print("\n===== 探测 PHASE 路由（development→closed）=====")
for toPhase in ["closed", "close", "结项", "已完成", "done", "finish"]:
    r = requests.post(f"{api_base}/idmp/project/phase/{pid}", params={"toPhase": toPhase}, json={}, headers=headers, timeout=10)
    body = r.json()
    print(f"  POST /idmp/project/phase/{pid}?toPhase={toPhase} → code={body.get('code')} msg={body.get('msg', '')[:100]}")
    if body.get("code") == 200:
        r_v = requests.get(f"{api_base}/idmp/project/{pid}", headers=headers, timeout=10)
        b_v = r_v.json()
        d_v = b_v.get("data") if isinstance(b_v.get("data"), dict) else b_v
        print(f"    → after phase: status={d_v.get('status')} phase={d_v.get('phase')}")
        break

# 4) 清理
r_del = requests.delete(f"{api_base}/idmp/project/{pid}", headers=headers, timeout=10)
print(f"\n[CLEANUP] DELETE code={r_del.json().get('code')} msg={r_del.json().get('msg', '')[:80]}")
