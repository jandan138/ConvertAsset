#!/usr/bin/env python3
import sys
import argparse
from pxr import Usd, UsdGeom


def _get_texcoord_primvars(mesh: UsdGeom.Mesh):
    api = UsdGeom.PrimvarsAPI(mesh.GetPrim())
    primvars = api.GetPrimvarsWithAuthoredValues()
    result = []
    for pv in primvars:
        name = pv.GetBaseName()
        role = pv.GetAttr().GetMetadata('roleName')
        role_l = role.lower() if isinstance(role, str) else None
        if role_l == "texturecoordinate":
            result.append(pv)
        elif name in ("st", "uv"):
            result.append(pv)
    return result


def _len_safe(value):
    try:
        return len(value) if value is not None else 0
    except Exception:
        return 0


def audit_stage(usdf: str, limit: int = 50):
    stage = Usd.Stage.Open(usdf)
    if not stage:
        print(f"[ERROR] Failed to open stage: {usdf}")
        return 2

    total_mesh = 0
    with_uv = 0
    fv_uv = 0
    mismatches = []

    for prim in stage.TraverseAll():
        if not prim.IsA(UsdGeom.Mesh):
            continue
        total_mesh += 1
        mesh = UsdGeom.Mesh(prim)
        fvc = mesh.GetFaceVertexCountsAttr().Get()
        if not fvc:
            continue
        num_corners = int(sum(int(x) for x in fvc))
        pts = mesh.GetPointsAttr().Get()
        num_points = _len_safe(pts)

        pvs = _get_texcoord_primvars(mesh)
        if pvs:
            with_uv += 1
        for pv in pvs:
            interp = pv.GetInterpolation()
            vals = pv.Get()
            vals_len = _len_safe(vals)
            idx = pv.GetIndicesAttr().Get()
            idx_len = _len_safe(idx)

            if interp == UsdGeom.Tokens.faceVarying:
                fv_uv += 1
                if idx_len > 0:
                    ok = (idx_len == num_corners)
                    if not ok:
                        mismatches.append({
                            "path": prim.GetPath().pathString,
                            "primvar": pv.GetPrimvarName(),
                            "interp": interp,
                            "expected_corners": num_corners,
                            "indices_len": idx_len,
                            "values_len": vals_len,
                            "reason": "indices length != face corners",
                        })
                else:
                    ok = (vals_len == num_corners)
                    if not ok:
                        mismatches.append({
                            "path": prim.GetPath().pathString,
                            "primvar": pv.GetPrimvarName(),
                            "interp": interp,
                            "expected_corners": num_corners,
                            "indices_len": idx_len,
                            "values_len": vals_len,
                            "reason": "values length != face corners",
                        })
            elif interp == UsdGeom.Tokens.vertex:
                if idx_len > 0:
                    ok = (idx_len == num_points)
                    if not ok:
                        mismatches.append({
                            "path": prim.GetPath().pathString,
                            "primvar": pv.GetPrimvarName(),
                            "interp": interp,
                            "expected_points": num_points,
                            "indices_len": idx_len,
                            "values_len": vals_len,
                            "reason": "indices length != vertex count",
                        })
                else:
                    ok = (vals_len == num_points)
                    if not ok:
                        mismatches.append({
                            "path": prim.GetPath().pathString,
                            "primvar": pv.GetPrimvarName(),
                            "interp": interp,
                            "expected_points": num_points,
                            "indices_len": idx_len,
                            "values_len": vals_len,
                            "reason": "values length != vertex count",
                        })
            else:
                # uniform/constant/varying: 这里不强制校验
                pass

    print(f"[SUMMARY] meshes={total_mesh} with_uv={with_uv} faceVarying_uv={fv_uv} mismatches={len(mismatches)}")
    if mismatches:
        print(f"[DETAIL] first {min(limit, len(mismatches))} mismatches:")
        for m in mismatches[:limit]:
            print(
                f"- {m['path']} primvar={m['primvar']} interp={m['interp']} reason={m['reason']} "
                f"expectedCorners={m.get('expected_corners','-')} expectedPoints={m.get('expected_points','-')} "
                f"valuesLen={m['values_len']} indicesLen={m['indices_len']}"
            )
    return 0


essential_desc = """
Audit UV primvars consistency for a USD: check primvars:st/uv interpolation and lengths
against face corners (for faceVarying) or vertex count (for vertex).
""".strip()


def main(argv=None):
    p = argparse.ArgumentParser(description=essential_desc)
    p.add_argument("usd", help="Path to USD file")
    p.add_argument("--limit", type=int, default=50, help="Max mismatches to print")
    args = p.parse_args(argv)
    return audit_stage(args.usd, args.limit)


if __name__ == "__main__":
    sys.exit(main())
