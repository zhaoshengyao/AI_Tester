#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""单独启动全流程测试 - 使用 invoke_shell 确保 nohup 进程脱离"""
import paramiko
import time

HOST = "192.168.2.70"; PORT = 22; USER = "root"; PASSWORD = "Zw@123qwe"
BASE = "/home/zhiwei/AutoTestHub"
LOG = f"{BASE}/full-flow-rerun.log"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)

# 使用 invoke_shell 方式，确保 nohup 进程能完全脱离
print("通过 invoke_shell 启动全流程测试...")
shell = c.invoke_shell()
time.sleep(1)
# 清空接收缓冲
while shell.recv_ready():
    shell.recv(4096)

# 发送启动命令
cmd = f"cd {BASE} && nohup bash scripts/run-full-test-flow.sh > {LOG} 2>&1 < /dev/null &\n"
shell.send(cmd)
time.sleep(3)

# 发送 disown 确保进程脱离
shell.send("disown\n")
time.sleep(2)

# 读取 shell 输出（会包含 PID 信息）
output = ""
while shell.recv_ready():
    output += shell.recv(4096).decode("utf-8", "replace")
print("Shell 输出:")
print(output)

shell.close()
time.sleep(3)

# 通过新连接确认进程是否存活
_, so, _ = c.exec_command("pgrep -af 'run-full-test-flow.sh' 2>/dev/null | grep -v pgrep", timeout=15)
procs = so.read().decode("utf-8", "replace")
print(f"\n相关进程:\n{procs}")

# 确认日志开始写入
_, so, _ = c.exec_command(f"head -8 {LOG} 2>/dev/null", timeout=15)
log_head = so.read().decode("utf-8", "replace")
print(f"\n日志开头:\n{log_head}")

if procs.strip() and "Step" in log_head:
    pid = procs.strip().split("\n")[0].split()[0]
    print(f"\n✅ 全流程测试已后台启动, PID={pid}")
    print(f"启动时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"日志: {LOG}")
    with open(r"d:\AICode\TestHub\AITestDemo\scripts\.rerun_state.txt", "w", encoding="utf-8") as f:
        f.write(f"PID={pid}\nLOG={LOG}\nSTART_TIME={time.strftime('%Y-%m-%d %H:%M:%S')}\n")
else:
    print("\n⚠️ 启动失败，查看日志:")
    _, so, _ = c.exec_command(f"cat {LOG} 2>/dev/null", timeout=15)
    print(so.read().decode("utf-8", "replace"))

c.close()