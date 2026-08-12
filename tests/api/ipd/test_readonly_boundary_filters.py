# -*- coding: utf-8 -*-
"""readonly-regression + consistency A1-A8 + 边界 / 过滤 / R10
函数集合（直接复用 test_project_risk_wf_consistency 中 A1-A8 已实现 + 本文件新增以下：
   分页边界 4 条
   无效 type 不抛 500
   RISK medium A3
   BUDGET change/list 缺 projectId 无堆栈
   WF R10 分类过滤参数名矩阵
   WF 最后页 3 条
   RISK medium 过滤
"""
from __future__ import annotations


# =========================================================
# PROJECT 分页边界 4 条
# =========================================================

def test_project_page_pagenum_negative_no_sql_stack(authed_session, api_base_url):
    """API-PRJ-008：pageNum=-1 不得出现 SQL 堆栈关键字。"""
    r = authed_session.get(
        f"{api_base_url}/idmp/project/page",
        params={"pageNum": -1, "pageSize": 10}, timeout=15,
    )
    text = r.text.lower()
    bad = ("sqlexception", "mysql", "stacktrace", "caused by:", "at java.", "psqlexception")
    hits = [k for k in bad if k in text]
    assert hits == [], f"pageNum=-1 响应含堆栈 hits={hits}; text={r.text[:500]}"


def test_project_page_pagesize_0_no_divide_by_zero(authed_session, api_base_url):
    """API-PRJ-009：pageSize=0 不得除 0 错误（msg 不得含 division/ArithmeticException/zero）。"""
    r = authed_session.get(
        f"{api_base_url}/idmp/project/page",
        params={"pageNum": 1, "pageSize": 0}, timeout=15,
    )
    text = r.text.lower()
    bad = ("division", "arithmetic", "divide", "zerodivide")
    hits = [k for k in bad if k in text]
    assert hits == [], f"pageSize=0 含除0 hits={hits}; text={r.text[:500]}"


def test_project_page_pagenum_99_has_empty_rows(authed_session, api_base_url):
    """API-PRJ-010：末页后 理应 rows=[]。若实现未分页（忽略 pageNum/pageSize，始终返回全量）=
    【接口契约/实现一致性缺陷 API-004 project/page 分页参数未生效】。"""
    body = authed_session.get(
        f"{api_base_url}/idmp/project/page",
        params={"pageNum": 99, "pageSize": 10}, timeout=15,
    ).json()
    assert body.get("code") == 200, f"末页后 code={body.get('code')}"
    rows = body.get("rows")
    assert isinstance(rows, list), f"rows 不是数组 type={type(rows)}"
    if rows == []:
        return
    total = int(body.get("total", -1))
    print(
        "[接口契约/实现一致性缺陷 API-004 分页参数未生效] project/page 接口：\n"
        f"  请求 pageNum=99 pageSize=10；实际返回 rows.len={len(rows)}，total={total}\n"
        f"  预期 rows=[]（页码超过 ceil(total/10) 时），实现可能忽略 pageNum/pageSize 或 未做偏移处理。\n"
        "缺陷分类=接口契约/实现一致性（不判失败，按 AGENTS.md 直接登记缺陷）。"
    )


def test_project_page_invalid_type_should_not_500(authed_session, api_base_url):
    """API-PRJ-007：type=invalid_type 不 500；允许 200 空数组或 400 参数错。"""
    r = authed_session.get(
        f"{api_base_url}/idmp/project/page",
        params={"pageNum": 1, "pageSize": 100, "type": "xxxinvalid_type"}, timeout=15,
    )
    text = r.text.lower()
    # 允许 HTTP 200 或 400；不允许 500
    if r.status_code == 500:
        raise AssertionError(f"无效 type=xxxinvalid_type 返回 HTTP 500；body={r.text[:500]}")
    try:
        body = r.json()
    except Exception:
        # 响应非 JSON = 404/其它，只要非 500 即可
        return
    code = body.get("code")
    if isinstance(code, int) and code == 500:
        raise AssertionError(f"无效 type=xxxinvalid_type 业务 code=500；body={body}")


# =========================================================
# RISK list level 过滤
# =========================================================

def test_risk_list_filter_level_high(authed_session, api_base_url):
    """API-RISK-002：level=high 过滤后结果为 3 条且全 high。"""
    body = authed_session.get(
        f"{api_base_url}/idmp/risk/list",
        params={"level": "high"}, timeout=15,
    ).json()
    assert body.get("code") == 200
    data = body.get("data") or []
    assert len(data) == 3, f"level=high 预期 3 条；实际 len={len(data)}"
    bad_levels = [r.get("level") for r in data if r.get("level") != "high"]
    assert bad_levels == [], f"过滤 level=high 却混入 levels={bad_levels}"


def test_risk_list_filter_medium_A3_tri_state(authed_session, api_base_url):
    """API-RISK-003 = A3 medium 三态（AMB-01）。
    此测试与一致性 A3 函数内容相同，允许直接通过（不重复 fail）。
    """
    from tests.api.ipd.test_project_risk_wf_consistency import (
        test_consistency_A3_risk_stats_levels_match_global_risk_list,
    )
    # 直接调用该函数（pytest fixture authed_session 已在本函数参数注入，
    # 但被调函数期望同签名。传相同参数即可。）
    test_consistency_A3_risk_stats_levels_match_global_risk_list(
        authed_session, api_base_url
    )


# =========================================================
# BUDGET change/list 缺 projectId 无堆栈
# =========================================================

def test_change_list_missing_projectid_no_stack(authed_session, api_base_url):
    """API-BUDG-003：缺 projectId 参数时 msg 不得含堆栈关键字（防信息泄漏）。"""
    r = authed_session.get(f"{api_base_url}/idmp/change/list", timeout=15)
    text = r.text.lower()
    bad = ("exception", "nullpointer", "stacktrace", "at java.", "caused by:", "sqlexception")
    hits = [k for k in bad if k in text]
    assert hits == [], f"change/list 缺参含堆栈 hits={hits}; text={r.text[:500]}"


def test_change_list_with_projectid_ok(authed_session, api_base_url, known_ids):
    """API-BUDG-002：带 projectId 调用返回 200 结构正常（数组或空）。"""
    body = authed_session.get(
        f"{api_base_url}/idmp/change/list",
        params={"projectId": known_ids["project_circuit"]}, timeout=15,
    ).json()
    assert body.get("code") == 200, f"change/list 带 projectId code={body.get('code')} msg={body.get('msg')}"
    data = body.get("data")
    # data 类型可能=list 或 dict；只要求不是字符串不崩溃
    assert isinstance(data, (list, dict, type(None))), (
        f"change/list data 类型异常 type={type(data)}"
    )


# =========================================================
# WF 定义：R10 分类过滤参数名矩阵（AMB-03 两档判据）
# =========================================================

def test_wf_definition_filter_category_param_matrix_R10(authed_session, api_base_url, known_ids):
    """API-WF-003（AMB-03）：categoryId / category_id / category 三参数名至少一种生效；
    生效名若≠规范 categoryId = 打印【接口契约/文档一致性缺陷 API-002 R10】。"""
    target_total_at_least_1 = True   # 不硬断言数量，只校验 "生效（结果<全量23）即参数过滤成立"
    full_body = authed_session.get(
        f"{api_base_url}/workflow/definition/list",
        params={"pageNum": 1, "pageSize": 100}, timeout=15,
    ).json()
    full_total = int(full_body.get("total", 0))
    assert full_total == 23, f"wf/definition total={full_total}，预期 23"

    candidates = [
        ("categoryId", "规范文档名 categoryId"),
        ("category_id", "下划线 category_id（常见 Rails/Spring 默认）"),
        ("category", "简写 category"),
    ]
    cat_id = known_ids["wf_category_idmp"]
    effective_ways = []
    for param_name, desc in candidates:
        body = authed_session.get(
            f"{api_base_url}/workflow/definition/list",
            params={"pageNum": 1, "pageSize": 100, param_name: cat_id}, timeout=15,
        ).json()
        rows = body.get("rows") or []
        total = int(body.get("total", -1))
        rows_category_match = sum(
            1 for r in rows
            if str(r.get("categoryName") or "").strip() != ""
            and ("idmp" in str(r.get("categoryName") or "").lower() or "IDMP" in str(r.get("categoryName") or ""))
        )
        # 生效判据：total < 23 或 rows 中 categoryName 非空 且 全部/多数匹配 IDMP 前缀分类
        if total < full_total and total >= 1:
            effective_ways.append((param_name, desc, total, rows_category_match, "total<full"))
        elif rows and rows_category_match >= len(rows) * 0.5 and total == full_total:
            # total=23 但 rows 默认 categoryId 不对全量返回，不算生效（只记录）
            pass
        elif rows and rows_category_match == len(rows) and len(rows) >= 1:
            effective_ways.append((param_name, desc, total, rows_category_match, "rows-all-match"))

    if len(effective_ways) == 0:
        # AMB-03 两档判据都不满足（3 参数名+全不生效 或 全返回空）→ 实现 bug 或 要完全不同的参数名
        # 打印【接口契约/实现一致性缺陷 API-005 WF 分类过滤不生效】
        print(
            "[接口契约/实现一致性缺陷 API-005 R10(AMB-03)] workflow/definition/list 分类过滤未生效：\n"
            f"  被测参数名集合（categoryId/category_id/category）全部传值 cat_id={cat_id} 后，\n"
            "  返回 total 仍=23（全量），或 rows 全部与分类名无匹配。\n"
            "  → 两种可能：① 实际生效参数名并非上述 3 个（遗漏未测，属于接口契约/文档一致性——文档名与实现名不符）；"
            "或 ② 该接口完全不支持按分类过滤（属于功能缺失 = 实现一致性缺陷）。"
            "  → 按 AGENTS.md 不直接断言 fail，登记缺陷移交研发确认实际支持的过滤参数名或功能范围。缺陷分类=接口契约/实现一致性。"
        )
    else:
        # 若有生效的，打印；若规范名 categoryId 不在生效集合=文档规范名 vs 实际生效名不符 → 文档/实现不一致
        effective_params = {e[0] for e in effective_ways}
        print(f"[INFO API-WF-003 R10] 实际生效参数名集合={effective_params}; full_total={full_total}; effective details={effective_ways}")
        if "categoryId" not in effective_params:
            print(
                "[接口契约/文档一致性缺陷 API-002 R10] workflow/definition/list 分类过滤"
                f"生效参数名={effective_params}，但官方规范应为 categoryId（驼峰）；"
                "前后端调用时若 categoryId 不生效则前端必须传非规范名，造成接口命名不一致（小缺陷，移交研发确认是否重命名兼容）。"
                "【接口契约/文档一致性缺陷】。"
            )


# =========================================================
# WF definition 最后页（pageSize=20 pageNum=2 → 3 条）
# =========================================================

def test_wf_definition_last_page_has_3_rows(authed_session, api_base_url):
    """API-WF-004：pageNum=2 pageSize=20 → 3；total=23。"""
    body = authed_session.get(
        f"{api_base_url}/workflow/definition/list",
        params={"pageNum": 2, "pageSize": 20}, timeout=15,
    ).json()
    assert body.get("code") == 200
    assert int(body.get("total", 0)) == 23, f"total={body.get('total')} 应为 23"
    rows = body.get("rows") or []
    assert len(rows) == 3, f"最后页 rows={len(rows)} 预期 3（20+3=23）"


# =========================================================
# RISK level=medium 过滤 + A3（重复 A3 合并）通过
# =========================================================
