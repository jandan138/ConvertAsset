"""Exact coaxial CAD specifications and 12-stage Bilibili BV17t4y1V7XH timeline for distillation_v06."""

from __future__ import annotations

import math
from typing import Any


CONDENSER_PITCH_DEG: float = 15.0  # +15 deg about +Y => +X points right & downward (cos 15, 0, -sin 15)
_TH = math.radians(CONDENSER_PITCH_DEG)
CONDENSER_AXIS_WORLD: tuple[float, float, float] = (math.cos(_TH), 0.0, -math.sin(_TH))
CONDENSER_QUAT_WXYZ: tuple[float, float, float, float] = (math.cos(0.5 * _TH), 0.0, math.sin(0.5 * _TH), 0.0)

TABLE_SURFACE_Z: float = 0.750

V06_INSTRUMENT_IDS: tuple[str, ...] = (
    "iron_stand_left",
    "iron_stand_right",
    "scissor_jack_blue",
    "scissor_jack_white",
    "heating_stirrer_bath",
    "bosshead_left",
    "bosshead_right",
    "flask_clamp_2prong",
    "condenser_clamp_3prong",
    "round_bottom_flask_250ml",
    "distillation_head_75deg",
    "screw_thermometer_adapter",
    "mercury_thermometer_300c",
    "liebig_condenser_24_29",
    "vacuum_tail_adapter",
    "erlenmeyer_flask_150ml",
    "long_stem_funnel",
    "pour_beaker_100ml",
    "keck_clip_head_cond",
    "keck_clip_cond_tail",
)

# Exact coaxial assembly chain matching Bilibili BV17t4y1V7XH (02:27 - 06:20)
_FLASK_X = -0.180
_FLASK_Y = 0.000
_FLASK_Z = 0.940
_HEAD_Z = 1.026  # Mates 0.0 mm coaxially into flask 24/29 socket (rim 1.041 m)
_SIDEARM_BRANCH_Z = _HEAD_Z + 0.062  # 1.088 m
_SIDEARM_BOTTOM_LIP_Z = _HEAD_Z + 0.054  # 1.0800 m ("水银球上沿和支管口下沿平齐")
_HEAD_SIDEARM_CONE_XYZ = (
    round(_FLASK_X + 0.085 * CONDENSER_AXIS_WORLD[0], 6),  # -0.097896
    0.0,
    round(_SIDEARM_BRANCH_Z + 0.085 * CONDENSER_AXIS_WORLD[2], 6),  # 1.066000
)
_COND_CENTER_XYZ = (
    round(_HEAD_SIDEARM_CONE_XYZ[0] + 0.125 * CONDENSER_AXIS_WORLD[0], 6),  # +0.022844
    0.0,
    round(_HEAD_SIDEARM_CONE_XYZ[2] + 0.125 * CONDENSER_AXIS_WORLD[2], 6),  # 1.033648
)
_COND_LOWER_CONE_XYZ = (
    round(_COND_CENTER_XYZ[0] + 0.125 * CONDENSER_AXIS_WORLD[0], 6),  # +0.143585
    0.0,
    round(_COND_CENTER_XYZ[2] + 0.125 * CONDENSER_AXIS_WORLD[2], 6),  # 1.001296
)
_DRIP_X = round(_COND_LOWER_CONE_XYZ[0] + 0.071415, 6)  # +0.215000
_DRIP_TIP_Z = round(_COND_LOWER_CONE_XYZ[2] - 0.079296, 6)  # 0.922000

# Barb root & tip world coordinates on assembled Liebig condenser ("下进上出")
# Local barb direction points forward (-Y) and downward (-Z) so hoses drape cleanly in front of rear stands
_BARB_LOCAL_DIR = (0.0, -0.469472, -0.882948)


def _cond_local_to_world(lx: float, ly: float, lz: float) -> tuple[float, float, float]:
    c, s = math.cos(_TH), math.sin(_TH)
    wx = _COND_CENTER_XYZ[0] + c * lx + s * lz
    wy = _COND_CENTER_XYZ[1] + ly
    wz = _COND_CENTER_XYZ[2] - s * lx + c * lz
    return (round(wx, 6), round(wy, 6), round(wz, 6))


V06_APPARATUS_LAYOUT: dict[str, Any] = {
    "table_surface_z": TABLE_SURFACE_Z,
    "condenser_pitch_deg": CONDENSER_PITCH_DEG,
    "condenser_axis_world": list(CONDENSER_AXIS_WORLD),
    "condenser_quat_wxyz": [round(v, 7) for v in CONDENSER_QUAT_WXYZ],
    "sidearm_bottom_lip_z_world": _SIDEARM_BOTTOM_LIP_Z,
    "thermometer_bulb_top_local_z": -0.0980,
    "thermometer_assembled_z_world": round(_SIDEARM_BOTTOM_LIP_Z + 0.0980, 6),  # 1.1780 m
    "head_sidearm_cone_world": list(_HEAD_SIDEARM_CONE_XYZ),
    "condenser_center_world": list(_COND_CENTER_XYZ),
    "condenser_lower_cone_world": list(_COND_LOWER_CONE_XYZ),
    "tail_drip_tip_world": [_DRIP_X, 0.0, _DRIP_TIP_Z],
    "lower_inlet_barb_root_world": list(
        _cond_local_to_world(
            +0.074,
            0.016 * _BARB_LOCAL_DIR[1],
            -0.016 + 0.016 * _BARB_LOCAL_DIR[2],
        )
    ),
    "lower_inlet_barb_tip_world": list(
        _cond_local_to_world(
            +0.074,
            0.038 * _BARB_LOCAL_DIR[1],
            -0.016 + 0.038 * _BARB_LOCAL_DIR[2],
        )
    ),
    "upper_outlet_barb_root_world": list(
        _cond_local_to_world(
            -0.074,
            0.016 * _BARB_LOCAL_DIR[1],
            -0.016 + 0.016 * _BARB_LOCAL_DIR[2],
        )
    ),
    "upper_outlet_barb_tip_world": list(
        _cond_local_to_world(
            -0.074,
            0.038 * _BARB_LOCAL_DIR[1],
            -0.016 + 0.038 * _BARB_LOCAL_DIR[2],
        )
    ),
    "water_tap_nozzle_world": [0.390, -0.185, 0.855],
    "sink_drain_nozzle_world": [-0.390, -0.185, 0.805],
    "rear_robot_bases": {
        "franka_left": {"xyz": [-0.300, 0.480, TABLE_SURFACE_Z], "wxyz": [0.7071068, 0.0, 0.0, -0.7071068]},
        "franka_right": {"xyz": [0.300, 0.480, TABLE_SURFACE_Z], "wxyz": [0.7071068, 0.0, 0.0, -0.7071068]},
    },
}

# Staged initial bench layout: spacious non-overlapping left/right zones (>= 8.5 cm clearance, 100% inside camera frame & clear of front hose lane!)
V06_COMPONENTS: dict[str, dict[str, Any]] = {
    "iron_stand_left": {
        "staged_xyz": [-0.310, 0.085, TABLE_SURFACE_Z],
        "assembled_xyz": [-0.265, 0.075, TABLE_SURFACE_Z],
        "staged_wxyz": [1.0, 0.0, 0.0, 0.0],
        "assembled_wxyz": [1.0, 0.0, 0.0, 0.0],
        "mass_kg": 2.40,
        "glass": False,
    },
    "iron_stand_right": {
        "staged_xyz": [0.095, 0.085, TABLE_SURFACE_Z],
        "assembled_xyz": [0.055, 0.085, TABLE_SURFACE_Z],
        "staged_wxyz": [1.0, 0.0, 0.0, 0.0],
        "assembled_wxyz": [1.0, 0.0, 0.0, 0.0],
        "mass_kg": 2.40,
        "glass": False,
    },
    "scissor_jack_blue": {
        "staged_xyz": [-0.180, 0.000, TABLE_SURFACE_Z],
        "assembled_xyz": [-0.180, 0.000, TABLE_SURFACE_Z],
        "staged_wxyz": [1.0, 0.0, 0.0, 0.0],
        "assembled_wxyz": [1.0, 0.0, 0.0, 0.0],
        "lift_staged_m": 0.048,
        "lift_assembled_m": 0.070,
        "mass_kg": 1.35,
        "glass": False,
    },
    "scissor_jack_white": {
        "staged_xyz": [0.215, 0.000, TABLE_SURFACE_Z],
        "assembled_xyz": [0.215, 0.000, TABLE_SURFACE_Z],
        "staged_wxyz": [1.0, 0.0, 0.0, 0.0],
        "assembled_wxyz": [1.0, 0.0, 0.0, 0.0],
        "lift_staged_m": 0.048,
        "lift_assembled_m": 0.082,
        "mass_kg": 1.25,
        "glass": False,
    },
    "heating_stirrer_bath": {
        "staged_xyz": [-0.180, 0.000, TABLE_SURFACE_Z + 0.048],
        "assembled_xyz": [-0.180, 0.000, TABLE_SURFACE_Z + 0.070],
        "staged_wxyz": [1.0, 0.0, 0.0, 0.0],
        "assembled_wxyz": [1.0, 0.0, 0.0, 0.0],
        "mass_kg": 1.85,
        "glass": True,
    },
    "bosshead_left": {
        "staged_xyz": [-0.510, 0.030, TABLE_SURFACE_Z + 0.018],
        "assembled_xyz": [-0.280, 0.075, 0.992],
        "staged_wxyz": [1.0, 0.0, 0.0, 0.0],
        "assembled_wxyz": [1.0, 0.0, 0.0, 0.0],
        "open_slot_up_axis_local": [0.0, 0.0, 1.0],
        "mass_kg": 0.16,
        "glass": False,
    },
    "bosshead_right": {
        "staged_xyz": [0.350, 0.095, TABLE_SURFACE_Z + 0.018],
        "assembled_xyz": [0.055, 0.085, _COND_CENTER_XYZ[2]],
        "staged_wxyz": [1.0, 0.0, 0.0, 0.0],
        "assembled_wxyz": [1.0, 0.0, 0.0, 0.0],
        "open_slot_up_axis_local": [0.0, 0.0, 1.0],
        "mass_kg": 0.16,
        "glass": False,
    },
    "flask_clamp_2prong": {
        "staged_xyz": [-0.465, 0.115, TABLE_SURFACE_Z + 0.018],
        "assembled_xyz": [-0.180, 0.000, 0.992],
        "staged_wxyz": [1.0, 0.0, 0.0, 0.0],
        "assembled_wxyz": [1.0, 0.0, 0.0, 0.0],
        "mass_kg": 0.22,
        "glass": False,
    },
    "condenser_clamp_3prong": {
        "staged_xyz": [0.455, 0.095, TABLE_SURFACE_Z + 0.028],
        "assembled_xyz": list(_COND_CENTER_XYZ),
        "staged_wxyz": [1.0, 0.0, 0.0, 0.0],
        "assembled_wxyz": [round(v, 7) for v in CONDENSER_QUAT_WXYZ],
        "fixed_prong_below_local_z": -0.014,
        "movable_prong_above_local_z": 0.016,
        "mass_kg": 0.24,
        "glass": False,
    },
    "round_bottom_flask_250ml": {
        "staged_xyz": [-0.385, -0.065, TABLE_SURFACE_Z + 0.044],
        "assembled_xyz": [_FLASK_X, _FLASK_Y, _FLASK_Z],
        "staged_wxyz": [1.0, 0.0, 0.0, 0.0],
        "assembled_wxyz": [1.0, 0.0, 0.0, 0.0],
        "mass_kg": 0.145,
        "glass": True,
    },
    "distillation_head_75deg": {
        "staged_xyz": [-0.505, -0.075, TABLE_SURFACE_Z + 0.022],
        "assembled_xyz": [_FLASK_X, _FLASK_Y, _HEAD_Z],
        "staged_wxyz": [0.7071068, 0.7071068, 0.0, 0.0],
        "assembled_wxyz": [1.0, 0.0, 0.0, 0.0],
        "mass_kg": 0.095,
        "glass": True,
    },
    "screw_thermometer_adapter": {
        "staged_xyz": [-0.350, -0.155, TABLE_SURFACE_Z + 0.022],
        "assembled_xyz": [_FLASK_X, _FLASK_Y, _HEAD_Z + 0.106],
        "staged_wxyz": [1.0, 0.0, 0.0, 0.0],
        "assembled_wxyz": [1.0, 0.0, 0.0, 0.0],
        "mass_kg": 0.042,
        "glass": True,
    },
    "mercury_thermometer_300c": {
        "staged_xyz": [-0.215, -0.155, TABLE_SURFACE_Z + 0.008],
        "assembled_xyz": [_FLASK_X, _FLASK_Y, round(_SIDEARM_BOTTOM_LIP_Z + 0.0980, 6)],
        "staged_wxyz": [0.7071068, 0.0, 0.7071068, 0.0],
        "assembled_wxyz": [1.0, 0.0, 0.0, 0.0],
        "mass_kg": 0.032,
        "glass": True,
    },
    "liebig_condenser_24_29": {
        "staged_xyz": [0.025, -0.145, TABLE_SURFACE_Z + 0.026],
        "assembled_xyz": list(_COND_CENTER_XYZ),
        "staged_wxyz": [0.0, 1.0, 0.0, 0.0],
        "assembled_wxyz": [round(v, 7) for v in CONDENSER_QUAT_WXYZ],
        "mass_kg": 0.185,
        "glass": True,
    },
    "vacuum_tail_adapter": {
        "staged_xyz": [0.355, -0.015, TABLE_SURFACE_Z + 0.022],
        "assembled_xyz": list(_COND_LOWER_CONE_XYZ),
        "staged_wxyz": [0.7071068, 0.7071068, 0.0, 0.0],
        "assembled_wxyz": [1.0, 0.0, 0.0, 0.0],
        "mass_kg": 0.068,
        "glass": True,
    },
    "erlenmeyer_flask_150ml": {
        "staged_xyz": [0.470, -0.020, TABLE_SURFACE_Z],
        "assembled_xyz": [_DRIP_X, 0.000, TABLE_SURFACE_Z + 0.082],
        "staged_wxyz": [1.0, 0.0, 0.0, 0.0],
        "assembled_wxyz": [1.0, 0.0, 0.0, 0.0],
        "mass_kg": 0.115,
        "glass": True,
    },
    "long_stem_funnel": {
        "staged_xyz": [-0.505, -0.165, TABLE_SURFACE_Z + 0.038],
        "pour_xyz": [_FLASK_X, _FLASK_Y, _HEAD_Z + 0.118],
        "assembled_xyz": [-0.505, -0.165, TABLE_SURFACE_Z + 0.038],
        "staged_wxyz": [0.7071068, 0.7071068, 0.0, 0.0],
        "assembled_wxyz": [0.7071068, 0.7071068, 0.0, 0.0],
        "mass_kg": 0.055,
        "glass": True,
    },
    "pour_beaker_100ml": {
        "staged_xyz": [-0.285, -0.095, TABLE_SURFACE_Z],
        "pour_xyz": [_FLASK_X + 0.052, -0.006, _HEAD_Z + 0.185],
        "assembled_xyz": [-0.285, -0.095, TABLE_SURFACE_Z],
        "staged_wxyz": [1.0, 0.0, 0.0, 0.0],
        "assembled_wxyz": [1.0, 0.0, 0.0, 0.0],
        "mass_kg": 0.088,
        "glass": True,
    },
    "keck_clip_head_cond": {
        "staged_xyz": [0.220, -0.115, TABLE_SURFACE_Z + 0.008],
        "assembled_xyz": list(_HEAD_SIDEARM_CONE_XYZ),
        "staged_wxyz": [1.0, 0.0, 0.0, 0.0],
        "assembled_wxyz": [round(v, 7) for v in CONDENSER_QUAT_WXYZ],
        "mass_kg": 0.008,
        "glass": False,
    },
    "keck_clip_cond_tail": {
        "staged_xyz": [0.280, -0.115, TABLE_SURFACE_Z + 0.008],
        "assembled_xyz": list(_COND_LOWER_CONE_XYZ),
        "staged_wxyz": [1.0, 0.0, 0.0, 0.0],
        "assembled_wxyz": [round(v, 7) for v in CONDENSER_QUAT_WXYZ],
        "mass_kg": 0.008,
        "glass": False,
    },
}

# 12 Exact Bilibili BV17t4y1V7XH Stages (02:27 - 06:20 => 147s - 380s)
BILIBILI_SOP_STAGES_V06: tuple[dict[str, Any], ...] = (
    {
        "stage_id": "S01_stand_bath_jack_datum",
        "title_zh": "S01 · 铁架台、升降台与集热式热浴定标",
        "bilibili_start_s": 147.0,
        "bilibili_end_s": 160.0,
        "bilibili_keyframe_s": 154.0,
        "sim_norm_window": [0.00, 0.07],
        "sop_rule_zh": "从下往上、从左往右：先定标左侧蓝色升降台与玻璃热浴高度及双铁架台间距",
    },
    {
        "stage_id": "S02_left_bosshead_flask_clamp",
        "title_zh": "S02 · 左侧十字夹（开口向上）与烧瓶夹安装",
        "bilibili_start_s": 161.0,
        "bilibili_end_s": 175.0,
        "bilibili_keyframe_s": 168.0,
        "sim_norm_window": [0.07, 0.14],
        "sop_rule_zh": "十字夹开口严格向上，防止顶丝松脱滑落；烧瓶夹对准热浴中心",
    },
    {
        "stage_id": "S03_round_flask_bath_immersion",
        "title_zh": "S03 · 圆底烧瓶夹持固定并浸入玻璃热浴",
        "bilibili_start_s": 176.0,
        "bilibili_end_s": 198.0,
        "bilibili_keyframe_s": 190.0,
        "sim_norm_window": [0.14, 0.22],
        "sop_rule_zh": "烧瓶夹抱紧瓶颈磨口下方，球部浸入热浴液面且不触碰浴槽底部",
    },
    {
        "stage_id": "S04_distillation_head_taper_mate",
        "title_zh": "S04 · 75°蒸馏头 24/29 标准磨口同轴插合",
        "bilibili_start_s": 199.0,
        "bilibili_end_s": 211.0,
        "bilibili_keyframe_s": 204.0,
        "sim_norm_window": [0.22, 0.29],
        "sop_rule_zh": "1:10 磨砂标准口零别劲同轴插合，支管朝向右侧冷凝接收端",
    },
    {
        "stage_id": "S05_right_bosshead_3prong_clamp",
        "title_zh": "S05 · 右侧十字夹（开口向上）与三指冷凝管夹（下固上动）",
        "bilibili_start_s": 212.0,
        "bilibili_end_s": 238.0,
        "bilibili_keyframe_s": 233.0,
        "sim_norm_window": [0.29, 0.37],
        "sop_rule_zh": "十字夹开口向上；红白胶套三指夹严格遵循『固定臂在下、活动臂在上』并校准 -15° 同轴倾角",
    },
    {
        "stage_id": "S06_condenser_keck_latex_hoses",
        "title_zh": "S06 · 直形冷凝管同轴对接、绿色标准口夹与下进上出乳胶管",
        "bilibili_start_s": 239.0,
        "bilibili_end_s": 253.0,
        "bilibili_keyframe_s": 248.0,
        "sim_norm_window": [0.37, 0.47],
        "sop_rule_zh": "双手稳托带琥珀乳胶水管的直形冷凝管嵌合支管，旋紧三指夹并扣绿色标准口夹，水管下进上出自然悬链无穿模",
    },
    {
        "stage_id": "S07_tail_adapter_white_jack_receiver",
        "title_zh": "S07 · 接引管安装与白色升降台托升三角烧瓶",
        "bilibili_start_s": 254.0,
        "bilibili_end_s": 260.0,
        "bilibili_keyframe_s": 255.0,
        "sim_norm_window": [0.47, 0.55],
        "sop_rule_zh": "接引管扣紧绿色标准口夹，旋升白色升降台使接引管滴口伸入三角烧瓶口内",
    },
    {
        "stage_id": "S08_funnel_pour_purple_solution",
        "title_zh": "S08 · 插长颈三角漏斗注入紫红色待蒸馏溶液",
        "bilibili_start_s": 261.0,
        "bilibili_end_s": 267.0,
        "bilibili_keyframe_s": 262.0,
        "sim_norm_window": [0.55, 0.64],
        "sop_rule_zh": "经长颈三角漏斗将紫红色待蒸馏液注入圆底烧瓶（严防沾污磨口与支管），注毕取下漏斗",
    },
    {
        "stage_id": "S09_screw_thermometer_bulb_align",
        "title_zh": "S09 · 螺帽温度计安装与水银球上沿对齐支管下沿",
        "bilibili_start_s": 268.0,
        "bilibili_end_s": 286.0,
        "bilibili_keyframe_s": 269.0,
        "sim_norm_window": [0.64, 0.72],
        "sop_rule_zh": "旋紧螺帽接头并微调水银温度计深度，使水银球上沿与支管口下沿严格平齐（误差 <= 1.0 mm）",
    },
    {
        "stage_id": "S10_active_distillation_condensate_drip",
        "title_zh": "S10 · 下进上出通水加热、水银球挂滴与无色馏分滴落",
        "bilibili_start_s": 287.0,
        "bilibili_end_s": 329.0,
        "bilibili_keyframe_s": 312.0,
        "sim_norm_window": [0.72, 0.82],
        "sop_rule_zh": "先通冷却水（下进上出）再开热浴搅拌加热；水银球凝结液滴，接引管匀速滴出无色透明馏出液；停热冷却",
    },
    {
        "stage_id": "S11_reverse_disassemble_right_train",
        "title_zh": "S11 · 逆序拆除右端（降白升降台退接收瓶 -> 拆接引管 -> 卸冷凝管）",
        "bilibili_start_s": 330.0,
        "bilibili_end_s": 353.0,
        "bilibili_keyframe_s": 341.0,
        "sim_norm_window": [0.82, 0.91],
        "sop_rule_zh": "严格遵循『先右后左』：先降白色升降台移出三角烧瓶与接引管，再取标准口夹、松三指夹双手卸下直形冷凝管",
    },
    {
        "stage_id": "S12_reverse_disassemble_left_column",
        "title_zh": "S12 · 逆序拆除左端（先上后下：拔温度计 -> 拆蒸馏头 -> 取圆底烧瓶）",
        "bilibili_start_s": 354.0,
        "bilibili_end_s": 380.0,
        "bilibili_keyframe_s": 363.0,
        "sim_norm_window": [0.91, 1.00],
        "sop_rule_zh": "严格遵循『先上后下』：拔出螺帽温度计组件 -> 垂直取下75°蒸馏头 -> 降热浴松烧瓶夹取下圆底烧瓶归位",
    },
)


def build_v06_cad_specs() -> dict[str, Any]:
    return {
        "schema_version": "distillation-v06-bilibili-aligned-cad/v1.0",
        "reference_bilibili_bvid": "BV17t4y1V7XH",
        "layout": V06_APPARATUS_LAYOUT,
        "components": V06_COMPONENTS,
        "stages": list(BILIBILI_SOP_STAGES_V06),
    }
