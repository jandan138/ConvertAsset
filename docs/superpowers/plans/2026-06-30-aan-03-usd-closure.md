# AAN-03 USD Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first real `normalize-asset` non-dry-run path that inventories a USD asset, copies package-local dependencies, rewrites package references, and writes an AAN-03 evidence manifest.

**Architecture:** Add a focused USD closure module under `convert_asset/asset_application_normalizer/` and keep `pxr` imports lazy inside execution functions. The pipeline will keep AAN-02 validation, route `--dry-run` to the existing manifest-only path, and route non-dry-run static closure through the new inventory/packager. The output package is not flattened: it preserves USD composition arcs while rewriting asset paths to package-local mirrors.

**Tech Stack:** Python standard library, lazy `pxr.Sdf`/`pxr.Usd` for USD static inspection, existing argparse CLI and pytest tests.

---

### Task 1: AAN-03 CLI Behavior Tests

**Files:**
- Modify: `tests/test_asset_application_normalizer_cli.py`

- [ ] **Step 1: Write failing tests**

Add tests that create a small USDA asset graph:

```python
def test_normalize_asset_writes_package_local_usd_closure(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    source_root.mkdir()
    (source_root / "materials").mkdir()
    (source_root / "textures").mkdir()
    (source_root / "parts").mkdir()
    (source_root / "materials" / "surface.mdl").write_text("mdl 1.0;\n", encoding="utf-8")
    (source_root / "textures" / "albedo.png").write_bytes(b"png")
    (source_root / "parts" / "part.usda").write_text(
        "#usda 1.0\n"
        "def Xform \"Part\" {\n"
        "    custom asset material = @../materials/surface.mdl@\n"
        "    custom asset texture = @../textures/albedo.png@\n"
        "}\n",
        encoding="utf-8",
    )
    source = source_root / "DryingBox.usda"
    source.write_text(
        "#usda 1.0\n"
        "(\n"
        "    defaultPrim = \"World\"\n"
        "    subLayers = [@parts/part.usda@]\n"
        ")\n"
        "def Xform \"World\" {\n"
        "    def Xform \"DryingBox\" (\n"
        "        references = @parts/part.usda@\n"
        "    ) {}\n"
        "}\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"
    args = _base_args(source, out_dir, evidence_out)
    args.remove("--dry-run")

    assert main(args) == 0
    assert (out_dir / "asset.usd").exists()
    assert (out_dir / "deps" / "usd" / "part.usda").exists()
    assert (out_dir / "deps" / "mdl" / "surface.mdl").exists()
    assert (out_dir / "deps" / "textures" / "albedo.png").exists()
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    assert manifest["milestone"] == "AAN-03-usd-closure"
    assert manifest["overall_status"] == "pass"
    assert manifest["dependency_closure"]["missing"] == []
    assert manifest["dependency_closure"]["unauthorized_remote_uri"] == []
```

Add a second test where the USDA references `@omniverse://server/asset.usd@`; assert return code `5`, manifest status `blocked`, no package root, and blocker id `aan03_block_remote_uri`. Add focused coverage for variant references and value clips so AAN-03 records `variant_reference`, `clip_asset`, and `clip_manifest` instead of only generic asset tokens.

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py -q
```

Expected: failure because non-dry-run is still blocked by AAN-02 and no package files are written.

### Task 2: USD Inventory And Closure Module

**Files:**
- Create: `convert_asset/asset_application_normalizer/usd_closure.py`
- Modify: `convert_asset/asset_application_normalizer/model.py`

- [ ] **Step 1: Implement minimal data model**

Create dataclasses for dependency records, closure reports, and package copy entries. Keep them serializable through explicit `to_manifest_record()` helpers.

- [ ] **Step 2: Implement lazy USD inventory**

Inside functions only, import `pxr.Sdf` and `pxr.Usd`. Inventory must capture:

- root layer path and defaultPrim;
- required prim existence via `Usd.Stage.GetPrimAtPath`;
- `subLayerPaths`;
- prim references and payloads from `Sdf.PrimSpec` list ops;
- variant references/payloads from `Sdf.VariantSetSpec`;
- clip asset paths from prim info fields when authored;
- generic asset-valued properties and `@...@` text fallbacks so texture and MDL paths are listed.

- [ ] **Step 3: Implement package closure**

Copy the root USD to `asset.usd` and local dependencies into `deps/usd/`, `deps/mdl/`, `deps/textures/`, or `deps/assets/`. Rewrite package USD text for USDA/text-decodable sources using exact asset-token replacement. For non-text USD layers with dependencies, block with `aan03_block_unrewritable_usd_dependency` rather than leaving package escapes.

### Task 3: Pipeline And Manifest Integration

**Files:**
- Modify: `convert_asset/asset_application_normalizer/pipeline.py`
- Modify: `convert_asset/asset_application_normalizer/evidence_manifest.py`
- Modify: `convert_asset/asset_application_normalizer/package_layout.py`

- [ ] **Step 1: Route non-dry-run static path to AAN-03**

After AAN-02 validation, call `build_usd_closure_package(request)` for non-dry-run. If closure status is pass, write manifest and return `0`. If blocked, write blocked manifest and return `5`.

- [ ] **Step 2: Extend manifest builder**

Allow manifest builder to accept milestone, entrypoint root USD, dependency closure, static USD report, and additional stage gates. Keep AAN-02 dry-run output compatible.

- [ ] **Step 3: Preserve AAN-02 import boundary**

No top-level imports of `pxr`, `omni`, or `isaacsim` in `convert_asset.cli` or `convert_asset.asset_application_normalizer`.

### Task 4: Documentation And Verification

**Files:**
- Create: `docs/records/2026-06-30-aan-03-usd-closure.md`
- Modify: `docs/records/README.md`

- [ ] **Step 1: Add implementation record**

Document the implemented scope, explicit non-claims, verification commands, and known limitations.

- [ ] **Step 2: Run verification**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py tests/test_render_single.py::test_cli_import_does_not_load_runtime_modules tests/test_render_single.py::test_thumbnails_missing_input_returns_before_runtime_imports -q
python -m py_compile convert_asset/asset_application_normalizer/__init__.py convert_asset/asset_application_normalizer/model.py convert_asset/asset_application_normalizer/package_layout.py convert_asset/asset_application_normalizer/evidence_manifest.py convert_asset/asset_application_normalizer/pipeline.py convert_asset/asset_application_normalizer/cli.py convert_asset/asset_application_normalizer/usd_closure.py convert_asset/cli.py
git diff --check
```

- [ ] **Step 3: Commit**

```bash
git add convert_asset/asset_application_normalizer tests/test_asset_application_normalizer_cli.py docs/superpowers/plans/2026-06-30-aan-03-usd-closure.md docs/records/2026-06-30-aan-03-usd-closure.md docs/records/README.md
git commit -m "feat(aan): add AAN-03 USD closure package path"
```
