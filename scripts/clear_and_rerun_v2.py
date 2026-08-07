#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""清理服务器历史测试数据并启动全流程测试（后台）"""
import paramiko
import time
import sys

HOST = "192.168.2.70"
PORT = 22
USER = "root"
PASSWORD = "Zw@123qwe"
REMOTE_BASE = "/home/zhiwei/AutoTestHub"

def get_ssh():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
    return c

def run(client, cmd, timeout=120):
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    return out, err

client = get_ssh()

print("=" * 60)
print("Step 1: 确认修复后的脚本已就位")
print("=" * 60)
out, _ = run(client, f"head -5 {REMOTE_BASE}/scripts/run-full-test-flow.sh")
print(out)
# 检查脚本是否包含缺陷清单生成逻辑（修复后的标志）
out, _ = run(client, f"grep -c '缺陷清单' {REMOTE_BASE}/scripts/run-full-test-flow.sh")
gen_count = out.strip()
print(f"脚本中'缺陷清单'出现次数: {gen_count}")
out, _ = run(client, f"grep -c '测试覆盖矩阵' {REMOTE_BASE}/scripts/run-full-test-flow.sh")
cm_count = out.strip()
print(f"脚本中'测试覆盖矩阵'出现次数: {cm_count}")
out, _ = run(client, f"grep -c 'stage-status' {REMOTE_BASE}/scripts/run-full-test-flow.sh")
ss_count = out.strip()
print(f"脚本中'stage-status'出现次数: {ss_count}")

if int(gen_count or 0) < 3 or int(cm_count or 0) < 1 or int(ss_count or 0) < 1:
    print("\n[警告] 修复后的脚本特征不完整，请先同步脚本！")
    sys.exit(1)
print("✅ 修复后的脚本已就位")

print("\n" + "=" * 60)
print("Step 2: 清理历史测试数据")
print("=" * 60)

# 清理范围清单（保留源码/脚本/配置/用例文档）
clean_targets = [
    ("docs/test-runs", "批次归档目录"),
    ("tests/api/reports", "API 测试报告"),
    ("tests/ui/playwright-report", "UI 测试报告"),
    ("tests/ui/test-results", "UI 测试原始结果"),
    ("tests/performance/locust/results", "性能测试结果"),
    ("tests/security/reports", "安全测试报告"),
]

for sub, desc in clean_targets:
    target = f"{REMOTE_BASE}/{sub}"
    # 先统计清理前大小
    out, _ = run(client, f"ls -d {target} 2>/dev/null && find {target} -type f 2>/dev/null | wc -l")
    file_count = out.strip().split("\n")[-1] if out.strip() else "0"
    # 重新创建空目录
    run(client, f"rm -rf {target} && mkdir -p {target}")
    print(f"  ✅ 已清理 {desc} ({sub}): 删除 {file_count} 个文件")

# 清理可能残留的 latest 软链接
run(client, f"rm -f {REMOTE_BASE}/docs/test-runs/latest 2>/dev/null")
run(client, f"mkdir -p {REMOTE_BASE}/docs/test-runs")

print("\n✅ 历史数据清理完成")

print("\n" + "=" * 60)
print("Step 3: 启动全流程测试（后台）")
print("=" * 60)

# 使用 nohup 后台运行，输出到日志文件
log_file = f"{REMOTE_BASE}/full-flow-rerun.log"
# 先清空旧日志
run(client, f"rm -f {log_file}")

# 构造启动命令：cd 到项目根，执行脚本，输出重定向到日志
start_cmd = (
    f"cd {REMOTE_BASE} && "
    f"nohup bash scripts/run-full-test-flow.sh > {log_file} 2>&1 & "
    f"echo $!"
)
out, err = run(client, start_cmd)
pid = out.strip().split("\n")[-1] if out.strip() else ""
print(f"✅ 全流程测试已后台启动, PID={pid}")

# 记录启动信息到本地状态文件，便于后续轮询
state = f"PID={pid}\nLOG={log_file}\nSTART_TIME={time.strftime('%Y-%m-%d %H:%M:%S')}\n"
with open(r"d:\AICode\TestHub\AITestDemo\scripts\.rerun_state.txt", "w", encoding="utf-8") as f:
    f.write(state)

print(f"日志文件: {log_file}")
print(f"启动时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

# 等待几秒确认进程存活
time.sleep(5)
out, _ = run(client, f"ps -p {pid} -o pid,cmd --no-headers 2>/dev/null")
if pid and out.strip():
    print(f"✅ 进程 {pid} 运行中")
else:
    # 进程可能已退出（快速失败），查看日志
    out, _ = run(client, f"tail -30 {log_file}")
    print(f"⚠️ 进程 {pid} 未检测到，日志末尾:\n{out}")
    sys.exit(1)

client.close()
print("\n" + "=" * 60)
print("✅ 清理完成，全流程测试已在后台运行")
print("预计耗时约 13-15 分钟，请稍后轮询进度")
print("=" * 60)