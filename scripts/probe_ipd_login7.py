import requests, json

BASE = 'http://192.168.2.97:6090/prod-api'
CLIENT_ID = 'e5cd7e4891bf95d1d19206ce24a7b32e'

grant_keys = ['grantType', 'grant_type', 'authType', 'auth_type', 'loginType', 'login_type', 'accountType', 'account_type']
grant_values = ['password', 'pwd', 'account', 'simple', 'default', '1']

for gk in grant_keys:
    for gv in grant_values:
        payload = {
            'username': '赵经理',
            'password': '123456',
            'clientId': CLIENT_ID,
            'tenantId': '000000',
        }
        payload[gk] = gv
        try:
            r = requests.post(BASE + '/auth/login', headers={'Content-Type': 'application/json'},
                              json=payload, timeout=8)
            b = r.json()
            msg = (b.get('msg') or '')[:60]
            flat = json.dumps(b)
            code = str(b.get('code', ''))
            has_token = ('access_token' in flat or 'accessToken' in flat or ('token' in flat.lower() and len(flat) < 2000))
            flag = 'KEY ' if has_token or code == '200' else '    '
            print(f'{flag} clientId + {gk}={gv!r:<10} => code={code:<5s} msg={msg!s}')
            if has_token or code == '200':
                print(f'  body: {flat[:600]}')
        except Exception as e:
            print(f'  ERR {gk}={gv}: {type(e).__name__} {e}')
