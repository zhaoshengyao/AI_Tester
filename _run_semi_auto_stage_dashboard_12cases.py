# -*- coding: utf-8 -*-
"""Step E-2 runner：执行 12 条 semi-auto 用例（不依赖 pytest-json-report 插件）。
原生 python -m pytest -v -s 输出解析后，生成和 _gen_api_report.py 兼容的 mini JSON。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(r"d:\AICode\TestHub\AITestDemo")
TARGET = "tests/api/ipd/test_project_stage_semi_auto.py"
TS = "20260811-122314"
OUT_DIR = REPO / "projects" / "ipd" / "docs" / "test-runs" / TS / "raw" / "api-results"
OUT_DIR.mkdir(parents=True, exist_ok=True)
JSON_OUT = OUT_DIR / "pytest-semi-auto-stage-dashboard.json"
STDOUT_OUT = OUT_DIR / "pytest-semi-auto-stage-dashboard-stdout.txt"

env = os.environ.copy()
env["PYTHONPATH"] = str(REPO) + os.pathsep + str(REPO / "tests" / "api" / "ipd")

cmd = [
    sys.executable, "-m", "pytest",
    str(REPO / TARGET),
    "-v", "-s", "--tb=short",
    "--no-header",
    "-p", "no:cacheprovider",  # 避免 __pycache__ 写（Sandbox 友好）
]
print(f"[RUN] {' '.join(cmd)}")
t0 = time.time()
cp = subprocess.run(cmd, cwd=str(REPO), env=env, capture_output=True, text=True)
duration = round(time.time() - t0, 3)
stdout_all = cp.stdout
if cp.stderr:
    stdout_all += "\n================ STDERR ================\n" + cp.stderr
print(f"[DONE] exitcode={cp.returncode}; duration={duration}s; stdout_chars={len(stdout_all)}")

# 写原始 stdout
STDOUT_OUT.write_text(stdout_all, encoding="utf-8")

# 解析每个测试项 outcome：用逐行状态机（简单可靠）
# 状态：遇到 nodeid 就记录 last_nodeid；遇到 outcome 关键字（同行或单独一行）则绑定到 last_nodeid
lines = stdout_all.splitlines()
outcomes = {"PASSED","FAILED","SKIPPED","ERROR","XFAIL","XPASS"}
nodeid_prefix = "tests/api/ipd/test_project_stage_semi_auto.py::"
nodeid_re_inline = re.compile(r"(tests/api/ipd/test_project_stage_semi_auto\.py::\S+)(?:\s+(PASSED|FAILED|SKIPPED|ERROR|XFAIL|XPASS))?")
last_nodeid: str | None = None
tests_dict: dict[str, dict] = {}
all_nodeids: list[str] = []

for line in lines:
    s = line.strip()
    # 1) 找 nodeid（可能带 outcome 可能不带）
    m = nodeid_re_inline.search(s)
    if m:
        nid = m.group(1)
        # nodeid 可能被后面的 outcome 词误吃，nid 只保留 outcome 词前
        for w in outcomes:
            tail = "::" + w  # 避免把 outcome 词吃掉
            pass
        if nid and nid not in all_nodeids:
            all_nodeids.append(nid)
        last_nodeid = nid
        # 同行 outcome？
        out_word = m.group(2)
        if out_word and last_nodeid not in tests_dict:
            tests_dict[last_nodeid] = {"outcome": out_word.lower()}
        continue
    # 2) 只有 outcome 的行（nodeid 在前面某行 + print INFO 打断）
    if s in outcomes and last_nodeid:
        if last_nodeid not in tests_dict:
            tests_dict[last_nodeid] = {"outcome": s.lower()}
    # 3) `... outcome` 的行（nodeid 和 outcome 之间中间有大量空格/换行被上面的 1) 吃掉了的情况）
    # 例如最后 3 行 "test_cons_A7_boss_risk_projects_ge_manager [INFO ...] \nPASSED" —— 已由 2) 覆盖

nodeids = all_nodeids
# 兜底：pytest 最终 "X passed in Ys"
m_final = re.search(r"(?P<passed>\d+)\s+passed\s+in\s+[\d.]+s", stdout_all)
m_failed = re.search(r"(?P<failed>\d+)\s+failed\b", stdout_all)
m_skipped = re.search(r"(?P<skipped>\d+)\s+skipped\b", stdout_all)
total_pytest = len(nodeids) or (
    (int(m_final.group("passed")) if m_final else 0)
    + (int(m_failed.group("failed")) if m_failed else 0)
    + (int(m_skipped.group("skipped")) if m_skipped else 0)
)

# 最终 tests 列表：优先解析出来的 dict + 缺失的按 nodeids 补齐
tests = []
passed = 0
for nid in nodeids:
    if nid in tests_dict:
        out = tests_dict[nid]["outcome"]
        outcome = {"passed":"passed","failed":"failed","skipped":"skipped","error":"error","xfail":"xfailed","xpass":"xpassed"}.get(out,out)
    else:
        outcome = "unknown"
    tests.append({"nodeid": nid, "outcome": outcome, "duration": None})
    if outcome == "passed": passed += 1

# 兜底：如果解析出来的 passed 数和 "X passed in Ys" 对不上，补 unknown
reported_passed = int(m_final.group("passed")) if m_final else passed
if passed < reported_passed and any(t["outcome"] == "unknown" for t in tests):
    need = reported_passed - passed
    for t in tests:
        if need <= 0: break
        if t["outcome"] == "unknown":
            t["outcome"] = "passed"; need -= 1; passed += 1
total = len(tests) or total_pytest or reported_passed
failed_total = sum(1 for t in tests if t["outcome"] in ("failed", "error"))
skipped_total = sum(1 for t in tests if t["outcome"] == "skipped")
summary = {
    "passed": passed, "total": total,
    "failed": failed_total, "skipped": skipped_total,
    "collected": total or None,
    "exitcode_raw": cp.returncode,
}
print(f"[PARSED summary] {summary}")

# 写 JSON（和 pytest-json-report 同 key，保持后续报告兼容）
out = {
    "created": time.time(),
    "duration": duration,
    "exitcode": cp.returncode,
    "root": str(REPO),
    "environment": {"python": sys.version, "platform": sys.platform},
    "summary": summary,
    "collectors": [],
    "tests": tests,
}
JSON_OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"✅ 写 stdout → {STDOUT_OUT}（{STDOUT_OUT.stat().st_size/1024:.1f} KB）")
print(f"✅ 写 JSON   → {JSON_OUT}（大小 {JSON_OUT.stat().st_size/1024:.1f} KB）")

# 结尾输出 passed/failed 概览（方便 log 末尾一眼看）
print("\n========= 12 条 semi-auto 结果 ==========")
for t in tests:
    emoji = {"passed": "✅", "failed": "❌", "skipped": "⏭"}.get(t["outcome"], "?")
    print(f"{emoji} {t['outcome'].upper():<7} {t['nodeid'].split('::',1)[1]}")
if cp.returncode != 0 and failed == 0 and total > 0:
    print(f"[INFO] pytest exitcode={cp.returncode} 但断言 0 failed；可能是 conftest 导入错误或收集阶段错误（见 stdout）。")
