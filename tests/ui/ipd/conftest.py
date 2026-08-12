# -*- coding: utf-8 -*-
"""tests/ui/ipd/conftest.py — Playwright + pytest IPD UI 公共 fixture
参照 AGENTS.md UI 自动化：Playwright；smoke=登录/首页/核心导航；
账号从 projects/ipd/.env 读取（不硬编码）。
"""
from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
IPD_DIR = PROJECT_ROOT / "projects" / "ipd"
DOTENV = IPD_DIR / ".env"
RUN_DIR = max(
    [p for p in (IPD_DIR / "docs" / "test-runs").glob("*") if p.is_dir()],
    key=lambda p: p.name,
)
RAW_UI = RUN_DIR / "raw" / "ui"
RAW_UI.mkdir(parents=True, exist_ok=True)
REPORT_DIR = RUN_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(DOTENV)

BASE_URL = os.getenv("BASE_URL", "http://192.168.2.97:6090").rstrip("/")
USERNAME = os.getenv("TEST_USERNAME", "赵经理")
PASSWORD = os.getenv("TEST_PASSWORD", "123456")


@pytest.fixture(scope="session")
def ipd_ui_config():
    """UI 配置。"""
    return {
        "base_url": BASE_URL,
        "username": USERNAME,
        "password": PASSWORD,
        "raw_ui_dir": str(RAW_UI),
        "run_ts": RUN_DIR.name,
    }


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """viewport 1440×900，截图完整。"""
    return {
        **browser_context_args,
        "viewport": {"width": 1440, "height": 900},
        "locale": "zh-CN",
    }
