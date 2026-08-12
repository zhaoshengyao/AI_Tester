# -*- coding: utf-8 -*-
"""独立脚本：现场验证 DEF-WR-007/008（IDOR 真越权 vs 假code=200）
与 DEF-WR-009~013（CREATE budget/managerId 未校验 vs 脚本断言错）。
本脚本不依赖 conftest fixture，与 pytest 完全隔离，拿到原始响应与数据写入证据。
"""
import sys, json, time, requests
from pathlib import Path

REPO = Path(r"d:\AICode\TestHub\AITestDemo")
sys.path.insert(0, str(REPO / "tests" / "api" / "ipd"))
from conftest import _load_system_yaml_auth, _load_dotenv, _encrypt_aes_256_ecb_hex

auth_cfg = _load_system_yaml_auth(REPO / "projects" / "ipd" / "system.yaml")
dotenv = _load_dotenv(REPO / "projects" / "ipd" / ".env")
client_id = dotenv.get("API_CLIENT_ID") or auth_cfg.get("client_id")
api_base = dotenv["API_BASE_URL"]

def login(username, password):
    auth_config = {
        "base_url": dotenv["BASE_URL"], "api_base_url": api_base,
        "username": username, "password": password, "client_id": client_id, "auth": auth_cfg
    }
    def enc(pw): return _encrypt_aes_256_ecb_hex(pw, client_id)
    payload = {
        auth_cfg.get("client_id_field", "clientId"): client_id,
        auth_cfg.get("grant_type_field", "grantType"): auth_cfg.get("grant_type", "password"),
        "username": username, "password": enc(password),
    }
    for k, v in (auth_cfg.get("extra_fields") or {}).items():
        payload.setdefault(k, v)
    r = requests.post(f"{api_base}/auth/login", json=payload, timeout=15)
    assert r.status_code == 200 and r.json().get("code") == 200, f"[{username}]登录失败 {r.text[:500]}"
    body = r.json()
    data = body.get("data") or {}
    token = data.get("access_token")
    assert token, f"[{username}] access_token缺失 body={json.dumps(body,ensure_ascii=False)[:500]}"
    user = data.get("user") or {}
    if not user:
        # 尝试 JWT 解析拿默认值（不影响功能，user 字段仅用于打印+默认 managerId 兜底 1）
        user = {"userId": 1, "userName": username, "roleGroup": ""}
    print(f"[LOGIN OK] {username}: userId={user.get('userId')} userName={user.get('userName')} roleGroup={user.get('roleGroup')} access_token_len={len(token)}")
    headers = {"Authorization": f"Bearer {token}", "clientid": client_id, "tenant-id": "000000",
               "Content-Type": "application/json;charset=UTF-8"}
    return headers, user

boss_h, boss_user = login("赵老板", "123456")
mgr_h, mgr_user  = login("赵经理", "123456")

def detail(h, pid, label=""):
    r = requests.get(f"{api_base}/idmp/project/{pid}", headers=h, timeout=15)
    b = r.json()
    d = b.get("data") if isinstance(b.get("data"), dict) else b
    print(f"  [GET详情{label}] pid={pid} projectName={d.get('projectName')!r} status={d.get('status')} phase={d.get('phase')} managerId={d.get('managerId')} managerName={d.get('managerName')} budget={d.get('budget')}")
    return d

# ==========================================
# PART A：DEF-WR-007/008 独立验证（赵经理 vs 赵老板 全新专用项目）
# ==========================================
print("\n" + "="*80)
print("PART A：DEF-WR-007/008 IDOR 越权真实验证")
print("="*80)

ts = time.strftime('%Y%m%d%H%M%S') + f"-{int(time.time())%1000:03d}"
code = f"IDOR-{ts}"
# 1) 赵老板创建 draft → get pid
r = requests.post(f"{api_base}/idmp/project", json={
    "projectCode": code, "projectName": f"IDOR-越权验证-{ts}",
    "type": "hardware", "status": "draft", "phase": "concept",
    "managerId": int(boss_user.get("userId") or 1),
    "budget": 1000, "spent": 0, "progress": 0, "profitRate": 0,
    "client": "", "contractNo": "", "startDate": "", "endDate": "",
    "description": "IDOR专用", "cloudEnabled": "0", "cloudProject": ""
}, headers=boss_h, timeout=15)
print(f"[赵老板 CREATE] HTTP={r.status_code} biz_code={r.json().get('code')} msg={r.json().get('msg','')[:60]}")
# 查 pid
r2 = requests.get(f"{api_base}/idmp/project/page",
                  params={"projectCode": code, "page": 1, "size": 5}, headers=boss_h, timeout=15)
b2 = r2.json()
rows = b2.get("data", {}).get("rows") if isinstance(b2.get("data"), dict) else b2.get("rows", [])
assert rows, "赵老板创建项目后搜索失败"
pid = rows[0]["id"]
print(f"[赵老板项目] pid={pid}")
before = detail(boss_h, pid, " 赵老板初始")

# 2) 赵老板 submit → pending
requests.post(f"{api_base}/idmp/project/submit/{pid}", json={}, headers=boss_h, timeout=15)
detail(boss_h, pid, " 赵老板 submit后")

# 3) 赵经理尝试 approve 赵老板项目 = DEF-WR-007 复现
print(f"\n[DEF-WR-007 复现] 赵经理 POST approve/{pid}")
r = requests.post(f"{api_base}/idmp/project/approve/{pid}", json={}, headers=mgr_h, timeout=15)
b = r.json()
print(f"  → HTTP={r.status_code} biz_code={b.get('code')} msg={b.get('msg','')[:80]}")
after_approve = detail(boss_h, pid, " 赵老板视角 after 赵经理 approve attempt")
mgr_view_approve = detail(mgr_h, pid, " 赵经理视角 after 赵经理 approve attempt")
# 判定：真越权 = 状态真变 approved；假越权 = code=200 但 status 仍 pending
if after_approve.get("status") == "approved":
    print(f"\n🟥【DEF-WR-007 真实越权】赵经理 approve 请求后，项目 status=pending → approved ✅ 数据已写。被系统问题 = 后端权限控制失效，非脚本问题")
else:
    print(f"\n🟨【DEF-WR-007 假阳性】赵经理 approve code=200，但 status 实际仍 {after_approve.get('status')!r}（静默 no-op）")
    print(f"  → 根因 = 后端为了统一返回值用 code=200 代替业务 fail 码，造成脚本误判；需改脚本以 GET 详情变更为断言，改缺陷状态为【已关闭=误报】或降为【后端接口返回规范缺失】")

# 4) 若 approved → 赵经理尝试 phase 推进 closed = DEF-WR-008 复现
if after_approve.get("status") == "approved":
    print(f"\n[DEF-WR-008 复现] 赵经理 POST phase/{pid}?toPhase=closed")
    r = requests.post(f"{api_base}/idmp/project/phase/{pid}?toPhase=closed", json={}, headers=mgr_h, timeout=15)
    b = r.json()
    print(f"  → HTTP={r.status_code} biz_code={b.get('code')} msg={b.get('msg','')[:80]}")
    after_phase = detail(boss_h, pid, " 赵老板视角 after 赵经理 phase closed attempt")
    if after_phase.get("phase") == "closed" or after_phase.get("status") == "closed":
        print(f"\n🟥【DEF-WR-008 真实越权】赵经理 phase 请求后 phase=plan → closed ✅ 数据真变。被系统问题 = 后端权限控制失效，非脚本问题")
    else:
        print(f"\n🟨【DEF-WR-008 假阳性】赵经理 phase code=200，但 phase 实际仍 {after_phase.get('phase')!r}")

# ==========================================
# PART B：DEF-WR-009~013（budget/managerId 5 子场景独立验证）
# ==========================================
print("\n" + "="*80)
print("PART B：DEF-WR-009~013 budget/managerId 未校验 独立验证")
print("="*80)

cases = [
    ("DEF-WR-009 budget=null",   lambda: {"budget": "__MISSING__"}),
    ("DEF-WR-010 budget=-999",   lambda: {"budget": -999}),
    ("DEF-WR-011 budget=''",     lambda: {"budget": ""}),
    ("DEF-WR-012 managerId=null",lambda: {"managerId": "__MISSING__"}),
    ("DEF-WR-013 managerId=0",   lambda: {"managerId": 0}),
]
for label, kwargs_fn in cases:
    extra = kwargs_fn()
    ts2 = time.strftime('%H%M%S') + f"-{int(time.time())%1000:03d}"
    body = {
        "projectCode": f"{label.split()[0][-3:]}-{ts2}",
        "projectName": f"{label.split()[0]}-{ts2}",
        "type": "software", "status": "draft", "phase": "concept",
        "client": "", "contractNo": "", "startDate": "", "endDate": "",
        "spent": 0, "progress": 0, "profitRate": 0,
        "description": label, "cloudEnabled": "0", "cloudProject": ""
    }
    # 默认 managerId=赵老板，默认 budget=0（如果该场景不是测 managerId/budget 本身）
    if "managerId" not in [k for k,_ in cases if k==label][0]:
        body["managerId"] = int(boss_user.get("userId") or 1)
    if "budget" not in label:
        body["budget"] = 0
    # 应用该场景的字段变化
    for k, v in extra.items():
        if v == "__MISSING__":
            body.pop(k, None)
        else:
            body[k] = v

    r = requests.post(f"{api_base}/idmp/project", json=body, headers=boss_h, timeout=15)
    b = r.json()
    code_r = b.get("code")
    msg_r = b.get("msg", "")[:100]
    print(f"\n[{label}]")
    sent_keys = sorted(body.keys())
    print(f"  发送 body key 列表 = {sent_keys}")
    if "budget" in label:
        print(f"  budget 实际发送值 = {json.dumps(body.get('budget', '<MISSING>'), ensure_ascii=False)}")
    else:
        print(f"  managerId 实际发送值 = {json.dumps(body.get('managerId', '<MISSING>'), ensure_ascii=False)}")
    print(f"  后端返回 HTTP={r.status_code} biz_code={code_r} msg={msg_r}")
    if code_r == 200:
        # 搜 GET 详情确认数据真的被写入（=真未拦截，而非 200 空响应不写）
        r2 = requests.get(f"{api_base}/idmp/project/page",
                          params={"projectCode": body["projectCode"], "page": 1, "size": 5}, headers=boss_h, timeout=15)
        b2 = r2.json()
        rows = b2.get("data", {}).get("rows") if isinstance(b2.get("data"), dict) else b2.get("rows", [])
        if rows:
            pid_v = rows[0]["id"]
            dv = detail(boss_h, pid_v, label)
            # 判定字段实际写入值
            if "budget" in label:
                actual_budget = dv.get("budget")
                if actual_budget in (None, "", 0, "0"):
                    print(f"  🟥【被测系统问题】budget 异常值 code=200 ✅ 并且项目真实创建（GET 可搜到 pid={pid_v}）；实际 budget={actual_budget!r}；非脚本问题")
                else:
                    print(f"  🟥【被测系统问题】项目真实存在 budget={actual_budget!r}（非空/非负未拦截）；被测系统问题")
            else:
                actual_mid = dv.get("managerId")
                actual_mname = dv.get("managerName")
                print(f"  🟥【被测系统问题】managerId 异常值 code=200 ✅ 并且项目真实创建 pid={pid_v}；实际 managerId={actual_mid!r} managerName={actual_mname!r}；被测系统校验缺失，非脚本问题")
            # 清理
            try: requests.delete(f"{api_base}/idmp/project/{pid_v}", headers=boss_h, timeout=10)
            except: pass
        else:
            print(f"  🟨【DEF 假阳性可疑】biz_code=200 但 GET page 搜不到项目 → 后端可能 code=200 但业务层实际未写；脚本需改断言")
    else:
        print(f"  ✅【后端校验已拦截】biz_code={code_r} msg={msg_r}；被测系统有校验；此前脚本 WR14/15 打缺陷=脚本问题（需要修脚本移除误报）")
