#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""对比历史批次与当前批次的文件差异"""
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

print("=" * 60)
print("当前批次文件结构")
print("=" * 60)
cmd = "find " + BATCH_DIR + " -type f 2>/dev/null | sort"
_, stdout, stderr = c.exec_command(cmd)
print(stdout.read().decode("utf-8", errors="replace"))

print("\n" + "=" * 60)
print("检查 reports/ 子目录")
print("=" * 60)
cmd2 = "ls -la " + BATCH_DIR + "/reports/ 2>/dev/null"
_, stdout2, stderr2 = c.exec_command(cmd2)
print(stdout2.read().decode("utf-8", errors="replace"))

print("\n" + "=" * 60)
print("检查是否有 defects/ 目录")
print("=" * 60)
cmd3 = "ls -la " + BATCH_DIR + "/defects/ 2>/dev/null || echo 'defects目录不存在!'"
_, stdout3, stderr3 = c.exec_command(cmd3)
print(stdout3.read().decode("utf-8", errors="replace"))

print("\n" + "=" * 60)
print("检查是否有覆盖矩阵")
print("=" * 60)
cmd4 = "find " + BATCH_DIR + " -name '*覆盖*' -o -name '*矩阵*' 2>/dev/null"
_, stdout4, stderr4 = c.exec_command(cmd4)
result4 = stdout4.read().decode("utf-8", errors="replace")
print(result4 or "未找到覆盖矩阵文件!")

print("\n" + "=" * 60)
print("检查专项报告")
print("=" * 60)
cmd5 = "find " + BATCH_DIR + " -name '*性能*' -o -name '*安全*' -o -name '*API*' -o -name '*接口*' -o -name '*UI*' -o -name '*专项*' 2>/dev/null | sort"
_, stdout5, stderr5 = c.exec_command(cmd5)
print(stdout5.read().decode("utf-8", errors="replace") or "未找到专项报告文件!")

print("\n" + "=" * 60)
print("检查缺陷清单相关文件")
print("=" * 60)
cmd6 = "find " + BATCH_DIR + " -name '*缺陷*' -o -name '*defect*' 2>/dev/null"
_, stdout6, stderr6 = c.exec_command(cmd6)
print(stdout6.read().decode("utf-8", errors="replace") or "未找到缺陷清单文件!")

c.close()