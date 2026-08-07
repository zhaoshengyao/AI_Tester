#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""快速检查服务器测试状态"""
import paramiko
import re

HOST = "192.168.2.70"
PORT = 22
USER = "root"
PASSWORD = "Zw@123qwe"
DEPLOY_DIR = "/home/zhiwei/AutoTestHub"
LOG_FILE = f"{DEPLOY_DIR}/full-test-flow.log"

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

# 1. 进程状态
print("=== [1] 进程状态 ===")
out = run(client, "pgrep -af 'run-full-test' 2>/dev/null || echo DEAD")
print(clean(out))

# 2. Playwright 进程数
print("\n=== [2] Playwright/Chromium 进程数 ===")
out = run(client, "pgrep -c 'playwright|chrome-headless' 2>/dev/null || echo 0")
print(f"进程数: {out.strip()}")

# 3. 日志大小
print("\n=== [3] 日志大小 ===")
out = run(client, f"wc -lc {LOG_FILE} 2>/dev/null")
print(out.strip())

# 4. 日志最后 40 行
print("\n=== [4] 日志最后 40 行 ===")
out = run(client, f"tail -40 {LOG_FILE} 2>/dev/null")
print(clean(out))

# 5. 批次目录
print("\n=== [5] 批次目录 ===")
out = run(client, f"ls -laR {DEPLOY_DIR}/docs/test-runs/20260805-113810/ 2>/dev/null | head -40")
print(out)

# 6. 如果系统测试报告已生成
print("\n=== [6] 系统测试报告 ===")
out = run(client, f"cat '{DEPLOY_DIR}/docs/test-runs/20260805-113810/reports/系统测试报告.md' 2>/dev/null || echo NOT_FOUND")
if out.strip() != "NOT_FOUND":
    print(clean(out))
else:
    print("未生成")

# 7. 批次摘要
print("\n=== [7] 批次摘要 ===")
out = run(client, f"cat '{DEPLOY_DIR}/docs/test-runs/20260805-113810/批次摘要.md' 2>/dev/null || echo NOT_FOUND")
if out.strip() != "NOT_FOUND":
    print(clean(out))
else:
    print("未生成")

# 8. UI 测试结果 JSON
print("\n=== [8] UI 测试 JSON 统计 ===")
out = run(client, f"python3 -c \"import json; d=json.load(open('{DEPLOY_DIR}/tests/ui/test-results.json')); s=d['stats']; print(f'Total: {{s[\"expected\"]}}, Unexpected: {{s[\"unexpected\"]}}, Flaky: {{s[\"flaky\"]}}, Skipped: {{s[\"skipped\"]}}')\" 2>/dev/null || echo NO_JSON")
print(out.strip())

client.close()
