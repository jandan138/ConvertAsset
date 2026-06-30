"""AAN MVP pipeline entrypoints."""

from __future__ import annotations

from pathlib import Path

from .benchmark_contract import build_benchmark_contract, build_not_run_benchmark_contract
from .evidence_manifest import build_manifest, write_manifest
from .material_closure import build_material_closure, build_not_run_material_closure
from .model import (
    ALLOWED_SOURCE_RUNTIMES,
    ALLOWED_TARGET_BENCHMARKS,
    ALLOWED_TARGET_RUNTIMES,
    MILESTONE_AAN05,
    MILESTONE_AAN06,
    MILESTONE_AAN07,
    USD_EXTENSIONS,
    NormalizeAssetRequest,
    NormalizeAssetResult,
)
from .package_layout import TargetPackageLayout, default_evidence_out
from .physics_checks import build_not_run_physics_checks, build_physics_checks
from .runtime_smoke import build_not_run_runtime_smoke, build_runtime_smoke
from .usd_closure import build_usd_closure_package


def _validation_error(message: str) -> NormalizeAssetResult:
    print(f"ERROR: {message}")
    return NormalizeAssetResult(return_code=2, manifest_path=None, overall_status="invalid")


def validate_request(request: NormalizeAssetRequest) -> NormalizeAssetResult | None:
    if not request.source_usd.exists():
        return _validation_error(f"source USD not found: {request.source_usd}")
    if request.source_usd.suffix.lower() not in USD_EXTENSIONS:
        return _validation_error(f"MVP only accepts USD files: {request.source_usd}")
    if request.source_runtime not in ALLOWED_SOURCE_RUNTIMES:
        return _validation_error(f"unsupported source runtime for MVP: {request.source_runtime}")
    if request.target_runtime not in ALLOWED_TARGET_RUNTIMES:
        return _validation_error(f"unsupported target runtime for MVP: {request.target_runtime}")
    if request.target_benchmark not in ALLOWED_TARGET_BENCHMARKS:
        return _validation_error(f"unsupported target benchmark for MVP: {request.target_benchmark}")
    return None


def normalize_asset(request: NormalizeAssetRequest) -> NormalizeAssetResult:
    validation = validate_request(request)
    if validation is not None:
        return validation

    evidence_out = request.evidence_out or default_evidence_out(request.out_dir)
    if request.dry_run:
        manifest = build_manifest(request, overall_status="dry_run_incomplete")
        write_manifest(evidence_out, manifest)
        print(f"AAN-02 dry-run manifest written: {evidence_out}")
        return NormalizeAssetResult(0, evidence_out, "dry_run_incomplete")

    closure = build_usd_closure_package(request)
    if closure.return_code == 0:
        material = build_material_closure(
            TargetPackageLayout(request.out_dir),
            closure.dependency_closure,
            request.material_policy,
        )
    else:
        material = build_not_run_material_closure(
            "AAN-04 material closure was not run because AAN-03 USD dependency closure blocked."
        )

    if material.return_code == 0 and material.stage_gate["status"] == "pass":
        physics = build_physics_checks(TargetPackageLayout(request.out_dir), request)
    else:
        physics = build_not_run_physics_checks(
            "AAN-05 physics static checks were not run because an earlier package or material gate blocked."
        )

    requested_gates = set(request.gates)
    runtime_requested = "runtime" in requested_gates
    benchmark_requested = "benchmark" in requested_gates
    if runtime_requested and physics.return_code == 0 and physics.stage_gate["status"] == "pass":
        runtime = build_runtime_smoke(TargetPackageLayout(request.out_dir), request)
    elif runtime_requested:
        runtime = build_not_run_runtime_smoke(
            "AAN-06 runtime smoke was not run because an earlier static gate blocked."
        )
    else:
        runtime = build_not_run_runtime_smoke(
            "AAN-06 runtime smoke requires the runtime gate, e.g. --gates static,runtime."
        )

    if (
        benchmark_requested
        and physics.return_code == 0
        and physics.stage_gate["status"] == "pass"
        and (not runtime_requested or (runtime.return_code == 0 and runtime.stage_gate["status"] == "pass"))
    ):
        benchmark = build_benchmark_contract(TargetPackageLayout(request.out_dir), request)
    elif benchmark_requested:
        benchmark = build_not_run_benchmark_contract(
            "AAN-07 benchmark contract was not run because an earlier static or runtime gate blocked."
        )
    else:
        benchmark = build_not_run_benchmark_contract(
            "AAN-07 benchmark contract requires the benchmark gate, e.g. --gates static,benchmark."
        )

    return_code = (
        closure.return_code
        or material.return_code
        or physics.return_code
        or runtime.return_code
        or benchmark.return_code
    )
    if benchmark.return_code:
        overall_status = benchmark.overall_status
    elif runtime.return_code:
        overall_status = runtime.overall_status
    elif physics.return_code:
        overall_status = physics.overall_status
    elif material.return_code:
        overall_status = material.overall_status
    elif closure.return_code:
        overall_status = closure.overall_status
    elif benchmark_requested:
        overall_status = benchmark.overall_status
    elif runtime_requested:
        overall_status = runtime.overall_status
    else:
        overall_status = physics.overall_status

    blocked_reasons = [
        *closure.blocked_reasons,
        *material.blocked_reasons,
        *physics.blocked_reasons,
        *runtime.blocked_reasons,
        *benchmark.blocked_reasons,
    ]
    stage_gates = [*closure.stage_gates, material.stage_gate, physics.stage_gate]
    if runtime_requested:
        stage_gates.append(runtime.stage_gate)
    if benchmark_requested:
        stage_gates.append(benchmark.stage_gate)
    material_passed = material.stage_gate["status"] == "pass"
    physics_passed = physics.stage_gate["status"] == "pass"
    runtime_passed = runtime.stage_gate["status"] == "pass"
    benchmark_passed = benchmark.stage_gate["status"] == "pass"
    manifest = build_manifest(
        request,
        overall_status=overall_status,
        blocked_reasons=blocked_reasons,
        milestone=(
            MILESTONE_AAN07
            if benchmark_requested
            else MILESTONE_AAN06 if runtime_requested else MILESTONE_AAN05
        ),
        root_usd=closure.root_usd_package_path,
        dependency_closure=closure.dependency_closure,
        material_closure=material.material_closure,
        physics_closure=physics.physics_closure,
        articulation_closure=physics.articulation_closure,
        static_usd_report=closure.static_usd_report,
        static_material_report=material.static_material_report,
        static_physics_report=physics.static_physics_report,
        static_articulation_report=physics.static_articulation_report,
        stage_gates=stage_gates,
        runtime_evidence=runtime.runtime_evidence,
        benchmark_contract=benchmark.benchmark_contract,
        task_contract_report=benchmark.task_contract_report,
        extra_commands=getattr(runtime, "extra_commands", {}),
        claims_allowed=[
            "AAN-03 static USD closure inspected the source graph and wrote an evidence manifest.",
            "Package USD asset paths are local when the AAN-03 gate status is pass.",
            *(
                [
                    "AAN-04 material closure recorded package-local source material evidence.",
                    "Source MDL and texture assets are preserved when listed with package hashes.",
                ]
                if material_passed
                else []
            ),
            *(
                [
                    "AAN-05 static physics and articulation evidence was recorded.",
                    "Authored rigid body, collision, mass, inertia, joint axis, and joint limits are preserved when listed with value_source=authored.",
                ]
                if physics_passed
                else []
            ),
            *(
                [
                    "AAN-06 headless Isaac runtime smoke passed under the configured runtime wrapper.",
                    "Cold load, render readback, physics step, and reset smoke evidence are recorded.",
                ]
                if runtime_passed
                else []
            ),
            *(
                [
                    "AAN-07 wrote EBench task_config, required_prims, and evaluator entrypoint files.",
                    "EBench task readiness is achieved.",
                ]
                if benchmark_passed
                else []
            ),
        ],
        claims_forbidden=[
            *([] if material_passed else ["Material closure is complete."]),
            *([] if physics_passed else ["Physics or articulation closure is complete."]),
            *([] if runtime_passed else ["Isaac runtime smoke passed."]),
            *([] if benchmark_passed else ["EBench task readiness is achieved."]),
            "Exact Isaac Sim 4.1 binary conformance is verified without an explicit runtime environment fingerprint.",
            "Binary USD layers with dependencies are fully supported by AAN-03 text rewriting.",
            "Full visual material parity beyond recorded source-preservation evidence is achieved.",
        ],
    )
    write_manifest(evidence_out, manifest)
    if return_code == 0:
        if benchmark_requested:
            print(f"AAN-07 benchmark contract package written: {request.out_dir}")
        elif runtime_requested:
            print(f"AAN-06 runtime smoke package written: {request.out_dir}")
        else:
            print(f"AAN-05 physics static package written: {request.out_dir}")
    elif closure.return_code != 0:
        print(f"AAN-05 physics static checks not run; AAN-03 blocked: {evidence_out}")
    elif material.return_code != 0:
        print(f"AAN-05 physics static checks not run; AAN-04 blocked: {evidence_out}")
    elif physics.return_code != 0 and runtime_requested:
        print(f"AAN-06 runtime smoke not run; AAN-05 blocked: {evidence_out}")
    elif physics.return_code != 0:
        print(f"AAN-05 physics static checks blocked; manifest written: {evidence_out}")
    elif runtime.return_code != 0 and benchmark_requested:
        print(f"AAN-07 benchmark contract not run; AAN-06 blocked: {evidence_out}")
    elif benchmark.return_code != 0:
        print(f"AAN-07 benchmark contract blocked; manifest written: {evidence_out}")
    else:
        print(f"AAN-06 runtime smoke blocked; manifest written: {evidence_out}")
    return NormalizeAssetResult(return_code, evidence_out, overall_status)


def parse_gates(raw: str | None) -> list[str]:
    if not raw:
        return ["static"]
    return [item.strip() for item in raw.split(",") if item.strip()]
