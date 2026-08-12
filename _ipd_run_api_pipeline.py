# -*- coding: utf-8 -*-
"""Runner: API smoke → readonly → full → WR → WR15 → 报告.

Direct runner without PowerShell wrapper.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ROOT = 脚本所在目录的父目录（跨平台：Windows d:\...\AITestDemo / Linux /home/.../AutoTestHub）
ROOT = Path(__file__).resolve().parent
PROJ = "projects/ipd"
TEST_RUNS_DIR = ROOT / PROJ / "docs" / "test-runs"
TEST_RUNS_DIR.mkdir(parents=True, exist_ok=True)

# 1. 生成 RUN_ID：优先读 IPD_RUN_ID 环境变量，未设置则自动生成时间戳
RUN_ID = os.environ.get("IPD_RUN_ID") or datetime.now().strftime("%Y%m%d-%H%M%S")
print(f"[INFO] RUN_ID = {RUN_ID}  (source = {'env IPD_RUN_ID' if os.environ.get('IPD_RUN_ID') else 'auto-timestamp'})")
RUN_DIR = TEST_RUNS_DIR / RUN_ID
RAW = RUN_DIR / "raw"
RAW_API = RAW / "api-results"
REPORTS = RUN_DIR / "reports"
DEFECTS = RUN_DIR / "defects"
STAGE = RUN_DIR / "stage-status"
for d in (RAW, RAW_API, REPORTS, DEFECTS, STAGE, RUN_DIR / "raw" / "run-logs"):
    d.mkdir(parents=True, exist_ok=True)

# 2. 写 .run_id 标记（兼容旧脚本 fallback 读取）
(RUN_DIR / ".run_id").write_text(RUN_ID, encoding="utf-8")
# 下游报告脚本（_gen_api_report.py / _gen_ui_perf_sec_mat_reports.py）通过 IPD_RUN_ID 环境变量获取批次号，
# 不再需要物理改写源文件中的 TS 硬编码。

# 3. 服务预检：登录+核心只读
PY = sys.executable
ENV = os.environ.copy()
ENV["PYTHONPATH"] = str(ROOT)
ENV["IPD_RUN_ID"] = RUN_ID  # 下游报告脚本通过此变量获取批次号
ENV.setdefault("TEST_SYSTEM_ID", "ipd")
# 显式加载 projects/ipd/.env
env_file = ROOT / "projects" / "ipd" / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        m = re.match(r'^([A-Z_]+)=(.*)$', line.strip())
        if not m:
            continue
        k, v = m.group(1), m.group(2)
        if v.startswith('"') and v.endswith('"'):
            v = v[1:-1]
        elif v.startswith("'") and v.endswith("'"):
            v = v[1:-1]
        ENV.setdefault(k, v)

# 预检脚本：直接用 python 跑 conftest 的登录 fixture 检测
# 不再 write_text 覆盖（避免硬编码路径），直接使用已有的 _ipd_preflight.py
preflight = ROOT / "_ipd_preflight.py"
for k in ("API_USERNAME", "API_PASSWORD"):
    if k not in ENV:
        ENV[k] = ENV.get("TEST_" + k.replace("API_", "")) or ""

print("\n[1/6] 服务预检（登录+核心只读）")
sys.stdout.flush()
cp = subprocess.run([PY, str(preflight)], cwd=str(ROOT), env=ENV, capture_output=True, text=True, timeout=90)
with open(RUN_DIR / "raw" / "run-logs" / "00-preflight.log", "w", encoding="utf-8") as f:
    f.write(cp.stdout)
    f.write("\n==== STDERR ====\n")
    f.write(cp.stderr)
print(cp.stdout)
if cp.returncode != 0:
    print(cp.stderr, file=sys.stderr)
    print("[FAIL] 服务预检失败，停止后续")
    sys.exit(1)

# 4. pytest 分层执行
def run_pytest(args, json_out, stdout_out, tag, timeout=600):
    print(f"\n[{tag}] pytest {' '.join(args)}")
    sys.stdout.flush()
    cmd = [PY, "-m", "pytest"] + args + [
        "--no-header", "-v", "-s",  # -s 不捕获 stdout，保证 print(缺陷) 输出进入 stdout
    ]
    # 不依赖 pytest-json-report，把 console 输出保存下来，再用自定义解析
    cp = subprocess.run(cmd, cwd=str(ROOT), env=ENV, capture_output=True, text=True, timeout=timeout)
    stdout_all = cp.stdout + "\n===== STDERR =====\n" + cp.stderr
    (RAW_API / stdout_out).write_text(stdout_all, encoding="utf-8")
    print(cp.stdout[-3500:] if len(cp.stdout) > 3500 else cp.stdout)
    # 解析 summary 生成兼容 JSON（最小结构：{tests:[{nodeid,outcome}], summary:{passed,failed,...}}）
    tests = []
    summary = {"passed": 0, "failed": 0, "skipped": 0, "xfailed": 0, "xpassed": 0, "error": 0, "total": 0, "collected": 0}
    collected_re = re.search(r"collected\s+(\d+)\s+item", stdout_all)
    if collected_re:
        summary["collected"] = int(collected_re.group(1))
    # 多模式解析：
    # 兼容 pytest -v + -s 的输出（print 会打断 nodeid<ws>PASSED 一行）
    outcome_words = r"(PASSED|FAILED|SKIPPED|XFAIL|XPASS|ERROR)"
    # A) 同行：nodeid + outcome，允许尾部 [progress]
    pattern_test_and_outcome = re.compile(
        r"(tests/api/ipd/test_\S+\.py::\S+?)\s+" + outcome_words + r"(?:\s+\[.*?\])?\s*$"
    )
    # B) 跨行：行首 = nodeid 行（行尾可能接 outcome 也可能接 print/defect 文本）
    node_line_start = re.compile(r"^(tests/api/ipd/test_\S+\.py::\S+?)(?:\s+|$)")
    outcome_only = re.compile(r"^" + outcome_words + r"(?:\s+\[.*?\])?\s*$")
    last_node_only = None
    def _add(node, out_raw):
        outcome = out_raw.lower()
        if outcome == "xfail": outcome = "xfailed"
        elif outcome == "xpass": outcome = "xpassed"
        tests.append({"nodeid": node, "outcome": outcome})
        if outcome in summary: summary[outcome] += 1
    for line in cp.stdout.splitlines():
        line = line.rstrip()
        if not line:
            continue
        m1 = pattern_test_and_outcome.search(line)
        if m1:
            _add(m1.group(1), m1.group(2))
            last_node_only = None
            continue
        m2 = node_line_start.match(line)
        if m2:
            # 行首是 nodeid：作为待配对
            last_node_only = m2.group(1)
            # 同时兼容：这一行本身末尾有 outcome + [progress]
            m1b = re.search(
                r"\s+" + outcome_words + r"(?:\s+\[.*?\])?\s*$", line
            )
            if m1b:
                _add(last_node_only, m1b.group(1))
                last_node_only = None
            continue
        m3 = outcome_only.match(line)
        if m3 and last_node_only:
            _add(last_node_only, m3.group(1))
            last_node_only = None
            continue
        # 其他行（INFO / 缺陷打印）：保留 last_node_only，不重置


    # 兜底：summary 从 "X passed, Y failed..." 中拿最终总数（跨行解析不全时补充）
    final_m = re.search(r"(\d+)\s+passed", cp.stdout)
    if final_m:
        summary["passed"] = max(summary["passed"], int(final_m.group(1)))
    for kw, key in [("failed", "failed"), ("skipped", "skipped"), ("error", "error"),
                    ("xfailed", "xfailed"), ("xpassed", "xpassed")]:
        fm = re.search(r"(\d+)\s+"+kw, cp.stdout)
        if fm:
            summary[key] = max(summary[key], int(fm.group(1)))
    summary["total"] = sum(summary.get(k,0) for k in ["passed","failed","skipped","xfailed","xpassed","error"])
    out_json = {
        "created": time.time(),
        "duration": 0,
        "exitcode": cp.returncode,
        "root": str(ROOT),
        "environment": {},
        "summary": summary,
        "tests": tests,
    }
    (RAW_API / json_out).write_text(json.dumps(out_json, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{tag}] exitcode={cp.returncode} collected={summary['collected']} total={summary['total']} passed={summary['passed']} failed={summary['failed']} skipped={summary['skipped']}")
    return cp.returncode, out_json

# API smoke: test_auth_login (登录+登出+token校验)
rc_smoke, j_smoke = run_pytest(
    ["tests/api/ipd/test_auth_login.py"],
    "pytest-smoke.json", "pytest-smoke-stdout.txt", "2/6 API smoke", timeout=300,
)

# readonly: test_user.py + test_readonly_boundary_filters.py + test_project_risk_wf_consistency.py + test_project_stage_semi_auto.py（semi-auto 其实不写真实数据）
rc_ro, j_ro = run_pytest(
    ["tests/api/ipd/test_user.py", "tests/api/ipd/test_readonly_boundary_filters.py",
     "tests/api/ipd/test_project_risk_wf_consistency.py", "tests/api/ipd/test_project_stage_semi_auto.py"],
    "pytest-readonly.json", "pytest-readonly-stdout.txt", "3/6 API readonly+semi-auto", timeout=600,
)

# full: 加上 test_wr_11_cases.py（不包含 WR15，因为 WR15 脚本单独跑）
rc_full, j_full = run_pytest(
    ["tests/api/ipd/test_auth_login.py", "tests/api/ipd/test_user.py",
     "tests/api/ipd/test_readonly_boundary_filters.py", "tests/api/ipd/test_project_risk_wf_consistency.py",
     "tests/api/ipd/test_project_stage_semi_auto.py", "tests/api/ipd/test_wr_11_cases.py"],
    "pytest-full-api.json", "pytest-full-api-stdout.txt", "4/6 API full (含 WR1~11)", timeout=1200,
)

# 5. WR15（预算校验 + 负责人必填 + …）：走 _run_wr15_cases.py
print("\n[5/6] WR15 用例执行（_run_wr15_cases.py）")
sys.stdout.flush()
rc_wr15 = 0
wr15_stdout_path = RAW_API / "wr15-stdout.txt"
if (ROOT / "_run_wr15_cases.py").exists():
    cp = subprocess.run([PY, str(ROOT / "_run_wr15_cases.py")], cwd=str(ROOT), env=ENV, capture_output=True, text=True, timeout=1200)
    wr15_stdout_path.write_text(cp.stdout + "\n===== STDERR =====\n" + cp.stderr, encoding="utf-8")
    print(cp.stdout[-3000:] if len(cp.stdout) > 3000 else cp.stdout)
    rc_wr15 = cp.returncode
    print(f"[WR15] exitcode={rc_wr15}")
else:
    wr15_stdout_path.write_text("[未执行] _run_wr15_cases.py 不存在\n", encoding="utf-8")
    rc_wr15 = 0

# 6. 生成 API 报告 & 缺陷清单（调用 _gen_api_report.py）
print("\n[6/6] 生成 API 专项报告 + 缺陷清单")
sys.stdout.flush()
cp = subprocess.run([PY, str(ROOT / "_gen_api_report.py")], cwd=str(ROOT), env=ENV, capture_output=True, text=True, timeout=180)
log_path = RUN_DIR / "raw" / "run-logs" / "06-gen-api-report.log"
log_path.write_text(cp.stdout + "\n===== STDERR =====\n" + cp.stderr, encoding="utf-8")
print(cp.stdout[-2000:] if len(cp.stdout) > 2000 else cp.stdout)
if cp.stderr.strip():
    print("---STDERR---")
    print(cp.stderr[-2000:])

print(f"\n===== DONE RUN_ID={RUN_ID} =====")
print(f"RUN_DIR = {RUN_DIR}")
print(f"SMOKE rc={rc_smoke}   READONLY rc={rc_ro}   FULL rc={rc_full}   WR15 rc={rc_wr15}")
# 打印报告文件
for f in sorted(REPORTS.glob("*.md")):
    print(f"  REPORT: {f.relative_to(ROOT)}")
for f in sorted(DEFECTS.glob("*.md")):
    print(f"  DEFECT: {f.relative_to(ROOT)}")
(RUN_DIR / ".api_run_result.json").write_text(json.dumps({
    "RUN_ID": RUN_ID,
    "rc_smoke": rc_smoke, "smoke": j_smoke.get("summary"),
    "rc_readonly": rc_ro, "readonly": j_ro.get("summary"),
    "rc_full": rc_full, "full": j_full.get("summary"),
    "rc_wr15": rc_wr15,
}, ensure_ascii=False, indent=2), encoding="utf-8")
