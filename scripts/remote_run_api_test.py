#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""在远程服务器上启动 CRM API 测试（冒烟+全量），轮询进度并报告结果"""
import paramiko
import re
import time
import sys

HOST = "192.168.2.70"
PORT = 22
USER = "root"
PASSWORD = "Zw@123qwe"
DEPLOY_DIR = "/home/zhiwei/AutoTestHub"
SYSTEM = sys.argv[1] if len(sys.argv) > 1 else "crm"
LOG_FILE = f"{DEPLOY_DIR}/api-test-remote.log"
PID_FILE = f"{DEPLOY_DIR}/api-test-remote.pid"

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

def main():
    # 1. 连接服务器
    print(f"[INFO] 连接服务器 {HOST}...")
    client = get_ssh()
    print(f"[OK] 已连接, 系统: {SYSTEM}")

    # 2. 先同步 .env 确保凭证最新
    print("\n=== [1/4] 检查环境 ===")
    out = run(client, f"cd {DEPLOY_DIR} && test -f projects/{SYSTEM}/.env && echo OK || echo MISSING")
    if out.strip() == "MISSING":
        print(f"[ERROR] projects/{SYSTEM}/.env 不存在")
        client.close()
        return
    print(f"[OK] .env 存在")

    # 检查被测服务连通性
    out = run(client, f"cd {DEPLOY_DIR} && source projects/{SYSTEM}/.env && curl -s -o /dev/null -w '%{{http_code}}' --connect-timeout 5 ${{BASE_URL:-http://192.168.2.97:6089}}/ 2>/dev/null || echo FAIL", timeout=15)
    print(f"[INFO] 被测服务连通性: HTTP {out.strip()}")

    # 3. 启动 API 测试（smoke + full）
    print(f"\n=== [2/4] 启动 API 测试 ===")
    # 先跑冒烟，再跑全量
    test_cmd = (
        f"cd {DEPLOY_DIR} && "
        f"export TEST_SYSTEM_ID={SYSTEM} && "
        f"source projects/{SYSTEM}/.env && "
        f"echo '=== API 冒烟测试 ===' && "
        f"bash scripts/run-api-tests.sh smoke && "
        f"echo '=== API 全量测试 ===' && "
        f"bash scripts/run-api-tests.sh full && "
        f"echo '=== API_TEST_DONE ==='"
    )
    start_cmd = (
        f"cd {DEPLOY_DIR} && "
        f"(setsid bash -c '{test_cmd}' > {LOG_FILE} 2>&1 < /dev/null &) ; "
        f"sleep 2 ; "
        f"pgrep -f 'run-api-tests' | head -1 > {PID_FILE} ; "
        f"cat {PID_FILE}"
    )
    try:
        out = run(client, start_cmd, timeout=25)
    except Exception as e:
        print(f"[WARN] 启动命令超时: {e}")
        out = ""

    pid = out.strip().split("\n")[0].strip() if out.strip() else ""
    if not pid or not pid.isdigit():
        out2 = run(client, "pgrep -f 'run-api-tests' | head -1", timeout=10)
        pid = out2.strip()

    if not pid or not pid.isdigit():
        print("[ERROR] 未能获取测试进程 PID")
        out3 = run(client, f"head -30 {LOG_FILE} 2>/dev/null", timeout=10)
        print(clean(out3))
        client.close()
        return

    print(f"[OK] API 测试已启动, PID={pid}")

    # 验证进程存活
    time.sleep(3)
    out2 = run(client, f"ps -p {pid} -o pid=,args= 2>/dev/null || echo DEAD", timeout=10)
    if "DEAD" in out2:
        print(f"[WARN] 进程 {pid} 未在运行，检查日志...")
        out3 = run(client, f"cat {LOG_FILE} 2>/dev/null", timeout=15)
        print(clean(out3)[:3000])
        client.close()
        return

    # 4. 轮询进度
    print(f"\n=== [3/4] 监控进度 ===")
    stage_markers = [
        ("=== API 冒烟测试 ===", "SMOKE_START"),
        ("API 冒烟", "SMOKE"),
        ("passed", "SMOKE_RESULT"),
        ("=== API 全量测试 ===", "FULL_START"),
        ("=== API_TEST_DONE ===", "DONE"),
    ]
    seen = set()
    last_size = 0
    waited = 0
    max_wait = 600  # 10 分钟超时
    interval = 10

    while waited < max_wait:
        try:
            # 检查进程存活
            out = run(client, f"ps -p {pid} -o pid= 2>/dev/null || echo DEAD", timeout=15)
            is_alive = out.strip() != "DEAD"

            # 读取日志增量
            out = run(client, f"wc -c < {LOG_FILE} 2>/dev/null || echo 0", timeout=15)
            try:
                current_size = int(out.strip())
            except ValueError:
                current_size = 0

            if current_size > last_size:
                out = run(client, f"tail -c +{last_size + 1} {LOG_FILE} 2>/dev/null", timeout=15)
                new_content = clean(out)

                # 检查阶段标记
                for marker, stage in stage_markers:
                    if marker in new_content and stage not in seen:
                        seen.add(stage)
                        ts = time.strftime("%H:%M:%S")
                        print(f"[{ts}] ▶ {marker}")
                        if stage == "DONE":
                            break

                # 输出关键日志行
                for line in new_content.split("\n"):
                    ls = line.strip()
                    if any(kw in ls for kw in ["[OK]", "[ERROR]", "[WARN]", "[INFO]", "passed", "failed", "error", "通过", "失败", "总计", "通过率", "PASSED", "FAILED", "ERROR"]):
                        if 5 < len(ls) < 200:
                            print(f"  | {ls}")

                last_size = current_size

            if not is_alive:
                # 进程已退出，读取剩余日志
                out = run(client, f"tail -50 {LOG_FILE} 2>/dev/null", timeout=15)
                remaining = clean(out)
                # 检查是否有 DONE 标记
                if "API_TEST_DONE" in remaining or "API_TEST_DONE" in seen:
                    print("\n[OK] 测试进程已正常完成")
                else:
                    print("\n[WARN] 测试进程已退出（可能异常）")
                print(f"\n--- 最后 50 行 ---\n{remaining}")
                break

            if "DONE" in seen:
                print("\n[OK] 检测到完成标记")
                break

        except Exception as e:
            print(f"[WARN] SSH 连接异常: {e}，重连...")
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

        time.sleep(interval)
        waited += interval

        # 每 3 分钟重连
        if waited % 180 == 0 and waited > 0:
            try:
                client.close()
                client = get_ssh()
            except Exception:
                pass

    if waited >= max_wait:
        print(f"\n[WARN] 超时 ({max_wait//60}分钟)，测试可能仍在运行")
        print(f"[INFO] 手动查看: ssh root@{HOST} 'tail -50 {LOG_FILE}'")

    # 5. 汇总结果
    print(f"\n=== [4/4] 测试结果汇总 ===")

    # 获取最新批次目录
    out = run(client, f"ls -dt {DEPLOY_DIR}/projects/{SYSTEM}/test-runs/*/ 2>/dev/null | head -1")
    batch_dir = out.strip().rstrip("/")
    if batch_dir:
        batch_id = batch_dir.split("/")[-1]
        print(f"批次 ID: {batch_id}")

        # 读取批次摘要
        out = run(client, f"cat '{batch_dir}/批次摘要.md' 2>/dev/null || echo NOT_FOUND", timeout=15)
        if out.strip() != "NOT_FOUND":
            print(f"\n--- 批次摘要 ---\n{clean(out)[:2000]}")

    # 读取完整日志的关键结果部分
    out = run(client, f"grep -E '(passed|failed|error|通过|失败|总计|通过率|PASSED|FAILED)' {LOG_FILE} 2>/dev/null | tail -20", timeout=15)
    if out.strip():
        print(f"\n--- 关键结果行 ---\n{clean(out)}")

    # 清理
    run(client, f"rm -f {PID_FILE}", timeout=5)
    client.close()
    print("\n[OK] 全部完成")

if __name__ == "__main__":
    main()
