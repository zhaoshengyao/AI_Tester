# -*- coding: utf-8 -*-
"""Step H-1：探测 IPD 项目管理写接口（赵老板）。

探测内容：
1. 项目 CREATE：常见路径 14 个 × POST（带最小 payload）
2. 项目 UPDATE：常见路径 14 个 × PUT/POST
3. STATUS 流转提交：submit/approve/reject × {id}/submit 等 27 个候选 URL
4. PHASE 推进：concept→plan / plan→development / development→closed 候选 URL 21 个
5. SOFT-DELETE：{id}/delete / {id}/soft-delete / {id}/recycle 候选 14 个
6. IDOR 越权写：赵经理账号去调 赵老板独有的 PID 的 PUT/status/phase → 返回结构

输出：write_api_probe_result.json（所有探测结果）供 H-2 脚本构造最小 payload。
"""
from __future__ import annotations
import json, os, sys, time, requests, uuid
from pathlib import Path

REPO = Path(r"d:\AICode\TestHub\AITestDemo")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tests" / "api" / "ipd"))
from conftest import _load_system_yaml_auth, _load_dotenv, BOSS_USERNAME, BOSS_PASSWORD, _do_login_request  # type: ignore
import conftest  # type: ignore

def _make_session(username: str, password_plain: str, cfg: dict, enc_func, api_prefix: str):
    login = _do_login_request(username, password_plain, cfg, enc_func, api_prefix)
    token = login["access_token"]
    client_id = cfg["client_id"]
    tenant_id = (cfg["auth"].get("extra_fields") or {}).get("tenantId", "000000")
    s = requests.Session()
    s.headers.update({
        "Authorization": f"Bearer {token}",
        "clientid": client_id,
        "tenant-id": tenant_id,
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
    })
    return s

# 手动加载 config（等价于 ipd_config fixture，避免 pytest 运行环境依赖）
def _build_cfg():
    sys_path = REPO / "projects" / "ipd" / "system.yaml"
    env_path = REPO / "projects" / "ipd" / ".env"
    auth = _load_system_yaml_auth(sys_path)
    env = _load_dotenv(env_path)
    cfg = {"auth": auth}
    cfg["base_url"] = env.get("BASE_URL", "").rstrip("/")
    cfg["api_base_url"] = (env.get("API_BASE_URL") or (cfg["base_url"] + "/prod-api")).rstrip("/")
    cfg["username"]   = env.get("TEST_USERNAME",  "赵经理")
    cfg["password"]   = env.get("TEST_PASSWORD",  "123456")
    cfg["api_username"] = env.get("API_USERNAME", cfg["username"])
    cfg["api_password"] = env.get("API_PASSWORD", cfg["password"])
    cfg["client_id"] = auth["client_id"]
    return cfg

cfg = _build_cfg()
def enc_pwd_func(plaintext: str) -> str:
    return conftest._encrypt_aes_256_ecb_hex(plaintext, cfg["client_id"])
api = cfg["api_base_url"].rstrip("/")
boss_s = _make_session(BOSS_USERNAME, BOSS_PASSWORD, cfg, enc_pwd_func, api)
mgr_s  = _make_session("赵经理", "123456", cfg, enc_pwd_func, api)

def _safe_req(method: str, url: str, **kwargs):
    try:
        kwargs.setdefault("timeout", 10)
        s = kwargs.pop("session", boss_s)
        r = s.request(method, url, **kwargs)
        try: body = r.json()
        except Exception: body = {"_raw_text": r.text[:500]}
        return r.status_code, body
    except Exception as e:
        return 0, {"_error": str(e)[:200]}

# 先拿赵老板 8 个项目，找 赵经理 5 条里不存在的 PID（IDOR 目标）
def _list(sess, url_path):
    st, body = _safe_req("GET", api + url_path, params={"pageNum":1,"pageSize":50}, headers={"Content-Type": None}, cookies={}, session=sess)
    rows=[]; total=0
    if isinstance(body, dict):
        data = body.get("data") if "data" in body else body
        if isinstance(data, dict):
            rows = data.get("rows") or body.get("rows") or []
            total = data.get("total") or body.get("total") or len(rows)
    return total, rows

boss_t, boss_rows = _list(boss_s, "/idmp/project/page")
mgr_t,  mgr_rows  = _list(mgr_s,  "/project/page")

def _pid(r): return str(r.get("id") or r.get("projectId") or "")
boss_ids = {_pid(p) for p in boss_rows if _pid(p)}
mgr_ids  = {_pid(p) for p in mgr_rows  if _pid(p)}
manager_cannot_see = boss_ids - mgr_ids
print(f"[INFO] boss_ids={len(boss_ids)} / mgr_ids={len(mgr_ids)} / 越权目标 PIDs={manager_cannot_see}")

# 先找一个 closed + draft 的项目样本 PID（FLOW-008 探测备用）
def _status(p): return p.get("status"), p.get("phase")
sample_ids = {"any": next(iter(boss_ids))}
for p in boss_rows:
    st, ph = _status(p)
    sample_ids.setdefault(st, _pid(p))
    sample_ids.setdefault(ph, _pid(p))
print(f"[INFO] 样本 PID：{sample_ids}")
any_pid = sample_ids["any"]
draft_pid = sample_ids.get("draft") or any_pid
pending_pid = sample_ids.get("pending") or any_pid
approved_concept_pid = next((_pid(p) for p in boss_rows if p.get("status")=="approved" and p.get("phase")=="concept"), any_pid)
approved_plan_pid = next((_pid(p) for p in boss_rows if p.get("status")=="approved" and p.get("phase")=="plan"), any_pid)
approved_dev_pid = next((_pid(p) for p in boss_rows if p.get("status")=="approved" and p.get("phase")=="development"), any_pid)
closed_pid = next((_pid(p) for p in boss_rows if p.get("phase")=="closed"), any_pid)
print(f"[INFO] 目标专用PID：draft={draft_pid} / pending={pending_pid} / approved_concept={approved_concept_pid} / approved_plan={approved_plan_pid} / approved_dev={approved_dev_pid} / closed={closed_pid}")

res = {
    "probe_time": time.strftime("%Y-%m-%d %H:%M:%S"),
    "setup": {"boss_ids_n": len(boss_ids), "mgr_ids_n": len(mgr_ids),
              "idor_target_pids": sorted(manager_cannot_see),
              "target_pids": {"draft": draft_pid, "pending": pending_pid,
                              "approved_concept": approved_concept_pid, "approved_plan": approved_plan_pid,
                              "approved_dev": approved_dev_pid, "closed": closed_pid}},
    "create_candidates": [],
    "update_candidates": [],
    "status_flow_candidates": [],
    "phase_flow_candidates": [],
    "soft_delete_candidates": [],
    "idor_probe_candidates": [],
}

# ========== 1) CREATE 候选（前缀 /idmp/project/ 优先赵老板全公司接口；无前缀备用）==========
project_prefixes = ["/idmp/project", "/project"]
suffix_create = ["", "/create", "/add", "/save", "/submit", "/new", "/apply", "/start"]
# 最小 payload：必填项猜（projectName/projectCode/projectType/budgetAmount/owner/description/status/phase）
PREFIX = "AUTO-TEST-" + time.strftime("%Y%m%d")
UNIQ = PREFIX + "-" + uuid.uuid4().hex[:4].upper()
payload_create_templates = [
    # 最小集
    {"projectName": UNIQ, "projectCode": UNIQ.lower(), "projectType": "software", "description": "write-regression 专用，执行完后软删除", "status": "draft", "phase": "concept", "priority": "medium"},
    # 带 budget
    {"projectName": UNIQ + "-B", "projectCode": UNIQ.lower()+"b", "projectType": "software", "planStartDate": "2026-08-01", "planEndDate": "2026-12-31", "budgetAmount": 100000, "description": "WR", "status": "draft", "phase": "concept"},
]
N = 0
for pp in project_prefixes:
    for sf in suffix_create:
        url = api + pp + sf
        for tpl_i, payload in enumerate(payload_create_templates):
            N += 1
            st, body = _safe_req("POST", url, json=payload, timeout=12)
            code = body.get("code") if isinstance(body, dict) else "?"
            hint = (body.get("msg") or body.get("data") or "") if isinstance(body, dict) else ""
            note = {
                "payload_idx": tpl_i, "payload_keys": sorted(payload.keys()),
            }
            res["create_candidates"].append({"no":N,"method":"POST","url":pp+sf,"http":st,"business_code":code,
                                              "success": (st==200 and isinstance(code,int) and code==200 and isinstance(body.get("data"), (dict, int, str))),
                                              "msg": str(hint)[:200] if hint else "", "note": note})
            if st < 500 and (code in (200, 400, 403, 404, 405, 409, 422)):
                print(f"  CREATE {st}/code={code}: POST {pp+sf}")
            # 成功的话立即停下（不要连续造 2+ 污染）
            if st == 200 and isinstance(code, int) and code == 200:
                res["create_candidates"][-1]["payload"] = payload
                res["create_candidates"][-1]["response_body_sample"] = ({"data": body.get("data"), "msg": body.get("msg")} if isinstance(body, dict) else None)
                print(f"  ✅ CREATE 命中：POST {pp+sf} HTTP=200 code=200 → 停止后续 candidate 探测避免污染")
                break
    else:
        continue
    break

# ========== 2) UPDATE 候选 ==========
suffix_update = ["/update", "/edit", "/save", ""]
N = 0
for pp in project_prefixes:
    for sf in suffix_update:
        # 两种形式：PUT /{id} + sf；或 POST /{id}/update 无 id 前缀在 URL 中直接 body 带 id
        forms = [
            ("PUT", f"{pp}/{approved_plan_pid}{sf}"),
            ("POST", f"{pp}/{approved_plan_pid}{sf}"),
            ("POST", f"{pp}{sf}"),
        ]
        update_tpl = {"id": approved_plan_pid, "name": "WR-UPDATE-PROBE", "projectName": "WR-UPDATE-PROBE", "phase": "plan", "status": "approved"}
        for method, sub in forms:
            N += 1
            st, body = _safe_req(method, api + sub, json=update_tpl, timeout=12)
            code = body.get("code") if isinstance(body, dict) else "?"
            msg = (body.get("msg") or "") if isinstance(body, dict) else ""
            res["update_candidates"].append({"no":N,"method":method,"url":sub,"http":st,"business_code":code,
                                             "success": (st==200 and isinstance(code,int) and code==200),
                                             "msg": str(msg)[:200]})
            if st in (200, 400, 403, 404, 405, 409, 422):
                print(f"  UPDATE {st}/code={code}: {method} {sub}")

# ========== 3) STATUS 流转：submit/approve/reject/pass ==========
actions = [
    ("submit",   draft_pid,   "draft→pending"),
    ("approve",  pending_pid, "pending→approved"),
    ("pass",     pending_pid, "pending→approved(alt)"),
    ("reject",   pending_pid, "pending→draft"),
    ("audit",    pending_pid, "pending→approved(alt2)"),
]
for action, pid, title in actions:
    # 候选形式 27 = 3 prefix_strategy × 3 http method × 3 body_strategy
    prefix_strategies = [f"/idmp/project/{pid}", f"/project/{pid}", f"/idmp/project"]
    for ps in prefix_strategies:
        for method in ["POST", "PUT", "GET"]:
            url = api + ps + (f"/{action}" if ps.endswith(str(pid)) else f"/{action}")
            body_strategies = [
                {"id": pid},
                {"projectId": pid, "action": action},
                {"id": pid, "status": "pending" if action=="submit" else "approved" if action in ("approve","pass","audit") else "draft", "remark": "WR probe"},
            ] if method != "GET" else [None]
            for bs in body_strategies:
                kwargs = {"params": bs} if method=="GET" else {"json": bs}
                st, body = _safe_req(method, url, **kwargs, timeout=10)
                code = body.get("code") if isinstance(body, dict) else "?"
                msg = (body.get("msg") or "") if isinstance(body, dict) else ""
                hit = st == 200 and isinstance(code, int) and code == 200
                if st != 0 and (st != 404 or code not in (404, None, "?")):
                    res["status_flow_candidates"].append({
                        "action_title": title, "action": action, "pid": pid, "strategy_prefix": ps,
                        "method": method, "url_sub": (url.replace(api,"")), "http": st, "business_code": code, "success": hit, "msg": str(msg)[:200],
                        "body_strategy": "params" if method=="GET" else sorted(bs.keys()) if isinstance(bs, dict) else None,
                    })
                    if hit or st in (200, 400, 403, 405, 409, 422):
                        print(f"  STATUS {title}: {method} {url.replace(api,'')} HTTP={st} code={code}")

# ========== 4) PHASE 推进：next-phase / advance / promote / start-next ==========
phase_pairs = [
    ("concept→plan", approved_concept_pid, [("nextPhase","plan"),("advance","plan"),("promote","plan"),("startPlan",None)]),
    ("plan→development", approved_plan_pid,  [("nextPhase","development"),("advance","development"),("startDev",None)]),
    ("development→closed", approved_dev_pid, [("nextPhase","closed"),("advance","closed"),("close",None),("complete",None)]),
]
for title, pid, ops in phase_pairs:
    for act, target_phase in ops:
        for ps in [f"/idmp/project/{pid}", f"/project/{pid}"]:
            for method in ["POST","PUT","GET"]:
                url = api + ps + f"/{act}"
                bs = {"id": pid, "phase": target_phase, "targetPhase": target_phase, "remark": "WR phase probe"} if target_phase else {"id": pid}
                kwargs = {"params": bs} if method=="GET" else {"json": bs}
                st, body = _safe_req(method, url, **kwargs, timeout=10)
                code = body.get("code") if isinstance(body, dict) else "?"
                msg = (body.get("msg") or "") if isinstance(body, dict) else ""
                hit = st == 200 and isinstance(code, int) and code == 200
                if st != 0 and (st != 404 or code not in (404, None, "?")):
                    res["phase_flow_candidates"].append({
                        "phase_title": title, "action": act, "pid": pid, "strategy_prefix": ps,
                        "method": method, "url_sub": (url.replace(api,"")), "http": st, "business_code": code, "success": hit, "msg": str(msg)[:200],
                    })
                    if hit or st in (200, 400, 403, 405, 409, 422):
                        print(f"  PHASE {title}: {method} {url.replace(api,'')} HTTP={st} code={code}")

# ========== 5) SOFT-DELETE / closed 禁止修改 探针 ==========
del_ops = ["delete", "remove", "softDelete", "soft-delete", "recycle", "discard", "archive", "close"]
for op in del_ops:
    # 直接用之前 create 成功的（若有新造）否则用 AUTO-TEST-XXX 若不存在则先跳过；此步用一个 dummy-id 测路径
    test_pid = draft_pid  # 用 draft 项目测删除路径（不要删用户真实数据 → 先探测路径然后只做 HTTP 200/code=400/403 等；如果返回成功 code=200 则实际不删）
    for ps in [f"/idmp/project/{test_pid}", f"/project/{test_pid}", "/idmp/project", "/project"]:
        for method in ["DELETE", "POST"]:
            url = api + ps + (f"/{op}" if ps.endswith(str(test_pid)) else f"/{op}")
            body = {"id": test_pid, "reason": "WR probe soft-delete 候选路径探测，如果真实成功 DELETE=不希望发生，仅探测"}
            kwargs = {"params": body} if method=="DELETE" else {"json": body}
            st, bd = _safe_req(method, url, **kwargs, timeout=10)
            code = bd.get("code") if isinstance(bd, dict) else "?"
            msg = (bd.get("msg") or "") if isinstance(bd, dict) else ""
            if st != 0 and (st != 404 or code not in (404, None, "?")):
                res["soft_delete_candidates"].append({
                    "op": op, "test_pid_used": test_pid, "method": method, "url_sub": url.replace(api,""),
                    "http": st, "business_code": code, "msg": str(msg)[:200],
                    "WARNING": "仅用于探测；如果 code=200 表示真实删除=不要直接用，需加 isDeleted=软删除参数改造" if code==200 else "",
                })
                if st in (200, 400, 403, 405, 409, 422):
                    print(f"  SOFT-DELETE {op}: {method} {url.replace(api,'')} HTTP={st} code={code} {'⚠️REAL-DELETE' if code==200 else ''}")

# ========== 6) IDOR 越权写探测：赵经理修改赵老板独有的 PID（phase/status/name）==========
idor_target = next(iter(manager_cannot_see)) if manager_cannot_see else list(boss_ids)[0]
idor_probes = [
    ("PUT status=pending", f"/project/{idor_target}", {"id":idor_target,"status":"pending","projectName":"WR-IDOR-PROBE"}),
    ("POST status",       f"/project/{idor_target}/submit", {"id":idor_target,"remark":"WR IDOR probe"}),
    ("PUT phase=development", f"/project/{idor_target}", {"id":idor_target,"phase":"development"}),
]
for title, sub, payload in idor_probes:
    for method in ("POST", "PUT"):
        st, body = _safe_req(method, api + sub, json=payload, timeout=12)
        code = body.get("code") if isinstance(body, dict) else "?"
        msg = (body.get("msg") or "") if isinstance(body, dict) else ""
        # IDOR 规则：403 / code=403 = 通过（权限收紧✅）；code=200 = IDOR 高危缺陷（赵经理越权修改了他无权看的项目）
        res["idor_probe_candidates"].append({
            "title": title, "method": method, "url_sub": sub, "target_pid": idor_target,
            "http": st, "business_code": code,
            "idor_pass_expected_403": (st == 403 or code == 403),
            "idor_risky_200": (st == 200 and isinstance(code, int) and code == 200),
            "msg": str(msg)[:200],
        })
        print(f"  IDOR {title}: {method} {sub} HTTP={st} code={code} → {'EXPECTED_403 ✅' if (st==403 or code==403) else 'RISKY_200 ⚠️⚠️' if (st==200 and code==200) else 'UNCLEAR'}")

# =========================================
# 写结果
OUT = REPO / "projects/ipd/docs/analysis/IPD项目管理写接口探测结果.json"
OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n✅ 探测报告 → {OUT}")
print(f"   - CREATE：{sum(1 for c in res['create_candidates'] if c.get('success'))} 个成功候选")
print(f"   - UPDATE：{sum(1 for c in res['update_candidates'] if c.get('success'))} 个成功候选")
print(f"   - STATUS 流转：{sum(1 for c in res['status_flow_candidates'] if c.get('success'))} 个成功候选")
print(f"   - PHASE 推进： {sum(1 for c in res['phase_flow_candidates'] if c.get('success'))} 个成功候选")
print(f"   - SOFT-DEL：  {sum(1 for c in res['soft_delete_candidates'] if c.get('business_code')==200)} 个返回 200（若=真删则不使用，需换软删参数）")
print(f"   - IDOR 越权 403：{sum(1 for c in res['idor_probe_candidates'] if c.get('idor_pass_expected_403'))} / {len(res['idor_probe_candidates'])}")
print(f"   - IDOR 越权 200（高危！）：{sum(1 for c in res['idor_probe_candidates'] if c.get('idor_risky_200'))}")
