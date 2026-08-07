#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""获取详细测试报告"""
import paramiko

HOST = "192.168.2.70"
PORT = 22
USER = "root"
PASSWORD = "Zw@123qwe"
REMOTE_BASE = "/home/zhiwei/AutoTestHub"
BATCH_DIR = REMOTE_BASE + "/docs/test-runs/20260805-175516"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)

# 获取系统测试报告
print("=" * 60)
print("系统测试报告")
print("=" * 60)
cmd = "cat " + BATCH_DIR + "/reports/系统测试报告.md"
_, stdout, stderr = c.exec_command(cmd)
print(stdout.read().decode("utf-8", errors="replace"))

# 获取性能常规测试日志
print("\n" + "=" * 60)
print("性能常规测试日志摘要")
print("=" * 60)
cmd2 = "grep -E 'Aggregated|FAIL|401|失败' " + BATCH_DIR + "/raw/perf-regular.log | tail -30"
_, stdout2, stderr2 = c.exec_command(cmd2)
print(stdout2.read().decode("utf-8", errors="replace"))

# 获取性能冒烟测试日志
print("\n" + "=" * 60)
print("性能冒烟测试日志摘要")
print("=" * 60)
cmd3 = "grep -E 'Aggregated|FAIL|401|失败' " + BATCH_DIR + "/raw/perf-smoke.log | tail -20"
_, stdout3, stderr3 = c.exec_command(cmd3)
print(stdout3.read().decode("utf-8", errors="replace"))

# 获取安全测试日志
print("\n" + "=" * 60)
print("安全测试摘要")
print("=" * 60)
cmd4 = "tail -50 " + BATCH_DIR + "/raw/security.log"
_, stdout4, stderr4 = c.exec_command(cmd4)
print(stdout4.read().decode("utf-8", errors="replace"))

c.close()