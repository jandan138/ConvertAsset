"""Four-engine deformable parity compiler and SHA-256 bundle manifest writer (M1)."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Sequence

from .contracts import (
    CALIBRATION_LOSS_MAX,
    VERIFICATION_LOSS_MAX,
    DeformableIntegrityBudget,
    DeformableSourceSpec,
    EngineParityEntry,
    MultiEngineDeformableBundleManifest,
    ProbeResponseSummary,
    compute_probe_discrepancy_loss,
    evaluate_integrity_readout,
)
from .rfws_intake import build_grid_cloth_mesh, build_subdivided_box_mesh
from .tet_utils import build_arched_cloth_points
from .workers import run_worker_request


def _sha256_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def _write_canonical_base_usda(
    usda_path: Path,
    spec: DeformableSourceSpec,
    budget: DeformableIntegrityBudget,
) -> None:
    """Emit canonical OpenUSD base geometry + integrity metadata without importing pxr."""
    sx, sy, sz = spec.dimensions_xyz_m
    if spec.structural_family == "soft_solid":
        verts, faces = build_subdivided_box_mesh((sx, sy, sz), subdiv_xyz=(4, 4, 2))
    else:
        flat_v, faces, _ = build_grid_cloth_mesh(sx, sy, grid_xy=(12, 12))
        verts = build_arched_cloth_points(flat_v, sx, arch_height_m=0.032)

    pts_str = ", ".join(f"({v[0]:.6f}, {v[1]:.6f}, {v[2]:.6f})" for v in verts)
    counts_str = ", ".join("3" for _ in range(len(faces)))
    idx_str = ", ".join(str(int(i)) for f in faces for i in f)

    usda = f'''#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
)

def Xform "World"
{{
    def Mesh "DeformableAsset"
    {{
        custom string deformable:assetId = "{spec.asset_id}"
        custom string deformable:structuralFamily = "{spec.structural_family}"
        custom double deformable:youngsModulusPa = {spec.youngs_modulus_pa}
        custom double deformable:poissonsRatio = {spec.poissons_ratio}
        custom string deformable:strainMetric = "{budget.strain_metric}"
        custom double deformable:strainOnsetA = {budget.strain_onset_a}
        custom double deformable:strainFailureB = {budget.strain_failure_b}
        custom double deformable:damageThreshold = {budget.damage_threshold}
        int[] faceVertexCounts = [{counts_str}]
        int[] faceVertexIndices = [{idx_str}]
        point3f[] points = [{pts_str}]
    }}
}}
'''
    usda_path.parent.mkdir(parents=True, exist_ok=True)
    usda_path.write_text(usda, encoding="utf-8")


def _candidate_grid(engine_id: str, spec: DeformableSourceSpec) -> list[dict[str, Any]]:
    e0 = float(spec.youngs_modulus_pa)
    nu0 = float(spec.poissons_ratio)
    is_solid = spec.structural_family == "soft_solid"

    if engine_id == "mujoco4":
        if is_solid:
            grid = []
            idx = 0
            for y_scale in (0.065, 0.075, 0.088, 0.105, 0.130):
                for damp in (0.04, 0.08, 0.14):
                    grid.append(
                        {
                            "id": f"mj_{idx}",
                            "params": {
                                "young_modulus": e0 * y_scale,
                                "poisson": nu0,
                                "damping": damp,
                                "radius": 0.0015,
                            },
                        }
                    )
                    idx += 1
            return grid
        grid = []
        idx = 0
        for young in (2.0e4, 5.0e4, 1.5e5, 4.5e5):
            for thick in (0.004, 0.008, 0.015):
                for damp in (0.04, 0.09):
                    grid.append(
                        {
                            "id": f"mj_c_{idx}",
                            "params": {
                                "young_modulus": young,
                                "poisson": nu0,
                                "thickness": thick,
                                "damping": damp,
                                "radius": 0.0015,
                            },
                        }
                    )
                    idx += 1
        return grid

    if engine_id == "newton18":
        if is_solid:
            grid = []
            idx = 0
            for e_scale in (0.70, 1.0, 1.35, 1.80):
                for damp in (1.5, 4.0, 9.0, 16.0):
                    grid.append(
                        {
                            "id": f"nw_{idx}",
                            "params": {
                                "E_scale": e_scale,
                                "nu": nu0,
                                "k_damp": damp,
                                "vbd_iterations": 10,
                                "substeps": 4,
                            },
                        }
                    )
                    idx += 1
            return grid
        grid = []
        idx = 0
        for edge_ke in (0.8, 2.5, 8.0, 25.0):
            for tri_ke in (4.0e3, 8.0e3):
                for edge_kd in (0.08, 0.20):
                    grid.append(
                        {
                            "id": f"nw_c_{idx}",
                            "params": {
                                "tri_ke": tri_ke,
                                "tri_ka": tri_ke,
                                "tri_kd": 1.0,
                                "edge_ke": edge_ke,
                                "edge_kd": edge_kd,
                                "vbd_iterations": 10,
                                "substeps": 4,
                            },
                        }
                    )
                    idx += 1
        return grid

    if engine_id == "isaac_physx":
        if is_solid:
            grid = []
            idx = 0
            for y_scale in (0.62, 0.72, 0.95, 1.25):
                for damp in (0.03, 0.10, 0.25, 0.45):
                    grid.append(
                        {
                            "id": f"is_{idx}",
                            "params": {
                                "youngs_modulus": e0 * y_scale,
                                "poissons_ratio": nu0,
                                "elasticity_damping": damp,
                                "dynamic_friction": 0.60,
                            },
                        }
                    )
                    idx += 1
            return grid
        grid = []
        idx = 0
        for bend in (100.0, 400.0, 1200.0, 3000.0):
            for stretch in (1500.0, 3500.0):
                for damp in (0.03, 0.12):
                    grid.append(
                        {
                            "id": f"is_c_{idx}",
                            "params": {
                                "youngs_modulus": 1.8e5,
                                "poissons_ratio": nu0,
                                "surface_thickness": 0.008,
                                "surface_stretch_stiffness": stretch,
                                "surface_shear_stiffness": 0.4 * stretch,
                                "surface_bend_stiffness": bend,
                                "elasticity_damping": damp,
                            },
                        }
                    )
                    idx += 1
        return grid

    raise ValueError(f"No candidate grid defined for engine_id={engine_id!r}")


def compile_multi_engine_deformable_bundle(
    source_spec: DeformableSourceSpec,
    bundle_dir: Path,
    *,
    target_engines: Sequence[str] = ("mujoco4", "newton18", "isaac_physx"),
    candidate_overrides: dict[str, list[dict[str, Any]]] | None = None,
    cal_loss_max: float = CALIBRATION_LOSS_MAX,
    verify_loss_max: float = VERIFICATION_LOSS_MAX,
) -> MultiEngineDeformableBundleManifest:
    """Compile and verify a multi-engine OpenUSD deformable parity bundle on live solvers.

    1. Runs Genesis as physical ground-truth reference across all 4 probes.
    2. For each target engine, fits physical parameters strictly on ``drop`` only.
    3. Freezes the winning parameters and evaluates independent ``compression_release``,
       rotated ``gentle_grasp``, and ``crush_counterfactual``.
    4. Emits ``base.usda``, per-engine USD/config artifacts, and SHA-256 ``manifest.json``.
    """
    bundle_dir = Path(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    work_dir = bundle_dir / "_worker_runs"

    # 1. Single Genesis reference run (cuts GPU time in half!) + score budget in Python
    gen_resp = run_worker_request(
        "genesis",
        {
            "source_spec": source_spec.to_dict(),
            "probe_list": ["drop", "compression_release", "gentle_grasp", "crush_counterfactual"],
            "artifact_out_dir": str(bundle_dir / "engines" / "genesis"),
        },
        work_dir,
        tag="ref_run",
    )
    gen_drop_f = ProbeResponseSummary.from_dict(gen_resp["probes"]["drop"])
    gen_comp_f = ProbeResponseSummary.from_dict(gen_resp["probes"]["compression_release"])
    gen_gentle_raw_dict = dict(gen_resp["probes"]["gentle_grasp"])
    gen_crush_raw_dict = dict(gen_resp["probes"]["crush_counterfactual"])
    gen_gentle_raw = ProbeResponseSummary.from_dict(gen_gentle_raw_dict)
    gen_crush_raw = ProbeResponseSummary.from_dict(gen_crush_raw_dict)

    is_solid = source_spec.structural_family == "soft_solid"
    if is_solid:
        band = source_spec.plastic_strain_band or (0.15, 0.45)
        strain_metric = "polar_stretch_frobenius_q95"
    else:
        band = (0.20, 0.48)
        strain_metric = "edge_stretch_q95"

    max_norm_force = max(
        float(gen_gentle_raw.peak_normal_force_n) * 2.2,
        float(gen_crush_raw.peak_normal_force_n) * 0.75,
        1.0,
    )
    budget = DeformableIntegrityBudget(
        fragility_tier=source_spec.fragility_tier,
        strain_metric=strain_metric,
        strain_onset_a=float(band[0]),
        strain_failure_b=float(band[1]),
        damage_threshold=0.25,
        max_normal_force_n=float(round(max_norm_force, 4)),
        max_shear_force_n=float(round(0.45 * max_norm_force, 4)),
    )

    def _score_gen(raw_dict: dict[str, Any]) -> ProbeResponseSummary:
        s_val = float(
            raw_dict["polar_stretch_strain"]
            if is_solid and raw_dict.get("polar_stretch_strain") is not None
            else (raw_dict.get("edge_stretch_strain") or 0.0)
        )
        r = evaluate_integrity_readout(
            strain=s_val,
            strain_onset_a=budget.strain_onset_a,
            strain_failure_b=budget.strain_failure_b,
            peak_normal_force_n=float(raw_dict.get("peak_normal_force_n", 0.0)),
            max_normal_force_n=budget.max_normal_force_n,
            damage_threshold=budget.damage_threshold,
        )
        scored = dict(raw_dict)
        scored["damage_score"] = r["damage_score"]
        scored["intact"] = r["intact"]
        return ProbeResponseSummary.from_dict(scored)

    gen_gentle = _score_gen(gen_gentle_raw_dict)
    gen_crush = _score_gen(gen_crush_raw_dict)

    engines: dict[str, EngineParityEntry] = {
        "genesis": EngineParityEntry(
            engine_id="genesis",
            solver=str(gen_resp["solver"]),
            artifact_relpath=str(gen_resp["artifact_relpath"]),
            effective_params=dict(gen_resp["params"]),
            fit_loss_drop=0.0,
            verify_loss_compression=0.0,
            cal_passed=True,
            independent_passed=True,
            parity_verified=bool((gen_gentle.intact is True) and (gen_crush.intact is False)),
            drop_summary=gen_drop_f,
            compression_summary=gen_comp_f,
            gentle_grasp=gen_gentle,
            crush_counterfactual=gen_crush,
        )
    }

    # 2. Emit canonical OpenUSD base.usda
    base_usda_path = bundle_dir / "base.usda"
    _write_canonical_base_usda(base_usda_path, source_spec, budget)

    # 3. Calibrate & verify each target engine strictly serialized
    for eid in target_engines:
        cands = (
            candidate_overrides[eid]
            if candidate_overrides and eid in candidate_overrides
            else _candidate_grid(eid, source_spec)
        )
        cal_resp = run_worker_request(
            eid,
            {
                "source_spec": source_spec.to_dict(),
                "probe_list": ["drop"],
                "candidates": cands,
            },
            work_dir,
            tag="cal_drop",
            timeout_s=420.0,
        )

        best_res: dict[str, Any] | None = None
        best_loss = float("inf")
        for res in cal_resp["results"]:
            cand_drop = ProbeResponseSummary.from_dict(res["probes"]["drop"])
            loss_d = compute_probe_discrepancy_loss(cand_drop, gen_drop_f, probe_kind="drop")
            if loss_d < best_loss:
                best_loss = loss_d
                best_res = res

        assert best_res is not None, f"Engine {eid} returned no candidates!"
        frozen_params = dict(best_res["params"])
        cand_drop_best = ProbeResponseSummary.from_dict(best_res["probes"]["drop"])

        verify_resp = run_worker_request(
            eid,
            {
                "source_spec": source_spec.to_dict(),
                "probe_list": ["compression_release", "gentle_grasp", "crush_counterfactual"],
                "params": frozen_params,
                "budget": budget.to_dict(),
                "artifact_out_dir": str(bundle_dir / "engines" / eid),
            },
            work_dir,
            tag="verify_frozen",
            timeout_s=420.0,
        )

        cand_comp = ProbeResponseSummary.from_dict(verify_resp["probes"]["compression_release"])
        cand_gentle = ProbeResponseSummary.from_dict(verify_resp["probes"]["gentle_grasp"])
        cand_crush = ProbeResponseSummary.from_dict(verify_resp["probes"]["crush_counterfactual"])

        verify_loss = compute_probe_discrepancy_loss(
            cand_comp, gen_comp_f, probe_kind="compression_release"
        )
        cal_passed = bool(best_loss <= cal_loss_max)
        ind_passed = bool(verify_loss <= verify_loss_max)
        parity_verified = bool(
            cal_passed
            and ind_passed
            and (cand_gentle.intact is True)
            and (cand_crush.intact is False)
        )

        engines[eid] = EngineParityEntry(
            engine_id=eid,
            solver=str(verify_resp["solver"]),
            artifact_relpath=str(verify_resp["artifact_relpath"]),
            effective_params=frozen_params,
            fit_loss_drop=float(best_loss),
            verify_loss_compression=float(verify_loss),
            cal_passed=cal_passed,
            independent_passed=ind_passed,
            parity_verified=parity_verified,
            drop_summary=cand_drop_best,
            compression_summary=cand_comp,
            gentle_grasp=cand_gentle,
            crush_counterfactual=cand_crush,
        )

    # 4. Build SHA-256 index
    sha_index: dict[str, str] = {"base.usda": _sha256_file(base_usda_path)}
    for rel in (source_spec.visual_mesh_relpath, source_spec.proxy_mesh_relpath):
        if rel and (bundle_dir / rel).is_file():
            sha_index[rel.replace("\\", "/")] = _sha256_file(bundle_dir / rel)
    engines_root = bundle_dir / "engines"
    if engines_root.is_dir():
        for p in sorted(engines_root.rglob("*")):
            if p.is_file():
                sha_index[p.relative_to(bundle_dir).as_posix()] = _sha256_file(p)

    manifest = MultiEngineDeformableBundleManifest(
        asset_id=source_spec.asset_id,
        source=source_spec,
        integrity_budget=budget,
        engines=engines,
        sha256_index=sha_index,
    )
    (bundle_dir / "manifest.json").write_text(
        json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


__all__ = ["compile_multi_engine_deformable_bundle"]

