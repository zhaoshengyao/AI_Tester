#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_DIR = ROOT / "stage-manifests"
SCHEMA_PATH = MANIFEST_DIR / "schema.yaml"

EXIT_OK = 0
EXIT_BLOCKED = 2
EXIT_NEEDS_UPDATE = 3
EXIT_INVALID = 4


@dataclass
class PathCheck:
    path: str
    exists: bool
    non_empty: bool
    kind: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "exists": self.exists,
            "non_empty": self.non_empty,
            "kind": self.kind,
        }


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data or {}


def load_schema() -> dict[str, Any]:
    return load_yaml(SCHEMA_PATH)


def get_manifest_map() -> dict[str, Path]:
    manifest_map: dict[str, Path] = {}
    for path in sorted(MANIFEST_DIR.glob("*.yaml")):
        if path.name == "schema.yaml":
            continue
        manifest = load_yaml(path)
        stage_id = manifest.get("stage_id")
        if stage_id:
            manifest_map[stage_id] = path
    return manifest_map


def validate_manifest(path: Path, manifest: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in schema.get("required_top_level_keys", []):
        if key not in manifest:
            errors.append(f"{path.name}: missing top-level key '{key}'")

    driver_type = manifest.get("driver_type")
    if driver_type and driver_type not in schema.get("allowed_driver_types", []):
        errors.append(f"{path.name}: unsupported driver_type '{driver_type}'")

    for field_name in ("required_inputs", "required_outputs"):
        for item in manifest.get(field_name, []):
            for key in schema.get("requirement_group_keys", []):
                if key not in item:
                    errors.append(f"{path.name}: {field_name} item missing '{key}'")
            match_value = item.get("match")
            if match_value and match_value not in schema.get("allowed_match_values", []):
                errors.append(f"{path.name}: invalid match '{match_value}' in {field_name}")
            path_type = item.get("path_type")
            if path_type and path_type not in schema.get("allowed_path_types", []):
                errors.append(f"{path.name}: invalid path_type '{path_type}' in {field_name}")

    for item in manifest.get("required_gates", []):
        gate_type = item.get("gate_type")
        if gate_type and gate_type not in schema.get("gate_types", []):
            errors.append(f"{path.name}: invalid gate_type '{gate_type}'")

    return errors


def resolve_run_id(run_id: str | None) -> str | None:
    if run_id:
        return run_id

    # 优先读 TEST_RUN_ID 环境变量（多系统并行隔离的关键）
    env_run_id = os.environ.get("TEST_RUN_ID")
    if env_run_id:
        return env_run_id

    runs_dir = ROOT / "docs" / "test-runs"
    if not runs_dir.exists():
        return None

    latest = sorted((p.name for p in runs_dir.iterdir() if p.is_dir()), reverse=True)
    return latest[0] if latest else None


def resolve_path(raw_path: str, run_id: str | None, system_id: str | None = None) -> Path:
    result = raw_path.replace("{run_id}", run_id or "")
    if system_id:
        result = result.replace("{system}", system_id)
    return ROOT / result


def check_single_path(path: Path, expected_kind: str) -> PathCheck:
    exists = path.exists()
    non_empty = False
    if exists:
        if path.is_dir():
            try:
                non_empty = any(path.iterdir())
            except OSError:
                non_empty = False
        else:
            non_empty = path.stat().st_size > 0

    return PathCheck(
        path=str(path.relative_to(ROOT)),
        exists=exists,
        non_empty=non_empty,
        kind=expected_kind,
    )


def evaluate_requirement(requirement: dict[str, Any], run_id: str | None, system_id: str | None = None) -> dict[str, Any]:
    path_checks = [
        check_single_path(resolve_path(raw_path, run_id, system_id), requirement["path_type"])
        for raw_path in requirement.get("paths", [])
    ]

    def is_ok(item: PathCheck) -> bool:
        if requirement["path_type"] == "dir":
            return item.exists
        if requirement["path_type"] == "file":
            return item.exists and item.non_empty
        return item.exists

    states = [is_ok(item) for item in path_checks]
    match_all = requirement.get("match", "all") == "all"
    ok = all(states) if match_all else any(states)

    return {
        "name": requirement["name"],
        "match": requirement["match"],
        "path_type": requirement["path_type"],
        "ok": ok,
        "paths": [item.to_dict() for item in path_checks],
        "must_reference_run_id": bool(requirement.get("must_reference_run_id")),
    }


def check_reference_to_run(output_state: dict[str, Any], run_id: str | None) -> tuple[bool, str]:
    if not output_state.get("must_reference_run_id") or not run_id:
        return False, ""

    for item in output_state["paths"]:
        if not item["exists"] or item["kind"] == "dir":
            continue
        absolute = ROOT / item["path"]
        try:
            content = absolute.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = absolute.read_text(encoding="utf-8", errors="ignore")
        if run_id not in content:
            return True, f"{item['path']} does not reference run_id {run_id}"

    return False, ""


def evaluate_gate(gate: dict[str, Any], run_id: str | None, system_id: str | None = None) -> dict[str, Any]:
    gate_type = gate["gate_type"]
    if gate_type == "external":
        return {
            "name": gate["name"],
            "gate_type": gate_type,
            "ok": True,
            "checked": False,
            "reason": gate.get("description", "external gate"),
        }

    requirement = {
        "name": gate["name"],
        "paths": gate.get("paths", []),
        "match": gate.get("match", "all"),
        "path_type": "dir" if gate_type == "dir_exists" else "file",
    }
    result = evaluate_requirement(requirement, run_id, system_id)
    return {
        "name": gate["name"],
        "gate_type": gate_type,
        "ok": result["ok"],
        "checked": True,
        "paths": result["paths"],
    }


def determine_status(
    mode: str,
    inputs_checked: list[dict[str, Any]],
    gates_checked: list[dict[str, Any]],
    outputs_checked: list[dict[str, Any]],
    stale_reasons: list[str],
) -> tuple[str, str]:
    if any(not item["ok"] for item in inputs_checked):
        return "blocked", "required inputs are missing"

    if any(not gate["ok"] for gate in gates_checked):
        return "blocked", "required gates are not satisfied"

    if mode == "preflight":
        return "ready", ""

    if any(not item["ok"] for item in outputs_checked):
        return "not_ready", "required outputs are missing"

    if stale_reasons:
        return "needs_update", "; ".join(stale_reasons)

    return "completed", ""


def status_to_exit_code(status: str) -> int:
    if status in {"ready", "completed"}:
        return EXIT_OK
    if status == "needs_update":
        return EXIT_NEEDS_UPDATE
    return EXIT_BLOCKED


def build_status_payload(
    manifest: dict[str, Any],
    manifest_path: Path,
    run_id: str | None,
    mode: str,
    status: str,
    reason: str,
    inputs_checked: list[dict[str, Any]],
    gates_checked: list[dict[str, Any]],
    outputs_checked: list[dict[str, Any]],
) -> dict[str, Any]:
    evidence_paths: list[str] = []
    for group in outputs_checked:
        for item in group.get("paths", []):
            if item["exists"]:
                evidence_paths.append(item["path"])

    next_decision = {
        "ready": "allow-execution",
        "completed": "allow-next-stage",
        "needs_update": "regenerate-stage-output",
        "blocked": "stop-and-confirm-inputs",
        "not_ready": "finish-stage-output",
    }[status]

    return {
        "stage_id": manifest["stage_id"],
        "display_name": manifest["display_name"],
        "run_id": run_id or "",
        "driver_type": manifest["driver_type"],
        "status": status,
        "inputs_checked": inputs_checked,
        "gates_checked": gates_checked,
        "outputs_written": outputs_checked,
        "evidence_paths": sorted(set(evidence_paths)),
        "next_decision": next_decision,
        "needs_update_reason": reason,
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "check_mode": mode,
        "manifest_path": str(manifest_path.relative_to(ROOT)),
    }


def write_stage_status(run_id: str | None, payload: dict[str, Any], system_id: str | None = None) -> str | None:
    if not run_id:
        return None

    # 优先读 TEST_RUN_DIR 环境变量（多系统隔离），否则用默认 docs/test-runs/<run_id>
    run_dir_env = os.environ.get("TEST_RUN_DIR")
    if run_dir_env:
        run_dir = Path(run_dir_env)
        if not run_dir.is_absolute():
            run_dir = ROOT / run_dir
    else:
        run_dir = ROOT / "docs" / "test-runs" / run_id

    status_dir = run_dir / "stage-status"
    status_dir.mkdir(parents=True, exist_ok=True)
    status_path = status_dir / f"{payload['stage_id']}.json"
    status_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        return str(status_path.relative_to(ROOT))
    except ValueError:
        return str(status_path)


def handle_check_stage(args: argparse.Namespace) -> int:
    schema = load_schema()
    manifest_map = get_manifest_map()
    manifest_path = manifest_map.get(args.stage_id)
    if manifest_path is None:
        print(json.dumps({"error": f"unknown stage_id: {args.stage_id}"}, ensure_ascii=False))
        return EXIT_INVALID

    manifest = load_yaml(manifest_path)
    validation_errors = validate_manifest(manifest_path, manifest, schema)
    if validation_errors:
        print(json.dumps({"errors": validation_errors}, ensure_ascii=False, indent=2))
        return EXIT_INVALID

    system_id = getattr(args, "system", None) or os.environ.get("TEST_SYSTEM_ID")
    run_id = resolve_run_id(args.run_id)
    inputs_checked = [evaluate_requirement(item, run_id, system_id) for item in manifest.get("required_inputs", [])]
    gates_checked = [evaluate_gate(item, run_id, system_id) for item in manifest.get("required_gates", [])]
    outputs_checked = []
    stale_reasons: list[str] = []

    if args.mode == "full":
        outputs_checked = [evaluate_requirement(item, run_id, system_id) for item in manifest.get("required_outputs", [])]
        for output_state in outputs_checked:
            stale, stale_reason = check_reference_to_run(output_state, run_id)
            if stale:
                stale_reasons.append(stale_reason)

    status, reason = determine_status(args.mode, inputs_checked, gates_checked, outputs_checked, stale_reasons)
    payload = build_status_payload(
        manifest=manifest,
        manifest_path=manifest_path,
        run_id=run_id,
        mode=args.mode,
        status=status,
        reason=reason,
        inputs_checked=inputs_checked,
        gates_checked=gates_checked,
        outputs_checked=outputs_checked,
    )

    if args.write_status:
        status_path = write_stage_status(run_id, payload, system_id)
        if status_path:
            payload["status_file"] = status_path

    json_output = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(json_output, encoding="utf-8")
    else:
        print(json_output)
    return status_to_exit_code(status)


def handle_validate_manifests(_: argparse.Namespace) -> int:
    schema = load_schema()
    manifest_map = get_manifest_map()
    errors: list[str] = []
    for stage_id, path in manifest_map.items():
        manifest = load_yaml(path)
        errors.extend(validate_manifest(path, manifest, schema))
        if manifest.get("stage_id") != stage_id:
            errors.append(f"{path.name}: stage_id lookup mismatch")

    if errors:
        print(json.dumps({"errors": errors}, ensure_ascii=False, indent=2))
        return EXIT_INVALID

    print(json.dumps({"validated_manifests": sorted(manifest_map.keys())}, ensure_ascii=False, indent=2))
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stage contract utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check-stage", help="Check one stage against unified manifests")
    check_parser.add_argument("--stage-id", required=True)
    check_parser.add_argument("--run-id")
    check_parser.add_argument("--system", help="System ID (e.g. crm). Falls back to TEST_SYSTEM_ID env var.")
    check_parser.add_argument("--mode", choices=["preflight", "full"], default="full")
    check_parser.add_argument("--write-status", action="store_true")
    check_parser.add_argument("--output", help="Output JSON to file instead of stdout")
    check_parser.set_defaults(func=handle_check_stage)

    validate_parser = subparsers.add_parser("validate-manifests", help="Validate stage manifests")
    validate_parser.set_defaults(func=handle_validate_manifests)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
