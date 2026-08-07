#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查已完成的测试报告"""
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

# 查看 API 冒烟测试日志
print("=== API 冒烟测试日志 ===")
cmd = "tail -30 " + BATCH_DIR + "/raw/api-smoke.log"
_, stdout, stderr = c.exec_command(cmd)
print(stdout.read().decode("utf-8", errors="replace"))

# 查看 API 全量测试日志
print("\n=== API 全量测试日志 ===")
cmd2 = "tail -30 " + BATCH_DIR + "/raw/api-full.log"
_, stdout2, stderr2 = c.exec_command(cmd2)
print(stdout2.read().decode("utf-8", errors="replace"))

# 查看性能冒烟测试日志
print("\n=== 性能冒烟测试日志 ===")
cmd3 = "tail -20 " + BATCH_DIR + "/raw/perf-smoke.log"
_, stdout3, stderr3 = c.exec_command(cmd3)
print(stdout3.read().decode("utf-8", errors="replace"))

# 查看 UI 冒烟测试日志
print("\n=== UI 冒烟测试日志 ===")
cmd4 = "tail -20 " + BATCH_DIR + "/raw/ui-smoke.log"
_, stdout4, stderr4 = c.exec_command(cmd4)
print(stdout4.read().decode("utf-8", errors="replace"))

# 查看 API 测试报告
print("\n=== API 自动化测试报告摘要 ===")
cmd5 = "head -80 " + BATCH_DIR + "/reports/接口自动化测试报告.md"
_, stdout5, stderr5 = c.exec_command(cmd5)
print(stdout5.read().decode("utf-8", errors="replace"))

# 查看 UI 测试报告
print("\n=== UI 自动化测试报告摘要 ===")
cmd6 = "head -80 " + BATCH_DIR + "/reports/UI自动化测试报告.md"
_, stdout6, stderr6 = c.exec_command(cmd6)
print(stdout6.read().decode("utf-8", errors="replace"))

c.close()