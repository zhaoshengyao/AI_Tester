#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""上传修复文件到服务器并重跑失败的测试"""
import paramiko
import os
import time
import re

HOST = "192.168.2.70"
PORT = 22
USER = "root"
PASSWORD = "Zw@123qwe"
REMOTE_BASE = "/home/zhiwei/AutoTestHub"

# 需要上传的文件列表（本地路径 -> 远程路径）
FILES = [
    # 之前修复的脚本
    (
        r"d:\AICode\TestHub\AITestDemo\scripts\run-security-tests.sh",
        f"{REMOTE_BASE}/scripts/run-security-tests.sh"
    ),
    (
        r"d:\AICode\TestHub\AITestDemo\scripts\run-full-test-flow.sh",
        f"{REMOTE_BASE}/scripts/run-full-test-flow.sh"
    ),
    (
        r"d:\AICode\TestHub\AITestDemo\scripts\run-perf-tests.sh",
        f"{REMOTE_BASE}/scripts/run-perf-tests.sh"
    ),
    # 之前修复的代码
    (
        r"d:\AICode\TestHub\AITestDemo\tests\performance\locust\utils\crm_helpers.py",
        f"{REMOTE_BASE}/tests/performance/locust/utils/crm_helpers.py"
    ),
    # 本轮新增修复 - API 数据一致性
    (
        r"d:\AICode\TestHub\AITestDemo\tests\api\testsuites\crm\test_data_consistency.py",
        f"{REMOTE_BASE}/tests/api/testsuites/crm/test_data_consistency.py"
    ),
    # 本轮新增修复 - API 工作流 ID 关联
    (
        r"d:\AICode\TestHub\AITestDemo\tests\api\testsuites\crm\test_crm_workflow.py",
        f"{REMOTE_BASE}/tests/api/testsuites/crm/test_crm_workflow.py"
    ),
    # 本轮新增修复 - 性能 Token 刷新 + 安全加密
    (
        r"d:\AICode\TestHub\AITestDemo\tests\performance\locust\utils\auth_helper.py",
        f"{REMOTE_BASE}/tests/performance/locust/utils/auth_helper.py"
    ),
    # 本轮新增修复 - 性能全量压测 Token 刷新
    (
        r"d:\AICode\TestHub\AITestDemo\tests\performance\locust\api\locustfile_crm_api.py",
        f"{REMOTE_BASE}/tests/performance/locust/api/locustfile_crm_api.py"
    ),
    # 本轮新增修复 - 性能冒烟 Token 刷新
    (
        r"d:\AICode\TestHub\AITestDemo\tests\performance\locust\api\locustfile_smoke.py",
        f"{REMOTE_BASE}/tests/performance/locust/api/locustfile_smoke.py"
    ),
    # 本轮新增修复 - 安全扫描器
    (
        r"d:\AICode\TestHub\AITestDemo\tests\security\scanner\security_scanner.py",
        f"{REMOTE_BASE}/tests/security/scanner/security_scanner.py"
    ),
]

def get_ssh():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
    c.get_transport().set_keepalive(30)
    return c

def run(client, cmd, timeout=60):
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    try: out = stdout.read().decode("utf-8", errors="replace")
    except: out = ""
    try: err = stderr.read().decode("utf-8", errors="replace")
    except: err = ""
    return out, err

def clean(s):
    return re.sub(r'\x1b\[[0-9;]*m', '', s)

def main():
    print("=" * 60)
    print("[1] 建立 SSH 连接")
    print("=" * 60)
    client = get_ssh()
    print("OK")

    # 上传文件
    print("\n" + "=" * 60)
    print("[2] 上传修复文件")
    print("=" * 60)

    sftp = client.open_sftp()
    for local_path, remote_path in FILES:
        try:
            sftp.put(local_path, remote_path)
            print(f"  ✅ {os.path.basename(local_path)}")
        except Exception as e:
            print(f"  ❌ {os.path.basename(local_path)}: {e}")
    sftp.close()

    # 设置执行权限
    for script in ["run-security-tests.sh", "run-full-test-flow.sh", "run-perf-tests.sh"]:
        run(client, f"chmod +x {REMOTE_BASE}/scripts/{script}")

    # 创建 results 目录
    run(client, f"mkdir -p {REMOTE_BASE}/tests/performance/locust/results")
    print("  ✅ 创建 results 目录")

    # 验证上传结果
    print("\n" + "=" * 60)
    print("[3] 验证上传结果")
    print("=" * 60)

    # 验证 run-security-tests.sh 修复
    out, _ = run(client, f"grep 'scanner.run()' {REMOTE_BASE}/scripts/run-security-tests.sh")
    if "scanner.run()" in out:
        print("  ✅ run-security-tests.sh: 已使用 scanner.run()")
    else:
        print("  ❌ run-security-tests.sh: 仍使用旧方法")

    # 验证 run-perf-tests.sh 修复
    out, _ = run(client, f"grep 'mkdir -p results' {REMOTE_BASE}/scripts/run-perf-tests.sh")
    if "mkdir -p results" in out:
        print("  ✅ run-perf-tests.sh: 已包含 results 目录创建")
    else:
        print("  ❌ run-perf-tests.sh: 缺少 results 目录创建")

    # 验证 crm_helpers.py 修复
    out, _ = run(client, f"grep 'AssertionError' {REMOTE_BASE}/tests/performance/locust/utils/crm_helpers.py")
    if "AssertionError" in out:
        print("  ✅ crm_helpers.py: assert_api_success 已改为抛出异常")
    else:
        print("  ❌ crm_helpers.py: 仍使用 response.failure")

    # 验证 API 数据一致性修复
    out, _ = run(client, f"grep 'total_clues <= 1000' {REMOTE_BASE}/tests/api/testsuites/crm/test_data_consistency.py")
    if "total_clues <= 1000" in out:
        print("  ✅ test_data_consistency.py: 已修复硬编码预期值")
    else:
        print("  ❌ test_data_consistency.py: 仍使用硬编码预期值")

    # 验证 API 工作流 ID 关联修复
    out, _ = run(client, f"grep 'str(business_data.get' {REMOTE_BASE}/tests/api/testsuites/crm/test_crm_workflow.py")
    if "str(business_data.get" in out:
        print("  ✅ test_crm_workflow.py: 已修复 ID 类型比较")
    else:
        print("  ❌ test_crm_workflow.py: 仍使用直接比较")

    # 验证 auth_helper.py 修复
    out, _ = run(client, f"grep 'encrypt_password' {REMOTE_BASE}/tests/performance/locust/utils/auth_helper.py")
    if "encrypt_password" in out:
        print("  ✅ auth_helper.py: 已导出 encrypt_password")
    else:
        print("  ❌ auth_helper.py: 缺少 encrypt_password")

    # 验证 locustfile Token 刷新修复
    out, _ = run(client, f"grep '_ensure_token' {REMOTE_BASE}/tests/performance/locust/api/locustfile_crm_api.py")
    if "_ensure_token" in out:
        print("  ✅ locustfile_crm_api.py: 已添加 Token 刷新机制")
    else:
        print("  ❌ locustfile_crm_api.py: 缺少 Token 刷新机制")

    # 验证安全扫描器
    out, _ = run(client, f"grep 'encrypt_password' {REMOTE_BASE}/tests/security/scanner/security_scanner.py")
    if "encrypt_password" in out:
        print("  ✅ security_scanner.py: 已使用 encrypt_password")
    else:
        print("  ❌ security_scanner.py: 缺少 encrypt_password 引用")

    # 验证 results 目录
    out, _ = run(client, f"test -d {REMOTE_BASE}/tests/performance/locust/results && echo EXISTS || echo MISSING")
    if "EXISTS" in out:
        print("  ✅ results 目录已存在")
    else:
        print("  ❌ results 目录不存在")

    # 清理旧的 full-test-flow.log
    run(client, f"rm -f {REMOTE_BASE}/full-test-flow.log")

    print("\n" + "=" * 60)
    print("[4] 启动全流程测试（后台）")
    print("=" * 60)

    # 使用 setsid 启动后台进程
    start_cmd = (
        f"cd {REMOTE_BASE} && "
        f"(setsid bash scripts/run-full-test-flow.sh > {REMOTE_BASE}/full-test-flow.log 2>&1 < /dev/null &) ; "
        f"sleep 2 ; "
        f"pgrep -f 'run-full-test-flow' | head -1"
    )
    out, _ = run(client, start_cmd, timeout=20)
    pid = out.strip()

    if pid and pid.isdigit():
        print(f"  ✅ 测试已启动, PID={pid}")
    else:
        print("  ❌ 测试启动失败")
        out2, _ = run(client, f"head -20 {REMOTE_BASE}/full-test-flow.log 2>/dev/null")
        print(clean(out2))
        client.close()
        return

    # 等待 30 秒后开始监控
    print("\n[5] 等待测试执行...")
    time.sleep(30)

    # 监控进度
    last_size = 0
    interval = 20
    max_wait = 2400  # 40 分钟
    waited = 0
    stage_announced = set()

    while waited < max_wait:
        try:
            out, _ = run(client, f"pgrep -f 'run-full-test-flow' 2>/dev/null || echo DEAD", timeout=10)
            alive = "DEAD" not in out

            out, _ = run(client, f"wc -c < {REMOTE_BASE}/full-test-flow.log 2>/dev/null || echo 0", timeout=10)
            try: current_size = int(out.strip())
            except: current_size = 0

            if current_size > last_size:
                out, _ = run(client, f"tail -c +{last_size + 1} {REMOTE_BASE}/full-test-flow.log 2>/dev/null", timeout=15)
                new_content = clean(out)
                last_size = current_size

                for line in new_content.split("\n"):
                    ls = line.strip()
                    if ls and len(ls) < 200:
                        if any(kw in ls for kw in [
                            "Step ", "==== ", "[OK]", "[ERROR]", "[WARN]",
                            "✅", "❌", "通过", "失败", "passed", "failed",
                            "Vulnerabilities", "Duration", "全流程", "批次ID",
                            "执行概况", "API 冒烟", "UI 冒烟", "性能", "安全",
                            "系统测试报告", "批次摘要"
                        ]):
                            ts = time.strftime("%H:%M:%S")
                            print(f"  [{ts}] {ls}")

                if "全流程执行完成" in new_content:
                    print("\n[INFO] 全流程测试执行完成！")
                    break

            if not alive:
                print(f"\n[INFO] 测试进程已退出")
                out, _ = run(client, f"tail -50 {REMOTE_BASE}/full-test-flow.log 2>/dev/null", timeout=15)
                print(clean(out))
                break

        except Exception as e:
            print(f"[WARN] 异常: {e}")
            try: client.close()
            except: pass
            time.sleep(5)
            try: client = get_ssh()
            except: time.sleep(10)

        time.sleep(interval)
        waited += interval

    # 获取最终结果
    print("\n" + "=" * 60)
    print("[6] 获取最终结果")
    print("=" * 60)

    client.close()
    client = get_ssh()

    # 查找最新批次
    out, _ = run(client, f"ls -dt {REMOTE_BASE}/docs/test-runs/*/ 2>/dev/null | head -1")
    batch_dir = out.strip()
    if batch_dir:
        print(f"  批次目录: {batch_dir}")

        # 系统测试报告
        out, _ = run(client, f"cat '{batch_dir}reports/系统测试报告.md' 2>/dev/null || echo NOT_FOUND")
        if out.strip() != "NOT_FOUND":
            print("\n--- 系统测试报告 ---")
            print(clean(out))

        # 批次摘要
        out, _ = run(client, f"cat '{batch_dir}批次摘要.md' 2>/dev/null || echo NOT_FOUND")
        if out.strip() != "NOT_FOUND":
            print("\n--- 批次摘要 ---")
            print(clean(out))

        # 检查性能日志
        out, _ = run(client, f"ls -la {batch_dir}raw/perf-*.log 2>/dev/null")
        if out:
            print("\n--- 性能日志 ---")
            print(out)

        # 检查安全日志
        out, _ = run(client, f"cat {batch_dir}raw/security.log 2>/dev/null | head -30")
        if out:
            print("\n--- 安全日志 ---")
            print(clean(out))

    # 最后查看日志尾部
    print("\n--- 执行日志最后 30 行 ---")
    out, _ = run(client, f"tail -30 {REMOTE_BASE}/full-test-flow.log 2>/dev/null")
    print(clean(out))

    client.close()
    print("\n[INFO] 全部完成")


if __name__ == "__main__":
    main()
