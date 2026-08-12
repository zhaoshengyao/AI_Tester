# -*- coding: utf-8 -*-
"""验证到底是 hex→bytes(16B) 还是 str.encode(UTF-8)(32B) 能登录成功。"""
import sys, requests, json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

sys.path.insert(0, r"d:\AICode\TestHub\AITestDemo\tests\api\ipd")
from conftest import _load_system_yaml_auth, _load_dotenv, DOTENV, SYSTEM_YAML, api_base_url as _  # noqa

auth_cfg = _load_system_yaml_auth(SYSTEM_YAML)
env = _load_dotenv(DOTENV)
client_id = env.get("API_CLIENT_ID") or auth_cfg["client_id"]
username = env.get("TEST_USERNAME") or "赵经理"
password = env.get("TEST_PASSWORD") or "123456"
login_path = auth_cfg["login_path"]
if login_path.startswith("/prod-api/"):
    login_path = login_path[len("/prod-api"):]
url = (env.get("API_BASE_URL") or "http://192.168.2.97:6090/prod-api").rstrip("/") + "/" + login_path.lstrip("/")
print("login URL:", url)

# Method 1: hex→bytes (16B) — 失败
# Method 2: str.encode('utf-8') as raw key bytes (32B for this 32 hex ASCII chars) — 之前实际用的这个
# Method 3: str + latin-1 / ascii encode same as utf-8 for pure hex
# Method 4: 16 bytes + zero pad到 32 (测试用例中曾经怀疑过)
def enc(way, pw: str, cid: str) -> str:
    if way == "hex2bytes_16":
        key = bytes.fromhex(cid)  # 16
        if len(key) == 16:
            key = key + b"\x00" * 16  # pad to 32
    elif way == "raw32_utf8":
        key = cid.encode("utf-8")  # 32 bytes for 32-char ascii hex
    elif way == "raw16_utf8_pad_to_32":
        key = cid[:16].encode("utf-8").ljust(32, b"\x00")
    else:
        raise ValueError
    if len(key) not in (16, 24, 32):
        raise ValueError(f"bad key len {len(key)}")
    if len(key) == 16:
        key = key + b"\x00" * 16
    cipher = AES.new(key, AES.MODE_ECB)
    ct = cipher.encrypt(pad(pw.encode("utf-8"), AES.block_size))
    return ct.hex().lower()

payload_base = {
    auth_cfg["client_id_field"]: client_id,
    auth_cfg["grant_type_field"]: auth_cfg["grant_type"],
    "username": username,
    "tenantId": auth_cfg["extra_fields"]["tenantId"],
}
for way in ["hex2bytes_16", "raw32_utf8", "raw16_utf8_pad_to_32"]:
    pw_enc = enc(way, password, client_id)
    r = requests.post(url, json={**payload_base, "password": pw_enc}, timeout=20)
    try:
        b = r.json()
    except Exception as e:
        b = {"text": r.text}
    token_ok = isinstance(b.get("data"), dict) and (b.get("data") or {}).get("access_token")
    print(f"way={way!s:<22} HTTP={r.status_code} code={b.get('code')} msg={str(b.get('msg',''))[:60]!r} token={bool(token_ok)}")
    if token_ok:
        tk = b["data"]["access_token"]
        print("  TOKEN FIRST 50 CHARS:", tk[:50])
        print("  TOKEN PARTS COUNT:", len(tk.split('.')))
        break
