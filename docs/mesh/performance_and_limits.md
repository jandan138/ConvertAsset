# Performance and Limits

Python backend is intentionally simple and dependency-free. It is suitable for:
- Prototyping and visual checks
- Small to medium meshes
- Bounded-time runs using `--time-limit`

Tips:
- Start with a conservative `--ratio` (e.g., 0.9 or 0.7) to validate pipeline and evaluate quality.
- Use `--time-limit` to ensure large meshes do not stall sessions; the run will continue with other meshes.
- Combine dry-run planning and per-mesh progress output to reduce surprises.

For large scenes or aggressive decimation, prefer the C++ backend.
