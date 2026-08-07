#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查服务器上测试进度并获取结果"""
import paramiko
import time
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
    try:
        out = stdout.read().decode("utf-8", errors="replace")
    except Exception:
        out = ""
    try:
        err = stderr.read().decode("utf-8", errors="replace")
    except Exception:
        err = ""
    return out, err

def main():
    client = get_ssh()

    # 1. 检查测试进程是否还在运行
    out, _ = run(client, "pgrep -f 'run-full-test-flow' || echo DEAD")
    pid = out.strip()
    if pid == "DEAD" or not pid:
        print("[INFO] 测试进程已结束")
        process_alive = False
    else:
        print(f"[INFO] 测试进程仍在运行, PID={pid}")
        process_alive = True

    # 2. 检查日志大小和最后部分
    out, _ = run(client, f"wc -l < {LOG_FILE} 2>/dev/null || echo 0")
    log_lines = out.strip()
    print(f"[INFO] 日志行数: {log_lines}")

    # 3. 读取日志最后 100 行
    out, _ = run(client, f"tail -100 {LOG_FILE} 2>/dev/null")
    print("\n--- 日志最后 100 行 ---")
    print(out)

    # 4. 检查阶段完成情况
    stages_found = []
    for line in out.split("\n"):
        for step in ["Step 1", "Step 2", "Step 3", "Step 4", "Step 5", "Step 6", "Step 7", "Step 8"]:
            if step in line and "进入阶段" not in line:
                pass
        if "全流程执行完成" in line:
            stages_found.append("DONE")

    # 5. 如果进程仍在运行，等待并轮询
    if process_alive:
        print("\n[INFO] 测试仍在运行，开始轮询等待...")
        last_size = 0
        for i in range(120):  # 最多等待 30 分钟 (120 * 15s)
            time.sleep(15)
            try:
                # 检查进程
                out, _ = run(client, "pgrep -f 'run-full-test-flow' || echo DEAD", timeout=10)
                if "DEAD" in out:
                    print(f"\n[INFO] 测试进程已退出")
                    break

                # 读取新增日志
                out, _ = run(client, f"wc -c < {LOG_FILE} 2>/dev/null || echo 0", timeout=10)
                try:
                    current_size = int(out.strip())
                except ValueError:
                    current_size = 0

                if current_size > last_size:
                    out, _ = run(client, f"tail -c +{last_size + 1} {LOG_FILE} 2>/dev/null", timeout=10)
                    new_content = out
                    last_size = current_size

                    for line in new_content.split("\n"):
                        line_s = line.strip()
                        if any(kw in line_s for kw in ["Step ", "全流程", "[OK]", "[ERROR]", "[WARN]", "❌", "✅", "失败", "通过", "总计", "Vulnerabilities", "Duration"]):
                            if len(line_s) < 200 and line_s:
                                # 过滤 ANSI 颜色码
                                import re
                                clean = re.sub(r'\x1b\[[0-9;]*m', '', line_s)
                                print(f"  | {clean}")

                if "全流程执行完成" in new_content if 'new_content' in dir() else False:
                    print("\n[INFO] 测试流程已完成！")
                    break
            except Exception as e:
                print(f"[WARN] 轮询异常: {e}，重连...")
                try:
                    client.close()
                except Exception:
                    pass
                time.sleep(5)
                try:
                    client = get_ssh()
                except Exception as e2:
                    print(f"[ERROR] 重连失败: {e2}")
                    time.sleep(10)

    # 6. 获取最终报告
    print("\n" + "=" * 60)
    print("[INFO] 获取最终测试报告")
    print("=" * 60)

    # 查找最新批次
    out, _ = run(client, f"ls -dt {DEPLOY_DIR}/docs/test-runs/*/ 2>/dev/null | head -1")
    batch_dir = out.strip()
    if batch_dir:
        print(f"[INFO] 批次目录: {batch_dir}")

        # 系统测试报告
        out, _ = run(client, f"cat '{batch_dir}reports/系统测试报告.md' 2>/dev/null || echo MISSING")
        if out.strip() != "MISSING":
            print("\n--- 系统测试报告 ---")
            print(out)
        else:
            print("[WARN] 系统测试报告尚未生成")

        # 批次摘要
        out, _ = run(client, f"cat '{batch_dir}批次摘要.md' 2>/dev/null || echo MISSING")
        if out.strip() != "MISSING":
            print("\n--- 批次摘要 ---")
            print(out)

        # 列出 raw 目录下的日志
        out, _ = run(client, f"ls -la {batch_dir}raw/ 2>/dev/null || echo NONE")
        if out.strip() != "NONE":
            print("\n--- 原始日志文件 ---")
            print(out)

    # 7. 最终日志尾部
    print("\n--- 执行日志最后 60 行 ---")
    out, _ = run(client, f"tail -60 {LOG_FILE} 2>/dev/null")
    print(out)

    client.close()

if __name__ == "__main__":
    main()
