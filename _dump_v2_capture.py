# -*- coding: utf-8 -*-
import json
from pathlib import Path
m = json.loads(Path(r"d:/AICode/TestHub/AITestDemo/projects/ipd/docs/analysis/zhaoboss-ui-write-captures/capture_manifest.json").read_text(encoding="utf-8"))
print("=" * 80)
print("非 GET 请求清单：")
for r in m["captured_non_get_requests"]:
    method = r["method"]
    path = r["path_without_base"]
    pd = r.get("post_data")
    resp = r.get("response") or {}
    st = resp.get("status")
    body = resp.get("body_sample") or {}
    biz = body.get("code") if isinstance(body, dict) else None
    msg = (body.get("msg") or "") if isinstance(body, dict) else ""
    data = (body.get("data") or None) if isinstance(body, dict) else None
    print(f"  {method:6s} {path[:130]} HTTP={st} code={biz} msg={str(msg)[:80]}")
    if isinstance(data, dict) and data: print("    response.data.keys=", sorted(data.keys()))
    if isinstance(pd, dict): print("    post_data.keys=", sorted(pd.keys()))
print("=" * 80)
print("\n步骤概览：")
for s in m["step_logs"]:
    print("[Step %s] ok=%s  title=%s" % (s["step_id"], "✅" if s["ok"] else "❌", s["step_title"]))
    if s.get("note"):
        print("  Note: %.400s" % s["note"])
# 详细 01 02 03 前 3 步的全部按钮
for s in m["step_logs"][1:4]:
    print("\n" + "=" * 100)
    print("[Step %s] %s   ok=%s" % (s["step_id"], s["step_title"], "✅" if s["ok"] else "❌"))
    print("  URL:", s["current_url"])
    btns = s.get("visible_buttons_links_top60") or []
    print("  按钮前 60：")
    for i, b in enumerate(btns[:60], 1):
        t = (b.get("text") or "").replace("\n", " ")
        print("  %2d. [%-35s] %s" % (i, t[:35], (b.get("selector") or "")[:120]))
