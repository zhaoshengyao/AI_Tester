#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""IPD 全流程测试远程执行脚本（SFTP 上传 + 执行 + 轮询 + 下载）。

服务器无 git，通过 SFTP 上传必要文件后执行。
"""
import paramiko
import re
import time
import os
import sys
import stat

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

def sftp_mkdirs(sftp, remote_dir):
    """递归创建远程目录。"""
    parts = remote_dir.strip("/").split("/")
    cur = ""
    for p in parts:
        cur = f"{cur}/{p}"
        try:
            sftp.stat(cur)
        except FileNotFoundError:
            sftp.mkdir(cur)

def sftp_upload_dir(sftp, local_dir, remote_dir, skip_patterns=None):
    """递归上传本地目录到远程。"""
    if skip_patterns is None:
        skip_patterns = []
    uploaded = 0
    for root, dirs, files in os.walk(local_dir):
        # 跳过模式
        rel = os.path.relpath(root, local_dir).replace("\\", "/")
        if any(sp in rel for sp in skip_patterns):
            continue

        remote_path = remote_dir if rel == "." else f"{remote_dir}/{rel}"
        try:
            sftp.stat(remote_path)
        except FileNotFoundError:
            sftp_mkdirs(sftp, remote_path)

        for f in files:
            if any(sp in f for sp in skip_patterns):
                continue
            local_file = os.path.join(root, f)
            remote_file = f"{remote_path}/{f}"
            try:
                sftp.put(local_file, remote_file)
                uploaded += 1
            except Exception as e:
                print(f"  [SKIP] {rel}/{f}: {e}")
    return uploaded

def main():
    client = get_ssh()

    # 1. 检查服务器目录
    print("=== [1/5] 检查服务器环境 ===")
    out, _ = run(client, f"ls -la {DEPLOY_DIR}/ 2>/dev/null | head -10; echo '---'; python3 --version")
    print(out.strip())

    # 2. 安装 pycryptodome（AES 加密依赖）
    print("\n=== [2/5] 安装依赖 ===")
    out, err = run(client, "pip3 install -q pycryptodome 2>&1 | tail -3", timeout=120)
    print(out.strip() if out.strip() else "[OK] pycryptodome 已安装")

    # 3. SFTP 上传必要文件
    print("\n=== [3/5] 上传文件到服务器 ===")
    sftp = client.open_sftp()

    total = 0
    # 上传 _ipd_run_api_pipeline.py
    sftp.put(f"{LOCAL_ROOT}/_ipd_run_api_pipeline.py", f"{DEPLOY_DIR}/_ipd_run_api_pipeline.py")
    total += 1
    # 上传 _gen_api_report.py
    sftp.put(f"{LOCAL_ROOT}/_gen_api_report.py", f"{DEPLOY_DIR}/_gen_api_report.py")
    total += 1
    # 上传 _gen_ui_perf_sec_mat_reports.py
    sftp.put(f"{LOCAL_ROOT}/_gen_ui_perf_sec_mat_reports.py", f"{DEPLOY_DIR}/_gen_ui_perf_sec_mat_reports.py")
    total += 1
    # 上传 _run_wr15_cases.py
    sftp.put(f"{LOCAL_ROOT}/_run_wr15_cases.py", f"{DEPLOY_DIR}/_run_wr15_cases.py")
    total += 1
    # 上传 _ipd_preflight.py
    sftp.put(f"{LOCAL_ROOT}/_ipd_preflight.py", f"{DEPLOY_DIR}/_ipd_preflight.py")
    total += 1
    print(f"  [OK] 根目录脚本: {total} 个")

    # 上传 tests/api/ipd/
    n = sftp_upload_dir(sftp, f"{LOCAL_ROOT}/tests/api", f"{DEPLOY_DIR}/tests/api",
                        skip_patterns=["__pycache__", ".pyc"])
    print(f"  [OK] tests/api/: {n} 个")
    total += n

    # 上传 projects/ipd/ (system.yaml, .env, docs/cases/, docs/analysis/, docs/test-plan/, docs/knowledge/)
    n = sftp_upload_dir(sftp, f"{LOCAL_ROOT}/projects/ipd", f"{DEPLOY_DIR}/projects/ipd",
                        skip_patterns=["__pycache__", ".pyc", "test-runs", "zhaoboss-ui-write-captures"])
    print(f"  [OK] projects/ipd/: {n} 个")
    total += n

    # 上传 pytest.ini
    if os.path.exists(f"{LOCAL_ROOT}/pytest.ini"):
        sftp.put(f"{LOCAL_ROOT}/pytest.ini", f"{DEPLOY_DIR}/pytest.ini")
        total += 1

    # 上传 scripts/lib/stage-common.ps1 和 scripts/stage_contract.py（如果存在）
    for f in ["scripts/stage_contract.py"]:
        local_f = f"{LOCAL_ROOT}/{f}"
        if os.path.exists(local_f):
            remote_f = f"{DEPLOY_DIR}/{f}"
            sftp_mkdirs(sftp, os.path.dirname(remote_f))
            sftp.put(local_f, remote_f)
            total += 1

    sftp.close()
    print(f"  [OK] 总计上传: {total} 个文件")

    # 4. 启动 IPD API 流水线
    print("\n=== [4/5] 启动 IPD 全流程测试 ===")
    run(client, f"rm -f {LOG_FILE} {PID_FILE}", timeout=10)

    start_cmd = (
        f"cd {DEPLOY_DIR} && "
        f"PYTHONPATH={DEPLOY_DIR} "
        f"(setsid python3 _ipd_run_api_pipeline.py > {LOG_FILE} 2>&1 < /dev/null &) ; "
        f"sleep 3 ; "
        f"pgrep -f '_ipd_run_api_pipeline' | head -1 > {PID_FILE} ; "
        f"cat {PID_FILE}"
    )
    out, err = run(client, start_cmd, timeout=30)
    pid = out.strip().split("\n")[0].strip()
    if not pid or not pid.isdigit():
        out2, _ = run(client, "pgrep -f '_ipd_run_api_pipeline' | head -1", timeout=10)
        pid = out2.strip()

    if not pid or not pid.isdigit():
        print("[ERROR] 未能获取测试进程 PID")
        out3, _ = run(client, f"cat {LOG_FILE} 2>/dev/null", timeout=15)
        print(out3[:3000])
        client.close()
        sys.exit(1)

    print(f"[INFO] PID={pid}")
    time.sleep(5)

    # 验证进程存活
    out, _ = run(client, f"ps -p {pid} -o pid= 2>/dev/null || echo DEAD", timeout=10)
    if "DEAD" in out:
        print(f"[WARN] 进程 {pid} 已退出，检查日志...")
        out2, _ = run(client, f"cat {LOG_FILE} 2>/dev/null", timeout=15)
        print(out2[:3000])
        client.close()
        sys.exit(1)
    print("[OK] 进程运行中")

    # 5. 轮询进度
    print("\n=== [5/5] 监控进度 ===")
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
    max_wait = 900  # 15 分钟

    while waited < max_wait:
        try:
            out, _ = run(client, f"ps -p {pid} -o pid= 2>/dev/null || echo DEAD", timeout=15)
            is_alive = out.strip() != "DEAD"

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

                for line in new_content.split("\n"):
                    ls = line.strip()
                    if any(kw in ls for kw in ["[OK]", "[ERROR]", "[WARN]", "[INFO]", "passed=", "failed=", "缺陷", "✅"]):
                        if 10 < len(ls) < 200:
                            print(f"  | {ls}")

            if not is_alive:
                out, _ = run(client, f"tail -50 {LOG_FILE} 2>/dev/null", timeout=15)
                print("\n[INFO] 进程已退出，最后 50 行日志:")
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

        if waited % 180 == 0 and waited > 0:
            try:
                client.close()
                client = get_ssh()
            except Exception:
                pass

    # 6. 下载报告
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
    for sub in ["reports", "defects", "raw/api-results", "raw/run-logs", "stage-status"]:
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

    for extra in ["批次摘要.md", ".run_id", ".api_run_result.json"]:
        try:
            sftp.get(f"{batch_dir}/{extra}", f"{local_batch}/{extra}")
            print(f"[OK] {extra}")
            downloaded += 1
        except Exception:
            pass

    sftp.close()
    client.close()
    print(f"\n[OK] 全部完成，共下载 {downloaded} 个文件")

if __name__ == "__main__":
    main()
