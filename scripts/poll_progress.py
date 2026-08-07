#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""轮询全流程测试进度，直到完成"""
import paramiko
import time
import sys

HOST = "192.168.2.70"
PORT = 22
USER = "root"
PASSWORD = "Zw@123qwe"
REMOTE_BASE = "/home/zhiwei/AutoTestHub"
LOG = f"{REMOTE_BASE}/full-flow-rerun.log"

def get_ssh():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
    return c

def run(client, cmd, t=30):
    _, so, _ = client.exec_command(cmd, timeout=t)
    return so.read().decode("utf-8", errors="replace")

MAX_WAIT = 1200  # 20 分钟
INTERVAL = 30
elapsed = 0

print(f"开始轮询，最大等待 {MAX_WAIT}s，间隔 {INTERVAL}s")
print("=" * 60)

while elapsed <= MAX_WAIT:
    client = get_ssh()
    # 检查进程
    procs = run(client, "pgrep -af 'run-full-test-flow' 2>/dev/null | grep -v pgrep")
    # 检查日志最后行（看当前步骤）
    log_tail = run(client, f"tail -5 {LOG} 2>/dev/null")
    # 检查批次目录
    batches = run(client, f"ls -d {REMOTE_BASE}/docs/test-runs/2026* 2>/dev/null")

    client.close()

    alive = bool([l for l in procs.strip().split("\n") if "run-full-test-flow.sh" in l])
    # 提取当前 Step
    step_line = ""
    for l in log_tail.strip().split("\n"):
        if "Step" in l and "===" in l:
            step_line = l.strip()
    last = log_tail.strip().split("\n")[-1] if log_tail.strip() else "(无日志)"

    print(f"[{elapsed:4d}s] alive={alive} batch={batches.strip().split(chr(10))[-1] if batches.strip() else 'N/A'}")
    print(f"        当前: {step_line or last}")

    if not alive:
        print("\n" + "=" * 60)
        print("✅ 全流程测试进程已结束")
        break

    time.sleep(INTERVAL)
    elapsed += INTERVAL

if elapsed > MAX_WAIT:
    print(f"\n⚠️ 超过最大等待时间 {MAX_WAIT}s")

# 最终状态：重新连接，输出完整总结
client = get_ssh()
print("\n" + "=" * 60)
print("最终日志（最后 40 行）:")
print("=" * 60)
print(run(client, f"tail -40 {LOG} 2>/dev/null"))

print("\n" + "=" * 60)
print("批次目录内容:")
print("=" * 60)
batches = run(client, f"ls -d {REMOTE_BASE}/docs/test-runs/2026* 2>/dev/null").strip()
if batches:
    batch = batches.split("\n")[0]
    print(f"批次: {batch}")
    print(run(client, f"find {batch} -type f | sort"))
else:
    print("未找到批次目录")

client.close()