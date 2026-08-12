#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""上传修复后的 _ipd_run_api_pipeline.py 到服务器并在后台启动测试。"""
import paramiko
import time
import sys

HOST = "192.168.2.70"
PORT = 22
USER = "root"
PASSWORD = "Zw@123qwe"
DEPLOY_DIR = "/home/zhiwei/AutoTestHub"
LOG_FILE = f"{DEPLOY_DIR}/ipd-full-test.log"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
c.get_transport().set_keepalive(30)

# 上传修复后的 pipeline
sftp = c.open_sftp()
sftp.put("_ipd_run_api_pipeline.py", f"{DEPLOY_DIR}/_ipd_run_api_pipeline.py")
print("[OK] _ipd_run_api_pipeline.py uploaded")
sftp.close()

# 清理旧的脏目录
c.exec_command(f'rm -rf "{DEPLOY_DIR}/d:\\\\AICode" 2>/dev/null', timeout=10)
time.sleep(1)

# 直接前台运行（不 setsid），先验证能跑起来
print("\n=== 启动测试（前台，超时 10 分钟）===")
_, stdout, stderr = c.exec_command(
    f"cd {DEPLOY_DIR} && PYTHONPATH={DEPLOY_DIR} python3 _ipd_run_api_pipeline.py 2>&1",
    timeout=600
)

# 增量读取输出
import socket
channel = stdout.channel
channel.settimeout(10)
buf = b""
while True:
    try:
        chunk = channel.recv(4096)
        if not chunk:
            break
        buf += chunk
        text = chunk.decode("utf-8", errors="replace")
        # 实时打印
        for line in text.split("\n"):
            ls = line.strip()
            if ls:
                print(f"  | {ls}")
    except socket.timeout:
        if channel.exit_status_ready():
            break
        continue

# 读取剩余
remaining = stdout.read().decode("utf-8", errors="replace")
if remaining.strip():
    for line in remaining.strip().split("\n"):
        print(f"  | {line.strip()}")

err_text = stderr.read().decode("utf-8", errors="replace")
if err_text.strip():
    print("\n=== STDERR ===")
    print(err_text[:2000])

c.close()
print("\n[OK] 完成")
