# -*- coding: utf-8 -*-
"""pytest ini / minimal root so pytest discovery works for tests/api/ipd subdir.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo root + tests dir on sys.path for 'tests.api.ipd...' discovery if needed
REPO_ROOT = Path(__file__).resolve().parents[2]
for p in (str(REPO_ROOT), str(REPO_ROOT / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)
