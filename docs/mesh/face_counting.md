# Face Counting (USD Mesh)

This page explains how the project counts faces (polygons) from USD meshes.

Scope and rules:
- Traverse all active prims of type `UsdGeom.Mesh`.
- Skip instance proxies to avoid counting both prototypes and instance views.
- Optionally filter by purpose: ignore `proxy` and `guide`, keep `default` and `render`.
- Face count equals the number of entries in `faceVertexCounts`.
- No triangulation or flattening occurs.

Why skip instance proxies?
- USD traversal can visit instance views; counting both instance proxies and underlying prototypes would double count. Skipping proxies ensures each authored mesh is counted once per prim encountered in traversal.

CLI example:
```
python -m convert_asset.cli mesh-faces <stage.usd>
```

Implementation reference: `convert_asset/mesh/faces.py`.
