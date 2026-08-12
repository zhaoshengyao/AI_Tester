#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查最新批次目录的进度和内容"""
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
    try:
        out = stdout.read().decode("utf-8", errors="replace")
    except Exception:
        out = ""
    return out


def clean(s):
    return re.sub(r'\x1b\[[0-9;]*m', '', s)


client = get_ssh()

# 1. 最新批次目录
print("=== [1] 最新批次目录结构 ===")
out = run(client, f"ls -dt {DEPLOY_DIR}/projects/crm/test-runs/*/ 2>/dev/null | head -1")
latest_batch = out.strip()
print(f"最新批次: {latest_batch}")

if latest_batch:
    print("\n=== [2] 批次目录树（2层）===")
    out = run(client, f"find {latest_batch} -maxdepth 2 -printf '%y %p\\n' 2>/dev/null | sort")
    print(out)

    print("\n=== [3] raw/ 目录日志文件 ===")
    out = run(client, f"ls -la --time-style=full-iso {latest_batch}raw/ 2>/dev/null")
    print(out)

    print("\n=== [4] stage-status/ 阶段状态 ===")
    out = run(client, f"ls -la {latest_batch}stage-status/ 2>/dev/null && echo '---' && for f in {latest_batch}stage-status/*.json; do echo \"--- $f ---\"; cat \"$f\" 2>/dev/null; echo; done")
    print(out)

    print("\n=== [5] reports/ 目录 ===")
    out = run(client, f"ls -la {latest_batch}reports/ 2>/dev/null")
    print(out)

    print("\n=== [6] 当前性能测试日志最后 30 行 ===")
    out = run(client, f"tail -30 {latest_batch}raw/perf-regular.log 2>/dev/null || echo 'NO_PERF_LOG'")
    print(clean(out))

    print("\n=== [7] 性能测试进程状态 ===")
    out = run(client, "ps -eo pid,etime,cmd | grep -E 'locust|run-perf' | grep -v grep")
    print(out if out.strip() else "(无性能测试进程)")

client.close()
print("\n[OK] 检查完成")
