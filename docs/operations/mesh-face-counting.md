# 面数统计（USD Mesh）

本文解释我们如何从 USD Mesh 统计“面片总数”。

范围与规则：
- 遍历所有活跃的 `UsdGeom.Mesh`；
- 跳过 Instance Proxy（避免对原型与实例视图重复计数）；
- 用途过滤（purpose）：忽略 `proxy/guide`，保留 `default/render`；
- 面数定义为 `faceVertexCounts` 的条目数（不打平、不三角化、不展开）。

为什么要跳过 Instance Proxy？
- USD 的遍历会访问实例视图；若同时统计实例视图与其原型，会重复计数。跳过 Instance Proxy 可确保每个 Mesh 只统计一次（按遍历遇到的 Prim）。

CLI 使用：
```
python -m convert_asset.cli mesh-faces <stage.usd>
```

核心实现（摘自 `convert_asset/mesh/faces.py`）：
```python
total = 0
for prim in stage.Traverse():
	if not prim.IsActive() or prim.IsInstanceProxy():
		continue
	if prim.GetTypeName() != "Mesh":
		continue
	img = UsdGeom.Imageable(prim)
	purpose = img.ComputePurpose()
	if purpose in (UsdGeom.Tokens.proxy, UsdGeom.Tokens.guide):
		continue
	mesh = UsdGeom.Mesh(prim)
	counts = mesh.GetFaceVertexCountsAttr().Get()
	if counts is None:
		continue
	total += len(counts)
```

注意：这是一种“保守、不打平”的统计，严格遵循 USD 的组合与可见性过滤，不会改变场景结构。
