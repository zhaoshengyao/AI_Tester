import requests, json

BASE = 'http://192.168.2.97:6090'
CLIENT_ID = 'e5cd7e4891bf95d1d19206ce24a7b32e'

# 发现 /prod-api/auth/login 返回 500: 认证客户端id不能为空
# 说明: 1) api_base_path = /prod-api 正确
#       2) login_path = /auth/login (不是 CRM 的 /system/login)
#       3) client_id 参数位置可能不同

candidates = [
    # client_id 放在 JSON body (带各种字段组合)
    {'path': '/prod-api/auth/login', 'json': {'username': '赵经理', 'password': '123456', 'client_id': CLIENT_ID, 'grant_type': 'password'}},
    {'path': '/prod-api/auth/login', 'json': {'username': '赵经理', 'password': '123456', 'clientid': CLIENT_ID, 'grant_type': 'password'}},
    {'path': '/prod-api/auth/login', 'json': {'username': '赵经理', 'password': '123456', 'client_id': CLIENT_ID}},
    # client_id 放在 header + body
    {'path': '/prod-api/auth/login', 'headers': {'clientid': CLIENT_ID}, 'json': {'username': '赵经理', 'password': '123456', 'grant_type': 'password', 'tenantId': '000000'}},
    {'path': '/prod-api/auth/login', 'headers': {'Authorization': 'Basic ' + CLIENT_ID}, 'json': {'username': '赵经理', 'password': '123456', 'grant_type': 'password'}},
    # form-urlencoded 形式
    {'path': '/prod-api/auth/login', 'data': {'username': '赵经理', 'password': '123456', 'client_id': CLIENT_ID, 'grant_type': 'password'}, 'json': None},
]

for i, c in enumerate(candidates):
    try:
        headers = c.get('headers', {})
        headers.setdefault('Content-Type', 'application/json')
        kwargs = {'headers': headers, 'timeout': 10}
        if c.get('json') is not None:
            kwargs['json'] = c['json']
        if c.get('data'):
            kwargs['data'] = c['data']
            kwargs['headers']['Content-Type'] = 'application/x-www-form-urlencoded'
        r = requests.post(BASE + c['path'], **kwargs)
        try:
            body = r.json()
        except:
            body = {'raw': r.text[:150]}
        flat = json.dumps(body)
        has_token = 'token' in flat.lower() and len(flat) < 3000
        print(f'[{i+1}] {r.status_code} {c["path"]}')
        print(f'  request: headers={list(c.get("headers",{}).keys())} json_keys={list(c.get("json") or c.get("data") or {}).keys()}')
        print(f'  response: code={body.get("code","")} msg={str(body.get("msg",""))[:60]} has_token={has_token}')
        if has_token:
            print(f'  body={flat[:500]}')
        print()
    except Exception as e:
        print(f'[{i+1}] ERR {c["path"]}: {e}')
        print()
