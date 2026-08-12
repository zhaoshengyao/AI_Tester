import requests, json

BASE = 'http://192.168.2.97:6090'
CLIENT_ID = 'e5cd7e4891bf95d1d19206ce24a7b32e'
payload = {
    'username': '赵经理',
    'password': '123456',
    'client_id': CLIENT_ID,
    'grant_type': 'password',
    'tenantId': '000000'
}

candidates = [
    '/prod-api/system/login',
    '/api/system/login',
    '/auth/login',
    '/api/auth/login',
    '/prod-api/auth/login',
    '/login',
    '/system/login',
    '/auth/oauth/token',
    '/prod-api/auth/oauth/token',
]

for path in candidates:
    try:
        r = requests.post(BASE + path,
                          headers={'clientid': CLIENT_ID, 'Content-Type': 'application/json'},
                          json=payload, timeout=8)
        try:
            body = r.json()
        except:
            body = {'msg': r.text[:80]}
        code = str(body.get('code', ''))
        flat = json.dumps(body)
        token_found = 'token' in flat.lower() and len(flat) < 3000
        msg = str(body.get('msg', ''))[:40]
        print(f'{r.status_code:3d} POST {path:40s} => code={code:6s} token={token_found} msg={msg}')
    except Exception as e:
        print(f'ERR POST {path:40s} => {e}')
