import requests, json, base64, os, sys
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

BASE = 'http://192.168.2.97:6090/prod-api'
CLIENT_ID = 'e5cd7e4891bf95d1d19206ce24a7b32e'

def encrypt(plain, key_bytes, mode=AES.MODE_ECB, iv=None):
    if mode == AES.MODE_ECB:
        c = AES.new(key_bytes, mode)
    else:
        c = AES.new(key_bytes, mode, iv=iv)
    ct = c.encrypt(pad(plain.encode('utf-8'), 16))
    return base64.b64encode(ct).decode()

def run(idx, enc_pwd, note):
    payload = {
        'username': '赵经理',
        'password': enc_pwd,
        'clientId': CLIENT_ID,
        'tenantId': '000000',
        'grantType': 'password',
    }
    try:
        r = requests.post(BASE + '/auth/login', headers={'Content-Type': 'application/json'},
                          json=payload, timeout=10)
        b = r.json()
        msg = (b.get('msg') or '')[:80]
        flat = json.dumps(b, ensure_ascii=False)
        code = str(b.get('code', ''))
        has_tok = 'access_token' in flat or 'accessToken' in flat
        print(f'[{idx:02d}] {note}')
        print(f'     HTTP {r.status_code} code={code}  has_token={has_tok}')
        print(f'     msg={msg}')
        if has_tok or code == '200':
            print(f'  >>> body={flat[:800]}')
        print()
        return has_tok or code == '200'
    except Exception as e:
        print(f'[{idx:02d}] ERR {note}: {e}\n')
        return False

# 用浏览器实际登录成功: JWT payload 里 clientid=e5cd7e48... 所以 key 应该是 client_id 相关
# CRM 旧系统用的是 AES-128-ECB 加密, key = client_id[:16] = 'e5cd7e4891bf95d1'
idx = 0
keys = {
    'clientId[:16]': CLIENT_ID[:16].encode('utf-8'),
    'clientId[:24]': CLIENT_ID[:24].encode('utf-8'),
    'clientId[:32]': CLIENT_ID[:32].encode('utf-8'),
    'clientId(full)': CLIENT_ID.encode('utf-8'),
    'CLIENT_ID_utf8': CLIENT_ID.encode('utf-8'),
    'hardcoded_16b': b'1234567890123456',
    'hardcoded_32b': b'12345678901234567890123456789012',
    'hex_clientId[:32]': bytes.fromhex(CLIENT_ID[:32]),
}
for kname, k in keys.items():
    try:
        idx += 1
        ep = encrypt('123456', k, AES.MODE_ECB)
        if run(idx, ep, f'AES-ECB key={kname}({len(k)}B) pwd=123456 -> {ep[:20]}...'):
            print(f'  成功! key_len={len(k)} key_bytes={k!r}')
            sys.exit(0)
    except Exception as e:
        print(f'[{idx:02d}] skip {kname}: {e}')

# 再试 CBC 模式 + 各种 IV
for kname, k in keys.items():
    if len(k) not in (16, 24, 32): continue
    for iv in (b'\x00'*16, CLIENT_ID[:16].encode('utf-8'), b'1234567890abcdef'):
        try:
            idx += 1
            ep = encrypt('123456', k, AES.MODE_CBC, iv)
            if run(idx, ep, f'AES-CBC key={kname} iv={iv[:8].hex()}... pwd=123456 -> {ep[:20]}...'):
                print(f'  成功! key={k} iv={iv}')
                sys.exit(0)
        except Exception as e:
            pass

# 最后再试明文 (JWT里userName是"赵经理"所以登录成功过，浏览器应该是明文或者固定加密)
idx += 1
run(idx, '123456', '明文 password=123456')
idx += 1
run(idx, 'MTIzNDU2', 'base64(password=123456)')
idx += 1
run(idx, '123456'.encode().hex(), 'hex(password=123456)')
