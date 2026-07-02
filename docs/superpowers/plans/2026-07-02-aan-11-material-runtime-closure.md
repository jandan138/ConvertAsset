# AAN-11 Material Runtime Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `AAN-11 Material Runtime Closure` stage-by-stage so AAN can prove required package materials have closed MDL runtime dependencies, compiler-log evidence, and scoped material visibility evidence.

**Architecture:** Add a focused `convert_asset/asset_application_normalizer/mdl_runtime_closure.py` module owned by AAN, not `no_mdl/`. The module first provides pure-Python static MDL graph parsing and package audits, then pipeline integration, then runtime-log and render-evidence enrichment. The pipeline keeps AAN-04 source material closure and AAN-06 runtime smoke intact; AAN-11 adds a new manifest field and optional stage gate without claiming full material parity.

**Tech Stack:** Python 3, standard library only for static MDL parsing; existing AAN dataclass/result style; pytest; Isaac runtime only for later AAN-11.5/11.6 integration and only through `./scripts/isaac_python.sh`.

---

## File Structure

- Create `convert_asset/asset_application_normalizer/mdl_runtime_closure.py`
  - Owns `MaterialRuntimeClosureResult`, MDL parser, root discovery, dependency classification, static package audit, runtime log parser, and not-run result.
- Modify `convert_asset/asset_application_normalizer/model.py`
  - Add `MILESTONE_AAN11 = "AAN-11-material-runtime-closure"`.
- Modify `convert_asset/asset_application_normalizer/evidence_manifest.py`
  - Add `material_runtime_closure` field to manifest construction and command stage mapping.
- Modify `convert_asset/asset_application_normalizer/pipeline.py`
  - Insert AAN-11 after AAN-04 and before AAN-05 for static runs.
  - Feed AAN-06 stdout/stderr into AAN-11.5 when runtime gate is requested.
- Modify `convert_asset/asset_application_normalizer/runtime_smoke.py`
  - Expose retained stdout/stderr paths and keep runtime material log parsing out of runtime repair logic.
- Create `tests/test_asset_application_normalizer_mdl_runtime_closure.py`
  - Unit tests for parser, native-module classification, root discovery, package audit, runtime log parser.
- Modify `tests/test_asset_application_normalizer_cli.py`
  - Integration tests that package manifests include `material_runtime_closure` and AAN-11 blocks when required package MDL dependencies are unresolved.
- Update docs/records after code work
  - Append an implementation note to `docs/records/2026-07-02-aan-11-material-runtime-closure.md`.

---

### Task 1: AAN-11.1 Pure MDL Runtime Graph Parser

**Files:**
- Create: `convert_asset/asset_application_normalizer/mdl_runtime_closure.py`
- Create: `tests/test_asset_application_normalizer_mdl_runtime_closure.py`

- [x] **Step 1: Write failing parser test**

Add this test:

```python
from pathlib import Path

from convert_asset.asset_application_normalizer.mdl_runtime_closure import parse_mdl_runtime_dependencies


def test_parse_mdl_runtime_dependencies_extracts_imports_using_and_textures(tmp_path: Path) -> None:
    mdl = tmp_path / "material_06.mdl"
    mdl.write_text(
        'mdl 1.0;\n'
        'import ad_3dsmax_maps::*;\n'
        'import ::OmniPBR::OmniPBR;\n'
        'using ::vray_materials import VRayMtl;\n'
        '// import ignored_comment::*;\n'
        'export material m(\n'
        '    texture_2d tex = texture_2d("../textures/image3.jpg"),\n'
        '    texture_2d empty_tex = texture_2d()\n'
        ') = material();\n',
        encoding="utf-8",
    )

    deps = parse_mdl_runtime_dependencies(mdl)

    assert deps.imported_modules == [
        "ad_3dsmax_maps",
        "OmniPBR",
        "vray_materials",
    ]
    assert deps.texture_literals == ["../textures/image3.jpg"]
```

- [x] **Step 2: Run test to verify RED**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_mdl_runtime_closure.py::test_parse_mdl_runtime_dependencies_extracts_imports_using_and_textures -q
```

Expected: FAIL with `ModuleNotFoundError` or missing `parse_mdl_runtime_dependencies`.

- [x] **Step 3: Implement minimal parser**

Create `mdl_runtime_closure.py` with:

```python
"""AAN-11 static MDL runtime dependency closure."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re


_IMPORT_RE = re.compile(r"\bimport\s+(?P<module>(?:::)?[A-Za-z_][\w]*(?:::[A-Za-z_][\w]*)*)")
_USING_RE = re.compile(r"\busing\s+(?P<module>(?:::)?[A-Za-z_][\w]*(?:::[A-Za-z_][\w]*)*)\s+import\b")
_TEXTURE_RE = re.compile(r"\btexture_2d\s*\(\s*\"(?P<path>[^\"]+)\"")


@dataclass(frozen=True)
class MdlRuntimeDependencies:
    mdl_path: Path
    imported_modules: list[str] = field(default_factory=list)
    texture_literals: list[str] = field(default_factory=list)


def parse_mdl_runtime_dependencies(path: Path) -> MdlRuntimeDependencies:
    text = _strip_line_comments(path.read_text(encoding="utf-8", errors="ignore"))
    modules = []
    for match in [*_IMPORT_RE.finditer(text), *_USING_RE.finditer(text)]:
        module = _module_root(match.group("module"))
        if module and module not in modules:
            modules.append(module)
    textures = []
    for match in _TEXTURE_RE.finditer(text):
        value = match.group("path").strip()
        if value and value not in textures:
            textures.append(value)
    return MdlRuntimeDependencies(path, modules, textures)


def _strip_line_comments(text: str) -> str:
    return "\n".join(line.split("//", 1)[0] for line in text.splitlines())


def _module_root(raw: str) -> str:
    module = raw.strip(":")
    if not module:
        return ""
    return module.split("::", 1)[0]
```

- [x] **Step 4: Run test to verify GREEN**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_mdl_runtime_closure.py::test_parse_mdl_runtime_dependencies_extracts_imports_using_and_textures -q
```

Expected: PASS.

---

### Task 2: AAN-11.1 Native Module Classification And Empty Texture Safety

**Files:**
- Modify: `convert_asset/asset_application_normalizer/mdl_runtime_closure.py`
- Modify: `tests/test_asset_application_normalizer_mdl_runtime_closure.py`

- [x] **Step 1: Write failing classification test**

Add:

```python
from convert_asset.asset_application_normalizer.mdl_runtime_closure import classify_mdl_module


def test_classify_mdl_module_treats_stdlib_as_native_and_custom_as_required() -> None:
    assert classify_mdl_module("df") == "native_runtime_module"
    assert classify_mdl_module("::base::file_texture") == "native_runtime_module"
    assert classify_mdl_module("ad_3dsmax_materials") == "required_helper_module"
    assert classify_mdl_module("OmniPBR_ClearCoat") == "required_helper_module"
```

- [x] **Step 2: Run test to verify RED**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_mdl_runtime_closure.py::test_classify_mdl_module_treats_stdlib_as_native_and_custom_as_required -q
```

Expected: FAIL with missing `classify_mdl_module`.

- [x] **Step 3: Implement classifier**

Add:

```python
NATIVE_MDL_MODULES = {"anno", "base", "df", "math", "state", "tex"}


def classify_mdl_module(module: str) -> str:
    root = _module_root(module)
    if root in NATIVE_MDL_MODULES:
        return "native_runtime_module"
    return "required_helper_module"
```

- [x] **Step 4: Run parser/classifier tests**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_mdl_runtime_closure.py -q
```

Expected: PASS.

---

### Task 3: AAN-11.1 Root Discovery From AAN-04 Material Closure And Package MDL

**Files:**
- Modify: `convert_asset/asset_application_normalizer/mdl_runtime_closure.py`
- Modify: `tests/test_asset_application_normalizer_mdl_runtime_closure.py`

- [x] **Step 1: Write failing root discovery test**

Add:

```python
from convert_asset.asset_application_normalizer.mdl_runtime_closure import discover_mdl_roots


def test_discover_mdl_roots_uses_material_closure_and_package_mdl_directory(tmp_path: Path) -> None:
    package = tmp_path / "package"
    (package / "deps" / "mdl").mkdir(parents=True)
    (package / "deps" / "mdl" / "from_dir.mdl").write_text("mdl 1.0;\n", encoding="utf-8")
    (package / "deps" / "mdl" / "from_record.mdl").write_text("mdl 1.0;\n", encoding="utf-8")
    material_closure = [
        {
            "source_mdl_assets": [
                {"package_path": "deps/mdl/from_record.mdl"},
                {"package_path": "deps/mdl/missing_from_record.mdl"},
            ]
        }
    ]

    roots = discover_mdl_roots(package, material_closure)

    assert roots == [
        package / "deps" / "mdl" / "from_dir.mdl",
        package / "deps" / "mdl" / "from_record.mdl",
    ]
```

- [x] **Step 2: Run test to verify RED**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_mdl_runtime_closure.py::test_discover_mdl_roots_uses_material_closure_and_package_mdl_directory -q
```

Expected: FAIL with missing `discover_mdl_roots`.

- [x] **Step 3: Implement root discovery**

Add a deterministic sorted implementation:

```python
def discover_mdl_roots(package_root: Path, material_closure: list[dict]) -> list[Path]:
    roots: set[Path] = set()
    mdl_dir = package_root / "deps" / "mdl"
    if mdl_dir.exists():
        roots.update(path for path in mdl_dir.glob("*.mdl") if path.is_file())
    for material in material_closure:
        for asset in material.get("source_mdl_assets", []):
            package_path = asset.get("package_path")
            if not package_path:
                continue
            candidate = package_root / str(package_path)
            if candidate.exists() and candidate.suffix.lower() == ".mdl":
                roots.add(candidate)
    return sorted(roots, key=lambda item: item.relative_to(package_root).as_posix())
```

- [x] **Step 4: Run tests**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_mdl_runtime_closure.py -q
```

Expected: PASS.

---

### Task 4: AAN-11.2 Static Transitive Dependency Report

**Files:**
- Modify: `convert_asset/asset_application_normalizer/mdl_runtime_closure.py`
- Modify: `tests/test_asset_application_normalizer_mdl_runtime_closure.py`

- [x] **Step 1: Write failing report test for unresolved helper and mirrored texture**

Add:

```python
from convert_asset.asset_application_normalizer.mdl_runtime_closure import build_material_runtime_closure


def test_build_material_runtime_closure_blocks_unresolved_required_helper_and_records_texture(tmp_path: Path) -> None:
    package = tmp_path / "package"
    (package / "deps" / "mdl").mkdir(parents=True)
    (package / "deps" / "textures").mkdir(parents=True)
    (package / "deps" / "textures" / "image3.jpg").write_bytes(b"jpg")
    (package / "deps" / "mdl" / "material_06.mdl").write_text(
        'mdl 1.0;\n'
        'import ad_3dsmax_materials::*;\n'
        'export material m(texture_2d tex = texture_2d("../textures/image3.jpg")) = material();\n',
        encoding="utf-8",
    )

    result = build_material_runtime_closure(package, material_closure=[])

    assert result.return_code == 5
    assert result.stage_gate["check_id"] == "AAN-11-material-runtime-closure"
    assert result.stage_gate["status"] == "blocked"
    report = result.material_runtime_closure
    assert report["status"] == "blocked"
    assert report["root_mdl_assets"] == ["deps/mdl/material_06.mdl"]
    assert report["imported_mdl_modules"][0]["module"] == "ad_3dsmax_materials"
    assert report["imported_mdl_modules"][0]["resolution"] == "blocked"
    assert report["mdl_texture_assets"][0]["raw_asset_path"] == "../textures/image3.jpg"
    assert report["mdl_texture_assets"][0]["resolution"] == "mirrored"
    assert result.blocked_reasons[0]["blocker_id"] == "aan11_block_required_mdl_runtime_dependency"
```

- [x] **Step 2: Run test to verify RED**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_mdl_runtime_closure.py::test_build_material_runtime_closure_blocks_unresolved_required_helper_and_records_texture -q
```

Expected: FAIL with missing `build_material_runtime_closure`.

- [x] **Step 3: Implement result dataclass and report builder**

Implement:

```python
@dataclass(frozen=True)
class MaterialRuntimeClosureResult:
    overall_status: str
    return_code: int
    material_runtime_closure: dict
    static_material_runtime_report: dict
    stage_gate: dict
    blocked_reasons: list[dict]


def build_material_runtime_closure(package_root: Path, material_closure: list[dict]) -> MaterialRuntimeClosureResult:
    roots = discover_mdl_roots(package_root, material_closure)
    module_records = []
    texture_records = []
    for root in roots:
        deps = parse_mdl_runtime_dependencies(root)
        root_rel = root.relative_to(package_root).as_posix()
        for module in deps.imported_modules:
            module_records.append(_module_record(package_root, root_rel, module))
        for texture in deps.texture_literals:
            texture_records.append(_texture_record(package_root, root, root_rel, texture))
    unresolved = [
        item for item in [*module_records, *texture_records]
        if item.get("resolution") == "blocked"
    ]
    status = "blocked" if unresolved else "pass"
    return_code = 5 if unresolved else 0
    closure = {
        "status": status,
        "claim_level": "required_surface_runtime_dependency_closure" if status == "pass" else "not_claimed",
        "full_material_parity_claimed": False,
        "root_mdl_assets": [path.relative_to(package_root).as_posix() for path in roots],
        "imported_mdl_modules": module_records,
        "mdl_texture_assets": texture_records,
        "native_runtime_modules": [r for r in module_records if r["resolution"] == "native_runtime_module"],
        "rewrite_actions": [],
        "runtime_compiler": {"status": "not_run"},
        "view_evidence": [],
    }
    summary = "AAN-11 material runtime dependency closure passed." if status == "pass" else "AAN-11 material runtime dependency closure found blocking gaps."
    blockers = []
    if unresolved:
        blockers.append({
            "blocker_id": "aan11_block_required_mdl_runtime_dependency",
            "severity": "blocking",
            "summary": "One or more required MDL runtime helper modules or textures are unresolved.",
            "count": len(unresolved),
            "required_resolution": "Mirror the helper MDL/texture into the package, classify it as native runtime module, or attach a scoped waiver.",
        })
    return MaterialRuntimeClosureResult(
        overall_status=status,
        return_code=return_code,
        material_runtime_closure=closure,
        static_material_runtime_report={
            "status": status,
            "root_mdl_count": len(roots),
            "imported_module_count": len(module_records),
            "mdl_texture_asset_count": len(texture_records),
            "blocked_dependency_count": len(unresolved),
        },
        stage_gate={
            "check_id": MILESTONE_AAN11,
            "stage": "material_runtime_closure",
            "status": status,
            "summary": summary,
        },
        blocked_reasons=blockers,
    )
```

Implement `_module_record()` and `_texture_record()` so module files resolve to `deps/mdl/<module>.mdl`, and texture paths resolve relative to the owning MDL.

- [x] **Step 4: Run tests**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_mdl_runtime_closure.py -q
```

Expected: PASS.

---

### Task 5: AAN-11 Manifest And Pipeline Integration

**Files:**
- Modify: `convert_asset/asset_application_normalizer/model.py`
- Modify: `convert_asset/asset_application_normalizer/evidence_manifest.py`
- Modify: `convert_asset/asset_application_normalizer/pipeline.py`
- Modify: `tests/test_asset_application_normalizer_cli.py`

- [x] **Step 1: Write failing integration test**

Add a test that creates a package-local MDL with missing helper import and expects AAN-11 to block before AAN-05:

```python
def test_normalize_asset_blocks_unresolved_mdl_runtime_helper_before_physics(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    (source_root / "materials").mkdir(parents=True)
    (source_root / "materials" / "paint.mdl").write_text(
        "mdl 1.0;\nimport ad_3dsmax_materials::*;\n",
        encoding="utf-8",
    )
    source = source_root / "DryingBox.usda"
    source.write_text(
        "#usda 1.0\n"
        "(\n"
        "    defaultPrim = \"World\"\n"
        ")\n"
        "def Xform \"World\" {\n"
        "    def Xform \"DryingBox\" {}\n"
        "}\n"
        "def Scope \"Looks\" {\n"
        "    def Material \"Paint\" {\n"
        "        def Shader \"Shader\" {\n"
        "            uniform token info:implementationSource = \"sourceAsset\"\n"
        "            asset info:mdl:sourceAsset = @materials/paint.mdl@\n"
        "            token outputs:out\n"
        "        }\n"
        "    }\n"
        "}\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"
    args = _base_args(source, out_dir, evidence_out)
    args.remove("--dry-run")

    code = main(args)

    assert code == 5
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    assert manifest["overall_status"] == "blocked"
    assert manifest["material_runtime_closure"]["status"] == "blocked"
    gate_by_id = {gate["check_id"]: gate for gate in manifest["stage_gates"]}
    assert gate_by_id["AAN-11-material-runtime-closure"]["status"] == "blocked"
    assert gate_by_id["AAN-05-physics-static"]["status"] == "not_run"
```

- [x] **Step 2: Run test to verify RED**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py::test_normalize_asset_blocks_unresolved_mdl_runtime_helper_before_physics -q
```

Expected: FAIL because manifest lacks `material_runtime_closure` and pipeline does not run AAN-11.

- [x] **Step 3: Integrate AAN-11 into model/manifest/pipeline**

Implementation requirements:

- `model.py`: add `MILESTONE_AAN11`.
- `evidence_manifest.py`: accept `material_runtime_closure` and `static_material_runtime_report`; include them in manifest even when not-run.
- `pipeline.py`: call `build_material_runtime_closure()` after AAN-04 pass. If AAN-11 blocks, AAN-05 returns not-run. Add AAN-11 stage gate to `stage_gates`.

- [x] **Step 4: Run integration test**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py::test_normalize_asset_blocks_unresolved_mdl_runtime_helper_before_physics -q
```

Expected: PASS.

- [x] **Step 5: Run AAN test subset**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py tests/test_asset_application_normalizer_mdl_runtime_closure.py -q
```

Expected: PASS.

---

### Task 6: AAN-11.3 Package Escape And Safe Rewrite Metadata

**Files:**
- Modify: `convert_asset/asset_application_normalizer/mdl_runtime_closure.py`
- Modify: `tests/test_asset_application_normalizer_mdl_runtime_closure.py`

- [x] **Step 1: Write failing package escape test**

Add:

```python
def test_material_runtime_closure_blocks_absolute_texture_escape(tmp_path: Path) -> None:
    package = tmp_path / "package"
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"png")
    (package / "deps" / "mdl").mkdir(parents=True)
    (package / "deps" / "mdl" / "paint.mdl").write_text(
        f'mdl 1.0;\nexport material m(texture_2d tex = texture_2d("{outside}")) = material();\n',
        encoding="utf-8",
    )

    result = build_material_runtime_closure(package, material_closure=[])

    assert result.return_code == 5
    texture = result.material_runtime_closure["mdl_texture_assets"][0]
    assert texture["resolution"] == "blocked"
    assert texture["failure_mode"] == "package_escape"
```

- [x] **Step 2: Run test to verify RED**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_mdl_runtime_closure.py::test_material_runtime_closure_blocks_absolute_texture_escape -q
```

Expected: FAIL because absolute path handling is incomplete.

- [x] **Step 3: Implement package escape classification**

Update `_texture_record()` to resolve absolute paths and block any path that is not under `package_root`. Do not rewrite yet; record `rewrite_actions=[]`.

- [x] **Step 4: Run tests**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_mdl_runtime_closure.py -q
```

Expected: PASS.

---

### Task 7: AAN-11.5 Runtime Compiler Log Parser

**Files:**
- Modify: `convert_asset/asset_application_normalizer/mdl_runtime_closure.py`
- Modify: `tests/test_asset_application_normalizer_mdl_runtime_closure.py`

- [x] **Step 1: Write failing log parser test**

Add:

```python
from convert_asset.asset_application_normalizer.mdl_runtime_closure import parse_material_runtime_log


def test_parse_material_runtime_log_counts_mdlc_and_shader_failures() -> None:
    text = (
        "[Error] [rtx.mdltranslator] MDLC: could not find module .::ad_3dsmax_materials\n"
        "[Error] Failed to create MDL shade node for /Looks/Paint/Shader\n"
        "[Warning] [omni.hydra] unrelated warning\n"
    )

    report = parse_material_runtime_log(text)

    assert report["status"] == "blocked"
    assert report["counters"]["error_count"] == 2
    assert report["counters"]["warning_count"] == 1
    assert report["counters"]["mdlc_count"] == 1
    assert report["counters"]["failed_shader_node_count"] == 1
    assert report["missing_modules"] == ["ad_3dsmax_materials"]
    assert report["exemplars"][0]["line_hash"]
```

- [x] **Step 2: Run test to verify RED**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_mdl_runtime_closure.py::test_parse_material_runtime_log_counts_mdlc_and_shader_failures -q
```

Expected: FAIL with missing parser.

- [x] **Step 3: Implement log parser**

Add `parse_material_runtime_log(text: str) -> dict` using case-insensitive line matching for `[Error]`, `[Warning]`, `MDLC`, `USD_MDL`, `omni.hydra`, `rtx.mdltranslator`, `Failed to create MDL shade node`, `could not find module`, and missing texture lines. Hash exemplar lines with SHA-256 and keep first five exemplars.

- [x] **Step 4: Run tests**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_mdl_runtime_closure.py -q
```

Expected: PASS.

---

### Task 8: Runtime Evidence Enrichment Hook

**Files:**
- Modify: `convert_asset/asset_application_normalizer/pipeline.py`
- Modify: `convert_asset/asset_application_normalizer/evidence_manifest.py`
- Modify: `tests/test_asset_application_normalizer_cli.py`

- [x] **Step 1: Write failing merge-helper test**

Add this test to `tests/test_asset_application_normalizer_mdl_runtime_closure.py`:

```python
from convert_asset.asset_application_normalizer.mdl_runtime_closure import merge_runtime_compiler_report


def test_merge_runtime_compiler_report_blocks_required_material_errors() -> None:
    closure = {
        "status": "pass",
        "claim_level": "required_surface_runtime_dependency_closure",
        "full_material_parity_claimed": False,
        "root_mdl_assets": ["deps/mdl/paint.mdl"],
        "imported_mdl_modules": [],
        "mdl_texture_assets": [],
        "native_runtime_modules": [],
        "rewrite_actions": [],
        "runtime_compiler": {"status": "not_run"},
        "view_evidence": [],
    }
    compiler = {
        "status": "blocked",
        "counters": {"mdlc_count": 1, "failed_shader_node_count": 1},
        "missing_modules": ["ad_3dsmax_materials"],
        "exemplars": [{"line_hash": "abc", "message": "MDLC could not find module"}],
    }

    merged = merge_runtime_compiler_report(closure, compiler)

    assert merged["status"] == "blocked"
    assert merged["claim_level"] == "not_claimed"
    assert merged["runtime_compiler"] == compiler
```

- [x] **Step 2: Run test to verify RED**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_mdl_runtime_closure.py::test_merge_runtime_compiler_report_blocks_required_material_errors -q
```

Expected: FAIL with missing `merge_runtime_compiler_report`.

- [x] **Step 3: Implement merge helper**

Add:

```python
def merge_runtime_compiler_report(closure: dict, compiler_report: dict) -> dict:
    merged = {**closure, "runtime_compiler": compiler_report}
    if compiler_report.get("status") == "blocked":
        merged["status"] = "blocked"
        merged["claim_level"] = "not_claimed"
    return merged
```

Pipeline wiring for real AAN-06 logs should use this helper after `runtime_smoke` exposes stdout/stderr paths. Until that path exists, keep the helper unit-tested and leave `runtime_compiler.status = "not_run"` in static-only AAN-11 manifests.

- [x] **Step 4: Run AAN test subset**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py tests/test_asset_application_normalizer_mdl_runtime_closure.py -q
```

Expected: PASS.

---

### Task 9: AAN-11.4 Binding Scope Audit Skeleton

**Files:**
- Modify: `convert_asset/asset_application_normalizer/mdl_runtime_closure.py`
- Modify: `tests/test_asset_application_normalizer_mdl_runtime_closure.py`

- [x] **Step 1: Write failing binding-scope test**

Add:

```python
from convert_asset.asset_application_normalizer.mdl_runtime_closure import build_binding_scope_report


def test_build_binding_scope_report_uses_static_material_hints_for_required_prims() -> None:
    material_closure = [
        {
            "material_prim": "/Looks/Paint",
            "binding_scope": "/World/DryingBox",
            "source_mdl_assets": [{"package_path": "deps/mdl/paint.mdl"}],
        }
    ]

    report = build_binding_scope_report(material_closure, required_prims=["/World/DryingBox"])

    assert report["status"] == "static_hint"
    assert report["required_materials"] == [
        {
            "required_prim": "/World/DryingBox",
            "material_prim": "/Looks/Paint",
            "binding_source": "material_closure.binding_scope",
        }
    ]
    assert report["unknown_required_prims"] == []
```

- [x] **Step 2: Run test to verify RED**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_mdl_runtime_closure.py::test_build_binding_scope_report_uses_static_material_hints_for_required_prims -q
```

Expected: FAIL with missing `build_binding_scope_report`.

- [x] **Step 3: Implement binding-scope skeleton**

Add:

```python
def build_binding_scope_report(material_closure: list[dict], required_prims: list[str]) -> dict:
    required_materials = []
    matched = set()
    for material in material_closure:
        scope = material.get("binding_scope")
        material_prim = material.get("material_prim")
        if not scope or not material_prim:
            continue
        for required in required_prims:
            if scope == required:
                matched.add(required)
                required_materials.append({
                    "required_prim": required,
                    "material_prim": material_prim,
                    "binding_source": "material_closure.binding_scope",
                })
    unknown = [prim for prim in required_prims if prim not in matched]
    return {
        "status": "static_hint" if required_materials else "unknown",
        "required_materials": required_materials,
        "unknown_required_prims": unknown,
    }
```

- [x] **Step 4: Run tests**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_mdl_runtime_closure.py -q
```

Expected: PASS.

---

### Task 10: AAN-11.6 Multi-view Material Evidence Schema

**Files:**
- Modify: `convert_asset/asset_application_normalizer/mdl_runtime_closure.py`
- Modify: `tests/test_asset_application_normalizer_mdl_runtime_closure.py`

- [x] **Step 1: Write failing view evidence normalization test**

Add:

```python
from convert_asset.asset_application_normalizer.mdl_runtime_closure import build_material_view_evidence


def test_build_material_view_evidence_preserves_required_render_metrics() -> None:
    evidence = build_material_view_evidence(
        [
            {
                "view_id": "front",
                "camera_pose": {"position": [1, 0, 1], "look_at": [0, 0, 0]},
                "target_prim": "/World/DryingBox",
                "render_hash": "a" * 64,
                "mean_rgb": [0.2, 0.3, 0.4],
                "foreground_rgb": [0.25, 0.35, 0.45],
                "non_background_ratio": 0.42,
                "bbox_ratio": 0.3,
            }
        ]
    )

    assert evidence == [
        {
            "view_id": "front",
            "camera_pose": {"position": [1, 0, 1], "look_at": [0, 0, 0]},
            "target_prim": "/World/DryingBox",
            "render_hash": "a" * 64,
            "mean_rgb": [0.2, 0.3, 0.4],
            "foreground_rgb": [0.25, 0.35, 0.45],
            "non_background_ratio": 0.42,
            "bbox_ratio": 0.3,
        }
    ]
```

- [x] **Step 2: Run test to verify RED**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_mdl_runtime_closure.py::test_build_material_view_evidence_preserves_required_render_metrics -q
```

Expected: FAIL with missing `build_material_view_evidence`.

- [x] **Step 3: Implement schema helper**

Add:

```python
_VIEW_EVIDENCE_KEYS = {
    "view_id",
    "camera_pose",
    "target_prim",
    "render_hash",
    "mean_rgb",
    "foreground_rgb",
    "non_background_ratio",
    "bbox_ratio",
}


def build_material_view_evidence(records: list[dict]) -> list[dict]:
    normalized = []
    for record in records:
        missing = sorted(_VIEW_EVIDENCE_KEYS.difference(record))
        if missing:
            raise ValueError(f"material view evidence missing keys: {', '.join(missing)}")
        normalized.append({key: record[key] for key in sorted(_VIEW_EVIDENCE_KEYS)})
    return normalized
```

- [x] **Step 4: Run tests**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_mdl_runtime_closure.py -q
```

Expected: PASS.

---

### Task 11: Documentation And Closeout For Implemented Slice

**Files:**
- Modify: `docs/records/2026-07-02-aan-11-material-runtime-closure.md`
- Modify: `docs/records/README.md` only if a new implementation record is created

- [x] **Step 1: Update implementation record**

Append a section named `Implementation Progress` with:

```markdown
## Implementation Progress

### AAN-11.1 / AAN-11.2 Static Graph Slice

- Added pure-Python MDL import/using/texture parsing.
- Added native module classification for `df`, `base`, `state`, `tex`, `anno`, and `math`.
- Added package-local MDL root discovery from `deps/mdl/**/*.mdl` and `material_closure[*].source_mdl_assets`.
- Added nested relative module path handling such as `.::templates::mdl_0001::*`
  resolving to `deps/mdl/templates/mdl_0001.mdl`.
- Added manifest-level `material_runtime_closure` and `static_material_runtime_report`.
- Verification:
  - `python -m pytest tests/test_asset_application_normalizer_mdl_runtime_closure.py -q`
  - `python -m pytest tests/test_asset_application_normalizer_cli.py -q`
  - `git diff --check`
```

- [x] **Step 2: Run final verification**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_mdl_runtime_closure.py tests/test_asset_application_normalizer_cli.py tests/test_asset_application_normalizer_pm_and_mjcf.py -q
python -m compileall convert_asset/asset_application_normalizer
git diff --check
```

Expected: all pass.

- [x] **Step 3: Review git status**

Run:

```bash
git status --short
```

Expected: only AAN-11 code/tests/docs and previously known AAN-11 docs are modified.

---

## Implementation Delta

The original AAN-11.4 plan called for a static binding-scope skeleton. The completed
implementation extends this to effective UsdShade binding tracing when `pxr` and the
package root USD are available. The final report records direct versus inherited
binding, `bound_at_prim`, descendant render mesh bindings, and
`non_render_required_prims` for existing joint/helper prims that should not be treated
as unknown material gaps.

Final retained verification also includes DryingBox, MuffleFurnace, and Beaker_01
runtime packages under `/tmp/aan11_real_packages_final`, with copied manifests, logs,
single render PNGs, and three material-view PNGs under
`docs/records/evidence/2026-07-02-aan-11-material-runtime-closure/runtime/`.
