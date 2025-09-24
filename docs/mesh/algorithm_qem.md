# QEM Algorithm (Python reference)

Inputs:
- V: list of 3D points `(x, y, z)`
- F: list of triangle indices `(i, j, k)`
- Target faces `T` (computed from `--ratio` or derived from `--target-faces` planning)

Steps:
1. For each triangle, compute the plane normal and plane equation, then build its 4x4 quadric `K = p p^T`, where `p=[a,b,c,d]` for the plane `ax + by + cz + d = 0`.
2. Accumulate quadrics to the involved vertices: `Q[v] += K`.
3. Build vertex adjacency; initialize a min-heap of candidate edges (u,v) with cost computed as `v'^T (Q[u]+Q[v]) v'`:
   - Solve optimal `v'` from a 3x3 linear system. If singular, fallback to midpoint of endpoints.
4. Repeatedly pop the cheapest edge and collapse it (merge v into u, set u to v'), update faces and adjacency, and push new candidate edges around u.
5. Stop when `faces<=T`, heap is empty, or time-limit reached.
6. Compact vertices and remap triangle indices.

Edge cases and guards:
- Degenerate faces (area ~ 0) are dropped.
- Time limit per mesh (seconds) aborts early for that mesh but not the whole stage.
- No normal/UV preservation in v1; this is a geometric topology-only pass.
