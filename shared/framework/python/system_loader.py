"""
系统配置加载器 - 解析 system.yaml 并注入环境变量

这是 shared/lib/test_framework.sh 的 Python 等价实现，
供 stage_contract.py、check-stage 等 Python 脚本使用。
"""
import os
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("警告: pyyaml 未安装，system_loader 功能受限", file=sys.stderr)
    yaml = None


def find_root(start: Path | None = None) -> Path:
    """从给定路径向上查找项目根目录（包含 projects/ 的目录）"""
    if start is None:
        start = Path(__file__).resolve().parent
        # shared/framework/python/ -> 向上 3 层到根
        start = start.parent.parent.parent
    current = start
    for _ in range(10):
        if (current / "projects").is_dir():
            return current
        if current.parent == current:
            break
        current = current.parent
    return start


ROOT = find_root()


def load_system_config(root: Path | None = None, system_id: str | None = None) -> dict[str, Any]:
    """
    加载系统配置

    Args:
        root: 项目根目录
        system_id: 系统标识（默认从 TEST_SYSTEM_ID 环境变量或 'crm'）

    Returns:
        配置字典，包含:
        - system_id, system_name
        - project_dir: 系统项目目录绝对路径
        - base_url, api_base_url, api_base_path, timeout
        - auth: 认证配置
        - test_scope: 测试范围配置（tests_dir 已拼接 project_dir 前缀）
        - output_dir: 批次输出目录（已拼接 project_dir 前缀）
        - test_cases_dir, test_data_dir
    """
    if root is None:
        root = ROOT
    if system_id is None:
        system_id = os.environ.get("TEST_SYSTEM_ID", "crm")

    project_dir = root / "projects" / system_id
    yaml_path = project_dir / "system.yaml"

    config: dict[str, Any] = {
        "system_id": system_id,
        "system_name": system_id,
        "project_dir": str(project_dir),
        "base_url": "",
        "api_base_path": "/prod-api",
        "api_base_url": "",
        "timeout": 30,
        "auth": {},
        "test_scope": {},
        "output_dir": str(project_dir / "test-runs"),
        "test_cases_dir": str(project_dir / "docs" / "cases"),
        "test_data_dir": str(project_dir / "tests" / "data"),
    }

    if not yaml_path.exists() or yaml is None:
        return config

    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    config["system_id"] = data.get("id", system_id)
    config["system_name"] = data.get("name", system_id)

    # 协议配置
    proto = data.get("protocols", {}).get("default", {})
    if proto:
        proto_cfg = proto.get("config", {})
        config["base_url"] = proto_cfg.get("base_url", "")
        config["api_base_path"] = proto_cfg.get("api_base_path", "/prod-api")
        config["timeout"] = proto_cfg.get("timeout", 30)
        if config["base_url"]:
            base = config["base_url"].rstrip("/")
            path = config["api_base_path"].lstrip("/")
            config["api_base_url"] = f"{base}/{path}"

    # 认证配置
    auth = data.get("auth", {})
    if auth:
        config["auth"] = {
            "type": auth.get("type", ""),
            **auth.get("config", {}),
        }

    # 测试范围（拼接 project_dir 前缀）
    scope = data.get("test_scope", {})
    for test_type in ("api", "ui", "performance", "security"):
        type_cfg = scope.get(test_type, {})
        if type_cfg:
            tests_dir = type_cfg.get("tests_dir", "")
            if tests_dir:
                type_cfg["tests_dir"] = str(project_dir / tests_dir)
            config["test_scope"][test_type] = type_cfg

    # 路径映射
    paths = data.get("paths", {})
    if paths:
        output_dir = paths.get("output_dir", "test-runs")
        config["output_dir"] = str(project_dir / output_dir)
        test_cases = paths.get("test_cases", "docs/cases")
        config["test_cases_dir"] = str(project_dir / test_cases)
        test_data = paths.get("test_data", "tests/data")
        config["test_data_dir"] = str(project_dir / test_data)

    return config


def get_tests_dir(config: dict[str, Any], test_type: str) -> str:
    """获取测试目录绝对路径"""
    scope = config.get("test_scope", {}).get(test_type, {})
    return scope.get("tests_dir", "")


def get_output_dir(config: dict[str, Any]) -> str:
    """获取批次输出目录"""
    return config.get("output_dir", "")


if __name__ == "__main__":
    import json
    cfg = load_system_config()
    print(json.dumps(cfg, indent=2, ensure_ascii=False))
