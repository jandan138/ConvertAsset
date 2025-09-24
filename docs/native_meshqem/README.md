# meshqem Native Backend Deep Dive

This guide explains the native C++ implementation that powers the `--backend cpp` mode of mesh simplification. It aims to be friendly, thorough, and practical.

- What it is: a tiny, dependency-free Quadric Error Metrics (QEM) decimator for triangle meshes.
- Where it lives: `native/meshqem` (CMake project) plus a Python adapter at `convert_asset/mesh/backend_cpp.py`.
- Why it exists: performance and portability, while keeping code easy to read and maintain.

## Quick Map

- `src/mesh.hpp`, `src/mesh.cpp`: minimal mesh container (`verts`, `faces`).
- `src/io_obj.hpp`, `src/io_obj.cpp`: triangle-only OBJ reader/writer (positions only).
- `src/qem.hpp`, `src/qem.cpp`: the QEM core (quadrics, heap of edges, collapse loop).
- `src/main.cpp`: CLI wrapper; parses flags, runs QEM, prints summary.
- `CMakeLists.txt`: build script (`-O3`, C++17).

## Algorithm: QEM in 5 minutes

Inputs:
- Vertices V = [(x,y,z)...] (double)
- Triangles F = [(i,j,k)...] (0-based)

Steps:
1) For each triangle t=(i,j,k), compute plane normal n and equation `ax+by+cz+d=0`. Build a 4x4 quadric `K = p p^T` with `p=[a,b,c,d]`.
2) Accumulate `K` to the three vertices' quadrics: `Q[i]+=K`, `Q[j]+=K`, `Q[k]+=K`.
3) For each undirected edge (u,v) in adjacency, estimate collapse cost by merging quadrics `Quv = Q[u]+Q[v]` and evaluating `v'^T Quv v'` at:
   - the optimal position (solve a 3x3), or
   - fallback: midpoint of endpoints if system is singular.
4) Repeatedly pop the cheapest edge, collapse v->u (move u to new position), merge quadrics, update faces/adjacency, and push new edges around u.
5) Stop at target faces, or hit time/collapse caps; compact arrays and return.

What we don’t do in v1 (on purpose): attribute preservation (normals/UVs), boundary/feature heuristics, flip detection. The focus is clarity and robustness.

## Files Explained

### `mesh.hpp` / `mesh.cpp`
- `Vec3`, `Tri` are plain structs for cache-friendly data.
- `Mesh` stores `verts` (positions) and `faces` (triangles). `clear()` resets both arrays.

### `io_obj.hpp` / `io_obj.cpp`
- Reads `v` (positions) and `f` (triangles) only. Ignores vt/vn/materials/objects.
- Converts OBJ 1-based indices to internal 0-based; saves back symmetrically.
- Defensive checks: reports error if file can’t be opened or mesh is empty.

### `qem.hpp` / `qem.cpp`
- `Quadric`: 4x4 matrix in row-major order.
- `EdgeCand`: node in a min-heap (priority_queue with inverted comparator).
- `SimplifyOptions`: knobs for ratio/target, max collapses, time-limit, progress cadence.
- `qem_simplify`: the engine. Highly commented code explains each step.

Key helpers:
- `plane_quadric(a,b,c,d)`: builds `K = p p^T`.
- `solve3(A,b)`: small 3x3 Gaussian elimination with partial pivoting.
- `quadric_eval(Q, v4)`: computes `v^T Q v` at `[x,y,z,1]`.

Quality and safety:
- Drops zero-area triangles when building quadrics.
- Uses midpoint for vertex position after collapse (stable and simple). You can switch to the optimal `x` if desired.
- Time limit stops the current mesh simplification but returns a valid (partially simplified) result.

### `main.cpp`
- Minimal CLI. Prints exactly two summary lines to stdout so the Python side can parse:
  - `faces: M -> N`
  - `verts: A -> B`
- Progress lines (every N collapses) go to stderr.

## Building and Running

Build:
```
mkdir -p native/meshqem/build
cd native/meshqem/build
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build . -j
```
Run directly:
```
./meshqem --in in.obj --out out.obj --ratio 0.5 --progress-interval 20000
```
From Python adapter (recommended): see `convert_asset/mesh/backend_cpp.py` and the CLI `mesh-simplify --backend cpp`.

## Tuning and Extensions

- Use conservative ratios (e.g., 0.9 or 0.7) for initial validation.
- Set `--time-limit` to keep large meshes bounded in time.
- Future enhancements (not in v1):
  - Boundary preservation and feature sensitivity
  - Attribute propagation (normals/UVs)
  - Flip detection and quality metrics
  - Parallel per-mesh execution

## FAQ

- Why triangle-only? Simplicity and speed. Non-triangle meshes can be triangulated upstream.
- Why double precision? To minimize drift over many collapses.
- Why midpoint instead of the optimal `x` when collapsing? Stability and simplicity; the cost still guides ordering. You can switch to `x` with small code changes.

## Troubleshooting

- "cannot open": check input path and file permissions.
- "empty mesh": ensure your OBJ has both `v` and `f` lines.
- Progress stalls: adjust `--progress-interval` or set a `--time-limit`.

---
Last updated: 2025-09-24
