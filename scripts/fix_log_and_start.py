#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""删除错误的日志目录 + 重新启动全流程测试"""
import paramiko
import time

HOST = "192.168.2.70"; PORT = 22; USER = "root"; PASSWORD = "Zw@123qwe"
BASE = "/home/zhiwei/AutoTestHub"
LOG = f"{BASE}/full-flow-rerun.log"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
r = lambda cmd,t=15: c.exec_command(cmd, timeout=t)[1].read().decode("utf-8","replace")

# 1. 删除被错误创建为目录的 full-flow-rerun.log
print("1. 删除被错误创建为目录的 full-flow-rerun.log")
out = r(f"ls -la {LOG} 2>/dev/null")
print(f"   当前状态: {out.strip()}")
r(f"rm -rf {LOG}")
out = r(f"ls -la {LOG} 2>/dev/null")
print(f"   删除后: {'已删除' if not out.strip() else out.strip()}")

# 2. 通过 invoke_shell 启动测试
print("\n2. 启动全流程测试...")
shell = c.invoke_shell()
time.sleep(1)
while shell.recv_ready():
    shell.recv(4096)

cmd = f"cd {BASE} && nohup bash scripts/run-full-test-flow.sh > {LOG} 2>&1 < /dev/null &\n"
shell.send(cmd)
time.sleep(4)
shell.send("disown\n")
time.sleep(2)

output = ""
while shell.recv_ready():
    output += shell.recv(4096).decode("utf-8", "replace")
print(f"   Shell 输出: {output.strip()}")
shell.close()
time.sleep(3)

# 3. 确认进程存活
procs = r("pgrep -af 'run-full-test-flow.sh' 2>/dev/null | grep -v pgrep")
log_head = r(f"head -10 {LOG} 2>/dev/null")
print(f"\n3. 进程状态:\n{procs}")
print(f"\n4. 日志开头:\n{log_head}")

if procs.strip() and "Step" in log_head:
    pid = procs.strip().split("\n")[0].split()[0]
    print(f"\n✅ 全流程测试已后台启动, PID={pid}")
    print(f"启动时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    with open(r"d:\AICode\TestHub\AITestDemo\scripts\.rerun_state.txt", "w", encoding="utf-8") as f:
        f.write(f"PID={pid}\nLOG={LOG}\nSTART_TIME={time.strftime('%Y-%m-%d %H:%M:%S')}\n")
else:
    print("\n❌ 启动失败")

c.close()