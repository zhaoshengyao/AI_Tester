"""IPD 实测接口基线探测脚本：
1. 用破解的 AES-256-ECB 登录，拿 token
2. 用 token 尝试所有从菜单/Network 看到的候选接口
3. 输出一份 {method, path, status, 样本响应} 的基线清单
"""
import requests, json, base64, os, sys
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

BASE = 'http://192.168.2.97:6090'
API = BASE + '/prod-api'
CLIENT_ID = 'e5cd7e4891bf95d1d19206ce24a7b32e'

def enc_pwd(pwd):
    c = AES.new(CLIENT_ID.encode('utf-8'), AES.MODE_ECB)
    return base64.b64encode(c.encrypt(pad(pwd.encode('utf-8'), 16))).decode()

# 1. 登录
r = requests.post(API + '/auth/login', json={
    'username': '赵经理', 'password': enc_pwd('123456'),
    'clientId': CLIENT_ID, 'grantType': 'password', 'tenantId': '000000',
}, timeout=10)
r.raise_for_status()
b = r.json()
assert b.get('code') == 200, f'登录失败: {b}'
token = b['data']['access_token']
H = {'Authorization': f'Bearer {token}', 'clientid': CLIENT_ID, 'Content-Type': 'application/json'}
print(f'✅ 登录成功，token_len={len(token)}')
print(f'   login response keys: {list(b["data"].keys())}\n')

# 2. 候选接口清单（从前面页面探测和菜单名推断）
candidates = [
    # 认证
    ('GET',  '/auth/logout', None),
    ('GET',  '/auth/code', None),
    # 系统/用户 (若依风格，IPD 也用了同一套骨架)
    ('GET',  '/system/user/profile', None),
    ('GET',  '/system/menu/getRouters', None),
    ('GET',  '/system/menu/build', None),
    ('GET',  '/system/dict/data/type/common_status', None),
    ('GET',  '/system/dict/data/type/sys_yes_no', None),
    ('GET',  '/system/dept/list', None),
    ('GET',  '/system/role/list', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/system/user/list', {'pageNum': 1, 'pageSize': 10}),
    # 仪表盘
    ('GET',  '/idmp/dashboard/overview', None),
    ('GET',  '/idmp/dashboard/summary', None),
    ('GET',  '/idmp/dashboard/stat', None),
    ('GET',  '/idmp/dashboard/projectTrend', None),
    # IPD 项目管理
    ('GET',  '/idmp/project/list', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/idmp/project/page', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/idmp/project/2086985374914007042', None),
    ('POST', '/idmp/project/list', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/idmp/project/options', None),
    ('GET',  '/idmp/project/stat', None),
    ('GET',  '/idmp/project/tree', None),
    # 交付物/里程碑/任务
    ('GET',  '/idmp/deliverable/list', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/idmp/milestone/list', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/idmp/task/list', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/idmp/task/my', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/idmp/member/list', {'pageNum': 1, 'pageSize': 10}),
    # 风险
    ('GET',  '/idmp/risk/list', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/idmp/riskRule/list', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/idmp/riskRule/1', None),
    ('GET',  '/idmp/riskRecord/list', {'pageNum': 1, 'pageSize': 10}),
    # 审批
    ('GET',  '/idmp/approval/list', {'pageNum': 1, 'pageSize': 10, 'id': 1}),
    ('GET',  '/idmp/approval/myPending', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/idmp/approval/myDone', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/idmp/approval/myStarted', {'pageNum': 1, 'pageSize': 10}),
    ('POST', '/idmp/approval/_search', {}),
    # 会议/评审
    ('GET',  '/idmp/meeting/list', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/idmp/review/list', {'pageNum': 1, 'pageSize': 10}),
    # 文档/知识
    ('GET',  '/idmp/document/list', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/idmp/knowledge/list', {'pageNum': 1, 'pageSize': 10}),
    # 成本/预算
    ('GET',  '/idmp/cost/list', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/idmp/budget/list', {'pageNum': 1, 'pageSize': 10}),
    # 变更
    ('GET',  '/idmp/change/list', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/idmp/changeRequest/list', {'pageNum': 1, 'pageSize': 10}),
    # 流程工作流 (workflow)
    ('GET',  '/workflow/category/list', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/workflow/category/treeSelect', None),
    ('GET',  '/workflow/template/list', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/workflow/definition/list', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/workflow/instance/list', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/workflow/task/list', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/workflow/task/todo', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/workflow/task/done', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/workflow/form/list', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/workflow/formManage/list', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/workflow/processDefinition/list', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/workflow/monitor/processInstance/list', {'pageNum': 1, 'pageSize': 10}),
    ('GET',  '/workflow/monitor/allTaskWaiting/list', {'pageNum': 1, 'pageSize': 10}),
    # dashboard 备选
    ('GET',  '/dashboard/overview', None),
    ('GET',  '/idmp/home/summary', None),
    ('GET',  '/idmp/stat/summary', None),
    ('GET',  '/idmp/index/info', None),
]

results = []
cnt_ok = 0
cnt_partial = 0
cnt_404 = 0
for method, path, params in candidates:
    try:
        url = API + path.split('?')[0]
        kwargs = {'headers': H, 'timeout': 8}
        if method == 'GET':
            if params: kwargs['params'] = params
            r = requests.get(url, **kwargs)
        else:
            kwargs['json'] = params or {}
            r = requests.post(url, **kwargs)
        try: b = r.json(); flat = json.dumps(b, ensure_ascii=False)
        except: b = None; flat = r.text[:300]
        code = ''; msg = ''; total = ''; dk = ''
        if isinstance(b, dict):
            code = str(b.get('code', ''))
            msg = (b.get('msg') or '')[:60]
            data = b.get('data')
            if isinstance(data, dict):
                total = str(data.get('total', ''))
                dk = 'dict keys=' + ','.join(list(data.keys())[:8])
            elif isinstance(data, list):
                total = str(len(data)) if isinstance(data, list) else ''
                dk = 'list len=' + str(len(data))
        flag = '✅' if r.status_code == 200 and (code == '200' or code == '') else '  '
        if (code == '200' or (r.status_code == 200 and not code)) and (r.status_code == 200):
            cnt_ok += 1; flag = '✅'
        elif r.status_code == 200 and code not in ('404','403','500','405'):
            cnt_partial += 1; flag = '🟡'
        else:
            cnt_404 += 1
        print(f'{flag} {method:4s} {path:55s} HTTP{r.status_code} code={code:<5s} total={str(total):<6s} msg={msg}')
        if code == '200' and dk:
            print(f'          {dk}')
        results.append({
            'method': method, 'path': path, 'http_status': r.status_code,
            'biz_code': code, 'msg': msg, 'total': total,
            'sample': flat[:220] if (code == '200' or r.status_code != 200) else '',
        })
    except Exception as e:
        print(f'❌ {method} {path}: {type(e).__name__}: {e}')
        results.append({'method': method, 'path': path, 'error': str(e)})

print(f'\n汇总: ✅{cnt_ok}  🟡{cnt_partial}  ❌{cnt_404}  Total={len(results)}')

# 保存结果
os.makedirs('projects/ipd/docs/analysis', exist_ok=True)
with open('projects/ipd/docs/analysis/实测API基线.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f'\n已保存到 projects/ipd/docs/analysis/实测API基线.json')

# 输出 CSV 摘要 (成功/部分成功)
print('\n===== ✅/🟡 接口(供需求分析报告引用) =====')
print(f'{"方法":<5}{"路径":<60}{"HTTP":<6}{"BizCode":<7}{"总条数/样本":<10} 说明')
for r in results:
    if ('http_status' in r and r['http_status']==200 and r.get('biz_code') not in ('404','403','500','405')):
        msg = (r.get('msg') or '')[:20]
        tot = r.get('total') or '-'
        print(f'{r["method"]:<5}{r["path"]:<60}{r["http_status"]:<6}{r.get("biz_code",""):<7}{tot:<10} {msg}')
