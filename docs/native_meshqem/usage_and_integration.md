# Usage and Integration (meshqem + Python adapter)

This page focuses on how the native executable is used from Python and how to run it directly.

## Direct CLI

Build (once):
```
mkdir -p native/meshqem/build
cd native/meshqem/build
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build . -j
```
Run:
```
./meshqem --in in.obj --out out.obj --ratio 0.5 \
  --max-collapses 200000 --time-limit 120 --progress-interval 20000
```
Outputs two summary lines to stdout:
```
faces: <before> -> <after>
verts: <before> -> <after>
```
Progress goes to stderr every N collapses.

## Python Adapter

File: `convert_asset/mesh/backend_cpp.py`

Workflow per `UsdGeom.Mesh` prim:
1) Extract points and topology, assert triangle-only.
2) Write a temporary `in.obj` (positions + triangle indices).
3) Execute the native `meshqem` with desired flags (`--ratio` or `--target-faces`, time-limit, etc.).
4) Parse stdout for before/after counts; read `out.obj` and write back to USD when `apply=True`.

CLI integration (from `convert_asset/cli.py`):
```
python -m convert_asset.cli mesh-simplify <stage.usd> \
  --backend cpp --cpp-exe native/meshqem/build/meshqem \
  --ratio 0.9 --apply --out <out.usd> --progress --time-limit 60
```

## Planning Mode (Dry-run)

For the C++ backend, planning (`--target-faces` without `--apply`) returns early with a suggested ratio and skips invoking the native binary. This avoids unnecessary native runs when you only need a global ratio estimate.

## Tips

- Ensure meshes are triangles; non-triangle meshes are skipped by the adapter.
- Use `--progress` in Python CLI to see per-mesh progress and timeouts.
- Start with a gentle ratio to validate pipeline quality, then iterate.

---
