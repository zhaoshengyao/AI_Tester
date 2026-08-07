#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""诊断服务器上测试中断的原因"""
import paramiko
import re

HOST = "192.168.2.70"
PORT = 22
USER = "root"
PASSWORD = "Zw@123qwe"
DEPLOY_DIR = "/home/zhiwei/AutoTestHub"
LOG_FILE = f"{DEPLOY_DIR}/full-test-flow.log"

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
    try:
        err = stderr.read().decode("utf-8", errors="replace")
    except Exception:
        err = ""
    return out, err

def clean(s):
    """过滤 ANSI 颜色码"""
    return re.sub(r'\x1b\[[0-9;]*m', '', s)

def main():
    client = get_ssh()

    print("=" * 60)
    print("[1] 检查测试进程状态")
    print("=" * 60)
    out, _ = run(client, "pgrep -af 'run-full-test|playwright|locust' 2>/dev/null || echo NONE")
    print(out)

    print("=" * 60)
    print("[2] 检查最近退出码和 dmesg")
    print("=" * 60)
    out, _ = run(client, "echo 'Last exit code: '$?")
    print(out)

    print("=" * 60)
    print("[3] 检查批次目录内容")
    print("=" * 60)
    out, _ = run(client, f"ls -laR {DEPLOY_DIR}/docs/test-runs/20260805-113810/ 2>/dev/null || echo MISSING")
    print(out)

    print("=" * 60)
    print("[4] 检查 UI 测试目录")
    print("=" * 60)
    out, _ = run(client, f"ls -la {DEPLOY_DIR}/tests/ui/playwright-report/ 2>/dev/null; echo '---'; ls -la {DEPLOY_DIR}/tests/ui/test-results/ 2>/dev/null; echo '---'; ls -la {DEPLOY_DIR}/tests/ui/.auth/ 2>/dev/null")
    print(out)

    print("=" * 60)
    print("[5] 完整日志行数统计")
    print("=" * 60)
    out, _ = run(client, f"wc -l {LOG_FILE}")
    print(out)

    print("=" * 60)
    print("[6] 日志中的 Step 标记")
    print("=" * 60)
    out, _ = run(client, f"grep -n 'Step\\|====\\|全流程\\|ERROR\\|FAIL\\|失败\\|通过' {LOG_FILE} 2>/dev/null | head -60")
    print(clean(out))

    print("=" * 60)
    print("[7] 日志最后 30 行")
    print("=" * 60)
    out, _ = run(client, f"tail -30 {LOG_FILE}")
    print(clean(out))

    print("=" * 60)
    print("[8] 检查 run-full-test-flow.sh 的 set -e 问题")
    print("=" * 60)
    out, _ = run(client, f"head -10 {DEPLOY_DIR}/scripts/run-full-test-flow.sh")
    print(out)

    print("=" * 60)
    print("[9] 手动测试 UI 全量（dry run 收集）")
    print("=" * 60)
    out, _ = run(client, f"cd {DEPLOY_DIR}/tests/ui && npx playwright test --list 2>&1 | tail -30", timeout=30)
    print(clean(out))

    print("=" * 60)
    print("[10] 检查 Playwright 进程是否 OOM")
    print("=" * 60)
    out, _ = run(client, "dmesg | grep -i 'oom\\|killed' | tail -10 2>/dev/null || echo NONE")
    print(out)

    client.close()

if __name__ == "__main__":
    main()
