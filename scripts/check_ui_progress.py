#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查 UI 全量测试进度和用例规模"""
import paramiko, time

HOST = "192.168.2.70"; PORT = 22; USER = "root"; PASSWORD = "Zw@123qwe"
BASE = "/home/zhiwei/AutoTestHub"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
run = lambda cmd,t=30: c.exec_command(cmd, timeout=t)[1].read().decode("utf-8","replace")

# 1. 统计 UI 测试用例数
print("=== UI 测试用例规模 ===")
print(run(f"cd {BASE}/tests/ui && grep -rn 'test\\(' tests/ --include='*.spec.ts' 2>/dev/null | wc -l", ) + " 个 test()")
print(run(f"cd {BASE}/tests/ui && grep -rn 'test.describe' tests/ --include='*.spec.ts' 2>/dev/null | wc -l") + " 个 describe 块")
print("\n测试文件:")
print(run(f"cd {BASE}/tests/ui && find tests/ -name '*.spec.ts' 2>/dev/null"))

# 2. 检查 test-results 目录最近修改（判断是否在推进）
print("\n=== test-results 最近修改的文件 (前10) ===")
print(run(f"find {BASE}/tests/ui/test-results/ -type f -printf '%T+ %p\\n' 2>/dev/null | sort -r | head -10"))

# 3. 检查 chrome-headless-shell 进程数（实际浏览器）
print("\n=== chrome-headless-shell 进程数 ===")
print(run("pgrep -c chrome-headless-shell 2>/dev/null || echo 0"))

# 4. 检查 playwright worker 进程
print("\n=== playwright worker 进程 ===")
print(run("pgrep -af 'workerProcessEntry' 2>/dev/null | grep -v pgrep"))

# 5. 主进程是否存活
print("\n=== 全流程主进程 ===")
alive = run("pgrep -f 'run-full-test-flow.sh' | grep -v pgrep").strip()
print("存活" if alive else "已结束")

# 6. 最近 30 秒内是否有新文件产生（判断是否卡住）
print("\n=== 最近 60 秒内 test-results 新增/修改文件数 ===")
print(run(f"find {BASE}/tests/ui/test-results/ -type f -mmin -1 2>/dev/null | wc -l"))

c.close()