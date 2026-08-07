#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查服务器测试状态"""
import paramiko

HOST = "192.168.2.70"
PORT = 22
USER = "root"
PASSWORD = "Zw@123qwe"
REMOTE_BASE = "/home/zhiwei/AutoTestHub"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)

# 查看测试运行目录
print("=== 检查测试运行目录 ===")
cmd = "ls -la " + REMOTE_BASE + "/docs/test-runs/ 2>/dev/null || echo '目录为空或不存在'"
_, stdout, stderr = c.exec_command(cmd)
print(stdout.read().decode("utf-8", errors="replace"))

# 检查后台进程
print("=== 检查是否有测试进程 ===")
cmd2 = "ps aux | grep locust | grep -v grep"
_, stdout2, stderr2 = c.exec_command(cmd2)
result = stdout2.read().decode("utf-8", errors="replace")
print(result or "无 locust 进程运行")

# 检查pytest进程
cmd3 = "ps aux | grep pytest | grep -v grep"
_, stdout3, stderr3 = c.exec_command(cmd3)
result3 = stdout3.read().decode("utf-8", errors="replace")
print(result3 or "无 pytest 进程运行")

# 查看是否有新批次目录
print("=== 检查批次目录 ===")
cmd4 = "ls -t " + REMOTE_BASE + "/docs/test-runs/ 2>/dev/null | head -5"
_, stdout4, stderr4 = c.exec_command(cmd4)
print(stdout4.read().decode("utf-8", errors="replace") or "无批次目录")

c.close()