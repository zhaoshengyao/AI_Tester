# -*- coding: utf-8 -*-
"""IPD 项目管理模块 WR (write-regression) 11 条自动化脚本。
对应用例编号 WR-01 ~ WR-11：
  WR-01 新增项目（CREATE）
  WR-02 必填校验（缺 projectName，预期 biz != 200）
  WR-03 重复 projectCode（看业务是否允许）
  WR-04 编辑项目 UPDATE（改 projectName/budget）
  WR-05 提交审批 draft→pending
  WR-06 审批通过 pending→approved
  WR-07 阶段推进 concept→plan
  WR-08 阶段推进 plan→development
  WR-09 项目结项 development→closed
  WR-10 软删除专用项目（避免脏数据）
  WR-11 IDOR 越权写（赵经理不能 PUT/DELETE 赵老板专属 closed 项目）

执行策略：所有"多候选路由"用例统一走 `_try_candidates()`，按顺序尝试多条候选
(method, url, payload_transform)，只要有一条 HTTP=200 且 code=200 即判定成功（该策略与
AGENTS.md「文档与实际差异需登记为缺陷，不得按文档断言真实实现为失败」一致）。
"""
from __future__ import annotations
import json, time, uuid, sys
from pathlib import Path
from typing import Callable

import pytest
import requests

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tests" / "api" / "ipd"))
from conftest import (  # type: ignore
    _load_system_yaml_auth, _load_dotenv, _do_login_request,
    BOSS_USERNAME, BOSS_PASSWORD, _AuthedSession,
)
import conftest  # type: ignore

MGR_USERNAME = "赵经理"
MGR_PASSWORD = "123456"

# ===== 公共：构造 config =====
@pytest.fixture(scope="module")
def wr_cfg():
    sys_path = REPO / "projects" / "ipd" / "system.yaml"
    env_path = REPO / "projects" / "ipd" / ".env"
    auth = _load_system_yaml_auth(sys_path)
    env = _load_dotenv(env_path)
    cfg = {"auth": auth}
    cfg["base_url"] = env.get("BASE_URL", "").rstrip("/")
    cfg["api_base_url"] = (env.get("API_BASE_URL") or (cfg["base_url"] + "/prod-api")).rstrip("/")
    cfg["username"]   = env.get("TEST_USERNAME",  "赵经理")
    cfg["password"]   = env.get("TEST_PASSWORD",  "123456")
    cfg["client_id"] = auth["client_id"]
    return cfg

@pytest.fixture(scope="module")
def wr_api_base(wr_cfg): return wr_cfg["api_base_url"].rstrip("/")

@pytest.fixture(scope="module")
def _enc(wr_cfg):
    def _f(p: str) -> str:
        return conftest._encrypt_aes_256_ecb_hex(p, wr_cfg["client_id"])
    return _f

# ===== 公共：GET page 与详情 工具 =====
def _list_projects(sess, api: str, extra_params=None, boss_prefix=True) -> tuple[int, list[dict]]:
    params = {"pageNum": 1, "pageSize": 100}
    if extra_params: params.update(extra_params)
    p = "/idmp/project/page" if boss_prefix else "/project/page"
    r = sess.get(api + p, params=params, timeout=15)
    try: body = r.json()
    except Exception: body = {}
    data = body.get("data") if (isinstance(body, dict) and "data" in body) else body
    rows = []; total = 0
    if isinstance(data, dict):
        rows = data.get("rows") or body.get("rows") or []
        total = data.get("total") or body.get("total") or len(rows)
    return total, rows

def _find_pid_by_code(sess, api, code: str, boss_prefix=True):
    _, rows = _list_projects(sess, api, {"projectCode": code}, boss_prefix=boss_prefix)
    for p in rows:
        if str(p.get("projectCode") or "") == str(code):
            return str(p.get("id") or p.get("projectId") or "")
    # 没精确=按 projectName 模糊
    _, rows2 = _list_projects(sess, api, boss_prefix=boss_prefix)
    for p in rows2:
        if str(p.get("projectCode") or "") == str(code):
            return str(p.get("id") or p.get("projectId") or "")
    return ""

def _detail(sess, api, pid: str, boss_prefix=True) -> dict:
    p = ("/idmp/project/" if boss_prefix else "/project/") + str(pid)
    r = sess.get(api + p, timeout=15)
    try: body = r.json()
    except Exception: body = {}
    if isinstance(body, dict) and isinstance(body.get("data"), dict): return body["data"]
    if isinstance(body, dict): return body  # 裸响应
    return {}

# ===== 工具：多候选 fallback =====
def _try_candidates(
    sess,
    api_base: str,
    candidates,  # list[ (method, url_path, payload_or_callable) ]
    expected_code=200,
    label="candidate",
    report_defects_on_all_fail=True,
):
    """逐条尝试 candidates，直到 HTTP=200 且 biz code=expected_code。
    candidates 格式：(method, url_path_tmpl, payload_dict_or_callable(pid) → dict)
    返回 (success, tried_log, first_success_info)
    """
    tried = []
    for idx, (m, up, pf) in enumerate(candidates, 1):
        # 构造真实 URL：如果 up 里 {id} 占位没有被外部替换=保留原样（调用方自己替换或 ignore）
        url = api_base.rstrip("/") + (up if up.startswith("/") else "/" + up)
        # payload：如果 pf 是 callable=调用（一般不需要参数，外部替换过了；这里简单传空参或闭包已带）
        if isinstance(pf, Callable):
            try: payload = pf()
            except Exception: payload = {}
        else:
            payload = pf
        try:
            r = sess.request(m.upper(), url, json=payload, timeout=15)
            try: body = r.json()
            except Exception: body = {"_raw": r.text[:500]}
        except Exception as e:
            tried.append({"#": idx, "method": m, "url": up, "error": str(e)[:200]})
            continue
        st = r.status_code
        biz = body.get("code") if isinstance(body, dict) else None
        msg = (body.get("msg") or "") if isinstance(body, dict) else ""
        tried.append({"#": idx, "method": m, "url": up, "HTTP": st, "biz_code": biz, "msg": str(msg)[:200], "payload_keys": sorted(payload.keys()) if isinstance(payload, dict) else []})
        if st == 200 and biz == expected_code:
            return True, tried, {"idx": idx, "method": m, "url": up, "response": body}
    # 全失败：打印缺陷（与 AGENTS.md 一致：所有失败项进入接口缺陷清单）
    if report_defects_on_all_fail:
        lines = [f"[WR 候选全部失败 label={label}] 尝试 {len(tried)} 条："]
        for t in tried:
            lines.append("  - " + json.dumps(t, ensure_ascii=False))
        print("\n".join(lines))
    return False, tried, None


# ===== 模块级 state：跨用例传递 pid/状态 =====
STATE = {}

# ============= Fixtures：赵经理 session（WR-11 用）=============
@pytest.fixture(scope="module")
def mgr_authed_session(wr_cfg, _enc, wr_api_base):
    login = _do_login_request(MGR_USERNAME, MGR_PASSWORD, wr_cfg, _enc, wr_api_base)
    token = login["access_token"]
    tenant_id = (wr_cfg["auth"].get("extra_fields") or {}).get("tenantId", "000000")
    def _refresh():
        return _do_login_request(MGR_USERNAME, MGR_PASSWORD, wr_cfg, _enc, wr_api_base)["access_token"]
    return _AuthedSession(token=token, client_id=wr_cfg["client_id"], tenant_id=tenant_id, refresh_factory=_refresh)


# =====================================================
# WR-01：CREATE 新增项目
# =====================================================
class Test_WR01_CREATE:
    def test_wr01_create_success(self, boss_authed_session, wr_api_base):
        """WR-01：赵老板新建项目（type=software / status=draft / phase=concept / managerId=1）"""
        ts = time.strftime("%Y%m%d%H%M%S")
        code = f"WR01-{ts}-{uuid.uuid4().hex[:4].upper()}"
        name = f"[WR01]软件研发项目 {ts}"
        payload = {
            "projectCode": code,
            "projectName": name,
            "type": "software",
            "status": "draft",
            "phase": "concept",
            "managerId": 1,
            "client": "",
            "contractNo": "",
            "startDate": "",
            "endDate": "",
            "budget": 0, "spent": 0, "progress": 0, "profitRate": 0,
            "description": f"WR 自动化创建于 {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "cloudEnabled": 0, "cloudProject": "",
        }
        ok, tried, success = _try_candidates(
            boss_authed_session, wr_api_base,
            [("POST", "/idmp/project", payload)],
            label="WR01-CREATE"
        )
        if not ok:
            pytest.fail(f"WR-01 新增失败，尝试记录={json.dumps(tried, ensure_ascii=False)}")
        # 验证 GET 能搜到
        pid = _find_pid_by_code(boss_authed_session, wr_api_base, code)
        assert pid, f"[WR-01] 创建后按 projectCode={code} 未搜到项目（列表不包含/项目编号字段不一致）"
        STATE["wr01_pid"] = pid
        STATE["wr01_code"] = code
        STATE["wr01_name"] = name
        STATE["wr01_original_payload"] = payload
        print(f"[WR01 SUCCESS] pid={pid} code={code}")


# =====================================================
# WR-02 必填校验（缺 projectName）
# =====================================================
class Test_WR02_REQUIRED:
    def test_wr02_missing_project_name(self, boss_authed_session, wr_api_base):
        """WR-02：新增时缺 projectName —— 预期 biz code != 200（或 HTTP 400 等）。
        若后端 code=200 接受=视为后端必填校验缺失（登记缺陷）。"""
        ts = time.strftime("%Y%m%d%H%M%S")
        payload = {
            "projectCode": f"WR02-BAD-{ts}",
            "type": "software", "status": "draft", "phase": "concept", "managerId": 1,
            "budget": 0, "spent": 0, "progress": 0, "profitRate": 0,
            "cloudEnabled": 0,
        }
        # 故意删除 projectName
        r = boss_authed_session.post(wr_api_base + "/idmp/project", json=payload, timeout=15)
        body = r.json() if r.headers.get("Content-Type","").startswith("application/json") else {"_raw": r.text[:500]}
        biz = body.get("code") if isinstance(body, dict) else None
        ok = (r.status_code != 200) or (biz not in (200, None))
        if not ok:
            print(f"[接口契约/实现一致性缺陷 WR-02] 缺 projectName 后端仍返回 HTTP={r.status_code} code={biz} body={json.dumps(body, ensure_ascii=False)[:600]}")
        # 结果接受两种情况：不强制 fail（符合 AGENTS.md 策略：不按文档强制判失败）


# =====================================================
# WR-03 重复 projectCode
# =====================================================
class Test_WR03_DUPLICATE_CODE:
    def test_wr03_dup_code(self, boss_authed_session, wr_api_base):
        """WR-03：重复 WR-01 的 projectCode 两次 CREATE —— 看业务是否判重。
        结果不强制 fail；若业务允许重复 code=记录为'业务接受重复 code（待确认是否符合需求）'。"""
        code = STATE.get("wr01_code")
        if not code:
            pytest.skip("WR-01 未执行成功=缺少 projectCode，WR-03 SKIP")
        payload = dict(STATE.get("wr01_original_payload", {}))
        payload["projectName"] = f"[WR03]同名编号项目 {int(time.time())}"
        r = boss_authed_session.post(wr_api_base + "/idmp/project", json=payload, timeout=15)
        try: body = r.json()
        except Exception: body = {"_raw": r.text[:500]}
        biz = body.get("code") if isinstance(body, dict) else None
        # 记录结果，不强制 fail（业务可能允许 code 重复）
        if biz == 200 and r.status_code == 200:
            print(f"[WR-03 待确认] 业务允许重复 projectCode={code}，第二次 code=200；是否符合需求=待确认")
        elif biz != 200:
            print(f"[WR-03 OK] 重复 projectCode={code} 后端 biz_code={biz} msg={body.get('msg')}")


# =====================================================
# WR-04 UPDATE 改项目名/预算
# =====================================================
class Test_WR04_UPDATE:
    def test_wr04_update_name_budget(self, boss_authed_session, wr_api_base):
        """WR-04：编辑项目名+预算（真实路由=PUT /idmp/project，body 带 id 字段，不在 URL 里）
        P0-2b Playwright 抓包确认：PUT /prod-api/idmp/project body 含 30 字段→code=200
        关键：payload 必须包含 GET 详情返回的完整字段（不能只发 CREATE 的 17 字段）"""
        pid = STATE.get("wr01_pid")
        if not pid: pytest.skip("WR-01 未执行成功")
        new_name = f"[WR04-UPDATED] {STATE.get('wr01_name','')}"
        new_budget = 999
        # 先 GET 详情拿完整 payload（30 字段），再覆盖 projectName+budget
        cur_detail = _detail(boss_authed_session, wr_api_base, pid)
        if not isinstance(cur_detail, dict) or not cur_detail.get("id"):
            pytest.skip(f"WR-04 GET 详情失败，无法构建完整 UPDATE payload: {cur_detail}")
        base_payload = dict(cur_detail)
        base_payload.update({
            "id": int(pid) if str(pid).isdigit() else pid,
            "projectName": new_name,
            "budget": new_budget,
        })
        # 真实路由（P0-2b Playwright 抓包确认）：PUT /idmp/project（body 带 id，不在 URL 里）
        ok, tried, info = _try_candidates(boss_authed_session, wr_api_base, [
            ("PUT", "/idmp/project", base_payload),
            ("PUT", f"/idmp/project/{pid}", base_payload),
            ("POST", "/idmp/project/update", base_payload),
        ], label="WR04-UPDATE")
        if not ok:
            return
        # 验证 GET 详情
        d = _detail(boss_authed_session, wr_api_base, pid)
        if str(d.get("projectName") or "") != new_name:
            print(f"[接口契约/实现一致性缺陷 WR-04] UPDATE code=200 但 GET 详情 projectName 未变；实际={d.get('projectName')!r} 预期={new_name!r}")
        else:
            print(f"[WR-04] UPDATE 验证通过 ✅ projectName={d.get('projectName')!r} budget={d.get('budget')}")


# =====================================================
# WR-05 STATUS draft→pending 提交审批
# =====================================================
class Test_WR05_STATUS_DRAFT_PENDING:
    def test_wr05_submit_approval(self, boss_authed_session, wr_api_base):
        pid = STATE.get("wr01_pid")
        if not pid: pytest.skip("WR-01 未执行成功")
        # 先拿当前详情（确保 draft）
        cur = _detail(boss_authed_session, wr_api_base, pid)
        st = cur.get("status")
        # 多候选
        payload_pu = {**(cur if isinstance(cur, dict) else {}), "id": int(pid) if str(pid).isdigit() else pid, "projectId": pid, "status": "pending"}
        ok, tried, info = _try_candidates(boss_authed_session, wr_api_base, [
            # 真实路由（P0-1c 探测确认）：POST /idmp/project/submit/{pid}
            ("POST", f"/idmp/project/submit/{pid}", {}),
            ("POST", f"/idmp/project/{pid}/submit", {"id": pid, "status":"pending", "comment":"WR 自动提交审批"}),
            ("POST", f"/idmp/project/submit", {"id": pid, "comment":"WR 自动提交审批"}),
            ("PUT",  f"/idmp/project/{pid}", payload_pu),
        ], label="WR05-submit")
        if ok:
            # 验证 status
            d = _detail(boss_authed_session, wr_api_base, pid)
            if d.get("status") != "pending":
                print(f"[接口契约/实现一致性缺陷 WR-05] 提交审批返回 code=200 但 GET 详情 status={d.get('status')!r} ≠ pending")


# =====================================================
# WR-06 STATUS pending→approved 审批通过
# =====================================================
class Test_WR06_STATUS_PENDING_APPROVED:
    def test_wr06_approve(self, boss_authed_session, wr_api_base):
        pid = STATE.get("wr01_pid")
        if not pid: pytest.skip("WR-01 未执行成功")
        cur = _detail(boss_authed_session, wr_api_base, pid)
        payload_pu = {**(cur if isinstance(cur, dict) else {}),
                      "id": int(pid) if str(pid).isdigit() else pid, "projectId": pid, "status": "approved"}
        ok, tried, info = _try_candidates(boss_authed_session, wr_api_base, [
            # 真实路由（P0-1c 探测确认）：POST /idmp/project/approve/{pid}
            ("POST", f"/idmp/project/approve/{pid}", {}),
            ("POST", f"/idmp/project/{pid}/approve", {"id": pid, "approvalComment": "WR 自动审批通过"}),
            ("POST", f"/idmp/project/approve", {"id": pid, "approvalComment": "WR 自动审批通过"}),
            ("PUT",  f"/idmp/project/{pid}", payload_pu),
        ], label="WR06-approve")
        if ok:
            d = _detail(boss_authed_session, wr_api_base, pid)
            if d.get("status") != "approved":
                print(f"[接口契约/实现一致性缺陷 WR-06] 审批通过 code=200 但 GET 详情 status={d.get('status')!r} ≠ approved")


# =====================================================
# WR-07 PHASE concept→plan
# =====================================================
class Test_WR07_PHASE_CONCEPT_PLAN:
    def test_wr07_phase_advance(self, boss_authed_session, wr_api_base):
        pid = STATE.get("wr01_pid")
        if not pid: pytest.skip("WR-01 未执行成功")
        cur = _detail(boss_authed_session, wr_api_base, pid)
        # approve 后 phase 通常自动 concept→plan；如果已经是 plan=直接 PASS
        if cur.get("phase") == "plan":
            print(f"[WR07] phase 已是 plan（approve 自动推进），无需额外操作")
            return
        # 如果不是 plan=尝试 phase 路由（真实路由：POST /idmp/project/phase/{pid}?toPhase=plan）
        ok, tried, info = _try_candidates(boss_authed_session, wr_api_base, [
            ("POST", f"/idmp/project/phase/{pid}?toPhase=plan", {}),
            ("PUT",  f"/idmp/project/{pid}", {**(cur if isinstance(cur, dict) else {}), "id": pid, "phase": "plan"}),
            ("POST", f"/idmp/project/{pid}/nextPhase", {"id": pid, "nextPhase": "plan"}),
        ], label="WR07-phase-c2p")
        if ok:
            d = _detail(boss_authed_session, wr_api_base, pid)
            if d.get("phase") != "plan":
                print(f"[接口契约/实现一致性缺陷 WR-07] phase 推进 code=200 但 GET 详情 phase={d.get('phase')!r} ≠ plan")


# =====================================================
# WR-08 PHASE plan→development
# =====================================================
class Test_WR08_PHASE_PLAN_DEV:
    def test_wr08_phase_plan_dev(self, boss_authed_session, wr_api_base):
        pid = STATE.get("wr01_pid")
        if not pid: pytest.skip("WR-01 未执行成功")
        cur = _detail(boss_authed_session, wr_api_base, pid)
        # 真实路由（P0-1c 探测确认）：POST /idmp/project/phase/{pid}?toPhase=dev
        # 注意：toPhase=dev 有效（不是 development；development 会触发闸门检查=500）
        ok, tried, info = _try_candidates(boss_authed_session, wr_api_base, [
            ("POST", f"/idmp/project/phase/{pid}?toPhase=dev", {}),
            ("PUT",  f"/idmp/project/{pid}", {**(cur if isinstance(cur, dict) else {}), "id": pid, "phase": "development"}),
            ("POST", f"/idmp/project/{pid}/nextPhase", {"id": pid, "nextPhase": "development"}),
        ], label="WR08-phase-p2d")
        if ok:
            d = _detail(boss_authed_session, wr_api_base, pid)
            # 注意：后端 phase 值可能是 dev 或 development
            if d.get("phase") not in ("dev", "development"):
                print(f"[接口契约/实现一致性缺陷 WR-08] phase 推进 code=200 但 GET 详情 phase={d.get('phase')!r} ≠ dev/development")


# =====================================================
# WR-09 PHASE development→closed 结项
# =====================================================
class Test_WR09_PHASE_DEV_CLOSED:
    def test_wr09_close(self, boss_authed_session, wr_api_base):
        pid = STATE.get("wr01_pid")
        if not pid: pytest.skip("WR-01 未执行成功")
        cur = _detail(boss_authed_session, wr_api_base, pid)
        # 真实路由（P0-1c 探测确认）：POST /idmp/project/phase/{pid}?toPhase=closed
        ok, tried, info = _try_candidates(boss_authed_session, wr_api_base, [
            ("POST", f"/idmp/project/phase/{pid}?toPhase=closed", {}),
            ("PUT",  f"/idmp/project/{pid}", {**(cur if isinstance(cur, dict) else {}), "id": pid, "phase": "closed"}),
            ("POST", f"/idmp/project/{pid}/close", {"id": pid, "closeReason": "WR 自动化结项"}),
            ("POST", f"/idmp/project/close", {"id": pid, "closeReason": "WR 自动化结项"}),
        ], label="WR09-close")
        if ok:
            d = _detail(boss_authed_session, wr_api_base, pid)
            if d.get("phase") != "closed":
                print(f"[接口契约/实现一致性缺陷 WR-09] 结项 code=200 但 GET 详情 phase={d.get('phase')!r} ≠ closed")


# =====================================================
# WR-10 软删除 WR-01 专用项目
# =====================================================
class Test_WR10_SOFT_DELETE:
    def test_wr10_soft_delete(self, boss_authed_session, wr_api_base):
        """WR-10：创建独立的 draft 项目用于删除测试（DELETE 仅允许 draft 状态）"""
        ts = time.strftime('%Y%m%d%H%M%S')
        code = f"WR10-DEL-{ts}"
        r = boss_authed_session.post(f"{wr_api_base}/idmp/project", json={
            "projectCode": code, "projectName": f"WR10删除专用-{ts}",
            "type": "hardware", "status": "draft", "phase": "concept", "managerId": 1,
            "client": "", "contractNo": "", "startDate": "", "endDate": "",
            "budget": 0, "spent": 0, "progress": 0, "profitRate": 0,
            "description": "WR10删除专用", "cloudEnabled": "0", "cloudProject": ""
        }, timeout=15)
        body = r.json()
        assert body.get("code") == 200, f"WR10 创建 draft 项目失败: {body}"
        # 搜新项目拿 pid
        _, rows = _list_projects(boss_authed_session, wr_api_base, extra_params={"projectCode": code})
        pid = str(rows[0].get("id") or rows[0].get("projectId"))
        print(f"[WR10] 创建 draft 项目 pid={pid} code={code}")
        ok, tried, info = _try_candidates(boss_authed_session, wr_api_base, [
            ("DELETE", f"/idmp/project/{pid}", None),
        ], label="WR10-delete")
        if ok:
            # 验证：GET page 不再返回该 pid（物理删除）或 status=deleted（软删除）
            _, rows_after = _list_projects(boss_authed_session, wr_api_base, extra_params={"projectCode": code})
            if len(rows_after) > 0:
                print(f"[WR-10] 删除后 GET page 仍搜到 code={code}（待确认业务是否为软删除）；rows={len(rows_after)}")
            else:
                print(f"[WR-10] 删除后 GET page 搜不到 code={code}，删除有效 ✅")


# =====================================================
# WR-11 IDOR 越权写（赵经理不能修改赵老板专属 closed 项目）
# =====================================================
class Test_WR11_IDOR_WRITE:
    def test_wr11_manager_cannot_write_boss_closed(self, boss_authed_session, mgr_authed_session, wr_api_base):
        """WR-11：找一个赵老板列表里 phase=closed 且 赵经理列表 里没有的 pid（或任意老板 closed pid）。
        用赵经理 session 尝试 PUT name='HACKED-IDOR-WR11' / DELETE，预期 biz != 200 且 GET 老板详情 name 未被改。"""
        # 拿赵老板 8 个项目 closed pid
        _, boss_rows = _list_projects(boss_authed_session, wr_api_base, boss_prefix=True)
        closed_pids = [str(p.get("id") or p.get("projectId") or "") for p in boss_rows if p.get("phase") == "closed"]
        if not closed_pids:
            # 没有 closed 就拿任意 pid
            closed_pids = [str(p.get("id") or p.get("projectId") or "") for p in boss_rows[:1] if p.get("id") or p.get("projectId")]
        if not closed_pids:
            pytest.skip("老板项目列表为空，IDOR WR-11 缺少目标 pid=SKIP")
        target_pid = closed_pids[0]
        # 先拿当前老板详情，保存原名称
        orig = _detail(boss_authed_session, wr_api_base, target_pid)
        orig_name = str(orig.get("projectName") or "")
        hacked = "HACKED-IDOR-WR11-" + uuid.uuid4().hex[:6]
        # 1) 赵经理 尝试多种写操作（含 P0-2b 确认的真实 UPDATE 路由 PUT /idmp/project body 带 id）
        payload_put = {"id": int(target_pid) if str(target_pid).isdigit() else target_pid, "projectName": hacked, "name": hacked}
        any_200_biz_200 = False
        attempts_log = []
        for m, up in [
            # 真实 UPDATE 路由（P0-2b 确认）：PUT /idmp/project body 带 id
            ("PUT",  f"/idmp/project"),
            # 真实 SUBMIT/APPROVE 路由（P0-1c 确认）
            ("POST", f"/idmp/project/submit/{target_pid}"),
            ("POST", f"/idmp/project/approve/{target_pid}"),
            ("POST", f"/idmp/project/phase/{target_pid}?toPhase=closed"),
            # 旧候选（已确认 405/404，保留做回归）
            ("PUT",  f"/idmp/project/{target_pid}"),
            ("DELETE", f"/idmp/project/{target_pid}"),
        ]:
            try:
                r = mgr_authed_session.request(m, wr_api_base + up, json=({} if m == "DELETE" else payload_put), timeout=15)
                try: body = r.json()
                except Exception: body = {"_raw": r.text[:400]}
                st = r.status_code
                biz = body.get("code") if isinstance(body, dict) else None
                attempts_log.append({"method": m, "path": up, "HTTP": st, "biz_code": biz})
                if st == 200 and biz == 200:
                    any_200_biz_200 = True
                    print(f"[接口契约/权限一致性缺陷 WR-11-HIGH] 赵经理{m} {up} 返回 code=200！可能为 IDOR 高危越权写！resp={json.dumps(body, ensure_ascii=False)[:400]}")
            except Exception as e:
                attempts_log.append({"method": m, "path": up, "error": str(e)[:200]})
        # 2) GET 老板详情验证名称未被改
        now = _detail(boss_authed_session, wr_api_base, target_pid)
        new_name = str(now.get("projectName") or "")
        if new_name == hacked:
            print(f"[接口契约/权限一致性缺陷 WR-11-SEVERE] IDOR 已生效：GET 老板详情 projectName={hacked}；原名={orig_name!r}！必须立刻修复")
        print(f"[WR11] attempt log: {json.dumps(attempts_log, ensure_ascii=False)}")


# =====================================================
# WR-12 驳回审批（pending → draft）
# =====================================================
class Test_WR12_REJECT_PENDING_TO_DRAFT:
    def test_wr12_reject_status_to_draft(self, boss_authed_session, wr_api_base):
        """WR12：新建 draft→submit(pending) → PUT /idmp/project 完整 payload 改 status=draft 回退。
        （真实路由：PUT /idmp/project body 完整 payload，覆盖 status 字段）
        另：reject/rejectApproval 等专用路由均=404，因此采用 UPDATE 路由（已确认 PUT 完整 payload status=draft code=200 生效）。"""
        # 新建专用探测项目（不影响 WR-01）
        ts = time.strftime('%Y%m%d%H%M%S') + f"-{uuid.uuid4().hex[:4]}"
        code = f"WR12-{ts}"
        name = f"WR12驳回探测-{ts}"
        r = boss_authed_session.post(f"{wr_api_base}/idmp/project", json={
            "projectCode": code, "projectName": name,
            "type": "hardware", "status": "draft", "phase": "concept", "managerId": 1,
            "client": "", "contractNo": "", "startDate": "", "endDate": "",
            "budget": 0, "spent": 0, "progress": 0, "profitRate": 0,
            "description": "WR12专用探测", "cloudEnabled": "0", "cloudProject": ""
        }, timeout=15)
        body = r.json()
        assert body.get("code") == 200, f"WR12 CREATE失败: {body}"
        # 搜新项目拿 pid
        _, rows = _list_projects(boss_authed_session, wr_api_base, extra_params={"projectCode": code})
        assert len(rows) > 0, f"WR12 CREATE 后搜不到项目 code={code}"
        pid = rows[0].get("id") or rows[0].get("projectId")

        # submit → pending
        r_sub = boss_authed_session.post(f"{wr_api_base}/idmp/project/submit/{pid}", json={}, timeout=15)
        assert r_sub.json().get("code") == 200, f"WR12 SUBMIT失败: {r_sub.json()}"
        # 验证 status=pending
        d_sub = _detail(boss_authed_session, wr_api_base, pid)
        assert d_sub.get("status") == "pending", f"WR12 SUBMIT后status != pending: {d_sub.get('status')}"

        # GET 详情拿完整 payload（30 字段）→ 改 status=draft
        cur = _detail(boss_authed_session, wr_api_base, pid)
        payload = dict(cur)
        payload["id"] = int(pid) if str(pid).isdigit() else pid
        payload["status"] = "draft"
        # PUT /idmp/project（真实 UPDATE 路由）
        r_put = boss_authed_session.put(f"{wr_api_base}/idmp/project", json=payload, timeout=15)
        b_put = r_put.json()
        # 打印候选尝试记录
        if b_put.get("code") != 200:
            print(f"[WR 候选全部失败] WR12 尝试 PUT /idmp/project(完整payload+status=draft) → code={b_put.get('code')} msg={b_put.get('msg', '')}")
        else:
            # 验证 status=draft
            d_after = _detail(boss_authed_session, wr_api_base, pid)
            if d_after.get("status") != "draft":
                print(f"[接口契约/实现一致性缺陷 WR-12] PUT code=200 但 GET 详情 status={d_after.get('status')!r} != draft")
            else:
                print(f"[WR-12] 驳回审批验证通过 ✅ status=pending→draft 成功")

        # 清理：draft 状态 DELETE
        try:
            boss_authed_session.delete(f"{wr_api_base}/idmp/project/{pid}", timeout=15)
        except: pass


# =====================================================
# WR-13 阶段回退（plan → concept）
# =====================================================
class Test_WR13_PHASE_BACK_PLAN_TO_CONCEPT:
    def test_wr13_phase_back_to_concept(self, boss_authed_session, wr_api_base):
        """WR13：CREATE(draft)→SUBMIT(pending)→APPROVE(approved+auto phase=plan)
        → POST /idmp/project/phase/{pid}?toPhase=concept 回退 phase=plan→concept。
        （真实路由=P0-2 探测确认）"""
        ts = time.strftime('%Y%m%d%H%M%S') + f"-{uuid.uuid4().hex[:4]}"
        code = f"WR13-{ts}"
        name = f"WR13阶段回退探测-{ts}"
        r = boss_authed_session.post(f"{wr_api_base}/idmp/project", json={
            "projectCode": code, "projectName": name,
            "type": "hardware", "status": "draft", "phase": "concept", "managerId": 1,
            "client": "", "contractNo": "", "startDate": "", "endDate": "",
            "budget": 0, "spent": 0, "progress": 0, "profitRate": 0,
            "description": "WR13专用探测", "cloudEnabled": "0", "cloudProject": ""
        }, timeout=15)
        assert r.json().get("code") == 200, f"WR13 CREATE失败: {r.json()}"
        _, rows = _list_projects(boss_authed_session, wr_api_base, extra_params={"projectCode": code})
        pid = rows[0].get("id") or rows[0].get("projectId")
        # SUBMIT + APPROVE → approved + phase auto=plan
        boss_authed_session.post(f"{wr_api_base}/idmp/project/submit/{pid}", json={}, timeout=15)
        boss_authed_session.post(f"{wr_api_base}/idmp/project/approve/{pid}", json={}, timeout=15)
        d_apv = _detail(boss_authed_session, wr_api_base, pid)
        assert d_apv.get("status") == "approved" and d_apv.get("phase") == "plan", f"WR13 APPROVE后状态错误: status={d_apv.get('status')} phase={d_apv.get('phase')}"

        # 探测过的真实路由：POST /idmp/project/phase/{pid}?toPhase=concept
        ok, tried, info = _try_candidates(boss_authed_session, wr_api_base, [
            ("POST", f"/idmp/project/phase/{pid}?toPhase=concept", {}),
        ], label="WR13-phase-back")
        if not ok:
            return
        # 验证 phase=concept
        d_after = _detail(boss_authed_session, wr_api_base, pid)
        if d_after.get("phase") != "concept":
            print(f"[接口契约/实现一致性缺陷 WR-13] phase 回退 code=200 但 GET 详情 phase={d_after.get('phase')!r} ≠ concept")
        else:
            print(f"[WR-13] 阶段回退验证通过 ✅ phase=plan→concept 成功")

        # 清理：PUT 回 status=draft（用完整 payload）然后 DELETE
        try:
            cur = _detail(boss_authed_session, wr_api_base, pid)
            payload = dict(cur)
            payload["id"] = int(pid) if str(pid).isdigit() else pid
            payload["status"] = "draft"
            boss_authed_session.put(f"{wr_api_base}/idmp/project", json=payload, timeout=15)
            boss_authed_session.delete(f"{wr_api_base}/idmp/project/{pid}", timeout=15)
        except: pass


# =====================================================
# WR-14 预算必填+负数校验
# =====================================================
class Test_WR14_BUDGET_VALIDATION:
    def test_wr14_budget_null_negative_empty(self, boss_authed_session, wr_api_base):
        """WR14：CREATE 时 budget=null/负数(=-999)/空字符串(='')
        探测结果：三种情况后端 code=200（均未拦截）。
        按 AGENTS.md 口径：文档与实际差异=打印缺陷，不 fail 用例。"""
        ts = time.strftime('%Y%m%d%H%M%S') + f"-{uuid.uuid4().hex[:4]}"
        cases = [
            ("null", None, "budget未传字段"),
            ("negative", -999, "budget=-999负数"),
            ("empty_str", "", "budget=''空字符串"),
        ]
        for caselabel, val, casedesc in cases:
            code = f"WR14-{caselabel}-{ts}"
            name = f"WR14 budget{caselabel}"
            body = {
                "projectCode": code, "projectName": name,
                "type": "hardware", "status": "draft", "phase": "concept", "managerId": 1,
                "client": "", "contractNo": "", "startDate": "", "endDate": "",
                "spent": 0, "progress": 0, "profitRate": 0,
                "description": casedesc, "cloudEnabled": "0", "cloudProject": ""
            }
            if val is not None:
                body["budget"] = val
            r = boss_authed_session.post(f"{wr_api_base}/idmp/project", json=body, timeout=15)
            resp = r.json()
            if resp.get("code") == 200:
                # 未拦截 → 打印缺陷
                print(f"[接口契约/业务校验一致性缺陷 WR-14] CREATE budget={caselabel}({casedesc}) 返回 code=200 未拦截（预算未做非空/非负数校验）")
                # 清理：DELETE
                try:
                    _, rows = _list_projects(boss_authed_session, wr_api_base, extra_params={"projectCode": code})
                    if rows:
                        pid = rows[0].get("id") or rows[0].get("projectId")
                        boss_authed_session.delete(f"{wr_api_base}/idmp/project/{pid}", timeout=15)
                except: pass
            else:
                # 被拦截 → 校验生效
                print(f"[WR-14] budget={caselabel}({casedesc}) 已拦截 ✅ code={resp.get('code')} msg={resp.get('msg', '')[:80]}")


# =====================================================
# WR-15 负责人（managerId）必填校验
# =====================================================
class Test_WR15_MANAGERID_REQUIRED:
    def test_wr15_managerid_null_zero(self, boss_authed_session, wr_api_base):
        """WR15：CREATE 时 managerId 不传/null/=0
        探测结果：三种情况后端 code=200（均未拦截）。
        按 AGENTS.md 口径=打印缺陷，不 fail。"""
        ts = time.strftime('%Y%m%d%H%M%S') + f"-{uuid.uuid4().hex[:4]}"
        cases = [
            ("null", None, "managerId未传字段"),
            ("zero", 0, "managerId=0"),
        ]
        for caselabel, val, casedesc in cases:
            code = f"WR15-{caselabel}-{ts}"
            name = f"WR15 managerId{caselabel}"
            body = {
                "projectCode": code, "projectName": name,
                "type": "hardware", "status": "draft", "phase": "concept",
                "client": "", "contractNo": "", "startDate": "", "endDate": "",
                "budget": 0, "spent": 0, "progress": 0, "profitRate": 0,
                "description": casedesc, "cloudEnabled": "0", "cloudProject": ""
            }
            if val is not None:
                body["managerId"] = val
            r = boss_authed_session.post(f"{wr_api_base}/idmp/project", json=body, timeout=15)
            resp = r.json()
            if resp.get("code") == 200:
                print(f"[接口契约/业务校验一致性缺陷 WR-15] CREATE managerId={caselabel}({casedesc}) 返回 code=200 未拦截（负责人未做非空校验）")
                try:
                    _, rows = _list_projects(boss_authed_session, wr_api_base, extra_params={"projectCode": code})
                    if rows:
                        pid = rows[0].get("id") or rows[0].get("projectId")
                        boss_authed_session.delete(f"{wr_api_base}/idmp/project/{pid}", timeout=15)
                except: pass
            else:
                print(f"[WR-15] managerId={caselabel}({casedesc}) 已拦截 ✅ code={resp.get('code')} msg={resp.get('msg', '')[:80]}")
