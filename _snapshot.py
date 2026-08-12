# -*- coding: utf-8 -*-
import requests, sys
sys.path.insert(0, r"d:/AICode/TestHub/AITestDemo/tests/api/ipd")
from conftest import _load_system_yaml_auth, _load_dotenv, DOTENV, SYSTEM_YAML, _encrypt_aes_256_ecb_hex

auth_cfg = _load_system_yaml_auth(SYSTEM_YAML)
env = _load_dotenv(DOTENV)
client_id = env.get("API_CLIENT_ID") or auth_cfg["client_id"]
base = (env.get("API_BASE_URL") or "http://192.168.2.97:6090/prod-api").rstrip("/")
login_path = auth_cfg["login_path"]
if login_path.startswith("/prod-api/"): login_path = login_path[len("/prod-api"):]
login_url = base + "/" + login_path.lstrip("/")
pw = _encrypt_aes_256_ecb_hex(env.get("TEST_PASSWORD") or "123456", client_id)
body = {
    auth_cfg["client_id_field"]: client_id,
    auth_cfg["grant_type_field"]: auth_cfg["grant_type"],
    "username": env.get("TEST_USERNAME") or "赵经理",
    "password": pw,
}
for k, v in (auth_cfg.get("extra_fields") or {}).items(): body.setdefault(k, v)
r = requests.post(login_url, json=body, timeout=15)
tk = (r.json().get("data") or {}).get("access_token")
print("login token ok:", bool(tk))
H = {"Authorization": f"Bearer {tk}", "clientid": client_id, "tenant-id": "000000"}
dash = requests.get(base + "/idmp/dashboard/overview", headers=H, timeout=15).json()
lst = requests.get(base + "/idmp/project/list", headers=H, timeout=15).json()
print("stats.total =", (dash.get("data") or {}).get("stats", {}).get("total"))
print("list len   =", len(lst.get("data") or []))
print("typeDist    =", (dash.get("data") or {}).get("typeDistribution"))
lst_group = {}
for p in (lst.get("data") or []):
    t = p.get("type") or "unknown"
    lst_group[t] = lst_group.get(t, 0) + 1
print("list group  =", lst_group)
risk_stats = (dash.get("data") or {}).get("riskStats")
risk_list = requests.get(base + "/idmp/risk/list", headers=H, timeout=15).json().get("data") or []
print("riskStats   =", risk_stats)
levels = {"high": 0, "medium": 0, "low": 0}
for rl in risk_list:
    lv = rl.get("level") or "low"
    if lv in levels: levels[lv] += 1
print("risk/list agg=", levels)
page = requests.get(base + "/idmp/project/page", headers=H, params={"pageNum": 99, "pageSize": 10}, timeout=15).json()
print("page code/total/rows.len =", page.get("code"), page.get("total"), len(page.get("rows") or []))
# WF category 过滤测试
wf_def = requests.get(base + "/workflow/definition/list", headers=H, params={"pageNum": 1, "pageSize": 100}, timeout=15).json()
wf_cat = requests.get(base + "/workflow/category/list", headers=H, timeout=15).json()
cat_idmp = next((c.get("id") for c in (wf_cat.get("data") or []) if "idmp" in str(c.get("categoryName") or "").lower()), None)
print("WF cat IDMP id =", cat_idmp, "total =", wf_def.get("total"))
for pname in ["categoryId", "category_id", "category"]:
    r2 = requests.get(base + "/workflow/definition/list", headers=H, params={"pageNum":1,"pageSize":100,pname:cat_idmp}, timeout=15).json()
    rows = r2.get("rows") or []
    names = sorted({r.get("categoryName") for r in rows if r.get("categoryName")})
    print(f"  param {pname} total={r2.get('total')} distinct categoryNames={names[:6]}")
