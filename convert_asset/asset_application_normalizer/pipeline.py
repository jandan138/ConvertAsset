"""AAN MVP pipeline entrypoints."""

from __future__ import annotations

from pathlib import Path

from .benchmark_contract import build_benchmark_contract, build_not_run_benchmark_contract
from .evidence_manifest import build_manifest, sha256_file, write_manifest
from .material_closure import build_material_closure, build_not_run_material_closure
from .mdl_runtime_closure import (
    build_material_runtime_closure,
    build_not_run_material_runtime_closure,
    merge_material_view_evidence_result,
    merge_runtime_compiler_result,
    runtime_compiler_report_from_evidence,
)
from .model import (
    ALLOWED_ASSET_ROLES,
    ALLOWED_SOURCE_RUNTIMES,
    ALLOWED_TARGET_BENCHMARKS,
    ALLOWED_TARGET_RUNTIMES,
    MILESTONE_AAN05,
    MILESTONE_AAN06,
    MILESTONE_AAN07,
    MILESTONE_AAN11,
    USD_EXTENSIONS,
    NormalizeAssetRequest,
    NormalizeAssetResult,
    validate_scope_prim_paths,
)
from .package_layout import TargetPackageLayout, default_evidence_out
from .physics_authoring import apply_physics_profile
from .physics_checks import audit_source_physics, build_not_run_physics_checks, build_physics_checks
from .role_normalization import build_not_run_role_normalization, normalize_asset_role
from .runtime_smoke import (
    build_not_run_runtime_smoke,
    build_runtime_smoke,
    validate_runtime_scope_bindings,
)
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
    if request.asset_role not in ALLOWED_ASSET_ROLES:
        return _validation_error(f"unsupported asset role: {request.asset_role}")
    if request.physics_profile is not None and not request.physics_profile.is_file():
        return _validation_error(f"physics profile not found: {request.physics_profile}")
    if (
        request.target_benchmark == "scenario-forge"
        and request.asset_role == "dynamic"
        and request.physics_profile is None
    ):
        return _validation_error(
            "scenario-forge dynamic admission requires --physics-profile; "
            "do not rely on automatic mass computation"
        )
    scope_validation = validate_scope_prim_paths(request.effective_asset_scope_prims)
    if scope_validation["status"] != "pass":
        return _validation_error(
            "invalid asset scope: " + "; ".join(str(item) for item in scope_validation["errors"])
        )
    if request.target_runtime == "isaac41" and request.expected_runtime_version != "4.1":
        return _validation_error(
            "target runtime isaac41 requires --expected-runtime-version 4.1"
        )
    if request.runtime_timeout_seconds <= 0:
        return _validation_error("runtime timeout seconds must be positive")
    if request.warning_baseline_log is not None and not request.warning_baseline_log.exists():
        return _validation_error(f"warning baseline log not found: {request.warning_baseline_log}")
    if request.runtime_physx_log is not None and not request.runtime_physx_log.is_file():
        return _validation_error(f"runtime PhysX log not found: {request.runtime_physx_log}")
    if request.runtime_physx_log is not None and not request.runtime_scope_bindings:
        return _validation_error(
            "--runtime-physx-log requires one or more explicit --runtime-scope-binding values"
        )
    if request.runtime_scope_bindings:
        binding_validation, bindings = validate_runtime_scope_bindings(
            request.effective_asset_scope_prims,
            request.runtime_scope_bindings,
        )
        if binding_validation["status"] != "pass":
            return _validation_error(
                "invalid runtime scope binding: "
                + "; ".join(str(item) for item in binding_validation["errors"])
            )
        has_nonidentity_binding = any(
            binding["package_scope"] != binding["runtime_scope"] for binding in bindings
        )
        if has_nonidentity_binding and request.runtime_physx_log is None:
            return _validation_error(
                "non-identity runtime scope binding requires --runtime-physx-log from the instantiated consumer runtime"
            )
    return None


def normalize_asset(request: NormalizeAssetRequest) -> NormalizeAssetResult:
    validation = validate_request(request)
    if validation is not None:
        return validation

    evidence_out = request.evidence_out or default_evidence_out(request.out_dir)
    source_sha_before = sha256_file(request.source_usd)
    # Raw-source admission is independent evidence.  It must be recorded even
    # when a later material/package gate blocks role-specific normalization.
    source_physics_audit = audit_source_physics(
        request.source_usd,
        request.effective_asset_scope_prims,
    )
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
        layout = TargetPackageLayout(request.out_dir)
        material_runtime = build_material_runtime_closure(
            layout.root,
            material.material_closure,
            required_prims=request.required_prims,
            runtime_mdl_roots=_target_runtime_mdl_roots(request),
        )
    else:
        material_runtime = build_not_run_material_runtime_closure(
            "AAN-11 material runtime closure was not run because AAN-04 material closure blocked."
        )

    if (
        material_runtime.return_code == 0
        and material_runtime.stage_gate["status"] == "pass"
    ):
        layout = TargetPackageLayout(request.out_dir)
        role_normalization = normalize_asset_role(layout, request)
        if role_normalization.return_code == 0:
            profile_authoring = (
                apply_physics_profile(layout, request)
                if request.asset_role == "dynamic" and request.physics_profile is not None
                else None
            )
            physics = build_physics_checks(
                layout,
                request,
                source_physics_audit=source_physics_audit,
                normalization_actions=role_normalization.normalization_actions,
                physics_profile_admission=(
                    profile_authoring.profile_admission if profile_authoring is not None else None
                ),
                physics_profile_actions=(
                    profile_authoring.normalization_actions if profile_authoring is not None else None
                ),
                physics_profile_blockers=(
                    profile_authoring.blocked_reasons if profile_authoring is not None else None
                ),
            )
        else:
            physics = build_not_run_physics_checks(
                "AAN-05 physics output admission was not run because role normalization blocked."
            )
    else:
        role_normalization = build_not_run_role_normalization(
            "Role normalization was not run because an earlier package or material runtime gate blocked."
        )
        physics = build_not_run_physics_checks(
            "AAN-05 physics static checks were not run because an earlier package or material runtime gate blocked."
        )

    requested_gates = set(request.gates)
    runtime_requested = "runtime" in requested_gates
    benchmark_requested = "benchmark" in requested_gates
    if runtime_requested and physics.return_code == 0 and physics.stage_gate["status"] == "pass":
        layout = TargetPackageLayout(request.out_dir)
        runtime = build_runtime_smoke(
            layout,
            request,
            timeout_seconds=request.runtime_timeout_seconds,
        )
        if runtime.return_code == 0 and runtime.stage_gate["status"] == "pass":
            material_runtime = merge_runtime_compiler_result(
                material_runtime,
                runtime_compiler_report_from_evidence(layout.root, runtime.runtime_evidence),
            )
            material_view_evidence = runtime.runtime_evidence.get("material_view_evidence", [])
            if material_view_evidence:
                material_runtime = merge_material_view_evidence_result(
                    material_runtime,
                    material_view_evidence,
                )
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
        and request.target_benchmark == "ebench-lift2"
        and physics.return_code == 0
        and physics.stage_gate["status"] == "pass"
        and material_runtime.return_code == 0
        and material_runtime.stage_gate["status"] == "pass"
        and (not runtime_requested or (runtime.return_code == 0 and runtime.stage_gate["status"] == "pass"))
    ):
        benchmark = build_benchmark_contract(TargetPackageLayout(request.out_dir), request)
    elif benchmark_requested and request.target_benchmark != "ebench-lift2":
        benchmark = build_not_run_benchmark_contract(
            "AAN-07 benchmark contract is not applicable to the scenario-forge target profile."
        )
    elif benchmark_requested:
        benchmark = build_not_run_benchmark_contract(
            "AAN-07 benchmark contract was not run because an earlier static or runtime gate blocked."
        )
    else:
        benchmark = build_not_run_benchmark_contract(
            "AAN-07 benchmark contract requires the benchmark gate, e.g. --gates static,benchmark."
        )

    source_sha_after = sha256_file(request.source_usd)
    source_integrity = {
        "sha256_before": source_sha_before,
        "sha256_after": source_sha_after,
        "unchanged": source_sha_before == source_sha_after,
    }
    integrity_blockers = []
    integrity_return_code = 0
    if not source_integrity["unchanged"]:
        integrity_return_code = 5
        integrity_blockers.append(
            {
                "blocker_id": "aan_source_integrity_changed",
                "severity": "blocking",
                "summary": "The upstream source USD hash changed while AAN was running.",
                "before": source_sha_before,
                "after": source_sha_after,
                "required_resolution": "Re-run against a stable source and retain the matching SHA-256.",
            }
        )
    return_code = (
        closure.return_code
        or material.return_code
        or material_runtime.return_code
        or role_normalization.return_code
        or physics.return_code
        or runtime.return_code
        or benchmark.return_code
        or integrity_return_code
    )
    if integrity_return_code:
        overall_status = "blocked"
    elif benchmark.return_code:
        overall_status = benchmark.overall_status
    elif runtime.return_code:
        overall_status = runtime.overall_status
    elif physics.return_code:
        overall_status = physics.overall_status
    elif material_runtime.return_code:
        overall_status = material_runtime.overall_status
    elif role_normalization.return_code:
        overall_status = role_normalization.overall_status
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
        *material_runtime.blocked_reasons,
        *role_normalization.blocked_reasons,
        *physics.blocked_reasons,
        *runtime.blocked_reasons,
        *benchmark.blocked_reasons,
        *integrity_blockers,
    ]
    stage_gates = [
        *closure.stage_gates,
        material.stage_gate,
        material_runtime.stage_gate,
        *(
            [
                {
                    "check_id": "AAN-05R-role-normalization",
                    "stage": "role_normalization",
                    "status": role_normalization.overall_status,
                    "summary": "AAN package-owned visual_static overlay was applied."
                    if role_normalization.return_code == 0
                    else "AAN package-owned role normalization blocked.",
                }
            ]
            if request.asset_role == "visual_static"
            else []
        ),
        physics.stage_gate,
    ]
    if runtime_requested:
        stage_gates.append(runtime.stage_gate)
    if benchmark_requested:
        stage_gates.append(benchmark.stage_gate)
    stage_gates.insert(
        0,
        {
            "check_id": "AAN-source-integrity",
            "stage": "source_integrity",
            "status": "pass" if source_integrity["unchanged"] else "blocked",
            "summary": "Source SHA-256 remained unchanged during AAN processing."
            if source_integrity["unchanged"]
            else "Source SHA-256 changed during AAN processing.",
        },
    )
    material_passed = material.stage_gate["status"] == "pass"
    material_runtime_passed = material_runtime.stage_gate["status"] == "pass"
    physics_passed = physics.stage_gate["status"] == "pass"
    runtime_passed = runtime.stage_gate["status"] == "pass"
    benchmark_passed = benchmark.stage_gate["status"] == "pass"
    role_physics_claims = (
        [
            "AAN-05 records a package-owned visual_static admission for the declared asset scope only.",
            "The visual_static scope has no active rigid body, collision, articulation, or joint semantics.",
        ]
        if request.asset_role == "visual_static"
        else [
            "AAN-05 static physics and articulation evidence was recorded.",
            "Authored rigid body, collision, mass, inertia, joint axis, and joint limits are preserved when listed with value_source=authored.",
        ]
    )
    role_forbidden_claims = (
        [
            "The raw source asset family is normalization-ready.",
            "The visual_static asset is articulated-physics-ready or dynamic-physics-ready.",
            "Any sibling asset outside the declared visual_static scope is ready.",
        ]
        if request.asset_role == "visual_static"
        else []
    )
    dynamic_profile_forbidden_claims = _dynamic_profile_forbidden_claims(request, physics.physics_closure)
    manifest = build_manifest(
        request,
        overall_status=overall_status,
        blocked_reasons=blocked_reasons,
        milestone=(
            MILESTONE_AAN07
            if benchmark_requested
            and material_runtime.return_code == 0
            and material_runtime.stage_gate["status"] == "pass"
            else MILESTONE_AAN06
            if runtime_requested and material_runtime.return_code == 0
            else MILESTONE_AAN11
            if material_runtime.return_code
            else MILESTONE_AAN05
        ),
        root_usd=closure.root_usd_package_path,
        package_default_prim=closure.static_usd_report.get("root_layer", {}).get("default_prim"),
        dependency_closure=closure.dependency_closure,
        material_closure=material.material_closure,
        material_runtime_closure=material_runtime.material_runtime_closure,
        physics_closure=physics.physics_closure,
        articulation_closure=physics.articulation_closure,
        static_usd_report=closure.static_usd_report,
        static_material_report=material.static_material_report,
        static_material_runtime_report=material_runtime.static_material_runtime_report,
        static_physics_report=physics.static_physics_report,
        static_articulation_report=physics.static_articulation_report,
        source_physics_audit=source_physics_audit,
        output_role_admission=physics.output_role_admission,
        normalization_actions=role_normalization.normalization_actions,
        visual_preservation_fingerprint=role_normalization.visual_preservation_fingerprint,
        source_integrity=source_integrity,
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
                    "AAN-11 material runtime dependency closure passed for package-local MDL roots.",
                    "Required MDL helper modules and MDL-internal texture literals are classified with package evidence.",
                ]
                if material_runtime_passed
                else []
            ),
            *(
                [
                    *role_physics_claims,
                ]
                if physics_passed
                else []
            ),
            *(
                [
                    "AAN-06 headless Isaac runtime smoke passed under the configured isolated runtime runner.",
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
            *([] if material_runtime_passed else ["Material runtime closure is complete."]),
            *([] if physics_passed else ["Physics or articulation closure is complete."]),
            *([] if runtime_passed else ["Isaac runtime smoke passed."]),
            *([] if benchmark_passed else ["EBench task readiness is achieved."]),
            "Exact Isaac Sim 4.1 binary conformance is verified without an explicit runtime environment fingerprint.",
            "Binary USD layers with dependencies are fully supported by AAN-03 text rewriting.",
            "Full visual material parity beyond recorded source-preservation evidence is achieved.",
            *role_forbidden_claims,
            *dynamic_profile_forbidden_claims,
        ],
    )
    write_manifest(evidence_out, manifest)
    # Keep a self-contained manifest beside the owned package as well as the
    # caller-selected sidecar.  Consumers must not need a separate filesystem
    # convention to find the admission evidence that describes asset.usd.
    package_manifest = TargetPackageLayout(request.out_dir).evidence_manifest
    if request.out_dir.is_dir() and package_manifest != evidence_out:
        write_manifest(package_manifest, manifest)
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
    elif material_runtime.return_code != 0:
        print(f"AAN-05 physics static checks not run; AAN-11 blocked: {evidence_out}")
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


def _dynamic_profile_forbidden_claims(
    request: NormalizeAssetRequest,
    physics_closure: dict[str, object],
) -> list[str]:
    """Project profile-quality limits into machine-readable manifest claims."""
    if request.asset_role != "dynamic":
        return []
    profile = physics_closure.get("profile_admission")
    quality_tier = profile.get("quality_tier") if isinstance(profile, dict) else None
    claims = [
        "The immutable raw source USD was physically repaired in place.",
        "Any sibling asset outside the declared package scope is physics-ready.",
        "A pre-repaired overlay proves readiness of the immutable raw source family.",
    ]
    if quality_tier == "measured":
        claims.append(
            "Measured, BOM, CAD, or real-world physical-parameter parity beyond the declared profile evidence is verified."
        )
    elif quality_tier == "approved_estimate":
        claims.extend(
            [
                "Measured real-world physical-parameter parity is verified.",
                "BOM, CAD, or physical-parameter parity beyond the declared approved profile evidence is verified.",
            ]
        )
    else:
        # ``mixed``, ``provisional_geometry``, absent, and unknown tiers all
        # retain the strictest boundary.  A mixed profile cannot inherit the
        # strongest body's claim for the whole asset.
        claims.extend(
            [
                "Measured, BOM, CAD, or real-world physical-parameter parity is verified.",
                "Real material density was recovered from MDL appearance names or visual textures.",
            ]
        )
    return claims


def _target_runtime_mdl_roots(request: NormalizeAssetRequest) -> list[Path] | None:
    """Resolve MDL roots from the explicit target runner without importing Kit."""
    if request.runtime_python is None:
        return None
    prefix = request.runtime_python.resolve().parent.parent
    roots: list[Path] = []
    for site_packages in prefix.glob("lib/python*/site-packages"):
        roots.extend(
            [
                site_packages / "omni" / "mdl" / "core" / "mdl",
                site_packages / "omni" / "mdl" / "core" / "Base",
                site_packages / "omni" / "mdl" / "core",
            ]
        )
    return roots
