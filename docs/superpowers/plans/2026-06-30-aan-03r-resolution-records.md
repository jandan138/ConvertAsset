# AAN-03R Resolution Records Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make AAN-03 manifests record a final `mirrored`, `pruned`, `waived`, or `blocked` decision for every missing or remote dependency gap.

**Architecture:** Keep the existing AAN-03 dependency scanner and blocker flow. Add manifest-level resolution records and summary counts derived from the already-collected dependency inventory, preserving current package-writing behavior.

**Tech Stack:** Python, pytest, USD `pxr` lazy imports through the existing Isaac Python wrapper where needed.

---

### Task 1: RED Tests For AAN-03R Decisions

**Files:**
- Modify: `tests/test_asset_application_normalizer_cli.py`

- [ ] **Step 1: Add assertions for missing dependency decisions**

Extend `test_normalize_asset_blocks_missing_local_dependency_without_package` so the blocked manifest must contain:

```python
    missing_record = manifest["dependency_closure"]["missing"][0]
    assert missing_record["resolution"] == "blocked"
    assert missing_record["required_resolution"]
    assert manifest["dependency_closure"]["resolution_summary"]["blocked"] == 1
```

- [ ] **Step 2: Add assertions for mirrored dependency decisions**

Extend `test_normalize_asset_mirrors_mdl_from_package_sidecar_root` so the pass manifest must contain:

```python
    mirrored_records = [
        record
        for record in manifest["dependency_closure"]["resolution_records"]
        if record["raw_asset_path"] == "OmniPBR.mdl"
    ]
    assert mirrored_records[0]["resolution"] == "mirrored"
    assert mirrored_records[0]["package_path"] == "deps/mdl/OmniPBR.mdl"
    assert manifest["dependency_closure"]["resolution_summary"]["mirrored"] == 1
```

- [ ] **Step 3: Add assertions for unauthorized remote decisions**

Extend `test_normalize_asset_blocks_unauthorized_remote_uri_without_package` so the blocked manifest must contain:

```python
    remote_record = manifest["dependency_closure"]["unauthorized_remote_uri"][0]
    assert remote_record["resolution"] == "blocked"
    assert remote_record["required_resolution"]
    assert manifest["dependency_closure"]["resolution_summary"]["blocked"] == 1
```

- [ ] **Step 4: Run RED test slice**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py::test_normalize_asset_blocks_missing_local_dependency_without_package tests/test_asset_application_normalizer_cli.py::test_normalize_asset_mirrors_mdl_from_package_sidecar_root tests/test_asset_application_normalizer_cli.py::test_normalize_asset_blocks_unauthorized_remote_uri_without_package -q
```

Expected: failures due missing `resolution`, `required_resolution`, `resolution_summary`, or `resolution_records` fields.

### Task 2: Minimal Manifest Implementation

**Files:**
- Modify: `convert_asset/asset_application_normalizer/usd_closure.py`
- Modify if needed: `convert_asset/asset_application_normalizer/evidence_manifest.py`

- [ ] **Step 1: Preserve mirror provenance on dependencies**

Add optional fields to `AssetDependency`:

```python
    resolution: str | None = None
    required_resolution: str | None = None
    resolution_source: str | None = None
```

Include non-empty fields in `to_manifest_record`.

- [ ] **Step 2: Mark local mirror hits as `mirrored`**

In `_resolve_missing_dependencies_from_mirrors`, replace a mirror hit with:

```python
replace(
    dep,
    resolved_path=mirror.resolve(),
    status="mirrored",
    resolution="mirrored",
    resolution_source="local_mirror_search",
)
```

- [ ] **Step 3: Preserve resolution fields during package assignment**

In `_assign_package_paths`, copy `resolution`, `required_resolution`, and `resolution_source` into the new dependency object.

- [ ] **Step 4: Add blocked decision records for unresolved gaps**

Create helpers that add `resolution="blocked"` and a concrete `required_resolution` to missing and remote manifest records without changing the package-write path.

- [ ] **Step 5: Add `resolution_records` and `resolution_summary`**

Add both fields to `dependency_closure`:

```python
"resolution_records": _resolution_records(inventory),
"resolution_summary": _resolution_summary(_resolution_records(inventory)),
```

Summary keys must always include `mirrored`, `pruned`, `waived`, and `blocked`.

- [ ] **Step 6: Run GREEN test slice**

Run the same pytest command from Task 1. Expected: all selected tests pass.

### Task 3: Evidence, Docs, And Final Verification

**Files:**
- Modify: `docs/records/evidence/2026-06-30-aan-03-dryingbox-real/*.json`
- Modify: `docs/records/evidence/2026-06-30-aan-03-dryingbox-real/README.md`
- Modify: `docs/records/2026-06-30-aan-03r-dependency-resolution-policy.md`
- Modify: `docs/records/README.md` if a new implementation record is added

- [ ] **Step 1: Regenerate the real DryingBox evidence manifests**

Use the existing `normalize-asset` commands from the AAN-03 evidence record and the Isaac Python wrapper.

- [ ] **Step 2: Verify evidence decisions**

Confirm:

```bash
python -m json.tool docs/records/evidence/2026-06-30-aan-03-dryingbox-real/overlay_level1_poc_dryingbox_01.json >/tmp/aan03r_overlay.json
python -m json.tool docs/records/evidence/2026-06-30-aan-03-dryingbox-real/single_dryingbox_01.json >/tmp/aan03r_single.json
python -m json.tool docs/records/evidence/2026-06-30-aan-03-dryingbox-real/labutopia_lab_001_dryingbox_01.json >/tmp/aan03r_lab.json
```

Overlay must have no unauthorized remote URI. Single and lab blocked manifests must carry blocked resolution decisions.

- [ ] **Step 3: Update docs**

Document that AAN-03R is implemented at manifest level, with remaining unresolved source gaps still blocked until files are mirrored, pruned, or waived with evidence.

- [ ] **Step 4: Run full relevant verification**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py tests/test_render_single.py::test_cli_import_does_not_load_runtime_modules tests/test_render_single.py::test_thumbnails_missing_input_returns_before_runtime_imports -q
python -m py_compile convert_asset/asset_application_normalizer/usd_closure.py convert_asset/asset_application_normalizer/evidence_manifest.py
git diff --check
```

Expected: all pass.

- [ ] **Step 5: Commit**

Commit code, tests, evidence, and docs with:

```bash
git add convert_asset/asset_application_normalizer/usd_closure.py convert_asset/asset_application_normalizer/evidence_manifest.py tests/test_asset_application_normalizer_cli.py docs/superpowers/plans/2026-06-30-aan-03r-resolution-records.md docs/records
git commit -m "feat(aan): record AAN-03R dependency resolutions"
```
