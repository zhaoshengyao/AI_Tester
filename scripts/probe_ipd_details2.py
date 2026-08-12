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

def safe(v, width=0):
    s = '' if v is None else str(v)
    return f'{s:<{width}}' if width else s

print('=== 7. 预算/实际支出 ===')
bd = requests.get(API + '/idmp/budget/list', headers=H, params={'pageNum':1,'pageSize':10}, timeout=10).json()
for b in bd['data']:
    print(f'  id={safe(b.get("id")):<22} projId={safe(b.get("projectId")):<22} budgetAmt={safe(b.get("amount") or b.get("budgetAmount") or b.get("budget")):<10} category={safe(b.get("category") or b.get("budgetName") or b.get("name")):<12} spent={safe(b.get("usedAmount") or b.get("spentAmount") or b.get("actualAmount"))}')
    print(f'     all_keys={list(b.keys())}')

print('\n=== 8. 文档/交付物 ===')
dd = requests.get(API + '/idmp/document/list', headers=H, params={'pageNum':1,'pageSize':10}, timeout=10).json()
for d in dd['data']:
    print(f'  id={safe(d.get("id")):<22} projId={safe(d.get("projectId")):<22} name={safe(d.get("name") or d.get("fileName") or d.get("title")):<20} type={safe(d.get("type") or d.get("category") or d.get("docType")):<10} version={safe(d.get("version"))}')
    print(f'     all_keys={list(d.keys())}')

print('\n=== 9. 工作流分类(带流程数) ===')
wf = requests.get(API + '/workflow/category/list', headers=H, params={'pageNum':1,'pageSize':50}, timeout=10).json()
for c in wf['data']:
    print(f'  id={safe(c.get("categoryId")):<22} name={safe(c.get("categoryName")):<22} parentId={safe(c.get("parentId")):<6} order={safe(c.get("orderNum")):<4} flowCount={safe((c.get("flowDefinitionList") or []).__len__() if hasattr(c.get("flowDefinitionList") or [], "__len__") else None)}')

print('\n=== 10. 工作流定义(分页) 修正为 categoryId 参数形式 ===')
# 尝试两种形式: ?pageNum=1&pageSize=10 和 ?categoryId=xxx
wd1 = requests.get(API + '/workflow/definition/list', headers=H, params={'pageNum':1,'pageSize':10}, timeout=10).json()
print(f'  [无分类] top keys={list(wd1.keys())} sample_row_keys: ', end='')
rows = wd1.get('rows') or (wd1.get('data') or {}).get('rows') if isinstance(wd1.get('data'), dict) else None
if rows and len(rows): print(list(rows[0].keys()))
else:
    if isinstance(wd1.get('data'), list) and wd1['data']: print(list(wd1['data'][0].keys()))
    else: print(f'(无 rows) body={json.dumps(wd1, ensure_ascii=False)[:200]}')

# 用第一个 categoryId 过滤
cat_list = wf['data']
if cat_list:
    cid = cat_list[0].get('categoryId')
    wd2 = requests.get(API + '/workflow/definition/list', headers=H, params={'pageNum':1,'pageSize':10,'categoryId':cid}, timeout=10).json()
    print(f'  [categoryId={cid}] body_sample={json.dumps(wd2, ensure_ascii=False)[:350]}')

print('\n=== 11. 项目详情(带所有字段) ===')
p = requests.get(API + '/idmp/project/2086985374914007042', headers=H, timeout=10).json()
pdata = p.get('data') or {}
print(f'  project detail keys: {list(pdata.keys())}')
for k in ['id','projectCode','projectName','type','status','phase','client','managerName','startDate','endDate','budget','spent','progress','description']:
    print(f'    {k}: {pdata.get(k)}')

print('\n=== 12. 项目变更列表(带 projectId) ===')
ch = requests.get(API + '/idmp/change/list', headers=H, params={'pageNum':1,'pageSize':10,'projectId':'2086985374914007042'}, timeout=10).json()
print(f'  code={ch.get("code")} msg={str(ch.get("msg"))[:60]}')
if isinstance(ch.get('data'), list):
    for r in ch['data'][:3]:
        print(f'    {json.dumps(r, ensure_ascii=False)[:250]}')
elif isinstance(ch.get('data'), dict):
    d = ch['data']
    rows = d.get('rows') or d.get('list') or []
    for r in rows[:3]:
        print(f'    {json.dumps(r, ensure_ascii=False)[:250]}')
    print(f'  total={d.get("total","")}')
else:
    print(f'  sample={json.dumps(ch, ensure_ascii=False)[:350]}')

print('\n=== 13. 字典: ipd 专用枚举 (项目状态/项目类型/项目阶段/风险级别/审批状态) ===')
for dtype in ['ipd_project_status', 'ipd_project_type', 'ipd_project_phase', 'ipd_risk_level', 'ipd_risk_status', 'ipd_approval_status', 'ipd_budget_category']:
    r = requests.get(API + f'/system/dict/data/type/{dtype}', headers=H, timeout=10).json()
    code = r.get('code')
    rows = r.get('data') or []
    if code == 200 and rows:
        print(f'  [{dtype}] code=200 {len(rows)}项: ', end='')
        print(','.join(f'{x.get("dictLabel")}={x.get("dictValue")}' for x in rows[:6]))
    else:
        print(f'  [{dtype}] code={code} msg={str(r.get("msg"))[:40]} (字典不存在)')

print('\n=== 14. 尝试 项目分页 page 接口(带 type 过滤) ===')
for t in ['hardware','software']:
    pp = requests.get(API + '/idmp/project/page', headers=H, params={'pageNum':1,'pageSize':3,'type':t}, timeout=10).json()
    total = (pp.get('data') or {}).get('total', '?') if isinstance(pp.get('data'), dict) else '?'
    print(f'  type={t} total={total} code={pp.get("code")} msg={str(pp.get("msg"))[:30]}')
