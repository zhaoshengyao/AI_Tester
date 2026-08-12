#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""IPD 全流程测试远程执行脚本：git pull → 启动 API 流水线 → 轮询 → 下载报告。"""
import paramiko
import re
import time
import os
import sys

HOST = "192.168.2.70"
PORT = 22
USER = "root"
PASSWORD = "Zw@123qwe"
DEPLOY_DIR = "/home/zhiwei/AutoTestHub"
LOG_FILE = f"{DEPLOY_DIR}/ipd-full-test.log"
PID_FILE = f"{DEPLOY_DIR}/ipd-full-test.pid"

LOCAL_ROOT = "d:/AICode/TestHub/AITestDemo"

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
    return re.sub(r'\x1b\[[0-9;]*m', '', s)

def main():
    client = get_ssh()

    # 1. Git pull 最新代码
    print("=== [1/4] 同步代码到服务器 ===")
    out, err = run(client, f"cd {DEPLOY_DIR} && git pull origin master 2>&1", timeout=60)
    print(out.strip())
    if "Already up to date" in out:
        print("[OK] 服务器已是最新")
    elif "Updating" in out or "Fast-forward" in out:
        print("[OK] 代码已更新")
    else:
        print(f"[WARN] git pull 结果异常: {err[:300]}")

    # 2. 检查 Python 环境和依赖
    print("\n=== [2/4] 检查环境 ===")
    out, _ = run(client, "python3 --version 2>&1; pip3 list 2>/dev/null | grep -iE 'paramiko|pytest|requests|pycryptodome|cryptography' 2>/dev/null || echo 'some packages missing'")
    print(out.strip())

    # 确保依赖安装
    out, err = run(client, f"cd {DEPLOY_DIR} && pip3 install -q pytest requests pycryptodome paramiko 2>&1 | tail -5", timeout=120)
    print(out.strip() if out.strip() else "[OK] 依赖已就绪")

    # 3. 启动 IPD API 流水线
    print("\n=== [3/4] 启动 IPD 全流程测试 ===")
    # 先清理旧日志
    run(client, f"rm -f {LOG_FILE} {PID_FILE}", timeout=10)

    start_cmd = (
        f"cd {DEPLOY_DIR} && "
        f"(setsid python3 _ipd_run_api_pipeline.py > {LOG_FILE} 2>&1 < /dev/null &) ; "
        f"sleep 2 ; "
        f"pgrep -f '_ipd_run_api_pipeline' | head -1 > {PID_FILE} ; "
        f"cat {PID_FILE}"
    )
    out, err = run(client, start_cmd, timeout=20)
    pid = out.strip().split("\n")[0].strip()
    if not pid or not pid.isdigit():
        out2, _ = run(client, "pgrep -f '_ipd_run_api_pipeline' | head -1", timeout=10)
        pid = out2.strip()

    if not pid or not pid.isdigit():
        print("[ERROR] 未能获取测试进程 PID")
        out3, _ = run(client, f"head -50 {LOG_FILE} 2>/dev/null", timeout=10)
        print(out3)
        client.close()
        sys.exit(1)

    print(f"[INFO] 测试已启动, PID={pid}")
    time.sleep(5)

    # 验证进程存活
    out, _ = run(client, f"ps -p {pid} -o pid=,args= 2>/dev/null || echo DEAD", timeout=10)
    if "DEAD" in out:
        print(f"[WARN] 进程 {pid} 未在运行，检查日志...")
        out2, _ = run(client, f"cat {LOG_FILE} 2>/dev/null", timeout=15)
        print(out2[:2000])
        client.close()
        sys.exit(1)

    # 4. 轮询进度
    print("\n=== [4/4] 监控进度 ===")
    stage_markers = [
        ("RUN_ID =", "STARTED"),
        ("preflight", "PREFLIGHT"),
        ("pytest-smoke", "SMOKE"),
        ("pytest-readonly", "READONLY"),
        ("pytest-full-api", "FULL_API"),
        ("wr15", "WR15"),
        ("API 专项报告", "API_REPORT"),
        ("断言 passed=", "DONE"),
    ]
    seen = set()
    last_size = 0
    waited = 0
    max_wait = 600  # 10 分钟超时

    while waited < max_wait:
        try:
            # 检查进程存活
            out, _ = run(client, f"ps -p {pid} -o pid= 2>/dev/null || echo DEAD", timeout=15)
            is_alive = out.strip() != "DEAD"

            # 读取日志增量
            out, _ = run(client, f"wc -c < {LOG_FILE} 2>/dev/null || echo 0", timeout=15)
            try:
                current_size = int(out.strip())
            except ValueError:
                current_size = 0

            if current_size > last_size:
                out, _ = run(client, f"tail -c +{last_size + 1} {LOG_FILE} 2>/dev/null", timeout=15)
                new_content = clean(out)
                last_size = current_size

                for marker, stage in stage_markers:
                    if marker in new_content and stage not in seen:
                        seen.add(stage)
                        ts = time.strftime("%H:%M:%S")
                        print(f"[{ts}] ▶ {marker}")
                        if stage == "DONE":
                            break

                # 输出关键行
                for line in new_content.split("\n"):
                    ls = line.strip()
                    if any(kw in ls for kw in ["[OK]", "[ERROR]", "[WARN]", "[INFO]", "✅", "passed=", "failed=", "缺陷"]):
                        if 10 < len(ls) < 200:
                            print(f"  | {ls}")

            if not is_alive:
                out, _ = run(client, f"tail -40 {LOG_FILE} 2>/dev/null", timeout=15)
                print("\n[INFO] 进程已退出，最后 40 行日志:")
                print(clean(out))
                break

            if "DONE" in seen:
                print("\n[INFO] 测试完成！")
                break

        except Exception as e:
            print(f"[WARN] SSH 异常: {e}，重连...")
            try:
                client.close()
            except Exception:
                pass
            time.sleep(5)
            try:
                client = get_ssh()
                print("[OK] SSH 重连成功")
            except Exception as e2:
                print(f"[ERROR] SSH 重连失败: {e2}")
                time.sleep(10)

        time.sleep(10)
        waited += 10

    # 5. 下载报告
    print("\n=== 下载报告 ===")
    out, _ = run(client, f"ls -dt {DEPLOY_DIR}/projects/ipd/docs/test-runs/*/ 2>/dev/null | head -1")
    batch_dir = out.strip().rstrip("/")
    if not batch_dir:
        print("[ERROR] 未找到批次目录")
        client.close()
        sys.exit(1)

    batch_id = batch_dir.split("/")[-1]
    local_batch = f"{LOCAL_ROOT}/projects/ipd/docs/test-runs/{batch_id}"
    print(f"[INFO] 批次: {batch_id}")
    print(f"[INFO] 本地: {local_batch}")

    sftp = client.open_sftp()
    downloaded = 0
    for sub in ["reports", "defects", "raw/api-results", "raw/run-logs"]:
        remote_sub = f"{batch_dir}/{sub}"
        local_sub = f"{local_batch}/{sub}"
        os.makedirs(local_sub, exist_ok=True)
        try:
            for entry in sftp.listdir_attr(remote_sub):
                remote_path = f"{remote_sub}/{entry.filename}"
                local_path = f"{local_sub}/{entry.filename}"
                if not (entry.st_mode and (entry.st_mode & 0o040000)):
                    sftp.get(remote_path, local_path)
                    print(f"[OK] {sub}/{entry.filename} ({entry.st_size} bytes)")
                    downloaded += 1
        except Exception as e:
            print(f"[SKIP] {sub}: {e}")

    # 下载批次摘要
    try:
        sftp.get(f"{batch_dir}/批次摘要.md", f"{local_batch}/批次摘要.md")
        print(f"[OK] 批次摘要.md")
        downloaded += 1
    except Exception:
        pass

    # 下载 .run_id
    try:
        sftp.get(f"{batch_dir}/.run_id", f"{local_batch}/.run_id")
        downloaded += 1
    except Exception:
        pass

    # 下载 .api_run_result.json
    try:
        sftp.get(f"{batch_dir}/.api_run_result.json", f"{local_batch}/.api_run_result.json")
        downloaded += 1
    except Exception:
        pass

    sftp.close()
    client.close()
    print(f"\n[OK] 全部完成，共下载 {downloaded} 个文件")

if __name__ == "__main__":
    main()
