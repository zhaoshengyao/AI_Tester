#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""同步更新后的脚本到服务器"""
import paramiko

HOST = "192.168.2.70"
PORT = 22
USER = "root"
PASSWORD = "Zw@123qwe"
REMOTE_BASE = "/home/zhiwei/AutoTestHub"

LOCAL_SCRIPT = r"d:\AICode\TestHub\AITestDemo\scripts\run-full-test-flow.sh"
REMOTE_SCRIPT = REMOTE_BASE + "/scripts/run-full-test-flow.sh"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)

# 上传脚本
sftp = c.open_sftp()
sftp.put(LOCAL_SCRIPT, REMOTE_SCRIPT)
sftp.close()
print(f"✅ 已上传: scripts/run-full-test-flow.sh")

# 设置执行权限
_, stdout, stderr = c.exec_command(f"chmod +x {REMOTE_SCRIPT}")
print("✅ 已设置执行权限")

# 验证服务器当前批次文件结构
_, stdout, stderr = c.exec_command(f"ls -la {REMOTE_BASE}/docs/test-runs/20260805-175516/")
print("\n当前批次根目录:")
print(stdout.read().decode())

_, stdout, stderr = c.exec_command(f"ls -la {REMOTE_BASE}/docs/test-runs/20260805-175516/reports/")
print("reports/:")
print(stdout.read().decode())

_, stdout, stderr = c.exec_command(f"ls -la {REMOTE_BASE}/docs/test-runs/20260805-175516/defects/")
print("defects/:")
print(stdout.read().decode())

_, stdout, stderr = c.exec_command(f"ls -la {REMOTE_BASE}/docs/test-runs/20260805-175516/stage-status/ | head -20")
print("stage-status/:")
print(stdout.read().decode())

c.close()
print("\n✅ 同步完成")