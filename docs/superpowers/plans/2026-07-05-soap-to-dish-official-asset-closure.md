# Soap-to-Dish Official Asset Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` or `superpowers:executing-plans` to
> implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair the official EBench `soap-to-dish` USD asset package selected as
`official_ebench_scene@e1cf0d5b4d76` so Phase12 registry closure can report
`material_closure.status: passed`, `missing_material_refs: []`, and
`missing_textures: []`.

**Architecture:** This is a ConvertAsset official-asset closure case, not a Scenario
Forge task-generation change and not an `AAN-12` batch milestone. The implementation
uses AAN-03R dependency resolution, AAN-04 material closure, AAN-11 material runtime
closure, and the formal no-MDL / PreviewSurface compatibility path when exact source
MDL/texture dependencies are unavailable.

**Environment:** Use the existing wrapper:

```bash
./scripts/isaac_python.sh ./main.py ...
```

Do not modify conda environments, install packages, or change the Isaac installation.

---

## Target Evidence

Source blocker:

```text
/cpfs/user/zhuzihou/dev/scenario-forge/docs/records/evidence/2026-07-05-phase13-image-grounded-task-factory/phase13_batch_rc_20260705/blocked_probes/phase13_tabletop_photo_goal_soap_to_dish/handoff/asset_intake_blockers.yaml
```

Known missing dependencies:

- `O.mdl`
- `../textures/bf77ddc86c270d02747e7d0517103514ab51d0f.jpg`
- `../textures/c00e97e58585d8ddb0f8b16a724d05a13eae31.jpg`
- `../textures/c9c274d4ea1de7d059cec0a795b3b27e3941935.jpg`

Canonical external workspace for generated assets:

```text
/cpfs/user/zhuzihou/assets/convertasset_research/experiments/ebench/official_asset_closure/soap_to_dish_e1cf0d5b4d76_20260705
```

---

## File Structure

Likely implementation touchpoints:

- Modify `convert_asset/asset_application_normalizer/usd_closure.py`
  - Ensure material asset refs such as `O.mdl` are reported with owning layer and
    package resolution context.
- Modify `convert_asset/asset_application_normalizer/material_closure.py`
  - Ensure material records carry raw path, resolved path, package path, sha256, and
    binding-scope evidence for source-preserving or no-MDL routes.
- Modify `convert_asset/asset_application_normalizer/mdl_runtime_closure.py`
  - Ensure MDL `texture_2d("../textures/<hash>.jpg")` dependencies mirror or block
    deterministically.
- Modify `convert_asset/no_mdl/*` only if the formal no-MDL package still leaves active
  missing texture paths or material asset refs.
- Add tests under `tests/` for the `O.mdl` and three-JPG blocker pattern.
- Update `docs/records/2026-07-05-official-ebench-scene-e1cf0d5b4d76-soap-to-dish-material-closure.md`
  after the repair is actually run.

---

## Task S2D-00: Source Intake And Ref Origin Lock

**Files:**

- No required code edits yet.
- May add a lightweight fixture only after the active ref pattern is understood.

- [ ] **Step 1: Read the external blocker YAML and source package**

Record:

- source root;
- source USD hashes;
- selected prior no-MDL hash `e1cf0d5b4d76cdc32cb57459be501e55e736f533effe17838191fa63ee107840`;
- exact missing dependency strings;
- source package tree around `SubUSDs/materials` and `SubUSDs/textures`.

- [ ] **Step 2: Locate `O.mdl` origin with pxr-level traversal**

Do not rely only on raw string search. Determine whether `O.mdl` is:

- an active `info:mdl:sourceAsset` / `info:sourceAsset` / shader asset input;
- an authored dependency in a sublayer/reference/payload;
- a Phase12 registry artifact;
- an inactive residual byte string in a generated binary USD.

- [ ] **Step 3: Lock source read-only policy**

Confirm no operation writes into:

```text
/cpfs/shared/simulation/zhuzihou/dev/_datasets/EBench-Assets/assets/scene_usds/ebench/simple_pnp/task3
```

**Acceptance:** A source/ref-origin report exists. The report says whether Route A
source-preserving mirror is possible or Route B formal no-MDL fallback is required.

---

## Task S2D-01: Static Closure Reproduction

**Files:**

- Likely modify `tests/test_asset_application_normalizer_mdl_runtime_closure.py`
- Likely modify or add tests for material/USD closure.

- [ ] **Step 1: Add regression fixture for `O.mdl` plus three JPG texture literals**

Fixture should model:

- USD material ref to `O.mdl`;
- MDL-owned `texture_2d("../textures/<hash>.jpg")` references;
- expected package layout under `deps/mdl` and `deps/textures`.

- [ ] **Step 2: Reproduce blocker in ConvertAsset static closure**

Expected failing state before repair:

- `missing_material_refs` includes `O.mdl`;
- `missing_textures` includes the three JPG paths;
- AAN-04/AAN-11 status blocks if the dependency is required.

- [ ] **Step 3: Add active-vs-inactive residual test if needed**

If `O.mdl` only exists as an inactive raw byte string in a generated USD, add a test
that closure follows pxr/material dependency traversal, while a separate raw-string
package scan can still force re-export if Phase12 requires it.

**Acceptance:** Tests fail for the current gap and describe the intended pass state.

---

## Task S2D-02: Repair Route Implementation

**Files:**

- `convert_asset/asset_application_normalizer/usd_closure.py`
- `convert_asset/asset_application_normalizer/material_closure.py`
- `convert_asset/asset_application_normalizer/mdl_runtime_closure.py`
- `convert_asset/no_mdl/*` only if no-MDL fallback leaves active unresolved refs.

- [ ] **Step 1: Implement Route A if exact source deps are available**

Mirror `O.mdl` and the three JPGs package-locally, preserving owning-MDL relative path
semantics.

Acceptance:

- every mirrored file has source path, package path, sha256, and mirror action;
- `../textures/<hash>.jpg` resolves from package MDL context;
- same-name different-hash ambiguity blocks.

- [ ] **Step 2: Implement Route B formal no-MDL / PreviewSurface fallback if deps are missing**

Generate from a source snapshot in the canonical external workspace. Do not use the
old `/tmp/ebench-soap-to-dish-canary` tree as the final package.

Acceptance:

- active `O.mdl` dependency is removed from the package entrypoint;
- the three missing JPG paths are absent from active material/texture dependencies;
- every remaining texture resolves package-locally;
- `full_material_parity_claimed=false`.

- [ ] **Step 3: Keep available material inputs**

Preserve source-authored colors and textures that do exist. Do not synthesize fake
JPGs or hard-code soap/dish colors as a hidden repair.

**Acceptance:** The selected route can produce a package candidate with no active
missing material ref or texture dependency.

---

## Task S2D-03: Formal Package Builder

**Files:**

- Existing AAN pipeline/package layout modules as needed.
- No generated package tree should be committed to git.

- [ ] **Step 1: Build under canonical external workspace**

Use:

```text
/cpfs/user/zhuzihou/assets/convertasset_research/experiments/ebench/official_asset_closure/soap_to_dish_e1cf0d5b4d76_20260705/package
```

- [ ] **Step 2: Write package evidence**

Required files:

- `asset.usd`
- `evidence/manifest.json`
- `evidence/closure_report.json`
- `evidence/runtime_smoke/report.json`
- `evidence/runtime_smoke/stdout.log`
- `evidence/runtime_smoke/stderr.log`
- `evidence/runtime_smoke/render.png`
- `evidence/material_views/front.png`
- `evidence/material_views/orbit_3q.png`
- `evidence/material_views/side.png`
- `registry_handoff.yaml`
- `SHA256SUMS`

**Acceptance:** The package is portable enough for Phase12 to consume by path and
hash. It does not depend on `/tmp` or in-place source files.

---

## Task S2D-04: Static Closure Gate

**Command sketch:**

```bash
./scripts/isaac_python.sh ./main.py normalize-asset "$FIXED_OR_NOMDL_USD" \
  --out "$PKG" \
  --asset-id official_ebench_scene_e1cf0d5b4d76_soap_to_dish \
  --asset-class rigid \
  --source-runtime isaac51 \
  --target-runtime isaac41 \
  --target-benchmark ebench-lift2 \
  --task-id official_ebench_scene.soap_to_dish \
  --required-prim "$SOAP_PRIM" \
  --required-prim "$DISH_PRIM" \
  --gates static \
  --evidence-out "$PKG/evidence/manifest.json"
```

- [ ] **Step 1: Verify USD opens and required prims exist**

- [ ] **Step 2: Verify package dependency closure**

Acceptance:

- no unresolved sublayer/reference/payload/asset path;
- no unauthorized remote URI;
- no package escape;
- no active `/cpfs` dependency from `asset.usd`;
- no unresolved `O.mdl`;
- no unresolved known JPG texture.

- [ ] **Step 3: Verify material closure and runtime closure static sections**

Acceptance:

- `material_closure.status == "pass"`;
- `material_runtime_closure.status == "pass"` before runtime compiler merge, or
  `not_run` only if runtime gate has not been requested yet and the static portion is
  explicitly clean;
- Phase12 export can map this to `material_closure.status: passed`,
  `missing_material_refs: []`, `missing_textures: []`.

---

## Task S2D-05: Isaac Runtime And Material Render Gate

**Command sketch:**

```bash
./scripts/isaac_python.sh ./main.py normalize-asset "$FIXED_OR_NOMDL_USD" \
  --out "$PKG" \
  --asset-id official_ebench_scene_e1cf0d5b4d76_soap_to_dish \
  --asset-class rigid \
  --source-runtime isaac51 \
  --target-runtime isaac41 \
  --target-benchmark ebench-lift2 \
  --task-id official_ebench_scene.soap_to_dish \
  --required-prim "$SOAP_PRIM" \
  --required-prim "$DISH_PRIM" \
  --gates static,runtime \
  --evidence-out "$PKG/evidence/manifest.json"
```

Optional view render:

```bash
./scripts/isaac_python.sh ./main.py render-single "$PKG/asset.usd" \
  --out "$PKG/evidence/render_single" \
  --naming-style view \
  --overwrite
```

- [ ] **Step 1: Check runtime compiler counters**

Acceptance:

- `error_count == 0`
- `mdlc_count == 0`
- `failed_shader_node_count == 0`
- `missing_texture_count == 0`
- `missing_modules == []`

- [ ] **Step 2: Check material views**

Acceptance:

- required front/orbit/side or equivalent soap/dish views exist;
- PNGs are nonblank;
- target foreground has no contiguous strong red fallback (`R > 150`, `G < 90`,
  `B < 90`);
- target foreground has no contiguous magenta/pink fallback (`R > 150`, `B > 120`,
  `G < 100`).

**Acceptance:** Isaac 4.1 can open and render the package, and soap/dish materials do
not show fallback red/pink.

---

## Task S2D-06: Registry Handoff

**Files:**

- Generate external `registry_handoff.yaml`.
- Update this plan and the dated record only after the package exists.

- [ ] **Step 1: Generate handoff YAML**

Include:

- asset id;
- source root and source hashes;
- selected repair route;
- package root and package root USD;
- package sha256 / sidecar;
- closure report path;
- runtime evidence paths;
- material closure status mapping for Phase12;
- claim boundary.

- [ ] **Step 2: Verify downstream can run without local repair**

Handoff acceptance for ConvertAsset:

- Phase12 only needs to read the package and registry fields;
- Phase13 should not patch USD, MDL, texture paths, or material bindings.

---

## Task S2D-07: Final Verification And Documentation

- [ ] **Step 1: Run unit tests added for this case**

```bash
python -m pytest tests/test_asset_application_normalizer_mdl_runtime_closure.py -q
```

Add any specific new test file to this command.

- [ ] **Step 2: Run static/runtime package command**

Use the exact command from S2D-04/S2D-05 with the final source/package paths and
required prims.

- [ ] **Step 3: Run doc checks**

```bash
git diff --check
```

- [ ] **Step 4: Update the dated record**

Append actual package paths, hashes, closure report summary, render evidence hashes,
and the final downstream handoff status to:

```text
docs/records/2026-07-05-official-ebench-scene-e1cf0d5b4d76-soap-to-dish-material-closure.md
```

**Final acceptance:** ConvertAsset has produced a formal repaired package, closure
report, Isaac render evidence, provenance/hash/source records, and a registry handoff
that lets Phase12/Phase13 rerun without asset-level local patches.
