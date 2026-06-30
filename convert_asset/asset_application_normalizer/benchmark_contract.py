"""EBench task contract evidence for AAN-07."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .model import MILESTONE_AAN07, NormalizeAssetRequest
from .package_layout import TargetPackageLayout


TASK_CONFIG_FIELDS = ("task_id", "benchmark", "asset_id")
REQUIRED_PRIM_FIELDS = (
    "asset_root",
    "manipulated_body",
    "collision_root",
    "spawn_anchor",
    "goal_target",
)
EVALUATOR_FIELDS = ("entrypoint", "metric")


@dataclass(frozen=True)
class BenchmarkContractResult:
    overall_status: str
    return_code: int
    benchmark_contract: dict[str, Any]
    task_contract_report: dict[str, Any]
    stage_gate: dict[str, Any]
    blocked_reasons: list[dict[str, Any]]


def build_not_run_benchmark_contract(reason: str) -> BenchmarkContractResult:
    report = {
        "status": "not_run",
        "reason": reason,
        "task_file_count": 0,
        "required_prim_role_count": 0,
    }
    return BenchmarkContractResult(
        overall_status="blocked",
        return_code=0,
        benchmark_contract={
            "status": "not_run",
            "reason": reason,
            "task_files": {},
            "required_prims": [],
        },
        task_contract_report=report,
        stage_gate={
            "check_id": MILESTONE_AAN07,
            "stage": "benchmark_contract",
            "status": "not_run",
            "summary": reason,
        },
        blocked_reasons=[],
    )


def build_benchmark_contract(
    layout: TargetPackageLayout,
    request: NormalizeAssetRequest,
) -> BenchmarkContractResult:
    if request.contract is None:
        reason = "AAN-07 benchmark contract requires --contract."
        return _blocked_result(
            layout,
            request,
            {},
            reason,
            [
                {
                    "blocker_id": "aan07_block_missing_task_contract",
                    "severity": "blocking",
                    "summary": reason,
                    "required_resolution": "Provide a JSON or simple YAML EBench task contract.",
                }
            ],
        )

    contract, load_blocker = _load_contract_result(request.contract)
    if load_blocker is not None:
        return _blocked_result(layout, request, {}, load_blocker["summary"], [load_blocker])

    blockers = [
        *_required_field_blockers(contract, request),
        *_identity_blockers(contract, request),
    ]
    required_records = _required_prim_records(contract, request)
    stage_records, stage_blockers = _stage_prim_records(layout.root_usd, required_records)
    blockers.extend(stage_blockers)
    status = "blocked" if blockers else "pass"

    if status == "blocked":
        return _blocked_result(
            layout,
            request,
            contract,
            "AAN-07 found blocking task contract gaps.",
            blockers,
            required_prims=stage_records or required_records,
        )

    task_files = _write_task_files(layout, request, contract, stage_records)
    benchmark_contract = {
        "status": "pass",
        "contract_source": str(request.contract),
        "target_benchmark": request.target_benchmark,
        "task_id": request.task_id,
        "task_files": task_files,
        "required_prims": stage_records,
        "evaluator": dict(contract.get("evaluator", {})),
        "ready_for_ebench_task_contract": True,
    }
    report = {
        "status": "pass",
        "contract_source": str(request.contract),
        "task_file_count": len(task_files),
        "required_prim_role_count": len(stage_records),
        "evaluator_entrypoint": contract["evaluator"]["entrypoint"],
        "metric": contract["evaluator"]["metric"],
    }
    return BenchmarkContractResult(
        overall_status="pass",
        return_code=0,
        benchmark_contract=benchmark_contract,
        task_contract_report=report,
        stage_gate={
            "check_id": MILESTONE_AAN07,
            "stage": "benchmark_contract",
            "status": "pass",
            "summary": "AAN-07 wrote EBench task contract files.",
        },
        blocked_reasons=[],
    )


def _blocked_result(
    layout: TargetPackageLayout,
    request: NormalizeAssetRequest,
    contract: dict[str, Any],
    reason: str,
    blockers: list[dict[str, Any]],
    *,
    required_prims: list[dict[str, Any]] | None = None,
) -> BenchmarkContractResult:
    benchmark_contract = {
        "status": "blocked",
        "contract_source": str(request.contract) if request.contract else None,
        "target_benchmark": request.target_benchmark,
        "task_id": request.task_id,
        "task_files": {},
        "required_prims": required_prims or _required_prim_records(contract, request),
        "evaluator": dict(contract.get("evaluator", {})) if isinstance(contract.get("evaluator"), dict) else {},
        "ready_for_ebench_task_contract": False,
        "reason": reason,
    }
    report = {
        "status": "blocked",
        "contract_source": str(request.contract) if request.contract else None,
        "task_file_count": 0,
        "required_prim_role_count": len(benchmark_contract["required_prims"]),
        "reason": reason,
    }
    return BenchmarkContractResult(
        overall_status="blocked",
        return_code=5,
        benchmark_contract=benchmark_contract,
        task_contract_report=report,
        stage_gate={
            "check_id": MILESTONE_AAN07,
            "stage": "benchmark_contract",
            "status": "blocked",
            "summary": reason,
        },
        blocked_reasons=blockers,
    )


def _load_contract_result(path: Path) -> tuple[dict[str, Any], dict[str, Any] | None]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return {}, {
            "blocker_id": "aan07_block_contract_load",
            "severity": "blocking",
            "summary": f"Could not read benchmark contract: {path}",
            "detail": str(exc),
            "required_resolution": "Provide a readable JSON or simple YAML contract file.",
        }

    try:
        if path.suffix.lower() == ".json":
            data = json.loads(text)
        else:
            data = _parse_simple_yaml(text)
    except (ValueError, json.JSONDecodeError) as exc:
        return {}, {
            "blocker_id": "aan07_block_contract_load",
            "severity": "blocking",
            "summary": f"Could not parse benchmark contract: {path}",
            "detail": str(exc),
            "required_resolution": "Fix the task contract syntax.",
        }

    if not isinstance(data, dict):
        return {}, {
            "blocker_id": "aan07_block_contract_load",
            "severity": "blocking",
            "summary": "Benchmark contract root must be a mapping.",
            "required_resolution": "Use task_config, required_prims, and evaluator mapping sections.",
        }
    return data, None


def _required_field_blockers(contract: dict[str, Any], request: NormalizeAssetRequest) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for section, fields in (
        ("task_config", TASK_CONFIG_FIELDS),
        ("required_prims", REQUIRED_PRIM_FIELDS),
        ("evaluator", EVALUATOR_FIELDS),
    ):
        mapping = contract.get(section)
        if not isinstance(mapping, dict):
            blockers.append(_missing_field_blocker(section))
            continue
        for field in fields:
            if _is_missing(mapping.get(field)):
                blockers.append(_missing_field_blocker(f"{section}.{field}"))

    required_prims = contract.get("required_prims")
    if isinstance(required_prims, dict) and request.asset_class == "articulated":
        if _is_missing(required_prims.get("articulation_root")):
            blockers.append(_missing_field_blocker("required_prims.articulation_root"))
    return blockers


def _identity_blockers(contract: dict[str, Any], request: NormalizeAssetRequest) -> list[dict[str, Any]]:
    task_config = contract.get("task_config")
    if not isinstance(task_config, dict):
        return []
    checks = (
        ("task_id", request.task_id, "aan07_block_task_id_mismatch"),
        ("benchmark", request.target_benchmark, "aan07_block_benchmark_mismatch"),
        ("asset_id", request.asset_id, "aan07_block_asset_id_mismatch"),
    )
    blockers = []
    for field, expected, blocker_id in checks:
        value = task_config.get(field)
        if not _is_missing(value) and str(value) != str(expected):
            blockers.append(
                {
                    "blocker_id": blocker_id,
                    "severity": "blocking",
                    "summary": f"Contract task_config.{field} does not match normalize request.",
                    "expected": str(expected),
                    "actual": str(value),
                    "required_resolution": "Align the task contract with CLI request metadata.",
                }
            )
    return blockers


def _missing_field_blocker(field_path: str) -> dict[str, Any]:
    return {
        "blocker_id": f"aan07_block_missing_{field_path.replace('.', '_')}",
        "severity": "blocking",
        "summary": f"Benchmark contract is missing required field: {field_path}",
        "field": field_path,
        "required_resolution": "Provide the missing EBench task contract field.",
    }


def _required_prim_records(contract: dict[str, Any], request: NormalizeAssetRequest) -> list[dict[str, Any]]:
    required_prims = contract.get("required_prims")
    if not isinstance(required_prims, dict):
        return []
    roles = list(REQUIRED_PRIM_FIELDS)
    if request.asset_class == "articulated" or not _is_missing(required_prims.get("articulation_root")):
        roles.append("articulation_root")
    records = []
    for role in roles:
        value = required_prims.get(role)
        records.append(
            {
                "role": role,
                "path": None if _is_missing(value) else str(value),
                "required": role != "articulation_root" or request.asset_class == "articulated",
                "status": "missing" if _is_missing(value) else "pending",
            }
        )
    return records


def _stage_prim_records(
    root_usd: Path,
    required_records: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        from pxr import Usd  # type: ignore
    except Exception as exc:
        return required_records, [
            {
                "blocker_id": "aan07_block_stage_open",
                "severity": "blocking",
                "summary": "AAN-07 could not import pxr.Usd for required prim validation.",
                "detail": str(exc),
                "required_resolution": "Run AAN under the Isaac/USD Python environment.",
            }
        ]

    try:
        stage = Usd.Stage.Open(str(root_usd))
    except Exception as exc:
        return required_records, [
            {
                "blocker_id": "aan07_block_stage_open",
                "severity": "blocking",
                "summary": f"AAN-07 could not open package root USD: {root_usd}",
                "detail": str(exc),
                "required_resolution": "Fix the package USD so Usd.Stage.Open succeeds.",
            }
        ]
    if stage is None:
        return required_records, [
            {
                "blocker_id": "aan07_block_stage_open",
                "severity": "blocking",
                "summary": f"AAN-07 could not open package root USD: {root_usd}",
                "required_resolution": "Fix the package USD so Usd.Stage.Open succeeds.",
            }
        ]

    records = []
    blockers = []
    for record in required_records:
        path = record.get("path")
        if _is_missing(path):
            records.append({**record, "exists": False, "status": "missing"})
            continue
        if str(path).upper() == "N/A":
            records.append({**record, "exists": None, "status": "not_applicable"})
            continue
        prim = stage.GetPrimAtPath(str(path))
        exists = bool(prim and prim.IsValid())
        status = "pass" if exists else "blocked"
        records.append({**record, "exists": exists, "status": status})
        if not exists:
            blockers.append(
                {
                    "blocker_id": "aan07_block_required_prim_missing",
                    "severity": "blocking",
                    "summary": "Required benchmark prim path is absent in the packaged USD.",
                    "role": record.get("role"),
                    "path": path,
                    "required_resolution": "Fix the task contract required prim mapping or package USD.",
                }
            )
    return records, blockers


def _write_task_files(
    layout: TargetPackageLayout,
    request: NormalizeAssetRequest,
    contract: dict[str, Any],
    required_records: list[dict[str, Any]],
) -> dict[str, str]:
    layout.task_config.parent.mkdir(parents=True, exist_ok=True)
    task_config = {
        **dict(contract["task_config"]),
        "root_usd": "asset.usd",
        "target_runtime_profile": request.target_runtime,
        "target_benchmark_profile": request.target_benchmark,
    }
    required_prims = {
        "task_id": request.task_id,
        "required_prims": required_records,
    }
    evaluator = dict(contract["evaluator"])
    _write_yaml(layout.task_config, task_config)
    _write_yaml(layout.required_prims, required_prims)
    _write_yaml(layout.evaluator, evaluator)
    return {
        "task_config": "task/task_config.yaml",
        "required_prims": "task/required_prims.yaml",
        "evaluator": "task/evaluator.yaml",
    }


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(_dump_yaml(data), encoding="utf-8")


def _dump_yaml(data: Any, indent: int = 0) -> str:
    lines = _dump_yaml_lines(data, indent)
    return "\n".join(lines) + "\n"


def _dump_yaml_lines(data: Any, indent: int = 0) -> list[str]:
    prefix = " " * indent
    if isinstance(data, dict):
        lines: list[str] = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.extend(_dump_yaml_lines(value, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {_format_yaml_scalar(value)}")
        return lines
    if isinstance(data, list):
        lines = []
        for item in data:
            if isinstance(item, dict):
                lines.append(f"{prefix}-")
                lines.extend(_dump_yaml_lines(item, indent + 2))
            else:
                lines.append(f"{prefix}- {_format_yaml_scalar(item)}")
        return lines
    return [f"{prefix}{_format_yaml_scalar(data)}"]


def _format_yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if not text or text.upper() == "N/A" or any(ch in text for ch in ":#[]{}&,*?|-<>=!%@\\"):
        return json.dumps(text, ensure_ascii=False)
    return text


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line.startswith("\t"):
            raise ValueError("tabs are not supported in simple YAML contracts")
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if ":" not in line:
            raise ValueError(f"invalid YAML line: {raw_line}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if not value:
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _parse_yaml_scalar(value)
    return root


def _parse_yaml_scalar(value: str) -> Any:
    if value in {"null", "Null", "NULL", "~"}:
        return None
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        pass
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _is_missing(value: Any) -> bool:
    return value is None or value == ""
