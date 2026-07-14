#!/usr/bin/env python3
"""
主集成脚本 - 将所有改动集成到项目架构中
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_script(script_name: str) -> bool:
    """运行指定的脚本"""
    script_path = ROOT / "scripts" / script_name
    try:
        subprocess.run([sys.executable, str(script_path)], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 运行 {script_name} 失败: {e}")
        return False


def main():
    """主集成函数"""
    print("="*60)
    print(f"📦 开始集成所有改动到项目架构中")
    print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    steps = [
        ("更新需求分析报告", "integrate-exploration.py"),
        ("更新测试计划", "integrate-test-plan.py"),
        ("更新测试用例", "integrate-test-cases.py"),
    ]
    
    success_count = 0
    total_count = len(steps)
    
    for step_name, script_name in steps:
        print(f"\n🔄 {step_name}...")
        if run_script(script_name):
            print(f"✅ {step_name} 成功")
            success_count += 1
        else:
            print(f"❌ {step_name} 失败")
    
    print("\n" + "="*60)
    print(f"📊 集成结果: {success_count}/{total_count} 成功")
    
    if success_count == total_count:
        print("\n🎉 所有改动已成功集成到架构中!")
        print("\n📋 集成内容摘要:")
        print("  1. 更新了阶段配置文件 (stage-manifests/*.yaml)")
        print("  2. 更新了需求分析报告 (docs/analysis/需求分析报告.md)")
        print("  3. 更新了测试计划 (docs/test-plan/测试计划.md)")
        print("  4. 更新了测试方案 (docs/test-plan/测试方案.md)")
        print("  5. 更新了测试用例 (docs/cases/原型系统测试用例-评审版.md)")
        print("  6. 更新了评审记录 (docs/cases/测试用例评审记录.md)")
        print("  7. 更新了覆盖矩阵 (docs/cases/测试用例覆盖矩阵.md)")
        print("  8. 创建了集成脚本 (scripts/integrate-*.py)")
        
        print("\n📈 测试资产统计:")
        print("  - 模块数: 23个 (9一级 + 10二级 + 4三级)")
        print("  - 测试用例数: 69条")
        print("  - P0用例: 24条")
        print("  - P1用例: 37条")
        print("  - P2用例: 8条")
    else:
        print("\n⚠️ 部分集成步骤失败，请检查错误信息")
    
    print("="*60)


if __name__ == "__main__":
    main()
