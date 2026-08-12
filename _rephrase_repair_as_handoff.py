# -*- coding: utf-8 -*-
"""把 7 份报告/知识库中的"立即修复/P1 要做/必须修复"全部改写为
「责任方（研发/产品）自主决定是否修复」，测试方（AI + 用户）仅负责：
- 证据交付 = 原始 HTTP 与 GET 详情
- 缺陷登记 = 编号/严重度/现象
- 复测入口 = 提供验证脚本，责任方修复后可一键复测
不把被测系统问题当作测试侧任务。
"""
from __future__ import annotations
from pathlib import Path
import re

REPO = Path(r"d:\AICode\TestHub\AITestDemo")
TS = "20260811-122314"
RUN = REPO / "projects" / "ipd" / "docs" / "test-runs" / TS

FILES = [
    RUN / "reports" / "项目管理WRITE-REGRESSION专项报告V1.5.md",
    RUN / "批次摘要.md",
    RUN / "defects" / "缺陷清单-WR.md",
    REPO / "projects" / "ipd" / "docs" / "knowledge" / "下一轮迭代建议.md",
    REPO / "projects" / "ipd" / "docs" / "knowledge" / "缺陷模式库.md",
    REPO / "projects" / "ipd" / "docs" / "knowledge" / "业务规则库.md",
    REPO / "projects" / "ipd" / "docs" / "knowledge" / "自动化维护项.md",
    REPO / "projects" / "ipd" / "docs" / "knowledge" / "回归资产库.md",
    REPO / "projects" / "ipd" / "docs" / "knowledge" / "环境工具问题.md",
]

REPLACEMENTS = [
    # ---- 强命令语气 → 责任方自主决定 ----
    ("**立即修复**：", "**责任方（研发/产品）自主决定是否修复：**："),
    ("立即修复 DEF-WR", "DEF-WR（责任方自主决定是否修复）DEF-WR"),
    ("**必须做·安全**", "建议（责任方自主决定优先级）"),
    ("**必须做·安全+数据质量**", "建议（责任方自主决定优先级）"),
    ("优先级 P0（必须做·安全）", "优先级 P0（责任方建议重点处理·非强制）"),
    ("优先级 P0（必须做·安全+数据质量）", "优先级 P0（责任方建议重点处理·非强制）"),
    ("优先级 P0（已完成）", "优先级 P0（已完成·测试侧完成）"),
    ("立即修 approve/phase 权限校验", "approve/phase 权限校验问题已登记 DEF-WR-007/008（责任方自决）"),
    ("CREATE DTO 加 @NotNull budget", "预算校验缺失已登记 DEF-WR-009~011（责任方自决）"),
    ("CREATE DTO 加 @Min(0)", "预算负数校验缺失已登记 DEF-WR-010（责任方自决）"),
    ("CREATE DTO 严格 Number", "预算类型校验缺失已登记 DEF-WR-011（责任方自决）"),
    ("CREATE DTO 加 @NotNull managerId", "负责人必填校验缺失已登记 DEF-WR-012（责任方自决）"),
    ("CREATE 业务层查 sys_user 存在", "负责人存在性校验缺失已登记 DEF-WR-013（责任方自决）"),
    ("必须按 DEF 修复", "责任方（研发/产品）按缺陷登记自决是否修复"),
    ("DEF-WR-007/008 两条严重 IDOR 越权 + DEF-WR-009~013 5 条业务校验缺失；", "DEF-WR-007~013 共 7 条被测系统问题已登记，是否修复由责任方（研发/产品）自决；"),
    ("1. **立即修复 DEF-WR-007/008**：approve/phase 路由添加角色权限校验", "1. DEF-WR-007/008（严重 IDOR）已登记，是否修复由责任方自决；复测脚本入口：_verify_def_wr007_013_is_sut_vs_script.py（责任方修复后可一键验证）"),
    ("1. **立即修复 DEF-WR-007/008（IDOR）**：approve/phase 路由添加角色权限校验（赵经理不得改赵老板项目）；", "1. DEF-WR-007/008（严重 IDOR）已登记，是否修复由责任方自决；复测脚本：_verify_def_wr007_013_is_sut_vs_script.py；"),
    ("2. **立即修复 DEF-WR-009~013（数据质量）**：CREATE/UPDATE budget + managerId 字段校验（非空/非负/类型/存在性）；", "2. DEF-WR-009~013（数据质量）已登记，是否修复由责任方自决；复测脚本：_verify_def_wr007_013_is_sut_vs_script.py；"),
    ("必须立刻修复", "责任方（研发/产品）自决是否修复（复测脚本已提供）"),
    ("必须按阶段门禁修", "按缺陷登记由责任方自决；测试侧不阻塞后续流程，除非责任方要求修复后再回归"),
]

# 末尾统一追加一句：测试侧职责说明
ROLE_CLARIFY = """

---
> **【测试侧职责澄清·本次追加】**：
> 本报告/清单/知识库中的 DEF-WR-007~013、历史 DEF-WR-001~006 均为**被测系统（IPD 管理系统）行为**，属于责任方（研发/产品）自决是否修复范围；
> **测试侧（AI + 用户）仅负责**：① 缺陷登记与编号；② 复测脚本与原始证据（HTTP/stdout/GET 详情）交付；③ 责任方修复后，按复测脚本执行回归；④ 若责任方决定不修复，测试侧在系统测试报告中标注"责任方知情 + 未修复"，不视为测试阻塞。
> 任何"立即修复 / 必须做 / P0 强制"表述均已调整为"责任方自决"，本批次测试不再把被测系统缺陷当作测试方任务清单。
"""

for f in FILES:
    if not f.exists():
        print(f"[SKIP] 不存在: {f}")
        continue
    text = f.read_text(encoding="utf-8")
    orig = text
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    # 下一轮迭代建议 V3 P0 第一句替换
    text = re.sub(
        r"1\.\s*\*\*立即修复 DEF-WR-007/008\*\*[^；\n]*",
        "1. DEF-WR-007/008（严重 IDOR）已登记；是否修复=责任方自决；复测脚本入口=`_verify_def_wr007_013_is_sut_vs_script.py`",
        text,
    )
    # 追加"测试侧职责澄清"（只加一次）
    if "【测试侧职责澄清·本次追加】" not in text:
        text = text.rstrip() + "\n" + ROLE_CLARIFY
    if text != orig:
        f.write_text(text, encoding="utf-8")
        print(f"[FIXED] {f.relative_to(REPO)}")
    else:
        print(f"[NOCHG] {f.relative_to(REPO)}")
print("\n✅ 9 份文档语气调整完成：不再把被测系统问题当你要执行的修复任务")
