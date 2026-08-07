#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""远程监控测试进度"""
import paramiko
import re
import time

HOST = "192.168.2.70"
PORT = 22
USER = "root"
PASSWORD = "Zw@123qwe"
REMOTE_BASE = "/home/zhiwei/AutoTestHub"
LOG_FILE = f"{REMOTE_BASE}/full-test-flow.log"

def get_ssh():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
    c.get_transport().set_keepalive(30)
    return c

def run(client, cmd, timeout=30):
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    try: out = stdout.read().decode("utf-8", errors="replace")
    except: out = ""
    return out

def clean(s):
    return re.sub(r'\x1b\[[0-9;]*m', '', s)

client = get_ssh()

# 检查进程
out = run(client, "pgrep -af 'run-full-test' 2>/dev/null || echo NONE")
print("进程状态:")
print(clean(out))

# 检查日志大小
out = run(client, f"wc -lc {LOG_FILE} 2>/dev/null || echo 0")
print(f"\n日志: {out.strip()}")

# 查看日志最后 30 行
print("\n--- 日志最后 30 行 ---")
out = run(client, f"tail -30 {LOG_FILE} 2>/dev/null")
print(clean(out))

# 检查性能日志（如果有）
out = run(client, f"ls -lt {REMOTE_BASE}/docs/test-runs/20260805-135149/raw/ 2>/dev/null || echo NONE")
print("\n--- 原始日志文件 ---")
print(out)

# 如果性能测试已启动，检查其内容
out = run(client, f"tail -10 {REMOTE_BASE}/docs/test-runs/20260805-135149/raw/perf-smoke.log 2>/dev/null || echo NONE")
if out.strip() != "NONE":
    print("\n--- 性能冒烟日志尾部 ---")
    print(clean(out))

out = run(client, f"tail -10 {REMOTE_BASE}/docs/test-runs/20260805-135149/raw/perf-regular.log 2>/dev/null || echo NONE")
if out.strip() != "NONE":
    print("\n--- 性能常规日志尾部 ---")
    print(clean(out))

client.close()
