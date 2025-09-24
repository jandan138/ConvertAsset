# meshqem - Quadric Error Metrics Mesh Simplifier (C++)

A self-contained C++ implementation of Quadric Edge Collapse decimation for triangle meshes.

- Input/Output format: OBJ (triangles only). Ignores normals/UVs for v1.
- Options: target ratio or target faces, max collapses, per-mesh time limit, progress interval.
- Designed to be called from Python (`convert_asset.mesh.backend_cpp`).

## Build
```
mkdir -p build
cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build . -j
```
This produces `meshqem` executable in `build/`.

## Usage
```
./meshqem --in input.obj --out output.obj --ratio 0.5 \
  --max-collapses 200000 --time-limit 120 --progress-interval 20000
```

## Notes
- For robustness, only triangle faces are supported. Non-triangle will error out.
- Boundary preservation and attributes (normals/UVs) can be added in later iterations.