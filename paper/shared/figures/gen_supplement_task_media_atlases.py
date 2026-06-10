#!/usr/bin/env python3
"""Build task/media atlas pages for the ACL supplement."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps


FIG_DIR = Path(__file__).resolve().parent

MATERIAL_OUT = FIG_DIR / "fig_supplement_material_diagnostic_atlas.png"
MATERIAL_CLAIM_BOUNDARY_OUT = FIG_DIR / "fig_supplement_material_claim_boundary_atlas.png"
MATERIAL_CLAIM_BOUNDARY_GATE_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_material_claim_boundary_gate_ai_slot.png"
MATERIAL_DECISION_MAP_OUT = FIG_DIR / "fig_supplement_material_decision_map.png"
MATERIAL_DECISION_GATE_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_material_decision_gate_v2_ai_slot.png"
FIRST_PAGE_EVIDENCE_QUICKSTART_OUT = FIG_DIR / "fig_supplement_first_page_evidence_quickstart.png"
PAGE4_CLAIM_BOUNDARY_COMPANION_OUT = FIG_DIR / "fig_supplement_page4_claim_boundary_companion.png"
NAVIGATION_OUT = FIG_DIR / "fig_supplement_navigation_media_atlas.png"
MATERIAL_STRIP_OUT = FIG_DIR / "fig_supplement_material_intro_strip.png"
NAVIGATION_STRIP_OUT = FIG_DIR / "fig_supplement_navigation_intro_strip.png"
MATERIAL_COLUMN_OUT = FIG_DIR / "fig_supplement_material_intro_column.png"
NAVIGATION_COLUMN_OUT = FIG_DIR / "fig_supplement_navigation_intro_column.png"
NAVIGATION_MEDIA_BOUNDARY_OUT = FIG_DIR / "fig_supplement_navigation_media_boundary_strip.png"
INTERNNAV_SELECTED6_NEUTRAL_COMPANION_OUT = FIG_DIR / "fig_supplement_internnav_selected6_neutral_companion.png"
INTERNNAV_0036_NEUTRAL_COMPANION_OUT = FIG_DIR / "fig_supplement_internnav_0036_neutral_companion.png"
INTERNNAV_UPLOAD_GATE_CLOSURE_OUT = FIG_DIR / "fig_supplement_internnav_upload_gate_closure_card.png"
THEORY_BRIDGE_OUT = FIG_DIR / "fig_supplement_theory_evidence_bridge.png"
THEORY_FAILURE_MODE_MAP_OUT = FIG_DIR / "fig_supplement_theory_failure_mode_map.png"
THEORY_HYPOTHESIS_BOUNDARY_COMPANION_OUT = FIG_DIR / "fig_supplement_theory_hypothesis_boundary_companion.png"
REVIEW_PACKET_CONTACT_OUT = FIG_DIR / "fig_supplement_review_packet_contact_sheet.png"
SOURCE_BOUNDARY_COMPANION_OUT = FIG_DIR / "fig_supplement_source_boundary_companion.png"
PROXY_METRIC_DERIVATION_COMPANION_OUT = FIG_DIR / "fig_supplement_proxy_metric_derivation_companion.png"
GROUNDING_DERIVATION_COMPANION_OUT = FIG_DIR / "fig_supplement_grounding_derivation_companion.png"
NAVIGATION_DERIVATION_COMPANION_OUT = FIG_DIR / "fig_supplement_navigation_derivation_companion.png"
RENDER_SCENE_EXTENDED_OUT = FIG_DIR / "fig_supplement_render_scene_evidence_extended.png"
GRSCENES_VLM_GUIDE_OUT = FIG_DIR / "fig_supplement_grscenes_vlm_visual_guide.png"
VLM_COORDINATE_PROTOCOL_OUT = FIG_DIR / "fig_supplement_vlm_coordinate_protocol_atlas.png"
VLM_COORDINATE_TABLE_COMPANION_OUT = FIG_DIR / "fig_supplement_vlm_coordinate_table_companion.png"
VLM_COORDINATE_BASELINE_SANITY_COMPANION_OUT = FIG_DIR / "fig_supplement_vlm_coordinate_baseline_sanity_companion.png"
GRSCENES_DIAGNOSTIC_CASE_OUT = FIG_DIR / "fig_supplement_grscenes_diagnostic_case_atlas.png"
GRSCENES_VLM_STRESS_STRIP_OUT = FIG_DIR / "fig_supplement_grscenes_vlm_stress_render_strip.png"
GRSCENES_FAILURE_TAXONOMY_COMPANION_OUT = FIG_DIR / "fig_supplement_grscenes_failure_taxonomy_table_companion.png"
GRSCENES_PASS_ONLY_COMPANION_OUT = FIG_DIR / "fig_supplement_grscenes_pass_only_table_companion.png"
GRSCENES_ZOOM_STRESS_COMPANION_OUT = FIG_DIR / "fig_supplement_grscenes_zoom_stress_table_companion.png"
VISUAL_EVIDENCE_ROADMAP_OUT = FIG_DIR / "fig_supplement_visual_evidence_roadmap.png"
RENDER_ATLAS_OPENER_OUT = FIG_DIR / "fig_supplement_render_atlas_opener.png"
METRIC_BOUNDARY_BRIDGE_OUT = FIG_DIR / "fig_supplement_metric_boundary_bridge.png"
CLAIM_BOUNDARY_EXAMPLES_OUT = FIG_DIR / "fig_supplement_claim_boundary_examples.png"
EVIDENCE_GATE_REGISTRY_COMPANION_OUT = FIG_DIR / "fig_supplement_evidence_gate_registry_companion.png"

SUPPLEMENT_RENDER_ATLAS = FIG_DIR / "fig_supplement_render_atlas.png"
RENDER_SCENE_WIDE = FIG_DIR / "fig_render_scene_evidence_wide.png"
RENDER_PAIRS = FIG_DIR / "fig_render_pairs.png"
GRSCENE_QUALITATIVE = FIG_DIR / "fig_grscene_qualitative.png"
MATERIAL_BASELINE = FIG_DIR / "fig_material_effect_baseline_qualitative.png"
MATERIAL_SUPPLEMENTAL = FIG_DIR / "fig_material_effect_supplemental_qualitative.png"
RAW_RENDER_ROOT = FIG_DIR.parent / "evidence" / "raw" / "renders"
PROXY_OBJECT_0011_A = RAW_RENDER_ROOT / "chestofdrawers_0011" / "A_top_front_right.png"
PROXY_OBJECT_0011_B = RAW_RENDER_ROOT / "chestofdrawers_0011" / "B_top_front_right.png"
PROXY_OBJECT_0011_A_FRONT = RAW_RENDER_ROOT / "chestofdrawers_0011" / "A_front.png"
PROXY_OBJECT_0011_B_FRONT = RAW_RENDER_ROOT / "chestofdrawers_0011" / "B_front.png"
PROXY_OBJECT_0023_A = RAW_RENDER_ROOT / "chestofdrawers_0023" / "A_top_front_right.png"
PROXY_OBJECT_0023_B = RAW_RENDER_ROOT / "chestofdrawers_0023" / "B_top_front_right.png"
PROXY_OBJECT_0023_A_FRONT = RAW_RENDER_ROOT / "chestofdrawers_0023" / "A_front.png"
PROXY_OBJECT_0023_B_FRONT = RAW_RENDER_ROOT / "chestofdrawers_0023" / "B_front.png"
GRSCENES_ORBIT_MDL_01 = FIG_DIR / "out_tmp" / "mdl_images" / "orbit_mdl_01.png"
GRSCENES_ORBIT_NOMDL_01 = FIG_DIR / "out_tmp" / "nomdl_images" / "orbit_01.png"
GRSCENES_ORBIT_MDL_03 = FIG_DIR / "out_tmp" / "mdl_images" / "orbit_mdl_03.png"
GRSCENES_ORBIT_NOMDL_03 = FIG_DIR / "out_tmp" / "nomdl_images" / "orbit_03.png"
VLM_CLEAN_RERENDER = FIG_DIR / "fig_supplement_vlm_clean_rerender_panel.png"
VLM_RENDER_ROOT = FIG_DIR.parent / "evidence" / "raw" / "grscene_vlm_grounding" / "retake_zoom_renders"
VLM_BACKPACK_ORIGINAL = VLM_RENDER_ROOT / "MV7J6NIKTKJZ2AABAAAAADQ8_usd" / "47aa36277a54f6ca90cc" / "zoom_018" / "original" / "original_0000.png"
VLM_BACKPACK_CONVERTED = VLM_RENDER_ROOT / "MV7J6NIKTKJZ2AABAAAAADQ8_usd" / "47aa36277a54f6ca90cc" / "zoom_018" / "converted" / "converted_0000.png"
VLM_CLOCK_ORIGINAL = VLM_RENDER_ROOT / "MV7J6NIKTKJZ2AABAAAAADQ8_usd" / "f35ef3d86c42446b7ddf" / "zoom_018" / "original" / "original_0000.png"
VLM_CLOCK_CONVERTED = VLM_RENDER_ROOT / "MV7J6NIKTKJZ2AABAAAAADQ8_usd" / "f35ef3d86c42446b7ddf" / "zoom_018" / "converted" / "converted_0000.png"
VLM_BOTTLE_ORIGINAL = VLM_RENDER_ROOT / "MV7J6NIKTKJZ2AABAAAAADA8_usd" / "c27086f557d316584264" / "zoom_018" / "original" / "original_0000.png"
VLM_BOTTLE_CONVERTED = VLM_RENDER_ROOT / "MV7J6NIKTKJZ2AABAAAAADA8_usd" / "c27086f557d316584264" / "zoom_018" / "converted" / "converted_0000.png"
VLM_CUP_ORIGINAL = VLM_RENDER_ROOT / "MV7J6NIKTKJZ2AABAAAAADQ8_usd" / "e2ec085d524d5df4455d" / "zoom_020" / "original" / "original_0000.png"
VLM_CUP_CONVERTED = VLM_RENDER_ROOT / "MV7J6NIKTKJZ2AABAAAAADQ8_usd" / "e2ec085d524d5df4455d" / "zoom_020" / "converted" / "converted_0000.png"
VLM_CUP_ALT_ORIGINAL = VLM_RENDER_ROOT / "MV7J6NIKTKJZ2AABAAAAADQ8_usd" / "bb985fd4504a1afe8516" / "zoom_017" / "original" / "original_0000.png"
VLM_CUP_ALT_CONVERTED = VLM_RENDER_ROOT / "MV7J6NIKTKJZ2AABAAAAADQ8_usd" / "bb985fd4504a1afe8516" / "zoom_017" / "converted" / "converted_0000.png"
VLM_FAUCET_ORIGINAL = VLM_RENDER_ROOT / "MV7J6NIKTKJZ2AABAAAAADY8_usd" / "c8ee4b66274b05d242c2" / "zoom_017" / "original" / "original_0000.png"
VLM_FAUCET_CONVERTED = VLM_RENDER_ROOT / "MV7J6NIKTKJZ2AABAAAAADY8_usd" / "c8ee4b66274b05d242c2" / "zoom_017" / "converted" / "converted_0000.png"
VLM_PICTURE_ORIGINAL = VLM_RENDER_ROOT / "MV7J6NIKTKJZ2AABAAAAADI8_usd" / "ef6a4fe9448f672c2ecc" / "zoom_017" / "original" / "original_0000.png"
VLM_PICTURE_CONVERTED = VLM_RENDER_ROOT / "MV7J6NIKTKJZ2AABAAAAADI8_usd" / "ef6a4fe9448f672c2ecc" / "zoom_017" / "converted" / "converted_0000.png"
VLM_BACKPACK_Z19_ORIGINAL = VLM_RENDER_ROOT / "MV7J6NIKTKJZ2AABAAAAADQ8_usd" / "47aa36277a54f6ca90cc" / "zoom_019" / "original" / "original_0000.png"
VLM_BACKPACK_Z19_CONVERTED = VLM_RENDER_ROOT / "MV7J6NIKTKJZ2AABAAAAADQ8_usd" / "47aa36277a54f6ca90cc" / "zoom_019" / "converted" / "converted_0000.png"
VLM_CLOCK_Z19_ORIGINAL = VLM_RENDER_ROOT / "MV7J6NIKTKJZ2AABAAAAADQ8_usd" / "f35ef3d86c42446b7ddf" / "zoom_019" / "original" / "original_0000.png"
VLM_CLOCK_Z19_CONVERTED = VLM_RENDER_ROOT / "MV7J6NIKTKJZ2AABAAAAADQ8_usd" / "f35ef3d86c42446b7ddf" / "zoom_019" / "converted" / "converted_0000.png"
VLM_SCORING_GATE_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_grscenes_vlm_scoring_gate_ai_slot.png"
GRSCENES_VLM_READING_ROUTE_V2_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_grscenes_vlm_reading_route_v2_ai_slot.png"
GRSCENES_TABLE_READING_GATE_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_grscenes_table_reading_gate_ai_slot.png"
GRSCENES_FAILURE_TAXONOMY_GATE_V2_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_grscenes_failure_taxonomy_gate_v2_ai_slot.png"
GRSCENES_FAILURE_TAXONOMY_GATE_V4_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_grscenes_failure_taxonomy_gate_v4_ai_slot.png"
GRSCENES_PASS_ONLY_GATE_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_grscenes_pass_only_gate_ai_slot.png"
GRSCENES_PASS_ONLY_GATE_V3_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_grscenes_pass_only_gate_v3_ai_slot.png"
GRSCENES_ZOOM_STRESS_GATE_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_grscenes_zoom_stress_gate_ai_slot.png"
GRSCENES_ZOOM_STRESS_GATE_V3_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_grscenes_zoom_stress_gate_v3_ai_slot.png"
VLM_COORDINATE_CONTRACT_GATE_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_vlm_coordinate_contract_gate_ai_slot.png"
VLM_COORDINATE_CONTRACT_GATE_V2_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_vlm_coordinate_contract_gate_v2_ai_slot.png"
VLM_COORDINATE_CONTRACT_GATE_V3_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_vlm_coordinate_contract_gate_v3_ai_slot.png"
VLM_PROTOCOL_ROUTE_V2_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_vlm_protocol_route_v2_ai_slot.png"
VLM_COORDINATE_BASELINE_GATE_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_vlm_coordinate_baseline_gate_ai_slot.png"
VLM_COORDINATE_BASELINE_GATE_V2_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_vlm_coordinate_baseline_gate_v2_ai_slot.png"
PROXY_METRIC_LENS_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_proxy_metric_lens_ai_slot.png"
PROXY_METRIC_AXIS_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_proxy_metric_axis_v2_ai_slot.png"
METRIC_CONTRACT_GATE_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_metric_contract_gate_ai_slot.png"
METRIC_CONTRACT_GATE_V2_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_metric_contract_gate_v2_ai_slot.png"
METRIC_CONTRACT_GATE_V3_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_metric_contract_gate_v3_ai_slot.png"
METRIC_BOUNDARY_LENS_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_metric_boundary_lens_ai_slot.png"
EVIDENCE_GATE_READER_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_evidence_gate_reader_ai_slot.png"
EVIDENCE_GATE_READER_V2_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_evidence_gate_reader_v2_ai_slot.png"
EVIDENCE_GATE_READER_V3_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_evidence_gate_reader_v3_ai_slot.png"
EVIDENCE_GATE_READER_V4_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_evidence_gate_reader_v4_ai_slot.png"
EVIDENCE_GATE_READER_V5_TABLE_READING_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_evidence_gate_reader_v5_table_reading_ai_slot.png"
EVIDENCE_SCOPE_READER_V6_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_evidence_scope_reader_v6_ai_slot.png"
THEORY_EVIDENCE_LENS_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_theory_evidence_lens_ai_slot.png"
THEORY_FAILURE_MODE_GATE_V2_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_theory_failure_mode_gate_v2_ai_slot.png"
THEORY_HYPOTHESIS_BOUNDARY_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_theory_hypothesis_boundary_ai_slot.png"
THEORY_HYPOTHESIS_BOUNDARY_V2_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_theory_hypothesis_boundary_v2_ai_slot.png"
THEORY_HYPOTHESIS_BOUNDARY_V3_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_theory_hypothesis_boundary_v3_ai_slot.png"
THEORY_HYPOTHESIS_BOUNDARY_V5_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_theory_hypothesis_boundary_v5_ai_slot.png"
THEORY_HYPOTHESIS_BOUNDARY_V6_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_theory_hypothesis_boundary_v6_ai_slot.png"
FIRST_PAGE_READING_COMPASS_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_first_page_reading_compass_v4_ai_slot.png"
PAGE4_BOUNDARY_MARKER_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_page4_boundary_marker_v3_ai_slot.png"
SOURCE_BOUNDARY_GATE_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_source_boundary_gate_ai_slot.png"
CLAIM_BOUNDARY_EXAMPLES_GATE_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_claim_boundary_examples_gate_v2_ai_slot.png"
SELECTED6_NEUTRAL_GATE_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_internnav_selected6_neutral_gate_ai_slot.png"
NAV_DOWNSTREAM = FIG_DIR / "fig_internnav_downstream_panel.png"
NAV_STILLS = FIG_DIR / "fig_internnav_rollout_stills.png"
NAV_0036_MAIN = FIG_DIR / "fig_internnav_rollout_0036_0066_main3_readable.png"
NAV_SELECTED6 = FIG_DIR / "fig_internnav_rollout_selected6_supp.png"
NAV_0036_SELECTED6 = FIG_DIR / "fig_internnav_rollout_0036_0066_selected6_supp.png"
NAV_SELECTED_CASE = FIG_DIR / "supplement" / "internnav_selected6_case01.png"
NAV_SELECTED_CASE2 = FIG_DIR / "supplement" / "internnav_selected6_case02.png"
NAV_SELECTED_CASE3 = FIG_DIR / "supplement" / "internnav_selected6_case03.png"
NAV_SELECTED_CASE4 = FIG_DIR / "supplement" / "internnav_selected6_case04.png"
NAV_SELECTED_CASE5 = FIG_DIR / "supplement" / "internnav_selected6_case05.png"
NAV_SELECTED_CASE6 = FIG_DIR / "supplement" / "internnav_selected6_case06.png"
NAV_0036_CASE = FIG_DIR / "supplement" / "internnav_0036_0066_case01.png"
NAV_0036_CASE2 = FIG_DIR / "supplement" / "internnav_0036_0066_case02.png"
NAV_0036_CASE3 = FIG_DIR / "supplement" / "internnav_0036_0066_case03.png"
NAV_0036_CASE4 = FIG_DIR / "supplement" / "internnav_0036_0066_case04.png"
NAV_0036_CASE5 = FIG_DIR / "supplement" / "internnav_0036_0066_case05.png"
NAV_0036_CASE6 = FIG_DIR / "supplement" / "internnav_0036_0066_case06.png"
NAV_MEDIA_PACKAGE_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_navigation_media_package_ai_slot.png"
NAV_MEDIA_PACKAGE_V2_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_navigation_media_package_v2_ai_slot.png"
NAV_MEDIA_PACKAGE_V3_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_navigation_media_package_v3_ai_slot.png"
NAV_REVIEW_GATE_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_navigation_review_gate_ai_slot.png"
NAV_UPLOAD_GATE_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_internnav_upload_gate_ai_slot.png"
NAV_UPLOAD_GATE_V2_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_internnav_upload_gate_v2_ai_slot.png"
NAVIGATION_METRIC_GATE_V2_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_navigation_metric_gate_v2_ai_slot.png"
NAVIGATION_METRIC_GATE_V3_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_navigation_metric_gate_v3_ai_slot.png"
NAVIGATION_METRIC_GATE_V4_AI_SLOT = FIG_DIR / "ai_slots" / "fig_supplement_navigation_metric_gate_v4_ai_slot.png"

WIDTH = 1800
MARGIN = 42
GAP = 24
TITLE_H = 42
LABEL_H = 30


def _font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _fit(path: Path, size: tuple[int, int], *, cover: bool = False) -> Image.Image:
    image = Image.open(path).convert("RGB")
    if cover:
        return ImageOps.fit(image, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    contained = ImageOps.contain(image, size, method=Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, (250, 250, 250))
    canvas.paste(contained, ((size[0] - contained.width) // 2, (size[1] - contained.height) // 2))
    return canvas


def _fit_with_bbox(path: Path, size: tuple[int, int], bbox: tuple[float, float, float, float]) -> Image.Image:
    source = Image.open(path).convert("RGB")
    contained = ImageOps.contain(source, size, method=Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, (250, 250, 250))
    offset_x = (size[0] - contained.width) // 2
    offset_y = (size[1] - contained.height) // 2
    canvas.paste(contained, (offset_x, offset_y))
    scale_x = contained.width / source.width
    scale_y = contained.height / source.height
    x1, y1, x2, y2 = bbox
    draw = ImageDraw.Draw(canvas)
    draw.rectangle(
        (
            offset_x + x1 * scale_x,
            offset_y + y1 * scale_y,
            offset_x + x2 * scale_x,
            offset_y + y2 * scale_y,
        ),
        outline=(0, 150, 112),
        width=4,
    )
    return canvas


def _bbox_focus_tile(path: Path, size: tuple[int, int], bbox: tuple[float, float, float, float], *, pad_scale: float = 1.55) -> Image.Image:
    source = Image.open(path).convert("RGB")
    x1, y1, x2, y2 = bbox
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    bw = max(1.0, x2 - x1)
    bh = max(1.0, y2 - y1)
    crop_w = min(source.width, max(bw * pad_scale, source.width * 0.42))
    crop_h = min(source.height, max(bh * pad_scale, source.height * 0.42))
    left = max(0, min(source.width - crop_w, cx - crop_w / 2))
    top = max(0, min(source.height - crop_h, cy - crop_h / 2))
    crop = source.crop((int(left), int(top), int(left + crop_w), int(top + crop_h)))
    crop = ImageEnhance.Contrast(crop).enhance(1.06)
    tile = ImageOps.fit(crop, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))

    scale_x = size[0] / crop.width
    scale_y = size[1] / crop.height
    draw = ImageDraw.Draw(tile)
    draw.rectangle(
        (
            (x1 - left) * scale_x,
            (y1 - top) * scale_y,
            (x2 - left) * scale_x,
            (y2 - top) * scale_y,
        ),
        outline=(0, 150, 112),
        width=4,
    )
    return tile


def _fit_with_protocol_overlay(
    path: Path,
    size: tuple[int, int],
    bbox: tuple[float, float, float, float],
    *,
    raw_center: tuple[float, float] = (300.0, 225.0),
) -> Image.Image:
    source = Image.open(path).convert("RGB")
    scale = max(size[0] / source.width, size[1] / source.height)
    resized_w = int(round(source.width * scale))
    resized_h = int(round(source.height * scale))
    resized = source.resize((resized_w, resized_h), Image.Resampling.LANCZOS)
    target_x = ((bbox[0] + bbox[2]) / 2.0) * scale
    target_y = ((bbox[1] + bbox[3]) / 2.0) * scale
    crop_left = max(0, min(resized_w - size[0], int(round(target_x - size[0] / 2))))
    crop_top = max(0, min(resized_h - size[1], int(round(target_y - size[1] / 2))))
    canvas = resized.crop((crop_left, crop_top, crop_left + size[0], crop_top + size[1]))
    offset_x = -crop_left
    offset_y = -crop_top
    scale_x = scale
    scale_y = scale
    x1, y1, x2, y2 = bbox
    draw = ImageDraw.Draw(canvas)
    box = (
        offset_x + x1 * scale_x,
        offset_y + y1 * scale_y,
        offset_x + x2 * scale_x,
        offset_y + y2 * scale_y,
    )
    draw.rectangle(box, outline=(0, 150, 112), width=4)

    raw_x = offset_x + raw_center[0] * scale_x
    raw_y = offset_y + raw_center[1] * scale_y
    draw.line((raw_x - 16, raw_y, raw_x + 16, raw_y), fill=(40, 96, 168), width=4)
    draw.line((raw_x, raw_y - 16, raw_x, raw_y + 16), fill=(40, 96, 168), width=4)

    norm_x = offset_x + ((x1 + x2) / 2.0) * scale_x
    norm_y = offset_y + ((y1 + y2) / 2.0) * scale_y
    draw.ellipse((norm_x - 12, norm_y - 12, norm_x + 12, norm_y + 12), fill=(211, 116, 32), outline=(255, 255, 255), width=3)
    return canvas


def _crop_fit(path: Path, box: tuple[int, int, int, int], size: tuple[int, int]) -> Image.Image:
    image = Image.open(path).convert("RGB").crop(box)
    return ImageOps.fit(image, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def _crop_contain(path: Path, box: tuple[int, int, int, int], size: tuple[int, int]) -> Image.Image:
    image = Image.open(path).convert("RGB").crop(box)
    contained = ImageOps.contain(image, size, method=Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, (250, 250, 250))
    canvas.paste(contained, ((size[0] - contained.width) // 2, (size[1] - contained.height) // 2))
    return canvas


def _draw_panel(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    path: Path,
    cover: bool = False,
    crop: tuple[int, int, int, int] | None = None,
    contain: bool = False,
) -> None:
    title_font = _font(22, bold=True)
    draw.text((x, y), title, fill=(22, 22, 22), font=title_font)
    image_y = y + LABEL_H
    if crop is not None:
        image = _crop_contain(path, crop, (w, h)) if contain else _crop_fit(path, crop, (w, h))
    else:
        image = _fit(path, (w, h), cover=cover and not contain)
    canvas.paste(image, (x, image_y))
    draw.rectangle((x, image_y, x + w, image_y + h), outline=(155, 155, 155), width=2)


def _draw_image_panel(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    image: Image.Image,
) -> None:
    title_font = _font(22, bold=True)
    draw.text((x, y), title, fill=(22, 22, 22), font=title_font)
    image_y = y + LABEL_H
    panel = ImageOps.contain(image, (w, h), method=Image.Resampling.LANCZOS)
    background = Image.new("RGB", (w, h), (250, 250, 250))
    background.paste(panel, ((w - panel.width) // 2, (h - panel.height) // 2))
    canvas.paste(background, (x, image_y))
    draw.rectangle((x, image_y, x + w, image_y + h), outline=(155, 155, 155), width=2)


def _navigation_pair_row_cards(path: Path, size: tuple[int, int]) -> Image.Image:
    canvas = Image.new("RGB", size, (250, 250, 250))
    draw = ImageDraw.Draw(canvas)
    title_font = _font(15, bold=True)
    label_font = _font(13, bold=True)
    note_font = _font(12)

    rows = [
        (
            "493_493",
            "full-run fail -> fail | both_failure_neutral",
            (24, 1738, 548, 2042),
            (558, 1738, 1086, 2042),
        ),
        (
            "484_484",
            "full-run success -> success | both_success_neutral",
            (24, 2144, 548, 2448),
            (558, 2144, 1086, 2448),
        ),
    ]
    pad = 14
    row_gap = 14
    col_gap = 12
    row_h = (size[1] - 2 * pad - row_gap) // 2
    cell_w = (size[0] - 2 * pad - col_gap) // 2
    cell_h = row_h - 58

    for idx, (case_id, outcome, original_box, nomdl_box) in enumerate(rows):
        row_y = pad + idx * (row_h + row_gap)
        draw.rounded_rectangle(
            (pad, row_y, size[0] - pad, row_y + row_h),
            radius=5,
            fill=(252, 252, 252),
            outline=(184, 184, 184),
            width=1,
        )
        draw.text((pad + 10, row_y + 8), case_id, fill=(18, 18, 18), font=title_font)
        draw.text((pad + 96, row_y + 10), outcome, fill=(58, 58, 58), font=note_font)
        cell_y = row_y + 40
        for col, (label, box) in enumerate((("Original row", original_box), ("noMDL row", nomdl_box))):
            cell_x = pad + col * (cell_w + col_gap)
            draw.rectangle((cell_x, cell_y, cell_x + cell_w, cell_y + 20), fill=(238, 238, 238), outline=(176, 176, 176), width=1)
            draw.text((cell_x + 8, cell_y + 3), label, fill=(30, 30, 30), font=label_font)
            tile = _crop_contain(path, box, (cell_w, cell_h))
            canvas.paste(tile, (cell_x, cell_y + 20))
            draw.rectangle((cell_x, cell_y + 20, cell_x + cell_w, cell_y + 20 + cell_h), outline=(176, 176, 176), width=1)

    return canvas


def _navigation_0036_row_detail_cards(path: Path, size: tuple[int, int]) -> Image.Image:
    canvas = Image.new("RGB", size, (250, 250, 250))
    draw = ImageDraw.Draw(canvas)
    title_font = _font(13, bold=True)
    note_font = _font(11)
    header_font = _font(10, bold=True)

    rows = [
        ("919_919", "modified-only\nsuccess", 350, 526),
        ("895_895", "failure\ndivergent", 646, 822),
        ("597_597", "success\ndivergent", 942, 1118),
        ("891_891", "failure\nneutral", 1238, 1414),
    ]
    columns = [
        ("orig start", 174, 423),
        ("orig end", 685, 934),
        ("noMDL start", 940, 1189),
        ("noMDL end", 1452, 1701),
    ]

    pad = 12
    row_gap = 8
    label_w = 108
    col_gap = 6
    row_h = (size[1] - 2 * pad - row_gap * (len(rows) - 1)) // len(rows)
    cell_w = (size[0] - 2 * pad - label_w - col_gap * (len(columns) - 1)) // len(columns)
    cell_h = row_h - 38

    for row_index, (case_id, outcome, y1, y2) in enumerate(rows):
        row_y = pad + row_index * (row_h + row_gap)
        draw.rounded_rectangle(
            (pad, row_y, size[0] - pad, row_y + row_h),
            radius=5,
            fill=(252, 252, 252),
            outline=(184, 184, 184),
            width=1,
        )
        draw.text((pad + 8, row_y + 16), case_id, fill=(18, 18, 18), font=title_font)
        draw.multiline_text((pad + 8, row_y + 36), outcome, fill=(58, 58, 58), font=note_font, spacing=2)
        for col_index, (label, x1, x2) in enumerate(columns):
            cell_x = pad + label_w + col_index * (cell_w + col_gap)
            draw.rectangle((cell_x, row_y + 8, cell_x + cell_w, row_y + 26), fill=(238, 238, 238), outline=(176, 176, 176), width=1)
            draw.text((cell_x + 5, row_y + 11), label, fill=(30, 30, 30), font=header_font)
            tile = _crop_contain(path, (x1, y1, x2, y2), (cell_w, cell_h))
            canvas.paste(tile, (cell_x, row_y + 26))
            draw.rectangle((cell_x, row_y + 26, cell_x + cell_w, row_y + 26 + cell_h), outline=(176, 176, 176), width=1)

    return canvas


def _draw_strip_panel(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    path: Path,
    crop: tuple[int, int, int, int] | None = None,
    contain: bool = False,
) -> None:
    label_font = _font(19, bold=True)
    image_y = y + 28
    if crop is not None:
        image = _crop_fit(path, crop, (w, h))
    else:
        image = _fit(path, (w, h), cover=not contain)
    draw.text((x, y), title, fill=(24, 24, 24), font=label_font)
    canvas.paste(image, (x, image_y))
    draw.rectangle((x, image_y, x + w, image_y + h), outline=(150, 150, 150), width=2)


def _draw_column_panel(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    path: Path,
    crop: tuple[int, int, int, int] | None = None,
    contain: bool = False,
) -> int:
    label_font = _font(24, bold=True)
    draw.text((x, y), title, fill=(24, 24, 24), font=label_font)
    image_y = y + 34
    if crop is not None:
        image = _crop_contain(path, crop, (w, h)) if contain else _crop_fit(path, crop, (w, h))
    else:
        image = _fit(path, (w, h), cover=not contain)
    canvas.paste(image, (x, image_y))
    draw.rectangle((x, image_y, x + w, image_y + h), outline=(145, 145, 145), width=2)
    return image_y + h


def _draw_bridge_band(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    label_w: int,
    image_w: int,
    h: int,
    title: str,
    note: str,
    image: Image.Image,
) -> None:
    title_font = _font(22, bold=True)
    note_font = _font(17)
    body_font = _font(15)
    draw.rounded_rectangle((x, y, x + label_w + image_w + GAP, y + h), radius=8, fill=(252, 252, 252), outline=(180, 180, 180), width=2)
    draw.text((x + 18, y + 18), title, fill=(20, 20, 20), font=title_font)
    draw.text((x + 18, y + 55), note, fill=(70, 70, 70), font=note_font)
    draw.text((x + 18, y + h - 38), "source render evidence", fill=(95, 95, 95), font=body_font)
    image_x = x + label_w + GAP
    image_y = y + 18
    canvas.paste(image, (image_x, image_y))
    draw.rectangle((image_x, image_y, image_x + image_w, image_y + h - 36), outline=(145, 145, 145), width=2)


def _draw_roadmap_lane(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
    index: str,
    title: str,
    note: str,
    tag: str,
    tiles: list[tuple[str, Image.Image]],
    lane_h: int,
) -> int:
    label_w = 285
    thumb_x = MARGIN + label_w + GAP
    content_w = WIDTH - MARGIN - thumb_x
    tile_gap = 16
    tile_w = (content_w - tile_gap * (len(tiles) - 1)) // len(tiles)
    tile_h = lane_h - 116
    title_font = _font(25, bold=True)
    note_font = _font(16)
    badge_font = _font(20, bold=True)
    label_font = _font(14, bold=True)
    small_font = _font(13)

    draw.rounded_rectangle((MARGIN, y, WIDTH - MARGIN, y + lane_h), radius=8, fill=(252, 252, 252), outline=(176, 176, 176), width=2)
    draw.rectangle((MARGIN + 22, y + 24, MARGIN + 62, y + 64), outline=(45, 45, 45), width=2)
    draw.text((MARGIN + 35, y + 28), index, fill=(18, 18, 18), font=badge_font)
    draw.text((MARGIN + 78, y + 21), title, fill=(18, 18, 18), font=title_font)
    draw.multiline_text((MARGIN + 78, y + 61), note, fill=(68, 68, 68), font=note_font, spacing=4)
    draw.rounded_rectangle((MARGIN + 22, y + lane_h - 58, MARGIN + 150, y + lane_h - 28), radius=6, fill=(245, 249, 255), outline=(38, 95, 156), width=2)
    draw.text((MARGIN + 44, y + lane_h - 52), tag, fill=(38, 95, 156), font=label_font)
    draw.text((MARGIN + 22, y + lane_h - 22), "source visuals", fill=(96, 96, 96), font=small_font)

    image_y = y + 72
    for idx, (label, tile) in enumerate(tiles):
        x = thumb_x + idx * (tile_w + tile_gap)
        contained = ImageOps.contain(tile, (tile_w, tile_h), method=Image.Resampling.LANCZOS)
        tile_canvas = Image.new("RGB", (tile_w, tile_h), (250, 250, 250))
        tile_canvas.paste(contained, ((tile_w - contained.width) // 2, (tile_h - contained.height) // 2))
        canvas.paste(tile_canvas, (x, image_y))
        draw.rectangle((x, image_y, x + tile_w, image_y + tile_h), outline=(136, 136, 136), width=2)
        draw.rectangle((x, image_y, x + tile_w, image_y + 26), fill=(250, 250, 250), outline=(136, 136, 136), width=1)
        draw.text((x + 8, image_y + 5), label, fill=(28, 28, 28), font=small_font)
    return y + lane_h


def _draw_claim_boundary_example_lane(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
    index: str,
    title: str,
    cue: str,
    allowed: str,
    not_proved: str,
    tiles: list[tuple[str, Image.Image]],
    accent: tuple[int, int, int],
) -> int:
    lane_h = 310
    label_w = 260
    card_w = 330
    x = MARGIN
    w = WIDTH - 2 * MARGIN
    tile_x = x + label_w + GAP
    card_x = x + w - card_w
    tile_w_total = card_x - tile_x - GAP
    tile_gap = 14
    tile_w = (tile_w_total - tile_gap * (len(tiles) - 1)) // len(tiles)
    tile_h = lane_h - 78
    title_font = _font(24, bold=True)
    note_font = _font(16)
    small_font = _font(13, bold=True)
    body_font = _font(14)

    draw.rectangle((x, y, x + w, y + lane_h), fill=(252, 252, 252), outline=(174, 174, 174), width=2)
    draw.rectangle((x, y, x + 10, y + lane_h), fill=accent)
    draw.rectangle((x + 24, y + 24, x + 62, y + 62), outline=(45, 45, 45), width=2)
    draw.text((x + 37, y + 28), index, fill=(20, 20, 20), font=_font(19, bold=True))
    draw.multiline_text((x + 78, y + 22), title, fill=(18, 18, 18), font=title_font, spacing=3)
    draw.text((x + 78, y + 112), "visual cue", fill=accent, font=small_font)
    draw.multiline_text((x + 78, y + 140), cue, fill=(58, 58, 58), font=note_font, spacing=4)
    draw.text((x + 78, y + lane_h - 36), "source render evidence", fill=(96, 96, 96), font=body_font)

    image_y = y + 48
    for idx, (tile_label, tile) in enumerate(tiles):
        xx = tile_x + idx * (tile_w + tile_gap)
        image = ImageOps.fit(tile, (tile_w, tile_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        canvas.paste(image, (xx, image_y))
        draw.rectangle((xx, image_y, xx + tile_w, image_y + tile_h), outline=(134, 134, 134), width=2)
        draw.rectangle((xx, image_y, xx + tile_w, image_y + 25), fill=(248, 248, 248), outline=(134, 134, 134), width=1)
        draw.text((xx + 7, image_y + 5), tile_label, fill=(28, 28, 28), font=_font(12, bold=True))

    draw.rectangle((card_x, y, card_x + card_w, y + lane_h), fill=(247, 247, 247), outline=(174, 174, 174), width=2)
    draw.text((card_x + 18, y + 28), "shown here", fill=(38, 95, 156), font=_font(18, bold=True))
    draw.multiline_text((card_x + 18, y + 64), allowed, fill=(36, 36, 36), font=body_font, spacing=5)
    draw.text((card_x + 18, y + 160), "open question", fill=(211, 116, 32), font=_font(18, bold=True))
    draw.multiline_text((card_x + 18, y + 196), not_proved, fill=(36, 36, 36), font=body_font, spacing=5)
    return y + lane_h


def _draw_claim_boundary_audit_strip(canvas: Image.Image, draw: ImageDraw.ImageDraw, *, y: int, h: int) -> int:
    x = MARGIN
    w = WIDTH - 2 * MARGIN
    gap = 18
    slot_w = 500
    tile_area_w = w - slot_w - gap
    title_font = _font(23, bold=True)
    note_font = _font(14)
    label_font = _font(12, bold=True)
    body_font = _font(13)

    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(252, 252, 252), outline=(174, 174, 174), width=2)
    draw.rectangle((x, y, x + w, y + 8), fill=(82, 82, 82))
    draw.text((x + 16, y + 18), "cross-check render audit strip", fill=(18, 18, 18), font=title_font)
    draw.text(
        (x + 16, y + 48),
        "additional source panels make the scope examples inspectable without adding a new result",
        fill=(72, 72, 72),
        font=note_font,
    )

    tile_gap = 10
    tile_cols = 5
    tile_rows = 3
    tile_w = (tile_area_w - 24 - (tile_cols - 1) * tile_gap) // tile_cols
    tile_h = (h - 116 - (tile_rows - 1) * tile_gap) // tile_rows
    tile_y0 = y + 82

    def paired_tile(original: Path, converted: Path, bbox: tuple[float, float, float, float]) -> Image.Image:
        half_gap = 6
        half_w = (tile_w - half_gap) // 2
        pair = Image.new("RGB", (tile_w, tile_h), (250, 250, 250))
        pair.paste(_fit_with_bbox(original, (half_w, tile_h), bbox), (0, 0))
        pair.paste(_fit_with_bbox(converted, (tile_w - half_w - half_gap, tile_h), bbox), (half_w + half_gap, 0))
        return pair

    tiles = [
        ("proxy MDL", _crop_fit(RENDER_SCENE_WIDE, (34, 90, 888, 470), (tile_w, tile_h))),
        ("proxy noMDL", _crop_fit(RENDER_SCENE_WIDE, (912, 90, 1767, 470), (tile_w, tile_h))),
        ("extended scene", _crop_fit(RENDER_SCENE_EXTENDED_OUT, (40, 790, 1760, 1540), (tile_w, tile_h))),
        ("backpack noMDL", _fit_with_bbox(VLM_BACKPACK_CONVERTED, (tile_w, tile_h), (207.811, 105.285, 376.441, 364.938))),
        ("bottle pair", paired_tile(VLM_BOTTLE_ORIGINAL, VLM_BOTTLE_CONVERTED, (230.385, 89.121, 369.378, 372.696))),
        ("cup noMDL", _fit_with_bbox(VLM_CUP_CONVERTED, (tile_w, tile_h), (183.338, 133.12, 416.662, 331.46))),
        ("coord atlas", _crop_fit(VLM_COORDINATE_PROTOCOL_OUT, (30, 82, 1770, 690), (tile_w, tile_h))),
        ("target guide", _crop_fit(GRSCENES_VLM_GUIDE_OUT, (30, 82, 1770, 690), (tile_w, tile_h))),
        ("covered material", _crop_fit(MATERIAL_BASELINE, (12, 55, 372, 174), (tile_w, tile_h))),
        ("clearcoat limit", _crop_fit(MATERIAL_SUPPLEMENTAL, (24, 62, 832, 258), (tile_w, tile_h))),
        ("procedural limit", _crop_fit(MATERIAL_SUPPLEMENTAL, (24, 340, 832, 535), (tile_w, tile_h))),
        ("nav atlas", _crop_fit(NAVIGATION_OUT, (40, 340, 1760, 1160), (tile_w, tile_h))),
        ("selected route", _crop_fit(NAV_SELECTED_CASE4, (0, 34, 1106, 430), (tile_w, tile_h))),
        ("0036 route", _crop_fit(NAV_0036_CASE4, (0, 34, 770, 430), (tile_w, tile_h))),
        ("route stills", _crop_fit(NAV_STILLS, (0, 140, 1106, 770), (tile_w, tile_h))),
    ]
    for idx, (label, image) in enumerate(tiles):
        col = idx % tile_cols
        row = idx // tile_cols
        xx = x + 12 + col * (tile_w + tile_gap)
        yy = tile_y0 + row * (tile_h + tile_gap)
        canvas.paste(image, (xx, yy))
        draw.rectangle((xx, yy, xx + tile_w, yy + tile_h), outline=(136, 136, 136), width=2)
        draw.rectangle((xx, yy, xx + tile_w, yy + 24), fill=(250, 250, 250), outline=(136, 136, 136), width=1)
        draw.text((xx + 7, yy + 5), label, fill=(28, 28, 28), font=label_font)

    slot_x = x + tile_area_w + gap
    slot_y = y + 82
    slot_h = h - 122
    draw.rounded_rectangle((slot_x, slot_y, x + w - 12, y + h - 16), radius=7, fill=(247, 247, 247), outline=(174, 174, 174), width=2)
    draw.text((slot_x + 14, slot_y + 14), "scope-check guide", fill=(18, 18, 18), font=title_font)
    draw.text((slot_x + 14, slot_y + 43), "orientation panel", fill=(78, 78, 78), font=note_font)
    slot = _fit(CLAIM_BOUNDARY_EXAMPLES_GATE_AI_SLOT, (slot_w - 36, min(282, slot_h - 118)), cover=False)
    canvas.paste(slot, (slot_x + 14, slot_y + 66))
    draw.rectangle((slot_x + 14, slot_y + 66, slot_x + 14 + slot.width, slot_y + 66 + slot.height), outline=(136, 136, 136), width=2)
    bullet_y = slot_y + 66 + slot.height + 12
    for idx, line in enumerate(["scoped results enter", "future tests required", "table context"]):
        yy = bullet_y + idx * 20
        draw.rectangle((slot_x + 18, yy + 4, slot_x + 28, yy + 14), fill=(0, 133, 100))
        draw.text((slot_x + 36, yy), line, fill=(48, 48, 48), font=body_font)
    return y + h


def build_claim_boundary_examples() -> None:
    height = 2320
    canvas = Image.new("RGB", (WIDTH, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(36, bold=True)
    note_font = _font(18)
    footer_font = _font(15)

    y = MARGIN
    draw.text((MARGIN, y), "Evaluation-scope examples", fill=(18, 18, 18), font=heading_font)
    y += 52
    draw.text(
        (MARGIN, y),
        "The same real render evidence can support a scoped result while leaving a stronger conclusion unproved.",
        fill=(64, 64, 64),
        font=note_font,
    )
    y += 62

    y = _draw_claim_boundary_example_lane(
        canvas,
        draw,
        y=y,
        index="1",
        title="proxy render\npair",
        cue="matched cameras\nand lighting",
        allowed="appearance is compared\nunder this frozen view",
        not_proved="semantic or task\npreservation in general",
        accent=(38, 95, 156),
        tiles=[
            ("MDL object", _crop_fit(RENDER_SCENE_WIDE, (34, 90, 888, 470), (270, 210))),
            ("noMDL object", _crop_fit(RENDER_SCENE_WIDE, (912, 90, 1767, 470), (270, 210))),
            ("scene pair", _crop_fit(RENDER_SCENE_WIDE, (34, 548, 1767, 884), (270, 210))),
        ],
    ) + 18
    y = _draw_claim_boundary_example_lane(
        canvas,
        draw,
        y=y,
        index="2",
        title="VLM target\nbox",
        cue="visible target\nand projected box",
        allowed="prompt-and-box\ncontract is auditable",
        not_proved="all targets, all VLMs,\nor open-ended language",
        accent=(0, 133, 100),
        tiles=[
            ("backpack", _fit_with_bbox(VLM_BACKPACK_ORIGINAL, (270, 210), (207.811, 105.285, 376.441, 364.938))),
            ("clock", _fit_with_bbox(VLM_CLOCK_ORIGINAL, (270, 210), (211.647, 107.436, 370.171, 360.234))),
            ("cup", _fit_with_bbox(VLM_CUP_ORIGINAL, (270, 210), (183.338, 133.12, 416.662, 331.46))),
        ],
    ) + 18
    y = _draw_claim_boundary_example_lane(
        canvas,
        draw,
        y=y,
        index="3",
        title="material\nmechanism",
        cue="covered bins plus\nselected limitations",
        allowed="scoped covered-bin\nevidence and limits",
        not_proved="population failure rates\nor procedural success",
        accent=(211, 116, 32),
        tiles=[
            ("covered", _crop_fit(MATERIAL_BASELINE, (12, 55, 372, 174), (270, 210))),
            ("clearcoat", _crop_fit(MATERIAL_SUPPLEMENTAL, (24, 62, 832, 258), (270, 210))),
            ("procedural", _crop_fit(MATERIAL_SUPPLEMENTAL, (24, 340, 284, 535), (270, 210))),
        ],
    ) + 18
    y = _draw_claim_boundary_example_lane(
        canvas,
        draw,
        y=y,
        index="4",
        title="navigation\nmedia",
        cue="official-scene run\nand selected stills",
        allowed="stack can be exercised\nunder frozen conditions",
        not_proved="broad embodied\nnavigation robustness",
        accent=(85, 85, 85),
        tiles=[
            ("rollout", _crop_fit(NAV_STILLS, (0, 140, 1106, 770), (270, 210))),
            ("0036/0066", _crop_fit(NAV_0036_MAIN, (390, 108, 1738, 790), (270, 210))),
            ("media atlas", _crop_fit(NAVIGATION_OUT, (40, 340, 1760, 1160), (270, 210))),
        ],
    ) + 22

    y = _draw_claim_boundary_audit_strip(canvas, draw, y=y, h=620) + 22

    draw.rectangle((MARGIN, y, WIDTH - MARGIN, height - MARGIN), fill=(252, 252, 252), outline=(176, 176, 176), width=2)
    draw.multiline_text(
        (MARGIN + 24, y + 22),
        "Reading rule: this page is a scope check built from tracked render panels.",
        fill=(48, 48, 48),
        font=footer_font,
        spacing=5,
    )
    footer_tiles = [
        ("proxy", _crop_fit(RENDER_SCENE_EXTENDED_OUT, (40, 790, 1760, 1540), (230, 86))),
        ("target", _fit_with_bbox(VLM_BACKPACK_CONVERTED, (230, 86), (207.811, 105.285, 376.441, 364.938))),
        ("material", _crop_fit(MATERIAL_SUPPLEMENTAL, (24, 340, 284, 535), (230, 86))),
        ("nav", _crop_fit(NAV_SELECTED_CASE4, (0, 34, 1106, 430), (230, 86))),
        ("held out", _crop_fit(NAV_0036_CASE4, (0, 34, 770, 430), (230, 86))),
        ("record", _crop_fit(VLM_COORDINATE_PROTOCOL_OUT, (30, 82, 1770, 690), (230, 86))),
    ]
    tile_gap = 14
    tile_w = (WIDTH - 2 * MARGIN - 48 - (len(footer_tiles) - 1) * tile_gap) // len(footer_tiles)
    tile_h = max(58, height - MARGIN - (y + 72))
    tile_y = y + 62
    small_font = _font(12, bold=True)
    for idx, (label, tile) in enumerate(footer_tiles):
        xx = MARGIN + 24 + idx * (tile_w + tile_gap)
        image = ImageOps.fit(tile, (tile_w, tile_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        canvas.paste(image, (xx, tile_y))
        draw.rectangle((xx, tile_y, xx + tile_w, tile_y + tile_h), outline=(138, 138, 138), width=2)
        draw.rectangle((xx, tile_y, xx + tile_w, tile_y + 22), fill=(238, 238, 238), outline=(138, 138, 138), width=1)
        draw.text((xx + 6, tile_y + 4), label, fill=(28, 28, 28), font=small_font)

    CLAIM_BOUNDARY_EXAMPLES_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(CLAIM_BOUNDARY_EXAMPLES_OUT)
    print(CLAIM_BOUNDARY_EXAMPLES_OUT)


def _draw_registry_gate_card(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    evidence: str,
    boundary: str,
    image: Image.Image,
    accent: tuple[int, int, int],
) -> None:
    title_font = _font(18, bold=True)
    body_font = _font(12)
    small_font = _font(12, bold=True)
    image_h = 270
    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(252, 252, 252), outline=(172, 172, 172), width=2)
    draw.rectangle((x, y, x + w, y + 8), fill=accent)
    draw.text((x + 14, y + 22), title, fill=(20, 20, 20), font=title_font)
    draw.multiline_text((x + 14, y + 52), evidence, fill=(62, 62, 62), font=body_font, spacing=3)
    image_y = y + 112
    image_slot = (w - 28, image_h)
    contained = ImageOps.contain(image, image_slot, method=Image.Resampling.LANCZOS)
    tile = Image.new("RGB", image_slot, (250, 250, 250))
    tile.paste(contained, ((image_slot[0] - contained.width) // 2, (image_slot[1] - contained.height) // 2))
    canvas.paste(tile, (x + 14, image_y))
    draw.rectangle((x + 14, image_y, x + w - 14, image_y + image_h), outline=(142, 142, 142), width=2)
    draw.rounded_rectangle((x + 14, y + h - 102, x + w - 14, y + h - 18), radius=6, fill=(248, 250, 252), outline=accent, width=2)
    draw.text((x + 25, y + h - 92), "not tested", fill=accent, font=small_font)
    draw.multiline_text((x + 25, y + h - 67), boundary, fill=(45, 45, 45), font=body_font, spacing=1)


def build_evidence_gate_registry_companion() -> None:
    height = 1240
    canvas = Image.new("RGB", (WIDTH, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(34, bold=True)
    note_font = _font(16)
    footer_font = _font(14)

    y = 34
    draw.text((MARGIN, y), "Evaluation scope companion", fill=(18, 18, 18), font=heading_font)
    draw.text(
        (MARGIN, y + 46),
        "The table rows below map each evaluation check to source visual evidence.",
        fill=(66, 66, 66),
        font=note_font,
    )

    card_y = 104
    card_h = 500
    gap = 16
    card_w = 282
    ai_w = WIDTH - 2 * MARGIN - 4 * card_w - 4 * gap
    cards = [
        (
            "Proxy similarity",
            "matched object/scene\nrender pairs",
            "visual proxy only;\ntask checks separate",
            _crop_contain(RENDER_SCENE_WIDE, (34, 90, 1767, 884), (360, 250)),
            (38, 95, 156),
        ),
        (
            "VLM grounding",
            "target box and point\ncontract",
            "fixed prompt;\nselected targets",
            _fit_with_bbox(VLM_BACKPACK_ORIGINAL, (360, 250), (207.811, 105.285, 376.441, 364.938)),
            (0, 133, 100),
        ),
        (
            "Material cases",
            "covered bins plus\nselected limits",
            "selected cases;\nnot failure rate",
            _crop_contain(MATERIAL_BASELINE, (12, 54, 372, 174), (360, 250)),
            (112, 130, 70),
        ),
        (
            "Stack entry",
            "official-scene run\nand still panels",
            "frozen run;\nnot robustness",
            _crop_contain(NAV_STILLS, (0, 140, 1106, 770), (360, 250)),
            (85, 85, 85),
        ),
    ]

    x = MARGIN
    for title, evidence, boundary, image, accent in cards:
        _draw_registry_gate_card(
            canvas,
            draw,
            x=x,
            y=card_y,
            w=card_w,
            h=card_h,
            title=title,
            evidence=evidence,
            boundary=boundary,
            image=image,
            accent=accent,
        )
        x += card_w + gap

    draw.rounded_rectangle((x, card_y, x + ai_w, card_y + card_h), radius=8, fill=(252, 252, 252), outline=(172, 172, 172), width=2)
    draw.rectangle((x, card_y, x + ai_w, card_y + 8), fill=(46, 108, 176))
    reader_gate = _fit(EVIDENCE_SCOPE_READER_V6_AI_SLOT, (ai_w - 36, card_h - 42), cover=False)
    canvas.paste(reader_gate, (x + 18, card_y + 22))
    draw.rectangle((x + 18, card_y + 22, x + ai_w - 18, card_y + card_h - 20), outline=(142, 142, 142), width=2)

    strip_y = card_y + card_h + 20
    _draw_opener_band(
        canvas,
        draw,
        y=strip_y,
        title="source evidence thumbnails",
        tiles=[
            ("proxy scene", _crop_contain(RENDER_SCENE_WIDE, (34, 430, 1767, 884), (560, 210))),
            ("VLM original", _fit_with_bbox(VLM_BACKPACK_ORIGINAL, (560, 210), (207.811, 105.285, 376.441, 364.938))),
            ("VLM noMDL", _fit_with_bbox(VLM_BACKPACK_CONVERTED, (560, 210), (207.811, 105.285, 376.441, 364.938))),
            ("material bins", _crop_contain(MATERIAL_BASELINE, (12, 54, 372, 174), (560, 210))),
            ("material limits", _crop_contain(MATERIAL_SUPPLEMENTAL, (24, 340, 284, 535), (560, 210))),
            ("InternNav", _crop_contain(NAV_0036_MAIN, (390, 108, 1738, 790), (560, 210))),
        ],
        band_h=570,
        columns=3,
        contain_tiles=True,
    )

    draw.text(
        (MARGIN, height - 38),
        "The strip makes the table rows inspectable.",
        fill=(70, 70, 70),
        font=footer_font,
    )

    EVIDENCE_GATE_REGISTRY_COMPANION_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(EVIDENCE_GATE_REGISTRY_COMPANION_OUT)
    print(EVIDENCE_GATE_REGISTRY_COMPANION_OUT)


def _draw_opener_band(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
    title: str,
    tiles: list[tuple[str, Image.Image]],
    band_h: int = 230,
    columns: int | None = None,
    contain_tiles: bool = False,
) -> int:
    x = 34
    w = canvas.width - 68
    tile_gap = 10
    row_gap = 10
    title_font = _font(19, bold=True)
    label_font = _font(12, bold=True)
    label_h = 22
    tile_y = y + 40
    columns = columns or len(tiles)
    rows = (len(tiles) + columns - 1) // columns
    tile_area_h = band_h - 58
    tile_h = (tile_area_h - row_gap * (rows - 1)) // rows
    tile_w = (w - tile_gap * (columns - 1)) // columns

    draw.rectangle((x, y, x + w, y + band_h), fill=(252, 252, 252), outline=(178, 178, 178), width=2)
    draw.text((x + 14, y + 12), title, fill=(22, 22, 22), font=title_font)
    for idx, (label, tile) in enumerate(tiles):
        row = idx // columns
        col = idx % columns
        tile_x = x + col * (tile_w + tile_gap)
        tile_top = tile_y + row * (tile_h + row_gap)
        if contain_tiles:
            image_area = (tile_w, tile_h - label_h)
            image = ImageOps.contain(tile, image_area, method=Image.Resampling.LANCZOS)
            tile_canvas = Image.new("RGB", (tile_w, tile_h), (250, 250, 250))
            tile_canvas.paste(image, ((tile_w - image.width) // 2, label_h + (image_area[1] - image.height) // 2))
        else:
            tile_canvas = ImageOps.fit(tile, (tile_w, tile_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        canvas.paste(tile_canvas, (tile_x, tile_top))
        draw.rectangle((tile_x, tile_top, tile_x + tile_w, tile_top + tile_h), outline=(135, 135, 135), width=2)
        draw.rectangle((tile_x, tile_top, tile_x + tile_w, tile_top + label_h), fill=(248, 248, 248), outline=(135, 135, 135), width=1)
        draw.text((tile_x + 6, tile_top + 4), label, fill=(30, 30, 30), font=label_font)
    return y + band_h


def _draw_extended_render_pair_row(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
    title: str,
    note: str,
    original: Image.Image,
    converted: Image.Image,
) -> int:
    row_label_h = 30
    image_h = original.height
    cell_gap = 26
    cell_w = (WIDTH - 2 * MARGIN - cell_gap) // 2
    title_font = _font(22, bold=True)
    note_font = _font(14)
    label_font = _font(15, bold=True)

    draw.text((MARGIN, y), title, fill=(22, 22, 22), font=title_font)
    draw.text((MARGIN + 390, y + 5), note, fill=(70, 70, 70), font=note_font)
    y += row_label_h
    for idx, (label, image) in enumerate((("original MDL", original), ("converted noMDL", converted))):
        x = MARGIN + idx * (cell_w + cell_gap)
        draw.rectangle((x, y, x + cell_w, y + 24), fill=(246, 248, 250), outline=(150, 150, 150), width=1)
        draw.text((x + 8, y + 5), label, fill=(35, 35, 35), font=label_font)
        canvas.paste(image, (x, y + 24))
        draw.rectangle((x, y + 24, x + cell_w, y + 24 + image_h), outline=(150, 150, 150), width=2)
    return y + 24 + image_h


def _proxy_context_detail_pair(
    front_path: Path,
    detail_path: Path,
    size: tuple[int, int],
) -> Image.Image:
    """Build one condition tile with full context plus a contained detail view."""
    w, h = size
    gap = 14
    label_h = 26
    context_w = int((w - gap) * 0.43)
    detail_w = w - gap - context_w
    tile = Image.new("RGB", size, (240, 240, 240))
    draw = ImageDraw.Draw(tile)
    label_font = _font(14, bold=True)

    panels = (
        ("full context", front_path, 0, context_w),
        ("material detail", detail_path, context_w + gap, detail_w),
    )
    for label, path, x, panel_w in panels:
        draw.rectangle((x, 0, x + panel_w, label_h), fill=(248, 249, 250), outline=(168, 168, 168), width=1)
        draw.text((x + 8, 5), label, fill=(45, 45, 45), font=label_font)
        image = _fit(path, (panel_w, h - label_h), cover=False)
        tile.paste(image, (x, label_h))
        draw.rectangle((x, label_h, x + panel_w, h), outline=(168, 168, 168), width=1)
    return tile


def build_render_scene_evidence_extended() -> None:
    width = 1800
    cell_gap = 26
    cell_w = (width - 2 * MARGIN - cell_gap) // 2
    image_h = 330
    row_gap = 18
    title_block_h = 78
    row_h = 30 + 24 + image_h
    height = MARGIN + title_block_h + 4 * row_h + 3 * row_gap + MARGIN
    canvas = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(32, bold=True)
    note_font = _font(18)

    y = MARGIN
    draw.text((MARGIN, y), "Extended render-scene evidence view", fill=(18, 18, 18), font=heading_font)
    y += 42
    draw.text(
        (MARGIN, y),
        "Supplement-only expansion of tracked proxy and GRScenes render pairs; no generated evidence is used.",
        fill=(66, 66, 66),
        font=note_font,
    )
    y += 36

    y = _draw_extended_render_pair_row(
        canvas,
        draw,
        y=y,
        title="Proxy object pair #0011",
        note="Proxy object full-context + material-detail pair",
        original=_proxy_context_detail_pair(PROXY_OBJECT_0011_A_FRONT, PROXY_OBJECT_0011_A, (cell_w, image_h)),
        converted=_proxy_context_detail_pair(PROXY_OBJECT_0011_B_FRONT, PROXY_OBJECT_0011_B, (cell_w, image_h)),
    ) + row_gap
    y = _draw_extended_render_pair_row(
        canvas,
        draw,
        y=y,
        title="Proxy object pair #0023",
        note="Proxy object full-context + material-detail pair",
        original=_proxy_context_detail_pair(PROXY_OBJECT_0023_A_FRONT, PROXY_OBJECT_0023_A, (cell_w, image_h)),
        converted=_proxy_context_detail_pair(PROXY_OBJECT_0023_B_FRONT, PROXY_OBJECT_0023_B, (cell_w, image_h)),
    ) + row_gap
    y = _draw_extended_render_pair_row(
        canvas,
        draw,
        y=y,
        title="GRScenes scene pair view 1",
        note="matched scene camera carried into the render-evidence chain",
        original=_fit(GRSCENES_ORBIT_MDL_01, (cell_w, image_h), cover=True),
        converted=_fit(GRSCENES_ORBIT_NOMDL_01, (cell_w, image_h), cover=True),
    ) + row_gap
    _draw_extended_render_pair_row(
        canvas,
        draw,
        y=y,
        title="GRScenes scene pair view 2",
        note="second scene camera before task-specific VLM panels",
        original=_fit(GRSCENES_ORBIT_MDL_03, (cell_w, image_h), cover=True),
        converted=_fit(GRSCENES_ORBIT_NOMDL_03, (cell_w, image_h), cover=True),
    )

    RENDER_SCENE_EXTENDED_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(RENDER_SCENE_EXTENDED_OUT)
    print(RENDER_SCENE_EXTENDED_OUT)


def build_render_atlas_opener() -> None:
    width = 1800
    height = 1330
    canvas = Image.new("RGB", (width, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(32, bold=True)
    note_font = _font(18)
    footer_font = _font(16)

    y = 30
    draw.text((34, y), "Render Evidence Atlas opener", fill=(18, 18, 18), font=heading_font)
    y += 46
    draw.text(
        (34, y),
        "Compact index built from tracked render panels; detailed full-page figures follow.",
        fill=(62, 62, 62),
        font=note_font,
    )
    y += 50

    y = _draw_opener_band(
        canvas,
        draw,
        y=y,
        title="Proxy render pairs",
        tiles=[
            ("0011 MDL", _crop_fit(RENDER_PAIRS, (72, 75, 702, 546), (220, 170))),
            ("0011 noMDL", _crop_fit(RENDER_PAIRS, (726, 75, 1354, 546), (220, 170))),
            ("0004 MDL", _crop_fit(RENDER_PAIRS, (72, 615, 702, 1085), (220, 170))),
            ("0004 noMDL", _crop_fit(RENDER_PAIRS, (726, 615, 1354, 1085), (220, 170))),
        ],
        band_h=280,
    ) + 12
    y = _draw_opener_band(
        canvas,
        draw,
        y=y,
        title="GRScenes target views",
        tiles=[
            ("backpack", _fit_with_bbox(VLM_BACKPACK_ORIGINAL, (220, 170), (207.811, 105.285, 376.441, 364.938))),
            ("clock", _fit_with_bbox(VLM_CLOCK_ORIGINAL, (220, 170), (211.647, 107.436, 370.171, 360.234))),
            ("bottle", _fit_with_bbox(VLM_BOTTLE_ORIGINAL, (220, 170), (230.385, 89.121, 369.378, 372.696))),
            ("cup", _fit_with_bbox(VLM_CUP_ORIGINAL, (220, 170), (183.338, 133.12, 416.662, 331.46))),
        ],
        band_h=280,
    ) + 12
    y = _draw_opener_band(
        canvas,
        draw,
        y=y,
        title="Material comparison",
        tiles=[
            ("covered", _crop_fit(MATERIAL_BASELINE, (12, 55, 372, 174), (220, 170))),
            ("emission", _crop_fit(MATERIAL_BASELINE, (382, 216, 742, 337), (220, 170))),
            ("clearcoat", _crop_fit(MATERIAL_SUPPLEMENTAL, (24, 62, 284, 258), (220, 170))),
            ("procedural", _crop_fit(MATERIAL_SUPPLEMENTAL, (24, 340, 284, 535), (220, 170))),
        ],
        band_h=280,
    ) + 12
    y = _draw_opener_band(
        canvas,
        draw,
        y=y,
        title="InternNav media",
        tiles=[
            ("rollout", _crop_fit(NAV_STILLS, (0, 140, 1106, 770), (220, 170))),
            ("0036/0066", _crop_fit(NAV_0036_MAIN, (390, 108, 1738, 790), (220, 170))),
            ("selected", _crop_fit(NAV_SELECTED_CASE, (0, 42, 1106, 360), (220, 170))),
            ("0036 case", _crop_fit(NAV_0036_CASE, (0, 34, 770, 338), (220, 170))),
        ],
        band_h=280,
    ) + 12

    draw.text(
        (34, y + 4),
        "Reading note: this opener is an index over source evidence, table context only.",
        fill=(70, 70, 70),
        font=footer_font,
    )

    RENDER_ATLAS_OPENER_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(RENDER_ATLAS_OPENER_OUT)
    print(RENDER_ATLAS_OPENER_OUT)


def _metric_boundary_pair_tile(
    original: Path,
    converted: Path,
    bbox: tuple[float, float, float, float],
    size: tuple[int, int],
    case_label: str,
) -> Image.Image:
    tile = Image.new("RGB", size, (250, 250, 250))
    tile_draw = ImageDraw.Draw(tile)
    label_font = _font(12, bold=True)
    case_font = _font(13, bold=True)
    label_h = 18
    case_h = 20
    gap = 8
    image_y = label_h + case_h
    image_w = (size[0] - gap) // 2
    image_h = size[1] - image_y

    tile_draw.rectangle((0, 0, size[0], case_h), fill=(244, 248, 250), outline=(135, 135, 135))
    tile_draw.text((8, 4), case_label, fill=(35, 35, 35), font=case_font)
    for idx, (label, path) in enumerate((("original", original), ("noMDL", converted))):
        x = idx * (image_w + gap)
        tile_draw.rectangle((x, case_h, x + image_w, image_y), fill=(248, 248, 248))
        tile_draw.text((x + 7, case_h + 4), label, fill=(38, 95, 156) if idx else (70, 70, 70), font=label_font)
        image = _fit_with_protocol_overlay(path, (image_w, image_h), bbox)
        image = ImageEnhance.Color(image).enhance(0.75)
        tile.paste(image, (x, image_y))
        tile_draw.rectangle((x, image_y, x + image_w, image_y + image_h), outline=(128, 128, 128), width=2)

    return tile


def _draw_metric_boundary_lens_strip(canvas: Image.Image, draw: ImageDraw.ImageDraw, *, y: int) -> int:
    x = MARGIN
    w = WIDTH - 2 * MARGIN
    strip_h = 210
    pad = 14
    title_font = _font(19, bold=True)
    note_font = _font(14)
    draw.rectangle((x, y, x + w, y + strip_h), fill=(252, 252, 252), outline=(172, 172, 172), width=2)
    draw.text((x + pad, y + 12), "metric-scope lens strip", fill=(22, 22, 22), font=title_font)
    draw.text(
        (x + 310, y + 15),
        "orientation panel; paired crops are source target-view renders.",
        fill=(72, 72, 72),
        font=note_font,
    )

    content_y = y + 42
    content_h = strip_h - 54
    gap = 12
    lens_w = 480
    pair_w = (w - 2 * pad - lens_w - 3 * gap) // 3
    lens = _fit(METRIC_BOUNDARY_LENS_AI_SLOT, (lens_w, content_h), cover=False)
    lens_x = x + pad
    canvas.paste(lens, (lens_x, content_y))
    draw.rectangle((lens_x, content_y, lens_x + lens_w, content_y + content_h), outline=(128, 128, 128), width=2)

    pairs = [
        (
            "cup view B",
            VLM_CUP_ALT_ORIGINAL,
            VLM_CUP_ALT_CONVERTED,
            (197.137, 107.89, 402.863, 372.325),
        ),
        (
            "faucet",
            VLM_FAUCET_ORIGINAL,
            VLM_FAUCET_CONVERTED,
            (215.154, 118.861, 407.249, 356.885),
        ),
        (
            "picture",
            VLM_PICTURE_ORIGINAL,
            VLM_PICTURE_CONVERTED,
            (240.087, 100.65, 374.808, 360.903),
        ),
    ]
    for idx, (case_label, original, converted, bbox) in enumerate(pairs):
        pair_x = lens_x + lens_w + gap + idx * (pair_w + gap)
        tile = _metric_boundary_pair_tile(original, converted, bbox, (pair_w, content_h), case_label)
        canvas.paste(tile, (pair_x, content_y))
        draw.rectangle((pair_x, content_y, pair_x + pair_w, content_y + content_h), outline=(128, 128, 128), width=2)

    return y + strip_h


def _draw_metric_boundary_lane(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
    index: str,
    family: str,
    measures: str,
    boundary: str,
    tiles: list[tuple[str, Image.Image]],
    lane_h: int,
) -> int:
    label_w = 270
    boundary_w = 270
    x = MARGIN
    w = WIDTH - 2 * MARGIN
    tile_x = x + label_w + GAP
    tile_w_total = w - label_w - boundary_w - 2 * GAP
    tile_gap = 12
    tile_w = (tile_w_total - tile_gap * (len(tiles) - 1)) // len(tiles)
    tile_h = lane_h - 56
    label_font = _font(22, bold=True)
    small_font = _font(15)
    index_font = _font(18, bold=True)
    boundary_font = _font(18, bold=True)

    draw.rectangle((x, y, x + w, y + lane_h), fill=(252, 252, 252), outline=(172, 172, 172), width=2)
    draw.rectangle((x + 18, y + 22, x + 52, y + 56), outline=(42, 42, 42), width=2)
    draw.text((x + 30, y + 26), index, fill=(20, 20, 20), font=index_font)
    draw.multiline_text((x + 68, y + 20), family, fill=(18, 18, 18), font=label_font, spacing=4)
    draw.multiline_text((x + 68, y + 84), measures, fill=(72, 72, 72), font=small_font, spacing=5)

    image_y = y + 34
    for idx, (tile_label, tile) in enumerate(tiles):
        xx = tile_x + idx * (tile_w + tile_gap)
        image = ImageOps.fit(tile, (tile_w, tile_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        canvas.paste(image, (xx, image_y))
        draw.rectangle((xx, image_y, xx + tile_w, image_y + tile_h), outline=(140, 140, 140), width=2)
        draw.rectangle((xx, image_y, xx + tile_w, image_y + 24), fill=(248, 248, 248), outline=(140, 140, 140), width=1)
        draw.text((xx + 7, image_y + 5), tile_label, fill=(30, 30, 30), font=_font(12, bold=True))

    bx = x + w - boundary_w
    draw.rectangle((bx, y, bx + boundary_w, y + lane_h), fill=(248, 248, 248), outline=(172, 172, 172), width=2)
    draw.text((bx + 18, y + 28), "scope", fill=(38, 95, 156), font=boundary_font)
    draw.multiline_text((bx + 18, y + 66), boundary, fill=(45, 45, 45), font=small_font, spacing=6)
    return y + lane_h


def build_metric_boundary_bridge() -> None:
    height = 1250
    canvas = Image.new("RGB", (WIDTH, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(34, bold=True)
    note_font = _font(18)
    footer_font = _font(15)

    y = 30
    draw.text((MARGIN, y), "Metric scope metric bridge", fill=(18, 18, 18), font=heading_font)
    y += 42
    draw.text(
        (MARGIN, y),
        "Each metric family is tied to the visible evidence and setting it measures.",
        fill=(64, 64, 64),
        font=note_font,
    )
    y += 36

    y = _draw_metric_boundary_lens_strip(canvas, draw, y=y) + 8

    y = _draw_metric_boundary_lane(
        canvas,
        draw,
        y=y,
        index="1",
        family="Proxy render\nmetrics",
        measures="PSNR / SSIM /\nCLIP / DINOv2",
        boundary="appearance proxy only;\ntask checks separate",
        lane_h=220,
        tiles=[
            ("object MDL", _crop_fit(RENDER_SCENE_WIDE, (34, 90, 888, 470), (250, 190))),
            ("object noMDL", _crop_fit(RENDER_SCENE_WIDE, (912, 90, 1767, 470), (250, 190))),
            ("scene MDL", _crop_fit(RENDER_SCENE_WIDE, (34, 548, 888, 884), (250, 190))),
            ("scene noMDL", _crop_fit(RENDER_SCENE_WIDE, (912, 548, 1767, 884), (250, 190))),
        ],
    ) + 8
    y = _draw_metric_boundary_lane(
        canvas,
        draw,
        y=y,
        index="2",
        family="VLM point-in-box\ngrounding",
        measures="answer hit /\npoint hit /\ncoordinate frame",
        boundary="valid under the fixed\nprompt and box contract",
        lane_h=220,
        tiles=[
            ("backpack", _fit_with_bbox(VLM_BACKPACK_ORIGINAL, (250, 190), (207.811, 105.285, 376.441, 364.938))),
            ("clock", _fit_with_bbox(VLM_CLOCK_ORIGINAL, (250, 190), (211.647, 107.436, 370.171, 360.234))),
            ("bottle", _fit_with_bbox(VLM_BOTTLE_ORIGINAL, (250, 190), (230.385, 89.121, 369.378, 372.696))),
            ("cup", _fit_with_bbox(VLM_CUP_ORIGINAL, (250, 190), (183.338, 133.12, 416.662, 331.46))),
        ],
    ) + 8
    y = _draw_metric_boundary_lane(
        canvas,
        draw,
        y=y,
        index="3",
        family="Material mechanism\ndiagnostics",
        measures="covered bins /\nselected limits",
        boundary="selected material cases;\nselected case only",
        lane_h=220,
        tiles=[
            ("covered", _crop_fit(MATERIAL_BASELINE, (12, 55, 372, 174), (250, 190))),
            ("emission", _crop_fit(MATERIAL_BASELINE, (382, 216, 742, 337), (250, 190))),
            ("clearcoat", _crop_fit(MATERIAL_SUPPLEMENTAL, (24, 62, 284, 258), (250, 190))),
            ("procedural", _crop_fit(MATERIAL_SUPPLEMENTAL, (24, 340, 284, 535), (250, 190))),
        ],
    ) + 8
    y = _draw_metric_boundary_lane(
        canvas,
        draw,
        y=y,
        index="4",
        family="Navigation\nmetrics",
        measures="SR / NE / SPL /\ntrajectory length",
        boundary="official-scene run;\nselected stills are qualitative",
        lane_h=220,
        tiles=[
            ("rollout", _crop_fit(NAV_STILLS, (0, 140, 1106, 770), (250, 190))),
            ("0036/0066", _crop_fit(NAV_0036_MAIN, (390, 108, 1738, 790), (250, 190))),
            ("selected", _crop_fit(NAV_SELECTED_CASE, (0, 42, 1106, 360), (250, 190))),
            ("0036 case", _crop_fit(NAV_0036_CASE, (0, 34, 770, 338), (250, 190))),
        ],
    ) + 4

    draw.text(
        (MARGIN, y),
        "Reading rule: similar-looking renders, correct VLM points, material-case panels, and successful routes answer different questions.",
        fill=(70, 70, 70),
        font=footer_font,
    )

    METRIC_BOUNDARY_BRIDGE_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(METRIC_BOUNDARY_BRIDGE_OUT)
    print(METRIC_BOUNDARY_BRIDGE_OUT)


def _draw_proxy_metric_card(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    subtitle: str,
    image_a: Image.Image,
    image_b: Image.Image,
    metric_lines: list[str],
    boundary: str,
    accent: tuple[int, int, int],
) -> None:
    title_font = _font(20, bold=True)
    body_font = _font(13)
    small_font = _font(12, bold=True)
    image_gap = 10
    image_y = y + 102
    image_h = min(430, h - 290)
    image_w = (w - 36 - image_gap) // 2

    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(252, 252, 252), outline=(174, 174, 174), width=2)
    draw.rectangle((x, y, x + w, y + 8), fill=accent)
    draw.text((x + 16, y + 20), title, fill=(20, 20, 20), font=title_font)
    draw.multiline_text((x + 16, y + 50), subtitle, fill=(68, 68, 68), font=body_font, spacing=3)

    for idx, (label, image) in enumerate((("Original MDL", image_a), ("noMDL", image_b))):
        xx = x + 16 + idx * (image_w + image_gap)
        draw.text((xx, image_y - 22), label, fill=(38, 95, 156), font=_font(12, bold=True))
        fitted = ImageOps.fit(image, (image_w, image_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        canvas.paste(fitted, (xx, image_y))
        draw.rectangle((xx, image_y, xx + image_w, image_y + image_h), outline=(140, 140, 140), width=2)

    chip_y = y + h - 168
    for idx, line in enumerate(metric_lines):
        yy = chip_y + idx * 30
        draw.rounded_rectangle((x + 16, yy, x + w - 16, yy + 25), radius=5, fill=(247, 250, 252), outline=accent, width=1)
        draw.text((x + 28, yy + 5), line, fill=(45, 45, 45), font=body_font)
    footer_y = y + h - 38
    draw.rounded_rectangle((x + 16, footer_y, x + w - 16, y + h - 12), radius=6, fill=(248, 251, 254), outline=accent, width=1)
    draw.text((x + 28, footer_y + 6), boundary, fill=accent, font=small_font)


def _draw_proxy_metric_lens_card(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
) -> None:
    title_font = _font(20, bold=True)
    body_font = _font(13)
    accent = (40, 96, 168)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(252, 252, 252), outline=(174, 174, 174), width=2)
    draw.text((x + 18, y + 18), "proxy-metric axis", fill=(20, 20, 20), font=title_font)
    draw.text((x + 18, y + 48), "orientation panel", fill=(76, 76, 76), font=body_font)
    image_h = 400
    image = _fit(PROXY_METRIC_AXIS_AI_SLOT, (w - 36, image_h), cover=False)
    canvas.paste(image, (x + 18, y + 78))
    draw.rectangle((x + 18, y + 78, x + w - 18, y + 78 + image_h), outline=(140, 140, 140), width=2)

    bullets = [
        "pixel proxy",
        "structure proxy",
        "feature proxy",
        "task checks separate",
    ]
    bullet_y = y + 492
    for idx, line in enumerate(bullets):
        yy = bullet_y + idx * 30
        draw.ellipse((x + 22, yy + 5, x + 34, yy + 17), fill=accent)
        draw.text((x + 48, yy), line, fill=(45, 45, 45), font=_font(13, bold=True))

    draw.rounded_rectangle((x + 18, y + h - 48, x + w - 18, y + h - 14), radius=6, fill=(246, 250, 255), outline=accent, width=2)
    draw.text((x + 34, y + h - 39), "table context only", fill=accent, font=body_font)


def build_proxy_metric_derivation_companion() -> None:
    width = 1800
    height = 1260
    canvas = Image.new("RGB", (width, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(32, bold=True)
    note_font = _font(16)
    footer_font = _font(12)

    y = 34
    draw.text((MARGIN, y), "Proxy metric derivation companion", fill=(18, 18, 18), font=heading_font)
    y += 44
    draw.text(
        (MARGIN, y),
        "source paired renders anchor the PSNR, SSIM, and feature-similarity equations before later task-level checks.",
        fill=(66, 66, 66),
        font=note_font,
    )

    body_y = 122
    card_gap = 16
    right_w = 430
    left_w = width - 2 * MARGIN - right_w - card_gap
    card_w = (left_w - card_gap) // 2
    card_h = 720
    _draw_proxy_metric_card(
        canvas,
        draw,
        x=MARGIN,
        y=body_y,
        w=card_w,
        h=card_h,
        title="object render pair",
        subtitle="matched camera and lighting\nbefore pixel-level proxy scores",
        image_a=_crop_fit(RENDER_SCENE_WIDE, (34, 90, 888, 470), (420, 255)),
        image_b=_crop_fit(RENDER_SCENE_WIDE, (912, 90, 1767, 470), (420, 255)),
        metric_lines=["MSE then PSNR", "local windows for SSIM", "same object/view only", "pixel proxy scope"],
        boundary="appearance proxy only",
        accent=(40, 96, 168),
    )
    _draw_proxy_metric_card(
        canvas,
        draw,
        x=MARGIN + card_w + card_gap,
        y=body_y,
        w=card_w,
        h=card_h,
        title="scene render pair",
        subtitle="larger context shows texture and\nlayout preserved under the pair",
        image_a=_crop_fit(RENDER_SCENE_WIDE, (34, 548, 888, 884), (420, 300)),
        image_b=_crop_fit(RENDER_SCENE_WIDE, (912, 548, 1767, 884), (420, 300)),
        metric_lines=["CLIP/DINO cosine", "global feature proxy", "layout/context proxy", "target grounding checked separately"],
        boundary="downstream checks separate",
        accent=(0, 133, 100),
    )
    _draw_proxy_metric_lens_card(
        canvas,
        draw,
        x=MARGIN + left_w + card_gap,
        y=body_y,
        w=right_w,
        h=card_h,
    )

    strip_y = body_y + card_h + 18
    _draw_opener_band(
        canvas,
        draw,
        y=strip_y,
        title="source proxy render ladder",
        tiles=[
            ("0011 MDL", _crop_fit(RENDER_PAIRS, (72, 75, 702, 546), (300, 230))),
            ("0011 noMDL", _crop_fit(RENDER_PAIRS, (726, 75, 1354, 546), (300, 230))),
            ("scene MDL", _crop_fit(RENDER_SCENE_WIDE, (34, 548, 888, 884), (300, 230))),
            ("scene noMDL", _crop_fit(RENDER_SCENE_WIDE, (912, 548, 1767, 884), (300, 230))),
            ("backpack pair", _first_page_pair_tile(VLM_BACKPACK_Z19_ORIGINAL, VLM_BACKPACK_Z19_CONVERTED, (300, 230))),
            ("clock pair", _first_page_pair_tile(VLM_CLOCK_Z19_ORIGINAL, VLM_CLOCK_Z19_CONVERTED, (300, 230))),
            ("atlas pair", _crop_fit(SUPPLEMENT_RENDER_ATLAS, (70, 630, 1710, 1120), (300, 230))),
        ],
        band_h=320,
    )
    draw.text(
        (MARGIN, height - 28),
        "Reading note: this companion explains proxy equations using source render pairs; it is proxy-equation context.",
        fill=(82, 82, 82),
        font=footer_font,
    )

    PROXY_METRIC_DERIVATION_COMPANION_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(PROXY_METRIC_DERIVATION_COMPANION_OUT)
    print(PROXY_METRIC_DERIVATION_COMPANION_OUT)


def _draw_metric_contract_gate(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    accent: tuple[int, int, int],
    title: str,
    bullets: list[str],
    slot_path: Path = METRIC_CONTRACT_GATE_AI_SLOT,
) -> None:
    title_font = _font(20, bold=True)
    body_font = _font(13)
    bullet_font = _font(14, bold=True)
    image_h = 230
    image = _fit(slot_path, (w - 34, image_h), cover=False)

    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(252, 252, 252), outline=(178, 178, 178), width=2)
    draw.text((x + 17, y + 14), title, fill=(20, 20, 20), font=title_font)
    draw.text((x + 17, y + 42), "orientation panel", fill=(82, 82, 82), font=body_font)
    canvas.paste(image, (x + 17, y + 66))
    draw.rectangle((x + 17, y + 66, x + 17 + w - 34, y + 66 + image_h), outline=(138, 138, 138), width=2)

    bullet_y = y + 322
    for idx, line in enumerate(bullets):
        dot_y = bullet_y + idx * 38 + 7
        draw.ellipse((x + 20, dot_y, x + 31, dot_y + 11), fill=accent)
        draw.text((x + 42, bullet_y + idx * 38), line, fill=(45, 45, 45), font=bullet_font)

    draw.rounded_rectangle((x + 17, y + h - 58, x + w - 17, y + h - 18), radius=7, fill=(246, 250, 255), outline=accent, width=2)
    draw.text((x + 34, y + h - 47), "scoring context", fill=accent, font=body_font)


def build_grounding_derivation_companion() -> None:
    width = 1800
    height = 1320
    canvas = Image.new("RGB", (width, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(30, bold=True)
    note_font = _font(16)
    small_font = _font(12)
    accent = (40, 96, 168)

    y = 34
    draw.text((MARGIN, y), "Grounding derivation render companion", fill=(18, 18, 18), font=heading_font)
    y += 42
    draw.text(
        (MARGIN, y),
        "Point-in-box and normalized-coordinate equations are tied to source target-view render pairs, visible render coordinates.",
        fill=(68, 68, 68),
        font=note_font,
    )

    body_y = 104
    card_gap = 16
    left_w = 1190
    right_w = width - MARGIN * 2 - left_w - card_gap
    card_w = (left_w - card_gap) // 2
    card_h = 258
    pairs = [
        ("backpack | point-in-box", "target box bounds the parsed point", VLM_BACKPACK_ORIGINAL, VLM_BACKPACK_CONVERTED, (207.811, 105.285, 376.441, 364.938)),
        ("clock | pair agreement", "same/miss status is separate from correctness", VLM_CLOCK_ORIGINAL, VLM_CLOCK_CONVERTED, (211.647, 107.436, 370.171, 360.234)),
        ("bottle | norm-1000", "normalized point maps back to image pixels", VLM_BOTTLE_ORIGINAL, VLM_BOTTLE_CONVERTED, (230.385, 89.121, 369.378, 372.696)),
        ("cup | scorable row", "malformed points stay out of hit counts", VLM_CUP_ORIGINAL, VLM_CUP_CONVERTED, (183.338, 133.12, 416.662, 331.46)),
    ]
    for idx, (title, note, original, converted, bbox) in enumerate(pairs):
        row = idx // 2
        col = idx % 2
        _draw_table_companion_pair(
            canvas,
            draw,
            x=MARGIN + col * (card_w + card_gap),
            y=body_y + row * (card_h + card_gap),
            w=card_w,
            h=card_h,
            title=title,
            note=note,
            original=original,
            converted=converted,
            bbox=bbox,
            accent=accent,
        )

    _draw_metric_contract_gate(
        canvas,
        draw,
        x=MARGIN + left_w + card_gap,
        y=body_y,
        w=right_w,
        h=card_h * 2 + card_gap,
        accent=accent,
        title="grounding metric check",
        bullets=["box and point are explicit", "norm primary; raw diagnostic", "scorable rows stay separate"],
        slot_path=METRIC_CONTRACT_GATE_V3_AI_SLOT,
    )

    strip_y = body_y + card_h * 2 + card_gap + 16

    def pair_tile(
        original: Path,
        converted: Path,
        bbox: tuple[float, float, float, float],
        size: tuple[int, int] = (560, 220),
        *,
        desaturate: bool = False,
    ) -> Image.Image:
        tile = Image.new("RGB", size, (250, 250, 250))
        tile_draw = ImageDraw.Draw(tile)
        label_font = _font(13, bold=True)
        gap = 8
        label_h = 22
        image_w = (size[0] - gap) // 2
        image_h = size[1] - label_h
        for idx, (label, path) in enumerate((("original", original), ("noMDL", converted))):
            image_x = idx * (image_w + gap)
            tile_draw.rectangle((image_x, 0, image_x + image_w, label_h), fill=(245, 248, 250))
            tile_draw.text((image_x + 8, 4), label, fill=accent if idx else (70, 70, 70), font=label_font)
            image = _fit_with_protocol_overlay(path, (image_w, image_h), bbox)
            if desaturate:
                image = ImageEnhance.Color(image).enhance(0.15)
            tile.paste(image, (image_x, label_h))
            tile_draw.rectangle((image_x, label_h, image_x + image_w, label_h + image_h), outline=(132, 132, 132), width=2)
        return tile

    _draw_opener_band(
        canvas,
        draw,
        y=strip_y,
        title="formula-to-render audit strip: source target-view pairs with protocol overlays",
        tiles=[
            ("backpack box/point", pair_tile(VLM_BACKPACK_ORIGINAL, VLM_BACKPACK_CONVERTED, (207.811, 105.285, 376.441, 364.938))),
            ("clock agreement", pair_tile(VLM_CLOCK_ORIGINAL, VLM_CLOCK_CONVERTED, (211.647, 107.436, 370.171, 360.234))),
            ("bottle norm-1000", pair_tile(VLM_BOTTLE_ORIGINAL, VLM_BOTTLE_CONVERTED, (230.385, 89.121, 369.378, 372.696))),
            ("cup scorable row", pair_tile(VLM_CUP_ORIGINAL, VLM_CUP_CONVERTED, (183.338, 133.12, 416.662, 331.46))),
        ],
        band_h=205,
    )

    wall_y = strip_y + 205 + 14
    _draw_opener_band(
        canvas,
        draw,
        y=wall_y,
        title="source coordinate-conversion render wall: zoom-level anchors",
        tiles=[
            ("backpack z018", pair_tile(VLM_BACKPACK_ORIGINAL, VLM_BACKPACK_CONVERTED, (207.811, 105.285, 376.441, 364.938))),
            ("backpack z019", pair_tile(VLM_BACKPACK_Z19_ORIGINAL, VLM_BACKPACK_Z19_CONVERTED, (207.811, 105.285, 376.441, 364.938), desaturate=True)),
            ("clock z018", pair_tile(VLM_CLOCK_ORIGINAL, VLM_CLOCK_CONVERTED, (211.647, 107.436, 370.171, 360.234))),
            ("clock z019", pair_tile(VLM_CLOCK_Z19_ORIGINAL, VLM_CLOCK_Z19_CONVERTED, (211.647, 107.436, 370.171, 360.234), desaturate=True)),
            ("bottle norm", pair_tile(VLM_BOTTLE_ORIGINAL, VLM_BOTTLE_CONVERTED, (230.385, 89.121, 369.378, 372.696))),
            ("cup scorable", pair_tile(VLM_CUP_ORIGINAL, VLM_CUP_CONVERTED, (183.338, 133.12, 416.662, 331.46))),
        ],
        band_h=185,
    )

    close_y = wall_y + 185 + 14

    def close_tile(
        path: Path,
        bbox: tuple[float, float, float, float],
        size: tuple[int, int] = (360, 230),
    ) -> Image.Image:
        return _fit_with_protocol_overlay(path, size, bbox)

    _draw_opener_band(
        canvas,
        draw,
        y=close_y,
        title="target close-up scorer wall: source crops spanning pass and diagnostic views",
        tiles=[
            ("cupB original", close_tile(VLM_CUP_ALT_ORIGINAL, (197.137, 107.89, 402.863, 372.325))),
            ("cupB noMDL", close_tile(VLM_CUP_ALT_CONVERTED, (197.137, 107.89, 402.863, 372.325))),
            ("faucet original", close_tile(VLM_FAUCET_ORIGINAL, (215.154, 118.861, 407.249, 356.885))),
            ("faucet noMDL", close_tile(VLM_FAUCET_CONVERTED, (215.154, 118.861, 407.249, 356.885))),
            ("picture original", close_tile(VLM_PICTURE_ORIGINAL, (240.087, 100.65, 374.808, 360.903))),
            ("picture noMDL", close_tile(VLM_PICTURE_CONVERTED, (240.087, 100.65, 374.808, 360.903))),
        ],
        band_h=218,
    )
    draw.text(
        (MARGIN, height - 26),
        "Reading note: the render pairs explain the formulas; they explain the formula rows and denominators.",
        fill=(82, 82, 82),
        font=small_font,
    )

    GROUNDING_DERIVATION_COMPANION_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(GROUNDING_DERIVATION_COMPANION_OUT)
    print(GROUNDING_DERIVATION_COMPANION_OUT)


def _draw_navigation_metric_card(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    note: str,
    image: Image.Image,
    accent: tuple[int, int, int],
) -> None:
    title_font = _font(18, bold=True)
    note_font = _font(12)
    image_y = y + 58
    image_h = h - 74

    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(252, 252, 252), outline=(180, 180, 180), width=2)
    draw.rectangle((x, y, x + 7, y + h), fill=accent)
    draw.text((x + 16, y + 10), title, fill=(20, 20, 20), font=title_font)
    draw.text((x + 16, y + 36), note, fill=(72, 72, 72), font=note_font)
    fitted = ImageOps.fit(image, (w - 32, image_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    canvas.paste(fitted, (x + 16, image_y))
    draw.rectangle((x + 16, image_y, x + w - 16, image_y + image_h), outline=(140, 140, 140), width=2)


def build_navigation_derivation_companion() -> None:
    width = 1800
    height = 740
    canvas = Image.new("RGB", (width, height), (236, 236, 236))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(30, bold=True)
    note_font = _font(16)
    small_font = _font(12)

    y = 30
    draw.text((MARGIN, y), "Navigation derivation media companion", fill=(18, 18, 18), font=heading_font)
    y += 42
    draw.text(
        (MARGIN, y),
        "Formula-to-route metric bridge: SR, NE, SPL, and TL are episode-level quantities grounded in source routes.",
        fill=(68, 68, 68),
        font=note_font,
    )
    y += 44
    y = _draw_opener_band(
        canvas,
        draw,
        y=y,
        title="Formula-to-route metric bridge",
        tiles=[
            ("metric panel", _crop_fit(NAV_DOWNSTREAM, (0, 40, 1110, 480), (340, 220))),
            ("selected stills", _crop_fit(NAV_SELECTED6, (0, 120, 1106, 1400), (340, 220))),
            ("route spread", _crop_fit(NAV_0036_SELECTED6, (0, 220, 1706, 1250), (340, 220))),
            ("metric check", _fit(NAVIGATION_METRIC_GATE_V4_AI_SLOT, (340, 220), cover=False)),
            ("route case", _crop_fit(NAV_0036_CASE4, (0, 34, 770, 338), (340, 220))),
        ],
        band_h=190,
    )
    y += 10
    y = _draw_opener_band(
        canvas,
        draw,
        y=y,
        title="SR / NE / SPL / TL route-outcome anchors",
        tiles=[
            ("SR / NE case", _crop_fit(NAV_SELECTED_CASE, (0, 42, 1106, 360), (300, 210))),
            ("SPL route 01", _crop_fit(NAV_0036_CASE, (0, 34, 770, 338), (300, 210))),
            ("TL case 02", _crop_fit(NAV_SELECTED_CASE2, (0, 42, 1106, 380), (300, 210))),
            ("route 02", _crop_fit(NAV_0036_CASE2, (0, 34, 770, 338), (300, 210))),
            ("case 03", _crop_fit(NAV_SELECTED_CASE3, (0, 42, 1106, 380), (300, 210))),
            ("route 03", _crop_fit(NAV_0036_CASE3, (0, 34, 770, 338), (300, 210))),
        ],
        band_h=180,
    )
    y += 10
    y = _draw_opener_band(
        canvas,
        draw,
        y=y,
        title="source route-pair audit wall",
        tiles=[
            ("case 04", _crop_fit(NAV_SELECTED_CASE4, (0, 42, 1106, 380), (300, 205))),
            ("route 04", _crop_fit(NAV_0036_CASE4, (0, 34, 770, 338), (300, 205))),
            ("case 05", _crop_fit(NAV_SELECTED_CASE5, (0, 42, 1106, 380), (300, 205))),
            ("route 05", _crop_fit(NAV_0036_CASE5, (0, 34, 770, 338), (300, 205))),
            ("case 06", _crop_fit(NAV_SELECTED_CASE6, (0, 42, 1106, 380), (300, 205))),
            ("route 06", _crop_fit(NAV_0036_CASE6, (0, 34, 770, 338), (300, 205))),
        ],
        band_h=180,
    )

    draw.text(
        (MARGIN, y + 16),
        "Reading note: route and still panels make the formulas inspectable; aggregate results remain tied to the frozen official-scene run.",
        fill=(82, 82, 82),
        font=small_font,
    )

    NAVIGATION_DERIVATION_COMPANION_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(NAVIGATION_DERIVATION_COMPANION_OUT)
    print(NAVIGATION_DERIVATION_COMPANION_OUT)


def build_visual_evidence_roadmap() -> None:
    height = 2050
    canvas = Image.new("RGB", (WIDTH, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(36, bold=True)
    note_font = _font(18)
    footer_font = _font(15)

    y = MARGIN
    draw.text((MARGIN, y), "Visual evidence roadmap", fill=(18, 18, 18), font=heading_font)
    y += 54
    draw.text(
        (MARGIN, y),
        "A render-first index over the supplement: the panels are copied from source figures and are source index.",
        fill=(64, 64, 64),
        font=note_font,
    )
    y += 74

    y = _draw_roadmap_lane(
        canvas,
        draw,
        y=y,
        index="1",
        title="proxy render pairs",
        note="object-level MDL and\nUsdPreviewSurface views",
        tag="proxy",
        lane_h=370,
        tiles=[
            ("0011 MDL", _crop_fit(RENDER_PAIRS, (72, 75, 702, 546), (330, 240))),
            ("0011 noMDL", _crop_fit(RENDER_PAIRS, (726, 75, 1354, 546), (330, 240))),
            ("0004 MDL", _crop_fit(RENDER_PAIRS, (72, 615, 702, 1085), (330, 240))),
            ("0004 noMDL", _crop_fit(RENDER_PAIRS, (726, 615, 1354, 1085), (330, 240))),
        ],
    ) + GAP
    y = _draw_roadmap_lane(
        canvas,
        draw,
        y=y,
        index="2",
        title="GRScenes target views",
        note="post-repair target boxes,\nno VLM point overlays",
        tag="VLM",
        lane_h=370,
        tiles=[
            ("backpack", _fit_with_bbox(VLM_BACKPACK_ORIGINAL, (330, 240), (207.811, 105.285, 376.441, 364.938))),
            ("clock", _fit_with_bbox(VLM_CLOCK_ORIGINAL, (330, 240), (211.647, 107.436, 370.171, 360.234))),
            ("bottle", _fit_with_bbox(VLM_BOTTLE_ORIGINAL, (330, 240), (230.385, 89.121, 369.378, 372.696))),
            ("cup", _fit_with_bbox(VLM_CUP_ORIGINAL, (330, 240), (183.338, 133.12, 416.662, 331.46))),
        ],
    ) + GAP
    y = _draw_roadmap_lane(
        canvas,
        draw,
        y=y,
        index="3",
        title="material diagnostics",
        note="covered bins plus selected\nclearcoat/procedural limits",
        tag="material",
        lane_h=370,
        tiles=[
            ("covered bottle", _crop_fit(MATERIAL_BASELINE, (12, 55, 372, 174), (330, 240))),
            ("covered clock", _crop_fit(MATERIAL_BASELINE, (382, 216, 742, 337), (330, 240))),
            ("clearcoat", _crop_fit(MATERIAL_SUPPLEMENTAL, (24, 62, 284, 258), (330, 240))),
            ("procedural", _crop_fit(MATERIAL_SUPPLEMENTAL, (24, 340, 284, 535), (330, 240))),
        ],
    ) + GAP
    y = _draw_roadmap_lane(
        canvas,
        draw,
        y=y,
        index="4",
        title="InternNav media",
        note="paired metrics, route context,\nand selected video stills",
        tag="navigation",
        lane_h=515,
        tiles=[
            ("rollout", _crop_fit(NAV_STILLS, (0, 140, 1106, 770), (330, 330))),
            ("0036/0066", _crop_fit(NAV_0036_MAIN, (390, 108, 1738, 790), (330, 330))),
            ("selected case", _crop_fit(NAV_SELECTED_CASE, (0, 42, 1106, 360), (330, 330))),
            ("0036 case", _crop_fit(NAV_0036_CASE, (0, 34, 770, 338), (330, 330))),
        ],
    ) + 28

    draw.rounded_rectangle((MARGIN, y, WIDTH - MARGIN, height - MARGIN), radius=8, fill=(252, 252, 252), outline=(176, 176, 176), width=2)
    draw.multiline_text(
        (MARGIN + 24, y + 22),
        "Reading rule: this page is a visual index. It ties the reader to the detailed tables and figure pages that follow, "
        "and points readers to the detailed tables.",
        fill=(44, 44, 44),
        font=footer_font,
        spacing=5,
    )

    VISUAL_EVIDENCE_ROADMAP_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(VISUAL_EVIDENCE_ROADMAP_OUT)
    print(VISUAL_EVIDENCE_ROADMAP_OUT)


def _draw_first_page_quickstart_lane(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    note: str,
    accent: tuple[int, int, int],
    tiles: list[tuple[str, Image.Image]],
) -> None:
    title_font = _font(18, bold=True)
    body_font = _font(12)
    small_font = _font(10, bold=True)
    image_y = y + 50
    image_h = h - 66
    tile_gap = 8
    tile_w = (w - 32 - (len(tiles) - 1) * tile_gap) // len(tiles)

    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(252, 252, 252), outline=(174, 174, 174), width=2)
    draw.rectangle((x, y, x + 8, y + h), fill=accent)
    draw.text((x + 18, y + 12), title, fill=(20, 20, 20), font=title_font)
    draw.text((x + 18, y + 36), note, fill=(68, 68, 68), font=body_font)
    for idx, (label, tile) in enumerate(tiles):
        tile_x = x + 18 + idx * (tile_w + tile_gap)
        image = ImageOps.fit(tile, (tile_w, image_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        canvas.paste(image, (tile_x, image_y))
        draw.rectangle((tile_x, image_y, tile_x + tile_w, image_y + image_h), outline=(140, 140, 140), width=2)
        draw.rectangle((tile_x, image_y, tile_x + tile_w, image_y + 26), fill=(236, 236, 236), outline=(140, 140, 140), width=1)
        draw.text((tile_x + 5, image_y + 4), label, fill=(28, 28, 28), font=small_font)


def _first_page_pair_tile(original: Path, converted: Path, size: tuple[int, int]) -> Image.Image:
    tile = Image.new("RGB", size, (248, 248, 248))
    gap = 4
    half_w = (size[0] - gap) // 2
    left = ImageOps.fit(Image.open(original).convert("RGB"), (half_w, size[1]), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    right = ImageOps.fit(Image.open(converted).convert("RGB"), (size[0] - half_w - gap, size[1]), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    tile.paste(left, (0, 0))
    tile.paste(right, (half_w + gap, 0))
    return tile


def _draw_first_page_render_ladder(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
) -> None:
    title_font = _font(17, bold=True)
    note_font = _font(11)
    label_font = _font(9, bold=True)
    tiles = [
        ("scene ext.", _crop_fit(RENDER_SCENE_EXTENDED_OUT, (40, 790, 1760, 1540), (320, 170))),
        ("proxy pair", _crop_fit(RENDER_SCENE_WIDE, (34, 548, 1767, 884), (320, 170))),
        ("coord atlas", _crop_fit(VLM_COORDINATE_PROTOCOL_OUT, (30, 82, 1770, 690), (320, 170))),
        ("target guide", _crop_fit(GRSCENES_VLM_GUIDE_OUT, (30, 82, 1770, 690), (320, 170))),
        ("material", _crop_fit(MATERIAL_SUPPLEMENTAL, (10, 54, 568, 535), (320, 170))),
        ("nav atlas", _crop_fit(NAVIGATION_OUT, (40, 340, 1760, 1160), (320, 170))),
        ("route stills", _crop_fit(NAV_STILLS, (0, 140, 1106, 770), (320, 170))),
        ("case frames", _crop_fit(NAV_0036_MAIN, (390, 108, 1738, 790), (320, 170))),
    ]
    cols = 4
    tile_gap = 8
    row_gap = 8
    tile_y = y + 50
    tile_h = (h - 64 - row_gap) // 2
    tile_w = (w - 32 - (cols - 1) * tile_gap) // cols

    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(252, 252, 252), outline=(174, 174, 174), width=2)
    draw.text((x + 16, y + 10), "source opening render ladder v4", fill=(18, 18, 18), font=title_font)
    draw.text((x + 16, y + 30), "same evaluation checks, more render anchors before the detailed pages", fill=(70, 70, 70), font=note_font)
    for idx, (label, tile) in enumerate(tiles):
        col = idx % cols
        row = idx // cols
        tile_x = x + 16 + col * (tile_w + tile_gap)
        yy = tile_y + row * (tile_h + row_gap)
        image = ImageOps.fit(tile, (tile_w, tile_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        canvas.paste(image, (tile_x, yy))
        draw.rectangle((tile_x, yy, tile_x + tile_w, yy + tile_h), outline=(140, 140, 140), width=2)
        draw.rectangle((tile_x, yy, tile_x + tile_w, yy + 24), fill=(236, 236, 236), outline=(140, 140, 140), width=1)
        draw.text((tile_x + 4, yy + 4), label, fill=(28, 28, 28), font=label_font)


def build_first_page_evidence_quickstart() -> None:
    width = 920
    height = 1800
    margin = 24
    gap = 10
    lane_h = 240
    canvas = Image.new("RGB", (width, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(27, bold=True)
    note_font = _font(14)
    footer_font = _font(11)

    y = margin
    draw.text((margin, y), "First-page evidence quickstart", fill=(18, 18, 18), font=heading_font)
    y += 38
    draw.text(
        (margin, y),
        "A compact visual index: real render, target-view, material, and navigation evidence before the detailed pages.",
        fill=(64, 64, 64),
        font=note_font,
    )
    y += 38

    _draw_first_page_quickstart_lane(
        canvas,
        draw,
        x=margin,
        y=y,
        w=width - 2 * margin,
        h=lane_h,
        title="proxy render evidence",
        note="matched original/noMDL views define image-level proxies",
        accent=(40, 96, 168),
        tiles=[
            ("scene MDL", _crop_fit(RENDER_SCENE_WIDE, (34, 548, 888, 884), (260, 150))),
            ("scene noMDL", _crop_fit(RENDER_SCENE_WIDE, (912, 548, 1767, 884), (260, 150))),
            ("object MDL", _crop_fit(RENDER_PAIRS, (72, 75, 702, 546), (260, 150))),
            ("object noMDL", _crop_fit(RENDER_PAIRS, (736, 75, 1366, 546), (260, 150))),
        ],
    )
    y += lane_h + gap
    _draw_first_page_quickstart_lane(
        canvas,
        draw,
        x=margin,
        y=y,
        w=width - 2 * margin,
        h=lane_h,
        title="VLM target evidence",
        note="source target boxes anchor prompt/coordinate checks",
        accent=(0, 133, 100),
        tiles=[
            ("backpack", _fit_with_bbox(VLM_BACKPACK_ORIGINAL, (260, 210), (207.811, 105.285, 376.441, 364.938))),
            ("clock", _fit_with_bbox(VLM_CLOCK_ORIGINAL, (260, 210), (211.647, 107.436, 370.171, 360.234))),
            ("bottle", _first_page_pair_tile(VLM_BOTTLE_ORIGINAL, VLM_BOTTLE_CONVERTED, (260, 210))),
            ("cup", _fit_with_bbox(VLM_CUP_ORIGINAL, (260, 210), (183.338, 133.12, 416.662, 331.46))),
        ],
    )
    y += lane_h + gap
    _draw_first_page_quickstart_lane(
        canvas,
        draw,
        x=margin,
        y=y,
        w=width - 2 * margin,
        h=lane_h,
        title="material-effect evidence",
        note="covered bins and selected limitations stay visually inspectable",
        accent=(211, 116, 32),
        tiles=[
            ("covered", _crop_fit(MATERIAL_BASELINE, (12, 55, 372, 174), (260, 150))),
            ("emission", _crop_fit(MATERIAL_SUPPLEMENTAL, (305, 62, 560, 258), (260, 150))),
            ("clearcoat", _crop_fit(MATERIAL_SUPPLEMENTAL, (24, 62, 284, 258), (260, 150))),
            ("procedural", _crop_fit(MATERIAL_SUPPLEMENTAL, (24, 340, 284, 535), (260, 150))),
        ],
    )
    y += lane_h + gap
    _draw_first_page_quickstart_lane(
        canvas,
        draw,
        x=margin,
        y=y,
        w=width - 2 * margin,
        h=lane_h,
        title="navigation media evidence",
        note="official metrics stay separate from selected qualitative stills",
        accent=(99, 82, 156),
        tiles=[
            ("rollout", _crop_fit(NAV_STILLS, (0, 140, 1106, 770), (260, 150))),
            ("0036/0066", _crop_fit(NAV_0036_MAIN, (390, 108, 1738, 790), (260, 150))),
            ("case", _crop_fit(NAV_SELECTED_CASE, (0, 42, 1106, 360), (260, 150))),
            ("route", _crop_fit(NAV_0036_CASE4, (0, 44, 1106, 360), (260, 150))),
        ],
    )
    y += lane_h + gap

    ladder_h = 220
    _draw_first_page_render_ladder(canvas, draw, x=margin, y=y, w=width - 2 * margin, h=ladder_h)
    y += ladder_h + gap

    card_h = height - y - margin - 28
    draw.rounded_rectangle((margin, y, width - margin, y + card_h), radius=8, fill=(252, 252, 252), outline=(174, 174, 174), width=2)
    draw.text((margin + 18, y + 12), "reader compass", fill=(20, 20, 20), font=_font(18, bold=True))
    draw.text((margin + 18, y + 36), "orientation panel", fill=(72, 72, 72), font=note_font)
    slot_h = card_h - 68
    slot = _fit(FIRST_PAGE_READING_COMPASS_AI_SLOT, (width - 2 * margin - 36, slot_h), cover=False)
    canvas.paste(slot, (margin + 18, y + 50))
    draw.rectangle((margin + 18, y + 50, width - margin - 18, y + 50 + slot_h), outline=(140, 140, 140), width=2)
    draw.rounded_rectangle((margin + 18, y + card_h - 16, width - margin - 18, y + card_h - 5), radius=4, fill=(246, 250, 255), outline=(38, 95, 156), width=1)
    draw.text((margin + 28, y + card_h - 16), "source index or task result", fill=(38, 95, 156), font=_font(8))

    draw.rounded_rectangle((margin, height - 36, width - margin, height - 8), radius=6, fill=(234, 242, 250), outline=(38, 95, 156), width=1)
    draw.text(
        (margin + 12, height - 29),
        "Reading note: this quickstart reuses source media; the compass is source orientation panel.",
        fill=(38, 95, 156),
        font=footer_font,
    )

    FIRST_PAGE_EVIDENCE_QUICKSTART_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(FIRST_PAGE_EVIDENCE_QUICKSTART_OUT)
    print(FIRST_PAGE_EVIDENCE_QUICKSTART_OUT)


def _draw_page4_boundary_card(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    not_proved: str,
    accent: tuple[int, int, int],
    tiles: list[tuple[str, Image.Image]],
) -> None:
    title_font = _font(17, bold=True)
    body_font = _font(11)
    label_font = _font(9, bold=True)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=7, fill=(252, 252, 252), outline=(174, 174, 174), width=2)
    draw.rectangle((x, y, x + 7, y + h), fill=accent)
    draw.text((x + 16, y + 12), title, fill=(18, 18, 18), font=title_font)
    draw.text((x + 16, y + 38), not_proved, fill=(72, 72, 72), font=body_font)

    image_y = y + 56
    image_h = h - 66
    tile_gap = 8
    tile_w = (w - 32 - (len(tiles) - 1) * tile_gap) // len(tiles)
    for idx, (label, tile) in enumerate(tiles):
        tile_x = x + 16 + idx * (tile_w + tile_gap)
        image = ImageOps.fit(tile, (tile_w, image_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        canvas.paste(image, (tile_x, image_y))
        draw.rectangle((tile_x, image_y, tile_x + tile_w, image_y + image_h), outline=(139, 139, 139), width=2)
        draw.rectangle((tile_x, image_y, tile_x + tile_w, image_y + 22), fill=(236, 236, 236), outline=(139, 139, 139), width=1)
        draw.text((tile_x + 4, image_y + 4), label, fill=(30, 30, 30), font=label_font)

    draw.rectangle((x + 16, y + h - 15, x + w - 16, y + h - 7), fill=accent)


def _draw_page4_render_ladder(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
) -> None:
    title_font = _font(16, bold=True)
    note_font = _font(10)
    label_font = _font(9, bold=True)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=7, fill=(252, 252, 252), outline=(172, 172, 172), width=2)
    draw.text((x + 16, y + 10), "source exclusion-to-render ladder", fill=(18, 18, 18), font=title_font)
    draw.text(
        (x + 16, y + 32),
        "same negative conclusions, now anchored to source render/media examples",
        fill=(72, 72, 72),
        font=note_font,
    )
    tiles = [
        ("proxy pair", _crop_fit(RENDER_SCENE_WIDE, (34, 548, 1767, 884), (220, 124))),
        ("backpack pair", _first_page_pair_tile(VLM_BACKPACK_Z19_ORIGINAL, VLM_BACKPACK_Z19_CONVERTED, (220, 124))),
        ("clock pair", _first_page_pair_tile(VLM_CLOCK_Z19_ORIGINAL, VLM_CLOCK_Z19_CONVERTED, (220, 124))),
        ("material limits", _crop_fit(MATERIAL_SUPPLEMENTAL, (24, 62, 558, 258), (220, 124))),
        ("rollout", _crop_fit(NAV_STILLS, (0, 140, 1106, 770), (220, 124))),
        ("case media", _crop_fit(NAV_SELECTED_CASE, (0, 42, 1106, 360), (220, 124))),
    ]
    tile_gap = 8
    tile_w = (w - 32 - (len(tiles) - 1) * tile_gap) // len(tiles)
    tile_h = h - 72
    tile_y = y + 54
    for idx, (label, tile) in enumerate(tiles):
        tile_x = x + 16 + idx * (tile_w + tile_gap)
        image = ImageOps.fit(tile, (tile_w, tile_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        canvas.paste(image, (tile_x, tile_y))
        draw.rectangle((tile_x, tile_y, tile_x + tile_w, tile_y + tile_h), outline=(139, 139, 139), width=2)
        draw.rectangle((tile_x, tile_y, tile_x + tile_w, tile_y + 22), fill=(236, 236, 236), outline=(139, 139, 139), width=1)
        draw.text((tile_x + 4, tile_y + 4), label, fill=(30, 30, 30), font=label_font)


def build_page4_claim_boundary_companion() -> None:
    width = 920
    height = 1480
    margin = 20
    gap = 10
    card_w = (width - 2 * margin - gap) // 2
    card_h = 272
    canvas = Image.new("RGB", (width, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(26, bold=True)
    note_font = _font(13)
    footer_font = _font(10)

    y = margin
    draw.text((margin, y), "Page-4 evaluation-scope companion", fill=(18, 18, 18), font=heading_font)
    y += 34
    draw.text(
        (margin, y),
        "The visual examples keep the overview exclusions attached to source render evidence.",
        fill=(64, 64, 64),
        font=note_font,
    )
    y += 30

    _draw_page4_boundary_card(
        canvas,
        draw,
        x=margin,
        y=y,
        w=card_w,
        h=card_h,
        title="proxy render score",
        not_proved="task checks separate",
        accent=(40, 96, 168),
        tiles=[
            ("object MDL", _crop_fit(RENDER_SCENE_WIDE, (34, 90, 888, 470), (210, 140))),
            ("object noMDL", _crop_fit(RENDER_SCENE_WIDE, (913, 90, 1767, 470), (210, 140))),
            ("scene detail", _crop_fit(RENDER_SCENE_WIDE, (430, 548, 1767, 884), (210, 140))),
        ],
    )
    _draw_page4_boundary_card(
        canvas,
        draw,
        x=margin + card_w + gap,
        y=y,
        w=card_w,
        h=card_h,
        title="VLM target box",
        not_proved="backend coverage separate",
        accent=(0, 133, 100),
        tiles=[
            ("backpack", _fit_with_bbox(VLM_BACKPACK_ORIGINAL, (210, 140), (268.5, 144.1, 466.2, 416.9))),
            ("clock", _fit_with_bbox(VLM_CLOCK_ORIGINAL, (210, 140), (211.647, 107.436, 370.171, 360.234))),
            ("cup", _fit_with_bbox(VLM_CUP_ORIGINAL, (210, 140), (183.338, 133.12, 416.662, 331.46))),
        ],
    )
    y += card_h + gap
    _draw_page4_boundary_card(
        canvas,
        draw,
        x=margin,
        y=y,
        w=card_w,
        h=card_h,
        title="material cases",
        not_proved="selected case only",
        accent=(211, 116, 32),
        tiles=[
            ("clearcoat", _crop_fit(MATERIAL_SUPPLEMENTAL, (24, 62, 284, 258), (210, 140))),
            ("procedural", _crop_fit(MATERIAL_SUPPLEMENTAL, (24, 340, 284, 535), (210, 140))),
            ("nvidia limit", _crop_fit(MATERIAL_SUPPLEMENTAL, (572, 340, 833, 535), (210, 140))),
        ],
    )
    _draw_page4_boundary_card(
        canvas,
        draw,
        x=margin + card_w + gap,
        y=y,
        w=card_w,
        h=card_h,
        title="navigation media",
        not_proved="route scope limited",
        accent=(99, 82, 156),
        tiles=[
            ("rollout", _crop_fit(NAV_STILLS, (0, 140, 1106, 770), (210, 140))),
            ("route", _crop_fit(NAV_0036_MAIN, (0, 130, 1106, 770), (210, 140))),
            ("case", _crop_fit(NAV_SELECTED_CASE, (0, 42, 1106, 360), (210, 140))),
        ],
    )
    y += card_h + 12

    ladder_h = 260
    _draw_page4_render_ladder(canvas, draw, x=margin, y=y, w=width - 2 * margin, h=ladder_h)
    y += ladder_h + gap

    marker_h = height - y - margin - 16
    draw.rounded_rectangle((margin, y, width - margin, y + marker_h), radius=7, fill=(252, 252, 252), outline=(174, 174, 174), width=2)
    draw.text((margin + 16, y + 10), "scope marker", fill=(18, 18, 18), font=_font(16, bold=True))
    draw.text((margin + 16, y + 32), "scope marker for reading the examples", fill=(72, 72, 72), font=note_font)
    callout_y = y + 58
    callout_h = 52
    callout_w = (width - 2 * margin - 48) // 3
    callouts = [
        ("reading panel", (38, 95, 156)),
        ("fixed labels", (0, 133, 100)),
        ("summary panel", (99, 82, 156)),
    ]
    for idx, (label, color) in enumerate(callouts):
        x0 = margin + 16 + idx * (callout_w + 8)
        draw.rounded_rectangle((x0, callout_y, x0 + callout_w, callout_y + callout_h), radius=5, fill=(246, 250, 255), outline=color, width=1)
        draw.text((x0 + 12, callout_y + 17), label, fill=color, font=_font(13, bold=True))
    slot_x = margin + 16
    slot_y = callout_y + callout_h + 12
    slot_w = width - 2 * margin - 32
    slot_h = marker_h - (slot_y - y) - 16
    slot = _fit(PAGE4_BOUNDARY_MARKER_AI_SLOT, (slot_w, slot_h), cover=False)
    canvas.paste(slot, (slot_x, slot_y))
    draw.rectangle((slot_x, slot_y, slot_x + slot_w, slot_y + slot_h), outline=(140, 140, 140), width=2)

    draw.text(
        (margin, height - 13),
        "Reading note: source index context.",
        fill=(82, 82, 82),
        font=footer_font,
    )

    PAGE4_CLAIM_BOUNDARY_COMPANION_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(PAGE4_CLAIM_BOUNDARY_COMPANION_OUT)
    print(PAGE4_CLAIM_BOUNDARY_COMPANION_OUT)


def _compose_material_bridge(size: tuple[int, int]) -> Image.Image:
    width, height = size
    gap = 14
    panel_w = (width - 2 * gap) // 3
    canvas = Image.new("RGB", size, (250, 250, 250))
    draw = ImageDraw.Draw(canvas)
    panels = [
        _crop_fit(MATERIAL_BASELINE, (12, 378, 1112, 500), (panel_w, height)),
        _crop_contain(MATERIAL_SUPPLEMENTAL, (24, 62, 832, 258), (panel_w, height)),
        _crop_contain(MATERIAL_SUPPLEMENTAL, (24, 340, 832, 535), (panel_w, height)),
    ]
    for idx, panel in enumerate(panels):
        x = idx * (panel_w + gap)
        canvas.paste(panel, (x, 0))
        draw.rectangle((x, 0, x + panel_w, height), outline=(145, 145, 145), width=2)
    return canvas


def _draw_material_claim_row(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
    index: str,
    title: str,
    note: str,
    source: Path,
    crop: tuple[int, int, int, int],
    claim: str,
    boundary: str,
) -> int:
    row_h = 390
    label_w = 185
    claim_w = 300
    image_w = WIDTH - 2 * MARGIN - label_w - claim_w - 2 * GAP
    title_font = _font(20, bold=True)
    note_font = _font(14)
    index_font = _font(18, bold=True)
    claim_font = _font(15, bold=True)
    body_font = _font(13)

    draw.rounded_rectangle((MARGIN, y, WIDTH - MARGIN, y + row_h), radius=8, fill=(252, 252, 252), outline=(178, 178, 178), width=2)
    draw.rectangle((MARGIN + 18, y + 22, MARGIN + 54, y + 58), outline=(45, 45, 45), width=2)
    draw.text((MARGIN + 30, y + 25), index, fill=(20, 20, 20), font=index_font)
    draw.multiline_text((MARGIN + 68, y + 18), title, fill=(20, 20, 20), font=title_font, spacing=2)
    note_y = y + (88 if "\n" in title else 58)
    draw.multiline_text((MARGIN + 68, note_y), note, fill=(68, 68, 68), font=note_font, spacing=4)
    draw.text((MARGIN + 20, y + row_h - 34), "source renders", fill=(96, 96, 96), font=note_font)

    image_x = MARGIN + label_w + GAP
    image_y = y + 46
    image_h = row_h - 92
    image = _crop_fit(source, crop, (image_w, image_h))
    canvas.paste(image, (image_x, image_y))
    draw.rectangle((image_x, image_y, image_x + image_w, image_y + image_h), outline=(145, 145, 145), width=2)
    draw.rectangle((image_x, image_y - 26, image_x + image_w, image_y), fill=(238, 244, 250), outline=(145, 145, 145), width=1)
    draw.text((image_x + 12, image_y - 20), "render evidence crop", fill=(38, 95, 156), font=_font(13, bold=True))

    claim_x = image_x + image_w + GAP
    claim_y = y + 46
    draw.rectangle((claim_x, claim_y, claim_x + claim_w, claim_y + image_h), fill=(247, 247, 247), outline=(166, 166, 166), width=2)
    draw.rectangle((claim_x, claim_y, claim_x + claim_w, claim_y + 8), fill=(38, 95, 156))
    draw.text((claim_x + 16, claim_y + 20), "paper result", fill=(38, 95, 156), font=claim_font)
    draw.multiline_text((claim_x + 16, claim_y + 52), claim, fill=(32, 32, 32), font=body_font, spacing=3)
    draw.rectangle((claim_x, claim_y + image_h // 2, claim_x + claim_w, claim_y + image_h // 2 + 8), fill=(211, 116, 32))
    draw.text((claim_x + 16, claim_y + image_h // 2 + 20), "scope limit", fill=(211, 116, 32), font=claim_font)
    draw.multiline_text((claim_x + 16, claim_y + image_h // 2 + 52), boundary, fill=(32, 32, 32), font=body_font, spacing=3)
    return y + row_h


def _draw_material_claim_boundary_gate_footer(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
    h: int,
) -> None:
    x = MARGIN
    w = WIDTH - 2 * MARGIN
    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(252, 252, 252), outline=(178, 178, 178), width=2)
    draw.text((x + 24, y + 20), "Material scope guide", fill=(38, 95, 156), font=_font(22, bold=True))
    draw.text(
        (x + 24, y + 50),
        "orientation panel; source material renders remain the evidence-bearing panels.",
        fill=(70, 70, 70),
        font=_font(14),
    )

    slot_x = x + 24
    slot_y = y + 82
    slot_w = 1050
    slot_h = h - 112
    slot = _fit(MATERIAL_CLAIM_BOUNDARY_GATE_AI_SLOT, (slot_w, slot_h))
    canvas.paste(slot, (slot_x, slot_y))
    draw.rectangle((slot_x, slot_y, slot_x + slot_w, slot_y + slot_h), outline=(145, 145, 145), width=2)
    draw.rectangle((slot_x, slot_y, slot_x + slot_w, slot_y + 25), fill=(248, 248, 248), outline=(145, 145, 145), width=1)
    draw.text((slot_x + 10, slot_y + 6), "material-scope panel", fill=(35, 35, 35), font=_font(12, bold=True))

    card_x = slot_x + slot_w + GAP
    card_w = x + w - card_x - 24
    card_h = (slot_h - 24) // 3
    rows = [
        ("covered bins", "scoped static and selected qualitative results", (66, 135, 92)),
        ("clearcoat", "selected diagnostic; selected case only", (38, 95, 156)),
        ("procedural texture", "limitation case unless kept as MDL or baked", (70, 70, 70)),
    ]
    for idx, (title, body, accent) in enumerate(rows):
        yy = slot_y + idx * (card_h + 12)
        draw.rectangle((card_x, yy, card_x + card_w, yy + card_h), fill=(248, 248, 248), outline=(166, 166, 166), width=2)
        draw.rectangle((card_x, yy, card_x + 9, yy + card_h), fill=accent)
        draw.text((card_x + 24, yy + 18), title, fill=(24, 24, 24), font=_font(17, bold=True))
        draw.multiline_text((card_x + 24, yy + 48), body, fill=(45, 45, 45), font=_font(14), spacing=4)


def build_material_claim_boundary_atlas() -> None:
    height = 1940
    canvas = Image.new("RGB", (WIDTH, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(34, bold=True)
    note_font = _font(18)

    y = MARGIN
    draw.text((MARGIN, y), "Material scope render atlas", fill=(18, 18, 18), font=heading_font)
    y += 50
    draw.text(
        (MARGIN, y),
        "The same risk-matrix rows are tied back to real Original MDL, ConvertAsset, and NVIDIA render evidence.",
        fill=(66, 66, 66),
        font=note_font,
    )
    y += 72

    y = _draw_material_claim_row(
        canvas,
        draw,
        y=y,
        index="1",
        title="covered bins",
        note="4 covered\neffect bins",
        source=MATERIAL_BASELINE,
        crop=(0, 0, 1124, 337),
        claim="scoped static +\nselected qualitative",
        boundary="scoped visual\nevidence",
    ) + 20
    y = _draw_material_claim_row(
        canvas,
        draw,
        y=y,
        index="2",
        title="clearcoat",
        note="selected\nsupplemental case",
        source=MATERIAL_SUPPLEMENTAL,
        crop=(24, 62, 832, 258),
        claim="selected NVIDIA\nfailure case",
        boundary="selected case\ncontext",
    ) + 20
    y = _draw_material_claim_row(
        canvas,
        draw,
        y=y,
        index="3",
        title="procedural\ntexture",
        note="checker signal\nnot preserved",
        source=MATERIAL_SUPPLEMENTAL,
        crop=(24, 340, 832, 535),
        claim="limitation /\ninvestigation case",
        boundary="limitation\ncase",
    ) + 24

    _draw_material_claim_boundary_gate_footer(canvas, draw, y=y, h=height - y - MARGIN)

    MATERIAL_CLAIM_BOUNDARY_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(MATERIAL_CLAIM_BOUNDARY_OUT)
    print(MATERIAL_CLAIM_BOUNDARY_OUT)


def _draw_decision_step(
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    body: str,
    accent: tuple[int, int, int],
) -> None:
    title_font = _font(15, bold=True)
    body_font = _font(12)
    draw.rectangle((x, y, x + w, y + h), fill=(248, 248, 248), outline=(166, 166, 166), width=2)
    draw.rectangle((x, y, x + w, y + 8), fill=accent)
    draw.text((x + 14, y + 18), title, fill=(24, 24, 24), font=title_font)
    draw.multiline_text((x + 14, y + 44), body, fill=(45, 45, 45), font=body_font, spacing=3)


def _draw_material_decision_lane(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
    index: str,
    title: str,
    note: str,
    source: Path,
    crop: tuple[int, int, int, int],
    risk: str,
    action: str,
    paper_use: str,
    accent: tuple[int, int, int],
) -> int:
    lane_h = 390
    label_w = 185
    thumb_w = 1010
    decision_w = WIDTH - 2 * MARGIN - label_w - thumb_w - 2 * GAP
    title_font = _font(20, bold=True)
    note_font = _font(14)
    index_font = _font(18, bold=True)

    draw.rounded_rectangle((MARGIN, y, WIDTH - MARGIN, y + lane_h), radius=8, fill=(252, 252, 252), outline=(178, 178, 178), width=2)
    draw.rectangle((MARGIN + 18, y + 22, MARGIN + 54, y + 58), outline=(45, 45, 45), width=2)
    draw.text((MARGIN + 30, y + 25), index, fill=(20, 20, 20), font=index_font)
    draw.multiline_text((MARGIN + 68, y + 18), title, fill=(20, 20, 20), font=title_font, spacing=2)
    draw.multiline_text((MARGIN + 68, y + 92), note, fill=(68, 68, 68), font=note_font, spacing=4)
    draw.text((MARGIN + 20, y + lane_h - 34), "source renders", fill=(96, 96, 96), font=note_font)

    thumb_x = MARGIN + label_w + GAP
    thumb_y = y + 46
    thumb_h = lane_h - 92
    image = _crop_fit(source, crop, (thumb_w, thumb_h))
    canvas.paste(image, (thumb_x, thumb_y))
    draw.rectangle((thumb_x, thumb_y, thumb_x + thumb_w, thumb_y + thumb_h), outline=(145, 145, 145), width=2)
    draw.rectangle((thumb_x, thumb_y - 26, thumb_x + thumb_w, thumb_y), fill=(238, 244, 250), outline=(145, 145, 145), width=1)
    draw.text((thumb_x + 12, thumb_y - 20), "render evidence crop", fill=(38, 95, 156), font=_font(13, bold=True))

    decision_x = thumb_x + thumb_w + GAP
    step_gap = 12
    step_h = (thumb_h - 2 * step_gap) // 3
    _draw_decision_step(
        draw,
        x=decision_x,
        y=thumb_y,
        w=decision_w,
        h=step_h,
        title="risk",
        body=risk,
        accent=accent,
    )
    _draw_decision_step(
        draw,
        x=decision_x,
        y=thumb_y + step_h + step_gap,
        w=decision_w,
        h=step_h,
        title="ConvertAsset action",
        body=action,
        accent=(38, 95, 156),
    )
    _draw_decision_step(
        draw,
        x=decision_x,
        y=thumb_y + 2 * (step_h + step_gap),
        w=decision_w,
        h=step_h,
        title="paper use",
        body=paper_use,
        accent=(80, 80, 80),
    )
    return y + lane_h


def _draw_material_decision_gate_footer(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
    h: int,
) -> None:
    x = MARGIN
    w = WIDTH - 2 * MARGIN
    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(252, 252, 252), outline=(178, 178, 178), width=2)
    draw.text((x + 24, y + 20), "Material decision panel", fill=(38, 95, 156), font=_font(22, bold=True))
    draw.text(
        (x + 24, y + 50),
        "orientation panel; the lane panels above are the evidence-bearing renders.",
        fill=(70, 70, 70),
        font=_font(14),
    )

    slot_x = x + 24
    slot_y = y + 82
    slot_w = 820
    slot_h = h - 112
    slot = _fit(MATERIAL_DECISION_GATE_AI_SLOT, (slot_w, slot_h), cover=False)
    canvas.paste(slot, (slot_x, slot_y))
    draw.rectangle((slot_x, slot_y, slot_x + slot_w, slot_y + slot_h), outline=(145, 145, 145), width=2)
    draw.rectangle((slot_x, slot_y, slot_x + slot_w, slot_y + 25), fill=(248, 248, 248), outline=(145, 145, 145), width=1)
    draw.text((slot_x + 10, slot_y + 6), "material-decision panel", fill=(35, 35, 35), font=_font(12, bold=True))

    card_x = slot_x + slot_w + GAP
    card_w = x + w - card_x - 24
    card_h = (slot_h - 24) // 3
    rows = [
        ("covered bins", "static check + selected visual review", (66, 135, 92)),
        ("clearcoat", "manual approximation review", (207, 126, 40)),
        ("procedural texture", "keep MDL or bake before preservation statements", (70, 70, 70)),
    ]
    for idx, (title, body, accent) in enumerate(rows):
        yy = slot_y + idx * (card_h + 12)
        draw.rectangle((card_x, yy, card_x + card_w, yy + card_h), fill=(248, 248, 248), outline=(166, 166, 166), width=2)
        draw.rectangle((card_x, yy, card_x + 9, yy + card_h), fill=accent)
        draw.text((card_x + 24, yy + 18), title, fill=(24, 24, 24), font=_font(17, bold=True))
        draw.multiline_text((card_x + 24, yy + 48), body, fill=(45, 45, 45), font=_font(14), spacing=4)


def _draw_material_covered_bin_matrix(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
    h: int,
) -> int:
    x = MARGIN
    w = WIDTH - 2 * MARGIN
    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(252, 252, 252), outline=(178, 178, 178), width=2)
    draw.text((x + 24, y + 18), "Covered-bin render matrix", fill=(38, 95, 156), font=_font(22, bold=True))
    draw.text(
        (x + 24, y + 50),
        "source original, ConvertAsset, and NVIDIA crops keep the four scoped material bins visible.",
        fill=(70, 70, 70),
        font=_font(14),
    )

    columns = [
        (
            "bottle",
            [
                ("original", (12, 54, 371, 174)),
                ("noMDL", (382, 54, 741, 174)),
                ("NVIDIA", (752, 54, 1111, 174)),
            ],
        ),
        (
            "clock",
            [
                ("original", (12, 216, 371, 337)),
                ("noMDL", (382, 216, 741, 337)),
                ("NVIDIA", (752, 216, 1111, 337)),
            ],
        ),
        (
            "cup",
            [
                ("original", (12, 379, 371, 500)),
                ("noMDL", (382, 379, 741, 500)),
                ("NVIDIA", (752, 379, 1111, 500)),
            ],
        ),
        (
            "backpack",
            [
                ("original", (12, 540, 371, 660)),
                ("noMDL", (382, 540, 741, 660)),
                ("NVIDIA", (752, 540, 1111, 660)),
            ],
        ),
    ]
    pad = 24
    col_gap = 14
    row_gap = 10
    col_w = (w - 2 * pad - (len(columns) - 1) * col_gap) // len(columns)
    title_h = 24
    matrix_y = y + 84
    tile_h = (h - 112 - title_h - 2 * row_gap) // 3
    label_font = _font(12, bold=True)
    small_font = _font(11)

    for col_idx, (title, rows) in enumerate(columns):
        col_x = x + pad + col_idx * (col_w + col_gap)
        draw.rectangle((col_x, matrix_y, col_x + col_w, matrix_y + title_h), fill=(238, 244, 250), outline=(166, 166, 166), width=1)
        draw.text((col_x + 10, matrix_y + 5), title, fill=(35, 35, 35), font=label_font)
        for row_idx, (label, crop) in enumerate(rows):
            tile_y = matrix_y + title_h + row_idx * (tile_h + row_gap)
            tile = _crop_fit(MATERIAL_BASELINE, crop, (col_w, tile_h))
            canvas.paste(tile, (col_x, tile_y))
            draw.rectangle((col_x, tile_y, col_x + col_w, tile_y + tile_h), outline=(145, 145, 145), width=1)
            draw.rectangle((col_x, tile_y, col_x + col_w, tile_y + 18), fill=(250, 250, 250), outline=(166, 166, 166), width=1)
            draw.text((col_x + 8, tile_y + 4), label, fill=(40, 40, 40), font=small_font)

    return y + h


def build_material_decision_map() -> None:
    height = 2480
    canvas = Image.new("RGB", (WIDTH, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(34, bold=True)
    note_font = _font(18)

    y = MARGIN
    draw.text((MARGIN, y), "Material safe-conversion decision map", fill=(18, 18, 18), font=heading_font)
    y += 50
    draw.text(
        (MARGIN, y),
        "A render-supported reading guide for the risk matrix, recommender, and selected NVIDIA-baseline interpretation.",
        fill=(66, 66, 66),
        font=note_font,
    )
    y += 70

    y = _draw_material_decision_lane(
        canvas,
        draw,
        y=y,
        index="1",
        title="covered\nbins",
        note="4 covered\nmaterial bins",
        source=MATERIAL_BASELINE,
        crop=(0, 0, 1124, 337),
        risk="scoped;\nfour material bins",
        action="static check +\nselected review",
        paper_use="scoped evidence;\nno global ranking",
        accent=(66, 135, 92),
    ) + 20
    y = _draw_material_decision_lane(
        canvas,
        draw,
        y=y,
        index="2",
        title="clearcoat",
        note="selected\nsupplemental case",
        source=MATERIAL_SUPPLEMENTAL,
        crop=(0, 0, 856, 285),
        risk="manual review;\napproximation risk",
        action="inspect clearcoat\nbefore task use",
        paper_use="selected failure;\nselected case only",
        accent=(207, 126, 40),
    ) + 20
    y = _draw_material_decision_lane(
        canvas,
        draw,
        y=y,
        index="3",
        title="procedural\ntexture",
        note="checker signal\nnot preserved",
        source=MATERIAL_SUPPLEMENTAL,
        crop=(0, 285, 856, 600),
        risk="high;\nchecker lost",
        action="keep MDL or bake\nbefore statements",
        paper_use="limitation;\nnot success case",
        accent=(120, 87, 50),
    ) + 24

    y = _draw_material_covered_bin_matrix(canvas, draw, y=y, h=390) + 24

    _draw_material_decision_gate_footer(canvas, draw, y=y, h=height - y - MARGIN)

    MATERIAL_DECISION_MAP_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(MATERIAL_DECISION_MAP_OUT)
    print(MATERIAL_DECISION_MAP_OUT)


def _compose_navigation_bridge(size: tuple[int, int]) -> Image.Image:
    width, height = size
    gap = 14
    half_w = (width - gap) // 2
    row_h = (height - gap) // 2
    canvas = Image.new("RGB", size, (250, 250, 250))
    draw = ImageDraw.Draw(canvas)
    panels = [
        (0, 0, _crop_fit(NAV_STILLS, (0, 140, 1106, 770), (half_w, row_h))),
        (half_w + gap, 0, _crop_fit(NAV_0036_MAIN, (395, 122, 1735, 790), (half_w, row_h))),
        (0, row_h + gap, _crop_fit(NAV_SELECTED_CASE, (0, 42, 1106, 360), (half_w, row_h))),
        (half_w + gap, row_h + gap, _crop_fit(NAV_0036_CASE, (0, 34, 770, 338), (half_w, row_h))),
    ]
    for x, y, panel in panels:
        canvas.paste(panel, (x, y))
        draw.rectangle((x, y, x + panel.width, y + panel.height), outline=(145, 145, 145), width=2)
    return canvas


def _draw_manifest_card(size: tuple[int, int]) -> Image.Image:
    width, height = size
    canvas = Image.new("RGB", size, (248, 248, 248))
    draw = ImageDraw.Draw(canvas)
    title_font = _font(18, bold=True)
    row_font = _font(13)
    head_font = _font(12, bold=True)
    draw.rectangle((0, 0, width - 1, height - 1), outline=(150, 150, 150), width=2)
    draw.text((18, 16), "manifest mapping", fill=(38, 95, 156), font=title_font)
    cols = ["case", "clip", "status", "role"]
    col_x = [18, 95, 178, 272]
    y = 58
    draw.rectangle((12, y - 8, width - 12, y + 20), fill=(238, 244, 250), outline=(170, 185, 205), width=1)
    for x, col in zip(col_x, cols):
        draw.text((x, y - 2), col, fill=(35, 35, 35), font=head_font)
    rows = [
        ("494", "sel6", "orig+", "qual"),
        ("479", "sel6", "nomdl+", "qual"),
        ("898", "0036", "orig+", "qual"),
        ("919", "0066", "nomdl+", "qual"),
        ("99", "run", "paired", "metric"),
    ]
    y += 32
    for idx, row in enumerate(rows):
        if idx % 2 == 0:
            draw.rectangle((12, y - 6, width - 12, y + 18), fill=(252, 252, 252))
        for x, cell in zip(col_x, row):
            draw.text((x, y), cell, fill=(45, 45, 45), font=row_font)
        y += 28
    draw.text((18, height - 34), "selected media is evidence support, media context", fill=(84, 84, 84), font=row_font)
    return canvas


def _draw_navigation_boundary_lane(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
    index: str,
    title: str,
    note: str,
    boundary_title: str,
    boundary: str,
    tiles: list[tuple[str, Image.Image]],
    accent: tuple[int, int, int],
) -> int:
    lane_h = 345
    label_w = 270
    card_w = 320
    x = MARGIN
    w = WIDTH - 2 * MARGIN
    tile_x = x + label_w + GAP
    card_x = x + w - card_w
    tile_w_total = card_x - tile_x - GAP
    tile_gap = 14
    tile_w = (tile_w_total - tile_gap * (len(tiles) - 1)) // len(tiles)
    tile_h = lane_h - 86
    title_font = _font(23, bold=True)
    note_font = _font(16)
    body_font = _font(14)
    chip_font = _font(12, bold=True)

    draw.rectangle((x, y, x + w, y + lane_h), fill=(252, 252, 252), outline=(172, 172, 172), width=2)
    draw.rectangle((x, y, x + 10, y + lane_h), fill=accent)
    draw.rectangle((x + 24, y + 24, x + 62, y + 62), outline=(45, 45, 45), width=2)
    draw.text((x + 37, y + 28), index, fill=(18, 18, 18), font=_font(19, bold=True))
    draw.multiline_text((x + 78, y + 22), title, fill=(18, 18, 18), font=title_font, spacing=2)
    draw.multiline_text((x + 78, y + 108), note, fill=(58, 58, 58), font=note_font, spacing=4)
    draw.text((x + 78, y + lane_h - 34), "selected still evidence", fill=(96, 96, 96), font=body_font)

    image_y = y + 52
    for idx, (tile_label, tile) in enumerate(tiles):
        xx = tile_x + idx * (tile_w + tile_gap)
        image = ImageOps.fit(tile, (tile_w, tile_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        canvas.paste(image, (xx, image_y))
        draw.rectangle((xx, image_y, xx + tile_w, image_y + tile_h), outline=(135, 135, 135), width=2)
        draw.rectangle((xx, image_y, xx + tile_w, image_y + 24), fill=(248, 248, 248), outline=(135, 135, 135), width=1)
        draw.text((xx + 6, image_y + 5), tile_label, fill=(28, 28, 28), font=chip_font)

    draw.rectangle((card_x, y, card_x + card_w, y + lane_h), fill=(247, 247, 247), outline=(172, 172, 172), width=2)
    draw.text((card_x + 18, y + 28), boundary_title, fill=accent, font=_font(18, bold=True))
    draw.multiline_text((card_x + 18, y + 66), boundary, fill=(38, 38, 38), font=body_font, spacing=5)
    draw.text((card_x + 18, y + lane_h - 54), "media context", fill=(211, 116, 32), font=_font(18, bold=True))
    draw.text((card_x + 18, y + lane_h - 28), "qualitative support only", fill=(58, 58, 58), font=body_font)
    return y + lane_h


def build_navigation_media_boundary_strip() -> None:
    width = 2000
    height = 2240
    canvas = Image.new("RGB", (width, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(36, bold=True)
    note_font = _font(18)
    body_font = _font(16)

    y = MARGIN
    draw.text((MARGIN, y), "Navigation media scope", fill=(18, 18, 18), font=heading_font)
    y += 52
    draw.text(
        (MARGIN, y),
        "Selected video stills and route overlays explain qualitative cases; aggregate results remain tied to source metrics.",
        fill=(64, 64, 64),
        font=note_font,
    )
    y += 62

    media_x = MARGIN
    media_w = width - 2 * MARGIN
    media_h = 1460
    draw.rounded_rectangle((media_x, y, media_x + media_w, y + media_h), radius=8, fill=(252, 252, 252), outline=(176, 176, 176), width=2)
    draw.text((media_x + 22, y + 18), "source selected-media wall", fill=(18, 18, 18), font=_font(28, bold=True))
    draw.text((media_x + 22, y + 58), "twelve real still, route, and manifest panels show what the media bundle can make inspectable.", fill=(68, 68, 68), font=body_font)
    tile_gap = 16
    tile_x0 = media_x + 22
    tile_y0 = y + 96
    tile_w = (media_w - 44 - 2 * tile_gap) // 3
    tile_h = (media_h - 118 - 3 * tile_gap) // 4
    media_tiles = [
        ("selected case 01", NAV_SELECTED_CASE, (0, 42, 1106, 360)),
        ("selected case 02", NAV_SELECTED_CASE2, (0, 42, 1106, 360)),
        ("selected case 03", NAV_SELECTED_CASE3, (0, 42, 1106, 360)),
        ("selected case 04", NAV_SELECTED_CASE4, (0, 42, 1106, 360)),
        ("selected case 05", NAV_SELECTED_CASE5, (0, 42, 1106, 360)),
        ("selected case 06", NAV_SELECTED_CASE6, (0, 42, 1106, 360)),
        ("route case 01", NAV_0036_CASE, (0, 34, 770, 338)),
        ("route case 02", NAV_0036_CASE2, (0, 34, 770, 338)),
        ("route case 03", NAV_0036_CASE3, (0, 34, 770, 338)),
        ("route case 04", NAV_0036_CASE4, (0, 34, 770, 338)),
        ("route case 05", NAV_0036_CASE5, (0, 34, 770, 338)),
        ("route case 06", NAV_0036_CASE6, (0, 34, 770, 338)),
    ]
    for idx, (title, path, crop) in enumerate(media_tiles):
        col = idx % 3
        row = idx // 3
        _draw_upload_visual_tile(
            canvas,
            draw,
            x=tile_x0 + col * (tile_w + tile_gap),
            y=tile_y0 + row * (tile_h + tile_gap),
            w=tile_w,
            h=tile_h,
            title=title,
            path=path,
            crop=crop,
        )

    y += media_h + 24
    gate_h = height - y - MARGIN
    left_w = 1000
    right_x = MARGIN + left_w + 24
    right_w = width - MARGIN - right_x
    draw.rounded_rectangle((MARGIN, y, MARGIN + left_w, y + gate_h), radius=8, fill=(252, 252, 252), outline=(176, 176, 176), width=2)
    draw.text((MARGIN + 22, y + 18), "media-package guide", fill=(18, 18, 18), font=_font(24, bold=True))
    draw.text((MARGIN + 22, y + 52), "source panel with fixed labels", fill=(68, 68, 68), font=body_font)
    slot = _fit(NAV_MEDIA_PACKAGE_V3_AI_SLOT, (left_w - 44, gate_h - 106), cover=False)
    slot_y = y + 82
    canvas.paste(slot, (MARGIN + 22, slot_y))
    draw.rectangle((MARGIN + 22, slot_y, MARGIN + 22 + left_w - 44, slot_y + gate_h - 106), outline=(138, 138, 138), width=2)

    boundary_cards = [
        ("selected qualitative videos", "visual audit and rebuttal figures", "qualitative media", (38, 95, 156), ["6 selected still pairs", "case ids + outcomes", "caption-only scope"]),
        ("route overlays", "trajectory-shape inspection", "selected route context", (0, 133, 100), ["6 route contact sheets", "red/green trajectories", "paired-run context"]),
        ("manifest mapping", "clip id, stills, metrics, check", "audit context", (211, 116, 32), ["clip -> case id", "still -> metric row", "README status record"]),
        ("author approval", "raw videos wait for media approval", "approval-gated media", (130, 74, 145), ["legal approval flag", "supplement-safe packet", "media bundle after approval"]),
    ]
    card_gap = 16
    card_w = (right_w - card_gap) // 2
    card_h = (gate_h - card_gap) // 2
    for idx, (title, evidence, boundary, accent, details) in enumerate(boundary_cards):
        col = idx % 2
        row = idx // 2
        _draw_upload_gate_status_card(
            draw,
            x=right_x + col * (card_w + card_gap),
            y=y + row * (card_h + card_gap),
            w=card_w,
            h=card_h,
            title=title,
            evidence=evidence,
            boundary=boundary,
            accent=accent,
            details=details,
        )

    draw.text(
        (MARGIN, height - 28),
        "Reading note: selected stills, route overlays, and manifest mapping make the video evidence inspectable as qualitative media.",
        fill=(82, 82, 82),
        font=_font(14),
    )

    NAVIGATION_MEDIA_BOUNDARY_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(NAVIGATION_MEDIA_BOUNDARY_OUT)
    print(NAVIGATION_MEDIA_BOUNDARY_OUT)


def _draw_upload_gate_status_card(
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    evidence: str,
    boundary: str,
    accent: tuple[int, int, int],
    details: list[str] | None = None,
) -> None:
    title_font = _font(18, bold=True)
    body_font = _font(13)
    detail_font = _font(12)
    ready_font = _font(14, bold=True)

    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(252, 252, 252), outline=(176, 176, 176), width=2)
    draw.rectangle((x, y, x + 8, y + h), fill=accent)
    draw.text((x + 18, y + 12), title, fill=(18, 18, 18), font=title_font)
    draw.rounded_rectangle((x + w - 88, y + 12, x + w - 18, y + 36), radius=6, fill=(245, 249, 255), outline=accent, width=2)
    draw.text((x + w - 70, y + 16), "ready", fill=accent, font=ready_font)
    draw.text((x + 18, y + 46), evidence, fill=(54, 54, 54), font=body_font)
    if details:
        row_y = y + 78
        row_h = 29
        row_gap = 9
        for idx, detail in enumerate(details[:3]):
            yy = row_y + idx * (row_h + row_gap)
            draw.rounded_rectangle((x + 18, yy, x + w - 18, yy + row_h), radius=5, fill=(244, 248, 251), outline=(184, 196, 204), width=1)
            draw.ellipse((x + 30, yy + 8, x + 42, yy + 20), fill=accent)
            draw.text((x + 54, yy + 6), detail, fill=(38, 38, 38), font=detail_font)
            for tick in range(3):
                xx = x + w - 78 + tick * 18
                draw.rectangle((xx, yy + 9, xx + 10, yy + 19), fill=(235, 240, 243), outline=accent, width=1)
    draw.text((x + 18, y + h - 42), boundary, fill=(211, 116, 32), font=body_font)


def _draw_upload_visual_tile(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    path: Path,
    crop: tuple[int, int, int, int] | None = None,
) -> None:
    label_font = _font(15, bold=True)
    if crop is None:
        image = _fit(path, (w, h), cover=True)
    else:
        image = _crop_fit(path, crop, (w, h))
    canvas.paste(image, (x, y))
    draw.rectangle((x, y, x + w, y + h), outline=(135, 135, 135), width=2)
    draw.rectangle((x, y, x + w, y + 28), fill=(248, 248, 248), outline=(135, 135, 135), width=1)
    draw.text((x + 8, y + 6), title, fill=(28, 28, 28), font=label_font)


def build_internnav_upload_gate_closure_card() -> None:
    width = 1800
    height = 2200
    canvas = Image.new("RGB", (width, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(34, bold=True)
    note_font = _font(18)
    body_font = _font(15)

    y = MARGIN
    draw.text((MARGIN, y), "Official-scene upload-scope closure", fill=(18, 18, 18), font=heading_font)
    y += 48
    draw.text(
        (MARGIN, y),
        "Visual replacement for the sparse closure table: real stills show what is packaged; status cards state what is in scope.",
        fill=(66, 66, 66),
        font=note_font,
    )
    y += 58

    media_x = MARGIN
    media_w = width - 2 * MARGIN
    media_h = 1040
    draw.rounded_rectangle((media_x, y, media_x + media_w, y + media_h), radius=8, fill=(252, 252, 252), outline=(176, 176, 176), width=2)
    draw.text((media_x + 20, y + 18), "source navigation media wall", fill=(18, 18, 18), font=_font(25, bold=True))
    draw.text((media_x + 20, y + 54), "nine real still, route, and package panels anchor the upload-scope closure.", fill=(68, 68, 68), font=body_font)

    tile_gap = 16
    tile_x0 = media_x + 20
    tile_y0 = y + 92
    tile_w = (media_w - 40 - 2 * tile_gap) // 3
    tile_h = (media_h - 112 - 2 * tile_gap) // 3
    media_tiles = [
        ("selected rollout stills", NAV_STILLS, (0, 150, 1106, 760)),
        ("0036/0066 readable routes", NAV_0036_MAIN, (360, 90, 1740, 790)),
        ("media-scope context", NAVIGATION_MEDIA_BOUNDARY_OUT, None),
        ("selected case 01", NAV_SELECTED_CASE, (0, 42, 1106, 360)),
        ("selected case 02", NAV_SELECTED_CASE2, (0, 42, 1106, 360)),
        ("selected case 03", NAV_SELECTED_CASE3, (0, 42, 1106, 360)),
        ("route case 01", NAV_0036_CASE, (0, 34, 770, 338)),
        ("route case 02", NAV_0036_CASE2, (0, 34, 770, 338)),
        ("route case 03", NAV_0036_CASE3, (0, 34, 770, 338)),
    ]
    for idx, (title, path, crop) in enumerate(media_tiles):
        col = idx % 3
        row = idx // 3
        _draw_upload_visual_tile(
            canvas,
            draw,
            x=tile_x0 + col * (tile_w + tile_gap),
            y=tile_y0 + row * (tile_h + tile_gap),
            w=tile_w,
            h=tile_h,
            title=title,
            path=path,
            crop=crop,
        )

    y += media_h + 24
    closure_h = 590
    left_w = 860
    right_x = MARGIN + left_w + 24
    right_w = width - MARGIN - right_x
    draw.rounded_rectangle((MARGIN, y, MARGIN + left_w, y + closure_h), radius=8, fill=(252, 252, 252), outline=(176, 176, 176), width=2)
    draw.text((MARGIN + 20, y + 18), "upload-scope guide", fill=(18, 18, 18), font=_font(23, bold=True))
    draw.text((MARGIN + 20, y + 52), "source panel; upload packet screenshot can replace it", fill=(68, 68, 68), font=body_font)
    ai_image = _fit(NAV_UPLOAD_GATE_V2_AI_SLOT, (left_w - 40, closure_h - 92), cover=False)
    canvas.paste(ai_image, (MARGIN + 20, y + 78))
    draw.rectangle((MARGIN + 20, y + 78, MARGIN + left_w - 20, y + closure_h - 14), outline=(135, 135, 135), width=2)

    gates = [
        ("official scene scope", "official KuJiaLe / InteriorAgent plan", "official scope only", (38, 95, 156)),
        ("multi-run statistics", "repeated original/noMDL run rows", "NVIDIA official baseline unavailable", (0, 133, 100)),
        ("selected video package", "compressed clips, stills, manifest", "selected qualitative only", (211, 116, 32)),
        ("final scope audit", "scope checklist and decision record", "no broader route result", (130, 74, 145)),
    ]
    card_gap = 16
    card_w = (right_w - card_gap) // 2
    card_h = (closure_h - card_gap) // 2
    for idx, (title, evidence, boundary, accent) in enumerate(gates):
        col = idx % 2
        row = idx // 2
        _draw_upload_gate_status_card(
            draw,
            x=right_x + col * (card_w + card_gap),
            y=y + row * (card_h + card_gap),
            w=card_w,
            h=card_h,
            title=title,
            evidence=evidence,
            boundary=boundary,
            accent=accent,
        )

    y += closure_h + 24
    boundary_h = height - y - MARGIN
    draw.rounded_rectangle((MARGIN, y, width - MARGIN, y + boundary_h), radius=8, fill=(255, 250, 245), outline=(211, 116, 32), width=2)
    draw.text((MARGIN + 22, y + 22), "paper-result scope", fill=(211, 116, 32), font=_font(25, bold=True))
    draw.text((MARGIN + 22, y + 58), "The media wall makes the selected package inspectable; it summarizes the selected media scope.", fill=(45, 45, 45), font=_font(16))
    strip_y = y + 96
    strip_w = 920
    small_gap = 12
    small_w = (strip_w - 3 * small_gap) // 4
    small_h = boundary_h - 138
    small_tiles = [
        ("route still", NAV_SELECTED_CASE, (0, 42, 1106, 360)),
        ("route still", NAV_SELECTED_CASE2, (0, 42, 1106, 360)),
        ("route map", NAV_0036_CASE2, (0, 34, 770, 338)),
        ("route map", NAV_0036_CASE3, (0, 34, 770, 338)),
    ]
    for idx, (title, path, crop) in enumerate(small_tiles):
        _draw_upload_visual_tile(
            canvas,
            draw,
            x=MARGIN + 22 + idx * (small_w + small_gap),
            y=strip_y,
            w=small_w,
            h=small_h,
            title=title,
            path=path,
            crop=crop,
        )
    boundary_x = MARGIN + 22 + strip_w + 28
    for idx, line in enumerate(
        [
            "99-episode paired run remains the quantitative result.",
            "Selected videos and stills are qualitative inspection media.",
            "Upload happens only after final author/legal approval.",
            "This closure card summarizes the media scope.",
        ]
    ):
        draw.text((boundary_x, strip_y + idx * 58), line, fill=(45, 45, 45), font=_font(17))

    draw.text(
        (MARGIN, height - 28),
        "Reading note: the card replaces a sparse status table in the PDF; the original machine-readable status artifacts remain source under paper/shared/evidence.",
        fill=(82, 82, 82),
        font=_font(14),
    )

    INTERNNAV_UPLOAD_GATE_CLOSURE_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(INTERNNAV_UPLOAD_GATE_CLOSURE_OUT)
    print(INTERNNAV_UPLOAD_GATE_CLOSURE_OUT)


def _draw_contact_row(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
    title: str,
    note: str,
    items: list[tuple[Path, tuple[int, int, int, int]]],
) -> int:
    row_h = 365
    label_w = 280
    label_x = MARGIN + 18
    image_x = MARGIN + label_w + GAP
    content_w = WIDTH - MARGIN - image_x
    thumb_gap = 16
    thumb_w = (content_w - thumb_gap * (len(items) - 1)) // len(items)
    thumb_h = row_h - 56
    title_font = _font(22, bold=True)
    note_font = _font(16)
    chip_font = _font(14, bold=True)

    draw.rounded_rectangle((MARGIN, y, WIDTH - MARGIN, y + row_h), radius=8, fill=(252, 252, 252), outline=(176, 176, 176), width=2)
    draw.text((label_x, y + 22), title, fill=(20, 20, 20), font=title_font)
    draw.text((label_x, y + 60), note, fill=(65, 65, 65), font=note_font)
    draw.text((label_x, y + row_h - 38), "tracked paper figure", fill=(95, 95, 95), font=note_font)

    for idx, (path, crop) in enumerate(items):
        x = image_x + idx * (thumb_w + thumb_gap)
        image = _crop_contain(path, crop, (thumb_w, thumb_h))
        canvas.paste(image, (x, y + 28))
        draw.rectangle((x, y + 28, x + thumb_w, y + 28 + thumb_h), outline=(135, 135, 135), width=2)
        chip = f"{idx + 1:02d}"
        draw.rectangle((x + 8, y + 36, x + 48, y + 60), fill=(18, 18, 18))
        draw.text((x + 16, y + 38), chip, fill=(255, 255, 255), font=chip_font)
    return y + row_h


def _draw_vlm_guide_row(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
    index: str,
    title: str,
    note: str,
    table_label: str,
    items: list[tuple[Path, tuple[int, int, int, int] | None] | tuple[Path, None, tuple[float, float, float, float]]],
) -> int:
    row_h = 330
    label_w = 260
    table_w = 168
    inner_gap = 18
    thumb_x = MARGIN + label_w + inner_gap
    table_x = WIDTH - MARGIN - table_w
    content_w = table_x - thumb_x - inner_gap
    thumb_gap = 14
    thumb_w = (content_w - thumb_gap * (len(items) - 1)) // len(items)
    thumb_h = row_h - 82
    title_font = _font(23, bold=True)
    note_font = _font(16)
    badge_font = _font(20, bold=True)
    table_font = _font(16, bold=True)

    draw.rounded_rectangle((MARGIN, y, WIDTH - MARGIN, y + row_h), radius=8, fill=(252, 252, 252), outline=(178, 178, 178), width=2)
    draw.rectangle((MARGIN + 22, y + 24, MARGIN + 62, y + 64), outline=(45, 45, 45), width=2)
    draw.text((MARGIN + 35, y + 28), index, fill=(18, 18, 18), font=badge_font)
    draw.text((MARGIN + 78, y + 23), title, fill=(18, 18, 18), font=title_font)
    draw.text((MARGIN + 78, y + 58), note, fill=(68, 68, 68), font=note_font)
    draw.text((MARGIN + 78, y + row_h - 36), "source render crops", fill=(96, 96, 96), font=note_font)

    image_y = y + 74
    for idx, item in enumerate(items):
        x = thumb_x + idx * (thumb_w + thumb_gap)
        if len(item) == 3:
            path, crop, bbox = item
            image = _fit_with_bbox(path, (thumb_w, thumb_h), bbox)
        else:
            path, crop = item
            assert crop is not None
            image = _crop_fit(path, crop, (thumb_w, thumb_h))
        canvas.paste(image, (x, image_y))
        draw.rectangle((x, image_y, x + thumb_w, image_y + thumb_h), outline=(135, 135, 135), width=2)

    arrow_y = y + row_h // 2
    draw.line((table_x - 36, arrow_y, table_x - 12, arrow_y), fill=(38, 95, 156), width=4)
    draw.polygon([(table_x - 12, arrow_y), (table_x - 24, arrow_y - 8), (table_x - 24, arrow_y + 8)], fill=(38, 95, 156))
    draw.rounded_rectangle((table_x, y + 92, table_x + table_w, y + 236), radius=8, fill=(245, 249, 255), outline=(38, 95, 156), width=2)
    grid_x = table_x + 28
    grid_y = y + 116
    cell = 24
    for offset in range(5):
        draw.line((grid_x, grid_y + offset * cell, grid_x + 4 * cell, grid_y + offset * cell), fill=(93, 130, 174), width=1)
        draw.line((grid_x + offset * cell, grid_y, grid_x + offset * cell, grid_y + 4 * cell), fill=(93, 130, 174), width=1)
    draw.text((table_x + 28, y + 250), table_label, fill=(38, 95, 156), font=table_font)
    return y + row_h


def build_grscenes_vlm_visual_guide() -> None:
    width = 1800
    height = 1710
    canvas = Image.new("RGB", (width, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(34, bold=True)
    note_font = _font(18)
    label_font = _font(21, bold=True)
    small_font = _font(16)

    y = MARGIN
    draw.text((MARGIN, y), "GRScenes VLM reading panel", fill=(18, 18, 18), font=heading_font)
    y += 48
    draw.text(
        (MARGIN, y),
        "Real render crops linking clean target views, scene context, zoom-style target framing, and normalized-1000 scoring tables.",
        fill=(66, 66, 66),
        font=note_font,
    )
    y += 54

    y = _draw_vlm_guide_row(
        canvas,
        draw,
        y=y,
        index="1",
        title="clean target-box views",
        note="post-repair target projections",
        table_label="Table S4",
        items=[
            (VLM_BACKPACK_ORIGINAL, None, (207.811, 105.285, 376.441, 364.938)),
            (VLM_CLOCK_ORIGINAL, None, (211.647, 107.436, 370.171, 360.234)),
            (VLM_BOTTLE_ORIGINAL, None, (230.385, 89.121, 369.378, 372.696)),
            (VLM_CUP_ORIGINAL, None, (183.338, 133.12, 416.662, 331.46)),
        ],
    ) + GAP
    y = _draw_vlm_guide_row(
        canvas,
        draw,
        y=y,
        index="2",
        title="scene context pairs",
        note="matched MDL and noMDL views",
        table_label="Table S5",
        items=[
            (GRSCENE_QUALITATIVE, (24, 48, 444, 286)),
            (GRSCENE_QUALITATIVE, (468, 48, 890, 286)),
            (GRSCENE_QUALITATIVE, (24, 334, 444, 570)),
            (GRSCENE_QUALITATIVE, (468, 334, 890, 570)),
        ],
    ) + GAP
    y = _draw_vlm_guide_row(
        canvas,
        draw,
        y=y,
        index="3",
        title="viewpoint and material context",
        note="render evidence before stress tables",
        table_label="Table S6",
        items=[
            (RENDER_SCENE_WIDE, (34, 546, 888, 884)),
            (RENDER_SCENE_WIDE, (912, 546, 1766, 884)),
            (SUPPLEMENT_RENDER_ATLAS, (40, 1900, 880, 2035)),
            (SUPPLEMENT_RENDER_ATLAS, (930, 1900, 1760, 2035)),
        ],
    ) + GAP

    protocol_h = 280
    draw.rounded_rectangle((MARGIN, y, WIDTH - MARGIN, y + protocol_h), radius=8, fill=(252, 252, 252), outline=(178, 178, 178), width=2)
    draw.rectangle((MARGIN + 22, y + 24, MARGIN + 62, y + 64), outline=(45, 45, 45), width=2)
    draw.text((MARGIN + 35, y + 28), "4", fill=(18, 18, 18), font=_font(20, bold=True))
    draw.text((MARGIN + 78, y + 23), "normalized-1000 coordinate protocol", fill=(18, 18, 18), font=label_font)
    draw.text((MARGIN + 78, y + 58), "target box and point metrics are scored in the same [0, 1000] frame", fill=(68, 68, 68), font=small_font)

    crop = _fit_with_bbox(VLM_CLOCK_ORIGINAL, (330, 185), (211.647, 107.436, 370.171, 360.234))
    image_x = MARGIN + 330
    image_y = y + 88
    canvas.paste(crop, (image_x, image_y))
    draw.rectangle((image_x, image_y, image_x + 330, image_y + 185), outline=(135, 135, 135), width=2)
    draw.rectangle((image_x + 6, image_y + 6, image_x + 324, image_y + 179), outline=(38, 95, 156), width=2)
    draw.text((image_x - 22, image_y + 2), "0", fill=(38, 95, 156), font=small_font)
    draw.text((image_x + 288, image_y + 188), "1000", fill=(38, 95, 156), font=small_font)

    box_x = image_x + 430
    box_y = y + 112
    draw.line((image_x + 350, y + 182, box_x - 30, y + 182), fill=(0, 133, 100), width=3)
    draw.polygon([(box_x - 30, y + 182), (box_x - 44, y + 174), (box_x - 44, y + 190)], fill=(0, 133, 100))
    draw.rectangle((box_x, box_y, box_x + 240, box_y + 132), outline=(0, 133, 100), width=5)
    draw.text((box_x + 12, box_y - 30), "target box", fill=(18, 18, 18), font=small_font)
    draw.text((box_x - 46, box_y - 18), "(x1,y1)", fill=(0, 133, 100), font=small_font)
    draw.text((box_x + 170, box_y - 18), "(x2,y1)", fill=(0, 133, 100), font=small_font)
    draw.text((box_x - 46, box_y + 138), "(x1,y2)", fill=(0, 133, 100), font=small_font)
    draw.text((box_x + 170, box_y + 138), "(x2,y2)", fill=(0, 133, 100), font=small_font)

    card_x = box_x + 320
    draw.rounded_rectangle((card_x, y + 92, card_x + 280, y + 230), radius=8, fill=(245, 249, 255), outline=(38, 95, 156), width=2)
    draw.text((card_x + 24, y + 112), "scoring contract", fill=(38, 95, 156), font=label_font)
    draw.text((card_x + 24, y + 150), "answer category", fill=(45, 45, 45), font=small_font)
    draw.text((card_x + 24, y + 178), "point inside target box", fill=(45, 45, 45), font=small_font)

    table_x = WIDTH - MARGIN - 168
    draw.line((card_x + 300, y + 164, table_x - 18, y + 164), fill=(201, 111, 27), width=4)
    draw.polygon([(table_x - 18, y + 164), (table_x - 32, y + 156), (table_x - 32, y + 172)], fill=(201, 111, 27))
    draw.rounded_rectangle((table_x, y + 92, table_x + 168, y + 230), radius=8, fill=(255, 250, 245), outline=(201, 111, 27), width=2)
    draw.text((table_x + 25, y + 246), "Tables S4-S6", fill=(201, 111, 27), font=_font(16, bold=True))
    for offset in range(5):
        draw.line((table_x + 30, y + 118 + offset * 22, table_x + 126, y + 118 + offset * 22), fill=(210, 154, 92), width=1)
        draw.line((table_x + 30 + offset * 24, y + 118, table_x + 30 + offset * 24, y + 206), fill=(210, 154, 92), width=1)

    y = y + protocol_h + GAP
    _draw_opener_band(
        canvas,
        draw,
        y=y,
        title="source guide audit strip",
        tiles=[
            ("route map", _fit(GRSCENES_VLM_READING_ROUTE_V2_AI_SLOT, (280, 210), cover=False)),
            ("backpack pair", _fit_with_bbox(VLM_BACKPACK_CONVERTED, (280, 210), (207.811, 105.285, 376.441, 364.938))),
            ("clock pair", _fit_with_bbox(VLM_CLOCK_CONVERTED, (280, 210), (211.647, 107.436, 370.171, 360.234))),
            ("bottle pair", _fit_with_bbox(VLM_BOTTLE_CONVERTED, (280, 210), (230.385, 89.121, 369.378, 372.696))),
            ("cup pair", _fit_with_bbox(VLM_CUP_CONVERTED, (280, 210), (183.338, 133.12, 416.662, 331.46))),
            ("context", _crop_fit(RENDER_SCENE_WIDE, (912, 546, 1766, 884), (280, 210))),
        ],
        band_h=210,
    )

    GRSCENES_VLM_GUIDE_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(GRSCENES_VLM_GUIDE_OUT)
    print(GRSCENES_VLM_GUIDE_OUT)


def _draw_case_pair_card(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    status: str,
    original: Path,
    converted: Path,
    bbox: tuple[float, float, float, float],
) -> None:
    title_font = _font(19, bold=True)
    body_font = _font(14)
    chip_font = _font(14, bold=True)
    image_gap = 12
    image_w = (w - 30 - image_gap) // 2
    image_h = h - 108
    image_y = y + 88

    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(252, 252, 252), outline=(178, 178, 178), width=2)
    draw.text((x + 14, y + 13), title, fill=(18, 18, 18), font=title_font)
    chip_x = x + 14
    chip_y = y + 40
    chip_w = min(w - 28, max(160, len(status) * 8 + 28))
    draw.rounded_rectangle((chip_x, chip_y, chip_x + chip_w, chip_y + 22), radius=5, fill=(245, 249, 255), outline=(38, 95, 156), width=1)
    draw.text((chip_x + 10, chip_y + 3), status, fill=(38, 95, 156), font=chip_font)

    for idx, (label, path) in enumerate((("original", original), ("converted", converted))):
        image_x = x + 14 + idx * (image_w + image_gap)
        draw.text((image_x, image_y - 18), label, fill=(68, 68, 68), font=body_font)
        image = _fit_with_protocol_overlay(path, (image_w, image_h), bbox)
        canvas.paste(image, (image_x, image_y))
        draw.rectangle((image_x, image_y, image_x + image_w, image_y + image_h), outline=(135, 135, 135), width=2)


def _draw_case_band(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
    band_title: str,
    band_note: str,
    table_label: str,
    cases: list[dict[str, object]],
) -> int:
    band_h = 540
    label_w = 250
    content_x = MARGIN + label_w + GAP
    content_w = WIDTH - MARGIN - content_x
    card_gap = 18
    card_w = (content_w - card_gap) // 2
    title_font = _font(25, bold=True)
    note_font = _font(16)
    table_font = _font(20, bold=True)

    draw.rounded_rectangle((MARGIN, y, WIDTH - MARGIN, y + band_h), radius=8, fill=(248, 248, 248), outline=(170, 170, 170), width=2)
    draw.text((MARGIN + 20, y + 24), band_title, fill=(18, 18, 18), font=title_font)
    draw.text((MARGIN + 20, y + 62), band_note, fill=(68, 68, 68), font=note_font)
    draw.rounded_rectangle((MARGIN + 20, y + band_h - 74, MARGIN + label_w - 20, y + band_h - 32), radius=8, fill=(255, 250, 245), outline=(211, 116, 32), width=2)
    draw.text((MARGIN + 46, y + band_h - 64), table_label, fill=(211, 116, 32), font=table_font)

    for idx, case in enumerate(cases):
        _draw_case_pair_card(
            canvas,
            draw,
            x=content_x + idx * (card_w + card_gap),
            y=y + 24,
            w=card_w,
            h=band_h - 48,
            title=str(case["title"]),
            status=str(case["status"]),
            original=case["original"],  # type: ignore[arg-type]
            converted=case["converted"],  # type: ignore[arg-type]
            bbox=case["bbox"],  # type: ignore[arg-type]
        )
    return y + band_h


def build_grscenes_diagnostic_case_atlas() -> None:
    width = 1800
    height = 1820
    canvas = Image.new("RGB", (width, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(34, bold=True)
    note_font = _font(18)

    y = MARGIN
    draw.text((MARGIN, y), "GRScenes diagnostic case atlas", fill=(18, 18, 18), font=heading_font)
    y += 48
    draw.text(
        (MARGIN, y),
        "Real target-view render pairs used as visual anchors for failure taxonomy, PASS-only provenance, and zoom stress tables.",
        fill=(66, 66, 66),
        font=note_font,
    )
    y += 56

    y = _draw_case_band(
        canvas,
        draw,
        y=y,
        band_title="Failure taxonomy",
        band_note="selected diagnostic rows",
        table_label="Table S4",
        cases=[
            {
                "title": "bottle | zoom_018",
                "status": "raw point flip diagnostic",
                "original": VLM_BOTTLE_ORIGINAL,
                "converted": VLM_BOTTLE_CONVERTED,
                "bbox": (230.385, 89.121, 369.378, 372.696),
            },
            {
                "title": "clock | zoom_018",
                "status": "answer flip diagnostic",
                "original": VLM_CLOCK_ORIGINAL,
                "converted": VLM_CLOCK_CONVERTED,
                "bbox": (211.647, 107.436, 370.171, 360.234),
            },
        ],
    ) + GAP
    y = _draw_case_band(
        canvas,
        draw,
        y=y,
        band_title="PASS-only pilot",
        band_note="clean-rerender provenance",
        table_label="Table S5",
        cases=[
            {
                "title": "bottle | zoom_018",
                "status": "PASS-pool target view",
                "original": VLM_BOTTLE_ORIGINAL,
                "converted": VLM_BOTTLE_CONVERTED,
                "bbox": (230.385, 89.121, 369.378, 372.696),
            },
            {
                "title": "cup | zoom_020",
                "status": "PASS-pool target view",
                "original": VLM_CUP_ORIGINAL,
                "converted": VLM_CUP_CONVERTED,
                "bbox": (183.338, 133.12, 416.662, 331.46),
            },
        ],
    ) + GAP
    _draw_case_band(
        canvas,
        draw,
        y=y,
        band_title="Zoom stress",
        band_note="target-visible stress context",
        table_label="Table S6",
        cases=[
            {
                "title": "backpack | zoom_018",
                "status": "zoom stress pair",
                "original": VLM_BACKPACK_ORIGINAL,
                "converted": VLM_BACKPACK_CONVERTED,
                "bbox": (207.811, 105.285, 376.441, 364.938),
            },
            {
                "title": "clock | zoom_018",
                "status": "zoom stress pair",
                "original": VLM_CLOCK_ORIGINAL,
                "converted": VLM_CLOCK_CONVERTED,
                "bbox": (211.647, 107.436, 370.171, 360.234),
            },
        ],
    )

    GRSCENES_DIAGNOSTIC_CASE_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(GRSCENES_DIAGNOSTIC_CASE_OUT)
    print(GRSCENES_DIAGNOSTIC_CASE_OUT)


def _draw_stress_pair_card(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    note: str,
    original: Path,
    converted: Path,
    bbox: tuple[float, float, float, float],
    accent: tuple[int, int, int],
) -> None:
    title_font = _font(21, bold=True)
    note_font = _font(14)
    label_font = _font(14, bold=True)
    image_gap = 12
    image_w = (w - 34 - image_gap) // 2
    image_h = h - 92
    image_y = y + 70

    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(252, 252, 252), outline=(178, 178, 178), width=2)
    draw.rectangle((x, y, x + 8, y + h), fill=accent)
    draw.text((x + 18, y + 13), title, fill=(18, 18, 18), font=title_font)
    draw.text((x + 18, y + 42), note, fill=(70, 70, 70), font=note_font)

    for idx, (label, path) in enumerate((("original MDL", original), ("noMDL", converted))):
        image_x = x + 18 + idx * (image_w + image_gap)
        draw.text((image_x, image_y - 18), label, fill=accent if idx else (62, 62, 62), font=label_font)
        image = _fit_with_protocol_overlay(path, (image_w, image_h), bbox)
        canvas.paste(image, (image_x, image_y))
        draw.rectangle((image_x, image_y, image_x + image_w, image_y + image_h), outline=(135, 135, 135), width=2)


def _draw_process_card(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
) -> None:
    title_font = _font(22, bold=True)
    body_font = _font(15)
    image_w = min(520, (w - 82) // 2)
    image_h = min(270, h - 112)
    image = _fit(VLM_SCORING_GATE_AI_SLOT, (image_w, image_h), cover=False)

    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(252, 252, 252), outline=(178, 178, 178), width=2)
    draw.text((x + 18, y + 16), "prompt / point / score check", fill=(18, 18, 18), font=title_font)
    draw.text((x + 18, y + 48), "orientation panel", fill=(88, 88, 88), font=body_font)
    canvas.paste(image, (x + 18, y + 72))
    draw.rectangle((x + 18, y + 72, x + 18 + image_w, y + 72 + image_h), outline=(135, 135, 135), width=2)

    card_x = x + image_w + 46
    card_y = y + 72
    card_bottom = y + h - 26
    draw.rounded_rectangle((card_x, card_y, x + w - 18, card_bottom), radius=8, fill=(255, 250, 245), outline=(211, 116, 32), width=2)
    draw.text((card_x + 18, card_y + 20), "result scope", fill=(211, 116, 32), font=title_font)
    for idx, line in enumerate(
        [
            "source renders carry evidence",
            "scoring panel explains scoring flow",
            "tables remain the metric record",
            "table context",
        ]
    ):
        draw.text((card_x + 22, card_y + 62 + idx * 36), line, fill=(45, 45, 45), font=body_font)


def build_grscenes_vlm_stress_render_strip() -> None:
    width = 1500
    height = 1680
    canvas = Image.new("RGB", (width, height), (236, 236, 236))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(34, bold=True)
    note_font = _font(18)
    small_font = _font(14)

    y = MARGIN
    draw.text((MARGIN, y), "GRScenes VLM stress render strip", fill=(18, 18, 18), font=heading_font)
    y += 48
    draw.text(
        (MARGIN, y),
        "Render-heavy bridge for Tables S4-S6: target-view pairs and the process panel stay aligned.",
        fill=(66, 66, 66),
        font=note_font,
    )
    y += 48

    card_gap = 18
    card_w = (width - 2 * MARGIN - card_gap) // 2
    card_h = 455
    _draw_stress_pair_card(
        canvas,
        draw,
        x=MARGIN,
        y=y,
        w=card_w,
        h=card_h,
        title="PASS-only provenance | bottle",
        note="target-visible pair retained before clean-pool scaling",
        original=VLM_BOTTLE_ORIGINAL,
        converted=VLM_BOTTLE_CONVERTED,
        bbox=(230.385, 89.121, 369.378, 372.696),
        accent=(38, 95, 156),
    )
    _draw_stress_pair_card(
        canvas,
        draw,
        x=MARGIN + card_w + card_gap,
        y=y,
        w=card_w,
        h=card_h,
        title="PASS-only provenance | cup",
        note="clean-rerender target view with matched cameras",
        original=VLM_CUP_ORIGINAL,
        converted=VLM_CUP_CONVERTED,
        bbox=(183.338, 133.12, 416.662, 331.46),
        accent=(0, 133, 100),
    )
    y += card_h + card_gap

    _draw_stress_pair_card(
        canvas,
        draw,
        x=MARGIN,
        y=y,
        w=card_w,
        h=card_h,
        title="zoom stress | backpack",
        note="material/color/lighting stress row for visible-target checks",
        original=VLM_BACKPACK_ORIGINAL,
        converted=VLM_BACKPACK_CONVERTED,
        bbox=(207.811, 105.285, 376.441, 364.938),
        accent=(211, 116, 32),
    )
    _draw_stress_pair_card(
        canvas,
        draw,
        x=MARGIN + card_w + card_gap,
        y=y,
        w=card_w,
        h=card_h,
        title="zoom stress | clock",
        note="selected diagnostic pair with case-level context",
        original=VLM_CLOCK_ORIGINAL,
        converted=VLM_CLOCK_CONVERTED,
        bbox=(211.647, 107.436, 370.171, 360.234),
        accent=(130, 74, 145),
    )
    y += card_h + card_gap

    _draw_process_card(canvas, draw, x=MARGIN, y=y, w=width - 2 * MARGIN, h=430)
    draw.text(
        (MARGIN, height - 28),
        "Reading note: selected render pairs make the table rows inspectable; aggregate results remain tied to source metrics and frozen source artifacts.",
        fill=(82, 82, 82),
        font=small_font,
    )

    GRSCENES_VLM_STRESS_STRIP_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(GRSCENES_VLM_STRESS_STRIP_OUT)
    print(GRSCENES_VLM_STRESS_STRIP_OUT)


def _draw_table_companion_pair(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    note: str,
    original: Path,
    converted: Path,
    bbox: tuple[float, float, float, float],
    accent: tuple[int, int, int],
) -> None:
    title_font = _font(18, bold=True)
    note_font = _font(12)
    label_font = _font(12, bold=True)
    gap = 10
    image_w = (w - 30 - gap) // 2
    image_h = h - 92
    image_y = y + 74

    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(252, 252, 252), outline=(180, 180, 180), width=2)
    draw.rectangle((x, y, x + 7, y + h), fill=accent)
    draw.text((x + 16, y + 10), title, fill=(20, 20, 20), font=title_font)
    draw.text((x + 16, y + 36), note, fill=(72, 72, 72), font=note_font)

    for idx, (label, path) in enumerate((("original", original), ("noMDL", converted))):
        image_x = x + 16 + idx * (image_w + gap)
        draw.text((image_x, image_y - 16), label, fill=accent if idx else (68, 68, 68), font=label_font)
        image = _fit_with_protocol_overlay(path, (image_w, image_h), bbox)
        canvas.paste(image, (image_x, image_y))
        draw.rectangle((image_x, image_y, image_x + image_w, image_y + image_h), outline=(140, 140, 140), width=2)


def _draw_table_reading_gate(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    accent: tuple[int, int, int],
    bullets: list[str],
    slot_path: Path = GRSCENES_TABLE_READING_GATE_AI_SLOT,
    title: str = "table-reading check",
    image_h: int = 230,
) -> None:
    title_font = _font(20, bold=True)
    body_font = _font(13)
    bullet_font = _font(14, bold=True)
    image = _fit(slot_path, (w - 34, image_h), cover=False)

    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(252, 252, 252), outline=(178, 178, 178), width=2)
    draw.text((x + 17, y + 14), title, fill=(20, 20, 20), font=title_font)
    draw.text((x + 17, y + 42), "orientation panel", fill=(82, 82, 82), font=body_font)
    canvas.paste(image, (x + 17, y + 66))
    draw.rectangle((x + 17, y + 66, x + 17 + w - 34, y + 66 + image_h), outline=(138, 138, 138), width=2)

    bullet_y = y + image_h + 92
    for idx, line in enumerate(bullets):
        dot_y = bullet_y + idx * 38 + 7
        draw.ellipse((x + 20, dot_y, x + 31, dot_y + 11), fill=accent)
        draw.text((x + 42, bullet_y + idx * 38), line, fill=(45, 45, 45), font=bullet_font)

    draw.rounded_rectangle((x + 17, y + h - 58, x + w - 17, y + h - 18), radius=7, fill=(246, 250, 255), outline=accent, width=2)
    draw.text((x + 34, y + h - 47), "table context", fill=accent, font=body_font)


def _draw_failure_taxonomy_matrix_band(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
    h: int,
    accent: tuple[int, int, int],
) -> int:
    x = 34
    w = canvas.width - 68
    title_font = _font(20, bold=True)
    note_font = _font(13)
    label_font = _font(12, bold=True)
    tile_gap = 10
    row_gap = 12
    title_h = 58
    tile_w = (w - 4 * tile_gap) // 5
    tile_h = (h - title_h - 20 - row_gap) // 2
    tiles = [
        ("backpack original", VLM_BACKPACK_ORIGINAL, (207.811, 105.285, 376.441, 364.938)),
        ("backpack noMDL", VLM_BACKPACK_CONVERTED, (207.811, 105.285, 376.441, 364.938)),
        ("clock original", VLM_CLOCK_ORIGINAL, (211.647, 107.436, 370.171, 360.234)),
        ("clock noMDL", VLM_CLOCK_CONVERTED, (211.647, 107.436, 370.171, 360.234)),
        ("bottle original", VLM_BOTTLE_ORIGINAL, (230.385, 89.121, 369.378, 372.696)),
        ("bottle noMDL", VLM_BOTTLE_CONVERTED, (230.385, 89.121, 369.378, 372.696)),
        ("cup original", VLM_CUP_ORIGINAL, (183.338, 133.12, 416.662, 331.46)),
        ("cup noMDL", VLM_CUP_CONVERTED, (183.338, 133.12, 416.662, 331.46)),
        ("picture noMDL", VLM_PICTURE_CONVERTED, (240.087, 100.65, 374.808, 360.903)),
        ("faucet noMDL", VLM_FAUCET_CONVERTED, (215.154, 118.861, 407.249, 356.885)),
    ]

    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(252, 252, 252), outline=(178, 178, 178), width=2)
    draw.rectangle((x, y, x + w, y + 7), fill=accent)
    draw.text((x + 16, y + 16), "source failure-row render matrix", fill=(22, 22, 22), font=title_font)
    draw.text((x + 16, y + 42), "two rows of focused raw render evidence make the selected taxonomy rows inspectable", fill=(70, 70, 70), font=note_font)
    for idx, (label, path, bbox) in enumerate(tiles):
        row = idx // 5
        col = idx % 5
        tile_x = x + 14 + col * (tile_w + tile_gap)
        tile_y = y + title_h + row * (tile_h + row_gap)
        tile = _bbox_focus_tile(path, (tile_w, tile_h), bbox)
        canvas.paste(tile, (tile_x, tile_y))
        draw.rectangle((tile_x, tile_y, tile_x + tile_w, tile_y + tile_h), outline=(135, 135, 135), width=2)
        draw.rectangle((tile_x, tile_y, tile_x + tile_w, tile_y + 22), fill=(248, 248, 248), outline=(135, 135, 135), width=1)
        draw.text((tile_x + 6, tile_y + 4), label, fill=(30, 30, 30), font=label_font)
    return y + h


def _build_grscenes_table_companion(
    *,
    output: Path,
    title: str,
    subtitle: str,
    accent: tuple[int, int, int],
    bullets: list[str],
    pair_order: list[tuple[str, str, Path, Path, tuple[float, float, float, float]]],
    gate_slot: Path = GRSCENES_TABLE_READING_GATE_AI_SLOT,
    gate_title: str = "table-reading check",
    extra_failure_wall: bool = False,
    extra_stress_strip: bool = False,
    extra_pass_strip: bool = False,
) -> None:
    width = 1800
    if extra_failure_wall:
        height = 1640
    elif extra_pass_strip:
        height = 1200
    elif extra_stress_strip:
        height = 1320
    else:
        height = 680
    canvas = Image.new("RGB", (width, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(30, bold=True)
    note_font = _font(16)
    small_font = _font(12)

    y = 34
    draw.text((MARGIN, y), title, fill=(18, 18, 18), font=heading_font)
    y += 42
    draw.text((MARGIN, y), subtitle, fill=(68, 68, 68), font=note_font)

    body_y = 122
    card_gap = 16
    left_w = 1190
    right_w = width - MARGIN * 2 - left_w - card_gap
    card_w = (left_w - card_gap) // 2
    if extra_failure_wall:
        card_h = 274
    elif extra_pass_strip:
        card_h = 260
    else:
        card_h = 238
    for idx, (pair_title, note, original, converted, bbox) in enumerate(pair_order):
        row = idx // 2
        col = idx % 2
        _draw_table_companion_pair(
            canvas,
            draw,
            x=MARGIN + col * (card_w + card_gap),
            y=body_y + row * (card_h + card_gap),
            w=card_w,
            h=card_h,
            title=pair_title,
            note=note,
            original=original,
            converted=converted,
            bbox=bbox,
            accent=accent,
        )

    _draw_table_reading_gate(
        canvas,
        draw,
        x=MARGIN + left_w + card_gap,
        y=body_y,
        w=right_w,
        h=card_h * (3 if extra_failure_wall else 2) + card_gap * (2 if extra_failure_wall else 1),
        accent=accent,
        bullets=bullets,
        slot_path=gate_slot,
        title=gate_title,
        image_h=380 if extra_failure_wall else 230,
    )
    if extra_failure_wall:
        strip_y = body_y + card_h * 3 + card_gap * 2 + 18
        strip_y = _draw_opener_band(
            canvas,
            draw,
            y=strip_y,
            title="source taxonomy edge-case render audit strip",
            tiles=[
                ("picture MDL", _fit_with_bbox(VLM_PICTURE_ORIGINAL, (330, 185), (240.087, 100.65, 374.808, 360.903))),
                ("picture noMDL", _fit_with_bbox(VLM_PICTURE_CONVERTED, (330, 185), (240.087, 100.65, 374.808, 360.903))),
                ("cup view B", _fit_with_bbox(VLM_CUP_ALT_ORIGINAL, (330, 185), (197.137, 107.89, 402.863, 372.325))),
                ("faucet MDL", _fit_with_bbox(VLM_FAUCET_ORIGINAL, (330, 185), (215.154, 118.861, 407.249, 356.885))),
                ("faucet noMDL", _fit_with_bbox(VLM_FAUCET_CONVERTED, (330, 185), (215.154, 118.861, 407.249, 356.885))),
            ],
            band_h=230,
        )
        _draw_failure_taxonomy_matrix_band(
            canvas,
            draw,
            y=strip_y + 18,
            h=height - (strip_y + 18) - 54,
            accent=accent,
        )
    elif extra_stress_strip:
        def pair_tile(
            original: Path,
            converted: Path,
            bbox: tuple[float, float, float, float],
            *,
            size: tuple[int, int] = (280, 560),
        ) -> Image.Image:
            tile = Image.new("RGB", size, (248, 248, 248))
            gap = 8
            half_h = (size[1] - gap) // 2
            original_tile = _fit_with_bbox(original, (size[0], half_h), bbox)
            converted_tile = _fit_with_bbox(converted, (size[0], half_h), bbox)
            tile.paste(original_tile, (0, 0))
            tile.paste(converted_tile, (0, half_h + gap))
            return tile

        strip_y = body_y + card_h * 2 + card_gap + 18
        _draw_opener_band(
            canvas,
            draw,
            y=strip_y,
            title="source zoom-level audit strip: target-visible stress pairs",
            tiles=[
                ("backpack", pair_tile(VLM_BACKPACK_ORIGINAL, VLM_BACKPACK_CONVERTED, (207.811, 105.285, 376.441, 364.938))),
                ("clock", pair_tile(VLM_CLOCK_ORIGINAL, VLM_CLOCK_CONVERTED, (211.647, 107.436, 370.171, 360.234))),
                ("bottle", pair_tile(VLM_BOTTLE_ORIGINAL, VLM_BOTTLE_CONVERTED, (230.385, 89.121, 369.378, 372.696))),
                ("cup", pair_tile(VLM_CUP_ORIGINAL, VLM_CUP_CONVERTED, (183.338, 133.12, 416.662, 331.46))),
                ("picture", pair_tile(VLM_PICTURE_ORIGINAL, VLM_PICTURE_CONVERTED, (240.087, 100.65, 374.808, 360.903))),
            ],
            band_h=620,
        )
    elif extra_pass_strip:
        strip_y = body_y + card_h * 2 + card_gap + 18
        def muted_tile(image: Image.Image) -> Image.Image:
            return ImageEnhance.Color(image).enhance(0.48)

        _draw_opener_band(
            canvas,
            draw,
            y=strip_y,
            title="source PASS-only pilot render audit strip",
            tiles=[
                ("bottle MDL", muted_tile(_fit_with_bbox(VLM_BOTTLE_ORIGINAL, (330, 210), (230.385, 89.121, 369.378, 372.696)))),
                ("bottle noMDL", muted_tile(_fit_with_bbox(VLM_BOTTLE_CONVERTED, (330, 210), (230.385, 89.121, 369.378, 372.696)))),
                ("cup view A", muted_tile(_fit_with_bbox(VLM_CUP_ORIGINAL, (330, 210), (183.338, 133.12, 416.662, 331.46)))),
                ("cup view B", muted_tile(_fit_with_bbox(VLM_CUP_ALT_ORIGINAL, (330, 210), (197.137, 107.89, 402.863, 372.325)))),
                ("faucet MDL", muted_tile(_fit_with_bbox(VLM_FAUCET_ORIGINAL, (330, 210), (215.154, 118.861, 407.249, 356.885)))),
                ("faucet noMDL", muted_tile(_fit_with_bbox(VLM_FAUCET_CONVERTED, (330, 210), (215.154, 118.861, 407.249, 356.885)))),
            ],
            band_h=500,
        )
    draw.text(
        (MARGIN, height - 26),
        "Reading note: render pairs are source visual anchors; the guide explains how the table is read and carries no experimental result.",
        fill=(82, 82, 82),
        font=small_font,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)
    print(output)


def build_grscenes_table_companions() -> None:
    pairs = {
        "bottle": ("bottle | PASS-only", "early target-visible preservation row", VLM_BOTTLE_ORIGINAL, VLM_BOTTLE_CONVERTED, (230.385, 89.121, 369.378, 372.696)),
        "cup": ("cup | PASS-only", "matched clean-rerender target view", VLM_CUP_ORIGINAL, VLM_CUP_CONVERTED, (183.338, 133.12, 416.662, 331.46)),
        "cup_alt": ("cup view B | PASS-only", "second pilot cup view", VLM_CUP_ALT_ORIGINAL, VLM_CUP_ALT_CONVERTED, (197.137, 107.89, 402.863, 372.325)),
        "faucet": ("faucet | PASS-only", "pilot faucet target view", VLM_FAUCET_ORIGINAL, VLM_FAUCET_CONVERTED, (215.154, 118.861, 407.249, 356.885)),
        "backpack": ("backpack | zoom stress", "material/color/lighting stress anchor", VLM_BACKPACK_ORIGINAL, VLM_BACKPACK_CONVERTED, (207.811, 105.285, 376.441, 364.938)),
        "clock": ("clock | zoom stress", "selected diagnostic counterexample row", VLM_CLOCK_ORIGINAL, VLM_CLOCK_CONVERTED, (211.647, 107.436, 370.171, 360.234)),
        "picture": ("picture | zoom stress", "null-answer diagnostic row", VLM_PICTURE_ORIGINAL, VLM_PICTURE_CONVERTED, (240.087, 100.65, 374.808, 360.903)),
    }
    _build_grscenes_table_companion(
        output=GRSCENES_FAILURE_TAXONOMY_COMPANION_OUT,
        title="GRScenes failure-taxonomy table companion",
        subtitle="Selected misses and counterexamples are made inspectable with source render pairs before the taxonomy text.",
        accent=(38, 95, 156),
        bullets=["taxonomy is selected", "status comes from tables", "rows are not frequencies"],
        pair_order=[pairs["backpack"], pairs["clock"], pairs["bottle"], pairs["cup"], pairs["picture"], pairs["faucet"]],
        gate_slot=GRSCENES_FAILURE_TAXONOMY_GATE_V4_AI_SLOT,
        gate_title="failure-taxonomy check",
        extra_failure_wall=True,
    )
    _build_grscenes_table_companion(
        output=GRSCENES_PASS_ONLY_COMPANION_OUT,
        title="GRScenes PASS-only table companion",
        subtitle="The early pilot is tied to target-visible render pairs before scaling to the clean-pool evaluation check.",
        accent=(0, 133, 100),
        bullets=["pilot provenance only", "paired target views", "pilot provenance"],
        pair_order=[pairs["bottle"], pairs["cup"], pairs["cup_alt"], pairs["faucet"]],
        gate_slot=GRSCENES_PASS_ONLY_GATE_V3_AI_SLOT,
        gate_title="PASS-only provenance check",
        extra_pass_strip=True,
    )
    _build_grscenes_table_companion(
        output=GRSCENES_ZOOM_STRESS_COMPANION_OUT,
        title="GRScenes zoom-stress table companion",
        subtitle="Zoom rows stress grounding under visible material/color/lighting shifts without turning into a preservation conclusion.",
        accent=(211, 116, 32),
        bullets=["visible target stress", "zoom level separated", "scoped row results"],
        pair_order=[pairs["backpack"], pairs["clock"], pairs["bottle"], pairs["cup"], pairs["cup_alt"], pairs["faucet"]],
        gate_slot=GRSCENES_ZOOM_STRESS_GATE_V3_AI_SLOT,
        gate_title="zoom-stress check",
        extra_stress_strip=True,
    )


def _draw_coordinate_contract_gate(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    slot_path: Path = VLM_COORDINATE_CONTRACT_GATE_AI_SLOT,
) -> None:
    title_font = _font(20, bold=True)
    body_font = _font(13)
    bullet_font = _font(14, bold=True)
    accent = (40, 96, 168)
    image_h = 230
    image = _fit(slot_path, (w - 34, image_h), cover=False)

    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(252, 252, 252), outline=(178, 178, 178), width=2)
    draw.text((x + 17, y + 14), "coordinate-contract check", fill=(20, 20, 20), font=title_font)
    draw.text((x + 17, y + 42), "orientation panel", fill=(82, 82, 82), font=body_font)
    canvas.paste(image, (x + 17, y + 66))
    draw.rectangle((x + 17, y + 66, x + 17 + w - 34, y + 66 + image_h), outline=(138, 138, 138), width=2)

    bullets = [
        "prompt asks norm-1000",
        "raw rescoring is diagnostic",
        "baselines check scoring",
    ]
    bullet_y = y + 322
    for idx, line in enumerate(bullets):
        dot_y = bullet_y + idx * 38 + 7
        draw.ellipse((x + 20, dot_y, x + 31, dot_y + 11), fill=accent)
        draw.text((x + 42, bullet_y + idx * 38), line, fill=(45, 45, 45), font=bullet_font)

    draw.rounded_rectangle((x + 17, y + h - 58, x + w - 17, y + h - 18), radius=7, fill=(246, 250, 255), outline=accent, width=2)
    draw.text((x + 34, y + h - 47), "scoring context", fill=accent, font=body_font)


def build_vlm_coordinate_table_companion() -> None:
    width = 1800
    height = 1240
    canvas = Image.new("RGB", (width, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(30, bold=True)
    note_font = _font(16)
    small_font = _font(12)
    accent = (40, 96, 168)

    y = 34
    draw.text((MARGIN, y), "VLM coordinate table companion", fill=(18, 18, 18), font=heading_font)
    y += 42
    draw.text(
        (MARGIN, y),
        "source render pairs expose why raw-image center, target-box center, and normalized-1000 scoring must stay separated.",
        fill=(68, 68, 68),
        font=note_font,
    )

    body_y = 122
    card_gap = 16
    left_w = 1190
    right_w = width - MARGIN * 2 - left_w - card_gap
    card_w = (left_w - card_gap) // 2
    card_h = 270
    pairs = [
        ("backpack | clean/zoom", "raw center and norm center both visible", VLM_BACKPACK_ORIGINAL, VLM_BACKPACK_CONVERTED, (207.811, 105.285, 376.441, 364.938)),
        ("clock | zoom stress", "counterexample rows need coordinate split", VLM_CLOCK_ORIGINAL, VLM_CLOCK_CONVERTED, (211.647, 107.436, 370.171, 360.234)),
        ("bottle | PASS-only", "target box differs from raw image frame", VLM_BOTTLE_ORIGINAL, VLM_BOTTLE_CONVERTED, (230.385, 89.121, 369.378, 372.696)),
        ("cup | clean rerender", "bbox center is an oracle sanity check", VLM_CUP_ORIGINAL, VLM_CUP_CONVERTED, (183.338, 133.12, 416.662, 331.46)),
    ]
    for idx, (title, note, original, converted, bbox) in enumerate(pairs):
        row = idx // 2
        col = idx % 2
        _draw_table_companion_pair(
            canvas,
            draw,
            x=MARGIN + col * (card_w + card_gap),
            y=body_y + row * (card_h + card_gap),
            w=card_w,
            h=card_h,
            title=title,
            note=note,
            original=original,
            converted=converted,
            bbox=bbox,
            accent=accent,
        )

    _draw_coordinate_contract_gate(
        canvas,
        draw,
        x=MARGIN + left_w + card_gap,
        y=body_y,
        w=right_w,
        h=card_h * 2 + card_gap,
        slot_path=VLM_COORDINATE_CONTRACT_GATE_V3_AI_SLOT,
    )

    strip_y = body_y + card_h * 2 + card_gap + 18
    _draw_opener_band(
        canvas,
        draw,
        y=strip_y,
        title="source coordinate-frame render audit strip",
        tiles=[
            ("backpack MDL", _fit_with_bbox(VLM_BACKPACK_ORIGINAL, (310, 220), (207.811, 105.285, 376.441, 364.938))),
            ("clock noMDL", _fit_with_bbox(VLM_CLOCK_CONVERTED, (310, 220), (211.647, 107.436, 370.171, 360.234))),
            ("bottle noMDL", _fit_with_bbox(VLM_BOTTLE_CONVERTED, (310, 220), (230.385, 89.121, 369.378, 372.696))),
            ("cup view A", _fit_with_bbox(VLM_CUP_ORIGINAL, (310, 220), (183.338, 133.12, 416.662, 331.46))),
            ("cup noMDL", _fit_with_bbox(VLM_CUP_CONVERTED, (310, 220), (183.338, 133.12, 416.662, 331.46))),
            ("faucet noMDL", _fit_with_bbox(VLM_FAUCET_CONVERTED, (310, 220), (215.154, 118.861, 407.249, 356.885))),
        ],
        band_h=500,
    )
    draw.text(
        (MARGIN, height - 26),
        "Reading note: render pairs visualize the coordinate contract; tables remain the metric record.",
        fill=(82, 82, 82),
        font=small_font,
    )

    VLM_COORDINATE_TABLE_COMPANION_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(VLM_COORDINATE_TABLE_COMPANION_OUT)
    print(VLM_COORDINATE_TABLE_COMPANION_OUT)


def _draw_coordinate_baseline_card(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    subtitle: str,
    path: Path,
    bbox: tuple[float, float, float, float],
    baseline: str,
    boundary: str,
    accent: tuple[int, int, int],
) -> None:
    title_font = _font(20, bold=True)
    body_font = _font(13)
    small_font = _font(12, bold=True)
    image_h = 290
    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(252, 252, 252), outline=(174, 174, 174), width=2)
    draw.rectangle((x, y, x + w, y + 8), fill=accent)
    draw.text((x + 16, y + 20), title, fill=(20, 20, 20), font=title_font)
    draw.multiline_text((x + 16, y + 50), subtitle, fill=(68, 68, 68), font=body_font, spacing=3)

    image = _fit_with_protocol_overlay(path, (w - 32, image_h), bbox)
    image_y = y + 105
    canvas.paste(image, (x + 16, image_y))
    draw.rectangle((x + 16, image_y, x + w - 16, image_y + image_h), outline=(140, 140, 140), width=2)

    draw.rounded_rectangle((x + 16, y + h - 98, x + w - 16, y + h - 18), radius=6, fill=(248, 250, 252), outline=accent, width=2)
    draw.text((x + 28, y + h - 89), "baseline check", fill=accent, font=small_font)
    draw.multiline_text((x + 28, y + h - 66), baseline, fill=(45, 45, 45), font=body_font, spacing=1)
    draw.text((x + 28, y + h - 29), boundary, fill=(82, 82, 82), font=_font(10))


def _draw_coordinate_baseline_gate(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    slot_path: Path = VLM_COORDINATE_BASELINE_GATE_AI_SLOT,
) -> None:
    title_font = _font(20, bold=True)
    body_font = _font(13)
    bullet_font = _font(13, bold=True)
    accent = (40, 96, 168)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(252, 252, 252), outline=(174, 174, 174), width=2)
    draw.text((x + 18, y + 18), "baseline-check panel", fill=(20, 20, 20), font=title_font)
    draw.text((x + 18, y + 48), "orientation panel", fill=(76, 76, 76), font=body_font)
    image_h = 275
    image = _fit(slot_path, (w - 36, image_h), cover=False)
    canvas.paste(image, (x + 18, y + 78))
    draw.rectangle((x + 18, y + 78, x + w - 18, y + 78 + image_h), outline=(140, 140, 140), width=2)

    bullets = [
        "deterministic sanity rows",
        "oracle centers test scoring",
        "model predictions stay in tables",
    ]
    bullet_y = y + 378
    for idx, line in enumerate(bullets):
        yy = bullet_y + idx * 31
        draw.ellipse((x + 22, yy + 5, x + 34, yy + 17), fill=accent)
        draw.text((x + 48, yy), line, fill=(45, 45, 45), font=bullet_font)

    draw.rounded_rectangle((x + 18, y + h - 58, x + w - 18, y + h - 18), radius=6, fill=(246, 250, 255), outline=accent, width=2)
    draw.text((x + 34, y + h - 47), "scoring context", fill=accent, font=body_font)


def _coordinate_baseline_pair_tile(
    original: Path,
    converted: Path,
    bbox: tuple[float, float, float, float],
    *,
    size: tuple[int, int] = (520, 280),
) -> Image.Image:
    tile = Image.new("RGB", size, (248, 248, 248))
    draw = ImageDraw.Draw(tile)
    label_font = _font(13, bold=True)
    gap = 8
    label_h = 28
    image_w = (size[0] - gap) // 2
    image_h = size[1] - label_h
    for idx, (label, path) in enumerate((("original", original), ("noMDL", converted))):
        x = idx * (image_w + gap)
        draw.rectangle((x, 0, x + image_w, label_h), fill=(238, 242, 247), outline=(154, 154, 154), width=1)
        draw.text((x + 8, 7), label, fill=(32, 32, 32), font=label_font)
        image = _fit_with_protocol_overlay(path, (image_w, image_h), bbox)
        tile.paste(image, (x, label_h))
        draw.rectangle((x, label_h, x + image_w, label_h + image_h), outline=(132, 132, 132), width=2)
    return tile


def build_vlm_coordinate_baseline_sanity_companion() -> None:
    width = 1800
    height = 1040
    canvas = Image.new("RGB", (width, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(32, bold=True)
    note_font = _font(16)
    footer_font = _font(12)

    y = 34
    draw.text((MARGIN, y), "Coordinate-baseline sanity companion", fill=(18, 18, 18), font=heading_font)
    y += 44
    draw.text(
        (MARGIN, y),
        "Real target-view renders make Table S3's deterministic rows inspectable without treating them as model predictions.",
        fill=(66, 66, 66),
        font=note_font,
    )

    body_y = 122
    card_gap = 16
    right_w = 430
    left_w = width - 2 * MARGIN - right_w - card_gap
    card_w = (left_w - 2 * card_gap) // 3
    card_h = 535
    cards = [
        (
            "image-center pixel",
            "raw center can be easy\nunder target-centered cameras",
            VLM_BACKPACK_ORIGINAL,
            (207.811, 105.285, 376.441, 364.938),
            "30/30 can mean the view\nis camera-biased",
            "diagnostic only",
            (40, 96, 168),
        ),
        (
            "bbox-center pixel",
            "oracle target center checks\nbox geometry and scoring",
            VLM_CLOCK_ORIGINAL,
            (211.647, 107.436, 370.171, 360.234),
            "30/30 proves the scorer\ncan hit the box",
            "scorer sanity row",
            (0, 133, 100),
        ),
        (
            "bbox-center norm-1000",
            "normalized center checks\nthe prompt coordinate contract",
            VLM_CUP_ORIGINAL,
            (183.338, 133.12, 416.662, 331.46),
            "30/30 validates the\nnormalization frame",
            "scorer sanity row",
            (211, 116, 32),
        ),
    ]
    for idx, (title, subtitle, path, bbox, baseline, boundary, accent) in enumerate(cards):
        _draw_coordinate_baseline_card(
            canvas,
            draw,
            x=MARGIN + idx * (card_w + card_gap),
            y=body_y,
            w=card_w,
            h=card_h,
            title=title,
            subtitle=subtitle,
            path=path,
            bbox=bbox,
            baseline=baseline,
            boundary=boundary,
            accent=accent,
        )

    _draw_coordinate_baseline_gate(
        canvas,
        draw,
        x=MARGIN + left_w + card_gap,
        y=body_y,
        w=right_w,
        h=card_h,
        slot_path=VLM_COORDINATE_BASELINE_GATE_V2_AI_SLOT,
    )

    strip_y = body_y + card_h + 20
    _draw_opener_band(
        canvas,
        draw,
        y=strip_y,
        title="source baseline audit strip: original/noMDL target-view pairs",
        tiles=[
            ("backpack image-center", _coordinate_baseline_pair_tile(VLM_BACKPACK_ORIGINAL, VLM_BACKPACK_CONVERTED, (207.811, 105.285, 376.441, 364.938))),
            ("clock bbox-center", _coordinate_baseline_pair_tile(VLM_CLOCK_ORIGINAL, VLM_CLOCK_CONVERTED, (211.647, 107.436, 370.171, 360.234))),
            ("bottle norm-frame", _coordinate_baseline_pair_tile(VLM_BOTTLE_ORIGINAL, VLM_BOTTLE_CONVERTED, (230.385, 89.121, 369.378, 372.696))),
            ("cup scorer check", _coordinate_baseline_pair_tile(VLM_CUP_ORIGINAL, VLM_CUP_CONVERTED, (183.338, 133.12, 416.662, 331.46))),
        ],
        band_h=315,
    )
    draw.text(
        (MARGIN, height - 28),
        "Reading note: the strip visualizes deterministic sanity baselines; it is scorer sanity context.",
        fill=(82, 82, 82),
        font=footer_font,
    )

    VLM_COORDINATE_BASELINE_SANITY_COMPANION_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(VLM_COORDINATE_BASELINE_SANITY_COMPANION_OUT)
    print(VLM_COORDINATE_BASELINE_SANITY_COMPANION_OUT)


def _draw_coordinate_case_row(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
    target: str,
    note: str,
    original: Path,
    converted: Path,
    bbox: tuple[float, float, float, float],
    metric_note: str,
) -> int:
    row_h = 395
    label_w = 320
    card_w = 260
    inner_gap = 18
    image_x = MARGIN + label_w + inner_gap
    card_x = WIDTH - MARGIN - card_w
    image_w = (card_x - image_x - inner_gap * 2) // 2
    image_h = 285
    image_y = y + 82
    title_font = _font(24, bold=True)
    note_font = _font(16)
    card_font = _font(18, bold=True)

    draw.rounded_rectangle((MARGIN, y, WIDTH - MARGIN, y + row_h), radius=8, fill=(252, 252, 252), outline=(178, 178, 178), width=2)
    draw.text((MARGIN + 20, y + 24), target, fill=(18, 18, 18), font=title_font)
    draw.text((MARGIN + 20, y + 60), note, fill=(70, 70, 70), font=note_font)
    draw.text((MARGIN + 20, y + row_h - 38), "matched render pair", fill=(96, 96, 96), font=note_font)

    for idx, (title, path) in enumerate((("Original MDL", original), ("Converted noMDL", converted))):
        x = image_x + idx * (image_w + inner_gap)
        draw.text((x, y + 24), title, fill=(32, 32, 32), font=note_font)
        image = _fit_with_protocol_overlay(path, (image_w, image_h), bbox)
        canvas.paste(image, (x, image_y))
        draw.rectangle((x, image_y, x + image_w, image_y + image_h), outline=(135, 135, 135), width=2)

    draw.rounded_rectangle((card_x, y + 72, card_x + card_w, y + 252), radius=8, fill=(246, 250, 255), outline=(40, 96, 168), width=2)
    draw.text((card_x + 20, y + 94), "scoring view", fill=(40, 96, 168), font=card_font)
    draw.text((card_x + 20, y + 130), metric_note, fill=(54, 54, 54), font=note_font)
    draw.text((card_x + 20, y + 216), "Tables S2-S3", fill=(211, 116, 32), font=card_font)
    return y + row_h


def build_vlm_coordinate_protocol_atlas() -> None:
    width = 1800
    height = 1840
    canvas = Image.new("RGB", (width, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(34, bold=True)
    note_font = _font(18)
    legend_font = _font(17, bold=True)

    y = MARGIN
    draw.text((MARGIN, y), "VLM coordinate protocol render atlas", fill=(18, 18, 18), font=heading_font)
    y += 48
    draw.text(
        (MARGIN, y),
        "Real GRScenes target-view renders showing why raw-image center and normalized-1000 target-box scoring must be separated.",
        fill=(66, 66, 66),
        font=note_font,
    )
    y += 48

    legend_h = 112
    draw.rounded_rectangle((MARGIN, y, WIDTH - MARGIN, y + legend_h), radius=8, fill=(252, 252, 252), outline=(178, 178, 178), width=2)
    legend_items = [
        ((0, 150, 112), "target box"),
        ((40, 96, 168), "raw image center"),
        ((211, 116, 32), "normalized-1000 bbox center"),
    ]
    legend_x = MARGIN + 30
    for color, label in legend_items:
        draw.rounded_rectangle((legend_x, y + 34, legend_x + 38, y + 72), radius=4, fill=color)
        draw.text((legend_x + 52, y + 38), label, fill=(35, 35, 35), font=legend_font)
        legend_x += 390
    draw.text(
        (MARGIN + 1190, y + 32),
        "same image, different coordinate contracts",
        fill=(70, 70, 70),
        font=note_font,
    )
    y += legend_h + GAP

    y = _draw_coordinate_case_row(
        canvas,
        draw,
        y=y,
        target="backpack | zoom_018",
        note="camera-biased raw center",
        original=VLM_BACKPACK_ORIGINAL,
        converted=VLM_BACKPACK_CONVERTED,
        bbox=(207.811, 105.285, 376.441, 364.938),
        metric_note="raw center can score\nwithout following the\nnormalized prompt",
    ) + GAP
    y = _draw_coordinate_case_row(
        canvas,
        draw,
        y=y,
        target="clock | zoom_018",
        note="thin target, oracle bbox center",
        original=VLM_CLOCK_ORIGINAL,
        converted=VLM_CLOCK_CONVERTED,
        bbox=(211.647, 107.436, 370.171, 360.234),
        metric_note="bbox center maps to\nnormalized-1000\ncontract scoring",
    ) + GAP
    y = _draw_coordinate_case_row(
        canvas,
        draw,
        y=y,
        target="bottle | zoom_018",
        note="material shift with point contract",
        original=VLM_BOTTLE_ORIGINAL,
        converted=VLM_BOTTLE_CONVERTED,
        bbox=(230.385, 89.121, 369.378, 372.696),
        metric_note="answer, parseability,\nand point hits are\nreported separately",
    )

    y += GAP
    _draw_opener_band(
        canvas,
        draw,
        y=y,
        title="source protocol audit strip: route panel plus target-view crops",
        tiles=[
            ("route slot", _fit(VLM_PROTOCOL_ROUTE_V2_AI_SLOT, (260, 200), cover=False)),
            ("backpack noMDL", _fit_with_protocol_overlay(VLM_BACKPACK_CONVERTED, (260, 200), (207.811, 105.285, 376.441, 364.938))),
            ("clock noMDL", _fit_with_protocol_overlay(VLM_CLOCK_CONVERTED, (260, 200), (211.647, 107.436, 370.171, 360.234))),
            ("bottle noMDL", _fit_with_protocol_overlay(VLM_BOTTLE_CONVERTED, (260, 200), (230.385, 89.121, 369.378, 372.696))),
            ("cup original", _fit_with_protocol_overlay(VLM_CUP_ORIGINAL, (260, 200), (183.338, 133.12, 416.662, 331.46))),
            ("cup noMDL", _fit_with_protocol_overlay(VLM_CUP_CONVERTED, (260, 200), (183.338, 133.12, 416.662, 331.46))),
        ],
        band_h=260,
    )

    VLM_COORDINATE_PROTOCOL_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(VLM_COORDINATE_PROTOCOL_OUT)
    print(VLM_COORDINATE_PROTOCOL_OUT)


def build_material_intro_strip() -> None:
    width = 1200
    height = 470
    margin = 28
    gap = 18
    title_h = 42
    panel_w = (width - 2 * margin - 2 * gap) // 3
    panel_h = 280
    canvas = Image.new("RGB", (width, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, margin), "Material evidence preview", fill=(18, 18, 18), font=_font(27, bold=True))
    y = margin + title_h
    _draw_strip_panel(
        canvas,
        draw,
        x=margin,
        y=y,
        w=panel_w,
        h=panel_h,
        title="covered bins",
        path=MATERIAL_BASELINE,
        crop=(12, 54, 1112, 174),
    )
    _draw_strip_panel(
        canvas,
        draw,
        x=margin + panel_w + gap,
        y=y,
        w=panel_w,
        h=panel_h,
        title="clearcoat case",
        path=MATERIAL_SUPPLEMENTAL,
        crop=(24, 62, 284, 258),
    )
    _draw_strip_panel(
        canvas,
        draw,
        x=margin + 2 * (panel_w + gap),
        y=y,
        w=panel_w,
        h=panel_h,
        title="procedural limit",
        path=MATERIAL_SUPPLEMENTAL,
        crop=(24, 340, 284, 535),
    )
    MATERIAL_STRIP_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(MATERIAL_STRIP_OUT)
    print(MATERIAL_STRIP_OUT)


def build_material_intro_column() -> None:
    width = 1600
    height = 1700
    margin = 34
    gap = 18
    panel_w = (width - 2 * margin - gap) // 2
    full_w = width - 2 * margin
    canvas = Image.new("RGB", (width, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, margin), "Material evidence preview", fill=(18, 18, 18), font=_font(34, bold=True))
    draw.text(
        (margin, margin + 42),
        "source renders for covered material bins, selected clearcoat risk, and procedural-texture limitation",
        fill=(68, 68, 68),
        font=_font(18),
    )
    y = margin + 88
    row_y = y
    _draw_column_panel(
        canvas,
        draw,
        x=margin,
        y=row_y,
        w=panel_w,
        h=210,
        title="covered bin: opacity / emission / normals",
        path=MATERIAL_BASELINE,
        crop=(12, 54, 1112, 174),
        contain=False,
    )
    _draw_column_panel(
        canvas,
        draw,
        x=margin + panel_w + gap,
        y=row_y,
        w=panel_w,
        h=210,
        title="covered bin: scene object surfaces",
        path=MATERIAL_BASELINE,
        crop=(12, 216, 1112, 337),
        contain=False,
    )
    row_y += 244 + gap
    _draw_column_panel(
        canvas,
        draw,
        x=margin,
        y=row_y,
        w=panel_w,
        h=210,
        title="covered bin: cup target",
        path=MATERIAL_BASELINE,
        crop=(12, 378, 1112, 500),
        contain=False,
    )
    _draw_column_panel(
        canvas,
        draw,
        x=margin + panel_w + gap,
        y=row_y,
        w=panel_w,
        h=210,
        title="covered bin: backpack target",
        path=MATERIAL_BASELINE,
        crop=(12, 540, 1112, 660),
        contain=False,
    )
    row_y += 244 + gap
    _draw_column_panel(
        canvas,
        draw,
        x=margin,
        y=row_y,
        w=panel_w,
        h=310,
        title="selected clearcoat diagnostic",
        path=MATERIAL_SUPPLEMENTAL,
        crop=(24, 62, 832, 258),
        contain=False,
    )
    _draw_column_panel(
        canvas,
        draw,
        x=margin + panel_w + gap,
        y=row_y,
        w=panel_w,
        h=310,
        title="procedural texture limitation",
        path=MATERIAL_SUPPLEMENTAL,
        crop=(24, 340, 832, 535),
        contain=False,
    )
    y = row_y + 344 + gap
    y = _draw_column_panel(
        canvas,
        draw,
        x=margin,
        y=y,
        w=full_w,
        h=355,
        title="source material comparison wall",
        path=MATERIAL_BASELINE,
        crop=(12, 54, 1112, 660),
        contain=False,
    ) + gap
    footer_h = height - y - margin
    draw.rounded_rectangle((margin, y, width - margin, y + footer_h), radius=8, fill=(252, 252, 252), outline=(174, 174, 174), width=2)
    draw.text((margin + 18, y + 18), "reading scope", fill=(18, 18, 18), font=_font(24, bold=True))
    footer_font = _font(17)
    rows = [
        ("covered bins", "scoped qualitative support only"),
        ("clearcoat", "selected NVIDIA failure diagnostic"),
        ("procedural texture", "limitation case unless preserved or baked"),
    ]
    row_h = 54
    for idx, (label, note) in enumerate(rows):
        yy = y + 60 + idx * (row_h + 12)
        fill = (246, 250, 255) if idx % 2 == 0 else (250, 250, 250)
        draw.rounded_rectangle((margin + 18, yy, width - margin - 18, yy + row_h), radius=6, fill=fill, outline=(186, 186, 186), width=1)
        draw.text((margin + 36, yy + 14), label, fill=(38, 95, 156), font=_font(17, bold=True))
        draw.text((margin + 360, yy + 14), note, fill=(54, 54, 54), font=footer_font)
    MATERIAL_COLUMN_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(MATERIAL_COLUMN_OUT)
    print(MATERIAL_COLUMN_OUT)


def build_navigation_intro_strip() -> None:
    width = 1200
    height = 560
    margin = 28
    gap = 18
    title_h = 42
    panel_w = (width - 2 * margin - 2 * gap) // 3
    panel_h = 360
    canvas = Image.new("RGB", (width, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, margin), "Navigation media preview", fill=(18, 18, 18), font=_font(27, bold=True))
    y = margin + title_h
    _draw_strip_panel(
        canvas,
        draw,
        x=margin,
        y=y,
        w=panel_w,
        h=panel_h,
        title="paired metrics",
        path=NAV_DOWNSTREAM,
        crop=(1995, 170, 2585, 720),
    )
    _draw_strip_panel(
        canvas,
        draw,
        x=margin + panel_w + gap,
        y=y,
        w=panel_w,
        h=panel_h,
        title="selected stills",
        path=NAV_STILLS,
        crop=(0, 140, 1106, 770),
    )
    _draw_strip_panel(
        canvas,
        draw,
        x=margin + 2 * (panel_w + gap),
        y=y,
        w=panel_w,
        h=panel_h,
        title="route context",
        path=NAV_0036_MAIN,
        crop=(395, 122, 1735, 790),
    )
    NAVIGATION_STRIP_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(NAVIGATION_STRIP_OUT)
    print(NAVIGATION_STRIP_OUT)


def build_navigation_intro_column() -> None:
    width = 1700
    height = 1540
    margin = 34
    gap = 18
    canvas = Image.new("RGB", (width, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    title_font = _font(34, bold=True)
    subtitle_font = _font(17)
    label_font = _font(18, bold=True)
    small_font = _font(12)
    note_font = _font(14)

    draw.text((margin, margin), "Navigation evidence opener", fill=(18, 18, 18), font=title_font)
    draw.text(
        (margin, margin + 46),
        "source metrics, route stills, case panels, and review-scope media before the detailed navigation pages.",
        fill=(68, 68, 68),
        font=subtitle_font,
    )

    def card(x: int, y: int, w: int, h: int, title: str, image: Image.Image, accent: tuple[int, int, int]) -> None:
        draw.rounded_rectangle((x, y, x + w, y + h), radius=7, fill=(252, 252, 252), outline=(170, 170, 170), width=2)
        draw.rectangle((x, y, x + w, y + 6), fill=accent)
        draw.text((x + 12, y + 13), title, fill=(22, 22, 22), font=label_font)
        image_y = y + 42
        canvas.paste(image, (x + 10, image_y))
        draw.rectangle((x + 10, image_y, x + w - 10, y + h - 10), outline=(140, 140, 140), width=2)

    top_y = margin + 88
    left_w = 520
    mid_w = 500
    right_w = width - 2 * margin - left_w - mid_w - 2 * gap
    top_h = 360
    card(
        margin,
        top_y,
        left_w,
        top_h,
        "official paired-run metrics",
        _crop_fit(NAV_DOWNSTREAM, (790, 105, 1690, 665), (left_w - 20, top_h - 52)),
        (42, 103, 158),
    )
    card(
        margin + left_w + gap,
        top_y,
        mid_w,
        top_h,
        "selected rollout stills",
        _crop_fit(NAV_STILLS, (0, 0, 1106, 930), (mid_w - 20, top_h - 52)),
        (39, 126, 112),
    )

    gate_x = margin + left_w + mid_w + 2 * gap
    draw.rounded_rectangle((gate_x, top_y, gate_x + right_w, top_y + top_h), radius=7, fill=(252, 252, 252), outline=(170, 170, 170), width=2)
    draw.rectangle((gate_x, top_y, gate_x + right_w, top_y + 6), fill=(70, 99, 154))
    draw.text((gate_x + 12, top_y + 13), "navigation-review guide", fill=(22, 22, 22), font=label_font)
    draw.text((gate_x + 12, top_y + 38), "orientation panel", fill=(78, 78, 78), font=small_font)
    slot = _fit(NAV_REVIEW_GATE_AI_SLOT, (right_w - 24, 205), cover=False)
    canvas.paste(slot, (gate_x + 12, top_y + 62))
    draw.rectangle((gate_x + 12, top_y + 62, gate_x + right_w - 12, top_y + 267), outline=(140, 140, 140), width=2)
    for idx, line in enumerate(["selected qualitative media", "review-packet scope", "selected media context"]):
        yy = top_y + 285 + idx * 24
        draw.rectangle((gate_x + 16, yy + 4, gate_x + 26, yy + 14), fill=(39, 126, 112))
        draw.text((gate_x + 34, yy), line, fill=(48, 48, 48), font=note_font)

    route_y = top_y + top_h + gap
    route_h = 300
    route_w = 1040
    card(
        margin,
        route_y,
        route_w,
        route_h,
        "0036/0066 route context",
        _crop_fit(NAV_0036_MAIN, (395, 122, 1735, 790), (route_w - 20, route_h - 52)),
        (43, 119, 137),
    )
    cases_x = margin + route_w + gap
    cases_w = width - margin - cases_x
    draw.rounded_rectangle((cases_x, route_y, cases_x + cases_w, route_y + route_h), radius=7, fill=(252, 252, 252), outline=(170, 170, 170), width=2)
    draw.rectangle((cases_x, route_y, cases_x + cases_w, route_y + 6), fill=(83, 118, 75))
    draw.text((cases_x + 12, route_y + 13), "selected case panels", fill=(22, 22, 22), font=label_font)
    case_paths = [NAV_SELECTED_CASE, NAV_SELECTED_CASE2, NAV_SELECTED_CASE3, NAV_SELECTED_CASE4]
    case_w = (cases_w - 30) // 2
    case_h = 120
    for idx, path in enumerate(case_paths):
        x = cases_x + 10 + (idx % 2) * (case_w + 10)
        y = route_y + 42 + (idx // 2) * (case_h + 10)
        canvas.paste(_crop_fit(path, (0, 34, 1106, 390), (case_w, case_h)), (x, y))
        draw.rectangle((x, y, x + case_w, y + case_h), outline=(140, 140, 140), width=2)

    bottom_y = route_y + route_h + gap
    bottom_h = 390
    bottom_w = (width - 2 * margin - 2 * gap) // 3
    card(
        margin,
        bottom_y,
        bottom_w,
        bottom_h,
        "navigation media atlas",
        _fit(NAVIGATION_OUT, (bottom_w - 20, bottom_h - 52), cover=True),
        (42, 103, 158),
    )
    card(
        margin + bottom_w + gap,
        bottom_y,
        bottom_w,
        bottom_h,
        "media scope strip",
        _fit(NAVIGATION_MEDIA_BOUNDARY_OUT, (bottom_w - 20, bottom_h - 52), cover=False),
        (39, 126, 112),
    )
    draw.rounded_rectangle((margin + 2 * (bottom_w + gap), bottom_y, margin + 3 * bottom_w + 2 * gap, bottom_y + bottom_h), radius=7, fill=(252, 252, 252), outline=(170, 170, 170), width=2)
    draw.rectangle((margin + 2 * (bottom_w + gap), bottom_y, margin + 3 * bottom_w + 2 * gap, bottom_y + 6), fill=(83, 91, 142))
    spread_x = margin + 2 * (bottom_w + gap)
    draw.text((spread_x + 12, bottom_y + 13), "0036 case spread", fill=(22, 22, 22), font=label_font)
    spread_paths = [NAV_0036_CASE, NAV_0036_CASE2, NAV_0036_CASE3, NAV_0036_CASE4]
    spread_w = (bottom_w - 30) // 2
    spread_h = 160
    for idx, path in enumerate(spread_paths):
        x = spread_x + 10 + (idx % 2) * (spread_w + 10)
        y = bottom_y + 42 + (idx // 2) * (spread_h + 10)
        canvas.paste(_crop_fit(path, (0, 34, 770, 430), (spread_w, spread_h)), (x, y))
        draw.rectangle((x, y, x + spread_w, y + spread_h), outline=(140, 140, 140), width=2)

    neutral_y = bottom_y + bottom_h + gap
    neutral_h = 220
    draw.rounded_rectangle((margin, neutral_y, width - margin, neutral_y + neutral_h), radius=7, fill=(252, 252, 252), outline=(170, 170, 170), width=2)
    draw.rectangle((margin, neutral_y, width - margin, neutral_y + 6), fill=(96, 100, 105))
    draw.text((margin + 12, neutral_y + 13), "neutral case closure row", fill=(22, 22, 22), font=label_font)
    draw.text((margin + 300, neutral_y + 17), "remaining selected examples add balance before full case pages", fill=(78, 78, 78), font=small_font)
    neutral_tiles = [
        (NAV_SELECTED_CASE5, (0, 34, 1106, 430)),
        (NAV_SELECTED_CASE6, (0, 34, 1106, 430)),
        (NAV_0036_CASE5, (0, 34, 770, 430)),
        (NAV_0036_CASE6, (0, 34, 770, 430)),
    ]
    tile_gap = 10
    tile_w = (width - 2 * margin - 20 - 3 * tile_gap) // 4
    tile_h = neutral_h - 60
    for idx, (path, crop) in enumerate(neutral_tiles):
        x = margin + 10 + idx * (tile_w + tile_gap)
        y = neutral_y + 42
        canvas.paste(_crop_fit(path, crop, (tile_w, tile_h)), (x, y))
        draw.rectangle((x, y, x + tile_w, y + tile_h), outline=(140, 140, 140), width=2)

    footer_y = height - 76
    draw.rounded_rectangle((margin, footer_y, width - margin, height - margin), radius=7, fill=(252, 252, 252), outline=(170, 170, 170), width=2)
    draw.text((margin + 16, footer_y + 15), "Result scope", fill=(18, 18, 18), font=_font(18, bold=True))
    draw.text(
        (margin + 180, footer_y + 17),
        "source stills and route overlays are visual orientation evidence; the guide explains review scope only.",
        fill=(58, 58, 58),
        font=note_font,
    )
    draw.text((margin + 16, footer_y + 43), "Selected stills and route overlays support review; metrics remain in the official runs.", fill=(78, 78, 78), font=small_font)

    NAVIGATION_COLUMN_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(NAVIGATION_COLUMN_OUT)
    print(NAVIGATION_COLUMN_OUT)


def _draw_theory_evidence_lens_strip(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
) -> int:
    title_font = _font(19, bold=True)
    note_font = _font(14)
    label_font = _font(11, bold=True)
    pad = 14
    gap = 12
    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(252, 252, 252), outline=(176, 176, 176), width=2)
    draw.text((x + pad, y + 12), "theory-evidence lens strip", fill=(22, 22, 22), font=title_font)
    draw.text(
        (x + 310, y + 15),
        "orientation panel; real render crops carry the visual evidence.",
        fill=(72, 72, 72),
        font=note_font,
    )

    content_y = y + 44
    content_h = h - 58
    slot_w = 560
    slot = _fit(THEORY_EVIDENCE_LENS_AI_SLOT, (slot_w, content_h), cover=False)
    canvas.paste(slot, (x + pad, content_y))
    draw.rectangle((x + pad, content_y, x + pad + slot_w, content_y + content_h), outline=(138, 138, 138), width=2)

    tiles = [
        ("material cue", _crop_fit(MATERIAL_BASELINE, (12, 55, 372, 174), (260, 150))),
        ("target contract", _fit_with_bbox(VLM_CLOCK_ORIGINAL, (260, 150), (211.647, 107.436, 370.171, 360.234))),
        ("route context", _crop_fit(NAV_0036_MAIN, (390, 108, 1738, 790), (260, 150))),
        ("failure anchor", _fit_with_protocol_overlay(VLM_FAUCET_CONVERTED, (260, 150), (215.154, 118.861, 407.249, 356.885))),
    ]
    tile_w = (w - 2 * pad - slot_w - 4 * gap) // 4
    for idx, (label, tile) in enumerate(tiles):
        tile_x = x + pad + slot_w + gap + idx * (tile_w + gap)
        image = ImageOps.fit(tile, (tile_w, content_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        canvas.paste(image, (tile_x, content_y))
        draw.rectangle((tile_x, content_y, tile_x + tile_w, content_y + content_h), outline=(138, 138, 138), width=2)
        draw.rectangle((tile_x, content_y, tile_x + tile_w, content_y + 22), fill=(248, 248, 248), outline=(138, 138, 138), width=1)
        draw.text((tile_x + 6, content_y + 5), label, fill=(30, 30, 30), font=label_font)

    return y + h


def _compose_theory_failure_wall(size: tuple[int, int]) -> Image.Image:
    wall = Image.new("RGB", size, (248, 248, 248))
    draw = ImageDraw.Draw(wall)
    label_font = _font(13, bold=True)
    pair_label_font = _font(11, bold=True)
    cases = [
        ("cup view B", VLM_CUP_ALT_ORIGINAL, VLM_CUP_ALT_CONVERTED, (197.137, 107.89, 402.863, 372.325)),
        ("faucet", VLM_FAUCET_ORIGINAL, VLM_FAUCET_CONVERTED, (215.154, 118.861, 407.249, 356.885)),
        ("picture", VLM_PICTURE_ORIGINAL, VLM_PICTURE_CONVERTED, (240.087, 100.65, 374.808, 360.903)),
    ]
    gap = 12
    case_w = (size[0] - 2 * gap) // 3
    header_h = 24
    pair_gap = 8
    image_w = (case_w - pair_gap) // 2
    image_h = size[1] - header_h
    for idx, (label, original, converted, bbox) in enumerate(cases):
        x = idx * (case_w + gap)
        draw.rectangle((x, 0, x + case_w, header_h), fill=(244, 248, 250), outline=(135, 135, 135), width=1)
        draw.text((x + 8, 5), label, fill=(28, 28, 28), font=label_font)
        for pair_idx, (pair_label, path) in enumerate((("original", original), ("noMDL", converted))):
            image_x = x + pair_idx * (image_w + pair_gap)
            image = _fit_with_protocol_overlay(path, (image_w, image_h), bbox)
            image = ImageEnhance.Color(image).enhance(0.75)
            wall.paste(image, (image_x, header_h))
            draw.rectangle((image_x, header_h, image_x + image_w, header_h + image_h), outline=(130, 130, 130), width=2)
            draw.rectangle((image_x, header_h, image_x + image_w, header_h + 20), fill=(248, 248, 248), outline=(130, 130, 130), width=1)
            draw.text((image_x + 6, header_h + 4), pair_label, fill=(38, 95, 156) if pair_idx else (70, 70, 70), font=pair_label_font)
    return wall


def _compose_grounding_contract_bridge(size: tuple[int, int]) -> Image.Image:
    wall = Image.new("RGB", size, (248, 248, 248))
    draw = ImageDraw.Draw(wall)
    title_font = _font(13, bold=True)
    sub_font = _font(10, bold=True)
    note_font = _font(10)
    gap = 12
    card_w = (size[0] - 3 * gap) // 4
    header_h = 30
    label_h = 22
    image_h = size[1] - header_h - label_h - 12
    pair_gap = 6
    half_w = (card_w - pair_gap) // 2
    pairs = [
        ("backpack", (36, 174, 404, 438), (421, 174, 789, 438)),
        ("clock", (818, 174, 1182, 438), (1200, 174, 1566, 438)),
        ("bottle", (36, 552, 404, 816), (421, 552, 789, 816)),
        ("cup", (818, 552, 1182, 816), (1200, 552, 1566, 816)),
    ]
    for idx, (name, original_crop, converted_crop) in enumerate(pairs):
        x = idx * (card_w + gap)
        draw.rectangle((x, 0, x + card_w, size[1]), fill=(252, 252, 252), outline=(150, 150, 150), width=2)
        draw.rectangle((x, 0, x + card_w, 24), fill=(244, 248, 250), outline=(150, 150, 150), width=1)
        draw.text((x + 8, 5), name, fill=(28, 28, 28), font=title_font)
        draw.text((x + card_w - 142, 8), "target-box pair", fill=(80, 80, 80), font=note_font)
        for pair_idx, (pair_label, crop) in enumerate((("original", original_crop), ("noMDL", converted_crop))):
            image_x = x + pair_idx * (half_w + pair_gap)
            label_y = header_h
            image_y = label_y + label_h
            draw.rectangle((image_x, label_y, image_x + half_w, label_y + label_h), fill=(248, 248, 248), outline=(150, 150, 150), width=1)
            draw.text((image_x + 5, label_y + 4), pair_label, fill=(38, 95, 156) if pair_idx else (70, 70, 70), font=sub_font)
            image = _crop_contain(VLM_CLEAN_RERENDER, crop, (half_w, image_h))
            wall.paste(image, (image_x, image_y))
            draw.rectangle((image_x, image_y, image_x + half_w, image_y + image_h), outline=(150, 150, 150), width=2)
    return wall


def build_theory_bridge() -> None:
    width = 1800
    height = 1650
    margin = 42
    label_w = 300
    image_w = width - 2 * margin - label_w - GAP
    band_h = 300
    band_image_h = band_h - 36
    canvas = Image.new("RGB", (width, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)

    draw.text((margin, 30), "Theory metric bridge", fill=(18, 18, 18), font=_font(34, bold=True))
    draw.text(
        (margin, 76),
        "Real render panels connecting hypothesis-level interpretation to the material, VLM, and navigation evidence chains.",
        fill=(66, 66, 66),
        font=_font(18),
    )

    y = 112
    y = _draw_theory_evidence_lens_strip(canvas, draw, x=margin, y=y, w=width - 2 * margin, h=210) + 18
    _draw_bridge_band(
        canvas,
        draw,
        x=margin,
        y=y,
        label_w=label_w,
        image_w=image_w,
        h=band_h,
        title="Material salience",
        note="covered cues and selected limits",
        image=_compose_material_bridge((image_w, band_image_h)),
    )
    y += band_h + GAP
    _draw_bridge_band(
        canvas,
        draw,
        x=margin,
        y=y,
        label_w=label_w,
        image_w=image_w,
        h=band_h,
        title="Grounding contract",
        note="target boxes, not rerun VLM points",
        image=_compose_grounding_contract_bridge((image_w, band_image_h)),
    )
    y += band_h + GAP
    _draw_bridge_band(
        canvas,
        draw,
        x=margin,
        y=y,
        label_w=label_w,
        image_w=image_w,
        h=band_h,
        title="Embodied sensitivity",
        note="metrics, stills, and route context",
        image=_compose_navigation_bridge((image_w, band_image_h)),
    )
    y += band_h + GAP
    _draw_bridge_band(
        canvas,
        draw,
        x=margin,
        y=y,
        label_w=label_w,
        image_w=image_w,
        h=band_h,
        title="Selected-failure anchors",
        note="visible counterexamples, not rates",
        image=_compose_theory_failure_wall((image_w, band_image_h)),
    )

    THEORY_BRIDGE_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(THEORY_BRIDGE_OUT)
    print(THEORY_BRIDGE_OUT)


def _draw_failure_mode_lane(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
    index: str,
    title: str,
    note: str,
    boundary_title: str,
    boundary: str,
    tiles: list[tuple[str, Image.Image]],
) -> int:
    lane_h = 250
    x = MARGIN
    w = WIDTH - 2 * MARGIN
    number_w = 64
    render_w = 990
    focus_w = 340
    boundary_w = w - number_w - render_w - focus_w - 3 * GAP
    image_h = 194
    tile_gap = 12
    tile_w = (render_w - 2 * tile_gap) // 3
    image_y = y + 54
    label_font = _font(22, bold=True)
    body_font = _font(16)
    small_font = _font(12, bold=True)
    index_font = _font(26, bold=True)

    draw.rounded_rectangle((x, y, x + w, y + lane_h), radius=8, fill=(236, 236, 236), outline=(162, 162, 162), width=2)
    draw.text((x + 22, y + 86), index, fill=(22, 22, 22), font=index_font)

    render_x = x + number_w + GAP
    draw.text((render_x, y + 18), "representative tracked renders", fill=(44, 44, 44), font=body_font)
    for idx, (label, tile) in enumerate(tiles):
        tile_x = render_x + idx * (tile_w + tile_gap)
        image = ImageOps.fit(tile, (tile_w, image_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        canvas.paste(image, (tile_x, image_y))
        draw.rectangle((tile_x, image_y, tile_x + tile_w, image_y + image_h), outline=(137, 137, 137), width=2)
        draw.rectangle((tile_x, image_y, tile_x + tile_w, image_y + 24), fill=(248, 248, 248), outline=(137, 137, 137), width=1)
        draw.text((tile_x + 7, image_y + 5), label, fill=(28, 28, 28), font=small_font)

    focus_x = render_x + render_w + GAP
    draw.text((focus_x, y + 30), title, fill=(20, 20, 20), font=label_font)
    draw.multiline_text((focus_x, y + 70), note, fill=(52, 52, 52), font=body_font, spacing=5)
    draw.rounded_rectangle((focus_x, y + lane_h - 44, focus_x + 156, y + lane_h - 18), radius=5, fill=(244, 248, 255), outline=(38, 95, 156), width=2)
    draw.text((focus_x + 14, y + lane_h - 40), "hypothesis", fill=(38, 95, 156), font=_font(13, bold=True))

    boundary_x = focus_x + focus_w + GAP
    draw.rectangle((boundary_x, y + 20, boundary_x + boundary_w, y + lane_h - 20), fill=(247, 247, 247), outline=(154, 154, 154), width=2)
    draw.text((boundary_x + 18, y + 48), boundary_title, fill=(201, 111, 27), font=_font(18, bold=True))
    draw.multiline_text((boundary_x + 18, y + 88), boundary, fill=(45, 45, 45), font=body_font, spacing=6)
    return y + lane_h


def _draw_failure_mode_evidence_wall(canvas: Image.Image, draw: ImageDraw.ImageDraw, *, y: int) -> int:
    x = MARGIN
    w = WIDTH - 2 * MARGIN
    h = 500
    pad = 18
    gap = 14
    title_font = _font(22, bold=True)
    note_font = _font(14)
    label_font = _font(11, bold=True)
    body_font = _font(12)

    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(242, 245, 248), outline=(162, 162, 162), width=2)
    draw.text((x + pad, y + 16), "failure-mode evidence wall", fill=(20, 20, 20), font=title_font)
    draw.text(
        (x + 390, y + 21),
        "orientation panel; dense render crops keep each hypothesis visually anchored.",
        fill=(65, 65, 65),
        font=note_font,
    )

    content_y = y + 58
    content_h = h - 118
    gate_w = 520
    gate_h = content_h
    gate = _fit(THEORY_FAILURE_MODE_GATE_V2_AI_SLOT, (gate_w, gate_h), cover=False)
    canvas.paste(gate, (x + pad, content_y))
    draw.rectangle((x + pad, content_y, x + pad + gate_w, content_y + gate_h), outline=(132, 132, 132), width=2)
    draw.rectangle((x + pad, content_y, x + pad + gate_w, content_y + 24), fill=(248, 248, 248), outline=(132, 132, 132), width=1)
    draw.text((x + pad + 7, content_y + 5), "scope guide", fill=(38, 95, 156), font=label_font)

    def failure_pair_tile(
        original: Path,
        converted: Path,
        bbox: tuple[float, float, float, float],
        size: tuple[int, int],
    ) -> Image.Image:
        tile = Image.new("RGB", size, (250, 250, 250))
        pair_gap = 6
        half_w = (size[0] - pair_gap) // 2
        for idx, path in enumerate((original, converted)):
            image = _fit_with_protocol_overlay(path, (half_w, size[1]), bbox)
            image = ImageEnhance.Color(image).enhance(0.55)
            tile.paste(image, (idx * (half_w + pair_gap), 0))
        return tile

    grid_x = x + pad + gate_w + gap
    grid_w = x + w - pad - grid_x
    cell_gap = 10
    cols = 4
    rows = 2
    cell_w = (grid_w - (cols - 1) * cell_gap) // cols
    cell_h = (content_h - (rows - 1) * cell_gap) // rows
    tiles = [
        ("covered cue", _crop_fit(MATERIAL_BASELINE, (12, 55, 372, 174), (cell_w, cell_h))),
        ("clearcoat cue", _crop_fit(MATERIAL_SUPPLEMENTAL, (24, 62, 284, 258), (cell_w, cell_h))),
        ("procedural cue", _crop_fit(MATERIAL_SUPPLEMENTAL, (24, 340, 284, 535), (cell_w, cell_h))),
        ("target contract", _fit_with_bbox(VLM_BACKPACK_ORIGINAL, (cell_w, cell_h), (207.811, 105.285, 376.441, 364.938))),
        ("route media", _crop_fit(NAV_STILLS, (0, 140, 1106, 770), (cell_w, cell_h))),
        ("0036 route", _crop_fit(NAV_0036_MAIN, (390, 108, 1738, 790), (cell_w, cell_h))),
        ("cup pair", failure_pair_tile(VLM_CUP_ALT_ORIGINAL, VLM_CUP_ALT_CONVERTED, (197.137, 107.89, 402.863, 372.325), (cell_w, cell_h))),
        ("faucet pair", failure_pair_tile(VLM_FAUCET_ORIGINAL, VLM_FAUCET_CONVERTED, (215.154, 118.861, 407.249, 356.885), (cell_w, cell_h))),
    ]
    for idx, (label, tile) in enumerate(tiles):
        col = idx % cols
        row = idx // cols
        tile_x = grid_x + col * (cell_w + cell_gap)
        tile_y = content_y + row * (cell_h + cell_gap)
        image = ImageOps.fit(tile, (cell_w, cell_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        canvas.paste(image, (tile_x, tile_y))
        draw.rectangle((tile_x, tile_y, tile_x + cell_w, tile_y + cell_h), outline=(132, 132, 132), width=2)
        draw.rectangle((tile_x, tile_y, tile_x + cell_w, tile_y + 24), fill=(248, 248, 248), outline=(132, 132, 132), width=1)
        draw.text((tile_x + 7, tile_y + 5), label, fill=(28, 28, 28), font=label_font)

    claim_y = y + h - 46
    draw.rounded_rectangle((x + pad, claim_y, x + w - pad, claim_y + 28), radius=5, fill=(236, 246, 252), outline=(38, 95, 156), width=2)
    draw.text(
        (x + pad + 12, claim_y + 7),
        "Reading note: selected render evidence motivates hypothesis-level interpretation.",
        fill=(38, 95, 156),
        font=body_font,
    )
    return y + h


def build_theory_failure_mode_map() -> None:
    width = WIDTH
    height = 1800
    canvas = Image.new("RGB", (width, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(34, bold=True)
    note_font = _font(18)
    footer_font = _font(15)

    y = MARGIN
    draw.text((MARGIN, y), "Failure-mode interpretation map", fill=(18, 18, 18), font=heading_font)
    y += 48
    draw.text(
        (MARGIN, y),
        "Four hypothesis-level readings tied to real render, material, grounding, and navigation evidence.",
        fill=(64, 64, 64),
        font=note_font,
    )
    y += 58

    y = _draw_failure_mode_lane(
        canvas,
        draw,
        y=y,
        index="1",
        title="Material salience",
        note="Local material cues can\nmatter even when object\nsilhouette remains visible.",
        boundary_title="Scene-bound",
        boundary="Selected inspected\nmaterial cases with\nscoped comparison.",
        tiles=[
            ("covered cue", _crop_fit(MATERIAL_BASELINE, (12, 55, 372, 174), (300, 188))),
            ("clearcoat", _crop_fit(MATERIAL_SUPPLEMENTAL, (24, 62, 284, 258), (300, 188))),
            ("procedural", _crop_fit(MATERIAL_SUPPLEMENTAL, (24, 340, 284, 535), (300, 188))),
        ],
    ) + 18
    y = _draw_failure_mode_lane(
        canvas,
        draw,
        y=y,
        index="2",
        title="Coordinate contract",
        note="Material shift and model\ncoordinate convention are\nreported as separate units.",
        boundary_title="Frame-bound",
        boundary="Target boxes support the\nmetric contract and\npaired render context.",
        tiles=[
            ("backpack", _fit_with_bbox(VLM_BACKPACK_ORIGINAL, (300, 188), (207.811, 105.285, 376.441, 364.938))),
            ("clock", _fit_with_bbox(VLM_CLOCK_ORIGINAL, (300, 188), (211.647, 107.436, 370.171, 360.234))),
            ("bottle", _fit_with_bbox(VLM_BOTTLE_ORIGINAL, (300, 188), (230.385, 89.121, 369.378, 372.696))),
        ],
    ) + 18
    y = _draw_failure_mode_lane(
        canvas,
        draw,
        y=y,
        index="3",
        title="Embodied sensitivity",
        note="Route behavior can change\nwhile a static view remains\nusable for inspection.",
        boundary_title="Route-bound",
        boundary="Official-scene metrics are\nauthoritative; stills are\nselected qualitative media.",
        tiles=[
            ("rollout", _crop_fit(NAV_STILLS, (0, 140, 1106, 770), (300, 188))),
            ("0036/0066", _crop_fit(NAV_0036_MAIN, (390, 108, 1738, 790), (300, 188))),
            ("case", _crop_fit(NAV_SELECTED_CASE, (0, 42, 1106, 360), (300, 188))),
        ],
    ) + 18
    y = _draw_failure_mode_lane(
        canvas,
        draw,
        y=y,
        index="4",
        title="Negative-result discipline",
        note="Clearcoat, procedural texture,\nand route divergence stay\nas scoped limitations.",
        boundary_title="Protocol-bound",
        boundary="Selected failures define\nfuture checks; they do not\nbecome population rates.",
        tiles=[
            ("material limit", _crop_fit(MATERIAL_SUPPLEMENTAL, (0, 0, 856, 285), (300, 188))),
            ("navigation", _crop_fit(NAVIGATION_OUT, (42, 1500, 1758, 2390), (300, 188))),
            ("0036 case", _crop_fit(NAV_0036_CASE, (0, 34, 770, 338), (300, 188))),
        ],
    ) + 22

    y = _draw_failure_mode_evidence_wall(canvas, draw, y=y) + 20

    draw.text(
        (MARGIN, y),
        "Reading rule: this map explains how to interpret evidence already shown elsewhere; it adds no new experiment or result.",
        fill=(70, 70, 70),
        font=footer_font,
    )

    THEORY_FAILURE_MODE_MAP_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(THEORY_FAILURE_MODE_MAP_OUT)
    print(THEORY_FAILURE_MODE_MAP_OUT)


def _draw_hypothesis_boundary_lane(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    note: str,
    accent: tuple[int, int, int],
    tiles: list[tuple[str, Image.Image]],
) -> None:
    title_font = _font(18, bold=True)
    body_font = _font(12)
    small_font = _font(10, bold=True)
    tile_gap = 8
    tile_y = y + 52
    tile_h = h - 68
    tile_w = (w - 32 - 2 * tile_gap) // 3

    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(252, 252, 252), outline=(174, 174, 174), width=2)
    draw.rectangle((x, y, x + 8, y + h), fill=accent)
    draw.text((x + 18, y + 14), title, fill=(20, 20, 20), font=title_font)
    draw.text((x + 18, y + 37), note, fill=(66, 66, 66), font=body_font)
    for idx, (label, tile) in enumerate(tiles):
        tile_x = x + 18 + idx * (tile_w + tile_gap)
        image = ImageOps.fit(tile, (tile_w, tile_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        canvas.paste(image, (tile_x, tile_y))
        draw.rectangle((tile_x, tile_y, tile_x + tile_w, tile_y + tile_h), outline=(139, 139, 139), width=2)
        draw.rectangle((tile_x, tile_y, tile_x + tile_w, tile_y + 21), fill=(248, 248, 248), outline=(139, 139, 139), width=1)
        draw.text((tile_x + 5, tile_y + 5), label, fill=(28, 28, 28), font=small_font)
    draw.rounded_rectangle((x + 18, y + h - 16, x + w - 18, y + h - 7), radius=3, fill=(247, 250, 252), outline=accent, width=1)


def build_theory_hypothesis_boundary_companion() -> None:
    width = 920
    height = 1540
    margin = 28
    gap = 10
    lane_h = 236
    canvas = Image.new("RGB", (width, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(28, bold=True)
    note_font = _font(14)
    footer_font = _font(11)

    y = margin
    draw.text((margin, y), "Hypothesis-scope companion", fill=(18, 18, 18), font=heading_font)
    y += 38
    draw.text(
        (margin, y),
        "Real render rows keep the theory section tied to observed material, grounding, and route evidence.",
        fill=(64, 64, 64),
        font=note_font,
    )
    y += 42

    _draw_hypothesis_boundary_lane(
        canvas,
        draw,
        x=margin,
        y=y,
        w=width - 2 * margin,
        h=lane_h,
        title="material salience",
        note="localized cue loss is interpreted as a scoped hypothesis",
        accent=(40, 96, 168),
        tiles=[
            ("covered", _crop_fit(MATERIAL_BASELINE, (12, 55, 372, 174), (260, 150))),
            ("clearcoat", _crop_fit(MATERIAL_SUPPLEMENTAL, (24, 62, 284, 258), (260, 150))),
            ("procedural", _crop_fit(MATERIAL_SUPPLEMENTAL, (24, 340, 284, 535), (260, 150))),
        ],
    )
    y += lane_h + gap
    _draw_hypothesis_boundary_lane(
        canvas,
        draw,
        x=margin,
        y=y,
        w=width - 2 * margin,
        h=lane_h,
        title="coordinate contract",
        note="target boxes define scoring units before causal interpretation",
        accent=(0, 133, 100),
        tiles=[
            ("backpack", _crop_fit(VLM_CLEAN_RERENDER, (36, 174, 404, 438), (260, 150))),
            ("clock", _crop_fit(VLM_CLEAN_RERENDER, (818, 174, 1182, 438), (260, 150))),
            ("bottle", _crop_fit(VLM_CLEAN_RERENDER, (36, 552, 404, 816), (260, 150))),
        ],
    )
    y += lane_h + gap
    _draw_hypothesis_boundary_lane(
        canvas,
        draw,
        x=margin,
        y=y,
        w=width - 2 * margin,
        h=lane_h,
        title="embodied stack",
        note="navigation stills are scoped route media, not universal conclusions",
        accent=(99, 82, 156),
        tiles=[
            ("rollout", _crop_fit(NAV_STILLS, (0, 140, 1106, 770), (260, 150))),
            ("0036/0066", _crop_fit(NAV_0036_MAIN, (390, 108, 1738, 790), (260, 150))),
            ("case", _crop_fit(NAV_SELECTED_CASE, (0, 42, 1106, 360), (260, 150))),
        ],
    )
    y += lane_h + gap

    def failure_pair_tile(
        original: Path,
        converted: Path,
        bbox: tuple[float, float, float, float],
        size: tuple[int, int] = (320, 150),
    ) -> Image.Image:
        tile = Image.new("RGB", size, (250, 250, 250))
        half_w = (size[0] - 6) // 2
        for idx, path in enumerate((original, converted)):
            image = _fit_with_protocol_overlay(path, (half_w, size[1]), bbox)
            image = ImageEnhance.Color(image).enhance(0.35)
            tile.paste(image, (idx * (half_w + 6), 0))
        return tile

    _draw_hypothesis_boundary_lane(
        canvas,
        draw,
        x=margin,
        y=y,
        w=width - 2 * margin,
        h=lane_h,
        title="selected failure render wall",
        note="failure examples stay visible without becoming rates",
        accent=(112, 92, 142),
        tiles=[
            ("cup view B", failure_pair_tile(VLM_CUP_ALT_ORIGINAL, VLM_CUP_ALT_CONVERTED, (197.137, 107.89, 402.863, 372.325))),
            ("faucet", failure_pair_tile(VLM_FAUCET_ORIGINAL, VLM_FAUCET_CONVERTED, (215.154, 118.861, 407.249, 356.885))),
            ("picture", failure_pair_tile(VLM_PICTURE_ORIGINAL, VLM_PICTURE_CONVERTED, (240.087, 100.65, 374.808, 360.903))),
        ],
    )
    y += lane_h + gap

    strip_h = 104
    draw.rounded_rectangle((margin, y, width - margin, y + strip_h), radius=8, fill=(252, 252, 252), outline=(174, 174, 174), width=2)
    draw.text((margin + 18, y + 12), "cross-hypothesis render audit strip", fill=(20, 20, 20), font=_font(18, bold=True))
    draw.text((margin + 18, y + 36), "real panels stay visible across material, grounding, route, and failure interpretations", fill=(72, 72, 72), font=_font(11))
    audit_tiles = [
        ("proxy", _crop_fit(RENDER_PAIRS, (0, 0, 410, 230), (105, 74))),
        ("material", _crop_fit(MATERIAL_BASELINE, (0, 45, 460, 260), (105, 74))),
        ("target", _crop_fit(VLM_CLEAN_RERENDER, (36, 174, 404, 438), (105, 74))),
        ("clock", _crop_fit(VLM_CLEAN_RERENDER, (818, 174, 1182, 438), (105, 74))),
        ("route", _crop_fit(NAV_STILLS, (0, 118, 1106, 772), (105, 74))),
        ("0036", _crop_fit(NAV_0036_MAIN, (392, 105, 1738, 792), (105, 74))),
        ("failure", failure_pair_tile(VLM_CUP_ALT_ORIGINAL, VLM_CUP_ALT_CONVERTED, (197.137, 107.89, 402.863, 372.325), (146, 74))),
    ]
    tile_gap = 8
    tile_y = y + 54
    tile_w = (width - 2 * margin - 36 - 6 * tile_gap) // 7
    for idx, (label, tile) in enumerate(audit_tiles):
        tx = margin + 18 + idx * (tile_w + tile_gap)
        tw = tile_w
        image = ImageOps.fit(tile, (tw, 54), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        canvas.paste(image, (tx, tile_y))
        draw.rectangle((tx, tile_y, tx + tw, tile_y + 54), outline=(139, 139, 139), width=1)
        draw.rectangle((tx, tile_y, tx + tw, tile_y + 17), fill=(248, 248, 248), outline=(139, 139, 139), width=1)
        draw.text((tx + 4, tile_y + 4), label, fill=(28, 28, 28), font=_font(9, bold=True))
    y += strip_h + gap

    card_h = height - y - margin - 28
    draw.rounded_rectangle((margin, y, width - margin, y + card_h), radius=8, fill=(252, 252, 252), outline=(174, 174, 174), width=2)
    draw.text((margin + 18, y + 14), "hypothesis scope lens", fill=(20, 20, 20), font=_font(18, bold=True))
    draw.text((margin + 18, y + 40), "orientation panel", fill=(72, 72, 72), font=note_font)
    slot_x = margin + 18
    slot_y = y + 58
    slot_h = card_h - 108
    slot_w = min(width - 2 * margin - 36, max(260, int(slot_h * 1.5)))
    slot = _fit(THEORY_HYPOTHESIS_BOUNDARY_V6_AI_SLOT, (slot_w, slot_h), cover=False)
    canvas.paste(slot, (slot_x, slot_y))
    draw.rectangle((slot_x, slot_y, slot_x + slot_w, slot_y + slot_h), outline=(140, 140, 140), width=2)

    checkpoint_x = slot_x + slot_w + 14
    checkpoint_w = width - margin - 18 - checkpoint_x
    checkpoint_h = (slot_h - 14) // 3
    checkpoints = [
        ("cue lane", _crop_fit(MATERIAL_SUPPLEMENTAL, (24, 62, 284, 258), (90, 42)), "material crop constrains the hypothesis"),
        ("score unit", _crop_fit(VLM_CLEAN_RERENDER, (36, 174, 404, 438), (90, 42)), "target box stays a protocol object"),
        (
            "route check",
            failure_pair_tile(VLM_CUP_ALT_ORIGINAL, VLM_CUP_ALT_CONVERTED, (197.137, 107.89, 402.863, 372.325), (90, 42)),
            "selected media remains qualitative",
        ),
    ]
    for idx, (label, tile, note) in enumerate(checkpoints):
        row_y = slot_y + idx * (checkpoint_h + 7)
        draw.rounded_rectangle(
            (checkpoint_x, row_y, checkpoint_x + checkpoint_w, row_y + checkpoint_h),
            radius=5,
            fill=(236, 246, 252),
            outline=(170, 170, 170),
            width=1,
        )
        thumb = ImageOps.fit(tile, (84, checkpoint_h - 12), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        canvas.paste(thumb, (checkpoint_x + 8, row_y + 6))
        draw.rectangle((checkpoint_x + 8, row_y + 6, checkpoint_x + 92, row_y + checkpoint_h - 6), outline=(138, 138, 138), width=1)
        draw.text((checkpoint_x + 104, row_y + 7), label, fill=(24, 24, 24), font=_font(11, bold=True))
        draw.text((checkpoint_x + 104, row_y + 25), note, fill=(62, 62, 62), font=_font(10))
    draw.rounded_rectangle((margin + 18, y + card_h - 40, width - margin - 18, y + card_h - 14), radius=5, fill=(246, 250, 255), outline=(38, 95, 156), width=2)
    draw.text((margin + 30, y + card_h - 34), "hypothesis context", fill=(38, 95, 156), font=note_font)

    draw.text(
        (margin, height - 20),
        "Reading note: render evidence motivates the hypothesis panel.",
        fill=(82, 82, 82),
        font=footer_font,
    )

    THEORY_HYPOTHESIS_BOUNDARY_COMPANION_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(THEORY_HYPOTHESIS_BOUNDARY_COMPANION_OUT)
    print(THEORY_HYPOTHESIS_BOUNDARY_COMPANION_OUT)


def build_review_packet_contact_sheet() -> None:
    height = 2200
    canvas = Image.new("RGB", (WIDTH, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(34, bold=True)
    note_font = _font(18)

    y = MARGIN
    draw.text((MARGIN, y), "Review-packet media manifest", fill=(18, 18, 18), font=heading_font)
    y += 48
    draw.text(
        (MARGIN, y),
        "A visual index of tracked render, material, grounding, and navigation media used by the supplement.",
        fill=(66, 66, 66),
        font=note_font,
    )
    y += 64

    y = _draw_contact_row(
        canvas,
        draw,
        y=y,
        title="Render atlas",
        note="paired object and scene views",
        items=[
            (RENDER_PAIRS, (0, 80, 1367, 1040)),
            (RENDER_SCENE_WIDE, (0, 80, 1800, 840)),
            (SUPPLEMENT_RENDER_ATLAS, (0, 0, 1800, 1040)),
            (RENDER_SCENE_EXTENDED_OUT, (0, 760, 1800, 1592)),
        ],
    ) + GAP
    y = _draw_contact_row(
        canvas,
        draw,
        y=y,
        title="Render evidence",
        note="object and scene crops",
        items=[
            (RENDER_SCENE_EXTENDED_OUT, (0, 0, 900, 760)),
            (RENDER_SCENE_EXTENDED_OUT, (900, 0, 1800, 760)),
            (GRSCENE_QUALITATIVE, (0, 0, 912, 622)),
            (SUPPLEMENT_RENDER_ATLAS, (900, 1160, 1800, 2014)),
        ],
    ) + GAP
    y = _draw_contact_row(
        canvas,
        draw,
        y=y,
        title="Material diagnostics",
        note="covered bins and limitations",
        items=[
            (MATERIAL_OUT, (40, 120, 1740, 1050)),
            (MATERIAL_OUT, (40, 1060, 1740, 2240)),
            (MATERIAL_SUPPLEMENTAL, (24, 62, 832, 535)),
        ],
    ) + GAP
    y = _draw_contact_row(
        canvas,
        draw,
        y=y,
        title="VLM target views",
        note="clean target-box renders",
        items=[
            (VLM_CLEAN_RERENDER, (20, 108, 802, 490)),
            (VLM_CLEAN_RERENDER, (810, 108, 1582, 490)),
            (VLM_CLEAN_RERENDER, (20, 506, 802, 890)),
            (VLM_CLEAN_RERENDER, (810, 506, 1582, 890)),
        ],
    ) + GAP
    _draw_contact_row(
        canvas,
        draw,
        y=y,
        title="Navigation videos",
        note="official stills and routes",
        items=[
            (NAVIGATION_OUT, (40, 650, 880, 1450)),
            (NAVIGATION_OUT, (900, 650, 1760, 1450)),
            (NAV_SELECTED_CASE, (0, 42, 1106, 360)),
            (NAV_0036_CASE, (0, 34, 770, 338)),
            (NAVIGATION_MEDIA_BOUNDARY_OUT, (40, 180, 1960, 1510)),
        ],
    )

    REVIEW_PACKET_CONTACT_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(REVIEW_PACKET_CONTACT_OUT)
    print(REVIEW_PACKET_CONTACT_OUT)


def _draw_source_boundary_tile(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    note: str,
    path: Path,
    cover: bool = True,
    accent: tuple[int, int, int] = (42, 103, 158),
) -> None:
    title_font = _font(15, bold=True)
    note_font = _font(11)
    image_y = y + 48
    image_h = h - 60

    draw.rounded_rectangle((x, y, x + w, y + h), radius=7, fill=(252, 252, 252), outline=(168, 168, 168), width=2)
    draw.rectangle((x, y, x + w, y + 5), fill=accent)
    draw.text((x + 12, y + 11), title, fill=(20, 20, 20), font=title_font)
    draw.text((x + 12, y + 31), note, fill=(72, 72, 72), font=note_font)
    canvas.paste(_fit(path, (w - 18, image_h), cover=cover), (x + 9, image_y))
    draw.rectangle((x + 9, image_y, x + w - 9, image_y + image_h), outline=(135, 135, 135), width=2)


def build_source_boundary_companion() -> None:
    width = 1320
    height = 1380
    margin = 28
    gap = 12
    canvas = Image.new("RGB", (width, height), (236, 236, 236))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(31, bold=True)
    subtitle_font = _font(17)
    label_font = _font(16, bold=True)
    note_font = _font(13)

    draw.text((margin, 22), "Source-scope review companion", fill=(18, 18, 18), font=heading_font)
    draw.text(
        (margin, 62),
        "source readable render panels plus one source guide; raw/private artifacts remain outside the review packet.",
        fill=(66, 66, 66),
        font=subtitle_font,
    )

    left_x = margin
    left_y = 104
    left_w = 800
    tile_w = (left_w - 2 * gap) // 3
    tile_h = 210
    tiles = [
        ("packet index", "tracked visual classes", REVIEW_PACKET_CONTACT_OUT, (42, 103, 158)),
        ("render atlas", "scene/object context", RENDER_ATLAS_OPENER_OUT, (39, 126, 112)),
        ("material atlas", "diagnostic bins", MATERIAL_OUT, (104, 93, 156)),
        ("VLM renders", "target-box views", VLM_CLEAN_RERENDER, (40, 112, 166)),
        ("navigation media", "reviewable route stills", NAVIGATION_MEDIA_BOUNDARY_OUT, (74, 132, 78)),
        ("route case 04", "selected still panel", NAV_SELECTED_CASE4, (88, 112, 160)),
    ]
    for idx, (title, note, path, accent) in enumerate(tiles):
        row = idx // 3
        col = idx % 3
        _draw_source_boundary_tile(
            canvas,
            draw,
            x=left_x + col * (tile_w + gap),
            y=left_y + row * (tile_h + gap),
            w=tile_w,
            h=tile_h,
            title=title,
            note=note,
            path=path,
            cover=True,
            accent=accent,
        )

    route_y = left_y + 2 * (tile_h + gap)
    draw.rounded_rectangle(
        (left_x, route_y, left_x + left_w, route_y + 156),
        radius=7,
        fill=(252, 252, 252),
        outline=(168, 168, 168),
        width=2,
    )
    draw.rectangle((left_x, route_y, left_x + left_w, route_y + 5), fill=(39, 120, 136))
    draw.text((left_x + 14, route_y + 12), "0036/0066 route case 04", fill=(20, 20, 20), font=label_font)
    draw.text((left_x + 14, route_y + 38), "paired route stills", fill=(72, 72, 72), font=note_font)
    route_img = _fit(NAV_0036_CASE4, (left_w - 300, 114), cover=True)
    canvas.paste(route_img, (left_x + 286, route_y + 20))
    draw.rectangle((left_x + 286, route_y + 20, left_x + left_w - 14, route_y + 134), outline=(135, 135, 135), width=2)
    for chip_idx, chip in enumerate(["source", "readable", "case-scoped"]):
        chip_x = left_x + 14
        chip_y = route_y + 70 + chip_idx * 29
        draw.rounded_rectangle((chip_x, chip_y, chip_x + 208, chip_y + 22), radius=5, fill=(246, 250, 255), outline=(42, 103, 158), width=1)
        draw.text((chip_x + 10, chip_y + 3), chip, fill=(42, 103, 158), font=note_font)

    right_x = left_x + left_w + 22
    right_y = left_y
    right_w = width - margin - right_x
    right_h = 650
    draw.rounded_rectangle((right_x, right_y, right_x + right_w, right_y + right_h), radius=8, fill=(252, 252, 252), outline=(168, 168, 168), width=2)
    draw.rectangle((right_x, right_y, right_x + right_w, right_y + 6), fill=(38, 95, 156))
    draw.text((right_x + 18, right_y + 17), "source-scope guide", fill=(18, 18, 18), font=_font(20, bold=True))
    draw.text((right_x + 18, right_y + 45), "orientation panel", fill=(72, 72, 72), font=note_font)

    slot_y = right_y + 70
    slot_h = 420
    slot = _fit(SOURCE_BOUNDARY_GATE_AI_SLOT, (right_w - 32, slot_h), cover=False)
    canvas.paste(slot, (right_x + 16, slot_y))
    draw.rectangle((right_x + 16, slot_y, right_x + right_w - 16, slot_y + slot_h), outline=(135, 135, 135), width=2)

    flow_y = slot_y + slot_h + 18
    flow = [
        ("readable sources", (42, 103, 158)),
        ("review packet", (39, 126, 112)),
        ("excluded raw/private", (116, 108, 82)),
    ]
    chip_w = (right_w - 56) // 3
    for idx, (chip, color) in enumerate(flow):
        chip_x = right_x + 16 + idx * (chip_w + 12)
        draw.rounded_rectangle((chip_x, flow_y, chip_x + chip_w, flow_y + 38), radius=6, fill=(246, 250, 255), outline=color, width=2)
        draw.text((chip_x + 8, flow_y + 10), chip, fill=color, font=_font(10, bold=True))
        if idx < 2:
            arrow_x = chip_x + chip_w + 3
            draw.line((arrow_x, flow_y + 19, arrow_x + 8, flow_y + 19), fill=(90, 90, 90), width=2)
            draw.polygon((arrow_x + 8, flow_y + 15, arrow_x + 8, flow_y + 23, arrow_x + 14, flow_y + 19), fill=(90, 90, 90))

    boundary_text = [
        "source index",
        "source index context",
        "source panel can be replaced by a future real render",
    ]
    for idx, line in enumerate(boundary_text):
        y = flow_y + 58 + idx * 26
        draw.rectangle((right_x + 18, y + 4, right_x + 28, y + 14), fill=(39, 126, 112))
        draw.text((right_x + 36, y), line, fill=(45, 45, 45), font=note_font)

    tray_y = 784
    tray_h = 230
    draw.rounded_rectangle(
        (margin, tray_y, width - margin, tray_y + tray_h),
        radius=8,
        fill=(252, 252, 252),
        outline=(168, 168, 168),
        width=2,
    )
    draw.rectangle((margin, tray_y, width - margin, tray_y + 6), fill=(39, 126, 112))
    draw.text((margin + 16, tray_y + 16), "source render source tray", fill=(18, 18, 18), font=_font(20, bold=True))
    draw.text(
        (margin + 16, tray_y + 42),
        "more readable source imagery; no raw/private frame directories are pulled into the PDF",
        fill=(72, 72, 72),
        font=note_font,
    )
    tray_items = [
        ("proxy pairs", RENDER_PAIRS),
        ("scene context", RENDER_SCENE_WIDE),
        ("target views", VLM_CLEAN_RERENDER),
        ("material baseline", MATERIAL_BASELINE),
        ("route stills", NAV_0036_CASE4),
    ]
    thumb_gap = 12
    thumb_y = tray_y + 80
    thumb_h = 126
    thumb_w = (width - 2 * margin - 32 - thumb_gap * (len(tray_items) - 1)) // len(tray_items)
    for idx, (label, path) in enumerate(tray_items):
        thumb_x = margin + 16 + idx * (thumb_w + thumb_gap)
        draw.text((thumb_x, thumb_y - 17), label, fill=(45, 45, 45), font=_font(12, bold=True))
        canvas.paste(_fit(path, (thumb_w, thumb_h), cover=True), (thumb_x, thumb_y))
        draw.rectangle((thumb_x, thumb_y, thumb_x + thumb_w, thumb_y + thumb_h), outline=(135, 135, 135), width=2)

    pair_y = 1034
    pair_h = 216
    draw.rounded_rectangle(
        (margin, pair_y, width - margin, pair_y + pair_h),
        radius=8,
        fill=(252, 252, 252),
        outline=(168, 168, 168),
        width=2,
    )
    draw.rectangle((margin, pair_y, width - margin, pair_y + 6), fill=(42, 103, 158))
    draw.text((margin + 16, pair_y + 16), "paired target-view closeups", fill=(18, 18, 18), font=_font(20, bold=True))
    draw.text(
        (margin + 16, pair_y + 42),
        "selected source original/noMDL target renders used as readable examples, selected row examples",
        fill=(72, 72, 72),
        font=note_font,
    )
    pair_items = [
        ("backpack", VLM_BACKPACK_ORIGINAL, VLM_BACKPACK_CONVERTED),
        ("clock", VLM_CLOCK_ORIGINAL, VLM_CLOCK_CONVERTED),
        ("bottle", VLM_BOTTLE_ORIGINAL, VLM_BOTTLE_CONVERTED),
        ("cup", VLM_CUP_ORIGINAL, VLM_CUP_CONVERTED),
    ]
    pair_gap = 14
    pair_w = (width - 2 * margin - 32 - pair_gap * (len(pair_items) - 1)) // len(pair_items)
    pair_img_y = pair_y + 78
    pair_img_h = 116
    half_gap = 7
    half_w = (pair_w - half_gap) // 2
    for idx, (label, original_path, converted_path) in enumerate(pair_items):
        card_x = margin + 16 + idx * (pair_w + pair_gap)
        draw.text((card_x, pair_img_y - 18), label, fill=(45, 45, 45), font=_font(12, bold=True))
        canvas.paste(_fit(original_path, (half_w, pair_img_h), cover=True), (card_x, pair_img_y))
        canvas.paste(_fit(converted_path, (half_w, pair_img_h), cover=True), (card_x + half_w + half_gap, pair_img_y))
        draw.rectangle((card_x, pair_img_y, card_x + half_w, pair_img_y + pair_img_h), outline=(135, 135, 135), width=2)
        draw.rectangle((card_x + half_w + half_gap, pair_img_y, card_x + pair_w, pair_img_y + pair_img_h), outline=(135, 135, 135), width=2)
        draw.text((card_x + 6, pair_img_y + pair_img_h - 16), "orig", fill=(35, 35, 35), font=_font(10, bold=True))
        draw.text((card_x + half_w + half_gap + 6, pair_img_y + pair_img_h - 16), "noMDL", fill=(35, 35, 35), font=_font(10, bold=True))

    footer_y = height - 104
    draw.rounded_rectangle((margin, footer_y, width - margin, height - 28), radius=8, fill=(252, 252, 252), outline=(168, 168, 168), width=2)
    draw.text((margin + 18, footer_y + 15), "Result scope", fill=(18, 18, 18), font=_font(18, bold=True))
    draw.text(
        (margin + 214, footer_y + 17),
        "Guide only; all evidence-bearing panels are source source figures. The scoring panel explains what is excluded.",
        fill=(55, 55, 55),
        font=subtitle_font,
    )
    draw.text(
        (margin + 18, footer_y + 50),
        "Companion role: densify the reproducibility page with render-heavy traceability while preserving source/evidence scope.",
        fill=(80, 80, 80),
        font=_font(14),
    )

    SOURCE_BOUNDARY_COMPANION_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(SOURCE_BOUNDARY_COMPANION_OUT)
    print(SOURCE_BOUNDARY_COMPANION_OUT)


def build_material_atlas() -> None:
    height = 2380
    canvas = Image.new("RGB", (WIDTH, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(30, bold=True)
    note_font = _font(17)

    y = MARGIN
    draw.text((MARGIN, y), "Material diagnostics: covered bins and limitation cases", fill=(18, 18, 18), font=heading_font)
    y += TITLE_H
    draw.text(
        (MARGIN, y),
        "All panels are tracked renders for qualitative inspection.",
        fill=(70, 70, 70),
        font=note_font,
    )
    y += 46

    full_w = WIDTH - 2 * MARGIN
    _draw_panel(
        canvas,
        draw,
        x=MARGIN,
        y=y,
        w=full_w,
        h=990,
        title="Covered bins: Original MDL / ConvertAsset / NVIDIA",
        path=MATERIAL_BASELINE,
    )
    y += LABEL_H + 990 + GAP
    _draw_panel(
        canvas,
        draw,
        x=MARGIN,
        y=y,
        w=full_w,
        h=910,
        title="Limitation diagnostics: clearcoat and procedural texture",
        path=MATERIAL_SUPPLEMENTAL,
    )

    MATERIAL_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(MATERIAL_OUT)
    print(MATERIAL_OUT)


def build_navigation_atlas() -> None:
    height = 2450
    canvas = Image.new("RGB", (WIDTH, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(30, bold=True)
    note_font = _font(17)

    y = MARGIN
    draw.text((MARGIN, y), "InternNav selected media: metrics, stills, and route context", fill=(18, 18, 18), font=heading_font)
    y += TITLE_H
    draw.text(
        (MARGIN, y),
        "The overview uses selected qualitative media only. Case pages below remain the larger per-example evidence.",
        fill=(70, 70, 70),
        font=note_font,
    )
    y += 46

    full_w = WIDTH - 2 * MARGIN
    _draw_panel(
        canvas,
        draw,
        x=MARGIN,
        y=y,
        w=full_w,
        h=515,
        title="Downstream paired-run summary panel",
        path=NAV_DOWNSTREAM,
    )
    y += LABEL_H + 515 + GAP

    half_w = (full_w - GAP) // 2
    _draw_panel(
        canvas,
        draw,
        x=MARGIN,
        y=y,
        w=half_w,
        h=710,
        title="Selected rollout stills",
        path=NAV_STILLS,
    )
    _draw_panel(
        canvas,
        draw,
        x=MARGIN + half_w + GAP,
        y=y,
        w=half_w,
        h=710,
        title="0036/0066 readable route panel",
        path=NAV_0036_MAIN,
    )
    y += LABEL_H + 710 + GAP

    _draw_image_panel(
        canvas,
        draw,
        x=MARGIN,
        y=y,
        w=half_w,
        h=760,
        title="Selected6 index rows 05-06",
        image=_navigation_pair_row_cards(NAV_SELECTED6, (half_w, 760)),
    )
    _draw_image_panel(
        canvas,
        draw,
        x=MARGIN + half_w + GAP,
        y=y,
        w=half_w,
        h=760,
        title="0036/0066 official still rows",
        image=_navigation_0036_row_detail_cards(NAV_0036_SELECTED6, (half_w, 760)),
    )

    NAVIGATION_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(NAVIGATION_OUT)
    print(NAVIGATION_OUT)


def _case_frame_tile(path: Path, box: tuple[int, int, int, int], size: tuple[int, int]) -> Image.Image:
    source = Image.open(path).convert("RGB")
    crop = source.crop(box)
    crop = ImageEnhance.Contrast(crop).enhance(1.08)
    crop = ImageEnhance.Color(crop).enhance(1.05)
    return ImageOps.fit(crop, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def _selected6_panel_crop(path: Path, condition: str) -> Image.Image:
    source = Image.open(path).convert("RGB")
    if condition == "original":
        box = (0, 0, min(552, source.width), min(244, source.height))
    elif condition == "nomdl":
        box = (min(560, source.width), 0, source.width, min(244, source.height))
    else:
        raise ValueError(f"unknown selected6 condition: {condition}")
    crop = source.crop(box)
    crop = ImageEnhance.Contrast(crop).enhance(1.08)
    crop = ImageEnhance.Color(crop).enhance(1.04)
    return crop


def _selected6_panel(path: Path, condition: str, size: tuple[int, int]) -> Image.Image:
    return ImageOps.fit(_selected6_panel_crop(path, condition), size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def _selected6_detail_tile(path: Path, condition: str, detail: str, size: tuple[int, int]) -> Image.Image:
    panel = _selected6_panel_crop(path, condition)
    usable_h = max(1, panel.height - 25)
    split = int(panel.width * 0.48)
    if detail == "view":
        crop = panel.crop((0, 0, split, usable_h))
    elif detail == "map":
        crop = panel.crop((split, 0, panel.width, usable_h))
    else:
        raise ValueError(f"unknown selected6 detail: {detail}")
    return ImageOps.fit(crop, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def _draw_selected6_neutral_case(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    path: Path,
    case_id: str,
    status: str,
    accent: tuple[int, int, int],
) -> None:
    title_font = _font(22, bold=True)
    note_font = _font(14)
    chip_font = _font(12, bold=True)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=9, fill=(248, 248, 248), outline=(158, 158, 158), width=2)
    draw.rectangle((x, y, x + w, y + 7), fill=accent)
    draw.text((x + 18, y + 18), f"case {case_id}", fill=(18, 18, 18), font=title_font)
    draw.text((x + 206, y + 23), status, fill=(70, 70, 70), font=note_font)

    chip_specs = [("original", (242, 247, 252)), ("noMDL", (242, 250, 246)), ("neutral selected case", (250, 248, 241))]
    for idx, (chip, fill) in enumerate(chip_specs):
        chip_x = x + w - 520 + idx * 168
        draw.rounded_rectangle((chip_x, y + 16, chip_x + 154, y + 42), radius=5, fill=fill, outline=accent, width=1)
        draw.text((chip_x + 9, y + 22), chip, fill=accent, font=chip_font)

    gap = 14
    panel_y = y + 62
    panel_h = 220
    panel_w = (w - 36 - gap) // 2
    panels = [
        ("original still + route", _selected6_panel(path, "original", (panel_w, panel_h))),
        ("noMDL still + route", _selected6_panel(path, "nomdl", (panel_w, panel_h))),
    ]
    for idx, (label, tile) in enumerate(panels):
        tile_x = x + 18 + idx * (panel_w + gap)
        canvas.paste(tile, (tile_x, panel_y))
        draw.rectangle((tile_x, panel_y, tile_x + panel_w, panel_y + panel_h), outline=(112, 112, 112), width=2)
        draw.rectangle((tile_x, panel_y, tile_x + panel_w, panel_y + 25), fill=(246, 246, 246), outline=(112, 112, 112), width=1)
        draw.text((tile_x + 8, panel_y + 6), label, fill=(28, 28, 28), font=chip_font)

    detail_y = panel_y + panel_h + 14
    detail_h = h - (detail_y - y) - 18
    detail_gap = 12
    detail_w = (w - 36 - 3 * detail_gap) // 4
    details = [
        ("orig view", _selected6_detail_tile(path, "original", "view", (detail_w, detail_h))),
        ("orig route", _selected6_detail_tile(path, "original", "map", (detail_w, detail_h))),
        ("noMDL view", _selected6_detail_tile(path, "nomdl", "view", (detail_w, detail_h))),
        ("noMDL route", _selected6_detail_tile(path, "nomdl", "map", (detail_w, detail_h))),
    ]
    for idx, (label, tile) in enumerate(details):
        tile_x = x + 18 + idx * (detail_w + detail_gap)
        canvas.paste(tile, (tile_x, detail_y))
        draw.rectangle((tile_x, detail_y, tile_x + detail_w, detail_y + detail_h), outline=(120, 120, 120), width=2)
        draw.rectangle((tile_x, detail_y, tile_x + detail_w, detail_y + 22), fill=(246, 246, 246), outline=(120, 120, 120), width=1)
        draw.text((tile_x + 7, detail_y + 4), label, fill=(30, 30, 30), font=chip_font)


def _draw_selected6_neutral_context(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
) -> None:
    title_font = _font(22, bold=True)
    note_font = _font(14)
    label_font = _font(12, bold=True)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=9, fill=(248, 248, 248), outline=(158, 158, 158), width=2)
    draw.rectangle((x, y, x + w, y + 7), fill=(86, 86, 86))
    draw.text((x + 18, y + 18), "source selected6 neutral context", fill=(18, 18, 18), font=title_font)
    draw.text((x + 18, y + 50), "The page reuses selected official stills and route overlays; it remains qualitative orientation evidence.", fill=(70, 70, 70), font=note_font)

    tile_gap = 14
    tile_y = y + 82
    tile_h = h - 104
    left_w = int((w - 36 - 2 * tile_gap) * 0.44)
    mid_w = int((w - 36 - 2 * tile_gap) * 0.30)
    right_w = w - 36 - 2 * tile_gap - left_w - mid_w
    tiles = [
        ("selected6 rows 05-06", _crop_fit(NAV_SELECTED6, (0, 1718, 1106, 2542), (left_w, tile_h))),
        ("official still context", _crop_fit(NAV_STILLS, (0, 72, 1106, 430), (mid_w, tile_h))),
        ("neutral-guide slot", _fit(SELECTED6_NEUTRAL_GATE_AI_SLOT, (right_w, tile_h), cover=False)),
    ]
    tile_x = x + 18
    for label, tile in tiles:
        canvas.paste(tile, (tile_x, tile_y))
        draw.rectangle((tile_x, tile_y, tile_x + tile.width, tile_y + tile.height), outline=(118, 118, 118), width=2)
        draw.rectangle((tile_x, tile_y, tile_x + tile.width, tile_y + 23), fill=(246, 246, 246), outline=(118, 118, 118), width=1)
        draw.text((tile_x + 7, tile_y + 5), label, fill=(30, 30, 30), font=label_font)
        tile_x += tile.width + tile_gap


def _draw_selected6_neutral_footer(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
) -> None:
    title_font = _font(22, bold=True)
    note_font = _font(14)
    label_font = _font(12, bold=True)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=9, fill=(248, 248, 248), outline=(158, 158, 158), width=2)
    draw.rectangle((x, y, x + w, y + 7), fill=(74, 118, 76))
    draw.text((x + 18, y + 18), "compact neutral evidence strip", fill=(18, 18, 18), font=title_font)
    draw.text((x + 18, y + 50), "Small tiles repeat only source frame and route crops; the guide explains review scope.", fill=(70, 70, 70), font=note_font)

    top = y + 82
    tile_gap = 12
    strip_w = int((w - 36 - tile_gap) * 0.66)
    gate_w = w - 36 - tile_gap - strip_w
    tile_w = (strip_w - 2 * tile_gap) // 3
    tile_h = (h - 108 - tile_gap) // 2
    tiles = [
        ("493 orig view", _selected6_detail_tile(NAV_SELECTED_CASE5, "original", "view", (tile_w, tile_h))),
        ("493 orig route", _selected6_detail_tile(NAV_SELECTED_CASE5, "original", "map", (tile_w, tile_h))),
        ("493 noMDL route", _selected6_detail_tile(NAV_SELECTED_CASE5, "nomdl", "map", (tile_w, tile_h))),
        ("484 orig view", _selected6_detail_tile(NAV_SELECTED_CASE6, "original", "view", (tile_w, tile_h))),
        ("484 noMDL view", _selected6_detail_tile(NAV_SELECTED_CASE6, "nomdl", "view", (tile_w, tile_h))),
        ("484 noMDL route", _selected6_detail_tile(NAV_SELECTED_CASE6, "nomdl", "map", (tile_w, tile_h))),
    ]
    for idx, (label, tile) in enumerate(tiles):
        col = idx % 3
        row = idx // 3
        tile_x = x + 18 + col * (tile_w + tile_gap)
        tile_y = top + row * (tile_h + tile_gap)
        canvas.paste(tile, (tile_x, tile_y))
        draw.rectangle((tile_x, tile_y, tile_x + tile_w, tile_y + tile_h), outline=(120, 120, 120), width=2)
        draw.rectangle((tile_x, tile_y, tile_x + tile_w, tile_y + 22), fill=(246, 246, 246), outline=(120, 120, 120), width=1)
        draw.text((tile_x + 7, tile_y + 4), label, fill=(30, 30, 30), font=label_font)

    gate_x = x + 18 + strip_w + tile_gap
    gate_h = h - 104
    gate = _fit(SELECTED6_NEUTRAL_GATE_AI_SLOT, (gate_w, gate_h), cover=False)
    canvas.paste(gate, (gate_x, top))
    draw.rectangle((gate_x, top, gate_x + gate_w, top + gate_h), outline=(120, 120, 120), width=2)
    draw.rectangle((gate_x, top, gate_x + gate_w, top + 23), fill=(246, 246, 246), outline=(120, 120, 120), width=1)
    draw.text((gate_x + 7, top + 5), "selected6-neutral guide", fill=(30, 30, 30), font=label_font)


def build_internnav_selected6_neutral_companion() -> None:
    width = 1500
    height = 1900
    margin = 36
    gap = 18
    canvas = Image.new("RGB", (width, height), (236, 236, 236))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(32, bold=True)
    note_font = _font(17)

    draw.text((margin, 24), "Selected6 neutral navigation companion", fill=(18, 18, 18), font=heading_font)
    draw.text(
        (margin, 66),
        "Neutral selected cases are expanded into source still, route, and review-scope crops; no aggregate metric changes.",
        fill=(64, 64, 64),
        font=note_font,
    )

    card_w = width - 2 * margin
    context_h = 300
    case_h = 470
    footer_h = 370
    y = 112
    _draw_selected6_neutral_context(canvas, draw, x=margin, y=y, w=card_w, h=context_h)
    y += context_h + gap
    _draw_selected6_neutral_case(
        canvas,
        draw,
        x=margin,
        y=y,
        w=card_w,
        h=case_h,
        path=NAV_SELECTED_CASE5,
        case_id="493_493",
        status="both-failure-neutral; matched failure context",
        accent=(39, 112, 160),
    )
    y += case_h + gap
    _draw_selected6_neutral_case(
        canvas,
        draw,
        x=margin,
        y=y,
        w=card_w,
        h=case_h,
        path=NAV_SELECTED_CASE6,
        case_id="484_484",
        status="both-success-neutral; matched success context",
        accent=(39, 126, 112),
    )
    y += case_h + gap
    _draw_selected6_neutral_footer(canvas, draw, x=margin, y=y, w=card_w, h=footer_h)

    footer_y = height - 62
    draw.rounded_rectangle((margin, footer_y, width - margin, height - 28), radius=7, fill=(248, 248, 248), outline=(158, 158, 158), width=2)
    draw.text((margin + 16, footer_y + 12), "Reading note: selected stills and route crops remain qualitative orientation evidence.", fill=(50, 50, 50), font=note_font)

    INTERNNAV_SELECTED6_NEUTRAL_COMPANION_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(INTERNNAV_SELECTED6_NEUTRAL_COMPANION_OUT)
    print(INTERNNAV_SELECTED6_NEUTRAL_COMPANION_OUT)


def _draw_0036_neutral_case(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    path: Path,
    case_id: str,
    status: str,
    accent: tuple[int, int, int],
) -> None:
    title_font = _font(22, bold=True)
    note_font = _font(14)
    chip_font = _font(12, bold=True)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=9, fill=(248, 248, 248), outline=(158, 158, 158), width=2)
    draw.rectangle((x, y, x + w, y + 7), fill=accent)
    draw.text((x + 18, y + 18), f"case {case_id}", fill=(18, 18, 18), font=title_font)
    draw.text((x + 232, y + 23), status, fill=(70, 70, 70), font=note_font)
    chips = ["original row", "noMDL row", "start / mid / end"]
    for idx, chip in enumerate(chips):
        chip_x = x + w - 500 + idx * 158
        draw.rounded_rectangle((chip_x, y + 16, chip_x + 146, y + 42), radius=5, fill=(242, 247, 250), outline=accent, width=1)
        draw.text((chip_x + 9, y + 22), chip, fill=accent, font=chip_font)

    tile_gap = 12
    tile_w = (w - 36 - 2 * tile_gap) // 3
    tile_h = (h - 100 - tile_gap) // 2
    # Each source panel is a 3-column by 2-row still/route strip. These crops
    # remove label whitespace while preserving the original/noMDL row order.
    boxes = [
        (0, 43, 250, 137),
        (260, 43, 510, 137),
        (520, 43, 770, 137),
        (0, 202, 250, 305),
        (260, 202, 510, 305),
        (520, 202, 770, 305),
    ]
    labels = ["orig start", "orig mid", "orig end", "noMDL start", "noMDL mid", "noMDL end"]
    grid_y = y + 66
    for idx, box in enumerate(boxes):
        col = idx % 3
        row = idx // 3
        tile_x = x + 18 + col * (tile_w + tile_gap)
        tile_y = grid_y + row * (tile_h + tile_gap)
        tile = _case_frame_tile(path, box, (tile_w, tile_h))
        canvas.paste(tile, (tile_x, tile_y))
        draw.rectangle((tile_x, tile_y, tile_x + tile_w, tile_y + tile_h), outline=(118, 118, 118), width=2)
        draw.rectangle((tile_x, tile_y, tile_x + tile_w, tile_y + 23), fill=(246, 246, 246), outline=(118, 118, 118), width=1)
        draw.text((tile_x + 7, tile_y + 5), labels[idx], fill=(30, 30, 30), font=chip_font)


def _draw_0036_context_band(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
) -> None:
    title_font = _font(22, bold=True)
    note_font = _font(14)
    label_font = _font(12, bold=True)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=9, fill=(248, 248, 248), outline=(158, 158, 158), width=2)
    draw.rectangle((x, y, x + w, y + 7), fill=(86, 86, 86))
    draw.text((x + 18, y + 18), "source 0036/0066 context", fill=(18, 18, 18), font=title_font)
    draw.text(
        (x + 18, y + 50),
        "Read the neutral cases against the source rollout sheet; these crops are still qualitative evidence.",
        fill=(70, 70, 70),
        font=note_font,
    )
    tile_gap = 14
    tile_y = y + 82
    tile_h = h - 104
    tile_w = (w - 36 - tile_gap) // 2
    tiles = [
        ("official selected 0036/0066 rows", _crop_fit(NAV_0036_MAIN, (18, 104, 1732, 764), (tile_w, tile_h))),
        ("route-shape context crops", _crop_fit(NAV_0036_MAIN, (288, 122, 1732, 542), (tile_w, tile_h))),
    ]
    for idx, (label, tile) in enumerate(tiles):
        tile_x = x + 18 + idx * (tile_w + tile_gap)
        canvas.paste(tile, (tile_x, tile_y))
        draw.rectangle((tile_x, tile_y, tile_x + tile_w, tile_y + tile_h), outline=(118, 118, 118), width=2)
        draw.rectangle((tile_x, tile_y, tile_x + tile_w, tile_y + 23), fill=(246, 246, 246), outline=(118, 118, 118), width=1)
        draw.text((tile_x + 7, tile_y + 5), label, fill=(30, 30, 30), font=label_font)


def build_internnav_0036_neutral_companion() -> None:
    width = 1500
    height = 1680
    margin = 36
    gap = 18
    canvas = Image.new("RGB", (width, height), (236, 236, 236))
    draw = ImageDraw.Draw(canvas)
    heading_font = _font(32, bold=True)
    note_font = _font(17)

    draw.text((margin, 24), "0036/0066 neutral navigation cases", fill=(18, 18, 18), font=heading_font)
    draw.text(
        (margin, 66),
        "source selected stills are cropped into a dense start/mid/end grid; this is qualitative orientation evidence, media context.",
        fill=(64, 64, 64),
        font=note_font,
    )

    card_w = width - 2 * margin
    context_h = 330
    card_h = 512
    _draw_0036_context_band(
        canvas,
        draw,
        x=margin,
        y=112,
        w=card_w,
        h=context_h,
    )
    _draw_0036_neutral_case(
        canvas,
        draw,
        x=margin,
        y=112 + context_h + gap,
        w=card_w,
        h=card_h,
        path=NAV_0036_CASE5,
        case_id="891_891",
        status="both-failure-neutral; failure-context inspection",
        accent=(39, 112, 160),
    )
    _draw_0036_neutral_case(
        canvas,
        draw,
        x=margin,
        y=112 + context_h + gap + card_h + gap,
        w=card_w,
        h=card_h,
        path=NAV_0036_CASE6,
        case_id="598_598",
        status="both-success-neutral; selected explanation context",
        accent=(39, 126, 112),
    )

    footer_y = height - 64
    draw.rounded_rectangle((margin, footer_y, width - margin, height - 28), radius=7, fill=(248, 248, 248), outline=(158, 158, 158), width=2)
    draw.text((margin + 16, footer_y + 13), "Reading note: selected stills complete the balanced qualitative set.", fill=(50, 50, 50), font=note_font)

    INTERNNAV_0036_NEUTRAL_COMPANION_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(INTERNNAV_0036_NEUTRAL_COMPANION_OUT)
    print(INTERNNAV_0036_NEUTRAL_COMPANION_OUT)


def main() -> None:
    build_render_scene_evidence_extended()
    build_render_atlas_opener()
    build_metric_boundary_bridge()
    build_proxy_metric_derivation_companion()
    build_grounding_derivation_companion()
    build_navigation_derivation_companion()
    build_material_intro_strip()
    build_material_intro_column()
    build_navigation_intro_strip()
    build_theory_bridge()
    build_navigation_atlas()
    build_claim_boundary_examples()
    build_evidence_gate_registry_companion()
    build_navigation_media_boundary_strip()
    build_internnav_selected6_neutral_companion()
    build_internnav_0036_neutral_companion()
    build_navigation_intro_column()
    build_internnav_upload_gate_closure_card()
    build_theory_failure_mode_map()
    build_theory_hypothesis_boundary_companion()
    build_vlm_coordinate_protocol_atlas()
    build_vlm_coordinate_table_companion()
    build_vlm_coordinate_baseline_sanity_companion()
    build_grscenes_vlm_visual_guide()
    build_grscenes_diagnostic_case_atlas()
    build_grscenes_vlm_stress_render_strip()
    build_grscenes_table_companions()
    build_material_atlas()
    build_material_claim_boundary_atlas()
    build_material_decision_map()
    build_first_page_evidence_quickstart()
    build_page4_claim_boundary_companion()
    build_visual_evidence_roadmap()
    build_review_packet_contact_sheet()
    build_source_boundary_companion()


if __name__ == "__main__":
    main()
