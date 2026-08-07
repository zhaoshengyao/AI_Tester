#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查服务器测试详细状态"""
import paramiko

HOST = "192.168.2.70"
PORT = 22
USER = "root"
PASSWORD = "Zw@123qwe"
REMOTE_BASE = "/home/zhiwei/AutoTestHub"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)

# 查看批次目录内容
BATCH_DIR = REMOTE_BASE + "/docs/test-runs/20260805-175516"
print("=== 批次目录内容 ===")
cmd = "find " + BATCH_DIR + " -type f 2>/dev/null | sort"
_, stdout, stderr = c.exec_command(cmd)
print(stdout.read().decode("utf-8", errors="replace"))

# 查看已生成的报告
print("\n=== 批次摘要 ===")
cmd2 = "cat " + BATCH_DIR + "/批次摘要.md 2>/dev/null || echo '文件不存在'"
_, stdout2, stderr2 = c.exec_command(cmd2)
print(stdout2.read().decode("utf-8", errors="replace"))

# 查看阶段状态
print("\n=== 阶段状态 ===")
cmd3 = "find " + BATCH_DIR + "/stage-status/ -name '*.json' -exec echo '=== {} ===' \\; -exec cat {} \\; 2>/dev/null"
_, stdout3, stderr3 = c.exec_command(cmd3)
print(stdout3.read().decode("utf-8", errors="replace"))

# 查看 locust 运行进度
print("\n=== Locust 进程详情 ===")
cmd4 = "ps -ef | grep locust | grep -v grep"
_, stdout4, stderr4 = c.exec_command(cmd4)
print(stdout4.read().decode("utf-8", errors="replace"))

# 检查是否有 pytest 报告
print("\n=== API 测试结果 ===")
cmd5 = "find " + REMOTE_BASE + "/tests/performance/ -name '*.html' -ls 2>/dev/null"
_, stdout5, stderr5 = c.exec_command(cmd5)
print(stdout5.read().decode("utf-8", errors="replace"))

c.close()