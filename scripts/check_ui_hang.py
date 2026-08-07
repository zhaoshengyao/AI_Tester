#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查 UI 全量测试卡住的具体原因"""
import paramiko

HOST = "192.168.2.70"; PORT = 22; USER = "root"; PASSWORD = "Zw@123qwe"
BASE = "/home/zhiwei/AutoTestHub"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
run = lambda cmd,t=30: c.exec_command(cmd, timeout=t)[1].read().decode("utf-8","replace")

# 进程状态
print("=== 相关进程 ===")
print(run("pgrep -af 'playwright|node|chromium|run-full-test' | grep -v pgrep"))

# UI 全量日志末尾
print("\n=== ui-full.log 最后 40 行 ===")
print(run(f"tail -40 {BASE}/docs/test-runs/20260806-093518/raw/ui-full.log 2>/dev/null"))

# 主日志末尾
print("\n=== full-flow-rerun.log 最后 10 行 ===")
print(run(f"tail -10 {BASE}/full-flow-rerun.log 2>/dev/null"))

# 检查是否有 chromium 进程
print("\n=== Chromium 进程数 ===")
print(run("pgrep -c chromium 2>/dev/null || echo 0"))

c.close()