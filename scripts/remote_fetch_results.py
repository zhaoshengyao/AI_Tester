#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""获取详细测试结果"""
import paramiko
import re

HOST = "192.168.2.70"
PORT = 22
USER = "root"
PASSWORD = "Zw@123qwe"
DEPLOY_DIR = "/home/zhiwei/AutoTestHub"

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
batch = f"{DEPLOY_DIR}/docs/test-runs/20260805-113810"

# 1. API 全量失败详情
print("=== [1] API 全量测试失败详情 ===")
out = run(client, f"grep -A2 'FAILED' {batch}/raw/api-full.log | head -30")
print(clean(out))

# 2. UI 全量测试结果
print("\n=== [2] UI 全量测试结果 ===")
out = run(client, f"grep -E 'passed|failed|error|✅|❌| PASSED | FAILED |tests:' {batch}/raw/ui-full.log | tail -20")
print(clean(out))

# 3. UI 全量统计
print("\n=== [3] UI 全量 Playwright 统计 ===")
out = run(client, f"python3 -c \"import json; d=json.load(open('{DEPLOY_DIR}/tests/ui/test-results.json')); s=d['stats']; print(f'Total: {{s[\\\"expected\\\"]}}, Passed: {{s[\\\"expected\\\"]-s[\\\"unexpected\\\"]}}, Failed: {{s[\\\"unexpected\\\"]}}, Flaky: {{s[\\\"flaky\\\"]}}, Skipped: {{s[\\\"skipped\\\"]}}')\" 2>/dev/null || echo NO_JSON")
print(out.strip())

# 4. 性能冒烟结果
print("\n=== [4] 性能冒烟测试结果 ===")
out = run(client, f"tail -30 {batch}/raw/perf-smoke.log")
print(clean(out))

# 5. 性能常规失败详情
print("\n=== [5] 性能常规测试失败详情 ===")
out = run(client, f"tail -20 {batch}/raw/perf-regular.log")
print(clean(out))

# 6. 安全扫描日志
print("\n=== [6] 安全扫描日志 ===")
out = run(client, f"cat {batch}/raw/security.log")
print(clean(out))

# 7. 检查服务器上的脚本版本
print("\n=== [7] 服务器脚本版本检查 ===")
out = run(client, f"grep 'run_full_scan\\|scanner.run' {DEPLOY_DIR}/scripts/run-security-tests.sh 2>/dev/null")
print(f"安全扫描脚本: {out.strip()}")

out = run(client, f"grep 'set -e' {DEPLOY_DIR}/scripts/run-full-test-flow.sh 2>/dev/null")
print(f"全流程脚本 set -e: {out.strip()}")

# 8. 检查 heredoc 问题
print("\n=== [8] 全流程脚本 heredoc 检查 ===")
out = run(client, f"sed -n '240,260p' {DEPLOY_DIR}/scripts/run-full-test-flow.sh 2>/dev/null")
print(out)

client.close()
