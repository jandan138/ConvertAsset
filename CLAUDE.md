# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ConvertAsset** is a USD (Universal Scene Description) asset conversion and optimization toolkit for NVIDIA Isaac Sim environments. It converts USD assets with MDL materials to UsdPreviewSurface, simplifies meshes, and exports to GLB (glTF 2.0).

## Running Commands

All commands require Isaac Sim's Python environment (provides the `pxr` USD bindings).

```bash
# Wrapper script auto-detects Isaac Sim installation (respects $ISAAC_SIM_ROOT env var)
./scripts/isaac_python.sh ./main.py <subcommand> [args]

# Core subcommands:
./scripts/isaac_python.sh ./main.py no-mdl /path/to/scene.usd
./scripts/isaac_python.sh ./main.py mesh-simplify /path/to/scene.usd --backend py --ratio 0.5 --apply --out /output.usd
./scripts/isaac_python.sh ./main.py export-glb /path/to/scene_noMDL.usd --out /output.glb
./scripts/isaac_python.sh ./main.py usd-to-glb /path/to/scene.usd --out /output.glb
./scripts/isaac_python.sh ./main.py inspect /path/to/scene.usd usdpreview /Looks/MaterialName
./scripts/isaac_python.sh ./main.py mesh-faces /path/to/scene.usd
```

Default subcommand (when none specified) is `no-mdl`.

## Building the Optional C++ QEM Backend

```bash
# 1. Install pybind11 in Isaac Sim environment
python -m pip install "pybind11[global]"

# 2. Build
cd native/meshqem && mkdir -p build && cd build
cmake -DBUILD_MESHQEM_PY=ON ..
cmake --build . --config Release -j4

# 3. Copy compiled module to package
cp meshqem_py.cpython-*.so ../../../convert_asset/mesh/
```

After building, use `--backend cpp-uv` to invoke the C++ path.

## Architecture

### Entry Points

- **`main.py`** → calls `convert_asset.cli.main(sys.argv[1:])`
- **`convert_asset/cli.py`** → parses subcommands and dispatches to modules
- **`scripts/isaac_python.sh`** → sets up Isaac Sim Python environment, then runs `main.py`

### Modules

| Module | Responsibility |
|---|---|
| `no_mdl/processor.py` | Recursive USD traversal; detects/deduplicates dependencies, writes `*_noMDL.usd` |
| `no_mdl/materials.py` | Builds UsdPreviewSurface network, removes MDL shaders |
| `no_mdl/references.py` | Collects asset paths (sublayers, references, payloads, variants, clips) and rewrites them |
| `no_mdl/config.py` | Central configuration — MDL conversion strategy, diagnostic levels, output suffix |
| `mesh/simplify.py` | Pure-Python QEM mesh simplification with face-varying UV preservation |
| `mesh/backend_cpp.py` | Wraps compiled C++ QEM executable |
| `mesh/backend_cpp_impl.py` | pybind11 in-process C++ integration |
| `glb/converter.py` | Orchestrates USD→GLB pipeline |
| `glb/usd_mesh.py` | Mesh extraction; flattens face-varying UVs for glTF compliance |
| `glb/usd_material.py` | Extracts UsdPreviewSurface material/texture data |
| `glb/writer.py` | Writes binary glTF 2.0 (`.glb`) |
| `camera/fit.py`, `camera/orbit.py` | Camera framing for thumbnail rendering |

### Key Design Decisions

1. **Non-flattening composition**: Each USD file is processed independently — references/payloads/variants are preserved as-is; only asset paths are updated to `*_noMDL` variants.
2. **Cycle detection**: `Processor.in_stack` (set) prevents infinite recursion; `Processor.done` (dict) deduplicates already-converted files.
3. **Face-varying UV flattening**: glTF requires per-vertex UVs, so `usd_mesh.py` splits vertices when USD uses face-varying interpolation.
4. **Lazy imports**: `pxr` and other heavy Isaac Sim dependencies are imported only inside functions, not at module top-level.
5. **Multiple simplification backends**: `py` (pure Python), `cpp` (subprocess), `cpp-uv` (pybind11 in-process). The C++ backends are optional; the project works fully without them.

### Configuration

`convert_asset/no_mdl/config.py` controls behavior without touching core logic:
- `SUFFIX = "_noMDL"` — output file naming
- `MATERIAL_ROOT_HINTS` — where to search for materials
- `OVERRIDE_EXTERNAL_MDL_PREVIEW` — improve fidelity for external MDL
- `ALLOW_EXTERNAL_ONLY_PASS` — allow export with residual external MDL
- `DIAGNOSTIC_LEVEL` — verbosity of diagnostic output

## External Dependencies

- **`pxr`** (Usd, UsdGeom, UsdShade, Sdf, Gf) — provided by Isaac Sim, not pip-installable standalone
- **`numpy`** — array math for mesh operations
- **`pybind11`** — only needed when building the C++ QEM backend

## Docs

`docs/` uses a Genesis-LLM-style purpose-based structure:

| Path | Purpose |
|---|---|
| `docs/index.md` | Canonical documentation entry |
| `docs/setup.md` | Isaac Sim Python and runtime setup |
| `docs/design/` | Architecture, module responsibilities, algorithms, implementation deep dives |
| `docs/operations/` | CLI usage, runbooks, build instructions, troubleshooting, agent operations |
| `docs/records/` | Dated change logs, implementation records, audits, route decisions |
| `docs/reference/` | USD, UsdShade, MDL, and material background knowledge |
| `archive/` | Retained historical material that is not first-class active documentation |

Chinese inline comments are used throughout the source.

## Agent Team Documentation Rule (Mandatory)

**Every agent in a team MUST produce documentation for its work.** This is a hard requirement, not optional.

### What to document

Each agent must record the full lifecycle of its task:

1. **Research / Investigation** — what was explored, which files were read, what was discovered
2. **Design decisions** — why a particular approach was chosen, alternatives considered
3. **Code changes** — what was modified, added, or deleted, with file paths and brief rationale
4. **Testing** — what was tested, how it was tested, test commands run, and results (pass/fail/output)
5. **Open issues** — known limitations, follow-up work needed, edge cases not covered

### Where to write

- Place dated change logs and implementation records under `docs/records/`
- Place architecture, algorithm, and feature design docs under `docs/design/`
- Place CLI usage, setup, runbooks, and troubleshooting under `docs/operations/`
- Place USD, MDL, and conceptual background under `docs/reference/`
- Place retained but non-current historical material under `archive/`
- Keep `docs/index.md` and the relevant directory `README.md` updated when adding first-class docs

### How: agents with write permission

If the agent has file-write capability (Edit/Write tools), it **must write the documentation itself** before marking its task as completed. A task is NOT complete until its documentation is committed.

### How: agents without write permission

If the agent is read-only (e.g., Explore, Plan agents), it **must send a message to the docs-writer agent** (or request the team lead to dispatch docs-writer) with:
- A structured summary of findings, decisions, and results
- Suggested file path and title for the documentation

### Enforcement

- Team leads must verify documentation exists before accepting a task as completed
- The version-commit-agent should check for corresponding `docs/` changes when committing code changes — if missing, flag a warning
