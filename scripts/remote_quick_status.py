#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""快速检查服务器当前测试状态"""
import paramiko
import re
import sys

HOST = "192.168.2.70"
PORT = 22
USER = "root"
PASSWORD = "Zw@123qwe"
DEPLOY_DIR = "/home/zhiwei/AutoTestHub"
BATCH_ID = "20260811-091728-crm-0cee4e94"
BATCH_DIR = f"{DEPLOY_DIR}/projects/crm/test-runs/{BATCH_ID}"


def get_ssh():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
    c.get_transport().set_keepalive(30)
    return c


def run(client, cmd, timeout=30):
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    try:
        out = stdout.read().decode("utf-8", errors="replace")
    except Exception:
        out = ""
    return out


def clean(s):
    return re.sub(r'\x1b\[[0-9;]*m', '', s)


client = get_ssh()

# 1. 进程状态
print("=== [1] run-full-test 进程状态 ===")
out = run(client, "pgrep -af 'run-full-test|run-perf-tests|run-security-tests|locust' 2>/dev/null || echo DEAD")
print(clean(out) if out.strip() else "DEAD (无进程)")

# 2. 批次摘要是否生成
print("\n=== [2] 批次摘要 ===")
out = run(client, f"test -f {BATCH_DIR}/批次摘要.md && echo EXISTS || echo MISSING")
print(out.strip())

# 3. 系统测试报告
print("\n=== [3] 系统测试报告 ===")
out = run(client, f"test -f {BATCH_DIR}/reports/系统测试报告.md && echo EXISTS || echo MISSING")
print(out.strip())

# 4. reports/ 目录
print("\n=== [4] reports/ 目录 ===")
out = run(client, f"ls -la {BATCH_DIR}/reports/ 2>/dev/null")
print(out)

# 5. stage-status/ 目录
print("\n=== [5] stage-status/ 目录 ===")
out = run(client, f"ls -la {BATCH_DIR}/stage-status/ 2>/dev/null")
print(out if out.strip() else "(不存在)")

# 6. 如果报告已生成，显示内容
print("\n=== [6] 系统测试报告内容 ===")
out = run(client, f"cat {BATCH_DIR}/reports/系统测试报告.md 2>/dev/null || echo NOT_FOUND")
if out.strip() != "NOT_FOUND":
    print(clean(out))
else:
    print("NOT_FOUND")

# 7. 批次摘要内容
print("\n=== [7] 批次摘要内容 ===")
out = run(client, f"cat {BATCH_DIR}/批次摘要.md 2>/dev/null || echo NOT_FOUND")
if out.strip() != "NOT_FOUND":
    print(clean(out))
else:
    print("NOT_FOUND")

client.close()
