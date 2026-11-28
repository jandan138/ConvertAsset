"""Differentiable Anisotropic 3D Gaussian Splatting (EWA) driven by C1-Hermite Deformation Gradients on PyTorch CUDA.

Implements exact SIGA Phase 3 visual-physics coupling:
1. Evaluates 3D Gaussian centers mu_k(q) and exact C1 surface/wall deformation gradients F_k(q) = [a1, a2, n]
   for BOTH 1D Brazier-Cosserat hollow tubes and 2D Kirchhoff-Love thin shells in differentiable PyTorch.
2. Computes true anisotropic 3D covariances Sigma_3D = F_k @ diag(s1^2, s2^2, s3^2) @ F_k^T (zero tearing/streaking
   under extreme Brazier ovalization, torsion, or 180-deg shell folding!).
3. Performs exact 3D->2D EWA perspective projection Sigma_2D = J W Sigma_3D W^T J^T + 0.35 I_2 and
   front-to-back differentiable alpha compositing on RTX 4090 CUDA, yielding exact dL_img / dq via autograd.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

import numpy as np
import torch

from convert_asset.deformable_v08_hermite.bicubic_hermite_shell import HermiteShellMesh, _local_bf_element_matrices

from .state_and_basis import DOFS_PER_ROD_NODE, HermiteRodMesh, hermite_1d_basis


@dataclass(frozen=True)
class CameraSpec:
    """Pinhole perspective camera specification for differentiable 3DGS rendering."""

    height: int = 128
    width: int = 160
    eye_xyz: tuple[float, float, float] = (0.10, -0.34, 0.08)
    target_xyz: tuple[float, float, float] = (0.10, 0.0, -0.02)
    up_xyz: tuple[float, float, float] = (0.0, 0.0, 1.0)
    fov_y_deg: float = 38.0
    bg_rgb: tuple[float, float, float] = (0.06, 0.09, 0.15)


def _camera_matrices_torch(cam: CameraSpec, *, device: torch.device, dtype: torch.dtype) -> tuple[torch.Tensor, torch.Tensor, float, float, float, float]:
    """Build world-to-camera rotation R_wc (3,3) and eye position (3,) + pinhole intrinsics."""
    eye = torch.tensor(cam.eye_xyz, device=device, dtype=dtype)
    tgt = torch.tensor(cam.target_xyz, device=device, dtype=dtype)
    up_ref = torch.tensor(cam.up_xyz, device=device, dtype=dtype)

    fwd = tgt - eye
    fwd = fwd / torch.clamp(torch.linalg.norm(fwd), min=1e-12)
    right = torch.cross(fwd, up_ref, dim=0)
    right = right / torch.clamp(torch.linalg.norm(right), min=1e-12)
    # Image +y points DOWN, so camera y-axis = -up
    up = torch.cross(right, fwd, dim=0)
    cam_y = -up

    R_wc = torch.stack([right, cam_y, fwd], dim=0)  # rows are camera (x_right, y_down, z_fwd)
    fy = 0.5 * float(cam.height) / math.tan(0.5 * math.radians(float(cam.fov_y_deg)))
    fx = fy
    cx = 0.5 * float(cam.width)
    cy = 0.5 * float(cam.height)
    return R_wc, eye, fx, fy, cx, cy


def render_anisotropic_3dgs_torch(
    means_3d: torch.Tensor,  # (G, 3)
    cov_3d: torch.Tensor,  # (G, 3, 3) symmetric PSD
    colors: torch.Tensor,  # (G, 3) in [0, 1]
    opacities: torch.Tensor,  # (G,) in [0, 1]
    cam: CameraSpec,
    *,
    chunk_size: int = 128,
) -> dict[str, torch.Tensor]:
    """Differentiable EWA anisotropic 3D Gaussian Splatting on PyTorch CUDA (exact front-to-back compositing)."""
    device = means_3d.device
    dtype = means_3d.dtype
    H, W = int(cam.height), int(cam.width)

    R_wc, eye, fx, fy, cx, cy = _camera_matrices_torch(cam, device=device, dtype=dtype)
    p_cam = (means_3d - eye[None, :]) @ R_wc.T  # (G, 3)
    z = torch.clamp(p_cam[:, 2], min=0.05)
    inv_z = 1.0 / z
    inv_z2 = inv_z * inv_z

    # Project 3D centers to pixel space
    u_px = fx * (p_cam[:, 0] * inv_z) + cx
    v_px = fy * (p_cam[:, 1] * inv_z) + cy
    mu_2d = torch.stack([u_px, v_px], dim=-1)  # (G, 2)

    # Exact local affine perspective Jacobian J (G, 2, 3)
    G = means_3d.shape[0]
    zeros = torch.zeros(G, device=device, dtype=dtype)
    J = torch.stack(
        [
            torch.stack([fx * inv_z, zeros, -fx * p_cam[:, 0] * inv_z2], dim=-1),
            torch.stack([zeros, fy * inv_z, -fy * p_cam[:, 1] * inv_z2], dim=-1),
        ],
        dim=1,
    )  # (G, 2, 3)

    # EWA 2D covariance: Sigma_2D = J @ R_wc @ Sigma_3D @ R_wc^T @ J^T + 0.35 * I_2
    JW = torch.matmul(J, R_wc.unsqueeze(0))  # (G, 2, 3)
    cov_2d = torch.matmul(torch.matmul(JW, cov_3d), JW.transpose(1, 2))  # (G, 2, 2)
    reg_eye = 0.35 * torch.eye(2, device=device, dtype=dtype).unsqueeze(0)
    cov_2d = cov_2d + reg_eye

    # Sort Gaussians front-to-back by camera depth z
    order = torch.argsort(z, descending=False)
    mu_s = mu_2d[order]
    cov_s = cov_2d[order]
    col_s = colors[order]
    opa_s = opacities[order]

    # Analytical inverse of 2x2 symmetric SPD covariance matrices
    a = cov_s[:, 0, 0]
    b = cov_s[:, 0, 1]
    c = cov_s[:, 1, 1]
    det = torch.clamp(a * c - b * b, min=1e-6)
    inv_a = c / det
    inv_b = -b / det
    inv_c = a / det

    # Pixel grid (H, W)
    ys = torch.arange(H, device=device, dtype=dtype) + 0.5
    xs = torch.arange(W, device=device, dtype=dtype) + 0.5
    grid_y, grid_x = torch.meshgrid(ys, xs, indexing="ij")  # (H, W)

    # Chunked exact front-to-back alpha compositing (keeps VRAM tiny even at high resolution!)
    rgb_acc = torch.zeros((H, W, 3), device=device, dtype=dtype)
    trans_acc = torch.ones((H, W), device=device, dtype=dtype)

    for start in range(0, G, chunk_size):
        end = min(G, start + chunk_size)
        dx = grid_x.unsqueeze(0) - mu_s[start:end, 0].view(-1, 1, 1)  # (C, H, W)
        dy = grid_y.unsqueeze(0) - mu_s[start:end, 1].view(-1, 1, 1)
        maha = (
            inv_a[start:end].view(-1, 1, 1) * (dx * dx)
            + 2.0 * inv_b[start:end].view(-1, 1, 1) * (dx * dy)
            + inv_c[start:end].view(-1, 1, 1) * (dy * dy)
        )
        alpha = torch.clamp(opa_s[start:end].view(-1, 1, 1) * torch.exp(-0.5 * torch.clamp(maha, max=30.0)), max=0.99)

        # Exclusive prefix product inside chunk: T_local[k] = prod_{j < k} (1 - alpha[j])
        one_minus = torch.clamp(1.0 - alpha, min=1e-4)
        ones_top = torch.ones((1, H, W), device=device, dtype=dtype)
        t_local = torch.cumprod(torch.cat([ones_top, one_minus[:-1]], dim=0), dim=0)
        weights = trans_acc.unsqueeze(0) * t_local * alpha  # (C, H, W)

        rgb_acc = rgb_acc + torch.einsum("chw,cd->hwd", weights, col_s[start:end])
        trans_acc = trans_acc * torch.prod(one_minus, dim=0)

    bg = torch.tensor(cam.bg_rgb, device=device, dtype=dtype).view(1, 1, 3)
    rgb = rgb_acc + trans_acc.unsqueeze(-1) * bg
    silhouette = 1.0 - trans_acc
    return {
        "rgb": torch.clamp(rgb, 0.0, 1.0),
        "silhouette": torch.clamp(silhouette, 0.0, 1.0),
    }


def _parallel_transport_torch(d1_prev: torch.Tensor, t_prev: torch.Tensor, t_curr: torch.Tensor) -> torch.Tensor:
    """Differentiable Rodrigues minimal-twist parallel transport in PyTorch."""
    v = torch.cross(t_prev, t_curr, dim=0)
    c = torch.clamp(torch.dot(t_prev, t_curr), min=-1.0 + 1e-7, max=1.0 - 1e-7)
    s2 = torch.dot(v, v)
    s = torch.sqrt(s2 + 1e-14)
    k = v / s
    # Use smooth Rodrigues formula valid down to s -> 0: cos(ang)=c, sin(ang)=s
    d1_rot = d1_prev * c + torch.cross(k, d1_prev, dim=0) * s + k * (torch.dot(k, d1_prev) * (1.0 - c))
    d1_rot = d1_rot - torch.dot(d1_rot, t_curr) * t_curr
    return d1_rot / torch.clamp(torch.linalg.norm(d1_rot), min=1e-12)


class HermiteRodGaussianRenderer:
    """Differentiable C1-frame anisotropic 3DGS renderer anchored directly to a 1D Brazier-Cosserat rod."""

    def __init__(
        self,
        mesh: HermiteRodMesh,
        *,
        samples_per_elem: int = 3,
        n_phi: int = 12,
        base_rgb: tuple[float, float, float] = (0.86, 0.56, 0.16),
        stripe_rgb: tuple[float, float, float] = (0.18, 0.08, 0.02),
        device: str = "cuda:0",
        dtype: torch.dtype = torch.float64,
    ) -> None:
        self.mesh = mesh
        self.samples_per_elem = int(samples_per_elem)
        self.n_phi = int(n_phi)
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        self.dtype = dtype

        xis = np.linspace(0.15, 0.85, self.samples_per_elem)
        hv, hd1, _ = hermite_1d_basis(xis)
        self._xis = torch.tensor(xis, device=self.device, dtype=dtype)
        self._hv = torch.tensor(hv, device=self.device, dtype=dtype)
        self._hd1 = torch.tensor(hd1, device=self.device, dtype=dtype)
        self._ref_d1_0 = torch.tensor(mesh.ref_d1_0, device=self.device, dtype=dtype)

        phis = np.linspace(0.0, 2.0 * math.pi, self.n_phi, endpoint=False)
        self._c_phi = torch.tensor(np.cos(phis), device=self.device, dtype=dtype)
        self._s_phi = torch.tensor(np.sin(phis), device=self.device, dtype=dtype)
        self._c2_phi = torch.tensor(np.cos(2.0 * phis), device=self.device, dtype=dtype)
        self._s2_phi = torch.tensor(np.sin(2.0 * phis), device=self.device, dtype=dtype)

        # Anisotropic rest ellipsoid scales aligned with (axial a_s, circumferential a_phi, outward normal n)
        ds_g = mesh.ds / float(self.samples_per_elem)
        dphi_g = 2.0 * math.pi * mesh.spec.r_out_m / float(self.n_phi)
        self._rest_scales = torch.tensor([0.62 * ds_g, 0.65 * dphi_g, 0.25 * mesh.spec.wall_thickness_m], device=self.device, dtype=dtype)

        # Amber latex color + 2 longitudinal dark Cosserat torsion stripes (phi index 0 and n_phi//2)
        n_s = mesh.n_elems * self.samples_per_elem
        cols = np.tile(np.array(base_rgb, dtype=np.float64), (n_s, self.n_phi, 1))
        cols[:, 0, :] = np.array(stripe_rgb, dtype=np.float64)
        cols[:, self.n_phi // 2, :] = np.array(stripe_rgb, dtype=np.float64)
        self._base_colors = torch.tensor(cols.reshape(-1, 3), device=self.device, dtype=dtype)
        self._opacities = torch.full((n_s * self.n_phi,), 0.94, device=self.device, dtype=dtype)

    def build_gaussians(self, q_rod: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Map C1 rod state q_rod (n_dofs,) -> differentiable (means_3d, cov_3d, shaded_colors, opacities)."""
        qa = q_rod.view(self.mesh.n_nodes, DOFS_PER_ROD_NODE)
        ds = float(self.mesh.ds)
        r_out = float(self.mesh.spec.r_out_m)

        t0 = qa[0, 3:6]
        t_prev = t0 / torch.clamp(torch.linalg.norm(t0), min=1e-12)
        d1_prev = self._ref_d1_0 - torch.dot(self._ref_d1_0, t_prev) * t_prev
        d1_prev = d1_prev / torch.clamp(torch.linalg.norm(d1_prev), min=1e-12)

        means_list = []
        cov_list = []
        nrm_list = []
        s1_sq, s2_sq, s3_sq = self._rest_scales[0] ** 2, self._rest_scales[1] ** 2, self._rest_scales[2] ** 2

        for e in range(self.mesh.n_elems):
            q0, q1 = qa[e], qa[e + 1]
            for k in range(self.samples_per_elem):
                xi = self._xis[k]
                hv = self._hv[k]
                hd1 = self._hd1[k]

                x_s = hv[0] * q0[0:3] + (ds * hv[1]) * q0[3:6] + hv[2] * q1[0:3] + (ds * hv[3]) * q1[3:6]
                dx_ds = (hd1[0] / ds) * q0[0:3] + hd1[1] * q0[3:6] + (hd1[2] / ds) * q1[0:3] + hd1[3] * q1[3:6]
                norm_t = torch.clamp(torch.linalg.norm(dx_ds), min=1e-12)
                t_hat = dx_ds / norm_t

                d1_b = _parallel_transport_torch(d1_prev, t_prev, t_hat)
                d2_b = torch.cross(t_hat, d1_b, dim=0)
                t_prev, d1_prev = t_hat, d1_b

                theta = (1.0 - xi) * q0[6] + xi * q1[6]
                a0 = (1.0 - xi) * q0[7] + xi * q1[7]
                a2 = (1.0 - xi) * q0[8] + xi * q1[8]
                b2 = (1.0 - xi) * q0[9] + xi * q1[9]

                ct, st = torch.cos(theta), torch.sin(theta)
                d1_m = ct * d1_b + st * d2_b
                d2_m = -st * d1_b + ct * d2_b

                # Ring basis vectors (n_phi, 3)
                e_r = self._c_phi[:, None] * d1_m[None, :] + self._s_phi[:, None] * d2_m[None, :]
                e_phi = -self._s_phi[:, None] * d1_m[None, :] + self._c_phi[:, None] * d2_m[None, :]

                rad_scale = (1.0 + a0) + a2 * self._c2_phi + b2 * self._s2_phi
                tan_shift = -0.5 * a2 * self._s2_phi + 0.5 * b2 * self._c2_phi
                p_ring = x_s[None, :] + r_out * (rad_scale[:, None] * e_r + tan_shift[:, None] * e_phi)

                # Local C1 wall deformation gradient columns [a_s, a_phi, n_wall]:
                # Axial stretch scales a_s; radial expansion & Brazier flattening scale circumferential a_phi!
                dr_dphi = -2.0 * a2 * self._s2_phi + 2.0 * b2 * self._c2_phi
                dt_dphi = -a2 * self._c2_phi - b2 * self._s2_phi
                # Exact d(p_ring)/d(phi) / r_out = (dr_dphi - tan_shift)*e_r + (rad_scale + dt_dphi)*e_phi
                a_phi_vec = (dr_dphi - tan_shift)[:, None] * e_r + (rad_scale + dt_dphi)[:, None] * e_phi
                a_s_vec = dx_ds[None, :].expand(self.n_phi, 3)
                n_raw = torch.cross(a_s_vec, a_phi_vec, dim=-1)
                n_hat = n_raw / torch.clamp(torch.linalg.norm(n_raw, dim=-1, keepdim=True), min=1e-12)

                # Exact anisotropic 3D Gaussian covariance Sigma_3D = s1^2 a_s a_s^T + s2^2 a_phi a_phi^T + s3^2 n n^T
                cov_ring = (
                    s1_sq * (a_s_vec[:, :, None] * a_s_vec[:, None, :])
                    + s2_sq * (a_phi_vec[:, :, None] * a_phi_vec[:, None, :])
                    + s3_sq * (n_hat[:, :, None] * n_hat[:, None, :])
                )
                means_list.append(p_ring)
                cov_list.append(cov_ring)
                nrm_list.append(n_hat)

        means_3d = torch.cat(means_list, dim=0)
        cov_3d = torch.cat(cov_list, dim=0)
        nrms = torch.cat(nrm_list, dim=0)

        # Smooth directional studio shading (adds clean normal-coupled photometric gradient!)
        light_dir = torch.tensor([0.25, -0.60, 0.76], device=self.device, dtype=self.dtype)
        light_dir = light_dir / torch.linalg.norm(light_dir)
        ndotl = torch.clamp(torch.sum(nrms * light_dir[None, :], dim=-1), min=0.0)
        shade = (0.42 + 0.65 * ndotl).unsqueeze(-1)
        colors = torch.clamp(self._base_colors * shade, 0.0, 1.0)
        return means_3d, cov_3d, colors, self._opacities

    def render(self, q_rod: torch.Tensor, cam: CameraSpec) -> dict[str, torch.Tensor]:
        means_3d, cov_3d, colors, opacities = self.build_gaussians(q_rod)
        return render_anisotropic_3dgs_torch(means_3d, cov_3d, colors, opacities, cam)


class HermiteShellGaussianRenderer:
    """Differentiable C1-frame anisotropic 3DGS renderer anchored directly to a 2D Kirchhoff-Love thin shell."""

    def __init__(
        self,
        mesh: HermiteShellMesh,
        *,
        gs_nu: int = 16,
        gs_nv: int = 16,
        base_rgb: tuple[float, float, float] = (0.22, 0.58, 0.84),
        device: str = "cuda:0",
        dtype: torch.dtype = torch.float64,
    ) -> None:
        self.mesh = mesh
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        self.dtype = dtype

        u = np.linspace(0.0, mesh.length_u_m, gs_nu)
        v = np.linspace(0.0, mesh.length_v_m, gs_nv)
        uu, vv = np.meshgrid(u, v, indexing="ij")
        uv = np.column_stack([uu.ravel(), vv.ravel()])
        M = len(uv)

        W_pos = np.zeros((M, mesh.n_vec_dofs), dtype=np.float64)
        W_u = np.zeros((M, mesh.n_vec_dofs), dtype=np.float64)
        W_v = np.zeros((M, mesh.n_vec_dofs), dtype=np.float64)
        ix = np.minimum((uv[:, 0] / mesh.du).astype(np.int64), mesh.nx - 1)
        iy = np.minimum((uv[:, 1] / mesh.dv).astype(np.int64), mesh.ny - 1)
        xi = np.clip((uv[:, 0] - ix * mesh.du) / mesh.du, 0.0, 1.0)
        eta = np.clip((uv[:, 1] - iy * mesh.dv) / mesh.dv, 0.0, 1.0)
        for s in range(M):
            e = int(ix[s] * mesh.ny + iy[s])
            Ns, Nus, Nvs, _, _, _ = _local_bf_element_matrices(xi[s : s + 1], eta[s : s + 1], mesh.du, mesh.dv)
            dofs = mesh.elem_dof_indices[e]
            W_pos[s, dofs] = Ns[0]
            W_u[s, dofs] = Nus[0]
            W_v[s, dofs] = Nvs[0]

        self._W_pos = torch.tensor(W_pos, device=self.device, dtype=dtype)
        self._W_u = torch.tensor(W_u, device=self.device, dtype=dtype)
        self._W_v = torch.tensor(W_v, device=self.device, dtype=dtype)

        du_g = mesh.length_u_m / max(gs_nu - 1, 1)
        dv_g = mesh.length_v_m / max(gs_nv - 1, 1)
        self._rest_scales = torch.tensor([0.62 * du_g, 0.62 * dv_g, 0.0012], device=self.device, dtype=dtype)

        # Woven checker pattern so shell in-plane stretch and fold are crisp
        ui = uv[:, 0] / max(mesh.length_u_m, 1e-6)
        vi = uv[:, 1] / max(mesh.length_v_m, 1e-6)
        stripe = 0.10 * np.sin(16.0 * np.pi * ui) * np.sin(16.0 * np.pi * vi)
        cols = np.clip(np.array(base_rgb)[None, :] + stripe[:, None], 0.05, 0.96)
        self._base_colors = torch.tensor(cols, device=self.device, dtype=dtype)
        self._opacities = torch.full((M,), 0.92, device=self.device, dtype=dtype)

    def render(self, q_shell: torch.Tensor, cam: CameraSpec) -> dict[str, torch.Tensor]:
        qv = q_shell.view(self.mesh.n_vec_dofs, 3)
        means = self._W_pos @ qv  # (M, 3)
        a1 = self._W_u @ qv
        a2 = self._W_v @ qv
        n_raw = torch.cross(a1, a2, dim=-1)
        n_hat = n_raw / torch.clamp(torch.linalg.norm(n_raw, dim=-1, keepdim=True), min=1e-12)

        s1_sq, s2_sq, s3_sq = self._rest_scales[0] ** 2, self._rest_scales[1] ** 2, self._rest_scales[2] ** 2
        cov_3d = (
            s1_sq * (a1[:, :, None] * a1[:, None, :])
            + s2_sq * (a2[:, :, None] * a2[:, None, :])
            + s3_sq * (n_hat[:, :, None] * n_hat[:, None, :])
        )
        light_dir = torch.tensor([0.2, -0.5, 0.84], device=self.device, dtype=self.dtype)
        light_dir = light_dir / torch.linalg.norm(light_dir)
        ndotl = torch.clamp(torch.abs(torch.sum(n_hat * light_dir[None, :], dim=-1)), min=0.0)
        colors = torch.clamp(self._base_colors * (0.40 + 0.65 * ndotl).unsqueeze(-1), 0.0, 1.0)
        return render_anisotropic_3dgs_torch(means, cov_3d, colors, self._opacities, cam)

