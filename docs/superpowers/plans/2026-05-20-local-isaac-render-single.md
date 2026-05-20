# Local Isaac Render Single Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local Isaac Sim `render-single` command to ConvertAsset and remove the CLI import-order problem that makes render commands unsafe.

**Architecture:** `convert_asset.render.single` owns the new runtime. `convert_asset.cli` only parses and lazily imports it. Tests stay pure-Python and assert import isolation plus deterministic output planning; actual Isaac rendering is verified by a smoke command.

**Tech Stack:** Python 3.10, Isaac Sim `SimulationApp`, `omni.isaac.sensor.Camera`, `pxr.UsdGeom`, OpenCV, NumPy, pytest.

---

### Task 1: Add Import-Isolation Regression Tests

**Files:**
- Create: `tests/test_render_single.py`

- [ ] **Step 1: Write failing tests**

```python
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_probe(code: str) -> str:
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout.strip()


def test_cli_import_does_not_load_pxr() -> None:
    output = run_probe(
        "import sys; import convert_asset.cli; "
        "print(any(name == 'pxr' or name.startswith('pxr.') for name in sys.modules))"
    )
    assert output == "False"


def test_render_single_module_import_is_runtime_clean() -> None:
    output = run_probe(
        "import sys; import convert_asset.render.single; "
        "print(any(name in sys.modules for name in ('isaacsim', 'omni', 'pxr')))"
    )
    assert output == "False"
```

- [ ] **Step 2: Run tests to verify RED**

Run: `python -m pytest tests/test_render_single.py -q`

Expected before implementation: at least one failure because `convert_asset.cli` currently imports `convert_asset.mesh.faces`, which imports `pxr`.

### Task 2: Fix CLI Import Order

**Files:**
- Modify: `convert_asset/cli.py`

- [ ] **Step 1: Remove the top-level mesh-faces import**

Delete the top-level import:

```python
from .mesh.faces import count_mesh_faces
```

- [ ] **Step 2: Lazy import inside the `mesh-faces` branch**

Use this inside `if args_ns.cmd == "mesh-faces":` before calling `count_mesh_faces`:

```python
from .mesh.faces import count_mesh_faces
```

- [ ] **Step 3: Run import-isolation test**

Run: `python -m pytest tests/test_render_single.py::test_cli_import_does_not_load_pxr -q`

Expected: PASS.

### Task 3: Add Pure Render Planning Helpers

**Files:**
- Create: `convert_asset/render/__init__.py`
- Create: `convert_asset/render/single.py`
- Modify: `tests/test_render_single.py`

- [ ] **Step 1: Add tests for output planning**

Append:

```python
def test_plan_output_paths_uses_view_names(tmp_path: Path) -> None:
    from convert_asset.render.single import plan_output_paths

    usd_path = tmp_path / "asset.usd"
    usd_path.write_text("#usda 1.0\n", encoding="utf-8")

    planned = plan_output_paths(
        usd_path=usd_path,
        output_root=tmp_path / "renders",
        sample_number=4,
        naming_style="view",
    )

    assert [item.name for item in planned] == ["front.png", "left.png", "back.png", "right.png"]
    assert planned[0].parent == tmp_path / "renders" / "asset"
```

- [ ] **Step 2: Add pure helpers**

Create `convert_asset/render/single.py` with top-level imports limited to stdlib plus type-only safe modules. Define:

```python
VIEW_NAMES = ("front", "left", "back", "right")

def plan_output_paths(usd_path: Path, output_root: Path, sample_number: int, naming_style: str) -> list[Path]:
    ...
```

- [ ] **Step 3: Run tests**

Run: `python -m pytest tests/test_render_single.py -q`

Expected: PASS after implementation.

### Task 4: Implement `render-single` Runtime

**Files:**
- Modify: `convert_asset/render/single.py`
- Modify: `convert_asset/cli.py`

- [ ] **Step 1: Add CLI parser**

Add subcommand:

```python
p_render_single = sub.add_parser("render-single", help="Render one USD asset with local Isaac Sim")
p_render_single.add_argument("src", help="Path to USD file")
p_render_single.add_argument("--out", required=True, help="Output root directory")
p_render_single.add_argument("--width", type=int, default=512)
p_render_single.add_argument("--height", type=int, default=512)
p_render_single.add_argument("--views", type=int, default=4)
p_render_single.add_argument("--warmup-steps", type=int, default=100)
p_render_single.add_argument("--render-steps", type=int, default=8)
p_render_single.add_argument("--focal-mm", type=float, default=18.0)
p_render_single.add_argument("--renderer", default="PathTracing")
p_render_single.add_argument("--naming-style", choices=["index", "view"], default="index")
p_render_single.add_argument("--overwrite", action="store_true")
```

- [ ] **Step 2: Add lazy dispatch**

Inside `main`:

```python
if args_ns.cmd == "render-single":
    from .render.single import run_render_single
    return int(run_render_single(...))
```

- [ ] **Step 3: Implement runtime with SimulationApp first**

Inside `run_render_single`, import `SimulationApp`, create it, then import `omni`, `World`, `Camera`, `create_prim`, `delete_prim`, `add_update_semantics`, `UsdGeom`, and `UsdLux`.

- [ ] **Step 4: Run local help**

Run: `python main.py render-single --help`

Expected: command help prints without importing `isaacsim`.

### Task 5: Smoke Render With Local Isaac

**Files:**
- Runtime output only under `/tmp/convertasset-render-single-smoke`

- [ ] **Step 1: Run smoke command**

```bash
rm -rf /tmp/convertasset-render-single-smoke
./scripts/isaac_python.sh ./main.py render-single \
  assets/usd/chestofdrawers_nomdl/chestofdrawers_0011/instance.usd \
  --out /tmp/convertasset-render-single-smoke \
  --naming-style view \
  --overwrite
```

- [ ] **Step 2: Verify outputs**

Run:

```bash
find /tmp/convertasset-render-single-smoke -type f -name '*.png' -printf '%p %s\n' | sort
```

Expected: four nonempty files named `front.png`, `left.png`, `back.png`, `right.png`.

### Task 6: Document Result

**Files:**
- Create: `docs/operations/local-rendering.md`
- Create: `docs/records/2026-05-20-local-isaac-render-single.md`
- Modify: `docs/records/README.md`
- Modify: `docs/superpowers/README.md`

- [ ] **Step 1: Write operations runbook**

Document `render-single`, environment requirements, the reason `SimulationApp` must start before `pxr/omni`, and how this becomes the base for ACL `render_manifest` execution.

- [ ] **Step 2: Write implementation record**

Record findings, design decisions, tests, smoke output, and remaining work.

- [ ] **Step 3: Run verification**

Run:

```bash
python -m pytest tests/test_render_single.py tests/test_grscenes_vlm_render_manifest.py tests/test_paper_layout.py -q
python -m py_compile convert_asset/render/single.py convert_asset/cli.py
git diff --check
```

Expected: all pass.
