#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""清除服务器历史测试数据并重新执行全流程"""
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

def run_cmd(client, cmd, timeout=120):
    print(f"\n[执行] {cmd[:100]}...")
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    if out.strip():
        print(out[-3000:] if len(out) > 3000 else out)
    if err.strip():
        print(f"[错误] {err[-1000:]}")
    return out, err

# 连接服务器
print("=" * 60)
print("连接服务器...")
client = get_ssh()
print("✅ 已连接")

# ========== 步骤1: 清除历史数据 ==========
print("\n" + "=" * 60)
print("步骤1: 清除历史测试数据")
print("=" * 60)

# 清除 docs/test-runs/ 下所有历史批次
run_cmd(client, f"rm -rf {REMOTE_BASE}/docs/test-runs/* 2>/dev/null; echo '已清除测试运行记录'")

# 清除测试报告
run_cmd(client, f"rm -rf {REMOTE_BASE}/docs/reports/*.md 2>/dev/null; echo '已清除历史报告'")

# 清除 Locust HTML 报告
run_cmd(client, f"find {REMOTE_BASE}/tests/performance/ -name '*.html' -type f -delete 2>/dev/null; echo '已清除性能测试HTML报告'")

# 清除性能测试原始结果
run_cmd(client, f"rm -rf {REMOTE_BASE}/tests/performance/locust/results* 2>/dev/null; echo '已清除性能测试结果'")

# 清除 API 测试报告
run_cmd(client, f"find {REMOTE_BASE}/tests/api/ -name '*.html' -o -name '*.xml' -o -name 'reports' -type d -exec rm -rf {{}} + 2>/dev/null; echo '已清除API测试报告'")

# 清除 UI 测试报告
run_cmd(client, f"find {REMOTE_BASE}/tests/ui/ -name 'playwright-report' -type d -exec rm -rf {{}} + 2>/dev/null; find {REMOTE_BASE}/tests/ui/ -name 'test-results' -type d -exec rm -rf {{}} + 2>/dev/null; echo '已清除UI测试报告'")

# 清除安全测试结果
run_cmd(client, f"find {REMOTE_BASE}/tests/security/ -name '*.html' -o -name '*.json' -o -name 'reports' -type d -exec rm -rf {{}} + 2>/dev/null; echo '已清除安全测试结果'")

# 清除 Python 缓存
run_cmd(client, f"find {REMOTE_BASE}/tests/ -name '__pycache__' -type d -exec rm -rf {{}} + 2>/dev/null; echo '已清除Python缓存'")

print("\n✅ 历史数据清除完成!")

# 验证清理结果
print("\n[验证] 检查清理结果:")
run_cmd(client, f"ls {REMOTE_BASE}/docs/test-runs/ 2>/dev/null | wc -l")

# ========== 步骤2: 执行全流程测试 ==========
print("\n" + "=" * 60)
print("步骤2: 执行全流程测试")
print("=" * 60)

# 执行全流程测试
run_cmd(
    client, 
    f"cd {REMOTE_BASE} && bash scripts/run-full-test-flow.sh 2>&1",
    timeout=1800  # 30分钟超时
)

# ========== 步骤3: 检查结果 ==========
print("\n" + "=" * 60)
print("步骤3: 检查测试结果")
print("=" * 60)

# 检查批次摘要
print("\n[检查] 批次摘要:")
run_cmd(
    client,
    f"cd {REMOTE_BASE} && find docs/test-runs/ -name '批次摘要.md' -exec cat {{}} \\; 2>/dev/null | head -50"
)

# 检查测试报告
print("\n[检查] 系统测试报告:")
run_cmd(
    client,
    f"cd {REMOTE_BASE} && find docs/test-runs/ -name '系统测试报告.md' -exec ls -la {{}} \\; 2>/dev/null"
)

# 检查缺陷清单
print("\n[检查] 缺陷清单:")
run_cmd(
    client,
    f"cd {REMOTE_BASE} && find docs/test-runs/ -name '缺陷清单.md' -exec head -20 {{}} \\; 2>/dev/null"
)

# 检查生成的报告文件
print("\n[检查] 生成的所有文件:")
run_cmd(
    client,
    f"cd {REMOTE_BASE} && find docs/test-runs/ -type f 2>/dev/null | sort"
)

client.close()
print("\n" + "=" * 60)
print("✅ 全流程测试执行完毕!")
print("=" * 60)