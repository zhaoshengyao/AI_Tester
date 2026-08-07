#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""获取最终报告内容"""
import paramiko
import re

HOST = "192.168.2.70"
PORT = 22
USER = "root"
PASSWORD = "Zw@123qwe"

def get_ssh():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
    return c

def run(client, cmd, timeout=30):
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    try: out = stdout.read().decode("utf-8", errors="replace")
    except: out = ""
    try: err = stderr.read().decode("utf-8", errors="replace")
    except: err = ""
    return out, err

def clean(s):
    return re.sub(r'\x1b\[[0-9;]*m', '', s)

def main():
    client = get_ssh()
    
    batch_id = "20260805-141436"
    base = f"/home/zhiwei/AutoTestHub/docs/test-runs/{batch_id}"
    
    # 系统测试报告
    print("=" * 60)
    print("【系统测试报告】")
    print("=" * 60)
    out, err = run(client, f"cat '{base}/reports/系统测试报告.md' 2>/dev/null || echo NOT_FOUND")
    if out.strip() == "NOT_FOUND":
        print("❌ 系统测试报告未生成")
    else:
        print(clean(out))
    
    # 批次摘要
    print("\n" + "=" * 60)
    print("【批次摘要】")
    print("=" * 60)
    out, _ = run(client, f"cat '{base}/批次摘要.md' 2>/dev/null || echo NOT_FOUND")
    print(clean(out))
    
    # 检查报告目录
    print("\n" + "=" * 60)
    print("【报告文件列表】")
    print("=" * 60)
    out, _ = run(client, f"find {base} -type f -name '*.md' -o -name '*.html' -o -name '*.log' | sort")
    print(out)
    
    # 安全扫描报告
    print("\n" + "=" * 60)
    print("【安全扫描报告摘要】")
    print("=" * 60)
    out, _ = run(client, f"cat /home/zhiwei/AutoTestHub/tests/security/reports/security-report-20260805-143225.md 2>/dev/null | head -50")
    print(clean(out))

    # 性能冒烟结果
    print("\n" + "=" * 60)
    print("【性能冒烟结果】")
    print("=" * 60)
    out, _ = run(client, f"cat {base}/raw/perf-smoke.log 2>/dev/null | grep -E 'Vulnerabilities|Duration|Requests|Failures|Avg|Min|Max' | head -20")
    print(out)
    
    client.close()

if __name__ == "__main__":
    main()
