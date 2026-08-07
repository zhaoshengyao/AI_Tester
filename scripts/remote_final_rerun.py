#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""最终修复上传并重跑全流程"""
import paramiko
import os
import time
import re

HOST = "192.168.2.70"
PORT = 22
USER = "root"
PASSWORD = "Zw@123qwe"
REMOTE_BASE = "/home/zhiwei/AutoTestHub"

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

    # 上传修复后的 run-full-test-flow.sh
    print("\n[2] 上传修复文件")
    local_path = r"d:\AICode\TestHub\AITestDemo\scripts\run-full-test-flow.sh"
    remote_path = f"{REMOTE_BASE}/scripts/run-full-test-flow.sh"
    
    sftp = client.open_sftp()
    sftp.put(local_path, remote_path)
    sftp.close()
    run(client, f"chmod +x {remote_path}")
    print("  ✅ run-full-test-flow.sh 已上传")

    # 验证修复
    out, _ = run(client, f"grep 'API_FULL_STATUS=' {remote_path}")
    if "API_FULL_STATUS=" in out:
        print("  ✅ 已使用预计算变量方式")
    else:
        print("  ❌ 修复验证失败")
        client.close()
        return

    # 杀掉可能还在运行的旧进程
    run(client, f"pkill -f 'run-full-test-flow' 2>/dev/null; sleep 2")
    
    # 清理旧日志
    run(client, f"rm -f {REMOTE_BASE}/full-test-flow.log")

    # 启动新的全流程测试
    print("\n[3] 启动全流程测试")
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
        out2, _ = run(client, f"head -20 {REMOTE_BASE}/full-test-flow.log")
        print(clean(out2))
        client.close()
        return

    # 监控进度
    print("\n[4] 监控测试进度")
    time.sleep(20)
    
    last_size = 0
    waited = 0
    interval = 15
    max_wait = 2400

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
                            "系统测试报告", "批次摘要", "生成系统"
                        ]):
                            ts = time.strftime("%H:%M:%S")
                            print(f"  [{ts}] {ls}")

                if "全流程执行完成" in new_content:
                    print("\n[INFO] ✅ 全流程测试执行完成！")
                    break

            if not alive:
                print(f"\n[INFO] 测试进程已退出")
                break

        except Exception as e:
            print(f"[WARN] {e}")
            try: client.close()
            except: pass
            time.sleep(5)
            try: client = get_ssh()
            except: time.sleep(10)

        time.sleep(interval)
        waited += interval

    # 获取最终结果
    print("\n" + "=" * 60)
    print("[5] 获取最终结果")
    client.close()
    client = get_ssh()

    # 查找最新批次
    out, _ = run(client, f"ls -dt {REMOTE_BASE}/docs/test-runs/*/ 2>/dev/null | head -1")
    batch_dir = out.strip()
    if batch_dir:
        print(f"\n批次: {batch_dir}")
        
        # 系统测试报告
        out, _ = run(client, f"cat '{batch_dir}reports/系统测试报告.md' 2>/dev/null || echo NOT_FOUND")
        if out.strip() != "NOT_FOUND" and out.strip():
            print("\n--- 系统测试报告 ---")
            print(clean(out[:3000]))
        else:
            print("\n[WARN] 系统测试报告为空或未生成")

        # 批次摘要
        out, _ = run(client, f"cat '{batch_dir}批次摘要.md' 2>/dev/null || echo NOT_FOUND")
        if out.strip() != "NOT_FOUND":
            print("\n--- 批次摘要 ---")
            print(clean(out))

    # 最后日志
    print("\n--- 执行日志最后 40 行 ---")
    out, _ = run(client, f"tail -40 {REMOTE_BASE}/full-test-flow.log 2>/dev/null")
    print(clean(out))

    client.close()
    print("\n✅ 完成")

if __name__ == "__main__":
    main()
