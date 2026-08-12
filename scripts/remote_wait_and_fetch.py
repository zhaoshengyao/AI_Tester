#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""等待服务器端全流程测试完成，并获取最终报告"""
import paramiko
import re
import time
import sys

HOST = "192.168.2.70"
PORT = 22
USER = "root"
PASSWORD = "Zw@123qwe"
DEPLOY_DIR = "/home/zhiwei/AutoTestHub"
BATCH_ID = "20260811-091728-crm-0cee4e94"
BATCH_DIR = f"{DEPLOY_DIR}/projects/crm/test-runs/{BATCH_ID}"


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


def fetch_file(client, remote_path, local_path):
    """通过 SFTP 下载文件"""
    try:
        sftp = client.open_sftp()
        sftp.get(remote_path, local_path)
        sftp.close()
        return True
    except Exception as e:
        print(f"[WARN] 下载失败 {remote_path}: {e}")
        return False


def main():
    print("=" * 60)
    print(f"[INFO] 等待批次 {BATCH_ID} 完成")
    print("=" * 60)

    client = get_ssh()

    # 轮询等待测试完成
    max_wait = 1200  # 最大等待 20 分钟
    waited = 0
    interval = 20

    while waited < max_wait:
        # 检查 run-full-test 进程是否还在
        out = run(client, "pgrep -f 'run-full-test-flow' 2>/dev/null || echo DEAD")
        is_alive = out.strip() != "DEAD"

        # 检查批次摘要是否生成（Step 8 完成的标志）
        out = run(client, f"test -f {BATCH_DIR}/批次摘要.md && echo EXISTS || echo MISSING")
        summary_exists = "EXISTS" in out

        # 检查系统测试报告
        out = run(client, f"test -f {BATCH_DIR}/reports/系统测试报告.md && echo EXISTS || echo MISSING")
        report_exists = "EXISTS" in out

        ts = time.strftime("%H:%M:%S")
        print(f"[{ts}] 进程存活: {is_alive} | 批次摘要: {summary_exists} | 系统报告: {report_exists} | 已等待 {waited}s")

        if not is_alive and (summary_exists or report_exists):
            print(f"[OK] 测试已完成，等待最后 5 秒确保文件写完...")
            time.sleep(5)
            break

        if not is_alive and not summary_exists and not report_exists:
            # 进程退出但没有生成报告，可能异常
            print(f"[WARN] 进程已退出但未生成报告，检查日志...")
            out = run(client, f"ls -la {BATCH_DIR}/reports/ 2>/dev/null")
            print(out)
            break

        time.sleep(interval)
        waited += interval

        # 重连（防止连接断开）
        if waited % 180 == 0:
            try:
                client.close()
            except Exception:
                pass
            try:
                client = get_ssh()
                print(f"[OK] SSH 重连成功")
            except Exception as e:
                print(f"[WARN] 重连失败: {e}")
                time.sleep(10)
                client = get_ssh()

    print("\n" + "=" * 60)
    print("[INFO] 测试结束，获取最终结果")
    print("=" * 60)

    # 1. 列出批次目录最终结构
    print("\n=== [1] 批次目录最终结构 ===")
    out = run(client, f"find {BATCH_DIR} -maxdepth 3 -printf '%y %p\\n' 2>/dev/null | sort")
    print(out)

    # 2. 阶段状态
    print("\n=== [2] 阶段状态文件 ===")
    out = run(client, f"ls -la {BATCH_DIR}/stage-status/ 2>/dev/null && echo '---' && for f in {BATCH_DIR}/stage-status/*.json; do echo \"--- $(basename $f) ---\"; cat \"$f\" 2>/dev/null; echo; done")
    print(out)

    # 3. 报告列表
    print("\n=== [3] reports/ 目录 ===")
    out = run(client, f"ls -la {BATCH_DIR}/reports/ 2>/dev/null")
    print(out)

    # 4. 系统测试报告
    print("\n=== [4] 系统测试报告内容 ===")
    out = run(client, f"cat {BATCH_DIR}/reports/系统测试报告.md 2>/dev/null || echo NOT_FOUND")
    print(clean(out))

    # 5. 批次摘要
    print("\n=== [5] 批次摘要内容 ===")
    out = run(client, f"cat {BATCH_DIR}/批次摘要.md 2>/dev/null || echo NOT_FOUND")
    print(clean(out))

    # 6. 下载报告到本地
    print("\n=== [6] 下载报告到本地 ===")
    import os
    local_batch_dir = f"d:/AICode/TestHub/AITestDemo/projects/crm/test-runs/{BATCH_ID}"
    os.makedirs(local_batch_dir + "/reports", exist_ok=True)

    files_to_download = [
        (f"{BATCH_DIR}/reports/系统测试报告.md", f"{local_batch_dir}/reports/系统测试报告.md"),
        (f"{BATCH_DIR}/批次摘要.md", f"{local_batch_dir}/批次摘要.md"),
        (f"{BATCH_DIR}/reports/测试覆盖矩阵.md", f"{local_batch_dir}/reports/测试覆盖矩阵.md"),
        (f"{BATCH_DIR}/reports/全流程测试报告.md", f"{local_batch_dir}/reports/全流程测试报告.md"),
    ]

    for remote, local in files_to_download:
        if fetch_file(client, remote, local):
            print(f"[OK] 已下载: {os.path.basename(local)}")
        else:
            print(f"[SKIP] 不存在或下载失败: {os.path.basename(remote)}")

    client.close()
    print("\n[OK] 全部完成")


if __name__ == "__main__":
    main()
