#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""启动全流程测试（后台）- 修复 stdin 阻塞问题"""
import paramiko
import time
import sys

HOST = "192.168.2.70"
PORT = 22
USER = "root"
PASSWORD = "Zw@123qwe"
REMOTE_BASE = "/home/zhiwei/AutoTestHub"

def get_ssh():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
    return c

client = get_ssh()

log_file = f"{REMOTE_BASE}/full-flow-rerun.log"
run = lambda cmd: client.exec_command(cmd, timeout=30)

# 清空旧日志
run(f"rm -f {log_file}")

print("启动全流程测试（后台）...")
# 关键：添加 < /dev/null 关闭 stdin，并用 setsid 完全脱离
# 用 nohup + & + disown 确保进程脱离 ssh 会话
start_cmd = (
    f"cd {REMOTE_BASE} && "
    f"setsid bash -c 'nohup bash scripts/run-full-test-flow.sh > {log_file} 2>&1 < /dev/null &' "
    f"< /dev/null > /dev/null 2>&1 &"
)
_, stdout, stderr = run(start_cmd)
try:
    stdout.read()
except Exception:
    pass

# 等待进程启动并写入日志
time.sleep(8)

# 通过日志文件确认测试已启动
_, so, _ = run(f"head -20 {log_file} 2>/dev/null")
log_head = so.read().decode("utf-8", errors="replace")
print("日志开头:")
print(log_head)

# 查找 run-full-test-flow 相关进程
_, so, _ = run("pgrep -af 'run-full-test-flow' 2>/dev/null")
procs = so.read().decode("utf-8", errors="replace")
print(f"\n相关进程:\n{procs}")

if not procs.strip() and "Step" not in log_head:
    print("⚠️ 测试可能未成功启动")
    _, so, _ = run(f"cat {log_file} 2>/dev/null")
    print(so.read().decode("utf-8", errors="replace"))
    sys.exit(1)

# 获取进程 PID
pid = ""
for line in procs.strip().split("\n"):
    if "run-full-test-flow" in line:
        pid = line.split()[0]
        break

# 记录状态
state = f"PID={pid}\nLOG={log_file}\nSTART_TIME={time.strftime('%Y-%m-%d %H:%M:%S')}\n"
with open(r"d:\AICode\TestHub\AITestDemo\scripts\.rerun_state.txt", "w", encoding="utf-8") as f:
    f.write(state)

print(f"\n✅ 全流程测试已后台启动, PID={pid}")
print(f"日志: {log_file}")
print(f"启动时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
client.close()