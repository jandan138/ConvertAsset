"""Export MDL materials from current USD into standalone UsdPreviewSurface material USDs.

Rules:
- Only process materials defined in the current root layer (no flatten, no editing external files).
- For each MDL-driven material, build a minimal UsdPreviewSurface network and wire textures.
- Write each material into a separate USD file under <root_layer_dir>/<out_dir_name>/, default out_dir_name='mdl_materials'.

Outputs are stand-alone stages that contain a single Material prim at /Looks/<MaterialName> with internal preview network.
"""
from __future__ import annotations
from typing import List, Tuple
import os
from pxr import Usd, UsdShade, Sdf, UsdGeom  # type: ignore

from .no_mdl.materials import ensure_preview, find_mdl_shader, copy_textures, connect_preview, _resolve_abs_path, _anchor_dir_for_attr


def _is_in_root_layer(stage: Usd.Stage, prim: Usd.Prim) -> bool:
    root_id = stage.GetRootLayer().identifier
    try:
        for spec in prim.GetPrimStack():
            if spec.layer.identifier == root_id:
                return True
    except Exception:
        pass
    return False


def _authoring_layer_dir_for_prim(prim: Usd.Prim) -> str | None:
    """Try to find the weakest non-anonymous layer contributing a PrimSpec for this prim.
    This usually corresponds to the place where the prim was originally defined (referenced child file).
    Return the directory path for that layer, or None if unknown.
    """
    try:
        stack = prim.GetPrimStack()
    except Exception:
        stack = []
    # search from weakest to strongest
    for spec in reversed(list(stack)):
        lid = getattr(spec.layer, "identifier", "")
        if str(lid).startswith("anon:"):
            continue
        real = getattr(spec.layer, "realPath", None) or lid
        if real:
            return os.path.dirname(real)
    return None


def _sanitize_name(name: str) -> str:
    s = name.strip().replace(" ", "_")
    bad = "<>:\\/|?*\"'`"
    for ch in bad:
        s = s.replace(ch, "_")
    return s or "Material"


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def export_from_stage(
    stage: Usd.Stage,
    out_dir_name: str = "mdl_materials",
    ascii_usd: bool = True,
    placement: str = "authoring",  # 'authoring' | 'root'
    include_external: bool = True,
    export_mode: str = "mdl",  # 'mdl' | 'preview'
    emit_ball: bool = False,
    assets_path_mode: str = "relative",  # 'relative' | 'absolute'
) -> List[Tuple[str, str]]:
    """Export MDL materials found in the current root layer to individual USD files.

    Returns list of (materialPath, exportedFilePath).
    """
    results: List[Tuple[str, str]] = []
    root_dir = os.path.dirname(stage.GetRootLayer().realPath or stage.GetRootLayer().identifier)

    for prim in stage.Traverse():
        if prim.GetTypeName() != "Material":
            continue
        if (not include_external) and (not _is_in_root_layer(stage, prim)):
            continue
        mat = UsdShade.Material(prim)
        mdl = find_mdl_shader(mat)
        if not mdl:
            continue

        # New stage for exported material
        mat_name = _sanitize_name(prim.GetName())
        looks_path = "/Looks"
        # decide base directory per material
        if placement == "authoring":
            base_dir = _authoring_layer_dir_for_prim(prim) or root_dir
        else:
            base_dir = root_dir
        out_dir = os.path.join(base_dir, out_dir_name)
        _ensure_dir(out_dir)
        export_path = os.path.join(out_dir, f"{mat_name}.usda" if ascii_usd else f"{mat_name}.usd")

        new_stage = Usd.Stage.CreateNew(export_path)
        new_stage.SetDefaultPrim(new_stage.DefinePrim("/Root", "Scope"))
        new_stage.DefinePrim(looks_path, "Scope")
        new_mat = UsdShade.Material.Define(new_stage, f"{looks_path}/{mat_name}")

        if export_mode == "preview":
            # Build preview network and wire textures using original MDL shader as source of truth
            ensure_preview(new_stage, new_mat)
            filled, has_c, c_rgb, bc_tex = copy_textures(new_stage, mdl, new_mat)
            connect_preview(new_stage, new_mat, filled, has_c, c_rgb, bc_tex)
        else:
            # MDL-preserving export: duplicate minimal MDL shader metadata and inputs
            _export_mdl_material(new_stage, new_mat, mdl, assets_path_mode=assets_path_mode)

        # Save material file
        new_stage.GetRootLayer().Save()
        results.append((prim.GetPath().pathString, export_path))

        # Optionally create a small preview scene with a bound sphere
        if emit_ball:
            ball_path = os.path.join(out_dir, f"{mat_name}_ball.usda" if ascii_usd else f"{mat_name}_ball.usd")
            ball_stage = Usd.Stage.CreateNew(ball_path)
            world = ball_stage.DefinePrim("/World", "Xform")
            ball_stage.SetDefaultPrim(world)
            # Reference the material file under /Looks
            looks_prim = ball_stage.DefinePrim("/Looks", "Scope")
            # Create a target prim for the material and add a reference to the exported material prim path
            mat_target = ball_stage.DefinePrim(f"/Looks/{mat_name}", "Material")
            mat_ref = Sdf.Reference(assetPath=os.path.relpath(export_path, os.path.dirname(ball_path)).replace("\\", "/"), primPath=f"/Looks/{mat_name}")
            mat_target.GetReferences().AddReference(mat_ref)

            # Create a sphere and bind material
            sphere = UsdGeom.Sphere.Define(ball_stage, "/World/Sphere")
            # Give it a reasonable radius
            sphere.CreateRadiusAttr(50.0)
            UsdShade.MaterialBindingAPI.Apply(sphere.GetPrim()).Bind(UsdShade.Material(mat_target))
            ball_stage.GetRootLayer().Save()

    return results


__all__ = ["export_from_stage"]


def _export_mdl_material(new_stage: Usd.Stage, new_mat: UsdShade.Material, mdl_shader_src: UsdShade.Shader, assets_path_mode: str = "relative"):
    """Create a minimal MDL material on new_stage, preserving info:mdl:* metadata and inputs.

    Structure:
      /Looks/<MatName>
        outputs:surface:mdl -> /Looks/<MatName>/mdlShader.outputs:surface
        def Shader "mdlShader"
          - copy info:id if present
          - copy info:mdl:* attributes
          - recreate outputs:surface token
          - copy inputs (value attributes) without attempting to clone connected subgraphs
    """
    parent = new_mat.GetPath().pathString
    shader_path = f"{parent}/mdlShader"
    mdl_new = UsdShade.Shader.Define(new_stage, shader_path)

    # copy info:id
    src_prim = mdl_shader_src.GetPrim()
    id_attr = src_prim.GetAttribute("info:id")
    if id_attr and id_attr.HasAuthoredValue():
        mdl_new.CreateIdAttr(id_attr.Get())
    else:
        mdl_new.CreateIdAttr("mdlMaterial")

    # copy info:mdl:* attributes and some common impl source hints
    new_dir = os.path.dirname(new_stage.GetRootLayer().realPath or new_stage.GetRootLayer().identifier)
    for name in src_prim.GetPropertyNames():
        if name.startswith("info:mdl:") or name in ("info:implementationSource", "info:sourceAsset"):
            a_src = src_prim.GetAttribute(name)
            if not a_src:
                continue
            if a_src.HasAuthoredValue():
                v = a_src.Get()
                # Special handling for asset-valued attributes: rewrite path relative to the new file directory
                if isinstance(v, Sdf.AssetPath):
                    anchor_dir = _anchor_dir_for_attr(a_src)
                    abs_path = _resolve_abs_path(anchor_dir, (v.resolvedPath or v.path)) if (v and (v.resolvedPath or v.path)) else None
                    if abs_path:
                        if assets_path_mode == "absolute":
                            v = Sdf.AssetPath(abs_path)
                        else:
                            rel = os.path.relpath(abs_path, new_dir).replace("\\", "/")
                            v = Sdf.AssetPath(rel)
                a_dst = mdl_new.GetPrim().CreateAttribute(name, a_src.GetTypeName())
                a_dst.Set(v)

    # outputs:surface
    mdl_new.CreateOutput("surface", Sdf.ValueTypeNames.Token)

    # copy value inputs (rewrite asset paths relative to new file)
    new_dir = os.path.dirname(new_stage.GetRootLayer().realPath or new_stage.GetRootLayer().identifier)
    # fallback anchor from mdl source asset
    mdl_sa_attr = src_prim.GetAttribute("info:mdl:sourceAsset")
    mdl_anchor_dir = _anchor_dir_for_attr(mdl_sa_attr) if mdl_sa_attr else None
    for inp in mdl_shader_src.GetInputs():
        i_dst = mdl_new.CreateInput(inp.GetBaseName(), inp.GetTypeName())
        try:
            val = inp.Get()
            if isinstance(val, Sdf.AssetPath):
                # find anchor dir for this input attribute on the source prim
                attr = src_prim.GetAttribute(f"inputs:{inp.GetBaseName()}")
                anchor_dir = _anchor_dir_for_attr(attr) if attr else None
                if not anchor_dir:
                    anchor_dir = mdl_anchor_dir
                abs_path = _resolve_abs_path(anchor_dir, (val.resolvedPath or val.path)) if (val and (val.resolvedPath or val.path)) else None
                if abs_path:
                    if assets_path_mode == "absolute":
                        i_dst.Set(Sdf.AssetPath(abs_path))
                    else:
                        rel = os.path.relpath(abs_path, new_dir).replace("\\", "/")
                        i_dst.Set(Sdf.AssetPath(rel))
                else:
                    i_dst.Set(val)
            else:
                # For non-asset values, set directly if authored
                if val is not None:
                    i_dst.Set(val)
        except Exception:
            pass

    # connect material outputs:surface:mdl
    out_mdl = new_mat.GetSurfaceOutput("mdl") or new_mat.CreateSurfaceOutput("mdl")
    out_mdl.ConnectToSource(mdl_new.GetOutput("surface"))
