#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""验证新批次报告完整性：缺陷清单/覆盖矩阵/专项报告/阶段状态/交叉引用"""
import paramiko
import sys

HOST = "192.168.2.70"
PORT = 22
USER = "root"
PASSWORD = "Zw@123qwe"
REMOTE_BASE = "/home/zhiwei/AutoTestHub"

def get_ssh():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
    return c

def run(client, cmd, t=30):
    _, so, _ = client.exec_command(cmd, timeout=t)
    return so.read().decode("utf-8", errors="replace")

client = get_ssh()

# 找到最新批次
batches = run(client, f"ls -d {REMOTE_BASE}/docs/test-runs/2026* 2>/dev/null").strip()
if not batches:
    print("❌ 未找到任何批次目录")
    sys.exit(1)
batch = sorted(batches.split("\n"))[-1]
print(f"验证批次: {batch}")
print("=" * 60)

# 期望文件清单
expected = {
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
stages = [f"{batch}/stage-status/{s}.json" for s in [
    "01-requirements","02-test-plan","03-test-cases","04-coverage-matrix",
    "05-api-smoke","06-api-full","07-ui-smoke","08-ui-full",
    "09-perf-smoke","10-perf-regular","11-security-scan","12-system-test-report"]]

print("\n【1. 报告文件检查】")
missing_reports = []
for name, path in expected.items():
    out = run(client, f"test -f '{path}' && echo OK || echo MISS")
    status = "✅" if "OK" in out else "❌"
    if "MISS" in out:
        missing_reports.append(name)
    print(f"  {status} {name}: {path}")

print("\n【2. 阶段状态文件检查】")
missing_stages = []
for s in stages:
    name = s.split("/")[-1]
    out = run(client, f"test -f '{s}' && echo OK || echo MISS")
    status = "✅" if "OK" in out else "❌"
    if "MISS" in out:
        missing_stages.append(name)
    print(f"  {status} {name}")

print("\n【3. 日志文件检查】")
logs = ["api-smoke.log","api-full.log","ui-smoke.log","ui-full.log",
        "perf-smoke.log","perf-regular.log","security.log"]
for l in logs:
    path = f"{batch}/raw/{l}"
    out = run(client, f"test -f '{path}' && echo OK || echo MISS")
    status = "✅" if "OK" in out else "⚠️"
    print(f"  {status} {l}")

print("\n【4. 交叉引用完整性检查】")
# 批次摘要应引用缺陷清单和专项报告
summary = run(client, f"cat '{batch}/批次摘要.md' 2>/dev/null")
checks = {
    "批次摘要引用接口缺陷清单": "接口缺陷清单" in summary,
    "批次摘要引用性能专项报告": "性能测试专项报告" in summary,
    "批次摘要引用安全专项报告": "安全扫描专项报告" in summary,
    "批次摘要引用覆盖矩阵": "测试覆盖矩阵" in summary,
}
sys_report = run(client, f"cat '{batch}/reports/系统测试报告.md' 2>/dev/null")
checks.update({
    "系统报告引用接口缺陷清单": "接口缺陷清单" in sys_report,
    "系统报告引用性能缺陷清单": "性能缺陷清单" in sys_report,
    "系统报告引用安全缺陷清单": "安全缺陷清单" in sys_report,
    "系统报告引用性能专项报告": "性能测试专项报告" in sys_report,
    "系统报告引用安全专项报告": "安全扫描专项报告" in sys_report,
    "系统报告包含缺陷统计表": "缺陷统计" in sys_report or "合计" in sys_report,
})
for name, ok in checks.items():
    print(f"  {'✅' if ok else '❌'} {name}")

print("\n【5. 缺陷数量提取】")
for name, path in [("接口","接口缺陷清单.md"),("性能","性能缺陷清单.md"),
                   ("安全","安全缺陷清单.md"),("UI","UI缺陷清单.md")]:
    content = run(client, f"cat '{batch}/defects/{path}' 2>/dev/null")
    # 统计 DEF 或 VUL 编号的缺陷条目
    count = 0
    for line in content.split("\n"):
        if line.startswith("### ") and ("DEF" in line or "VUL" in line):
            count += 1
    print(f"  {name}缺陷: {count} 条")

print("\n" + "=" * 60)
total_missing = len(missing_reports) + len(missing_stages)
if total_missing == 0 and all(checks.values()):
    print("✅✅✅ 报告完整性验证通过！所有文件和引用齐全")
else:
    print(f"❌ 仍有缺失: 报告 {len(missing_reports)} 个, 阶段状态 {len(missing_stages)} 个")
    if missing_reports: print(f"   缺失报告: {missing_reports}")
    if missing_stages: print(f"   缺失阶段: {missing_stages}")
    bad_refs = [k for k,v in checks.items() if not v]
    if bad_refs: print(f"   缺失引用: {bad_refs}")
print("=" * 60)

client.close()