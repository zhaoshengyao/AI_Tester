#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ $# -lt 1 ]]; then
  echo "usage: bash scripts/check-stage.sh <stage_id> [run_id] [preflight|full] [--write-status]" >&2
  exit 2
fi

stage_id="$1"
shift

run_id=""
mode="full"
write_status_args=()

if [[ $# -gt 0 && "$1" != "preflight" && "$1" != "full" && "$1" != "--write-status" ]]; then
  run_id="$1"
  shift
fi

if [[ $# -gt 0 && ( "$1" == "preflight" || "$1" == "full" ) ]]; then
  mode="$1"
  shift
fi

if [[ $# -gt 0 && "$1" == "--write-status" ]]; then
  write_status_args+=(--write-status)
  shift
fi

cmd=(python scripts/stage_contract.py check-stage --stage-id "$stage_id" --mode "$mode")
if [[ -n "$run_id" ]]; then
  cmd+=(--run-id "$run_id")
fi
if [[ ${#write_status_args[@]} -gt 0 ]]; then
  cmd+=("${write_status_args[@]}")
fi

"${cmd[@]}"
