import requests, json

BASE = 'http://192.168.2.97:6090'
CLIENT_ID = 'e5cd7e4891bf95d1d19206ce24a7b32e'

def run_case(idx, path, headers=None, json_body=None, data_body=None):
    h = {'Content-Type': 'application/json'}
    if headers: h.update(headers)
    try:
        if data_body is not None:
            h['Content-Type'] = 'application/x-www-form-urlencoded'
            r = requests.post(BASE + path, headers=h, data=data_body, timeout=10)
        else:
            r = requests.post(BASE + path, headers=h, json=json_body, timeout=10)
        try:
            body = r.json()
            flat = json.dumps(body, ensure_ascii=False)
        except:
            body = None
            flat = r.text[:300]
        has_token = isinstance(body, dict) and 'token' in json.dumps(body).lower()
        msg = ''
        if isinstance(body, dict):
            msg = str(body.get('msg') or body.get('message') or '')[:60]
        req_keys = list((json_body or data_body or {}).keys()) if isinstance((json_body or data_body), dict) else []
        print(f'[{idx}] HTTP{r.status_code} {path}')
        print(f'     req_keys: {req_keys}  headers: {list(h.keys())}')
        print(f'     resp: msg={msg}  has_token={has_token}')
        if has_token or 'access_token' in flat:
            print(f'     body_sample: {flat[:600]}')
        if not has_token and msg:
            print(f'     body_sample: {flat[:400]}')
        print()
    except Exception as e:
        print(f'[{idx}] ERR {path}: {type(e).__name__}: {e}')
        print()

# 6 种组合
cases = [
    ('/prod-api/auth/login', None, {'username': '赵经理', 'password': '123456', 'client_id': CLIENT_ID, 'grant_type': 'password'}),
    ('/prod-api/auth/login', None, {'username': '赵经理', 'password': '123456', 'clientid': CLIENT_ID, 'grant_type': 'password'}),
    ('/prod-api/auth/login', None, {'username': '赵经理', 'password': '123456', 'client_id': CLIENT_ID}),
    ('/prod-api/auth/login', {'clientid': CLIENT_ID}, {'username': '赵经理', 'password': '123456', 'grant_type': 'password', 'tenantId': '000000'}),
    ('/prod-api/auth/login', {'Authorization': 'Basic ' + CLIENT_ID}, {'username': '赵经理', 'password': '123456', 'grant_type': 'password'}),
]
for i, (p, h, j) in enumerate(cases, 1):
    run_case(i, p, h, j)

# form 形式
run_case(7, '/prod-api/auth/login', None, None, {'username': '赵经理', 'password': '123456', 'client_id': CLIENT_ID, 'grant_type': 'password'})
