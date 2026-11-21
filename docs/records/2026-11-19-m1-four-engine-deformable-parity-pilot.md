# 2026-11-19 — M0.5 Environment Parity & M1 Four-Engine Deformable Parity Pilot

- **Date**: 2026-11-19
- **Status**: COMPLETE & VERIFIED
- **Repository**: `I:\cpfs\shared\simulation\zhuzihou\dev\ConvertAsset`
- **Package / Tests / Script**:
  - `convert_asset/deformable_parity/` (`contracts.py`, `rfws_intake.py`, `tet_utils.py`, `compiler.py`, `workers/`)
  - `scripts/run_m1_deformable_parity_pilot.py`
  - `tests/test_deformable_parity_m1.py` (`7 passed in 1.51s`)

---

## 1. Scope & Goals

1. **M0.5 Cross-Platform Simulator Environment Parity** across **Windows 11**, **WSL2 (`Ubuntu-22.04-isaac`)**, and **Google Drive Linux Archive (`J:\我的云端硬盘\UltraSync\conda_envs\`)**:
   - Complete the third deformable reference environment `sim-genesis-py312` (`genesis-world==1.4.7`, `quadrants==1.4.0`, `torch==2.11.0+cu128`, `usd-core==26.11`, `mujoco==4.0.1`, `pyyaml==6.0.3`, `pytest==9.2.0`) alongside the existing `sim-mujoco4-py312` (`mujoco==4.0.1`) and `sim-newton18-py312` (`newton==1.8.0`).
2. **M1 Four-Engine Deformable Parity Compiler & Integrity Verification**:
   - Build a unified, strictly serialized multi-engine deformable parity compiler treating **Genesis 1.4.7** as reference ground truth and compiling calibrated + independently verified OpenUSD (`base.usda` + per-engine overlays) bundles for **MuJoCo 4.0.1**, **Newton 1.8.0**, **Isaac Sim 6.0.1 (PhysX)**, and **Genesis 1.4.7**.
   - Enforce **zero calibration leakage**: target engine parameters are selected strictly on `drop` only (`L_drop <= 0.05`) and then frozen before running independent `compression_release` verification (`L_comp <= 0.08`) plus rotated (+35 deg) `gentle_grasp` and `crush_counterfactual` integrity probes.
   - Verify **rotation-invariant deformation gradient polar stretch** `Q_0.95(||U - I_3||_F)` vs naive `Q_0.95(||F - I_3||_F)` under +35 deg rigid pickup rotation on `soft_solid`.
   - Maintain **Apex Legends ultra-low-GPU coexistence** on the single RTX 4090 throughout execution.

---

## 2. M0.5 Cross-Platform Conda Environments (`ENV_MANIFEST.json`)

Recorded verbatim in `J:\我的云端硬盘\UltraSync\conda_envs\ENV_MANIFEST.json` (`schema_version: ultra-conda-envs-manifest/v1`, GPU verified on `NVIDIA GeForce RTX 4090 (sm_89)`):

| Env Name | Core Packages | Windows / WSL2 Smoke | Linux `conda-pack` Archive Size (bytes) | SHA-256 |
| --- | --- | --- | --- | --- |
| `sim-mujoco4-py312` | `mujoco==4.0.1`, `mujoco-usd==4.0.1`, `mujoco-warp==4.0.1`, `warp-lang==1.19.0`, `usd-core==25.11` | `PASSED` / `PASSED` | `439,274,418` | `0e5140ceffc19b03e4848eb7c53adce393132520d0322b84d37f90a22fba639a` |
| `sim-newton18-py312` | `newton==1.8.0`, `warp-lang==1.19.0`, `usd-core==26.8`, `newton-usd-schemas==0.7.0` | `PASSED` / `PASSED` | `940,111,321` | `24b26edca285ec9cead18100b811281301c22a72c444d27464946b4420a8fdef` |
| `sim-genesis-py312` | `genesis-world==1.4.7`, `quadrants==1.4.0`, `torch==2.11.0+cu128`, `usd-core==26.11`, `mujoco==4.0.1` | `PASSED` / `PASSED` (`mpm_particles=15`, `cloth_particles=239`) | `5,057,422,627` | `fc35097ebf8023bd4bc36fc9962afe786f4151c68c53ce7497716f82bef87070` |

Supporting lockfiles and bootstrapper synced under `J:\我的云端硬盘\UltraSync\conda_envs\`:
- `sim-genesis-py312.win64.requirements.lock.txt` (`1,581` B, sha256 `0aed24ccd3f927a91d3a5820ea8a80d8f57132a708eb29555ce2c4f9349c536c`)
- `sim-genesis-py312.linux.requirements.lock.txt` (`2,101` B, sha256 `ec0b1de57cc84aa82a7f483d95e25e7449fa9ed55311288561d6b8e3e653ffff`)
- `unpack_linux_envs.sh` (`2,545` B, sha256 `50a36b998a629b5e29ca51e6910e3b20815ab1b5bb770f88b2fc91c1d58e4d93`, LF verified)

---

## 3. Ultra-Low-GPU Scheduling & Engine Technical Fixes

### 3.1 Apex Legends Coexistence Guardrails
- **Strict Single-Process Serialization**: At most one GPU worker subprocess executes at any time via `convert_asset/deformable_parity/workers/__init__.py`.
- **Lowest OS Priority**: All isolated worker processes set `IDLE_PRIORITY_CLASS` (`0x00000040`) on Windows and `os.nice(19)` on Linux.
- **Genesis VRAM Cap**: `torch.cuda.set_per_process_memory_fraction(0.08)` inside `genesis_worker.py`.
- **MuJoCo 4 Pure CPU Execution**: `mujoco4_worker.py` runs `flexcomp` (`integrator="discrete"`, `<flag speculative="enable"/>`) purely on CPU (`0%` GPU), as does `pytest tests/test_deformable_parity_m1.py -v`.
- **Isaac Sim 6.0.1 Zero-RTX Memory-Stage Execution**: `isaac_worker.py` boots `SimulationApp` with `create_new_stage=False`, `disable_viewport_updates=True`, `renderer="MinimalRendering"`, `minimal_shading_mode=4`, `limit_cpu_threads=6`, and steps `get_physx_simulation_interface().simulate(dt, t)` on in-memory `Usd.Stage.CreateInMemory()` stages without calling `app.update()`.

### 3.2 Key Cross-Engine Physics Resolutions
1. **Genesis MPM Compression Platen Coupling**: Using `fixed=True` + `platen.set_pos(...)` left `links_state.vel == 0`, causing rigid-MPM grid velocity collision checks to skip downward impulse. Switching the platen to `fixed=False` with `gs.materials.Rigid(gravity_compensation=1.0, rho=1e5, coup_softness=0.002)` driven by `set_pos(..., zero_velocity=False)` + `set_dofs_velocity(...)` aligned MPM compression (`0.1884` at `frac=0.85`).
2. **MuJoCo 4.0.1 Soft-Body Welding & 2D Cloth Elasticity**: Discontinuous `d.qpos` vertex overwrites introduced artificial shear/stretch under `integrator="discrete"`; replacing them with kinematic `<body mocap="true">` jaws bound via `<equality><weld solref="0.004 1.0" solimp="0.9 0.99 0.001"/></equality>` and adding `elastic2d="both"` on `<elasticity>` for `dim="2"` cloth meshes eliminated both artifacts.
3. **Isaac Sim 6.0.1 Zero-RTX Deformable Attachment & Collision Offsets**: `deformableUtils.create_auto_deformable_attachment` triggers a fatal `NULL TfWeakPtr<UsdStage>` lookup when `create_new_stage=False`. Authoring `OmniPhysicsVtxXformAttachment` prims directly on kinematic `UsdGeom.Xform` jaw anchors (`omniphysics:vtxIndicesSrc0`, `omniphysics:localPositionsSrc1`) alongside explicit `PhysxSchema.PhysxCollisionAPI` (`restOffset=0.001`, `contactOffset=0.004`) eliminated the crash and restored ground contact detection (`contact_fraction=0.8333` / `0.8889`).
4. **Conditioned Discrepancy Normalization (`contracts.py`)**: `compute_probe_discrepancy_loss` separates deformation error (`denom = max(|r|, 0.02)`) from unit-scale height recovery error (`denom = max(|r|, 1 - |r|, 0.25)`) so draped flexible cloth (`recovery_ratio ~ 0.03-0.06` vs `0.00`) is evaluated on the `h_0` scale rather than dividing by `0.044` noise.

---

## 4. Live Four-Engine Verification Results

Executed via serialized pilot script:
```powershell
C:\Users\Administrator\Miniconda3\envs\sim-mujoco4-py312\python.exe I:\cpfs\shared\simulation\zhuzihou\dev\ConvertAsset\scripts\run_m1_deformable_parity_pilot.py
```

### 4.1 Asset 1: `pilot_fragile_chocopie_tofu_01` (`soft_solid`, 364.12 s total)
Manifest: `tmp/deformable_pilot_m1/pilot_fragile_chocopie_tofu_01/manifest.json`
Integrity budget: `polar_stretch_frobenius_q95`, `strain_onset_a = 0.15`, `strain_failure_b = 0.45`, `damage_threshold = 0.25`, `max_normal_force_n = 68.1113`.

| Engine (`solver`) | Drop Def / Recov | Fit Loss (`<=0.05`) | Frozen Comp Def / Recov | Verify Loss (`<=0.08`) | Gentle `||U-I||_F` / Naive `||F-I||_F` | Gentle Dmg (`intact`) | Crush `||U-I||_F` | Crush Dmg (`intact`) | `parity_verified` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `genesis` (`MPM.ElastoPlastic`) | `0.0519 / 1.0052` | `0.0000` | `0.1884 / 1.0294` | `0.0000` | `0.1116 / 0.8804` | `0.0000` (`True`) | `0.6619` | `1.0000` (`False`) | `True` |
| `mujoco4` (`flexcomp_3d_discrete_speculative`, `E=2940, damp=0.04`) | `0.0537 / 0.9662` | `0.0145` | `0.1747 / 0.9619` | `0.0277` | `0.1179 / 0.8884` | `0.0000` (`True`) | `0.9960` | `1.0000` (`False`) | `True` |
| `newton18` (`SolverVBD_SoftTet`, `E_scale=1.35, k_damp=4.0`) | `0.0516 / 0.9983` | `0.0028` | `0.1875 / 0.9998` | `0.0067` | `0.0572 / 0.8559` | `0.0000` (`True`) | `0.5846` | `1.0000` (`False`) | `True` |
| `isaac_physx` (`PhysX_VolumeTet`, `E=17360, damp=0.10`) | `0.0495 / 0.9507` | `0.0201` | `0.1799 / 0.9375` | `0.0270` | `0.1520 / 0.8842` | `0.0067` (`True`) | `1.0883` | `1.0000` (`False`) | `True` |

Key invariant observation: across all four solvers during the +35 deg pickup rotation (`gentle_grasp`), naive RFW-S `||F - I||_F` reports `0.8559–0.8884` (would falsely trigger crush failure across all engines), whereas polar stretch `||U - I||_F` stays in `0.0572–0.1520` (`damage_score <= 0.0067 < 0.25`, `intact = True`), while cleanly catching real crush in `crush_counterfactual` (`0.5846–1.0883`, `damage_score = 1.0`, `intact = False`).

### 4.2 Asset 2: `pilot_flexible_wiping_cloth_01` (`cloth_sheet`, 313.98 s total)
Manifest: `tmp/deformable_pilot_m1/pilot_flexible_wiping_cloth_01/manifest.json`
Integrity budget: `edge_stretch_q95`, `strain_onset_a = 0.20`, `strain_failure_b = 0.48`, `damage_threshold = 0.25`, `max_normal_force_n = 53.2179`.

| Engine (`solver`) | Drop Def / Recov | Fit Loss (`<=0.05`) | Frozen Comp Def / Recov | Verify Loss (`<=0.08`) | Gentle Edge Strain | Gentle Dmg (`intact`) | Crush Edge Strain | Crush Dmg (`intact`) | `parity_verified` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `genesis` (`PBD.Cloth`) | `0.9826 / 0.0444` | `0.0000` | `0.9808 / 0.0243` | `0.0000` | `0.0907` | `0.0000` (`True`) | `0.6570` | `1.0000` (`False`) | `True` |
| `mujoco4` (`flexcomp_2d_discrete_speculative`, `E=20000, t=0.015, d=0.04`) | `0.9742 / 0.0582` | `0.0046` | `0.9768 / 0.0581` | `0.0077` | `0.0052` | `0.0000` (`True`) | `0.5036` | `1.0000` (`False`) | `True` |
| `newton18` (`SolverVBD_Cloth`, `edge_ke=2.5, edge_kd=0.20`) | `0.9780 / 0.0300` | `0.0039` | `0.9774 / 0.0300` | `0.0018` | `0.0090` | `0.0000` (`True`) | `0.5597` | `1.0000` (`False`) | `True` |
| `isaac_physx` (`PhysX_SurfaceDeformable`, `stretch=1500, bend=100`) | `1.0000 / 1.0e-6` | `0.0128` | `1.0000 / 1.0e-6` | `0.0089` | `0.0105` | `0.0000` (`True`) | `0.6422` | `1.0000` (`False`) | `True` |

---

## 5. Verification Command Log & Git Status

- **Full test suite**:
  ```powershell
  C:\Users\Administrator\Miniconda3\envs\sim-mujoco4-py312\python.exe -m pytest "I:\cpfs\shared\simulation\zhuzihou\dev\ConvertAsset\tests\test_deformable_parity_m1.py" -v
  ```
  Result: **`7 passed in 1.51s`** (validating lazy imports, rotation-invariance of `||U - I||_F` & edge stretch, positive voxel tet Jacobians, integrity budget + discrepancy loss, RFW-S loader, OpenUSD stage load for `base.usda` and all per-engine `.usda` overlays, and SHA-256 checksums across both live pilot manifests).
- **Pre-existing dirty files check**: Zero pre-existing modified tracked files in `ConvertAsset` were touched by M1 changes.

