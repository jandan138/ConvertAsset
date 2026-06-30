# AAN-01 DryingBox Manifest Seed

Date: 2026-06-30

## Status

`AAN-01 Manifest Seed` is complete as a manual DryingBox seed manifest. The seed is
intentionally `blocked`, because the current visible evidence does not contain the real
DryingBox source USD, verified required prim paths, or EBench DryingBox task entrypoints.

Seed artifact:

- `docs/records/evidence/2026-06-30-aan-01-dryingbox-manifest-seed/dryingbox_manifest_seed.json`

## Evidence Used

1. `docs/design/asset-application-normalizer.md`
   - SHA256: `9b061f7a68a8a2a3c77e5fe13fa15f53cf3d06ee9757bca01125c3061e31a088`
   - Provides the frozen AAN-00 schema, gate status, material policy, physics policy, and
     AAN-01 acceptance contract.
2. `docs/records/2026-06-30-aan-00-contract-freeze.md`
   - SHA256: `53064a5f75912c6369ab4f807d5091e1f4afba949f849742b501ca5df54cd420`
   - Freezes the AAN-01 field checklist and claim boundary.
3. `/cpfs/user/zhuzihou/dev/labutopia_task整理_draft.xml`
   - SHA256: `2718c9cde8fbe3db1e370d44d9557a241847b5c2f5f0d84c6f1580010411c8e9`
   - Contains DryingBox door task signals: `level1_open_door`, `level1_close_door`, and
     `level3_open`.
4. `/cpfs/shared/simulation/zhuzihou/dev/EBench`
   - Git commit: `b68f9597640a40092dd1e6091a9dce8aa84bddc3`
   - Used only as target benchmark profile evidence; no DryingBox task config was found.

## Manifest Coverage Audit

| Required AAN-01 surface | Seed status | Evidence |
|---|---|---|
| `schema_version` | Present | `asset_application_normalizer.v1` |
| `source` | Present, blocked | LabUtopia draft identifies DryingBox tasks; source USD path is not located |
| `target` | Present | `isaac41` + `ebench-lift2` with EBench repo evidence |
| `entrypoints` | Present, blocked | Candidate paths recorded; real root USD, task config, and evaluator are missing |
| `required_prim_paths` | Present, blocked | Required semantic roles are enumerated; real prim paths are not verified |
| `dependency_closure` | Present, blocked | Root USD missing, so closure cannot be claimed |
| `material_closure` | Present, blocked | Source material inventory cannot run without root USD |
| `physics_closure` | Present, blocked | DryingBox is treated as an articulated candidate, but body/mass/inertia facts are unavailable |
| `articulation_closure` | Present, blocked | Door joint type, axis, limit, drive, DOF mapping, and reset pose are unavailable |
| `stage_gates` | Present | Source task signal passes; source USD, prim mapping, and EBench entrypoints are blocked |
| `waivers` | Present | Empty, because no AAN-01 blocker is safe to waive |
| `blocked_reasons` | Present | Four blocking reasons with required resolutions |
| `claims_allowed` / `claims_forbidden` | Present | Allows only seed/schema claims; forbids readiness, parity, runtime, and official comparability claims |

## Decisions

1. AAN-01 does not claim DryingBox is ready. It establishes a schema-complete manifest seed
   and makes the current missing evidence explicit.
2. The source task signal is accepted as evidence that DryingBox is the correct first asset,
   but it is not accepted as a substitute for source USD or prim paths.
3. Required prim roles are enumerated even when real paths are missing. This prevents the next
   milestone from silently ignoring asset root, manipulated body, collision prim, articulation
   root, spawn anchor, or goal semantic prim.
4. No temporary waiver is used. Missing source USD, missing required prim mapping, missing
   articulation facts, and missing EBench task entrypoints are blockers under AAN-00.

## Next Required Work

1. Locate or provide the Isaac 5.1-oriented DryingBox root USD path.
2. Extract `defaultPrim`, asset root, manipulated door body, collision prim, articulation root,
   spawn anchor, and goal semantic prim from the source stage.
3. Extract source MDL / texture closure and physics / articulation facts.
4. Create or locate `task_config.yaml`, `required_prims.yaml`, and `evaluator.yaml` for
   `Lift2.DryingBox`.
5. Use this manifest seed as the expected field surface for `AAN-02 CLI Skeleton` and
   `AAN-03 USD Closure`.
