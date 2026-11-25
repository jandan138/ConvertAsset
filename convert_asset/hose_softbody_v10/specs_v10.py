"""Continuum-to-discrete physics compiler for latex cooling hoses (Route A D6-DER & Route B GPU FEM)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any


@dataclass(frozen=True)
class HoseMaterialSpecV10:
    """Physical properties of laboratory natural amber-latex cooling tubing (6x9 mm)."""

    asset_id: str = "amber_latex_cooling_hose_6x9mm"
    outer_radius_m: float = 0.0048
    inner_radius_m: float = 0.0031
    density_kg_m3: float = 960.0
    youngs_modulus_pa: float = 1.65e6
    poissons_ratio: float = 0.44
    static_friction: float = 1.35
    dynamic_friction: float = 1.15
    rayleigh_beta_s: float = 0.035

    @property
    def cross_section_area_m2(self) -> float:
        return math.pi * (self.outer_radius_m**2 - self.inner_radius_m**2)

    @property
    def area_moment_I_m4(self) -> float:
        return 0.25 * math.pi * (self.outer_radius_m**4 - self.inner_radius_m**4)

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


@dataclass(frozen=True)
class BarbCuffMicroSpringSpec:
    """Method-B radial micro-spring silicone liner inside Route A hose cuff for barb interference lock."""

    n_pads: int = 4
    pad_radius_m: float = 0.0022
    cuff_rest_inner_radius_m: float = 0.0034
    barb_bead_outer_radius_m: float = 0.0048
    spring_stiffness_n_m: float = 1200.0
    spring_damping_ns_m: float = 18.0
    max_radial_force_n: float = 9.0
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
    # PhysX D6 angular drive expects N*m/deg when using USD degrees OR N*m/rad in physics;
    # we store SI N*m/rad here and convert explicitly by (pi/180) when writing USD DriveAPI stiffness!
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
        linear_damping=0.45,
        angular_damping=0.55,
        capsule_radius_m=float(mat.outer_radius_m),
        cuff_spec=BarbCuffMicroSpringSpec(),
    )

