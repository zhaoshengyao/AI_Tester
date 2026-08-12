# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"d:\AICode\TestHub\AITestDemo\tests\api\ipd")
from conftest import _load_system_yaml_auth, _load_dotenv, DOTENV, SYSTEM_YAML

print("SYSTEM_YAML exists?", SYSTEM_YAML.exists(), SYSTEM_YAML)
auth = _load_system_yaml_auth(SYSTEM_YAML)
print("auth keys:", sorted(auth.keys()))
for k, v in auth.items():
    if k == "extra_fields":
        continue
    ln = len(v) if isinstance(v, str) else "n/a"
    print(f"  auth.{k} = {v!r} (len={ln})")
print("extra_fields:", auth["extra_fields"])
print()
env = _load_dotenv(DOTENV)
print("env keys sorted:", sorted(env.keys()))
cid = env.get("API_CLIENT_ID")
print("env.API_CLIENT_ID =", cid, "len=", len(cid) if cid else "None")
cid_auth = auth.get("client_id")
print("auth.client_id =", cid_auth, "len=", len(cid_auth) if cid_auth else "None")
final_cid = cid or cid_auth
print("FINAL client_id used:", final_cid, "len=", len(final_cid) if final_cid else "None")
try:
    kb = bytes.fromhex(final_cid)
    print("key bytes len:", len(kb))
except Exception as e:
    print("key fromhex err:", e)
