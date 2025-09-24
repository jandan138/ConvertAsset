# Overview

The Python QEM backend provides triangle-only mesh decimation for USD stages without external dependencies. It targets small-to-medium meshes or constrained runs (via time limits), and mirrors the C++ backend semantics where possible.

Key points:
- Only active `UsdGeom.Mesh` prims with purposes `default` and `render` are processed; `proxy`/`guide` and instance proxies are skipped.
- Triangles-only: non-triangle meshes are skipped in this backend.
- Two modes:
  - Dry-run: estimate face counts after decimation, print a summary.
  - Apply: compute new points/topology and write back to the USD stage.
