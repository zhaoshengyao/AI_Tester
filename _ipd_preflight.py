# -*- coding: utf-8 -*-
import os, sys, json, time
# ROOT = 本脚本所在目录（跨平台自动适配）
_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(_ROOT, 'tests', 'api', 'ipd'))
try:
    from conftest import _load_dotenv, _load_system_yaml_auth, _do_login_request, _encrypt_aes_256_ecb_hex
    from pathlib import Path
    def _load_config_env():
        env = _load_dotenv(Path(os.path.join(_ROOT, 'projects', 'ipd', '.env')))
        auth_cfg = _load_system_yaml_auth(Path(os.path.join(_ROOT, 'projects', 'ipd', 'system.yaml')))
        return {
            'api_base_url': env.get('API_BASE_URL') or env.get('BASE_URL'),
            'base_url': env.get('BASE_URL'),
            'client_id': auth_cfg.get('client_id') or env.get('API_CLIENT_ID'),
            'auth': auth_cfg,
            'env': env,
        }
except Exception as e:
    print(f'[FAIL] 导入conftest失败: {e}')
    import traceback; traceback.print_exc()
    raise
cfg = _load_config_env()
base = (cfg.get('api_base_url') or '').rstrip('/')
def enc(p): return _encrypt_aes_256_ecb_hex(p, cfg['client_id'])
t0 = time.time()
r = _do_login_request(os.environ.get('API_USERNAME','赵经理'), os.environ.get('API_PASSWORD','123456'), cfg, enc, base)
dt_ms = int((time.time()-t0)*1000)
_user = r.get("user") or {}
print(f'[OK] 登录 HTTP 200 code=200 token_len={len(r["access_token"])} 耗时={dt_ms}ms user={_user.get("userName") or _user.get("nickName") or "N/A"}')
# 核心只读：GET /idmp/project/page
import requests
s = requests.Session()
s.headers.update({'Authorization': f'Bearer {r["access_token"]}', 'client-id': cfg['client_id'], 'tenant-id': '000000'})
t1 = time.time()
resp = s.get(base + '/idmp/project/page', params={'pageNum': 1, 'pageSize': 5}, timeout=15)
dt2 = int((time.time()-t1)*1000)
try: body = resp.json()
except Exception: body = {'_raw': resp.text[:500]}
total = None; rows = None
if isinstance(body, dict):
    total = body.get('total')
    data = body.get('data')
    if total is None and isinstance(data, dict):
        total = data.get('total')
    rows = body.get('rows')
    if rows is None and isinstance(data, dict):
        rows = data.get('rows')
print(f'[OK] 项目列表 HTTP={resp.status_code} 业务码={body.get("code") if isinstance(body,dict) else "N/A"} total={total} rows_len={len(rows) if isinstance(rows,list) else "N/A"} 耗时={dt2}ms')
# 赵老板角色预检
t2 = time.time()
r2 = _do_login_request('赵老板', '123456', cfg, enc, base)
dt3 = int((time.time()-t2)*1000)
print(f'[OK] 赵老板登录 HTTP 200 code=200 token_len={len(r2["access_token"])} 耗时={dt3}ms')
print('[PREFLIGHT] ALL PASSED')
