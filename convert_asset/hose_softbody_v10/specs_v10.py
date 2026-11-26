"""Continuum-to-discrete physics compiler for latex cooling hoses (Route A D6-DER & Route B GPU FEM)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any

import numpy as np


@dataclass(frozen=True)
class CondenserBarbGeometryV10:
    """Exact 1:1 geometry of the Liebig condenser serrated glass water barbs (blender_distillation_v06_kit)."""

    inlet_origin_local: tuple[float, float, float] = (+0.074, 0.0, -0.014)
    outlet_origin_local: tuple[float, float, float] = (-0.074, 0.0, -0.014)
    axis_local: tuple[float, float, float] = (0.0, -0.469472, -0.882948)
    length_m: float = 0.038
    stem_radius_m: float = 0.0044
    olive_radius_m: float = 0.0056
    olive_stations_m: tuple[float, float, float] = (0.010, 0.019, 0.028)
    olive_half_width_m: float = 0.0036
    seat_start_s_m: float = 0.005
    seat_end_s_m: float = 0.036

    def origin_local(self, side: str) -> np.ndarray:
        if side == "inlet":
            return np.asarray(self.inlet_origin_local, dtype=np.float64)
        if side == "outlet":
            return np.asarray(self.outlet_origin_local, dtype=np.float64)
        raise ValueError(f"Unknown barb side: {side!r}")

    def unit_axis_local(self) -> np.ndarray:
        v = np.asarray(self.axis_local, dtype=np.float64)
        return v / max(float(np.linalg.norm(v)), 1e-12)

    def radius_at_s(self, s_m: float) -> float:
        """Smooth glass barb outer radius profile along local barb arc-length s in [0, length_m]."""
        s = float(s_m)
        if s < -0.002 or s > self.length_m + 0.002:
            return 0.0
        r = self.stem_radius_m
        hw = self.olive_half_width_m
        dr = self.olive_radius_m - self.stem_radius_m
        for sc in self.olive_stations_m:
            d = abs(s - sc)
            if d < hw:
                bump = 0.5 * (1.0 + math.cos(math.pi * d / hw))
                r = max(r, self.stem_radius_m + dr * bump)
        # Slight chamfer at very tip (s > 34 mm)
        if s > self.length_m - 0.004:
            u = min(1.0, (s - (self.length_m - 0.004)) / 0.004)
            r = r * (1.0 - 0.25 * u)
        return float(r)

    def world_origin_and_axis(
        self,
        cond_pos_w: np.ndarray,
        cond_rot_w: np.ndarray,
        side: str,
    ) -> tuple[np.ndarray, np.ndarray]:
        p0 = np.asarray(cond_pos_w, dtype=np.float64) + np.asarray(cond_rot_w, dtype=np.float64) @ self.origin_local(side)
        ax = np.asarray(cond_rot_w, dtype=np.float64) @ self.unit_axis_local()
        ax = ax / max(float(np.linalg.norm(ax)), 1e-12)
        return p0, ax


DEFAULT_CONDENSER_BARB_V10 = CondenserBarbGeometryV10()


@dataclass(frozen=True)
class HoseMaterialSpecV10:
    """Physical properties of laboratory natural amber-latex cooling tubing."""

    asset_id: str = "amber_latex_cooling_hose_6x9mm"
    outer_radius_m: float = 0.0048
    inner_radius_m: float = 0.0031
    outer_radius_body_m: float | None = None
    density_kg_m3: float = 960.0
    youngs_modulus_pa: float = 1.65e6
    poissons_ratio: float = 0.44
    static_friction: float = 1.35
    dynamic_friction: float = 1.15
    rayleigh_beta_s: float = 0.035

    @property
    def effective_body_outer_radius_m(self) -> float:
        return float(self.outer_radius_body_m) if self.outer_radius_body_m is not None else float(self.outer_radius_m)

    @property
    def cross_section_area_m2(self) -> float:
        r_o = self.effective_body_outer_radius_m
        return math.pi * (r_o**2 - self.inner_radius_m**2)

    @property
    def area_moment_I_m4(self) -> float:
        r_o = self.effective_body_outer_radius_m
        return 0.25 * math.pi * (r_o**4 - self.inner_radius_m**4)

    @property
    def polar_moment_J_m4(self) -> float:
        return 2.0 * self.area_moment_I_m4

    @property
    def shear_modulus_pa(self) -> float:
        return self.youngs_modulus_pa / (2.0 * (1.0 + self.poissons_ratio))

    @property
    def mass_per_length_kg_m(self) -> float:
        return self.density_kg_m3 * self.cross_section_area_m2

    @property
    def EI_nm2(self) -> float:
        return self.youngs_modulus_pa * self.area_moment_I_m4

    @property
    def GJ_nm2(self) -> float:
        return self.shear_modulus_pa * self.polar_moment_J_m4


# v10.1 calibrated surgical amber-latex tubing matched to r_olive = 5.6 mm glass barbs (~27.3% interference strain):
# - Cuff: r_in = 4.4 mm, r_out = 6.8 mm (2.4 mm wall, zero olive poke-through)
# - Mid-span body: r_in = 4.4 mm, r_out = 6.2 mm (1.8 mm flexible wall, low bending torque on J02)
# - Youngs modulus: 0.55 MPa (authentic natural surgical latex 0.45-0.65 MPa)
SURGICAL_LATEX_V10_1_SPEC = HoseMaterialSpecV10(
    asset_id="amber_latex_cooling_hose_8p8x13p6mm_graded_v10_1",
    outer_radius_m=0.0068,
    inner_radius_m=0.0044,
    outer_radius_body_m=0.0062,
    density_kg_m3=960.0,
    youngs_modulus_pa=0.45e6,
    poissons_ratio=0.38,
    static_friction=1.35,
    dynamic_friction=1.15,
    rayleigh_beta_s=0.035,
)


@dataclass(frozen=True)
class BarbCuffMicroSpringSpec:
    """Method-B radial micro-spring silicone liner inside Route A hose cuff for barb interference lock."""

    n_pads: int = 4
    pad_radius_m: float = 0.0022
    cuff_rest_inner_radius_m: float = 0.0044
    barb_bead_outer_radius_m: float = 0.0056
    spring_stiffness_n_m: float = 1350.0
    spring_damping_ns_m: float = 20.0
    max_radial_force_n: float = 11.0
    liner_static_friction: float = 1.45
    liner_dynamic_friction: float = 1.25


@dataclass(frozen=True)
class D6DerRodSpec:
    """Compiled discrete elastic rod parameters for PhysX UsdPhysics.D6Joint angular drives."""

    n_links: int
    total_length_m: float
    segment_length_m: float
    link_mass_kg: float
    bend_stiffness_nm_per_rad: float
    bend_damping_nms_per_rad: float
    twist_stiffness_nm_per_rad: float
    twist_damping_nms_per_rad: float
    linear_damping: float
    angular_damping: float
    capsule_radius_m: float
    cuff_spec: BarbCuffMicroSpringSpec

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compile_d6_der_rod_spec(
    mat: HoseMaterialSpecV10,
    *,
    total_length_m: float,
    n_links: int = 24,
    bend_scale: float = 1.0,
    twist_scale: float = 1.0,
) -> D6DerRodSpec:
    """Compile continuum (E, nu, OD, ID) into discrete PhysX D6Joint bending/twisting drives."""
    if n_links < 4:
        raise ValueError(f"n_links must be >= 4, got {n_links}")
    ds = float(total_length_m) / float(n_links)
    k_bend = max(1e-4, (mat.EI_nm2 / ds) * float(bend_scale))
    k_twist = max(1e-4, (mat.GJ_nm2 / ds) * float(twist_scale))
    c_bend = max(1e-5, mat.rayleigh_beta_s * k_bend)
    c_twist = max(1e-5, mat.rayleigh_beta_s * k_twist)
    m_link = max(0.0012, mat.mass_per_length_kg_m * ds)
    return D6DerRodSpec(
        n_links=int(n_links),
        total_length_m=float(total_length_m),
        segment_length_m=ds,
        link_mass_kg=m_link,
        bend_stiffness_nm_per_rad=k_bend,
        bend_damping_nms_per_rad=c_bend,
        twist_stiffness_nm_per_rad=k_twist,
        twist_damping_nms_per_rad=c_twist,
        linear_damping=1.8,
        angular_damping=2.2,
        capsule_radius_m=float(mat.effective_body_outer_radius_m),
        cuff_spec=BarbCuffMicroSpringSpec(),
    )
