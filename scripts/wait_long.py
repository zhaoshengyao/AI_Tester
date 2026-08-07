#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""等待全流程测试完成（长等待，25分钟）"""
import paramiko
import time
import sys

HOST = "192.168.2.70"; PORT = 22; USER = "root"; PASSWORD = "Zw@123qwe"
BASE = "/home/zhiwei/AutoTestHub"; LOG = f"{BASE}/full-flow-rerun.log"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
run = lambda cmd,t=30: c.exec_command(cmd, timeout=t)[1].read().decode("utf-8","replace")

deadline = time.time() + 1500  # 25 分钟
last_step = ""
while time.time() < deadline:
    alive = run("pgrep -f 'run-full-test-flow.sh' | grep -v pgrep").strip()
    steps = run(f"grep -E '==== Step' {LOG} 2>/dev/null").strip().split("\n")
    cur = steps[-1] if steps else "?"
    # 去除颜色码
    import re
    cur = re.sub(r'\x1b\[[0-9;]*m', '', cur).strip()
    if cur != last_step:
        print(f"[{time.strftime('%H:%M:%S')}] 步骤变化: {cur}", flush=True)
        last_step = cur
    if not alive:
        print(f"[{time.strftime('%H:%M:%S')}] ✅ 全流程测试进程已结束", flush=True)
        break
    time.sleep(45)
else:
    print(f"[{time.strftime('%H:%M:%S')}] ⚠️ 等待超时", flush=True)

# 最终结果
print("\n" + "=" * 60, flush=True)
print("所有执行步骤:", flush=True)
print("=" * 60, flush=True)
print(run(f"grep -E '==== Step|全流程执行完成' {LOG} 2>/dev/null"), flush=True)

print("\n" + "=" * 60, flush=True)
print("日志最后 35 行:", flush=True)
print("=" * 60, flush=True)
print(run(f"tail -35 {LOG} 2>/dev/null"), flush=True)

# 批次目录文件清单
print("\n" + "=" * 60, flush=True)
print("批次目录文件清单:", flush=True)
print("=" * 60, flush=True)
batches = run(f"ls -d {BASE}/docs/test-runs/2026* 2>/dev/null").strip().split("\n")
for b in batches:
    b = b.strip()
    if not b: continue
    cnt = run(f"find {b} -type f | wc -l").strip()
    print(f"\n批次: {b} ({cnt} 个文件)", flush=True)
    print(run(f"find {b} -type f | sort"), flush=True)

c.close()