#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""快速检查测试当前进度（单次）"""
import paramiko

HOST = "192.168.2.70"; PORT = 22; USER = "root"; PASSWORD = "Zw@123qwe"
BASE = "/home/zhiwei/AutoTestHub"; LOG = f"{BASE}/full-flow-rerun.log"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
run = lambda cmd: c.exec_command(cmd, timeout=30)[1].read().decode("utf-8","replace")

alive = run("pgrep -af 'run-full-test-flow.sh' | grep -v pgrep | grep -v 'bash -c'").strip()
print(f"进程存活: {'是' if alive else '否（测试已结束）'}")
if alive:
    for l in alive.split("\n"):
        print(f"  {l}")

print("\n--- 当前步骤（日志中所有 Step 标题）---")
steps = run(f"grep -E '==== Step' {LOG} 2>/dev/null")
print(steps or "(无)")

print("\n--- 日志最后 15 行 ---")
print(run(f"tail -15 {LOG} 2>/dev/null"))

print("\n--- 批次目录 ---")
batches = run(f"ls -d {BASE}/docs/test-runs/2026* 2>/dev/null").strip()
print(batches or "(尚未创建)")
if batches:
    b = sorted(batches.split("\n"))[-1]
    print(f"\n最新批次已生成文件:")
    print(run(f"find {b} -type f 2>/dev/null | sort"))

c.close()