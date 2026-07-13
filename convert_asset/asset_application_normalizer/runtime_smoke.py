"""Isaac Sim 4.1 runtime smoke evidence for AAN-06."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any
import uuid

from .model import MILESTONE_AAN06, NormalizeAssetRequest, validate_scope_prim_paths
from .package_layout import TargetPackageLayout


MATERIAL_VIEW_SPECS = (
    {"view_id": "front", "elevation": 20.0, "azimuth": 0.0},
    {"view_id": "orbit_3q", "elevation": 35.0, "azimuth": 45.0},
    {"view_id": "side", "elevation": 25.0, "azimuth": 90.0},
)

PHYSX_WARNING_PATTERNS = {
    "negative_mass": re.compile(r"\bnegative\s+mass\b", re.IGNORECASE),
    "invalid_inertia": re.compile(
        r"\b(?:invalid\s+inertia|possibly\s+invalid\s+inertia\s+tensor)\b",
        re.IGNORECASE,
    ),
    "small_sphere_approximated_inertia": re.compile(
        r"\bsmall\s+sphere\s+approximated\s+inertia\b",
        re.IGNORECASE,
    ),
}
PHYSX_PRIM_RE = re.compile(r"\b(?:rigid body|body)\s+at\s+(?P<prim>/[^\s,]+)", re.IGNORECASE)
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")

# AAN normally runs the static USD work through the repository's default Isaac
# wrapper.  An explicit target runtime must not inherit that wrapper's Kit
# bootstrap, otherwise a 4.1 Python can silently start a 4.5 Kit process.
_PARENT_KIT_BOOTSTRAP_VARIABLES = (
    "ISAAC_SIM_ROOT",
    "ISAAC_PATH",
    "ISAACSIM_PATH",
    "CARB_APP_PATH",
    "EXP_PATH",
    "KIT_APP_NAME",
    "OMNI_KIT_ROOT",
    "OMNI_EXTENSIONS_PATH",
    "PYTHONPATH",
    "PYTHONHOME",
)


@dataclass(frozen=True)
class RuntimeSmokeResult:
    overall_status: str
    return_code: int
    runtime_evidence: dict[str, Any]
    stage_gate: dict[str, Any]
    blocked_reasons: list[dict[str, Any]]
    extra_commands: dict[str, Any] = field(default_factory=dict)


def build_not_run_runtime_smoke(reason: str) -> RuntimeSmokeResult:
    return RuntimeSmokeResult(
        overall_status="blocked",
        return_code=0,
        runtime_evidence={
            "status": "not_run",
            "reason": reason,
            "required_gate": "runtime",
        },
        stage_gate={
            "check_id": MILESTONE_AAN06,
            "stage": "runtime_smoke",
            "status": "not_run",
            "summary": reason,
        },
        blocked_reasons=[],
    )


def build_runtime_smoke(
    layout: TargetPackageLayout,
    request: NormalizeAssetRequest,
    *,
    timeout_seconds: int = 240,
) -> RuntimeSmokeResult:
    repo_root = Path(__file__).resolve().parents[2]
    evidence_dir = layout.root / "evidence" / "runtime_smoke"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    report_path = evidence_dir / "report.json"
    render_path = evidence_dir / "render.png"
    material_view_dir = evidence_dir / "material_views"
    stdout_path = evidence_dir / "stdout.log"
    stderr_path = evidence_dir / "stderr.log"
    if not layout.root_usd.is_file():
        report = {
            "status": "blocked",
            "cold_load": {
                "status": "blocked",
                "reason": f"package root USD does not exist: {layout.root_usd}",
            },
        }
        return _runtime_result(layout, report, {"stage": "runtime_smoke", "argv": []}, 5)
    runtime_run_id = uuid.uuid4().hex
    root_usd_sha256 = _sha256_file(layout.root_usd)
    wrapper = repo_root / "scripts" / "isaac_python.sh"
    runner = request.runtime_python.resolve() if request.runtime_python else wrapper
    if request.runtime_python is not None and not runner.is_file():
        report = {
            "status": "blocked",
            "runtime_profile_gate": {
                "status": "blocked",
                "reason": f"explicit runtime Python does not exist: {runner}",
            },
        }
        return _runtime_result(layout, report, {"stage": "runtime_smoke", "argv": []}, 5)
    runtime_environment, runtime_environment_policy = runtime_subprocess_environment(
        runner,
        explicit_runner=request.runtime_python is not None,
    )
    _clear_runtime_evidence_artifacts(
        report_path=report_path,
        render_path=render_path,
        material_view_dir=material_view_dir,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        warning_diff_path=evidence_dir / "warning_diff.json",
    )
    argv = [
        str(runner),
        "-m",
        "convert_asset.asset_application_normalizer.runtime_smoke",
        "--worker",
        "--root-usd",
        str(layout.root_usd),
        "--report-out",
        str(report_path),
        "--render-out",
        str(render_path),
        "--material-view-dir",
        str(material_view_dir),
        "--asset-id",
        request.asset_id,
        "--run-id",
        runtime_run_id,
        "--expected-root-usd-sha256",
        root_usd_sha256,
        "--width",
        "256",
        "--height",
        "192",
        "--warmup-steps",
        "4",
        "--render-steps",
        "1",
        "--step-frames",
        "2",
        "--expected-runtime-version",
        request.expected_runtime_version,
        "--process-exit-policy",
        "os-exit",
    ]
    for prim_path in request.required_prims:
        argv.extend(["--required-prim", prim_path])
    for prim_path in request.effective_asset_scope_prims:
        argv.extend(["--asset-scope-prim", prim_path])

    command_record = {
        "stage": "runtime_smoke",
        "cwd": str(repo_root),
        "argv": argv,
        "run_id": runtime_run_id,
        "root_usd_sha256": root_usd_sha256,
        "env_policy": {
            "allowed_existing_conda_env": "isaac41",
            "mutation_allowed": False,
            "headless_only": True,
            "runner_kind": "explicit_python" if request.runtime_python else "scripts/isaac_python.sh",
            "runner": str(runner),
            "runner_sha256": _sha256_file(runner) if runner.is_file() else None,
            "expected_runtime_version": request.expected_runtime_version,
            **runtime_environment_policy,
        },
        "stdout_path": _package_relative(layout.root, stdout_path),
        "stderr_path": _package_relative(layout.root, stderr_path),
        "report_path": _package_relative(layout.root, report_path),
        "render_path": _package_relative(layout.root, render_path),
        "material_view_dir": _package_relative(layout.root, material_view_dir),
    }

    try:
        completed = subprocess.run(
            argv,
            cwd=repo_root,
            env=runtime_environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )
        stdout_path.write_text(completed.stdout or "", encoding="utf-8")
        stderr_path.write_text(completed.stderr or "", encoding="utf-8")
        exit_code = int(completed.returncode)
    except subprocess.TimeoutExpired as exc:
        stdout_path.write_text(_coerce_process_text(exc.stdout), encoding="utf-8")
        stderr_path.write_text(_coerce_process_text(exc.stderr), encoding="utf-8")
        exit_code = 124
        report = {
            "status": "blocked",
            "cold_load": {
                "status": "blocked",
                "reason": f"runtime smoke timed out after {timeout_seconds} seconds",
            },
        }
        _write_report(report_path, report)
        return _runtime_result(layout, report, command_record, exit_code)

    report = _read_report(report_path)
    if report is None:
        report = {
            "status": "blocked",
            "cold_load": {
                "status": "blocked",
                "reason": "runtime worker did not write a report JSON",
            },
        }
    else:
        report_binding = _runtime_report_binding(
            report,
            run_id=runtime_run_id,
            root_usd_sha256=root_usd_sha256,
        )
        report["runtime_report_binding"] = report_binding
        if report_binding["status"] == "blocked":
            report["status"] = "blocked"
            report["cold_load"] = {
                "status": "blocked",
                "reason": "runtime worker report did not bind to this invocation",
            }
    warning_gate = _build_runtime_physx_warning_gate(
        stdout_path,
        stderr_path,
        request.effective_asset_scope_prims,
    )
    report["physics_warning_gate"] = warning_gate
    report["scope_map"] = {
        "source_scope_prims": request.effective_asset_scope_prims,
        "package_scope_prims": request.effective_asset_scope_prims,
        "runtime_scope_prims": request.effective_asset_scope_prims,
        "mapping_kind": "package_direct_identity",
        "relative_suffix": True,
    }
    if request.warning_baseline_log is not None:
        diff = build_physx_warning_diff(
            parse_physx_warning_events(
                request.warning_baseline_log.read_text(encoding="utf-8", errors="replace"),
                stream="baseline",
            ),
            warning_gate["events"],
            baseline_scopes=request.warning_baseline_scope_prims or request.effective_asset_scope_prims,
            candidate_scopes=request.effective_asset_scope_prims,
        )
        diff["baseline_log"] = str(request.warning_baseline_log)
        diff["baseline_sha256"] = _sha256_file(request.warning_baseline_log)
        diff_path = evidence_dir / "warning_diff.json"
        _write_report(diff_path, diff)
        report["warning_diff"] = {
            **diff,
            "path": _package_relative(layout.root, diff_path),
        }
        if diff["status"] != "pass":
            report["status"] = "blocked"
    else:
        report["warning_diff"] = {"status": "not_requested"}
    if warning_gate["status"] != "pass":
        report["status"] = "blocked"
    _write_report(report_path, report)
    return _runtime_result(layout, report, command_record, exit_code)


def _clear_runtime_evidence_artifacts(
    *,
    report_path: Path,
    render_path: Path,
    material_view_dir: Path,
    stdout_path: Path,
    stderr_path: Path,
    warning_diff_path: Path,
) -> None:
    """Remove prior worker evidence so an exit-zero process cannot reuse it."""
    for path in (report_path, render_path, stdout_path, stderr_path, warning_diff_path):
        try:
            path.unlink()
        except FileNotFoundError:
            pass
    if material_view_dir.exists():
        shutil.rmtree(material_view_dir)


def _runtime_report_binding(
    report: dict[str, Any],
    *,
    run_id: str,
    root_usd_sha256: str,
) -> dict[str, Any]:
    errors: list[str] = []
    if report.get("run_id") != run_id:
        errors.append("worker run_id does not match this runtime invocation")
    if report.get("root_usd_sha256") != root_usd_sha256:
        errors.append("worker root_usd_sha256 does not match the package entry USD")
    if report.get("expected_root_usd_sha256") != root_usd_sha256:
        errors.append("worker expected_root_usd_sha256 does not match the invocation")
    return {
        "status": "pass" if not errors else "blocked",
        "run_id": run_id,
        "root_usd_sha256": root_usd_sha256,
        "errors": errors,
    }


def runtime_subprocess_environment(
    runner: Path,
    *,
    explicit_runner: bool,
    parent_environment: dict[str, str] | None = None,
) -> tuple[dict[str, str], dict[str, Any]]:
    """Return the child environment and auditable explicit-runner policy.

    `scripts/isaac_python.sh` legitimately configures the repository's default
    runtime.  In contrast, a user-selected Python is a versioned target
    contract.  Its process receives a clean Kit/Python bootstrap and only its
    own CUDA/Torch shared-library directories, so the profile gate measures the
    intended installation rather than whichever Isaac wrapper launched AAN.
    """
    environment = dict(os.environ if parent_environment is None else parent_environment)
    if not explicit_runner:
        return environment, {
            "status": "not_applicable",
            "isolated_explicit_runtime_environment": False,
            "removed_parent_variables": [],
            "runtime_library_prefixes": [],
        }

    removed = []
    for name in _PARENT_KIT_BOOTSTRAP_VARIABLES:
        if name in environment:
            environment.pop(name)
            removed.append(name)

    # Do not preserve a parent LD_LIBRARY_PATH: it can preload a different
    # Isaac Kit's carb/USD/renderer libraries even after PYTHONPATH is scrubbed.
    environment.pop("LD_LIBRARY_PATH", None)
    runtime_prefix = runner.parent.parent
    runtime_library_dirs = sorted(
        {
            path
            for pattern in (
                "lib/python[0-9].[0-9][0-9]/site-packages/nvidia/cuda_runtime/lib",
                "lib/python[0-9].[0-9][0-9]/site-packages/torch/lib",
            )
            for path in runtime_prefix.glob(pattern)
            if path.is_dir()
        },
        key=lambda item: str(item),
    )
    if runtime_library_dirs:
        environment["LD_LIBRARY_PATH"] = os.pathsep.join(
            str(path) for path in runtime_library_dirs
        )
    environment["PYTHONNOUSERSITE"] = "1"
    environment["ACCEPT_EULA"] = "Y"
    environment["OMNI_KIT_ACCEPT_EULA"] = "YES"
    return environment, {
        "status": "pass",
        "isolated_explicit_runtime_environment": True,
        "removed_parent_variables": removed,
        "runtime_library_prefixes": [str(path) for path in runtime_library_dirs],
    }


def _runtime_result(
    layout: TargetPackageLayout,
    report: dict[str, Any],
    command_record: dict[str, Any],
    exit_code: int,
) -> RuntimeSmokeResult:
    command_record = {**command_record, "exit_code": exit_code}
    report = {
        **report,
        "command_id": "runtime_smoke_001",
        "stdout_path": command_record.get("stdout_path"),
        "stderr_path": command_record.get("stderr_path"),
    }
    status = "pass" if exit_code == 0 and report.get("status") == "pass" else "blocked"
    if status == "pass":
        blockers: list[dict[str, Any]] = []
        summary = "AAN-06 Isaac Sim runtime smoke passed."
        return_code = 0
    else:
        blockers = [
            {
                "blocker_id": "aan06_block_runtime_smoke",
                "severity": "blocking",
                "summary": "Isaac Sim runtime smoke did not complete successfully.",
                "exit_code": exit_code,
                "required_resolution": "Inspect runtime smoke stdout/stderr and fix load, render, step, or reset failures.",
            }
        ]
        warning_gate = report.get("physics_warning_gate")
        if isinstance(warning_gate, dict) and warning_gate.get("status") == "blocked":
            blockers.append(
                {
                    "blocker_id": "aan06_block_scoped_physx_warning",
                    "severity": "blocking",
                    "summary": "A scoped PhysX negative-mass or inertia warning was found in runtime output.",
                    "warning_summary": warning_gate.get("summary", {}),
                    "required_resolution": "Remove the package-scoped physics defect or use a declared visual_static role that strips the scoped physics semantics.",
                }
            )
        summary = "AAN-06 Isaac Sim runtime smoke blocked."
        return_code = 5
        report["status"] = "blocked"

    return RuntimeSmokeResult(
        overall_status=status,
        return_code=return_code,
        runtime_evidence=report,
        stage_gate={
            "check_id": MILESTONE_AAN06,
            "stage": "runtime_smoke",
            "status": status,
            "summary": summary,
        },
        blocked_reasons=blockers,
        extra_commands={"runtime_smoke_001": command_record},
    )


def _read_report(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _package_relative(package_root: Path, path: Path) -> str:
    try:
        return path.relative_to(package_root).as_posix()
    except ValueError:
        return str(path)


def parse_physx_warning_events(text: str, *, stream: str) -> list[dict[str, Any]]:
    """Parse only the PhysX mass/inertia warning family into stable evidence rows."""
    events = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = ANSI_ESCAPE_RE.sub("", raw_line)
        categories = [
            name for name, pattern in PHYSX_WARNING_PATTERNS.items() if pattern.search(line)
        ]
        if not categories:
            continue
        match = PHYSX_PRIM_RE.search(line)
        prim_path = match.group("prim").rstrip(".,;:") if match else None
        events.append(
            {
                "stream": stream,
                "line_number": line_number,
                "line_sha256": hashlib.sha256(line.encode("utf-8")).hexdigest(),
                "prim_path": prim_path,
                "categories": sorted(categories),
                "raw_line": line,
            }
        )
    return events


def evaluate_physx_warning_scope(
    events: list[dict[str, Any]],
    scope_prims: list[str],
) -> dict[str, Any]:
    """Fail closed for scoped or unattributed mass/inertia warnings."""
    scope_validation = validate_scope_prim_paths(scope_prims)
    scoped = []
    out_of_scope = []
    unattributed = []
    counters = {name: 0 for name in PHYSX_WARNING_PATTERNS}
    if scope_validation["status"] != "pass":
        return {
            "status": "blocked",
            "scope_prims": scope_prims,
            "scope_validation": scope_validation,
            "events": events,
            "scoped_events": [],
            "out_of_scope_events": [],
            "unattributed_events": events,
            "summary": {
                "scoped_event_count": 0,
                "out_of_scope_event_count": 0,
                "unattributed_event_count": len(events),
                "by_category": {},
            },
            "parser_version": "aan06.physx_scope.v2",
        }
    for event in events:
        path = event.get("prim_path")
        if not isinstance(path, str) or not path.startswith("/"):
            unattributed.append(event)
            continue
        matches = _scope_relative_matches(path, scope_prims)
        if len(matches) == 1:
            scoped.append(event)
            for category in event.get("categories", []):
                if category in counters:
                    counters[category] += 1
        elif len(matches) > 1:
            unattributed.append({**event, "scope_mapping": "ambiguous"})
        else:
            out_of_scope.append(event)
    status = "blocked" if scoped or unattributed else "pass"
    return {
        "status": status,
        "scope_prims": scope_prims,
        "scope_validation": scope_validation,
        "events": events,
        "scoped_events": scoped,
        "out_of_scope_events": out_of_scope,
        "unattributed_events": unattributed,
        "summary": {
            "scoped_event_count": len(scoped),
            "out_of_scope_event_count": len(out_of_scope),
            "unattributed_event_count": len(unattributed),
            "by_category": {name: count for name, count in counters.items() if count},
        },
        "parser_version": "aan06.physx_scope.v2",
    }


def build_physx_warning_diff(
    baseline_events: list[dict[str, Any]],
    candidate_events: list[dict[str, Any]],
    *,
    baseline_scopes: list[str],
    candidate_scopes: list[str],
) -> dict[str, Any]:
    """Compare normalized {scope-relative prim, category} counters, not timestamps."""
    baseline_validation = validate_scope_prim_paths(baseline_scopes)
    candidate_validation = validate_scope_prim_paths(candidate_scopes)
    baseline = _canonical_warning_counter(baseline_events, baseline_scopes)
    candidate = _canonical_warning_counter(candidate_events, candidate_scopes)
    keys = sorted(set(baseline) | set(candidate))
    rows = []
    for key in keys:
        before = baseline.get(key, 0)
        after = candidate.get(key, 0)
        rows.append(
            {
                "canonical_prim": key[0],
                "category": key[1],
                "baseline_count": before,
                "candidate_count": after,
                "removed": max(before - after, 0),
                "introduced": max(after - before, 0),
            }
        )
    return {
        "status": "pass"
        if baseline_validation["status"] == "pass"
        and candidate_validation["status"] == "pass"
        and not candidate
        else "blocked",
        "baseline_scope_prims": baseline_scopes,
        "candidate_scope_prims": candidate_scopes,
        "scope_validation": {
            "baseline": baseline_validation,
            "candidate": candidate_validation,
        },
        "comparison_basis": "canonical_scope_relative_prim_and_category",
        "rows": rows,
        "summary": {
            "baseline_scoped_count": sum(baseline.values()),
            "candidate_scoped_count": sum(candidate.values()),
            "removed_count": sum(max(baseline.get(key, 0) - candidate.get(key, 0), 0) for key in keys),
            "introduced_count": sum(max(candidate.get(key, 0) - baseline.get(key, 0), 0) for key in keys),
        },
    }


def _canonical_warning_counter(events: list[dict[str, Any]], scopes: list[str]) -> dict[tuple[str, str], int]:
    counter: dict[tuple[str, str], int] = {}
    for event in events:
        path = event.get("prim_path")
        if not isinstance(path, str):
            continue
        relative = _scope_relative_path(path, scopes)
        if relative is None:
            continue
        for category in event.get("categories", []):
            key = (relative, str(category))
            counter[key] = counter.get(key, 0) + 1
    return counter


def _path_in_scope(path: str, scopes: list[str]) -> bool:
    return _scope_relative_path(path, scopes) is not None


def _scope_relative_path(path: str, scopes: list[str]) -> str | None:
    matches = _scope_relative_matches(path, scopes)
    return matches[0] if len(matches) == 1 else None


def _scope_relative_matches(path: str, scopes: list[str]) -> list[str]:
    matches = []
    for index, scope in enumerate(scopes):
        normalized = scope.rstrip("/") or "/"
        if path == normalized:
            matches.append((len(normalized), f"scope_{index}"))
        elif path.startswith(normalized + "/"):
            matches.append((len(normalized), f"scope_{index}" + path[len(normalized) :]))
    return [item[1] for item in matches]


def _build_runtime_physx_warning_gate(
    stdout_path: Path,
    stderr_path: Path,
    scope_prims: list[str],
) -> dict[str, Any]:
    events = []
    for path, stream in ((stdout_path, "stdout"), (stderr_path, "stderr")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        events.extend(parse_physx_warning_events(text, stream=stream))
    result = evaluate_physx_warning_scope(events, scope_prims)
    result["log_hashes"] = {
        "stdout": _sha256_file(stdout_path) if stdout_path.exists() else None,
        "stderr": _sha256_file(stderr_path) if stderr_path.exists() else None,
    }
    return result


def _worker_report(
    args: argparse.Namespace,
    *,
    close_simulation_app: bool = True,
) -> dict[str, Any]:
    root_usd = Path(args.root_usd).resolve()
    required_prims = list(args.required_prim or [])
    asset_scope_prims = list(args.asset_scope_prim or [])
    render_path = Path(args.render_out).resolve()
    report_path = Path(args.report_out).resolve()
    report: dict[str, Any] = {
        "status": "blocked",
        "runtime_profile": "isaac41",
        "expected_runtime_version": str(args.expected_runtime_version),
        "run_id": str(args.run_id),
        "expected_root_usd_sha256": str(args.expected_root_usd_sha256),
        "runtime_profile_gate": {"status": "not_run"},
        "asset_id": str(args.asset_id),
        "root_usd": str(root_usd),
        "required_prims": required_prims,
        "asset_scope_prims": asset_scope_prims,
        "cold_load": {"status": "not_run"},
        "render_readback": {"status": "not_run"},
        "material_view_evidence": [],
        "physics_step": {"status": "not_run"},
        "reset": {"status": "not_run"},
        "environment": {},
    }
    if not root_usd.exists():
        report["cold_load"] = {
            "status": "blocked",
            "reason": f"root USD not found: {root_usd}",
        }
        return report
    report["root_usd_sha256"] = _sha256_file(root_usd)
    if report["root_usd_sha256"] != report["expected_root_usd_sha256"]:
        report["cold_load"] = {
            "status": "blocked",
            "reason": "package root USD changed after the parent runtime invocation was bound",
        }
        return report
    scope_validation = validate_scope_prim_paths(asset_scope_prims)
    report["asset_scope_validation"] = scope_validation
    if scope_validation["status"] != "pass":
        report["cold_load"] = {
            "status": "blocked",
            "reason": "invalid runtime asset scope: " + "; ".join(scope_validation["errors"]),
        }
        return report

    simulation_app = None
    world = None
    try:
        from isaacsim import SimulationApp  # type: ignore

        simulation_app = SimulationApp(
            {
                "headless": True,
                "anti_aliasing": 2,
                "multi_gpu": False,
                "renderer": str(args.renderer),
            }
        )

        import numpy as np  # type: ignore
        import omni  # type: ignore
        from pxr import Usd, UsdGeom  # type: ignore

        from convert_asset.render.single import (  # noqa: PLC0415
            DEFAULT_BACKGROUND_COLOR,
            _camera_rgba,
            _compute_bbox,
            _init_camera,
            _init_world,
            _is_valid_bbox,
            _rgba_to_rgb,
            _save_rgb_png,
            _set_camera_look_at,
            _setup_environment,
        )

        report["environment"] = _runtime_environment()
        report["runtime_profile_gate"] = _runtime_profile_gate(
            report["environment"],
            str(args.expected_runtime_version),
        )
        if report["runtime_profile_gate"]["status"] != "pass":
            report["cold_load"] = {
                "status": "blocked",
                "reason": "Isaac/Kit runtime fingerprint did not match the required profile.",
            }
            return report
        ctx = omni.usd.get_context()
        opened = bool(ctx.open_stage(str(root_usd)))
        loading_complete = False
        loading_state: dict[str, Any] = {"api": None, "value": None}
        for _ in range(240):
            simulation_app.update()
            try:
                loading_complete, loading_state = _stage_loading_complete(ctx)
                if loading_complete:
                    loading_complete = True
                    break
            except Exception as exc:
                report["cold_load"] = {
                    "status": "blocked",
                    "opened": opened,
                    "loading_complete": False,
                    "loading_state": loading_state,
                    "reason": f"could not determine USD loading completion: {exc}",
                }
                return report
        stage = ctx.get_stage()
        if not opened or stage is None or not loading_complete:
            report["cold_load"] = {
                "status": "blocked",
                "opened": opened,
                "loading_complete": loading_complete,
                "loading_state": loading_state,
                "reason": "omni.usd context did not return a fully loaded stage",
            }
            return report

        prim_records = _runtime_required_prims(stage, asset_scope_prims)
        if any(item["status"] == "blocked" for item in prim_records):
            report["cold_load"] = {
                "status": "blocked",
                "opened": opened,
                "asset_scope_prims": prim_records,
                "reason": "asset scope prim missing after runtime stage open",
            }
            return report

        report["cold_load"] = {
            "status": "pass",
            "opened": opened,
            "loading_complete": loading_complete,
            "loading_state": loading_state,
            "asset_scope_prims": prim_records,
            "consumer_required_prims": required_prims,
            "default_prim": _default_prim_path(stage),
        }

        world = _init_world()
        _setup_environment(stage)
        target_prim = _target_prim(stage, asset_scope_prims)
        bbox, bbox_source = _compute_bbox(target_prim)
        if not _is_valid_bbox(bbox):
            report["render_readback"] = {
                "status": "blocked",
                "reason": "target prim has invalid runtime bounding box",
                "bbox_source": bbox_source,
            }
            return report

        bbox_min, bbox_max = bbox
        center = (bbox_min + bbox_max) / 2.0
        distance = max(0.25, float(np.linalg.norm(bbox_max - bbox_min)))
        camera = _init_camera(
            "aan_runtime_smoke_camera",
            int(args.width),
            int(args.height),
            18.0,
        )
        _set_camera_look_at(camera, center, distance=distance, elevation=35.0, azimuth=45.0)
        initial_transforms = _world_transforms(stage, asset_scope_prims)
        finite_initial = _transforms_finite(initial_transforms)
        report["initial_state"] = {
            "status": "pass" if finite_initial else "blocked",
            "scope_prims": asset_scope_prims,
            "capture_point": "before_warmup_and_render",
            "finite_transforms": finite_initial,
        }
        if not finite_initial:
            return report

        for _ in range(max(0, int(args.warmup_steps))):
            world.step(render=False)
        for _ in range(max(1, int(args.render_steps))):
            world.step(render=True)

        rgba = _wait_for_camera_rgba(
            camera=camera,
            world=world,
            camera_rgba=_camera_rgba,
            max_attempts=20,
        )
        rgb = _rgba_to_rgb(rgba, background_color=DEFAULT_BACKGROUND_COLOR) if rgba is not None else None
        if rgb is None:
            report["render_readback"] = {
                "status": "blocked",
                "reason": "camera returned empty RGBA readback",
            }
            return report
        render_path.parent.mkdir(parents=True, exist_ok=True)
        if not _save_rgb_png(render_path, rgb):
            report["render_readback"] = {
                "status": "blocked",
                "reason": f"failed to write render PNG: {render_path}",
            }
            return report

        render_metrics = _render_metrics(rgb, render_path, DEFAULT_BACKGROUND_COLOR)
        if render_metrics["non_background_ratio"] <= float(args.min_non_background_ratio):
            report["render_readback"] = {
                **render_metrics,
                "status": "blocked",
                "reason": "render readback appears blank or all background",
                "bbox_source": bbox_source,
            }
            return report
        report["render_readback"] = {
            **render_metrics,
            "status": "pass",
            "bbox_source": bbox_source,
            "path": str(render_path),
        }
        report["material_view_evidence"] = _capture_material_view_evidence(
            camera=camera,
            world=world,
            center=center,
            distance=distance,
            args=args,
            target_prim_path=target_prim.GetPath().pathString,
            bbox_source=bbox_source,
            background_color=DEFAULT_BACKGROUND_COLOR,
            set_camera_look_at=_set_camera_look_at,
            camera_rgba=_camera_rgba,
            rgba_to_rgb=_rgba_to_rgb,
            save_rgb_png=_save_rgb_png,
        )

        before_step = _world_transforms(stage, asset_scope_prims)
        for _ in range(max(1, int(args.step_frames))):
            world.step(render=False)
        after = _world_transforms(stage, asset_scope_prims)
        finite_step = _transforms_finite(after)
        report["physics_step"] = {
            "status": "pass" if finite_step else "blocked",
            "frames": int(args.step_frames),
            "finite_transforms": finite_step,
            "comparison": "pre_step",
            "max_abs_delta": _max_abs_delta(before_step, after),
        }
        if not finite_step:
            return report

        try:
            world.reset()
            simulation_app.update()
        except Exception as exc:
            report["reset"] = {
                "status": "blocked",
                "reason": f"world.reset failed: {exc}",
            }
            return report
        reset = _world_transforms(stage, asset_scope_prims)
        reset_gate = _build_reset_gate(
            initial_transforms,
            reset,
            pre_step=before_step,
        )
        report["reset"] = {
            **reset_gate,
            "initial_capture_point": "before_warmup_and_render",
        }
        if reset_gate["status"] != "pass":
            return report

        report["status"] = "pass"
        return report
    except Exception as exc:
        failed_stage = "cold_load"
        if report["cold_load"].get("status") == "pass":
            failed_stage = "runtime_execution"
        report[failed_stage] = {
            "status": "blocked",
            "reason": str(exc),
        }
        return report
    finally:
        if world is not None:
            try:
                world.reset()
            except Exception:
                pass
        if simulation_app is not None and close_simulation_app:
            _close_simulation_app_with_report(
                simulation_app,
                report_path,
                report,
                world=world,
            )
        elif simulation_app is not None:
            _prepare_isolated_worker_exit(report, world=world)


def _runtime_environment() -> dict[str, Any]:
    env = {
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "headless": True,
        "isaac_sim_root": os.environ.get("ISAAC_SIM_ROOT"),
    }
    try:
        import isaacsim  # type: ignore

        env["isaacsim_file"] = getattr(isaacsim, "__file__", None)
    except Exception:
        env["isaacsim_file"] = None
    try:
        from pxr import Tf  # type: ignore

        env["pxr_version"] = getattr(Tf, "__doc__", None) or "available"
    except Exception:
        env["pxr_version"] = None
    try:
        import omni.kit.app  # type: ignore

        app = omni.kit.app.get_app()
        version = app.get_app_version() if app is not None else None
        env["kit_version"] = str(version) if version is not None else None
    except Exception:
        env["kit_version"] = None
    return env


def _runtime_profile_gate(environment: dict[str, Any], expected_version: str) -> dict[str, Any]:
    observed = str(environment.get("kit_version") or "")
    status = "pass" if observed.startswith(expected_version + ".") or observed == expected_version else "blocked"
    return {
        "status": status,
        "expected_version": expected_version,
        "observed_kit_version": observed or None,
        "reason": None if status == "pass" else "Runtime does not provide the required Isaac/Kit major.minor fingerprint.",
    }


def _stage_loading_complete(ctx: Any) -> tuple[bool, dict[str, Any]]:
    """Use the public loading API available in the active Isaac generation."""
    legacy = getattr(ctx, "is_stage_loading", None)
    if callable(legacy):
        loading = bool(legacy())
        return (not loading), {"api": "is_stage_loading", "value": loading}
    status_fn = getattr(ctx, "get_stage_loading_status", None)
    if callable(status_fn):
        status = status_fn()
        if isinstance(status, (tuple, list)) and status:
            # Kit 4.1 returns (stage_url, loading_count, loaded_count).
            loading_index = 1 if isinstance(status[0], str) and len(status) >= 2 else 0
            loading = int(status[loading_index])
            return loading == 0, {
                "api": "get_stage_loading_status",
                "value": [str(item) if isinstance(item, str) else int(item) for item in status],
            }
        raise RuntimeError("get_stage_loading_status returned no loading count")
    raise RuntimeError("the active omni.usd context exposes no loading-status API")


def _runtime_required_prims(stage: Any, required_prims: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "path": path,
            "exists": bool(stage.GetPrimAtPath(path).IsValid()),
            "status": "pass" if stage.GetPrimAtPath(path).IsValid() else "blocked",
        }
        for path in required_prims
    ]


def _default_prim_path(stage: Any) -> str | None:
    prim = stage.GetDefaultPrim()
    if prim and prim.IsValid():
        return prim.GetPath().pathString
    return None


def _target_prim(stage: Any, required_prims: list[str]) -> Any:
    for path in required_prims:
        prim = stage.GetPrimAtPath(path)
        if prim and prim.IsValid():
            return prim
    default_prim = stage.GetDefaultPrim()
    if default_prim and default_prim.IsValid():
        return default_prim
    return next(iter(stage.Traverse()))


def _render_metrics(rgb: Any, render_path: Path, background_color: tuple[int, int, int]) -> dict[str, Any]:
    import numpy as np  # type: ignore

    arr = np.asarray(rgb)
    bg = np.asarray(background_color, dtype=np.int16).reshape(1, 1, 3)
    diff = np.abs(arr.astype(np.int16) - bg)
    mask = np.any(diff > 5, axis=2)
    ys, xs = np.where(mask)
    height, width = arr.shape[:2]
    if xs.size and ys.size:
        bbox_ratio = float((xs.max() - xs.min() + 1) * (ys.max() - ys.min() + 1)) / float(width * height)
        foreground = arr[mask][:, :3]
    else:
        bbox_ratio = 0.0
        foreground = arr.reshape(-1, arr.shape[-1])[:, :3]
    return {
        "mean_rgb": [round(float(item), 6) for item in arr[:, :, :3].mean(axis=(0, 1)).tolist()],
        "foreground_rgb": [
            round(float(item), 6) for item in foreground.mean(axis=0).tolist()
        ],
        "non_background_ratio": round(float(mask.mean()), 8),
        "bbox_ratio": round(bbox_ratio, 8),
        "sha256": _sha256_file(render_path),
        "bytes": render_path.stat().st_size,
        "resolution": [int(width), int(height)],
    }


def _capture_material_view_evidence(
    *,
    camera: Any,
    world: Any,
    center: Any,
    distance: float,
    args: argparse.Namespace,
    target_prim_path: str,
    bbox_source: str,
    background_color: tuple[int, int, int],
    set_camera_look_at: Any,
    camera_rgba: Any,
    rgba_to_rgb: Any,
    save_rgb_png: Any,
) -> list[dict[str, Any]]:
    view_dir = Path(args.material_view_dir).resolve()
    records: list[dict[str, Any]] = []
    for spec in MATERIAL_VIEW_SPECS:
        view_id = str(spec["view_id"])
        elevation = float(spec["elevation"])
        azimuth = float(spec["azimuth"])
        path = view_dir / f"{view_id}.png"
        camera_pose = _camera_pose(center, distance=distance, elevation=elevation, azimuth=azimuth)
        set_camera_look_at(camera, center, distance=distance, elevation=elevation, azimuth=azimuth)
        for _ in range(max(1, int(args.render_steps))):
            world.step(render=True)
        rgba = _wait_for_camera_rgba(
            camera=camera,
            world=world,
            camera_rgba=camera_rgba,
            max_attempts=20,
        )
        rgb = rgba_to_rgb(rgba, background_color=background_color) if rgba is not None else None
        if rgb is None:
            continue
        if not save_rgb_png(path, rgb):
            continue
        metrics = _render_metrics(rgb, path, background_color)
        records.append(
            {
                "view_id": view_id,
                "camera_pose": camera_pose,
                "target_prim": target_prim_path,
                "render_hash": metrics["sha256"],
                "mean_rgb": metrics["mean_rgb"],
                "foreground_rgb": metrics["foreground_rgb"],
                "non_background_ratio": metrics["non_background_ratio"],
                "bbox_ratio": metrics["bbox_ratio"],
                "render_path": str(path),
                "bbox_source": bbox_source,
                "bytes": metrics["bytes"],
                "resolution": metrics["resolution"],
            }
        )
    return records


def _camera_pose(center: Any, *, distance: float, elevation: float, azimuth: float) -> dict[str, Any]:
    import numpy as np  # type: ignore

    elev_rad = math.radians(float(elevation))
    azim_rad = math.radians(float(azimuth))
    target = np.asarray(center, dtype=float)
    offset = np.array(
        [
            float(distance) * math.cos(elev_rad) * math.cos(azim_rad),
            float(distance) * math.cos(elev_rad) * math.sin(azim_rad),
            float(distance) * math.sin(elev_rad),
        ],
        dtype=float,
    )
    position = target + offset
    return {
        "position": [round(float(item), 8) for item in position.tolist()],
        "look_at": [round(float(item), 8) for item in target.tolist()],
        "distance": round(float(distance), 8),
        "elevation": round(float(elevation), 8),
        "azimuth": round(float(azimuth), 8),
    }


def _wait_for_camera_rgba(
    *,
    camera: Any,
    world: Any,
    camera_rgba: Any,
    max_attempts: int,
) -> Any | None:
    for attempt in range(max(1, int(max_attempts))):
        rgba = camera_rgba(camera)
        if rgba is not None:
            return rgba
        if attempt < max(1, int(max_attempts)) - 1:
            world.step(render=True)
    return None


def _world_transforms(stage: Any, prim_paths: list[str]) -> dict[str, list[list[float]] | None]:
    try:
        from pxr import Usd, UsdGeom  # type: ignore
    except Exception:
        return {}
    time = Usd.TimeCode.Default()
    transforms = {}
    for path in prim_paths:
        prim = stage.GetPrimAtPath(path)
        if not prim or not prim.IsValid():
            transforms[path] = None
            continue
        try:
            matrix = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(time)
            transforms[path] = _matrix_to_lists(matrix)
        except Exception:
            transforms[path] = None
    return transforms


def _matrix_to_lists(matrix: Any) -> list[list[float]]:
    rows = []
    for row_idx in range(4):
        rows.append([round(float(matrix[row_idx][col_idx]), 8) for col_idx in range(4)])
    return rows


def _transforms_finite(transforms: dict[str, list[list[float]] | None]) -> bool:
    for matrix in transforms.values():
        if matrix is None:
            return False
        for row in matrix:
            for value in row:
                if not math.isfinite(float(value)):
                    return False
    return True


def _max_abs_delta(
    before: dict[str, list[list[float]] | None],
    after: dict[str, list[list[float]] | None],
) -> float | None:
    deltas = []
    for path, before_matrix in before.items():
        after_matrix = after.get(path)
        if before_matrix is None or after_matrix is None:
            continue
        for row_idx in range(4):
            for col_idx in range(4):
                deltas.append(abs(float(after_matrix[row_idx][col_idx]) - float(before_matrix[row_idx][col_idx])))
    return round(max(deltas), 8) if deltas else None


def _build_reset_gate(
    initial: dict[str, list[list[float]] | None],
    reset: dict[str, list[list[float]] | None],
    *,
    pre_step: dict[str, list[list[float]] | None] | None = None,
) -> dict[str, Any]:
    """Evaluate reset against the state from before warmup or render frames."""
    finite_reset = _transforms_finite(reset)
    reset_delta = _max_abs_delta(initial, reset)
    restored = reset_delta is not None and reset_delta <= 1.0e-5
    return {
        "status": "pass" if finite_reset and restored else "blocked",
        "finite_transforms": finite_reset,
        "max_abs_delta_from_initial": reset_delta,
        "max_abs_delta_from_pre_step": (
            _max_abs_delta(pre_step, reset) if pre_step is not None else None
        ),
        "restored_to_initial": restored,
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _coerce_process_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _close_simulation_app_with_report(
    simulation_app: Any,
    report_path: Path,
    report: dict[str, Any],
    *,
    world: Any | None = None,
) -> None:
    """Persist evidence, release World callbacks, then let Kit unload plugins.

    Isaac Sim 4.1's ``SimulationApp.close`` explicitly unloads every Kit
    plugin.  Leaving the singleton ``World`` registered at that point can
    retain callback objects into the unload phase and intermittently segfault
    after an otherwise successful smoke run.  Clearing the singleton is
    standard Isaac lifecycle hygiene; this is not a pass-through for a failed
    runtime check.  The report is written before and after cleanup so a native
    failure cannot erase the evidence already collected.
    """
    _write_report(report_path, report)
    cleanup = _clear_runtime_world(world)
    report["shutdown_cleanup"] = cleanup
    if cleanup["status"] == "blocked":
        report["status"] = "blocked"
    _write_report(report_path, report)
    simulation_app.close()


def _clear_runtime_world(world: Any | None) -> dict[str, Any]:
    if world is None:
        return {
            "status": "not_applicable",
            "method": None,
        }
    clear_instance = getattr(world, "clear_instance", None)
    if not callable(clear_instance):
        return {
            "status": "blocked",
            "method": "world.clear_instance",
            "reason": "runtime World does not expose clear_instance",
        }
    try:
        clear_instance()
    except Exception as exc:
        return {
            "status": "blocked",
            "method": "world.clear_instance",
            "reason": str(exc),
        }
    return {
        "status": "pass",
        "method": "world.clear_instance",
    }


def _prepare_isolated_worker_exit(report: dict[str, Any], *, world: Any | None) -> None:
    """Record isolated-process cleanup without calling unstable Kit unload code.

    The AAN runtime worker is always a bounded child process.  Isaac Sim 4.1's
    ``SimulationApp.close`` can segfault in native plugin unloading *after*
    cold-load, render, step, reset, and scoped PhysX gates have completed.
    Once its report is durable, the worker uses ``os._exit`` so the operating
    system reclaims its Kit resources instead of entering that broken unload
    path.  A failed cleanup still changes the report to blocked and exits 5.
    """
    cleanup = _clear_runtime_world(world)
    report["shutdown_cleanup"] = cleanup
    report["process_exit"] = {
        "policy": "os_exit_after_evidence",
        "simulation_app_close": "not_called",
        "reason": "isolated_worker_avoids_isaac41_native_plugin_unload_crash",
    }
    if cleanup["status"] == "blocked":
        report["status"] = "blocked"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AAN runtime smoke worker")
    parser.add_argument("--worker", action="store_true", help="Run the runtime smoke worker")
    parser.add_argument("--root-usd", required=True)
    parser.add_argument("--report-out", required=True)
    parser.add_argument("--render-out", required=True)
    parser.add_argument("--material-view-dir", required=True)
    parser.add_argument("--asset-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--expected-root-usd-sha256", required=True)
    parser.add_argument("--required-prim", action="append", default=[])
    parser.add_argument("--asset-scope-prim", action="append", required=True)
    parser.add_argument("--width", type=int, default=160)
    parser.add_argument("--height", type=int, default=120)
    parser.add_argument("--warmup-steps", type=int, default=8)
    parser.add_argument("--render-steps", type=int, default=2)
    parser.add_argument("--step-frames", type=int, default=4)
    parser.add_argument("--renderer", default="RayTracedLighting")
    parser.add_argument("--min-non-background-ratio", type=float, default=0.001)
    parser.add_argument("--expected-runtime-version", default="4.1")
    parser.add_argument(
        "--process-exit-policy",
        choices=("close", "os-exit"),
        default="close",
        help="How the isolated worker exits after persisting runtime evidence.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if not args.worker:
        parser.error("--worker is required")
    use_os_exit = args.process_exit_policy == "os-exit"
    report = _worker_report(args, close_simulation_app=not use_os_exit)
    _write_report(Path(args.report_out), report)
    exit_code = 0 if report.get("status") == "pass" else 5
    if use_os_exit:
        # The report was written using a closed file handle above.  Flush pipe
        # capture too, then avoid Python/Kit interpreter teardown after the
        # intentionally skipped SimulationApp.close native unload path.
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(exit_code)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
