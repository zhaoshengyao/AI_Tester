# -*- coding: utf-8 -*-
"""Step I-3.1 (a)：把 Playwright HAR 捕获的 CREATE 请求 + probe 脚本探测到的候选写接口，整合成【IPD项目管理写接口捕获清单.json】。
清单结构：
{
  "capture_time": "...",
  "captured_interfaces": [
    {no, use_case, method, url, payload_fields, response_biz_code_example, body_example, notes}
  ],
  "candidate_interfaces_for_wr11": [
    {no, use_case, candidate_method_url_list, wr_action_hint, payload_hint}
  ]
}
"""
from __future__ import annotations
import json, time, sys
from pathlib import Path

REPO = Path(r"d:\AICode\TestHub\AITestDemo")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tests" / "api" / "ipd"))

HAR_MANIFEST = REPO / "projects/ipd/docs/analysis/zhaoboss-ui-write-captures/capture_manifest.json"
PROBE_OUT  = REPO / "projects/ipd/docs/analysis/IPD项目管理写接口探测结果.json"
OUT_FILE   = REPO / "projects/ipd/docs/analysis/IPD项目管理写接口捕获清单.json"

har = json.loads(HAR_MANIFEST.read_text(encoding="utf-8")) if HAR_MANIFEST.exists() else {"captured_non_get_requests": []}
probe = json.loads(PROBE_OUT.read_text(encoding="utf-8")) if PROBE_OUT.exists() else {}

captured = []
wr_candidates = []

# ----------- 1) 从 HAR 提取已抓包接口 -----------
for i, r in enumerate(har.get("captured_non_get_requests") or [], 1):
    method = r["method"]; path = r["path_without_base"]
    # 排除登录（重复多次）
    if "/auth/login" in path:
        continue
    pd = r.get("post_data") or {}
    resp = r.get("response") or {}
    body = resp.get("body_sample") or {}
    biz = body.get("code") if isinstance(body, dict) else None
    msg = body.get("msg") if isinstance(body, dict) else ""
    captured.append({
        "no": f"CAP-{i:02d}",
        "source": "Playwright UI HAR 捕获（赵老板账号）",
        "use_case": {
            "/prod-api/idmp/project": "WR-01 新增项目 CREATE（POST /idmp/project）",
        }.get(path, "未归类（需人工）: "+path),
        "method": method,
        "url_path": path,
        "payload_fields_sorted": sorted(pd.keys()) if isinstance(pd, dict) else [],
        "payload_example": pd,
        "response_biz_code_example": biz,
        "response_msg_example": msg,
        "notes": "body 里字段 value 取法：type=hardware→对应中文硬件研发；status=draft；phase=concept；managerId=1→赵老板；projectCode=AUTO-NO-XXX；projectName=AUTO-HAR-XXX"
    })

# ----------- 2) 为 WR11 条生成候选接口（基于 payload 结构真实字段）-----------
wr11_plan = [
    # WR-01 CREATE
    {"no": "WR-01", "use_case": "新增项目（赵老板创建 draft + concept + type=software）",
     "action_hint": "POST /prod-api/idmp/project，真实 payload 结构 17 字段。断言：HTTP200 code200；再 GET /idmp/project/page 按 projectCode 过滤能搜到。",
     "candidates": [{"method": "POST", "url_path": "/prod-api/idmp/project"}],
     "payload_hint": "projectCode,projectName,type=software,status=draft,phase=concept,managerId=1 必填；其他可选填默认（budget=0,progress=0等）"},
    # WR-02 CREATE 必填校验缺失（缺 projectName 预期 400/500/非 200 biz code）
    {"no": "WR-02", "use_case": "新增项目必填校验（缺 projectName，预期后端非 200 或校验错误=前端已拦截则后端不报错）",
     "action_hint": "POST /prod-api/idmp/project 去掉 projectName。断言：HTTP200 但 code!=200（或返回 400）。",
     "candidates": [{"method": "POST", "url_path": "/prod-api/idmp/project"}],
     "payload_hint": "projectCode存在，projectName=null/缺"},
    # WR-03 CREATE 重复 projectCode
    {"no": "WR-03", "use_case": "新增项目重复项目编号（projectCode 冲突预期非 200 或被接受看业务）",
     "action_hint": "先用 WR-01 存 projectCode，再发第二条同 projectCode。断言：若系统判重=code!=200",
     "candidates": [{"method": "POST", "url_path": "/prod-api/idmp/project"}],
     "payload_hint": "同 WR-01，projectCode 重复"},
    # WR-04 UPDATE 改项目名/预算
    {"no": "WR-04", "use_case": "编辑项目（PUT /prod-api/idmp/project/{id} 改 projectName + budget）",
     "action_hint": "先用 WR-01 创建拿 id；PUT /prod-api/idmp/project/{id} 带完整 payload 或部分字段。断言 code=200 且 GET 详情 budget 等新值。",
     "candidates": [
         {"method": "PUT", "url_path": "/prod-api/idmp/project/{id}"},
         {"method": "POST", "url_path": "/prod-api/idmp/project/{id}"},
         {"method": "PUT", "url_path": "/prod-api/idmp/project"},
     ],
     "payload_hint": "同 CREATE 结构 + id={id}"},
    # WR-05 STATUS 提交审批 draft→pending
    {"no": "WR-05", "use_case": "提交审批（status draft→pending）",
     "action_hint": "WR-01 创建 draft 后；PUT /idmp/project/{id}（只改 status=pending） 或 POST /idmp/project/{id}/submit。断言 GET 详情 status=pending。",
     "candidates": [
         {"method": "PUT",  "url_path": "/prod-api/idmp/project/{id}"},
         {"method": "POST", "url_path": "/prod-api/idmp/project/{id}/submit"},
         {"method": "POST", "url_path": "/prod-api/idmp/project/submit"},
         {"method": "PUT",  "url_path": "/prod-api/idmp/project/{id}/submit"},
     ],
     "payload_hint": "{id, status: 'pending'} 或 带审批意见 {comment, projectId}"},
    # WR-06 STATUS 审批通过 pending→approved
    {"no": "WR-06", "use_case": "审批通过（status pending→approved）",
     "action_hint": "WR-05 完成 pending；PUT /idmp/project/{id}（status=approved） 或 POST /idmp/project/{id}/approve。",
     "candidates": [
         {"method": "PUT",  "url_path": "/prod-api/idmp/project/{id}"},
         {"method": "POST", "url_path": "/prod-api/idmp/project/{id}/approve"},
         {"method": "POST", "url_path": "/prod-api/idmp/project/approve"},
     ],
     "payload_hint": "{id, status:'approved'} 或 {id, approvalComment:'WR 自动化通过'}"},
    # WR-07 PHASE concept→plan
    {"no": "WR-07", "use_case": "阶段推进 concept→plan（需要 status=approved）",
     "action_hint": "WR-06 后 approved+concept；PUT /idmp/project/{id}（phase=plan） 或 POST /idmp/project/{id}/nextPhase。",
     "candidates": [
         {"method": "PUT",  "url_path": "/prod-api/idmp/project/{id}"},
         {"method": "POST", "url_path": "/prod-api/idmp/project/{id}/nextPhase"},
         {"method": "POST", "url_path": "/prod-api/idmp/project/{id}/advance"},
         {"method": "POST", "url_path": "/prod-api/idmp/project/phase"},
     ],
     "payload_hint": "{id, phase:'plan'} 或 {id, nextPhase:'plan'}"},
    # WR-08 PHASE plan→development
    {"no": "WR-08", "use_case": "阶段推进 plan→development",
     "action_hint": "WR-07 后 phase=plan → PUT {id} phase=development / nextPhase。",
     "candidates": [
         {"method": "PUT",  "url_path": "/prod-api/idmp/project/{id}"},
         {"method": "POST", "url_path": "/prod-api/idmp/project/{id}/nextPhase"},
     ],
     "payload_hint": "{id, phase:'development'}"},
    # WR-09 PHASE development→closed
    {"no": "WR-09", "use_case": "项目结项 development→closed",
     "action_hint": "WR-08 后 → PUT {id} phase=closed / POST {id}/close。",
     "candidates": [
         {"method": "PUT",  "url_path": "/prod-api/idmp/project/{id}"},
         {"method": "POST", "url_path": "/prod-api/idmp/project/{id}/close"},
         {"method": "POST", "url_path": "/prod-api/idmp/project/{id}/complete"},
         {"method": "POST", "url_path": "/prod-api/idmp/project/close"},
     ],
     "payload_hint": "{id, phase:'closed'} 或 {id, closeReason:'WR 自动化结项'}"},
    # WR-10 DELETE 软删除/归档
    {"no": "WR-10", "use_case": "项目软删除（WR-01 创建专用项目后删，避免脏数据）",
     "action_hint": "DELETE/POST /prod-api/idmp/project/{id}/softDelete 或 DELETE {id}。断言 GET page 搜索 projectName 应该已不在列表或标记为 deleted（看业务）。",
     "candidates": [
         {"method": "DELETE", "url_path": "/prod-api/idmp/project/{id}"},
         {"method": "POST",   "url_path": "/prod-api/idmp/project/{id}/softDelete"},
         {"method": "POST",   "url_path": "/prod-api/idmp/project/{id}/delete"},
         {"method": "POST",   "url_path": "/prod-api/idmp/project/{id}/recycle"},
         {"method": "POST",   "url_path": "/prod-api/idmp/project/{id}/archive"},
         {"method": "POST",   "url_path": "/prod-api/idmp/project/softDelete"},
     ],
     "payload_hint": "DELETE 无 body；POST 可 {id, reason:'WR 清理专用'}"},
    # WR-11 IDOR 赵经理不能改赵老板专属项目（权限越权写）
    {"no": "WR-11", "use_case": "IDOR 越权写：赵经理账号 PUT/DELETE 赵老板专属 closed 项目，预期 403/404/code!=200",
     "action_hint": "取赵老板专属 pid（probe 脚本里的越权目标 pid 或从老板 list 选一个 phase=closed 的）；用赵经理 mgr_authed_session PUT {id} name='HACKED' 或 DELETE；断言 HTTP 非 200 或 biz code != 200。再 GET 老板详情，验证名称未被改。",
     "candidates": [
         {"method": "PUT",  "url_path": "/prod-api/idmp/project/{id}"},
         {"method": "DELETE", "url_path": "/prod-api/idmp/project/{id}"},
         {"method": "POST", "url_path": "/prod-api/project/{id}"},
     ],
     "payload_hint": "PUT: {id, projectName:'HACKED-IDOR-WR11'}; DELETE:无 body."},
]

for item in wr11_plan:
    wr_candidates.append(item)

final = {
    "capture_time": time.strftime("%Y-%m-%d %H:%M:%S"),
    "captured_interfaces_count": len(captured),
    "captured_interfaces": captured,
    "wr11_plan_count": len(wr_candidates),
    "wr11_candidate_interfaces": wr_candidates,
    "probe_reference": {
        "success_create": len([1 for c in probe.get("create_candidates", []) if c.get("success")]),
        "success_update": len([1 for c in probe.get("update_candidates", []) if c.get("success")]),
        "success_status": len([1 for c in probe.get("status_flow_candidates", []) if c.get("success")]),
        "success_phase":  len([1 for c in probe.get("phase_flow_candidates", [])  if c.get("success")]),
        "note": "探测脚本未命中是因为候选路径未覆盖真实前缀；真实 CREATE=Playwright HAR 已捕获=POST /prod-api/idmp/project，其余 WR04~WR10 全部基于 PUT /prod-api/idmp/project/{id} 改写 status/phase 字段——这是 ElementUI 最常见的 update 模式，WR 脚本内部采用「多候选 fallback 探测直到 HTTP200+code200，然后固化首条成功路由」策略。",
    }
}

OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
OUT_FILE.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[OK] 写接口捕获清单 → {OUT_FILE}")
print(f"   - 已捕获真实接口 = {len(captured)} 条（均 Playwright HAR 抓包）")
print(f"   - WR11 候选接口 = {len(wr_candidates)} 条（基于真实 CREATE payload 结构 + 多候选 fallback 路由）")
