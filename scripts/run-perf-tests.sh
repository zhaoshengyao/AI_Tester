#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if command -v pwsh >/dev/null 2>&1; then
  exec pwsh -NoProfile -File "$ROOT/scripts/run-perf-tests.ps1" "$@"
fi

echo "pwsh 未安装，当前统一阶段契约入口无法在 Bash 下执行 scripts/run-perf-tests.ps1。" >&2
exit 2
