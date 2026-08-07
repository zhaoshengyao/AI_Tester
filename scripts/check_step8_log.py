#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""提取并检查 Step 8 日志，确认无语法错误"""
import paramiko

HOST = "192.168.2.70"; PORT = 22; USER = "root"; PASSWORD = "Zw@123qwe"
BASE = "/home/zhiwei/AutoTestHub"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
r = lambda cmd,t=30: c.exec_command(cmd, timeout=t)[1].read().decode("utf-8","replace")

# 提取 Step 8 到日志末尾
full_log = r(f"cat {BASE}/full-flow-rerun.log 2>/dev/null")
step8_idx = full_log.find("Step 8")
if step8_idx == -1:
    print("❌ 未找到 Step 8")
    exit(1)
step8_log = full_log[step8_idx:]

print("=" * 60)
print("Step 8 完整日志")
print("=" * 60)
print(step8_log)

# 错误检查
print("\n" + "=" * 60)
print("错误检查")
print("=" * 60)
errors = []
for keyword in ["语法错误", "未绑定的变量", "unbound variable", "syntax error",
                "line 69", "line 70", "行694", "行695", "行696", "行697", "行698"]:
    if keyword in step8_log:
        errors.append(keyword)

if errors:
    print(f"❌ 发现错误关键词: {errors}")
else:
    print("✅ 未发现任何语法错误或未绑定变量错误")

# 成功标记检查
print("\n" + "=" * 60)
print("成功标记检查")
print("=" * 60)
expected_ok = [
    "阶段状态文件已生成", "覆盖矩阵已生成",
    "接口缺陷清单已生成", "性能缺陷清单已生成",
    "安全缺陷清单已生成", "UI缺陷清单已生成",
    "性能测试专项报告已生成", "安全扫描专项报告已生成",
    "系统测试报告已生成", "批次摘要已生成",
]
for marker in expected_ok:
    ok = marker in step8_log
    print(f"  {'✅' if ok else '❌'} {marker}")

# 全流程完成标记
if "全流程执行完成" in full_log:
    print("\n✅ 脚本正常执行完毕（找到'全流程执行完成'标记）")
else:
    print("\n⚠️ 未找到'全流程执行完成'标记")

# 文件总数
print("\n" + "=" * 60)
print("文件总数")
print("=" * 60)
batch = f"{BASE}/docs/test-runs/20260806-104633"
total = r(f"find {batch} -type f | wc -l").strip()
print(f"批次 {batch}: {total} 个文件")
print("期望: 30 个文件 (1摘要 + 6报告 + 4缺陷 + 7日志 + 12阶段状态)")

c.close()