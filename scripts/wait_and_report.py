#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""阻塞等待测试完成并输出最终结果"""
import paramiko
import time
import sys

HOST = "192.168.2.70"; PORT = 22; USER = "root"; PASSWORD = "Zw@123qwe"
BASE = "/home/zhiwei/AutoTestHub"; LOG = f"{BASE}/full-flow-rerun.log"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
run = lambda cmd,t=30: c.exec_command(cmd, timeout=t)[1].read().decode("utf-8","replace")

deadline = time.time() + 540  # 最多等 9 分钟
while time.time() < deadline:
    alive = run("pgrep -f 'run-full-test-flow.sh' | grep -v pgrep").strip()
    if not alive:
        print("✅ 全流程测试进程已结束")
        break
    steps = run(f"grep -E '==== Step' {LOG} 2>/dev/null").strip().split("\n")
    last_step = steps[-1] if steps else "?"
    print(f"[{int(time.time())%100}s] 运行中... 当前: {last_step}", flush=True)
    time.sleep(40)
else:
    print("⚠️ 等待超时，测试仍在运行")

print("\n" + "=" * 60)
print("所有执行步骤:")
print("=" * 60)
print(run(f"grep -E '==== Step|全流程执行完成' {LOG} 2>/dev/null"))

print("\n" + "=" * 60)
print("日志最后 30 行:")
print("=" * 60)
print(run(f"tail -30 {LOG} 2>/dev/null"))

# 清理残留的空批次目录
print("\n" + "=" * 60)
print("清理残留批次目录")
print("=" * 60)
batches = run(f"ls -d {BASE}/docs/test-runs/2026* 2>/dev/null").strip().split("\n")
for b in batches:
    b = b.strip()
    if not b: continue
    cnt = run(f"find {b} -type f | wc -l").strip()
    if int(cnt or 0) < 3:
        run(f"rm -rf {b}")
        print(f"  🗑️ 已删除空批次: {b} (仅 {cnt} 个文件)")
    else:
        print(f"  ✅ 保留批次: {b} ({cnt} 个文件)")

c.close()