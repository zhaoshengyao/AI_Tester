import requests, json

BASE = 'http://192.168.2.97:6090/prod-api'
CLIENT_ID = 'e5cd7e4891bf95d1d19206ce24a7b32e'

# 已知: clientId 是正确字段 (错误变"认证权限类型不能为空")
# 找 grant_type / account_type / auth_type 这类字段的正确名
grant_keys = ['grantType', 'grant_type', 'authType', 'auth_type', 'loginType', 'login_type', 'accountType', 'account_type']

for gk in grant_keys:
    for gv in ['password', 'pwd', 'account', 'simple', 'default', '1']:
        payload = {
            'username': '赵经理',
            'password': '123456',
            'clientId': CLIENT_ID,
            'tenantId': '000000',
            gk: gv,
        }
        try:
            r = requests.post(BASE + '/auth/login', headers={'Content-Type': 'application/json'},
                              json=payload, timeout=8)
            b = r.json()
            msg = str(b.get('msg',''))[:60]
            flat = json.dumps(b)
            has_token = 'access_token' in flat or 'accessToken' in flat or 'token' in flat.lower() and len(flat) < 2000
            ok = '200' == str(b.get('code',''))
            flag = '🔑' if has_token or ok else '  '
            print(f'{flag} HTTP{r.status_code} clientId + {gk}={gv!r:15s} => code={b.get("code",""):6s} msg={msg}')
            if has_token or ok:
                print(f'  body: {flat[:600]}')
        except Exception as e:
            print(f'  ERR {gk}={gv}: {e}')
