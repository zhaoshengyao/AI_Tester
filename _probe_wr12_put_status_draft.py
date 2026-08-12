# -*- coding: utf-8 -*-
"""探测 WR12：pending 项目 status→draft 是否可通过 PUT 完整 payload 改 status 或 reject/rejectApproval/refuse 其他备选（含 body 带字段）"""
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
H = {"Authorization": f"Bearer {token}", "clientid": ipd_config["client_id"],
     "tenant-id": "000000", "Content-Type": "application/json;charset=UTF-8"}

print(f"[LOGIN OK]")
ts = time.strftime('%Y%m%d%H%M%S')
code = f"WR12B-{ts}"
r = requests.post(f"{api_base}/idmp/project", json={
    "projectCode": code, "projectName": f"WR12B状态回draft探测-{ts}",
    "type": "hardware", "status": "draft", "phase": "concept", "managerId": 1,
    "client": "", "contractNo": "", "startDate": "", "endDate": "",
    "budget": 0, "spent": 0, "progress": 0, "profitRate": 0,
    "description": "WR12B探测", "cloudEnabled": "0", "cloudProject": ""
}, headers=H, timeout=15)
assert r.json().get("code") == 200
# 搜 pid
r2 = requests.get(f"{api_base}/idmp/project/page", params={"projectCode": code, "page": 1, "size": 5}, headers=H, timeout=15)
b2 = r2.json()
rows = b2.get("data", {}).get("rows") if isinstance(b2.get("data"), dict) else b2.get("rows", [])
pid = rows[0]["id"]
print(f"[FOUND] pid={pid}")

# submit → pending
requests.post(f"{api_base}/idmp/project/submit/{pid}", json={}, headers=H, timeout=15)

def show(pid, label):
    r_v = requests.get(f"{api_base}/idmp/project/{pid}", headers=H, timeout=10)
    b_v = r_v.json()
    d = b_v.get("data") if isinstance(b_v.get("data"), dict) else b_v
    print(f"  [{label}] status={d.get('status')} phase={d.get('phase')}")

show(pid, "after submit")

# 先 GET 详情，然后 PUT 完整 payload（改 status=draft）
r_detail = requests.get(f"{api_base}/idmp/project/{pid}", headers=H, timeout=10)
d = r_detail.json()
detail = d.get("data") if isinstance(d.get("data"), dict) else d
print(f"[GET DETAIL] type={detail.get('type')} managerName={detail.get('managerName')} managerId={detail.get('managerId')}")
payload = dict(detail)
payload["status"] = "draft"

print(f"\n[WR12-B-1] PUT /idmp/project → status=draft")
r = requests.put(f"{api_base}/idmp/project", json=payload, headers=H, timeout=15)
print(f"  → code={r.json().get('code')} msg={r.json().get('msg', '')[:80]}")
show(pid, "after PUT status=draft")

# 如果仍 pending → 尝试 submit/rejectApproval/refuse 等更多：reject/approvalReject/cancelSubmit
print(f"\n[WR12-B-2] 更多 reject 候选")
for action in [
    "rejectApproval", "approvalReject", "reject_approval", "reject_audit", "rejectAudit",
    "cancelApproval", "cancelSubmit", "cancel_approval", "cancel_submit",
    "unsubmit", "withdrawApproval", "approvalRevoke", "approvalCancel",
]:
    for p in [{}, {"rejectReason": "WR12探测", "comment": "WR12探测"}]:
        r = requests.post(f"{api_base}/idmp/project/{action}/{pid}", json=p, headers=H, timeout=8)
        try: body = r.json()
        except: body = {}
        code_r = body.get("code")
        if code_r == 200:
            print(f"  ✅ HIT: POST {action}/{pid} payload={p} → code=200 msg={body.get('msg','')[:60]}")
            show(pid, f"after {action}")
            break
        elif code_r != 404:
            print(f"  POST {action}/{pid} → code={code_r} msg={body.get('msg','')[:60]}")
    else: continue
    break
