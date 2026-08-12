import requests, json, base64, os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

BASE = 'http://192.168.2.97:6090'
API = BASE + '/prod-api'
CLIENT_ID = 'e5cd7e4891bf95d1d19206ce24a7b32e'

def enc_pwd(pwd):
    c = AES.new(CLIENT_ID.encode('utf-8'), AES.MODE_ECB)
    return base64.b64encode(c.encrypt(pad(pwd.encode('utf-8'), 16))).decode()

r = requests.post(API + '/auth/login', json={
    'username': '赵经理', 'password': enc_pwd('123456'),
    'clientId': CLIENT_ID, 'grantType': 'password', 'tenantId': '000000',
}, timeout=10)
token = r.json()['data']['access_token']
H = {'Authorization': f'Bearer {token}', 'clientid': CLIENT_ID}

print('=== 1. 系统菜单 (getRouters) ===')
routers = requests.get(API + '/system/menu/getRouters', headers=H, timeout=10).json()
os.makedirs('projects/ipd/docs/analysis', exist_ok=True)
with open('projects/ipd/docs/analysis/菜单结构.json', 'w', encoding='utf-8') as f:
    json.dump(routers, f, ensure_ascii=False, indent=2)
print(json.dumps(routers, ensure_ascii=False, indent=2)[:3500])

print('\n=== 2. 当前用户信息 ===')
profile = requests.get(API + '/system/user/profile', headers=H, timeout=10).json()
print(f'  user keys: {list(profile.get("data",{}).get("user",{}).keys())}')
print(f'  userName={profile["data"]["user"].get("nickName") or profile["data"]["user"].get("userName")}')
print(f'  roles={profile["data"].get("roleGroup")}')

print('\n=== 3. 仪表盘概览 ===')
d = requests.get(API + '/idmp/dashboard/overview', headers=H, timeout=10).json()
data = d.get('data', {})
print(f'  dashboard keys: {list(data.keys())}')
stats = data.get('stats', {})
print(f'  stats: {json.dumps(stats, ensure_ascii=False)[:300]}')
dist = data.get('typeDistribution', [])
print(f'  typeDistribution (项目类型分布): {json.dumps(dist, ensure_ascii=False)[:300]}')
risk_stats = data.get('riskStats', {})
print(f'  riskStats: {json.dumps(risk_stats, ensure_ascii=False)[:300]}')
prog = data.get('projectProgress', [])
print(f'  projectProgress (项目进度): 条数={len(prog)} 样本={json.dumps(prog[:2], ensure_ascii=False)[:400]}')

print('\n=== 4. 项目列表样本 ===')
pj = requests.get(API + '/idmp/project/list', headers=H, params={'pageNum':1,'pageSize':3}, timeout=10).json()
for p in (pj.get('data') or []):
    print(f'  id={p.get("id")} code={p.get("projectCode")} name={p.get("projectName")} type={p.get("type")} status={p.get("status")} phase={p.get("phase")} manager={p.get("managerName")} budget={p.get("budget")}')

print('\n=== 5. 风险规则 ===')
rr = requests.get(API + '/idmp/riskRule/list', headers=H, params={'pageNum':1,'pageSize':10}, timeout=10).json()
for r in rr['data']:
    print(f'  id={r["id"]} code={r["ruleCode"]:<18} name={r["ruleName"]:<14} level={r["level"]:<7} enabled={r["enabled"]} trigger={r.get("triggerCondition")}')

print('\n=== 6. 风险列表 ===')
risks = requests.get(API + '/idmp/risk/list', headers=H, params={'pageNum':1,'pageSize':10}, timeout=10).json()
for r in risks['data']:
    print(f'  id={r["id"]:<22} projId={str(r.get("projectId")):<22} title={str(r.get("title") or r.get("riskName"))[:18]:<18} level={r.get("level"):<7} status={r.get("status")}')

print('\n=== 7. 预算/实际支出 ===')
bd = requests.get(API + '/idmp/budget/list', headers=H, params={'pageNum':1,'pageSize':10}, timeout=10).json()
for b in bd['data']:
    print(f'  id={b["id"]} projId={str(b.get("projectId")):<22} budgetAmt={b.get("amount") or b.get("budgetAmount")} category={b.get("category"):<10} spent={b.get("usedAmount") or b.get("spentAmount")}')

print('\n=== 8. 文档/交付物 ===')
dd = requests.get(API + '/idmp/document/list', headers=H, params={'pageNum':1,'pageSize':10}, timeout=10).json()
for d in dd['data']:
    print(f'  id={d["id"]} projId={str(d.get("projectId")):<22} name={str(d.get("name") or d.get("fileName") or d.get("title"))[:20]:<20} type={d.get("type") or d.get("category"):<10} version={d.get("version")}')

print('\n=== 9. 工作流分类 ===')
wf = requests.get(API + '/workflow/category/list', headers=H, params={'pageNum':1,'pageSize':20}, timeout=10).json()
for c in wf['data']:
    print(f'  id={c["categoryId"]:<22} name={c["categoryName"]:<20} parentId={c.get("parentId")} order={c.get("orderNum")}')

print('\n=== 10. 工作流定义(分页) ===')
wd = requests.get(API + '/workflow/definition/list', headers=H, params={'pageNum':1,'pageSize':10}, timeout=10).json()
print(f'  body top keys: {list(wd.keys())}')
data = wd.get('data')
if isinstance(data, dict):
    rows = data.get('rows', [])
    print(f'  total={data.get("total")} rows_sample(3):')
    for r in rows[:3]:
        print(f'    {json.dumps(r, ensure_ascii=False)[:250]}')
elif isinstance(data, list):
    print(f'  len={len(data)} sample={json.dumps(data[:2], ensure_ascii=False)[:500]}')
else:
    print(f'  sample: {json.dumps(wd, ensure_ascii=False)[:400]}')

print('\n=== 11. 字典 sys_yes_no(验证通用字典) ===')
dy = requests.get(API + '/system/dict/data/type/sys_yes_no', headers=H, timeout=10).json()
for d in dy['data']:
    print(f'  label={d["dictLabel"]} value={d["dictValue"]}')

print('\n已将原始响应保存到 projects/ipd/docs/analysis/ 目录(菜单和 API 基线)。')
