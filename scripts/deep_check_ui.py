#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""深度检查 UI 全量测试状态"""
import paramiko, time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("192.168.2.70", 22, "root", "Zw@123qwe", timeout=15)
r = lambda cmd: c.exec_command(cmd, timeout=30)[1].read().decode("utf-8", "replace")

# 1. Playwright/npm/node 进程
print("=== playwright 相关进程 ===")
print(r("pgrep -af 'playwright|npm exec|workerProcessEntry' 2>/dev/null | grep -v pgrep"))

# 2. chrome-headless-shell 进程
print("\n=== chrome-headless-shell 进程数 ===")
print(r("pgrep -c chrome-headless-shell 2>/dev/null || echo 0").strip())

# 3. 最近 30 秒文件活动
print("\n=== 最近 30 秒 test-results 文件活动 ===")
cnt = r("find /home/zhiwei/AutoTestHub/tests/ui/test-results/ -type f -mmin -0.5 2>/dev/null | wc -l").strip()
print(f"{cnt} 个文件在最近 30 秒内修改")

# 4. 最新文件时间
print("\n=== 最新文件 ===")
print(r("find /home/zhiwei/AutoTestHub/tests/ui/test-results/ -type f -printf '%T+ %p\\n' 2>/dev/null | sort -r | head -3"))

# 5. 当前时间
print("\n=== 服务器当前时间 ===")
print(r("date '+%Y-%m-%d %H:%M:%S'").strip())

# 6. 检查 playwright 是否有输出到其他地方（如 stderr）
print("\n=== ui-full.log 大小 ===")
print(r("ls -la /home/zhiwei/AutoTestHub/docs/test-runs/20260806-093518/raw/ui-full.log 2>/dev/null"))

# 7. 检查 playwright JSON 报告是否已生成（表示测试完成）
print("\n=== test-results.json 是否存在 ===")
print(r("ls -la /home/zhiwei/AutoTestHub/tests/ui/test-results.json 2>/dev/null || echo '不存在（测试未完成）'"))

# 8. 检查 HTML 报告是否在生成
print("\n=== playwright-report 目录 ===")
print(r("ls -la /home/zhiwei/AutoTestHub/tests/ui/playwright-report/ 2>/dev/null || echo '不存在'"))

c.close()