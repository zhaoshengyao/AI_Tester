"""
批次 ID 生成器

格式: {YYYYMMDD-HHMMSS}-{system}-{uuid8}
保证多系统并行时批次目录不冲突。
"""
import os
import uuid
from datetime import datetime
from pathlib import Path


def generate_batch_id(system_id: str | None = None) -> str:
    """
    生成批次 ID

    优先级:
    1. TEST_RUN_ID 环境变量
    2. 新生成: {timestamp}-{system}-{uuid8}

    Args:
        system_id: 系统标识（默认从 TEST_SYSTEM_ID 或 'crm'）
    """
    env_run_id = os.environ.get("TEST_RUN_ID")
    if env_run_id:
        return env_run_id

    if system_id is None:
        system_id = os.environ.get("TEST_SYSTEM_ID", "crm")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    short_uuid = uuid.uuid4().hex[:8]
    return f"{timestamp}-{system_id}-{short_uuid}"


def get_batch_dir(root: Path | None = None, system_id: str | None = None) -> Path:
    """
    获取批次目录路径

    优先级:
    1. TEST_RUN_DIR 环境变量
    2. 在 projects/<system>/test-runs/ 下创建新批次

    Args:
        root: 项目根目录
        system_id: 系统标识
    """
    env_run_dir = os.environ.get("TEST_RUN_DIR")
    if env_run_dir:
        run_dir = Path(env_run_dir)
        if not run_dir.is_absolute():
            if root is None:
                root = Path(__file__).resolve().parent.parent.parent
            run_dir = root / run_dir
        return run_dir

    if root is None:
        root = Path(__file__).resolve().parent.parent.parent
    if system_id is None:
        system_id = os.environ.get("TEST_SYSTEM_ID", "crm")

    batch_id = generate_batch_id(system_id)
    batch_dir = root / "projects" / system_id / "test-runs" / batch_id
    return batch_dir


def ensure_batch_dirs(batch_dir: Path) -> Path:
    """确保批次目录结构存在"""
    for subdir in ("reports", "defects", "raw"):
        (batch_dir / subdir).mkdir(parents=True, exist_ok=True)
    return batch_dir


if __name__ == "__main__":
    bid = generate_batch_id()
    print(f"批次 ID: {bid}")
    bdir = get_batch_dir()
    print(f"批次目录: {bdir}")
