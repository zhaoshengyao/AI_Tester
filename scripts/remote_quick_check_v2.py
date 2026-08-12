#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""快速检查服务器测试状态（适配多系统架构）"""
import paramiko
import re
import sys

HOST = "192.168.2.70"
PORT = 22
USER = "root"
PASSWORD = "Zw@123qwe"
DEPLOY_DIR = "/home/zhiwei/AutoTestHub"
LOG_FILE = f"{DEPLOY_DIR}/full-test-flow.log"
SYSTEM = sys.argv[1] if len(sys.argv) > 1 else "crm"
TEST_RUNS_DIR = f"{DEPLOY_DIR}/projects/{SYSTEM}/test-runs"

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

try:
    client = get_ssh()
    print(f"[INFO] 已连接服务器 {HOST}, 检查系统: {SYSTEM}")
except Exception as e:
    print(f"[ERROR] SSH 连接失败: {e}")
    sys.exit(1)

# 1. 进程状态
print("\n=== [1] 测试进程状态 ===")
out = run(client, "pgrep -af 'run-full-test|run-perf-tests|locust|playwright' 2>/dev/null || echo DEAD")
result = clean(out).strip()
if result == "DEAD" or not result:
    print("无运行中的测试进程")
else:
    print(result)

# 2. 日志大小和最后 30 行
print("\n=== [2] 日志状态 ===")
out = run(client, f"wc -lc {LOG_FILE} 2>/dev/null || echo '0 0 {LOG_FILE}'")
print(f"日志文件: {out.strip()}")

out = run(client, f"tail -30 {LOG_FILE} 2>/dev/null")
tail = clean(out).strip()
if tail:
    print(f"\n--- 最后 30 行 ---\n{tail}")
else:
    print("(无日志)")

# 3. 最新批次目录
print(f"\n=== [3] {SYSTEM} 最新批次目录 ===")
out = run(client, f"ls -dt {TEST_RUNS_DIR}/*/ 2>/dev/null | head -3")
batches = out.strip()
if batches:
    print(batches)
    # 取最新批次
    latest = batches.split("\n")[0].strip().rstrip("/")
    batch_id = latest.split("/")[-1]
    print(f"\n最新批次 ID: {batch_id}")

    # 4. 批次内容
    print(f"\n=== [4] 批次目录内容 ===")
    out = run(client, f"find {latest} -type f 2>/dev/null | head -30")
    print(out.strip() if out.strip() else "(空)")

    # 5. 批次摘要
    print(f"\n=== [5] 批次摘要 ===")
    out = run(client, f"cat '{latest}/批次摘要.md' 2>/dev/null || echo NOT_FOUND")
    if out.strip() != "NOT_FOUND":
        print(clean(out)[:3000])
    else:
        print("未生成")

    # 6. 系统测试报告
    print(f"\n=== [6] 系统测试报告 ===")
    out = run(client, f"cat '{latest}/reports/系统测试报告.md' 2>/dev/null || echo NOT_FOUND")
    if out.strip() != "NOT_FOUND":
        print(clean(out)[:3000])
    else:
        print("未生成")
else:
    print(f"未找到 {SYSTEM} 的批次目录: {TEST_RUNS_DIR}/")

# 7. 服务器基本信息
print("\n=== [7] 服务器基本信息 ===")
out = run(client, f"cd {DEPLOY_DIR} && git log --oneline -3 2>/dev/null || echo '非Git仓库'")
print(f"Git 最新提交:\n{out.strip()}")
out = run(client, "uptime 2>/dev/null")
print(f"\n服务器 uptime: {out.strip()}")

client.close()
print("\n[OK] 检查完成")
