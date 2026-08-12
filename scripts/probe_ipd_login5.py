import requests, json, base64

BASE = 'http://192.168.2.97:6090'
CLIENT_ID = 'e5cd7e4891bf95d1d19206ce24a7b32e'

def rc(idx, path, h_extra=None, json=None, data=None, form_ct=False):
    h = {'Content-Type': 'application/x-www-form-urlencoded' if form_ct else 'application/json'}
    if h_extra: h.update(h_extra)
    kw = {'headers': h, 'timeout': 12}
    if json is not None: kw['json'] = json
    if data is not None: kw['data'] = data
    try:
        r = requests.post(BASE + path, **kw)
        try: b = r.json(); flat = json.dumps(b, ensure_ascii=False)
        except: b = None; flat = r.text[:400]
        has_tok = isinstance(b, dict) and 'token' in json.dumps(b).lower()
        msg = (b or {}).get('msg', '') if isinstance(b, dict) else ''
        rk = list((json or data or {}).keys()) if isinstance((json or data), dict) else []
        print(f'[{idx}] HTTP{r.status_code} {path}')
        print(f'     req_keys={rk} form_ct={form_ct} headers={list(h.keys())}')
        print(f'     msg={str(msg)[:80]}  has_token={has_tok}')
        print(f'     body_sample={flat[:500]}')
        print()
    except Exception as e:
        print(f'[{idx}] ERR {e}\n')

# 从浏览器拿到: 登录后 JWT 的 payload 里 clientid 是对的, 且 localStorage key 是 Admin-Token
# 这说明: 登录成功后返回 data.access_token, 与 CRM 一致. 问题是 IPD 的登录接口是 auth/login 不是 system/login, 且对 clientid 的接收方式不同.

# 方案 X: 从 /idmp 路由前缀出发, 试下在 body 里加 clientid (大写/小写下划线/驼峰)
for c_key in ['clientid', 'clientId', 'client_id', 'ClientId', 'clientID']:
    rc(list(range(99))[0] if False else None, '/prod-api/auth/login', None,
       {'username': '赵经理', 'password': '123456', 'grant_type': 'password', c_key: CLIENT_ID, 'tenantId': '000000'})

# 看起来上面的循环索引乱了, 直接硬编码
idx = 0
for c_key in ['clientid', 'clientId', 'client_id', 'ClientId', 'clientID', 'appid', 'appId', 'app_id']:
    idx += 1
    rc(idx, '/prod-api/auth/login', None,
       {'username': '赵经理', 'password': '123456', 'grant_type': 'password', c_key: CLIENT_ID, 'tenantId': '000000'})

# 方案 Y: header + body 同时传 client_id
idx += 1
rc(idx, '/prod-api/auth/login',
   {'clientid': CLIENT_ID, 'Client-Id': CLIENT_ID, 'X-Client-Id': CLIENT_ID},
   {'username': '赵经理', 'password': '123456', 'grant_type': 'password', 'client_id': CLIENT_ID, 'clientid': CLIENT_ID})

# 方案 Z: 使用 form content-type + Basic auth(带 client_id:client_id 作为 secret) + body 不带 client_id
idx += 1
basic_a = base64.b64encode(f'{CLIENT_ID}:{CLIENT_ID}'.encode()).decode()
rc(idx, '/prod-api/auth/login',
   {'Authorization': f'Basic {basic_a}'},
   None, {'username': '赵经理', 'password': '123456', 'grant_type': 'password'}, form_ct=True)

# 方案 Zb: Basic(client_id:空字符串) + form
idx += 1
basic_b = base64.b64encode(f'{CLIENT_ID}:'.encode()).decode()
rc(idx, '/prod-api/auth/login',
   {'Authorization': f'Basic {basic_b}'},
   None, {'username': '赵经理', 'password': '123456', 'grant_type': 'password'}, form_ct=True)

# 用浏览器已拿到的 token 试探测 API（绕过登录问题）
print('=== 用浏览器登录的 token 探测 GET 接口 ===')
TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJsb2dpblR5cGUiOiJsb2dpbiIsImxvZ2luSWQiOiJzeXNfdXNlcjoyMDg1NjA1NDMwNjE0OTc4NTYxIiwicm5TdHIiOiJuWDZMVjVxMW1Qd3M3ZWpydWJyOHdVekFkaXk5YzdnVCIsImNsaWVudGlkIjoiZTVjZDdlNDg5MWJmOTVkMWQxOTIwNmNlMjRhN2IzMmUiLCJ0ZW5hbnRJZCI6IjAwMDAwMCIsInVzZXJJZCI6MjA4NTYwNTQzMDYxNDk3ODU2MSwidXNlck5hbWUiOiLotbXnu4_nkIYifQ.D-aKu_NQJcKEXWjUoMHkBq7kjEMEOLek5bWdIQOOCso'
hdrs = {'Authorization': f'Bearer {TOKEN}', 'clientid': CLIENT_ID}
for p in [
    '/idmp/project/list?pageNum=1&pageSize=3',
    '/idmp/project/page?pageNum=1&pageSize=3',
    '/idmp/project',
    '/idmp/approval/list?pageNum=1&pageSize=3',
    '/idmp/riskRule/list?pageNum=1&pageSize=3',
    '/dashboard/overview/summary',
    '/dashboard/overview',
    '/workflow/category/list?pageNum=1&pageSize=3',
    '/workflow/formManage/list?pageNum=1&pageSize=3',
    '/workflow/processDefinition/list?pageNum=1&pageSize=3',
    '/workflow/monitor/processInstance/list?pageNum=1&pageSize=3',
    '/workflow/monitor/allTaskWaiting/list?pageNum=1&pageSize=3',
    '/system/menu/build',
    '/user/profile',
]:
    try:
        r = requests.get(BASE + '/prod-api' + p.split('?')[0],
                         headers=hdrs,
                         params=dict(x.split('=') for x in p.split('?')[1].split('&')) if '?' in p else None,
                         timeout=10)
        try: b = r.json(); flat = json.dumps(b, ensure_ascii=False)
        except: flat = r.text[:180]
        code = ''
        msg = ''
        try:
            if isinstance(b, dict): code = str(b.get('code','')); msg = str(b.get('msg',''))[:40]
        except: pass
        total = ''
        try:
            if isinstance(b, dict) and b.get('data') and isinstance(b['data'], dict):
                total = ' total=' + str(b['data'].get('total',''))
        except: pass
        print(f'{r.status_code:3d} GET {p:65s} => code={code:6s}{total} msg={msg}')
        if code == '200' or (r.status_code == 200 and code == ''):
            print(f'   sample: {flat[:350]}')
    except Exception as e:
        print(f'ERR GET {p}: {type(e).__name__}: {e}')
