# -*- coding: utf-8 -*-
"""WR11 条脚本 runner（不依赖 pytest-json-report 插件）：
执行 tests/api/ipd/test_wr_11_cases.py，解析 stdout，输出兼容 JSON。
"""
from __future__ import annotations
import json, os, re, subprocess, sys, time
from pathlib import Path

REPO = Path(r"d:\AICode\TestHub\AITestDemo")
TARGET = "tests/api/ipd/test_wr_11_cases.py"
TS = "20260811-122314"
OUT_DIR = REPO / "projects" / "ipd" / "docs" / "test-runs" / TS / "raw" / "api-results"
OUT_DIR.mkdir(parents=True, exist_ok=True)
JSON_OUT = OUT_DIR / "pytest-wr11.json"
STDOUT_OUT = OUT_DIR / "pytest-wr11-stdout.txt"

env = os.environ.copy()
env["PYTHONPATH"] = str(REPO) + os.pathsep + str(REPO / "tests" / "api" / "ipd")

cmd = [
    sys.executable, "-m", "pytest",
    str(REPO / TARGET),
    "-v", "-s", "--tb=short",
    "--no-header",
    "-p", "no:cacheprovider",
]
print(f"[RUN] {' '.join(cmd)}")
t0 = time.time()
cp = subprocess.run(cmd, cwd=str(REPO), env=env, capture_output=True, text=True)
duration = round(time.time() - t0, 3)
stdout_all = cp.stdout
if cp.stderr:
    stdout_all += "\n================ STDERR ================\n" + cp.stderr
print(f"[DONE] exitcode={cp.returncode}; duration={duration}s; stdout_chars={len(stdout_all)}")
STDOUT_OUT.write_text(stdout_all, encoding="utf-8")

# 解析 nodeid + outcome
lines = stdout_all.splitlines()
NODE_FILE = "tests/api/ipd/test_wr_11_cases.py"
nodeid_re_inline = re.compile(r"(" + re.escape(NODE_FILE) + r"::\S+)(?:\s+(PASSED|FAILED|SKIPPED|ERROR|XFAIL|XPASS))?")
outcomes = {"PASSED","FAILED","SKIPPED","ERROR","XFAIL","XPASS"}
all_nodeids: list[str] = []
tests_dict: dict[str, dict] = {}
last_nodeid = None

for line in lines:
    s = line.strip()
    m = nodeid_re_inline.search(s)
    if m:
        nid = m.group(1)
        if nid and nid not in all_nodeids: all_nodeids.append(nid)
        last_nodeid = nid
        out_word = m.group(2)
        if out_word and last_nodeid and last_nodeid not in tests_dict:
            tests_dict[last_nodeid] = {"outcome": out_word.lower()}
        continue
    if s in outcomes and last_nodeid and last_nodeid not in tests_dict:
        tests_dict[last_nodeid] = {"outcome": s.lower()}

# 汇总数字
m_final = re.search(r"(?P<passed>\d+)\s+passed\s+in\s+[\d.]+s", stdout_all)
m_failed = re.search(r"(?P<failed>\d+)\s+failed\b", stdout_all)
m_skipped = re.search(r"(?P<skipped>\d+)\s+skipped\b", stdout_all)
total_pytest = len(all_nodeids) or (
    (int(m_final.group("passed")) if m_final else 0)
    + (int(m_failed.group("failed")) if m_failed else 0)
    + (int(m_skipped.group("skipped")) if m_skipped else 0)
)

# 构建 tests 列表（和 pytest-json-report 格式兼容）
OUTCOME_MAP = {"passed":"passed","failed":"failed","skipped":"skipped","error":"error","xfail":"xfailed","xpass":"xpassed"}
tests = []; passed_n = 0; failed_n = 0; skipped_n = 0; error_n = 0; unknown_n = 0
for nid in all_nodeids:
    info = tests_dict.get(nid, {})
    out = info.get("outcome", "unknown")
    mapped = OUTCOME_MAP.get(out, out)
    if mapped == "passed": passed_n += 1
    elif mapped == "failed": failed_n += 1
    elif mapped == "skipped": skipped_n += 1
    elif mapped == "error": error_n += 1
    else: unknown_n += 1
    tests.append({"nodeid": nid, "outcome": mapped, "duration": None,
                  "keywords": nid.split("::")[-1], "longrepr": None})

summary = {
    "total": len(all_nodeids),
    "passed": passed_n, "failed": failed_n, "skipped": skipped_n,
    "error": error_n, "xpassed": 0, "xfailed": 0, "unknown": unknown_n,
    "duration": duration,
    "exit_code": cp.returncode,
    "stdout_char_count": len(stdout_all),
}
result = {
    "created": time.strftime("%Y-%m-%d %H:%M:%S"),
    "duration": duration,
    "exitcode": cp.returncode,
    "root": str(REPO),
    "environment": {"WR11": "true"},
    "summary": summary,
    "tests": tests,
    "tests_to_triage": failed_n + error_n,
}
JSON_OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[OUT] {JSON_OUT}")
print(f"[SUMMARY] total={summary['total']} passed={passed_n} failed={failed_n} skipped={skipped_n} error={error_n} unknown={unknown_n} duration={duration}s")
# 打印 stdout 末尾（show print 的缺陷信息）
tail = "\n".join(stdout_all.splitlines()[-60:])
print("\n----- STDOUT TAIL (last 60 lines) -----")
print(tail)
