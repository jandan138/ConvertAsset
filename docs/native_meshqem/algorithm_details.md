# QEM Algorithm Details (Native C++)

This document walks through the math and code path of the QEM implementation in `src/qem.cpp`.

## Plane Quadrics Recap

Given a triangle with vertices p, q, r in 3D, its plane normal is:

- `n = normalize((q - p) × (r - p))`

The plane equation is `a x + b y + c z + d = 0`, where `[a,b,c] = n` and `d = -dot(n, p)`.

The quadric for this plane is a 4×4 matrix `K = p p^T` with `p=[a,b,c,d]`.

For any homogeneous point `v' = [x, y, z, 1]`, the squared distance proxy is:

- `E(v') = v'^T K v'`

Summing quadrics across faces meeting at a vertex yields a quadric `Q[v]` that measures how far a point deviates from all incident planes.

## Edge Collapse Cost

To collapse an edge `(u, v)`, we merge quadrics:

- `Quv = Q[u] + Q[v]`

We seek the point `x = [x, y, z]` minimizing `E([x,1])`. This is obtained by solving the 3×3 system:

```
A x = b
A = Quv[0:3,0:3]
b = -Quv[0:3,3]
```

If `A` is singular or ill-conditioned, we fallback to the midpoint `(pu + pv)/2`.

The collapse cost is then `E([x,1])` evaluated by `quadric_eval`.

## Main Loop Mechanics

1) Build `Q[v]` per vertex by iterating faces; positions with zero-area faces are culled early (`face_alive=false`).
2) Build adjacency `adj[v]` as an unordered set of neighbor vertex indices.
3) Initialize a min-heap of candidate edges by pushing `(u, v)` for `u < v` with their initial costs.
4) While `faces_current > target && !heap.empty() && collapsed < max_collapses`:
   - Respect `time_limit` (seconds) and break if exceeded.
   - Pop the lowest-cost edge `(u, v)`; skip if either vertex is dead or no longer neighbors.
   - Move `u` to the new position (midpoint in v1); merge `Q[u] += Q[v]`; mark `v` dead.
   - Rewire adjacency: neighbors of `v` now connect to `u`.
   - Update faces: replace `v` with `u` and drop degenerate ones (duplicate indices).
   - Push updated candidate edges around `u` back into the heap.

5) After the loop, compact vertices and faces:
   - Build a `remap[]` from old vertex IDs to new compacted IDs.
   - Copy surviving vertices and faces into fresh arrays.

## Numerical Guardrails

- Degenerate faces (area < 1e-12) are ignored when building quadrics; this keeps `Q` bounded.
- Partial pivoting in `solve3` handles common near-singular cases.
- Midpoint fallback avoids noisy solutions; the cost still reflects merged `Q`.

## Complexity Notes

- Each collapse updates adjacency and potentially pushes O(deg(u)) edges back into the heap.
- With a binary heap, push/pop is `O(log E)` where `E` is the number of edges in the current graph.
- Overall, practical performance is good for small-to-medium meshes; for very large ones, prefer the C++ backend (this native code) via the Python adapter.

## Quality Tweaks (Future Work)

- Use the solved optimal position `x` (instead of midpoint) for better fidelity.
- Add boundary preservation by detecting boundary edges and restricting collapses.
- Integrate normal/UV attribute reprojection post-collapse.
- Add triangle flip checks by monitoring orientation.

---
