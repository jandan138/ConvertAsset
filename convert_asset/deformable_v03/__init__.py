"""Dual-mesh barycentric, rigid-frame shell, and PBR asset pipeline for v0.3 deformable tasks."""

from .bundle_writer import build_v03_bundle, verify_bundle_mujoco4
from .glb_compiler import compile_glb_to_deformable_proxy
from .pbr_textures import derive_pbr_maps_from_albedo, load_or_generate_albedo
from .sculpted_assets import V03_ASSET_SPECS, build_sculpted_v03_asset
from .skinning import (
    build_shell_normal_skinning,
    build_tet_barycentric_skinning,
    deform_shell_skinned_points,
    deform_tet_skinned_points,
)

__all__ = [
    "V03_ASSET_SPECS",
    "build_sculpted_v03_asset",
    "build_shell_normal_skinning",
    "build_tet_barycentric_skinning",
    "build_v03_bundle",
    "compile_glb_to_deformable_proxy",
    "deform_shell_skinned_points",
    "deform_tet_skinned_points",
    "derive_pbr_maps_from_albedo",
    "load_or_generate_albedo",
    "verify_bundle_mujoco4",
]

