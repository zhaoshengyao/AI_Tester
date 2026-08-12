#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查服务器端当前测试状态和最新批次目录"""
import paramiko
import re

HOST = "192.168.2.70"
PORT = 22
USER = "root"
PASSWORD = "Zw@123qwe"
DEPLOY_DIR = "/home/zhiwei/AutoTestHub"
LOG_FILE = f"{DEPLOY_DIR}/full-test-flow.log"
PID_FILE = f"{DEPLOY_DIR}/full-test-flow.pid"


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
    try:
        err = stderr.read().decode("utf-8", errors="replace")
    except Exception:
        err = ""
    return out, err


def clean(s):
    return re.sub(r'\x1b\[[0-9;]*m', '', s)


client = get_ssh()

# 1. 当前运行进程详情
print("=== [1] 当前 run-full-test 相关进程 ===")
out, _ = run(client, "ps -eo pid,ppid,etime,cmd | grep -E 'run-full-test|run-api-tests|run-ui-tests|run-perf-tests|run-security' | grep -v grep")
print(clean(out) if out.strip() else "(无)")

# 2. PID 文件内容
print("\n=== [2] PID 文件 ===")
out, _ = run(client, f"cat {PID_FILE} 2>/dev/null || echo NONE")
print(f"PID 文件内容: {out.strip()}")

# 3. 日志文件信息（大小+修改时间）
print("\n=== [3] 日志文件信息 ===")
out, _ = run(client, f"ls -la --time-style=full-iso {LOG_FILE} 2>/dev/null")
print(out.strip())
out, _ = run(client, f"stat {LOG_FILE} 2>/dev/null | grep -E 'Size|Modify'")
print(out.strip())

# 4. 最新批次目录（projects/crm/test-runs/ 改造后路径）
print("\n=== [4] projects/crm/test-runs/ 最新批次 ===")
out, _ = run(client, f"ls -dt {DEPLOY_DIR}/projects/crm/test-runs/*/ 2>/dev/null | head -5")
print(out.strip() if out.strip() else "(目录不存在或为空)")

# 5. 旧路径 docs/test-runs/ 最新批次
print("\n=== [5] docs/test-runs/ 最新批次（旧路径）===")
out, _ = run(client, f"ls -dt {DEPLOY_DIR}/docs/test-runs/*/ 2>/dev/null | head -5")
print(out.strip() if out.strip() else "(目录不存在或为空)")

# 6. 日志前 30 行（确认是哪次执行）
print("\n=== [6] 日志前 30 行 ===")
out, _ = run(client, f"head -30 {LOG_FILE} 2>/dev/null")
print(clean(out))

# 7. 日志最后 60 行
print("\n=== [7] 日志最后 60 行 ===")
out, _ = run(client, f"tail -60 {LOG_FILE} 2>/dev/null")
print(clean(out))

# 8. 服务器脚本路径验证
print("\n=== [8] run-full-test-flow.sh 批次目录配置 ===")
out, _ = run(client, f"grep -n 'BATCH_DIR\\|projects.*test-runs\\|docs/test-runs' {DEPLOY_DIR}/scripts/run-full-test-flow.sh | head -10")
print(out.strip())

# 9. system.yaml 是否存在
print("\n=== [9] system.yaml 文件 ===")
out, _ = run(client, f"ls -la {DEPLOY_DIR}/projects/crm/system.yaml 2>/dev/null || echo NOT_FOUND")
print(out.strip())
out, _ = run(client, f"grep -n 'output_dir' {DEPLOY_DIR}/projects/crm/system.yaml 2>/dev/null")
print(out.strip())

client.close()
print("\n[OK] 检查完成")
