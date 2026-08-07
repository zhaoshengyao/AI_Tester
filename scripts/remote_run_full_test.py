#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
远程执行全流程测试脚本
通过 SSH 连接服务器，在后台启动全流程测试，并轮询进度。
"""
import paramiko
import time
import sys
import os

# 服务器配置
HOST = "192.168.2.70"
PORT = 22
USER = "root"
PASSWORD = "Zw@123qwe"
DEPLOY_DIR = "/home/zhiwei/AutoTestHub"
LOG_FILE = f"{DEPLOY_DIR}/full-test-flow.log"
PID_FILE = f"{DEPLOY_DIR}/full-test-flow.pid"


def get_ssh_client():
    """建立 SSH 连接"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
    # 启用 keepalive，防止长时间等待后连接断开
    client.get_transport().set_keepalive(30)
    return client


def exec_cmd(client, cmd, timeout=60):
    """执行命令并返回输出"""
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout, get_pty=False)
    try:
        out = stdout.read().decode("utf-8", errors="replace")
    except Exception:
        out = ""
    try:
        err = stderr.read().decode("utf-8", errors="replace")
    except Exception:
        err = ""
    return out, err


def check_existing(client):
    """检查部署目录和脚本是否存在"""
    out, err = exec_cmd(client, f"test -d {DEPLOY_DIR} && echo EXISTS || echo MISSING")
    if "EXISTS" not in out:
        print(f"[ERROR] 部署目录不存在: {DEPLOY_DIR}")
        return False

    out, err = exec_cmd(client, f"test -f {DEPLOY_DIR}/scripts/run-full-test-flow.sh && echo EXISTS || echo MISSING")
    if "EXISTS" not in out:
        print(f"[ERROR] 全流程脚本不存在: {DEPLOY_DIR}/scripts/run-full-test-flow.sh")
        return False

    # 检查是否已有测试在运行
    out, err = exec_cmd(client, f"test -f {PID_FILE} && cat {PID_FILE} || echo NONE")
    if out.strip() != "NONE":
        pid = out.strip()
        out2, _ = exec_cmd(client, f"ps -p {pid} -o pid= 2>/dev/null || echo DEAD")
        if out2.strip() != "DEAD":
            print(f"[WARN] 已有测试进程在运行 (PID={pid})，将终止后重新启动")
            exec_cmd(client, f"kill -9 {pid} 2>/dev/null; rm -f {PID_FILE}")
            time.sleep(2)
        else:
            exec_cmd(client, f"rm -f {PID_FILE}")

    return True


def start_test(client):
    """在服务器后台启动全流程测试"""
    # 使用 setsid + 子 shell 完全分离进程，避免 SSH 通道挂起
    # 关键：( ... & ) 在子 shell 中启动，setsid 创建新会话，所有 FD 重定向
    start_cmd = (
        f"cd {DEPLOY_DIR} && "
        f"(setsid bash scripts/run-full-test-flow.sh > {LOG_FILE} 2>&1 < /dev/null &) ; "
        f"sleep 1 ; "
        f"pgrep -f 'run-full-test-flow' | head -1 > {PID_FILE} ; "
        f"cat {PID_FILE}"
    )
    try:
        out, err = exec_cmd(client, start_cmd, timeout=20)
    except Exception as e:
        print(f"[WARN] 启动命令超时（可能是正常现象），尝试直接读取 PID: {e}")
        out = ""

    pid = out.strip().split("\n")[0].strip() if out.strip() else ""

    if not pid or not pid.isdigit():
        # 如果没拿到 PID，尝试直接查找
        out2, _ = exec_cmd(client, "pgrep -f 'run-full-test-flow' | head -1", timeout=10)
        pid = out2.strip()

    if not pid or not pid.isdigit():
        print(f"[ERROR] 未能获取测试进程 PID")
        out3, _ = exec_cmd(client, f"head -30 {LOG_FILE} 2>/dev/null", timeout=10)
        print(out3)
        return None

    print(f"[INFO] 全流程测试已启动, PID={pid}")
    print(f"[INFO] 日志文件: {LOG_FILE}")

    # 验证进程确实在运行
    time.sleep(3)
    out2, _ = exec_cmd(client, f"ps -p {pid} -o pid=,args= 2>/dev/null || echo DEAD", timeout=10)
    if "DEAD" in out2:
        print(f"[WARN] 进程 {pid} 未在运行，检查日志:")
        out3, _ = exec_cmd(client, f"head -30 {LOG_FILE} 2>/dev/null", timeout=10)
        print(out3)
        return None
    else:
        print(f"[OK] 进程运行中: {out2.strip()[:100]}")

    return pid


def poll_progress(client, pid):
    """轮询测试进度"""
    stage_markers = [
        ("Step 1: API 冒烟测试", "API_SMOKE"),
        ("Step 2: API 全量测试", "API_FULL"),
        ("Step 3: UI 冒烟测试", "UI_SMOKE"),
        ("Step 4: UI 全量测试", "UI_FULL"),
        ("Step 5: 性能冒烟测试", "PERF_SMOKE"),
        ("Step 6: 性能常规测试", "PERF_REGULAR"),
        ("Step 7: 安全扫描", "SECURITY"),
        ("Step 8: 生成系统测试报告", "REPORT"),
        ("全流程执行完成", "DONE"),
    ]
    seen_stages = set()
    last_size = 0
    max_wait = 3600  # 最大等待 60 分钟
    waited = 0
    interval = 15

    while waited < max_wait:
        try:
            # 检查进程是否存活
            out, _ = exec_cmd(client, f"ps -p {pid} -o pid= 2>/dev/null || echo DEAD", timeout=15)
            is_alive = out.strip() != "DEAD"

            # 读取日志新增内容
            out, _ = exec_cmd(client, f"wc -c < {LOG_FILE} 2>/dev/null || echo 0", timeout=15)
            try:
                current_size = int(out.strip())
            except ValueError:
                current_size = 0

            if current_size > last_size:
                # 读取新增部分
                out, _ = exec_cmd(client, f"tail -c +{last_size + 1} {LOG_FILE} 2>/dev/null", timeout=15)
                new_content = out
                last_size = current_size

                # 检查阶段标记
                for marker, stage in stage_markers:
                    if marker in new_content and stage not in seen_stages:
                        seen_stages.add(stage)
                        ts = time.strftime("%H:%M:%S")
                        print(f"[{ts}] ▶ 进入阶段: {marker}")

                        if stage == "DONE":
                            print(f"[INFO] 测试流程已完成")
                            return True

                # 输出关键日志行（包含 OK/FAIL/ERROR/WARN）
                for line in new_content.split("\n"):
                    line_stripped = line.strip()
                    if any(kw in line_stripped for kw in ["[OK]", "[ERROR]", "[WARN]", "❌", "✅", "失败", "通过", "总计", "通过率"]):
                        if len(line_stripped) < 200:
                            print(f"  | {line_stripped}")

            if not is_alive:
                # 进程已退出，读取剩余日志
                out, _ = exec_cmd(client, f"tail -80 {LOG_FILE} 2>/dev/null", timeout=15)
                print("\n[INFO] 测试进程已退出，最后 80 行日志:")
                print(out)
                return "DONE" in seen_stages

        except Exception as e:
            print(f"[WARN] SSH 连接异常: {e}，尝试重连...")
            try:
                client.close()
            except Exception:
                pass
            time.sleep(5)
            try:
                client = get_ssh_client()
                print("[OK] SSH 重连成功")
            except Exception as e2:
                print(f"[ERROR] SSH 重连失败: {e2}")
                time.sleep(10)

        time.sleep(interval)
        waited += interval

    print(f"[WARN] 已等待 {max_wait//60} 分钟，超时退出")
    return False


def fetch_report(client=None):
    """获取测试报告"""
    print("\n" + "=" * 60)
    print("[INFO] 获取测试报告")
    print("=" * 60)

    # 如果没有传入 client，创建新连接
    own_client = False
    if client is None:
        client = get_ssh_client()
        own_client = True

    try:
        # 查找最新批次目录
        out, _ = exec_cmd(client, f"ls -dt {DEPLOY_DIR}/docs/test-runs/*/ 2>/dev/null | head -1")
        batch_dir = out.strip()
        if not batch_dir:
            print("[ERROR] 未找到测试批次目录")
            return

        print(f"[INFO] 最新批次目录: {batch_dir}")

        # 读取系统测试报告
        report_path = f"{batch_dir}reports/系统测试报告.md"
        out, _ = exec_cmd(client, f"test -f '{report_path}' && cat '{report_path}' || echo MISSING")
        if out.strip() != "MISSING":
            print("\n--- 系统测试报告 ---")
            print(out)
        else:
            print(f"[WARN] 系统测试报告不存在: {report_path}")

        # 读取批次摘要
        summary_path = f"{batch_dir}批次摘要.md"
        out, _ = exec_cmd(client, f"test -f '{summary_path}' && cat '{summary_path}' || echo MISSING")
        if out.strip() != "MISSING":
            print("\n--- 批次摘要 ---")
            print(out)

        # 读取日志尾部（执行总结）
        out, _ = exec_cmd(client, f"tail -80 {LOG_FILE} 2>/dev/null")
        print("\n--- 执行日志尾部 ---")
        print(out)
    finally:
        if own_client:
            client.close()


def main():
    print("=" * 60)
    print("[INFO] 远程全流程测试执行")
    print(f"[INFO] 服务器: {USER}@{HOST}:{PORT}")
    print(f"[INFO] 部署目录: {DEPLOY_DIR}")
    print("=" * 60)

    # 1. 建立连接
    print("\n[1/4] 建立 SSH 连接...")
    try:
        client = get_ssh_client()
        print("[OK] SSH 连接成功")
    except Exception as e:
        print(f"[ERROR] SSH 连接失败: {e}")
        sys.exit(1)

    # 2. 检查环境
    print("\n[2/4] 检查部署环境...")
    if not check_existing(client):
        client.close()
        sys.exit(1)
    print("[OK] 部署环境检查通过")

    # 3. 启动测试
    print("\n[3/4] 启动全流程测试...")
    pid = start_test(client)
    if pid is None:
        print("[ERROR] 测试启动失败")
        client.close()
        sys.exit(1)

    # 4. 轮询进度
    print("\n[4/4] 监控测试进度...")
    print("[INFO] 全流程测试包括: API(冒烟+全量) → UI(冒烟+全量) → 性能(冒烟+常规) → 安全扫描 → 报告生成")
    print("[INFO] 预计耗时 15-30 分钟，正在监控...\n")

    success = poll_progress(client, pid)

    # 关闭当前连接（poll_progress 中可能已重连，client 可能失效）
    try:
        client.close()
    except Exception:
        pass

    # 获取报告（使用独立连接）
    fetch_report()

    # 清理 PID 文件
    try:
        client2 = get_ssh_client()
        exec_cmd(client2, f"rm -f {PID_FILE}")
        client2.close()
    except Exception:
        pass

    print("\n" + "=" * 60)
    if success:
        print("[OK] 全流程测试执行完成")
    else:
        print("[WARN] 全流程测试执行结束（可能存在失败项）")
    print("=" * 60)


if __name__ == "__main__":
    main()
