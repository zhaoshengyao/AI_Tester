# -*- coding: utf-8 -*-
"""探测 WR12~15 所需路由：
1. 驳回审批（reject=reject）pending→draft
2. 阶段回退（phase?toPhase=concept / prevPhase / rollback / downgrade）
3. 预算必填+负数校验（CREATE+UPDATE）
4. 负责人必填校验（managerId=null）
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
H = {"Authorization": f"Bearer {token}", "clientid": ipd_config["client_id"],
     "tenant-id": "000000", "Content-Type": "application/json;charset=UTF-8"}

print(f"[LOGIN OK] 赵老板")

# 1. 先建一个项目，submit（pending），探测 reject（pending→draft）
ts = time.strftime('%Y%m%d%H%M%S')
code = f"WR12-{ts}"
r = requests.post(f"{api_base}/idmp/project", json={
    "projectCode": code, "projectName": f"WR12探测驳回-{ts}",
    "type": "hardware", "status": "draft", "phase": "concept", "managerId": 1,
    "client": "", "contractNo": "", "startDate": "", "endDate": "",
    "budget": 0, "spent": 0, "progress": 0, "profitRate": 0,
    "description": "WR12~15探测专用", "cloudEnabled": "0", "cloudProject": ""
}, headers=H, timeout=15)
assert r.json().get("code") == 200, f"CREATE失败: {r.json()}"

# 搜新项目拿 pid
r2 = requests.get(f"{api_base}/idmp/project/page", params={"projectCode": code, "page": 1, "size": 5}, headers=H, timeout=15)
b2 = r2.json()
rows = b2.get("data", {}).get("rows") if isinstance(b2.get("data"), dict) else b2.get("rows", [])
pid = rows[0]["id"]
print(f"[CREATE+FOUND] pid={pid} status=draft phase=concept code={code}")

# submit
r3 = requests.post(f"{api_base}/idmp/project/submit/{pid}", json={}, headers=H, timeout=15)
print(f"[SUBMIT] code={r3.json().get('code')} msg={r3.json().get('msg', '')[:60]}")

def show_status_phase(label):
    r_v = requests.get(f"{api_base}/idmp/project/{pid}", headers=H, timeout=10)
    b_v = r_v.json()
    d = b_v.get("data") if isinstance(b_v.get("data"), dict) else b_v
    print(f"  [{label}] status={d.get('status')} phase={d.get('phase')}")

show_status_phase("after submit")

# ======================================================
# 1) WR12 探测：驳回审批（pending→draft）路由
# ======================================================
print("\n===== WR12 探测 reject（pending→draft）=====")
reject_actions = ["reject", "deny", "refuse", "disapprove", "decline", "rejectApproval", "approveReject", "cancel", "rollback", "downgrade", "unapprove", "back", "withdraw"]
found_reject = False
for action in reject_actions:
    for payload in [{}, {"rejectReason": "WR12探测驳回", "comment": "WR12探测"}, {"reason": "WR12探测驳回"}]:
        r = requests.post(f"{api_base}/idmp/project/{action}/{pid}", json=payload, headers=H, timeout=10)
        try: body = r.json()
        except: body = {"_raw": r.text[:200]}
        code_r = body.get("code")
        msg = body.get("msg", "")[:80]
        if code_r == 200:
            print(f"  ✅ HIT: POST /idmp/project/{action}/{pid} payload={json.dumps(payload, ensure_ascii=False)} → code=200 msg={msg}")
            show_status_phase(f"after {action}")
            found_reject = True
            break
        elif code_r != 404:
            print(f"  POST /idmp/project/{action}/{pid} payload={json.dumps(payload, ensure_ascii=False)[:40]} → code={code_r} msg={msg}")
    if found_reject: break
if not found_reject:
    # 探测 query param: ?action=reject / ?status=draft 等
    print("  （未命中，尝试其他模式）")
    for extra in [
        ("POST", f"/idmp/project/audit/{pid}?status=draft", {}),
        ("POST", f"/idmp/project/audit/{pid}", {"status": "draft", "rejectReason": "WR12探测"}),
        ("POST", f"/idmp/project/status/{pid}", {"status": "draft"}),
        ("PUT",  f"/idmp/project", {"id": pid, "status": "draft"}),
    ]:
        m, u, p = extra
        r = requests.request(m, f"{api_base}{u}", json=p, headers=H, timeout=10)
        try: body = r.json()
        except: body = {"_raw": r.text[:200]}
        code_r = body.get("code")
        msg = body.get("msg", "")[:80]
        print(f"  {m} {u} → code={code_r} msg={msg}")
        if code_r == 200:
            show_status_phase(f"after {m} {u}")
            break

# 验证当前状态，如果是 pending 则 approve 进入 approved，进入 WR13 phase 回退探测
r_v0 = requests.get(f"{api_base}/idmp/project/{pid}", headers=H, timeout=10)
b_v0 = r_v0.json()
d0 = b_v0.get("data") if isinstance(b_v0.get("data"), dict) else b_v0
if d0.get("status") == "pending":
    # 先 approve → approved + phase auto concept→plan
    r_approve = requests.post(f"{api_base}/idmp/project/approve/{pid}", json={}, headers=H, timeout=15)
    print(f"\n[APPROVE 进入 approved 以便 phase 回退探测] code={r_approve.json().get('code')} msg={r_approve.json().get('msg','')[:60]}")
    show_status_phase("after approve")

# ======================================================
# 2) WR13 探测：阶段回退（phase 回退 plan→concept）
# ======================================================
print("\n===== WR13 探测 phase 回退（plan→concept）=====")
rollback_actions = ["prevPhase", "phasePrev", "rollbackPhase", "phaseRollback", "downgradePhase", "revertPhase", "backPhase", "phaseBack", "setPhase", "changePhase"]
found_phase_back = False
for action in rollback_actions:
    r = requests.post(f"{api_base}/idmp/project/{action}/{pid}", json={}, headers=H, timeout=10)
    try: body = r.json()
    except: body = {"_raw": r.text[:200]}
    code_r = body.get("code")
    msg = body.get("msg", "")[:80]
    if code_r == 200:
        print(f"  ✅ HIT: POST /idmp/project/{action}/{pid} → code=200 msg={msg}")
        show_status_phase(f"after {action}")
        found_phase_back = True
        break
    elif code_r != 404:
        print(f"  POST /idmp/project/{action}/{pid} → code={code_r} msg={msg}")

# 再试 toPhase=concept 与其他 query/body 形式
if not found_phase_back:
    for params in [
        ("POST", f"/idmp/project/phase/{pid}?toPhase=concept", {}),
        ("POST", f"/idmp/project/phase/{pid}", {"toPhase": "concept"}),
        ("POST", f"/idmp/project/phase/{pid}", {"phase": "concept"}),
        ("PUT", f"/idmp/project", {"id": pid, "phase": "concept"}),
    ]:
        m, u, p = params
        r = requests.request(m, f"{api_base}{u}", json=p, headers=H, timeout=10)
        try: body = r.json()
        except: body = {"_raw": r.text[:200]}
        code_r = body.get("code")
        msg = body.get("msg", "")[:80]
        print(f"  {m} {u} payload={p} → code={code_r} msg={msg}")
        if code_r == 200:
            show_status_phase(f"after {m} {u}")

# ======================================================
# 3) WR14 探测：预算必填/负数校验
# ======================================================
print("\n===== WR14 预算校验（budget=null/负数）=====")
# 先尝试 budget=null
for val, lab in [(None, "null"), (-999, "negative"), ("", "empty_string")]:
    try:
        create_body = {
            "projectCode": f"WR14-{lab}-{int(time.time())}",
            "projectName": f"WR14 budget{lab} 探测",
            "type": "hardware", "status": "draft", "phase": "concept",
            "managerId": 1, "client": "", "contractNo": "",
            "startDate": "", "endDate": "",
            "budget": val, "spent": 0, "progress": 0, "profitRate": 0,
            "description": f"WR14 budget{lab}",
            "cloudEnabled": "0", "cloudProject": ""
        }
        if val is None:
            create_body.pop("budget", None)
        r = requests.post(f"{api_base}/idmp/project", json=create_body, headers=H, timeout=15)
        try: body = r.json()
        except: body = {"_raw": r.text[:200]}
        code_r = body.get("code")
        msg = body.get("msg", "")[:80]
        print(f"  CREATE budget={lab} → code={code_r} msg={msg}")
        if code_r == 200:
            print(f"    ✅ budget={lab} 允许通过（未拦截=不强制）")
        else:
            print(f"    ✅ budget={lab} 已拦截（必填/格式校验）")
    except Exception as e:
        print(f"  CREATE budget={lab} 异常: {e}")

# ======================================================
# 4) WR15 探测：负责人（managerId）必填校验
# ======================================================
print("\n===== WR15 managerId 校验（null 时 CREATE）=====")
for val, lab in [(None, "null"), (0, "zero")]:
    try:
        create_body = {
            "projectCode": f"WR15-{lab}-{int(time.time())}",
            "projectName": f"WR15 managerId{lab} 探测",
            "type": "hardware", "status": "draft", "phase": "concept",
            "client": "", "contractNo": "",
            "startDate": "", "endDate": "",
            "budget": 0, "spent": 0, "progress": 0, "profitRate": 0,
            "description": f"WR15 managerId{lab}",
            "cloudEnabled": "0", "cloudProject": ""
        }
        if val is not None:
            create_body["managerId"] = val
        r = requests.post(f"{api_base}/idmp/project", json=create_body, headers=H, timeout=15)
        try: body = r.json()
        except: body = {"_raw": r.text[:200]}
        code_r = body.get("code")
        msg = body.get("msg", "")[:80]
        print(f"  CREATE managerId={lab} → code={code_r} msg={msg}")
        if code_r == 200:
            print(f"    ✅ managerId={lab} 允许通过（未拦截=不强制）")
        else:
            print(f"    ✅ managerId={lab} 已拦截（必填）")
    except Exception as e:
        print(f"  CREATE managerId={lab} 异常: {e}")

# ======================================================
# 清理：删除测试项目（如果是 draft）
# ======================================================
try:
    r_del = requests.delete(f"{api_base}/idmp/project/{pid}", headers=H, timeout=15)
    print(f"\n[CLEANUP] DELETE code={r_del.json().get('code')} msg={r_del.json().get('msg', '')[:60]}")
except Exception as e:
    print(f"[CLEANUP] DELETE 失败: {e}")
