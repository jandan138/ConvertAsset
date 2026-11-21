# Task09 r4 near-full powder bottle — producer model_r1

Date: 2026-09-11. ConvertAsset baseline `4090ec0`; Scenario Forge baseline
`bb36b24`. Status: **producer static geometry, actual CPU previews and Blender
reopen verified**. No runtime, particle-settle or final-scene qualification.

## Ownership and investigation

The user explicitly approved the r4 high tray and assigned these new files:

- [`scripts/model_full_powder_bottle.py`](../../scripts/model_full_powder_bottle.py)
- [`tests/test_full_powder_bottle.py`](../../tests/test_full_powder_bottle.py)
- This record.
- Generated artifacts only under
  `outputs/task09_powder_bottle_r4_20260911/model_r1/`.

Main owns scene builder, presets, runtime, validation scripts and packaging,
including integration of roughly 10,000 independent 1.4 mm grains and persisted
pre-settled poses. This task only supplies the bottle model and model evidence.
Existing concurrent work in both repos was present on arrival and preserved.
No existing r3 source or model was edited. No agents, Isaac or GPU were used;
no commit or push was made. The explicit user scope supersedes repository
defaults to edit indexes/memory or commit documentation.

Read before implementation: CA `AGENTS.md`, `CLAUDE.md`,
`.codex/file-ownership.md`, `.codex/agents/feature-implementer.md`, its canonical
`.claude/agents/feature-implementer.md` and role memory; `docs/index.md`; compact
model source and compact bottle/scene tests. Read SF standards README,
asset-intake, validation-and-delivery and maintenance.

Key discovery: the visual shoulder is a **piecewise triangulated loft**, not
the continuously interpolated radius/exponent envelope. The existing Blender
helper reads its module-global `INSERT_TOP=.059` only for the root custom
property; its camera targets are explicit and remain useful for the high tray.

## Decisions and contracts

### Geometry and collision

- Keep the same 60 × 60 × 100 mm bottle, thin rounded lip, minimum 48 mm clear
  mouth, white material and shell mesh. Preserve the 256 wall colliders, base,
  inner/outer profiles, units and identity transforms exactly as returned by r3.
- Replace only `FalseBottom` and the old `Insert` collider. Default tray occupies
  **82–84 mm**, thickness **2 mm**; `build_geometry(insert_top=.084)` accepts finite
  heights in **83–85 mm**. Other heights and non-finite values fail early.
- Clip the actual 128-segment triangulated visual cavity at the tray bottom and
  top. Keep intersections with the original triangle diagonals, including
  collinear cap boundary vertices, to avoid T-junctions and geometric drift.
  Expand the visual tray perimeter radially by **0.15 mm** into the wall.
  This is a fitted tapered tray, not an upward translation of the r3 body-sized
  superellipse plate.
- Collision uses the unchanged 32-segment wall-LOD inner rings. Make convex
  six-point radial-sector hulls with 0.15 mm radial outer-ring overlap, then
  clip them to the tray slab. Convexification contains both possible diagonals
  of a nonplanar inner quad. Adjacent radial sectors share their seam exactly;
  the overlap allowance applies at the bottle wall.
- Default: **32 `Insert_*` sectors + 256 walls + 1 base = 289 colliders**.
  At 83 mm top the slab crosses the existing 82 mm collision ring and uses
  64 sectors / 321 total; 85 mm uses 32 / 289. Consumers must consume the full
  `colliders` list, not assume a single object named `Insert` or 258 pieces.
- Each visual mesh and each collider is closed and outward with positive signed
  volume. Visual shell and tray remain two overlapping closed components, not
  a newly Boolean-welded shell. Each collision piece is individually convex;
  a convex hull of the whole bottle would be incorrect.

Reuse is through a normal sibling import of
`model_compact_powder_bottle`: `build_geometry`, `_profiles`, `_loft`, `_ring`,
`_wall_hull`, `_moments` and `_create_blender`. The compact implementation is not
copied into the new implementation. A sibling-path bootstrap supports pytest's
file loader, Blender, `runpy` and copied `source_scripts` execution.

### Mass and inertia

Mass is the sum of the unchanged shell and the **effective interior-only tray**,
integrated with signed tetrahedra at 950 kg/m³. The seam is already within the
shell and is excluded from the tray mass. The effective tray is clipped from
the actual triangulated cavity, not an interpolated superellipse approximation.

This is exact integration of the authored solid union to floating-point clipping
tolerance (vertices deduplicated at 14 decimal places in metres). It is **not**
an exact smooth-superellipse solid or measured manufactured HDPE bottle. The
convex contact LOD is an approximation and is not integrated for mass.
Fourfold symmetry makes root XYZ principal axes; inertia is about the COM.

Default values from the generated `geometry.json`:

| Property | Value |
|---|---|
| Tray bottom / top | `0.082 / 0.084 m` |
| Powder surface / depth targets | `0.095 / 0.011 m` |
| Target headspace | `0.005 m` |
| Solid volume | `4.926864277268845e-05 m³` |
| Mass | `0.04680521063405403 kg` |
| COM XYZ | `[1.6071640409110947e-17, -8.212759038761918e-18, 0.04647073732748337] m` |
| Diagonal inertia XYZ | `[6.765735673499959e-05, 6.765735673499967e-05, 3.98461435096269e-05] kg·m²` |
| Principal axes WXYZ | `[1, 0, 0, 0]` |

The r3 schema identity `compact-powder-bottle-geometry-v1` and existing field
names are retained. Metadata identifies the new producer and actual tray top,
with `suggested_powder_surface_m = insert_top + .011` and corresponding target
headspace. This is a **target actual settled powder surface**, not a seed-center
height, a visual false powder surface or an observed settle result. No powder
geometry is authored here.

### Blender and CLI

Ordinary Python writes JSON with no SDK or third-party imports. In Blender the
same CLI also saves `bottle.blend`; `--render` produces actual CPU images from
the new model. `--json-only` is supported; `--render` outside Blender or with
`--json-only` is rejected. `--samples` must be positive.

The local Blender adapter calls the compact helper on the new geometry, then
overwrites root `insert_top_m` from metadata, adds the powder target/COM/inertia
custom properties, and resaves. It does not mutate the compact module global.
The inherited camera framing is retained after image review. Section geometry
is freshly bisected from the new source meshes, with diagnostic terracotta cut
faces; there is no reused r3 image or fabricated powder surface.

For standalone replay copy **both** model scripts into the same `source_scripts`
directory. The owned output contains a tested source snapshot and a byte-identical
ordinary-Python replay under `standalone_replay/`. These are model diagnostics,
not a final scene package.

## Validation: red → green and commands

All commands below ran from `/cpfs/user/zhuzihou/dev/ConvertAsset`.
Python was 3.10.15; Ruff 0.15.13; Blender 4.4.3, build `802179c51ccc`.
Bytecode and pytest caches were disabled to respect the narrow write scope.

### TDD and regressions

Before adding the implementation:

```bash
PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -p no:cacheprovider tests/test_full_powder_bottle.py -x -q
```

**RED:** one setup error in 0.73 s: `FileNotFoundError` for the not-yet-created
`model_full_powder_bottle.py`. After implementation, the same command was
**GREEN: 17 passed in 83.21 s**.

Final targeted suite, including both r3 invariant files:

```bash
PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -p no:cacheprovider tests/test_full_powder_bottle.py tests/test_compact_powder_bottle.py tests/test_compact_powder_scene.py -q
python -B -m ruff check --no-cache scripts/model_full_powder_bottle.py tests/test_full_powder_bottle.py
python -B -m ruff check --no-cache outputs/task09_powder_bottle_r4_20260911/model_r1/verify_model.py
git diff --check
git diff -- scripts/model_compact_powder_bottle.py tests/test_compact_powder_bottle.py tests/test_compact_powder_scene.py
```

Results: **30 passed in 90.25 s**; both Ruff checks passed; diff whitespace check
passed and r3 diff was empty. The bare `ruff` executable was initially absent
from PATH; `python -m ruff` used the already installed module successfully.

New tests cover 83/84/85 mm: exact r3 shell/wall/base/profile equality, target
metadata, plate bounds, directed-edge manifold/Euler checks, positive volumes,
each collider's volume versus SciPy `ConvexHull`, and open-space probes. The seal
audit samples 256 angles × 9 slab heights × 17 radial positions, from the centre
through 0.05 mm inside the actual wall-hull entry surface, at each tested top.

The mass regression independently intersects **shell inner triangles** with
horizontal planes, computes polygon area and second moments, then numerically
integrates across the slab with `scipy.integrate.quad` (splitting at profile
breaks). Total volume, mass and inertia agree to relative `1e-9`; COM to absolute
`1e-12 m`. It also verifies the expanded visible tray volume is larger than the
effective mass volume. Invalid heights and isolated stdlib imports are tested.

### Ordinary Python and actual CPU Blender generation

```bash
PYTHONDONTWRITEBYTECODE=1 python -B scripts/model_full_powder_bottle.py --out outputs/task09_powder_bottle_r4_20260911/model_r1 --insert-top .084
CUDA_VISIBLE_DEVICES='' HIP_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /cpfs/shared/simulation/zhuzihou/tools/blender-4.4.3-linux-x64/blender -b -t 8 --python-exit-code 1 --python scripts/model_full_powder_bottle.py -- --out outputs/task09_powder_bottle_r4_20260911/model_r1 --insert-top .084 --render --samples 40
```

Both exited 0. Blender rendered three 900 × 1000 PNGs using **Cycles CPU,
40 samples, eight threads**, saved the `.blend`, corrected the root property and
resaved. The inherited helper checked all source meshes and actual cutaway
meshes with BMesh for manifoldness and positive signed volume.

### Reopen and copied-source replay

```bash
PYTHONDONTWRITEBYTECODE=1 python -B outputs/task09_powder_bottle_r4_20260911/model_r1/verify_model.py
CUDA_VISIBLE_DEVICES='' HIP_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /cpfs/shared/simulation/zhuzihou/tools/blender-4.4.3-linux-x64/blender -b outputs/task09_powder_bottle_r4_20260911/model_r1/bottle.blend -t 8 --python-exit-code 1 --python outputs/task09_powder_bottle_r4_20260911/model_r1/verify_model.py
```

Both exited 0. `verify_model.py` is a model-local evidence utility in the owned
output directory; it does not touch scene validation scripts.

- Copied-source replay runs with `-I -S -B`, no site packages or repo import
  dependency. Its `geometry.json` SHA-256 is identical to Blender's output.
- Fresh Blender reopen checked **291 asset meshes**, **7,200 vertices**,
  **11,014 faces**, exact JSON polygon index order, direct `Bottle` parenting,
  identity local transforms, no asset rigid bodies/modifiers, material names,
  metric unit scale 1, CPU settings, and closed positive-volume meshes.
- Maximum JSON-to-Blender coordinate error: **3.5762786898541066e-09 m** (float32
  mesh storage). All points are within the `5e-9 m` verification tolerance.
- Reopened root `insert_top_m=.084`, powder target `.095`; mass, COM and inertia
  properties equal JSON. Evidence is in `blender_validation.json`,
  `reopen_validation.json` and `standalone_validation.json`.

### Actual image self-review — explicitly non-independent

The implementer opened all three files with the image-capable `read` tool:

- [`preview_overall.png`](../../outputs/task09_powder_bottle_r4_20260911/model_r1/preview_overall.png):
  white thin-lipped bottle, rounded rectangular body, smooth narrowing shoulder;
  tray does not visibly break through the exterior. Complete bottle in frame.
- [`preview_mouth.png`](../../outputs/task09_powder_bottle_r4_20260911/model_r1/preview_mouth.png):
  open lip and shallow cavity above the high tray are visible; no obvious seam
  gap. White-on-white shading has low contrast; bottom crop is intentional for
  this mouth detail, and this view alone cannot establish tray thickness.
- [`preview_section.png`](../../outputs/task09_powder_bottle_r4_20260911/model_r1/preview_section.png):
  actual cutaway clearly shows a thin high plate joined at the shoulder,
  substantial empty space below, the base and thin lip. Terracotta is diagnostic
  cut-face tint only. No obvious gap, side protrusion or deep solid plug.

These are static model renders, **not** live simulation or settled-state replay.
Main will obtain independent visual review of the integrated final scene.

## Hash-bound handoff

Main geometry:
`/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/task09_powder_bottle_r4_20260911/model_r1/geometry.json`.
The `.blend`, previews and model evidence are adjacent. SHA-256 values below
were computed after the final render, resave, reopen and copied-source replay.
The final read-only record audit verified all 16 documented SHA-256 values
(including standards below) and all seven local Markdown links.

| File (output paths relative to model_r1) | SHA-256 |
|---|---|
| `scripts/model_full_powder_bottle.py` (CA source) | `9d84445bca917ed42bc6d11f80336e446c0e6f83948dbdedc3d1fa6e46a03c67` |
| `scripts/model_compact_powder_bottle.py` (unchanged dependency) | `ffcd794d4ef7b05682d7148736649d328668fa29b60556f30e1d52fdfa75e118` |
| `tests/test_full_powder_bottle.py` (CA source) | `e5c23e96017b674f431b03341d99885e943ca96b01423c44b225e291720a5d6e` |
| `geometry.json` | `121118a218ceb2581ad9584f0f5f756b1de4b062eec47d77f65b9cb7ca6ea09c` |
| `bottle.blend` | `f51507720422ae10cd4f977318cb533254fd41b178f5b88f9b185fd74a3ff6b4` |
| `preview_overall.png` | `f67f400719a197c77aa94c473359954dea52c0584f93a219a516442746d9146b` |
| `preview_mouth.png` | `c33fb42a613b4d5c3897a550d068b34e8b389d69a02f240079860efb733aec16` |
| `preview_section.png` | `f8381cdfa78aea99680cda7df24834bcfd9679bef923af5bf9a43a752001f2c8` |
| `blender_validation.json` | `b5a1d04b4b8595e4fa1e3e4e0d3884b7f38aaf9e5b50a08b0b4eaa070cdbc4ba` |
| `reopen_validation.json` | `e835717ae24e5816c836104a6029a19ae5dd8e596a92204246f7f91ce5720a49` |
| `standalone_validation.json` | `49fdda38aa9be13a8d820c8b11d2b71f89c5cb12acab0573204e3bee30d11b77` |
| `verify_model.py` | `baa77b49c986f2f0d69c77dfa725bd5b776d02d55ea374fe80d408a6ee2c285b` |

## Standards synchronization and limits

Applicable SF rules: **ASSET-001/002/003/006** (producer ownership, concrete source
identity, qualification scope and new version for capability changes),
**VAL-001/002/003/004/005/007** (validation layer, change-matched checks, actual
content and images, retained limits and explicit delivery). See
[SF standards](../../../scenario-forge/docs/standards/README.md) and
[maintenance](../../../scenario-forge/docs/standards/maintenance.md).

**规范无需变更 / no general standards change:** the task applies existing
producer-owned geometry and source-bound evidence rules to an approved bottle
parameter change. It establishes no new runtime capability or cross-project
rule. This owned dated record synchronizes decisions, usage, evidence and
handoff; no design/API contract change or index/memory edit is needed within
the assigned scope. Main owns final scene operations guidance and packaging.

SF had concurrent working-tree changes (including asset-intake), so the read
standards are identified by both baseline and actual SHA-256:

| SF standards file | SHA-256 |
|---|---|
| `README.md` | `ae8f67549d993cfe8aa056e8bc5bbd2501fbeca3c3aabbec56ae484bf8d99d8f` |
| `asset-intake.md` | `b40a22db3e10914587410ab56f69990bc0be9c299f09a608d3f477b105c3cf3e` |
| `validation-and-delivery.md` | `23ecb9a53e2f629e8eed08194dd5940d22f17c77235c1adf52677d0bab32b202` |
| `maintenance.md` | `26f997ac1c4f3722610bc10c72b5a7aefa758d41cb7bea1075a5f231e4e744d4` |

Remaining limits / main handoff:

1. Static sampled seal checks and convexity do not qualify 1.4 mm particles,
   contact offsets, collision cooking, CCD, spoon interaction or dynamic leakage.
   Runtime qualification and final settled-surface measurement belong to main.
2. The 95 mm surface / 11 mm depth / 5 mm headspace are default targets. Main must
   measure actual settled grain surfaces and persist the accepted poses; seeded
   or commanded heights are not evidence. No powder was used in these previews.
3. Changing tray top requires regenerated JSON/Blender output, updated mass/COM/
   inertia, metadata and hashes, and corresponding new integration evidence.
   83 and 85 mm have ordinary-Python geometry tests; actual CPU render/reopen
   evidence here is specifically for **84 mm**. Very small non-integer offsets
   below 84 mm can create a thin sector layer below the existing 82 mm ring;
   its runtime cooking/performance has not been evaluated.
4. Collision LOD differs from the visual mesh; existing r3 wall-LOD clearance
   remains documented in metadata and r3 tests. The tray sectors are contact
   approximations, with shared internal faces and a larger collider count than
   r3. Final simulator behavior/performance cannot be inherited from r3.
5. This is a model handoff, not the final portable scene or package. Final scene
   dependency closure, independent review, runtime evidence and package hashes
   must bind to main's integrated bytes.

Follow-up: [Task09 r4 integrated near-full scene and cold-start fixture evidence](2026-09-11-full-powder-scene-r4.md).
