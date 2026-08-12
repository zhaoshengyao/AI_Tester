# -*- coding: utf-8 -*-
import json
from pathlib import Path
m = json.loads(Path(r"d:/AICode/TestHub/AITestDemo/projects/ipd/docs/analysis/zhaoboss-ui-write-captures/capture_manifest.json").read_text(encoding="utf-8"))
for s in m["step_logs"]:
    print("=" * 80)
    print("[Step %s] %s   ok=%s" % (s["step_id"], s["step_title"], s["ok"]))
    print("  URL: %s" % s["current_url"])
    if s.get("note"): print("  Note: %.250s" % s["note"])
    btns = s.get("visible_buttons_links_top60") or []
    print("  可见按钮/链接前 30：")
    for b in btns[:30]:
        t = b.get("text", "") or ""
        sel = b.get("selector", "") or ""
        print("    - [%.40s]  selector=%.120s" % (t, sel))
