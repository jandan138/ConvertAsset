# AAN-04 Material Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add AAN-04 material closure records so every package material has a source-first closure decision with MDL/texture provenance.

**Architecture:** Keep AAN-03 as the package dependency closure producer. After a package passes AAN-03, run a new AAN material scanner over the package-local `asset.usd`, correlate material shader asset paths with `dependency_closure.local_files`, and write `material_closure`, `static_material_report`, and an AAN-04 stage gate into the evidence manifest.

**Tech Stack:** Python, pytest, USD `pxr` imported lazily inside scanner functions, existing `normalize-asset` CLI, existing Isaac Python wrapper for real evidence.

---

### Task 1: RED Tests For Material Closure Records

**Files:**
- Modify: `tests/test_asset_application_normalizer_cli.py`

- [ ] **Step 1: Add a packaged MDL/texture material test**

Create a USDA source with:

```python
def Material "Paint" {
    token outputs:mdl:surface.connect = </Looks/Paint/Shader.outputs:out>
    def Shader "Shader" {
        uniform token info:implementationSource = "sourceAsset"
        asset info:mdl:sourceAsset = @materials/paint.mdl@
        color3f inputs:diffuseColor = (0.2, 0.4, 0.6)
        float inputs:roughness = 0.5
        asset inputs:opacity_texture = @textures/alpha.png@
        token outputs:out
    }
}
```

Assert the pass manifest has:

```python
assert manifest["milestone"] == "AAN-04-material-closure"
record = manifest["material_closure"][0]
assert record["closure_mode"] == "local_mirror"
assert record["source_assets_preserved"] is True
assert record["source_mdl_assets"][0]["package_path"] == "deps/mdl/paint.mdl"
assert len(record["source_mdl_assets"][0]["package_sha256"]) == 64
assert record["texture_paths"][0]["package_path"] == "deps/textures/alpha.png"
assert record["transparency_strategy"] == "opacity_input"
assert record["preview_surface_fallback"]["status"] == "not_generated"
```

- [ ] **Step 2: Add a native UsdPreviewSurface material test**

Create a USDA source with a `UsdPreviewSurface` shader and no MDL/texture assets. Assert:

```python
record = manifest["material_closure"][0]
assert record["closure_mode"] == "native_resolved"
assert record["source_mdl_assets"] == []
assert record["extracted_channels"]["baseColor"]["source"] == "constant"
```

- [ ] **Step 3: Update one existing package-pass test**

Update the existing package-local closure test to expect the latest milestone:

```python
assert manifest["milestone"] == "AAN-04-material-closure"
assert manifest["static_material_report"]["material_count"] == 0
```

- [ ] **Step 4: Run RED test slice**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py::test_normalize_asset_writes_material_closure_for_packaged_mdl_and_texture tests/test_asset_application_normalizer_cli.py::test_normalize_asset_reports_native_preview_surface_material tests/test_asset_application_normalizer_cli.py::test_normalize_asset_writes_package_local_usd_closure -q
```

Expected: failures due missing AAN-04 milestone, `material_closure`, or `static_material_report` behavior.

### Task 2: AAN-04 Scanner And Pipeline Integration

**Files:**
- Create: `convert_asset/asset_application_normalizer/material_closure.py`
- Modify: `convert_asset/asset_application_normalizer/model.py`
- Modify: `convert_asset/asset_application_normalizer/evidence_manifest.py`
- Modify: `convert_asset/asset_application_normalizer/pipeline.py`

- [ ] **Step 1: Add milestone constant**

Add:

```python
MILESTONE_AAN04 = "AAN-04-material-closure"
```

- [ ] **Step 2: Add manifest inputs**

Extend `build_manifest` with optional `material_closure` and `static_material_report` parameters.

- [ ] **Step 3: Implement material scanner**

Implement `build_material_closure(layout, dependency_closure, material_policy)` with lazy `pxr` imports. It must:

- open `layout.root_usd`;
- enumerate `UsdShade.Material` prims;
- enumerate child shader prims;
- correlate material-owned MDL/texture dependencies from `dependency_closure.local_files`;
- compute package SHA-256 for package-local assets;
- assign closure modes:
  - `local_mirror` when MDL/texture assets are package-local;
  - `native_resolved` for native UsdPreviewSurface or asset-free materials;
  - `blocked` when material assets are missing package provenance.

- [ ] **Step 4: Add material stage gate**

Return:

```python
stage_gate = {
    "check_id": MILESTONE_AAN04,
    "stage": "material_closure",
    "status": "pass" or "blocked" or "not_run",
}
```

- [ ] **Step 5: Integrate after AAN-03 pass**

In `normalize_asset`, call AAN-04 only after AAN-03 writes the package. For AAN-03 blockers, add an AAN-04 `not_run` gate and leave `material_closure` empty.

- [ ] **Step 6: Run GREEN test slice**

Run the same pytest command from Task 1. Expected: all selected tests pass.

### Task 3: Evidence, Docs, And Verification

**Files:**
- Create: `docs/records/2026-06-30-aan-04-material-closure.md`
- Create: `docs/records/evidence/2026-06-30-aan-04-dryingbox-material-closure/README.md`
- Create: `docs/records/evidence/2026-06-30-aan-04-dryingbox-material-closure/*.json`
- Modify: `docs/records/README.md`

- [ ] **Step 1: Regenerate DryingBox AAN-04 evidence**

Run the same three DryingBox inputs into a new AAN-04 evidence directory:

- raw single `DryingBox_01.usd`;
- raw lab `lab_001.usd`;
- EBench overlay `scene.usda`.

- [ ] **Step 2: Verify material summaries**

Assert overlay has `overall_status = pass`, non-empty material closure records, and no material records with `closure_mode = blocked`.

- [ ] **Step 3: Update docs**

Record scope, design decisions, generated evidence, remaining limitations, and verification commands.

- [ ] **Step 4: Final verification**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py tests/test_render_single.py::test_cli_import_does_not_load_runtime_modules tests/test_render_single.py::test_thumbnails_missing_input_returns_before_runtime_imports -q
python -m py_compile convert_asset/asset_application_normalizer/material_closure.py convert_asset/asset_application_normalizer/pipeline.py convert_asset/asset_application_normalizer/evidence_manifest.py
git diff --check
```

Expected: all pass.

- [ ] **Step 5: Commit**

Commit with:

```bash
git add convert_asset/asset_application_normalizer tests/test_asset_application_normalizer_cli.py docs/records docs/superpowers/plans/2026-06-30-aan-04-material-closure.md
git commit -m "feat(aan): add AAN-04 material closure records"
```
