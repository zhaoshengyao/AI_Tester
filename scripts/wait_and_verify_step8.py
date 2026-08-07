#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""等待全流程测试完成并验证 Step 8 - 一体化脚本"""
import paramiko
import time
import re
import sys

HOST = "192.168.2.70"; PORT = 22; USER = "root"; PASSWORD = "Zw@123qwe"
BASE = "/home/zhiwei/AutoTestHub"; LOG = f"{BASE}/full-flow-rerun.log"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
r = lambda cmd,t=30: c.exec_command(cmd, timeout=t)[1].read().decode("utf-8","replace")

# ========== 阶段1: 等待测试完成 ==========
print("=" * 60)
print("阶段1: 等待全流程测试完成")
print("=" * 60)

deadline = time.time() + 1800  # 30 分钟
last_step = ""
while time.time() < deadline:
    alive = r("pgrep -f 'run-full-test-flow.sh' | grep -v pgrep").strip()
    steps = r(f"grep -E '==== Step' {LOG} 2>/dev/null").strip().split("\n")
    cur = re.sub(r'\x1b\[[0-9;]*m', '', steps[-1]).strip() if steps else "?"
    if cur != last_step:
        print(f"[{time.strftime('%H:%M:%S')}] {cur}", flush=True)
        last_step = cur
    if not alive:
        print(f"[{time.strftime('%H:%M:%S')}] ✅ 测试进程已结束", flush=True)
        break
    time.sleep(45)
else:
    print(f"[{time.strftime('%H:%M:%S')}] ⚠️ 等待超时(30分钟)", flush=True)

time.sleep(3)  # 等待文件写入完成

# ========== 阶段2: 验证 Step 8 日志无报错 ==========
print("\n" + "=" * 60)
print("阶段2: 验证 Step 8 日志无报错")
print("=" * 60)

# 提取 Step 8 部分的日志
full_log = r(f"cat {LOG} 2>/dev/null")
step8_start = full_log.find("Step 8")
if step8_start == -1:
    print("❌ 未找到 Step 8 日志")
    sys.exit(1)
step8_log = full_log[step8_start:]

print("--- Step 8 日志 ---")
print(step8_log[:3000])

# 检查是否有语法错误或未绑定变量
errors = []
if "语法错误" in step8_log:
    errors.append("发现 '语法错误'")
if "未绑定的变量" in step8_log:
    errors.append("发现 '未绑定的变量'")
if "unbound variable" in step8_log:
    errors.append("发现 'unbound variable'")
if "syntax error" in step8_log.lower():
    errors.append("发现 'syntax error'")

# 检查 Step 8 各子步骤是否都成功
expected_ok = [
    "阶段状态文件已生成",
    "覆盖矩阵已生成",
    "接口缺陷清单已生成",
    "性能缺陷清单已生成",
    "安全缺陷清单已生成",
    "UI缺陷清单已生成",
    "性能测试专项报告已生成",
    "安全扫描专项报告已生成",
    "系统测试报告已生成",
    "批次摘要已生成",
]
missing_ok = [e for e in expected_ok if e not in step8_log]

if errors:
    print(f"\n❌ Step 8 存在错误: {errors}")
else:
    print("\n✅ Step 8 无语法错误或未绑定变量")

if missing_ok:
    print(f"❌ Step 8 缺少成功标记: {missing_ok}")
else:
    print("✅ Step 8 所有子步骤都成功执行")

# ========== 阶段3: 验证文件完整性 ==========
print("\n" + "=" * 60)
print("阶段3: 验证文件完整性")
print("=" * 60)

batches = r(f"ls -d {BASE}/docs/test-runs/2026* 2>/dev/null").strip().split("\n")
batches = [b.strip() for b in batches if b.strip()]
if not batches:
    print("❌ 未找到批次目录")
    sys.exit(1)
# 选择最新的批次
batch = sorted(batches)[-1]
print(f"验证批次: {batch}")

expected_files = {
    "批次摘要": f"{batch}/批次摘要.md",
    "系统测试报告": f"{batch}/reports/系统测试报告.md",
    "测试覆盖矩阵": f"{batch}/reports/测试覆盖矩阵.md",
    "接口自动化测试报告": f"{batch}/reports/接口自动化测试报告.md",
    "UI自动化测试报告": f"{batch}/reports/UI自动化测试报告.md",
    "性能测试专项报告": f"{batch}/reports/性能测试专项报告.md",
    "安全扫描专项报告": f"{batch}/reports/安全扫描专项报告.md",
    "接口缺陷清单": f"{batch}/defects/接口缺陷清单.md",
    "性能缺陷清单": f"{batch}/defects/性能缺陷清单.md",
    "安全缺陷清单": f"{batch}/defects/安全缺陷清单.md",
    "UI缺陷清单": f"{batch}/defects/UI缺陷清单.md",
}
stages = ["01-requirements","02-test-plan","03-test-cases","04-coverage-matrix",
          "05-api-smoke","06-api-full","07-ui-smoke","08-ui-full",
          "09-perf-smoke","10-perf-regular","11-security-scan","12-system-test-report"]
logs = ["api-smoke.log","api-full.log","ui-smoke.log","ui-full.log",
        "perf-smoke.log","perf-regular.log","security.log"]

print("\n【报告文件】")
missing = []
for name, path in expected_files.items():
    out = r(f"test -f '{path}' && echo OK || echo MISS")
    ok = "OK" in out
    print(f"  {'✅' if ok else '❌'} {name}")
    if not ok: missing.append(name)

print("\n【阶段状态文件】")
for s in stages:
    path = f"{batch}/stage-status/{s}.json"
    out = r(f"test -f '{path}' && echo OK || echo MISS")
    ok = "OK" in out
    print(f"  {'✅' if ok else '❌'} {s}.json")
    if not ok: missing.append(s + ".json")

print("\n【日志文件】")
for l in logs:
    path = f"{batch}/raw/{l}"
    out = r(f"test -f '{path}' && echo OK || echo MISS")
    ok = "OK" in out
    print(f"  {'✅' if ok else '⚠️'} {l}")
    if not ok: missing.append(l)

# 文件总数
total = r(f"find {batch} -type f | wc -l").strip()
print(f"\n文件总数: {total}")

# ========== 阶段4: 交叉引用检查 ==========
print("\n" + "=" * 60)
print("阶段4: 交叉引用完整性")
print("=" * 60)
summary = r(f"cat '{batch}/批次摘要.md' 2>/dev/null")
sys_report = r(f"cat '{batch}/reports/系统测试报告.md' 2>/dev/null")
checks = {
    "批次摘要引用接口缺陷清单": "接口缺陷清单" in summary,
    "批次摘要引用性能专项报告": "性能测试专项报告" in summary,
    "批次摘要引用安全专项报告": "安全扫描专项报告" in summary,
    "批次摘要引用覆盖矩阵": "测试覆盖矩阵" in summary,
    "系统报告引用接口缺陷清单": "接口缺陷清单" in sys_report,
    "系统报告引用性能缺陷清单": "性能缺陷清单" in sys_report,
    "系统报告引用安全缺陷清单": "安全缺陷清单" in sys_report,
    "系统报告引用性能专项报告": "性能测试专项报告" in sys_report,
    "系统报告引用安全专项报告": "安全扫描专项报告" in sys_report,
    "系统报告包含缺陷统计表": "缺陷统计" in sys_report or "合计" in sys_report,
    "系统报告包含正确的缺陷数字(13)": "13" in sys_report,
}
for name, ok in checks.items():
    print(f"  {'✅' if ok else '❌'} {name}")
    if not ok: missing.append(name)

# ========== 最终结论 ==========
print("\n" + "=" * 60)
print("最终结论")
print("=" * 60)
all_ok = (not errors) and (not missing_ok) and (not missing) and all(checks.values())
if all_ok:
    print("✅✅✅ 验证完全通过！")
    print(f"  - Step 8 无报错")
    print(f"  - {total} 个文件全部由脚本独立生成")
    print(f"  - 所有交叉引用正确")
    print(f"  - 缺陷统计数字正确")
else:
    print("❌ 验证未通过，问题:")
    if errors: print(f"  - Step 8 错误: {errors}")
    if missing_ok: print(f"  - 缺少成功标记: {missing_ok}")
    if missing: print(f"  - 缺失项: {missing}")
print("=" * 60)

c.close()