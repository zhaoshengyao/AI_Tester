# -*- coding: utf-8 -*-
"""Step 2 of IPD pipeline: Build RUN_ID dirs, run pytest smoke/readonly/full, generate compatible JSON.
Designed to be idempotent-safe; runs pytest then parses console output.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJ = "projects/ipd"
TEST_RUNS = ROOT / PROJ / "docs" / "test-runs"
TEST_RUNS.mkdir(parents=True, exist_ok=True)
RUN_ID = datetime.now().strftime("%Y%m%d-%H%M%S")
# If .run_id latest already exists, re-use it (chain workflow)
existing = sorted([p.name for p in TEST_RUNS.iterdir() if p.is_dir() and re.match(r'^\d{8}-\d{6}$', p.name)], reverse=True)
if existing:
    RUN_ID = existing[0]
print(f"RUN_ID = {RUN_ID}")
RUN_DIR = TEST_RUNS / RUN_ID
RAW_API = RUN_DIR / "raw" / "api-results"
REPORTS = RUN_DIR / "reports"
DEFECTS = RUN_DIR / "defects"
STAGE = RUN_DIR / "stage-status"
for d in (RAW_API, REPORTS, DEFECTS, STAGE, RUN_DIR / "raw" / "run-logs"):
    d.mkdir(parents=True, exist_ok=True)
(RUN_DIR / ".run_id").write_text(RUN_ID, encoding="utf-8")

# Update TS variables in all generator scripts to match RUN_ID
TARGETS = [
    "_gen_api_report.py",
    "_gen_ui_perf_sec_reports_v2.py",
    "_gen_ui_perf_sec_reports.py",
    "_gen_stage_dashboard_report.py",
    "_gen_wr11_v2_final_report.py",
    "_gen_wr15_v15_reports.py",
]
for fname in TARGETS:
    p = ROOT / fname
    if not p.exists():
        continue
    txt = p.read_text(encoding="utf-8")
    new_txt = re.sub(r'TS\s*=\s*"[^"]+"', f'TS = "{RUN_ID}"', txt, count=1)
    if new_txt != txt:
        p.write_text(new_txt, encoding="utf-8")
        print(f"[TS] {fname} -> TS = {RUN_ID}")

# Build env
ENV = os.environ.copy()
ENV["PYTHONPATH"] = str(ROOT)
ENV.setdefault("TEST_SYSTEM_ID", "ipd")
DOTENV = ROOT / "projects" / "ipd" / ".env"
if DOTENV.exists():
    for line in DOTENV.read_text(encoding="utf-8").splitlines():
        m = re.match(r'^([A-Z_]+)=(.*)$', line.strip())
        if not m:
            continue
        k, v = m.group(1), m.group(2).strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
            v = v[1:-1]
        ENV.setdefault(k, v)

PY = sys.executable

def run_pytest(args, json_name, txt_name, tag, timeout=900):
    print(f"\n=== [{tag}] pytest {' '.join(args)} ===")
    cmd = [PY, "-m", "pytest", "--no-header", "-v", "-s", "--capture=no", "-p", "no:cacheprovider"] + args
    cp = subprocess.run(cmd, cwd=str(ROOT), env=ENV, capture_output=True, text=True, timeout=timeout)
    combined = cp.stdout + "\n===== STDERR =====\n" + cp.stderr
    (RAW_API / txt_name).write_text(combined, encoding="utf-8")
    # Parse
    tests = []
    summary = {"collected": 0, "passed": 0, "failed": 0, "skipped": 0, "xfailed": 0, "xpassed": 0, "error": 0, "deselected": 0, "warnings": 0, "total": 0}
    m_col = re.search(r"collected\s+(\d+)\s+items?", combined)
    if m_col:
        summary["collected"] = int(m_col.group(1))
    m_des = re.search(r"(\d+)\s+deselected", combined)
    if m_des:
        summary["deselected"] = int(m_des.group(1))
    m_warn = re.search(r"(\d+)\s+warning", combined)
    if m_warn:
        summary["warnings"] = int(m_warn.group(1))
    for line in combined.splitlines():
        m = re.search(r"(tests/api/ipd/test_\w+\.py::[\w:\[\]\-.,=+]+)\s+(PASSED|FAILED|SKIPPED|XFAIL|XPASS|ERROR)", line)
        if not m:
            continue
        node, out = m.group(1), m.group(2).lower()
        if out == "xfail":
            out = "xfailed"
        elif out == "xpass":
            out = "xpassed"
        tests.append({"nodeid": node, "outcome": out})
        summary[out] = summary.get(out, 0) + 1
    summary["total"] = len(tests)
    out_obj = {
        "created": time.time(),
        "exitcode": cp.returncode,
        "root": str(ROOT),
        "summary": summary,
        "tests": tests,
    }
    (RAW_API / json_name).write_text(json.dumps(out_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[SUMMARY {tag}] exitcode={cp.returncode} collected={summary['collected']} total={summary['total']} passed={summary['passed']} failed={summary['failed']} skipped={summary['skipped']} xfailed={summary['xfailed']}")
    tail = combined[-3500:]
    print(tail)
    return cp.returncode, out_obj

# (1) Smoke = only auth
rc_smoke, sm = run_pytest(
    ["tests/api/ipd/test_auth_login.py"],
    "pytest-smoke.json", "pytest-smoke-stdout.txt", "1/4 SMOKE (auth only)", 300,
)

# (2) Readonly regression + semi-auto (all except wr11 and auth)
rc_ro, ro = run_pytest(
    [
        "tests/api/ipd/test_user.py",
        "tests/api/ipd/test_readonly_boundary_filters.py",
        "tests/api/ipd/test_project_risk_wf_consistency.py",
        "tests/api/ipd/test_project_stage_semi_auto.py",
    ],
    "pytest-readonly.json", "pytest-readonly-stdout.txt", "2/4 READONLY+SEMI-AUTO", 900,
)

# (3) Full = all, including WR1~11 (WR1~11 are in test_wr_11_cases.py per earlier summary)
rc_full, full = run_pytest(
    [
        "tests/api/ipd/test_auth_login.py",
        "tests/api/ipd/test_user.py",
        "tests/api/ipd/test_readonly_boundary_filters.py",
        "tests/api/ipd/test_project_risk_wf_consistency.py",
        "tests/api/ipd/test_project_stage_semi_auto.py",
        "tests/api/ipd/test_wr_11_cases.py",
    ],
    "pytest-full-api.json", "pytest-full-api-stdout.txt", "3/4 FULL API (含 WR1~11)", 1800,
)

# (4) WR15 via _run_wr15_cases.py
rc_wr15 = 0
print("\n=== [4/4] WR15 执行：_run_wr15_cases.py ===")
wr15_script = ROOT / "_run_wr15_cases.py"
wr15_stdout = RAW_API / "wr15-stdout.txt"
if wr15_script.exists():
    cp = subprocess.run([PY, str(wr15_script)], cwd=str(ROOT), env=ENV, capture_output=True, text=True, timeout=1500)
    wr15_stdout.write_text(cp.stdout + "\n===== STDERR =====\n" + cp.stderr, encoding="utf-8")
    tail = cp.stdout[-3500:]
    print(tail)
    if cp.stderr.strip():
        print("----- STDERR tail -----")
        print(cp.stderr[-1500:])
    rc_wr15 = cp.returncode
    print(f"[WR15] exitcode={rc_wr15}")
else:
    wr15_stdout.write_text("[未执行] _run_wr15_cases.py 不存在\n", encoding="utf-8")
    print("[WR15] 脚本不存在，跳过")

# Persist overall result
res = {
    "RUN_ID": RUN_ID,
    "rc_smoke": rc_smoke, "smoke_summary": sm.get("summary"),
    "rc_readonly": rc_ro, "readonly_summary": ro.get("summary"),
    "rc_full": rc_full, "full_summary": full.get("summary"),
    "rc_wr15": rc_wr15,
}
(RUN_DIR / ".api_run_result.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
(RUN_DIR / "raw" / "run-logs" / "01-pytest-pipeline.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n===== DONE RUN_ID={RUN_ID} =====")
print(f"  SMOKE   exit={rc_smoke}  P/F/S/X={(sm['summary']['passed'], sm['summary']['failed'], sm['summary']['skipped'], sm['summary']['xfailed'])}")
print(f"  READONLY exit={rc_ro}  P/F/S/X={(ro['summary']['passed'], ro['summary']['failed'], ro['summary']['skipped'], ro['summary']['xfailed'])}")
print(f"  FULL    exit={rc_full} P/F/S/X={(full['summary']['passed'], full['summary']['failed'], full['summary']['skipped'], full['summary']['xfailed'])}")
print(f"  WR15    exit={rc_wr15}")
print(f"RUN_DIR = {RUN_DIR}")
