import requests, json, base64

BASE = 'http://192.168.2.97:6090'
CLIENT_ID = 'e5cd7e4891bf95d1d19206ce24a7b32e'
# Basic auth 格式是 base64(client_id:client_secret), 先用 client_id 单独试试
BASIC = base64.b64encode(f'{CLIENT_ID}:'.encode()).decode()

def run_case(idx, path, headers=None, json_body=None, data_body=None, params=None):
    h = {'Content-Type': 'application/json'}
    if headers: h.update(headers)
    try:
        kwargs = {'headers': h, 'timeout': 12}
        if data_body is not None:
            h['Content-Type'] = 'application/x-www-form-urlencoded'
            kwargs['data'] = data_body
        else:
            kwargs['json'] = json_body
        if params: kwargs['params'] = params
        r = requests.post(BASE + path, **kwargs)
        try: body = r.json(); flat = json.dumps(body, ensure_ascii=False)
        except: body = None; flat = r.text[:400]
        has_tok = isinstance(body, dict) and 'token' in json.dumps(body).lower()
        msg = ''
        if isinstance(body, dict): msg = str(body.get('msg') or body.get('message') or '')[:80]
        rk = list((json_body or data_body or {}).keys()) if isinstance((json_body or data_body), dict) else []
        print(f'[{idx}] HTTP{r.status_code} {path}')
        print(f'     req_keys={rk}  params={list(params.keys()) if params else None}  headers={list(h.keys())}')
        print(f'     msg={msg}  has_token={has_tok}')
        if has_tok: print(f'     body={flat[:600]}')
        else: print(f'     body_sample={flat[:400]}')
        print()
    except Exception as e:
        print(f'[{idx}] ERR: {type(e).__name__}: {e}\n')

i = 0
# A. 把 client_id 当 query string 参数
for q in [{'client_id': CLIENT_ID}, {'clientid': CLIENT_ID}]:
    i += 1
    run_case(i, '/prod-api/auth/login', None,
             {'username': '赵经理', 'password': '123456', 'grant_type': 'password'}, None, q)

# B. Basic auth + form body
i += 1
run_case(i, '/prod-api/auth/login',
         {'Authorization': f'Basic {BASIC}'},
         None, {'username': '赵经理', 'password': '123456', 'grant_type': 'password'})

# C. CRM 形式 /system/login
i += 1
run_case(i, '/prod-api/system/login', {'clientid': CLIENT_ID},
         {'username': '赵经理', 'password': '123456', 'client_id': CLIENT_ID, 'grant_type': 'password', 'tenantId': '000000'})

# D. 加密密码 + /auth/login
try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    import base64
    key = CLIENT_ID[:16].encode('utf-8')
    cipher = AES.new(key, AES.MODE_ECB)
    ct = cipher.encrypt(pad('123456'.encode('utf-8'), 16))
    enc_pwd = base64.b64encode(ct).decode()
except Exception as e:
    enc_pwd = 'V+GwtuX+DsY4rxGNZ9hZSg=='  # 复用 CRM 示例密文
    print(f'[enc] 使用默认加密密码 fallback: {e}')
print(f'[enc] AES-256-ECB 加密后的 123456 = {enc_pwd}\n')

i += 1
run_case(i, '/prod-api/auth/login', {'clientid': CLIENT_ID},
         {'username': '赵经理', 'password': enc_pwd, 'client_id': CLIENT_ID, 'grant_type': 'password'})

# E. 尝试 /oauth/token
i += 1
run_case(i, '/prod-api/oauth/token', {'Authorization': f'Basic {BASIC}'}, None,
         {'username': '赵经理', 'password': '123456', 'grant_type': 'password'})

# F. 把 login_path 切回 system/login + auth header
i += 1
run_case(i, '/prod-api/system/login', {'Authorization': f'Basic {BASIC}'},
         {'username': '赵经理', 'password': enc_pwd, 'grant_type': 'password'})
