# -*- coding: utf-8 -*-
import json
from pathlib import Path
m = json.loads(Path(r"d:/AICode/TestHub/AITestDemo/projects/ipd/docs/analysis/zhaoboss-ui-write-captures/capture_manifest.json").read_text(encoding="utf-8"))
print("=" * 120)
print("步骤 01 02 03 Note：")
for s in m["step_logs"][1:4]:
    print("[Step %s] ok=%s" % (s["step_id"], "✅" if s["ok"] else "❌"))
    print("  Title: %s" % s["step_title"])
    print("  Note:  %s" % s["note"])
print("=" * 120)
print("\n所有 captured_non_get_requests（全部打印，无 URL 过滤）：")
for i, r in enumerate(m["captured_non_get_requests"], 1):
    method = r["method"]; path = r["path_without_base"]
    print(f"  {i:2d}. {method:6s} {path[:180]}")
    resp = r.get("response") or {}
    st = resp.get("status")
    body = resp.get("body_sample") or {}
    biz = body.get("code") if isinstance(body, dict) else None
    msg = (body.get("msg") or "") if isinstance(body, dict) else ""
    print("       HTTP=%s code=%s msg=%s" % (st, biz, str(msg)[:120]))
