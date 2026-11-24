"""Shell-driven 3D Gaussian appearance binding (gs_binding.npz) & anisotropic splat renderer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from .bicubic_hermite_shell import HermiteShellMesh


def bind_gaussians_to_hermite_shell(
    mesh: HermiteShellMesh,
    *,
    out_npz_path: str | Path,
    base_rgb: tuple[float, float, float] = (0.24, 0.56, 0.78),
    pattern: str = "woven_grid",
    gs_nu: int = 28,
    gs_nv: int = 28,
) -> Path:
    """Bind dense anisotropic 3D Gaussians to the C1 Hermite shell tangent surface & save gs_binding.npz.

    Compatible with embodied-eval-os `GaussianTwinRendererAdapter` (rest_centers, anchor_nodes,
    scales, colors, opacities) while also carrying Hermite surface coordinates (sample_uv, W).
    """
    out_p = Path(out_npz_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    u = np.linspace(0.0, mesh.length_u_m, gs_nu)
    v = np.linspace(0.0, mesh.length_v_m, gs_nv)
    uu, vv = np.meshgrid(u, v, indexing="ij")
    uv = np.column_stack([uu.ravel(), vv.ravel()])
    W_gs = mesh.build_sample_matrix(uv)
    rest_centers = W_gs @ mesh.rest_q  # (G, 3)

    # Anchor indices over physical position DOFs for EOS GaussianTwinRendererAdapter compatibility
    n_g = len(rest_centers)
    # Build pseudo-anchors mapping each Gaussian to nearest coarse nodes
    node_pos = mesh.rest_q[0::4]
    dists = np.linalg.norm(rest_centers[:, None, :] - node_pos[None, :, :], axis=-1)
    nearest2 = np.argsort(dists, axis=1)[:, :2].astype(np.int32)

    du_g = mesh.length_u_m / max(gs_nu - 1, 1)
    dv_g = mesh.length_v_m / max(gs_nv - 1, 1)
    scales = np.tile(np.array([0.65 * du_g, 0.65 * dv_g, 0.0025], dtype=np.float64), (n_g, 1))

    # Rich procedural fabric/foam appearance colors
    r0, g0, b0 = base_rgb
    colors = np.tile(np.array([r0, g0, b0], dtype=np.float64), (n_g, 1))
    ui = (uv[:, 0] / max(mesh.length_u_m, 1e-6))
    vi = (uv[:, 1] / max(mesh.length_v_m, 1e-6))
    if pattern == "woven_grid":
        stripe = 0.08 * np.sin(24.0 * np.pi * ui) + 0.08 * np.sin(24.0 * np.pi * vi)
        border = ((ui < 0.08) | (ui > 0.92) | (vi < 0.08) | (vi > 0.92)).astype(np.float64)
        colors[:, 0] = np.clip(colors[:, 0] + stripe + 0.14 * border, 0.05, 0.95)
        colors[:, 1] = np.clip(colors[:, 1] + 0.6 * stripe + 0.05 * border, 0.05, 0.95)
        colors[:, 2] = np.clip(colors[:, 2] + 0.3 * stripe - 0.06 * border, 0.05, 0.95)
    elif pattern == "foam_speckle":
        rng = np.random.default_rng(7)
        colors = np.clip(colors + rng.normal(0.0, 0.035, size=colors.shape), 0.05, 0.95)

    opacities = np.full(n_g, 0.92, dtype=np.float64)
    np.savez_compressed(
        out_p,
        rest_centers=rest_centers,
        anchor_nodes=nearest2,
        scales=scales,
        colors=colors,
        opacities=opacities,
        sample_uv=uv,
        W_gs=W_gs,
    )
    return out_p


def render_hermite_3dgs_frame(
    gs_binding_path: str | Path,
    q_nodes: np.ndarray,
    *,
    image_hw: tuple[int, int] = (360, 480),
    camera_pos_xyz: tuple[float, float, float] = (0.0, -0.56, 1.06),
    look_at_xyz: tuple[float, float, float] = (0.0, 0.0, 0.78),
    fov_deg: float = 42.0,
    bg_rgb: tuple[float, float, float] = (0.09, 0.11, 0.14),
) -> dict[str, Any]:
    """Render anisotropic 3D Gaussians driven by C1 Hermite shell nodes into an RGB image."""
    with np.load(gs_binding_path, allow_pickle=False) as z:
        W_gs = np.asarray(z["W_gs"], dtype=np.float64)
        scales = np.asarray(z["scales"], dtype=np.float64)
        colors = np.asarray(z["colors"], dtype=np.float64)
        opacities = np.asarray(z["opacities"], dtype=np.float64)

    centers = W_gs @ np.asarray(q_nodes, dtype=np.float64)
    h, w = int(image_hw[0]), int(image_hw[1])
    focal = 0.5 * h / np.tan(0.5 * np.deg2rad(fov_deg))

    cam = np.asarray(camera_pos_xyz, dtype=np.float64)
    tgt = np.asarray(look_at_xyz, dtype=np.float64)
    fwd = tgt - cam
    fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, np.array([0.0, 0.0, 1.0], dtype=np.float64))
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)

    rel = centers - cam[None, :]
    cx_cam = rel @ right
    cy_cam = rel @ up
    cz_cam = rel @ fwd
    valid = cz_cam > 0.05

    u_px = 0.5 * w + focal * (cx_cam[valid] / cz_cam[valid])
    v_px = 0.5 * h - focal * (cy_cam[valid] / cz_cam[valid])
    r_px = np.clip(focal * (scales[valid, 0] * 1.45 / cz_cam[valid]), 1.8, 12.0)
    depths = cz_cam[valid]
    c_val = colors[valid]
    o_val = opacities[valid]

    # Simple directional shading modulation by center height for splat appearance
    shade = np.clip(0.76 + 0.28 * ((centers[valid, 2] - 0.75) / 0.15), 0.65, 1.15)[:, None]
    c_shaded = np.clip(c_val * shade, 0.0, 1.0)

    order = np.argsort(depths)
    img = np.zeros((h, w, 3), dtype=np.float64)
    alpha_acc = np.zeros((h, w), dtype=np.float64)

    for idx in order:
        px = float(u_px[idx])
        py = float(v_px[idx])
        rad = float(r_px[idx])
        x0 = max(0, int(np.floor(px - 2.4 * rad)))
        x1 = min(w, int(np.ceil(px + 2.4 * rad)) + 1)
        y0 = max(0, int(np.floor(py - 2.4 * rad)))
        y1 = min(h, int(np.ceil(py + 2.4 * rad)) + 1)
        if x1 <= x0 or y1 <= y0:
            continue
        yy, xx = np.mgrid[y0:y1, x0:x1]
        dist2 = (xx - px) ** 2 + (yy - py) ** 2
        g_a = o_val[idx] * np.exp(-0.5 * dist2 / max(rad * rad, 0.8))
        trans = 1.0 - alpha_acc[y0:y1, x0:x1]
        contrib = trans * g_a
        img[y0:y1, x0:x1] += contrib[:, :, None] * c_shaded[idx][None, None, :]
        alpha_acc[y0:y1, x0:x1] = np.clip(alpha_acc[y0:y1, x0:x1] + contrib, 0.0, 1.0)

    bg = np.asarray(bg_rgb, dtype=np.float64)[None, None, :]
    img = img + (1.0 - alpha_acc[:, :, None]) * bg
    return {
        "rgb": np.clip(img, 0.0, 1.0),
        "foreground_mask": alpha_acc > 0.10,
        "renderer_profile_id": "hermitetwin_3dgs_v08",
    }
