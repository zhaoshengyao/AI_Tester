#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""准备阶段：杀残留进程 + 清理历史批次 + 确认修复脚本 + 启动全流程测试"""
import paramiko
import time
import sys

HOST = "192.168.2.70"; PORT = 22; USER = "root"; PASSWORD = "Zw@123qwe"
BASE = "/home/zhiwei/AutoTestHub"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
r = lambda cmd,t=30: c.exec_command(cmd, timeout=t)[1].read().decode("utf-8","replace")

# ========== 1. 杀掉残留的测试进程 ==========
print("=" * 60)
print("1. 杀掉残留的测试进程（避免并发重复启动）")
print("=" * 60)
# 先检查是否有残留进程
residual = r("pgrep -af 'run-full-test-flow|playwright|locust|chrome-headless' 2>/dev/null | grep -v pgrep")
if residual.strip():
    print("发现残留进程:")
    print(residual)
    # 杀掉相关进程
    r("pkill -9 -f 'run-full-test-flow' 2>/dev/null; pkill -9 -f 'playwright' 2>/dev/null; "
      "pkill -9 -f 'locust' 2>/dev/null; pkill -9 -f 'chrome-headless' 2>/dev/null; "
      "pkill -9 -f 'workerProcessEntry' 2>/dev/null; sleep 2")
    time.sleep(3)
    still = r("pgrep -af 'run-full-test-flow|playwright|locust|chrome-headless' 2>/dev/null | grep -v pgrep")
    print("\n清理后残留进程:" if still.strip() else "\n✅ 所有残留进程已清理")
    if still.strip(): print(still)
else:
    print("✅ 无残留进程")

# ========== 2. 清理历史批次和测试结果 ==========
print("\n" + "=" * 60)
print("2. 清理历史测试数据")
print("=" * 60)
clean_targets = [
    ("docs/test-runs", "批次归档目录"),
    ("tests/api/reports", "API 测试报告"),
    ("tests/ui/playwright-report", "UI 测试报告"),
    ("tests/ui/test-results", "UI 测试原始结果"),
    ("tests/ui/test-results.json", "UI 测试结果JSON"),
    ("tests/performance/locust/results", "性能测试结果"),
    ("tests/security/reports", "安全测试报告"),
    ("full-flow-rerun.log", "全流程日志"),
]
for sub, desc in clean_targets:
    target = f"{BASE}/{sub}"
    out = r(f"ls -d {target} 2>/dev/null && find {target} -type f 2>/dev/null | wc -l")
    file_count = out.strip().split("\n")[-1] if out.strip() else "0"
    r(f"rm -rf {target} && mkdir -p {target} 2>/dev/null; true")
    print(f"  ✅ 已清理 {desc} ({sub}): 删除 {file_count} 个文件")

print("\n✅ 历史数据清理完成")

# ========== 3. 确认修复后的脚本就位 ==========
print("\n" + "=" * 60)
print("3. 确认修复后的脚本已就位")
print("=" * 60)
# 检查修复行（用 _PERF_H 变量替代 $((...)) 内的 [ ] 命令）
fix_check = r(f"grep -c '_PERF_H=' {BASE}/scripts/run-full-test-flow.sh")
print(f"修复特征 '_PERF_H=' 出现次数: {fix_check.strip()}")
# 检查是否有旧的错误语法
bad_check = r(f"grep -c '\\[.*\\] && echo' {BASE}/scripts/run-full-test-flow.sh")
print(f"旧错误语法 '[...] && echo' 出现次数: {bad_check.strip()}（应只在条件赋值行，不在 $((...)) 内）")
# 检查 Step 8 缺陷清单生成逻辑
defect_check = r(f"grep -c '生成.*缺陷清单' {BASE}/scripts/run-full-test-flow.sh")
print(f"缺陷清单生成逻辑: {defect_check.strip()} 处")

# 重新上传脚本确保最新（从本地覆盖）
print("\n重新上传本地最新脚本以确保最新版本...")
sftp = c.open_sftp()
sftp.put(r"d:\AICode\TestHub\AITestDemo\scripts\run-full-test-flow.sh",
         f"{BASE}/scripts/run-full-test-flow.sh")
sftp.close()
r(f"chmod +x {BASE}/scripts/run-full-test-flow.sh")

# 再次确认
out = r(f"sed -n '693,702p' {BASE}/scripts/run-full-test-flow.sh")
print("\n修复后的关键代码（第693-702行）:")
print(out)

if "_PERF_H=" not in out:
    print("❌ 修复未生效，请检查脚本")
    sys.exit(1)
print("✅ 修复后的脚本已确认就位")

# ========== 4. 后台启动全流程测试 ==========
print("\n" + "=" * 60)
print("4. 后台启动全流程测试")
print("=" * 60)

log_file = f"{BASE}/full-flow-rerun.log"
r(f"rm -f {log_file}")
start_time = time.strftime('%Y-%m-%d %H:%M:%S')
print(f"启动时间: {start_time}")

# 使用 setsid + nohup + < /dev/null 完全脱离 ssh 会话
start_cmd = (
    f"cd {BASE} && "
    f"setsid bash -c 'nohup bash scripts/run-full-test-flow.sh > {log_file} 2>&1 < /dev/null &' "
    f"< /dev/null > /dev/null 2>&1 &"
)
c.exec_command(start_cmd, timeout=10)
time.sleep(8)

# 确认进程已启动
procs = r("pgrep -af 'run-full-test-flow.sh' 2>/dev/null | grep -v pgrep")
print(f"\n相关进程:\n{procs}")

# 确认日志开始写入
log_head = r(f"head -8 {log_file} 2>/dev/null")
print(f"\n日志开头:\n{log_head}")

if not procs.strip() or "Step" not in log_head:
    print("⚠️ 测试可能未成功启动，查看完整日志:")
    print(r(f"cat {log_file} 2>/dev/null"))
    sys.exit(1)

pid = ""
for line in procs.strip().split("\n"):
    if "run-full-test-flow.sh" in line:
        pid = line.split()[0]
        break

# 记录状态
state = f"PID={pid}\nLOG={log_file}\nSTART_TIME={start_time}\n"
with open(r"d:\AICode\TestHub\AITestDemo\scripts\.rerun_state.txt", "w", encoding="utf-8") as f:
    f.write(state)

print(f"\n✅ 全流程测试已后台启动, PID={pid}")
print(f"日志: {log_file}")
print(f"预计耗时约 25 分钟")
c.close()