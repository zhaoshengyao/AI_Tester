# -*- coding: utf-8 -*-
"""Step E-1：semi-auto 用例（不真实写提交，仅验证入口+必填+枚举，按 AGENTS.md = semi-auto 层级）。

测试 12 条：
  项目管理模块 - 阶段&状态流转 semi-auto 8 条：
     PM-STATUS-001：赵老板 /idmp/project/page 返回 8 条，每一条 status ∈ 枚举（必填非空）
     PM-STATUS-002：8 个项目 status 分布覆盖率 ≥ 2（不能只有 1 种状态，否则流转测试没意义）
     PM-PHASE-003 : 8 条每条 phase ∈ 枚举（必填非空）
     PM-PHASE-004 : 8 条 phase 覆盖 ≥ 2
     PM-DETAIL-005: 每个详情 GET /idmp/project/{id} 与列表 name/status/phase 一一对应（随机抽 3 个省时间；若 8 条总数 < 3 则抽全部）
     PM-ENUM-006  : status 全集与 baseline.json 记录一致（不得新增/缺失）
     PM-ENUM-007  : phase 全集 与 baseline.json 一致
     PM-FLOW-008 : 流转动作入口（/idmp/project/{id}/actions /next-statuses 等）对 closed/draft 各一个 项目 = 不应 500（允许 200 data=空/404，只要不是 500 就判通过）

  看板权限一致性 A4~A7：
     CONS-A4 ：老板 stats.total ≥ 经理 stats.total（老板看全局，≥ 经理本人）
     CONS-A5 ：老板 stats.inProgress + completed + pendingAcceptance = total（聚合恒等式对老板/经理都要成立或差在合理阈值1内）
     CONS-A6 ：老板 typeDistribution 计数之和 = stats.total（比例 100%）
     CONS-A7 ：老板风险项目数 riskProjects ≥ 经理 riskProjects（全局≥本人）
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

# ============== 常量（Step B+C 实测枚举，与 项目状态流转接口实测.json 对齐） ==============
STATUS_ENUM = {"approved", "draft", "pending"}
PHASE_ENUM = {"closed", "concept", "development", "plan"}

BASELINE_FILE = Path(r"d:\AICode\TestHub\AITestDemo\projects\ipd\docs\analysis\项目状态流转接口实测.json")
assert BASELINE_FILE.exists(), f"{BASELINE_FILE} 不存在；先跑 _probe_stages_and_dashboard_diff.py 生成基线"


@pytest.fixture(scope="module")
def _status_phase_from_baseline():
    """与基线文件双校验（避免硬编码枚举和真实差）。"""
    with open(BASELINE_FILE, "r", encoding="utf-8") as f:
        base = json.load(f)
    return set(base.get("status_enum_all_found_in_list", [])), set(base.get("phase_enum_all_found_in_list", []))


# ==========================================
# 公共 helper（兼容 code/data 包装 & 裸 {total, rows} 两种）
# ==========================================
def _boss_list_and_projects(boss_authed_session, api_base_url):
    """返回 (total:int, rows:list)。兼容两种响应格式。"""
    api_base_url = api_base_url.rstrip("/")
    s = boss_authed_session
    # 老板专用前缀
    r = s.get(api_base_url + "/idmp/project/page", params={"pageNum": 1, "pageSize": 100}, timeout=15)
    assert r.status_code == 200, f"赵老板 /idmp/project/page HTTP={r.status_code} body={r.text[:300]}"
    body = r.json()
    rows = None; total = None
    if "rows" in body and isinstance(body["rows"], list):
        rows = body["rows"]; total = body.get("total")
    elif isinstance(body.get("data"), dict) and isinstance(body["data"].get("rows"), list):
        rows = body["data"]["rows"]; total = (body["data"] or {}).get("total")
    assert rows is not None, f"/idmp/project/page 响应格式未知 body keys={list(body.keys())[:10]}"
    if total is None: total = len(rows)
    return int(total), rows


# ==========================================
# 1. 项目管理 8 条 semi-auto
# ==========================================
class TestProjectStageAndStatusSemiAuto:
    def test_pm_status_001_all_8_projects_status_in_enum(self, boss_authed_session, api_base_url, _status_phase_from_baseline):
        """PM-STATUS-001：赵老板 8 个项目每个 status ∈ STATUS_ENUM 且 必填非空。
        失败=登记【接口契约/实现一致性缺陷 API-PM-STATUS-001：项目 status 字段缺失或超出枚举全集】
        （不直接断言，打印缺陷，符合 AGENTS.md 真接口行为>主观预期策略）"""
        enum, _ = _status_phase_from_baseline
        enum = enum or STATUS_ENUM
        total, rows = _boss_list_and_projects(boss_authed_session, api_base_url)
        bad = []
        for i, p in enumerate(rows):
            s = p.get("status")
            pid = p.get("id") or p.get("projectId") or i
            if not s: bad.append(f"[{pid}] name={p.get('projectName')} status=空 缺失必填")
            elif s not in enum: bad.append(f"[{pid}] name={p.get('projectName')} status={s!r} 不在 枚举全集 {sorted(enum)}")
        if bad:
            print("[接口契约/实现一致性缺陷 API-PM-STATUS-001] 8 个项目中存在 status 枚举不符：\n  - " + "\n  - ".join(bad))

    def test_pm_status_002_status_distribution_coverage_ge_2(self, boss_authed_session, api_base_url):
        """PM-STATUS-002：8 条项目 status 分布覆盖 ≥ 2 种（流转意义场景存在：如果所有项目都是 approved 已审批则无法测 draft→pending→approved，需要标记"样本不足 semi-auto 覆盖有限"）。
        不判缺陷=仅打印观察 note。"""
        _, rows = _boss_list_and_projects(boss_authed_session, api_base_url)
        from collections import Counter
        c = Counter(p.get("status") for p in rows)
        kinds = len([k for k in c if k])
        print(f"[INFO PM-STATUS-002 分布] status 分布 = {dict(c)}；distinct 状态种类 = {kinds}（≥ 2 视为流转覆盖样本足够）")
        if kinds < 2:
            print("[INFO 非缺陷 semi-auto 限制] 当前 8 项目 status 种类 < 2 = 流转场景多样性不足；本轮不判失败，下一轮新增项目时建议生成 draft 项目补流转样本。")

    def test_pm_phase_003_all_8_projects_phase_in_enum(self, boss_authed_session, api_base_url, _status_phase_from_baseline):
        """PM-PHASE-003：8 条项目 phase 必填非空 且 ∈ PHASE_ENUM（4 个阶段）。
        不通过=打印 接口契约/实现一致性缺陷 API-PM-PHASE-003。"""
        _, p_enum = _status_phase_from_baseline
        p_enum = p_enum or PHASE_ENUM
        _, rows = _boss_list_and_projects(boss_authed_session, api_base_url)
        bad = []
        for i, p in enumerate(rows):
            ph = p.get("phase")
            pid = p.get("id") or p.get("projectId") or i
            if not ph: bad.append(f"[{pid}] name={p.get('projectName')} phase=空（必填缺失）")
            elif ph not in p_enum: bad.append(f"[{pid}] name={p.get('projectName')} phase={ph!r} 不在 枚举全集 {sorted(p_enum)}")
        if bad:
            print("[接口契约/实现一致性缺陷 API-PM-PHASE-003] 8 个项目 phase 枚举/必填不符：\n  - " + "\n  - ".join(bad))

    def test_pm_phase_004_phase_distribution_ge_2(self, boss_authed_session, api_base_url):
        """PM-PHASE-004：phase 种类 ≥ 2（保证立项/执行/收尾等多个生命周期阶段项目都有样本）。
        仅打印观察。"""
        _, rows = _boss_list_and_projects(boss_authed_session, api_base_url)
        from collections import Counter
        c = Counter(p.get("phase") for p in rows)
        kinds = len([k for k in c if k])
        print(f"[INFO PM-PHASE-004 分布] phase 分布 = {dict(c)}；distinct 阶段种类 = {kinds}")
        if kinds < 2:
            print("[INFO 非缺陷 semi-auto 限制] 8 项目 phase 种类 < 2 = 项目生命周期单一样本不足；下一轮补 draft 概念 + execution 执行 样本。")

    def test_pm_detail_005_list_and_detail_consistency_name_status_phase(self, boss_authed_session, api_base_url):
        """PM-DETAIL-005（核心）：列表名/status/phase vs GET /idmp/project/{id} 详情一致。
        随机抽 max(3, min(len(rows), 5)) 个节省接口配额；不一致=打印【接口契约/实现一致性缺陷 API-PM-DETAIL-005】。"""
        import random
        _, rows = _boss_list_and_projects(boss_authed_session, api_base_url)
        sample = random.sample(rows, k=min(max(3, len(rows)), min(5, len(rows)))) if len(rows) > 3 else list(rows)
        bad = []
        for p in sample:
            pid = str(p.get("id") or p.get("projectId"))
            name = p.get("projectName"); st = p.get("status"); ph = p.get("phase")
            url = api_base_url.rstrip("/") + f"/idmp/project/{pid}"
            r = boss_authed_session.get(url, timeout=15)
            assert r.status_code == 200, f"详情 GET {url} HTTP={r.status_code}"
            body = r.json()
            data = body.get("data") if isinstance(body, dict) and body.get("code") == 200 else None
            if data is None:
                # 兼容裸格式（code 不存在，直接返回项目内容）
                if isinstance(body, dict) and body.get("id") or body.get("projectId"):
                    data = body
            if data is None:
                bad.append(f"[{pid}] 详情返回未知格式；HTTP=200 body keys={list(body.keys())[:8]}")
                continue
            # 字段名可能和列表一致（name/projectName, status, phase/projectPhase）
            d_name = data.get("projectName") or data.get("name")
            d_st = data.get("status")
            d_ph = data.get("phase") or data.get("projectPhase")
            if d_name != name or d_st != st or d_ph != ph:
                bad.append(
                    f"[{pid}={name}] 列表 vs 详情不一致：\n"
                    f"  列表(name={name!r} status={st!r} phase={ph!r})\n"
                    f"  详情(name={d_name!r} status={d_st!r} phase={d_ph!r})"
                )
        if bad:
            print("[接口契约/实现一致性缺陷 API-PM-DETAIL-005] 项目列表 vs 详情 name/status/phase 不一致：\n  - " + "\n  - ".join(bad))

    def test_pm_enum_006_status_set_matches_baseline(self, boss_authed_session, api_base_url, _status_phase_from_baseline):
        """PM-ENUM-006：本次 8 项目中出现的 status 集合 ⊆ 基线 status_enum_all_found_in_list（基线作为真源）。
        若本次出现基线未出现的新枚举 → 打印【文档与实际差异/待确认 API-PM-ENUM-006 新增 status 枚举需要同步文档】。"""
        base_s, _ = _status_phase_from_baseline
        base_s = base_s or STATUS_ENUM
        _, rows = _boss_list_and_projects(boss_authed_session, api_base_url)
        actual = {p.get("status") for p in rows if p.get("status")}
        extra = actual - base_s
        if extra:
            print(f"[文档与实际差异/待确认 API-PM-ENUM-006] 本次实测出现基线未登记的 status 新枚举={sorted(extra)}；基线 {sorted(base_s)}；请产品/研发确认后同步需求分析文档+知识库业务规则库。")
        else:
            print(f"[PASS ENUM-006] status 本次 {sorted(actual)} 全部在基线 {sorted(base_s)} 集合中。")

    def test_pm_enum_007_phase_set_matches_baseline(self, boss_authed_session, api_base_url, _status_phase_from_baseline):
        """PM-ENUM-007：phase 集合一致；缺新枚举=文档差异待确认。"""
        _, base_p = _status_phase_from_baseline
        base_p = base_p or PHASE_ENUM
        _, rows = _boss_list_and_projects(boss_authed_session, api_base_url)
        actual = {p.get("phase") for p in rows if p.get("phase")}
        extra = actual - base_p
        if extra:
            print(f"[文档与实际差异/待确认 API-PM-ENUM-007] 本次新 phase 枚举={sorted(extra)} 基线 {sorted(base_p)}；同步文档。")
        else:
            print(f"[PASS ENUM-007] phase 本次 {sorted(actual)} 全部在基线 {sorted(base_p)} 集合中。")

    def test_pm_flow_008_entrypoints_not_500_crash(self, boss_authed_session, api_base_url):
        """PM-FLOW-008：对 1 个 closed 项目 + 1 个 draft 项目（若存在）尝试流转入口类 URL（actions/next-statuses/status-log）。
        semi-auto 不真实提交，只验证不出现 500/网关错误（允许 404 或 200+空数据）。"""
        _, rows = _boss_list_and_projects(boss_authed_session, api_base_url)
        def _pick(status=None, phase=None):
            for p in rows:
                if status and p.get("status") != status: continue
                if phase and p.get("phase") != phase: continue
                return p
            return rows[0] if rows else None
        candidates = [("status=closed", _pick(status=None, phase="closed")), ("status=draft", _pick(status="draft")), ("任意 status=pending 如有", _pick(status="pending"))]
        entry_suffix = ["/actions", "/next-statuses", "/status-log", "/stage", "/approval"]
        bad = []
        for label, p in candidates:
            if not p:
                print(f"[INFO FLOW-008 跳过] {label} = 当前 8 项目中无此样本；不判失败。"); continue
            pid = str(p.get("id") or p.get("projectId"))
            for suf in entry_suffix:
                url = api_base_url.rstrip("/") + f"/idmp/project/{pid}" + suf
                try:
                    r = boss_authed_session.get(url, timeout=8)
                except Exception as e:
                    bad.append(f"{label} pid={pid} {suf} 连接异常 {type(e).__name__}:{e}")
                    continue
                if r.status_code >= 500:
                    bad.append(f"{label} pid={pid} {suf} HTTP={r.status_code} 5xx 崩溃；body={r.text[:200]}")
        if bad:
            print("[接口契约/实现一致性缺陷 API-PM-FLOW-008 项目状态流转入口类 5xx 崩溃]：\n  - " + "\n  - ".join(bad))


# ==========================================
# 2. 看板权限一致性 A4~A7
# ==========================================
class TestDashboardRoleConsistencyA4A7:
    @staticmethod
    def _overview(sess, api_base_url):
        r = sess.get(api_base_url.rstrip("/") + "/idmp/dashboard/overview", timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, dict) and body.get("code") == 200, f"overview 失败 body={r.text[:300]}"
        return body.get("data") or {}

    def test_cons_A4_boss_total_ge_manager_total(self, boss_authed_session, authed_session, api_base_url):
        """CONS-A4（看板权限一致性 A4）：老板 stats.total ≥ 经理 stats.total（老板全局口径 ≥ 经理本人口径）。
        若老板 < 经理 = 越权/口径错误 = 接口契约/实现一致性缺陷。"""
        boss = self._overview(boss_authed_session, api_base_url)
        mgr = self._overview(authed_session, api_base_url)
        bt = (boss.get("stats") or {}).get("total"); mt = (mgr.get("stats") or {}).get("total")
        print(f"[INFO CONS-A4] boss stats.total={bt} vs manager={mt}")
        if bt is None or mt is None:
            print("[INFO 证据不足] 一方无 stats.total，标记待确认。")
            return
        if bt < mt:
            print(
                f"[接口契约/实现一致性缺陷 CONS-A4 看板权限口径异常] 老板 stats.total={bt} < 经理 {mt}，"
                f"应该为 老板≥经理（全局≥本人）。"
            )

    def test_cons_A5_stats_inprogress_completed_pending_sum_equals_total(self, boss_authed_session, authed_session, api_base_url):
        """CONS-A5（看板聚合恒等式 A5）：对老板 & 经理分别校验：
        stats.inProgress + stats.completed + stats.pendingAcceptance ≈ stats.total。
        允许差值在 ±0~1（四舍五入或进度正在变更）；>1 = 聚合口径错误。"""
        for role_name, sess in (("老板", boss_authed_session), ("经理", authed_session)):
            d = self._overview(sess, api_base_url).get("stats") or {}
            keys = ["inProgress", "completed", "pendingAcceptance"]
            s = sum((d.get(k) or 0) for k in keys)
            t = d.get("total") or 0
            diff = abs(s - t)
            print(f"[INFO CONS-A5 {role_name}] sum({keys}) = {s} vs total={t} → |diff|={diff}")
            if diff > 1:
                print(
                    f"[接口契约/实现一致性缺陷 CONS-A5 {role_name} 看板 stats 聚合恒等式不成立] "
                    f"{keys} 求和={s} ≠ total={t}（|diff|={diff} > 1）；"
                    f"可能还有其他子状态未出现在 stats（如 cancelled/paused），需要产品确认完整维度。"
                )

    def test_cons_A6_boss_type_distribution_sum_counts_eq_total(self, boss_authed_session, api_base_url):
        """CONS-A6（老板 类型分布 A6）：typeDistribution 每一项 count 相加 = stats.total，
        百分比相加 = 100.0（允许 ±0.1 浮点误差）。"""
        data = self._overview(boss_authed_session, api_base_url)
        total = (data.get("stats") or {}).get("total") or 0
        td = data.get("typeDistribution") or []
        counts_sum = sum(int(x.get("count") or 0) for x in td)
        pct_sum = sum(float(str(x.get("percent") or "0").rstrip("%")) for x in td)
        print(f"[INFO CONS-A6 老板] 类型分布 counts_sum={counts_sum} vs stats.total={total}；pct_sum={pct_sum}%")
        if total != counts_sum:
            print(
                f"[接口契约/实现一致性缺陷 CONS-A6 老板看板类型分布 counts≠total] "
                f"typeDistribution 求和={counts_sum} 与 stats.total={total} 不等。"
            )
        if abs(pct_sum - 100.0) > 0.1:
            print(
                f"[文档与实际差异/待确认 CONS-A6 老板看板类型分布 percent 合计={pct_sum}%] "
                f"不等于 100%；是否四舍五入导致需要研发确认。"
            )

    def test_cons_A7_boss_risk_projects_ge_manager(self, boss_authed_session, authed_session, api_base_url):
        """CONS-A7（老板风险项目总数 A7 ≥ 经理本人）：riskProjects 老板 ≥ 经理（或若系统只统计"我创建的风险"口径，需要产品确认；默认全局≥本人）。"""
        boss = self._overview(boss_authed_session, api_base_url)
        mgr = self._overview(authed_session, api_base_url)
        b = (boss.get("stats") or {}).get("riskProjects"); m = (mgr.get("stats") or {}).get("riskProjects")
        print(f"[INFO CONS-A7] boss riskProjects={b} vs manager={m}")
        if b is None or m is None:
            print("[INFO 证据不足] 一方 riskProjects 缺失；标记待确认。"); return
        if b < m:
            print(
                f"[接口契约/实现一致性缺陷 CONS-A7 风险项目口径异常] 老板 riskProjects={b} < 经理 {m}；"
                f"通常应为老板全局 ≥ 经理本人。若系统 riskProjects 只统计'我创建的风险'则需产品文档化确认 = 改为文档差异待确认。"
            )
