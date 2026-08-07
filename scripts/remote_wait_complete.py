#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""等待测试完成并获取最终结果"""
import paramiko
import time
import re
import sys

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
    try: out = stdout.read().decode("utf-8", errors="replace")
    except: out = ""
    try: err = stderr.read().decode("utf-8", errors="replace")
    except: err = ""
    return out, err

def clean(s):
    return re.sub(r'\x1b\[[0-9;]*m', '', s)

def main():
    client = get_ssh()
    last_size = 0
    interval = 20
    max_wait = 2400  # 40 分钟
    waited = 0

    print("[INFO] 等待全流程测试完成...")
    print(f"[INFO] 检查间隔: {interval}s, 最大等待: {max_wait//60}分钟")
    print()

    while waited < max_wait:
        try:
            # 检查进程
            out, _ = run(client, "pgrep -f 'run-full-test-flow' 2>/dev/null || echo DEAD", timeout=10)
            alive = "DEAD" not in out

            # 日志大小
            out, _ = run(client, f"wc -c < {LOG_FILE} 2>/dev/null || echo 0", timeout=10)
            try: current_size = int(out.strip())
            except: current_size = 0

            # 读取新增
            if current_size > last_size:
                out, _ = run(client, f"tail -c +{last_size + 1} {LOG_FILE} 2>/dev/null", timeout=15)
                new_content = clean(out)
                last_size = current_size

                for line in new_content.split("\n"):
                    ls = line.strip()
                    if not ls or len(ls) > 200:
                        continue
                    if any(kw in ls for kw in ["Step ", "====", "[OK]", "[ERROR]", "[WARN]", "❌", "✅", "失败", "通过", "passed", "failed", "总计", "Vulnerabilities", "Duration", "全流程", "批次ID"]):
                        ts = time.strftime("%H:%M:%S")
                        print(f"[{ts}] {ls}")

                if "全流程执行完成" in new_content:
                    print("\n[INFO] 全流程测试已完成！")
                    break

            if not alive:
                print(f"\n[INFO] 测试进程已退出 (日志大小: {current_size} bytes)")
                # 读取最后部分
                out, _ = run(client, f"tail -40 {LOG_FILE} 2>/dev/null", timeout=15)
                print(clean(out))
                break

        except Exception as e:
            print(f"[WARN] 异常: {e}, 重连...")
            try: client.close()
            except: pass
            time.sleep(5)
            try: client = get_ssh()
            except: time.sleep(10)

        time.sleep(interval)
        waited += interval

    # 获取最终报告
    print("\n" + "=" * 60)
    print("[INFO] 获取最终报告")
    print("=" * 60)

    try:
        client.close()
    except: pass
    client = get_ssh()

    out, _ = run(client, f"ls -dt {DEPLOY_DIR}/docs/test-runs/*/ 2>/dev/null | head -1")
    batch_dir = out.strip()
    if batch_dir:
        print(f"[INFO] 批次: {batch_dir}")

        # 系统测试报告
        out, _ = run(client, f"cat '{batch_dir}reports/系统测试报告.md' 2>/dev/null || echo MISSING")
        if out.strip() != "MISSING":
            print("\n--- 系统测试报告 ---")
            print(clean(out))
        else:
            print("[WARN] 系统测试报告未生成")

        # 批次摘要
        out, _ = run(client, f"cat '{batch_dir}批次摘要.md' 2>/dev/null || echo MISSING")
        if out.strip() != "MISSING":
            print("\n--- 批次摘要 ---")
            print(clean(out))

        # 原始日志
        out, _ = run(client, f"ls -la {batch_dir}raw/ 2>/dev/null")
        print("\n--- 原始日志文件 ---")
        print(out)

    # 日志最后 60 行
    print("\n--- 执行日志最后 60 行 ---")
    out, _ = run(client, f"tail -60 {LOG_FILE} 2>/dev/null")
    print(clean(out))

    client.close()

if __name__ == "__main__":
    main()
