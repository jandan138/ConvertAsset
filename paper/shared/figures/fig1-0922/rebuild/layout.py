# Locked layout for fig1-0922 exact reconstruction (1672x941).
# All boxes are [x0, y0, x1, y1] in source pixels (x1/y1 exclusive).
# Every measurement was taken from the native-resolution source PNG.

CANVAS = (1672, 941)
CANVAS_COLOR = "#FEFEFE"

# palette (mode-sampled from source)
NAVY = "#000039"
SUB = "#4E6A96"
BLUE = "#0054FD"
ORANGE = "#FD6500"
TEAL = "#006E68"
PANEL_BORDER = "#E7F2FE"
CARD_BLUE_BORDER = "#CAE2FD"
CARD_ORANGE_BORDER = "#FCEEDA"
BAND_BLUE = "#EDF6FE"
BAND_ORANGE = "#FEF8F2"
CHIP_A_FILL = "#EFF6FE"
CHIP_A_BORDER = "#E4F0FC"
INFO_BORDER = "#D9EFFC"
READOUT_FILL = "#F4FAFE"
READOUT_BORDER = "#E5EEFD"
PROBES_FILL = "#FDFEFE"
PROBES_BORDER = "#DCEEFD"
LEGEND_RED = "#E90000"
LEGEND_GREEN = "#0FB44C"

# rounded rectangle frames: (box, radius, fill, border, border_width)
FRAMES = [
    # three main panels
    ([10, 46, 490, 895], 12, "#FBFDFE", PANEL_BORDER, 1.5),
    ([499, 46, 1173, 895], 12, "#F9FCFE", PANEL_BORDER, 1.5),
    ([1181, 46, 1662, 895], 12, "#F8FBFE", PANEL_BORDER, 1.5),
    # panel A photo cards (bodies mostly hidden behind photo rasters)
    ([25, 153, 237, 487], 10, "#FFFFFF", CARD_BLUE_BORDER, 1.5),
    ([263, 153, 475, 487], 10, "#FFFFFF", CARD_ORANGE_BORDER, 1.5),
    # panel A pipeline chips
    ([27, 507, 143, 622], 8, CHIP_A_FILL, CHIP_A_BORDER, 1.0),
    ([172, 507, 313, 622], 8, CHIP_A_FILL, CHIP_A_BORDER, 1.0),
    ([337, 507, 473, 622], 8, CHIP_A_FILL, CHIP_A_BORDER, 1.0),
    # panel A info cards
    ([25, 649, 238, 745], 8, "#FFFFFF", INFO_BORDER, 1.0),
    ([247, 649, 471, 745], 8, "#FFFFFF", INFO_BORDER, 1.0),
    ([25, 755, 238, 858], 8, "#FFFFFF", INFO_BORDER, 1.0),
    ([247, 755, 471, 858], 8, "#FFFFFF", INFO_BORDER, 1.0),
    # panel B readout band + step cards
    ([513, 372, 1158, 629], 10, READOUT_FILL, READOUT_BORDER, 1.5),
    ([527, 422, 708, 618], 8, "#FFFFFF", "#EDF3FB", 1.0),
    ([722, 422, 931, 618], 8, "#FFFFFF", "#EDF3FB", 1.0),
    ([947, 422, 1156, 618], 8, "#FFFFFF", "#EDF3FB", 1.0),
    # panel B probes band
    ([513, 639, 1158, 884], 10, PROBES_FILL, PROBES_BORDER, 1.5),
    # panel C cards
    ([1195, 153, 1413, 690], 10, "#FFFFFF", "#CDE4FD", 1.5),
    ([1434, 153, 1649, 690], 10, "#FFFFFF", "#FDE7CD", 1.5),
    # parse-step code block background (native; text carries the real
    # recorded prediction point [304, 180])
    ([528, 498, 710, 597], 8, "#F6F6F8", "#E8ECF2", 1.0),
    # panel C bottom chips
    ([1189, 714, 1339, 857], 8, "#FFFFFF", "#EDF4FA", 1.0),
    ([1351, 714, 1482, 857], 8, "#FFFFFF", "#EDF4FA", 1.0),
    ([1494, 714, 1644, 857], 8, "#FFFFFF", "#EDF4FA", 1.0),
]

# header bands: (box, radius_top, fill) — bottom corners square
BANDS = [
    ([27, 155, 235, 205], 8, BAND_BLUE),     # A original
    ([265, 155, 473, 205], 8, BAND_ORANGE),  # A converted
    ([1197, 155, 1411, 206], 8, BAND_BLUE),  # C original
    ([1436, 155, 1647, 206], 8, BAND_ORANGE),# C converted
]

# solid rects (legend swatches)
RECTS = [
    ([1206, 637, 1239, 641], LEGEND_RED),
    ([1206, 664, 1239, 668], LEGEND_GREEN),
    ([1436, 637, 1469, 641], LEGEND_RED),
    ([1436, 664, 1469, 668], LEGEND_GREEN),
]

# native text: (key, text, ink_box, color, bold)
TEXTS = [
    ("tA_title", "Material Intervention", [104, 70, 433, 96], NAVY, True),
    ("tA_sub", "Same geometry · same camera", [102, 112, 413, 131], SUB, False),
    ("tB_title", "Paired Visual Grounding", [603, 69, 974, 103], NAVY, True),
    ("tB_sub", "Query × position × material × image region", [601, 103, 1068, 132], SUB, False),
    ("tC_title", "Closed-loop Navigation", [1276, 70, 1617, 103], NAVY, True),
    ("tC_sub", "Same instruction · same start · different observations", [1276, 103, 1647, 127], SUB, False),
    ("tA_lbl_orig", "Original", [88, 168, 174, 193], BLUE, True),
    ("tA_lbl_conv", "Converted", [318, 169, 429, 188], ORANGE, True),
    ("tA_chip1", "USD / MDL", [49, 566, 123, 581], NAVY, False),
    ("tA_chip1s", "(scene assets)", [40, 589, 130, 604], SUB, False),
    ("tA_chip2", "ConvertAsset", [197, 566, 291, 578], NAVY, False),
    ("tA_chip2s", "(material conversion)", [178, 589, 310, 604], SUB, False),
    ("tA_chip3", "UsdPreviewSurface", [348, 566, 471, 578], NAVY, False),
    ("tA_chip3s", "(rendering)", [376, 588, 444, 604], SUB, False),
    ("tA_geo1", "Geometry", [122, 676, 198, 694], NAVY, False),
    ("tA_geo2", "retained", [123, 701, 184, 716], NAVY, False),
    ("tA_tr1", "Transforms", [350, 675, 435, 690], NAVY, False),
    ("tA_tr2", "retained", [352, 701, 413, 716], NAVY, False),
    ("tA_cam1", "Camera", [122, 787, 181, 801], NAVY, False),
    ("tA_cam2", "matched", [123, 812, 189, 827], NAVY, False),
    ("tA_app1", "Appearance", [351, 787, 445, 802], NAVY, False),
    ("tA_app2", "changed", [351, 804, 416, 831], NAVY, False),
    ("tB_lbl_orig", "Original", [704, 162, 771, 182], BLUE, True),
    ("tB_lbl_swap", "Swapped", [825, 163, 901, 182], ORANGE, True),
    ("tB_cap1", "Bottle on left", [691, 314, 782, 328], NAVY, False),
    ("tB_cap1b", "(target)", [711, 337, 764, 354], NAVY, False),
    ("tB_cap2", "Bottle on right", [816, 314, 918, 331], NAVY, False),
    ("tB_cap2b", "(target)", [838, 337, 890, 354], NAVY, False),
    ("tB_cap3", "Point prediction", [1041, 314, 1153, 331], NAVY, False),
    ("tB_readout", "Model readout and evaluation", [564, 388, 869, 405], NAVY, True),
    ("tB_s1", "Parse", [589, 442, 638, 457], NAVY, True),
    ("tB_s1s", "response", [588, 474, 651, 487], SUB, False),
    ("tB_code1", "<point>  [304, 180]", [536, 521, 699, 540], "#143271", False),
    ("tB_code2", "</point>", [536, 549, 608, 565], "#143271", False),
    ("tB_code3", "....", [536, 577, 556, 588], "#143271", False),
    ("tB_s2", "Align", [803, 441, 849, 462], NAVY, True),
    ("tB_s2s", "coordinate frame", [804, 462, 926, 483], SUB, False),
    ("tB_s3", "Score", [1023, 442, 1074, 458], NAVY, True),
    ("tB_s3s", "point-in-target", [1023, 470, 1124, 487], SUB, False),
    ("tB_probes", "Region probes", [560, 667, 702, 689], NAVY, True),
    ("tB_p1", "Original", [562, 705, 624, 723], BLUE, False),
    ("tB_p2", "Target window", [699, 705, 811, 723], TEAL, False),
    ("tB_p3", "Context window", [852, 705, 973, 719], ORANGE, False),
    ("tB_p4", "Full conversion", [1017, 705, 1130, 719], ORANGE, False),
    ("tC_lbl_orig", "Original", [1260, 171, 1345, 193], BLUE, True),
    ("tC_lbl_conv", "Converted", [1482, 172, 1589, 190], ORANGE, True),
    ("tC_end1", "End view", [1206, 211, 1272, 225], SUB, False),
    ("tC_end2", "End view", [1438, 211, 1504, 225], SUB, False),
    ("tC_mapl1", "Top-down map excerpt", [1206, 392, 1337, 408], NAVY, False),
    ("tC_mapl2", "Top-down map excerpt", [1440, 392, 1578, 407], NAVY, False),
    ("tC_leg1r", "Executed trajectory", [1250, 631, 1381, 647], NAVY, False),
    ("tC_leg1g", "Reference trajectory", [1250, 657, 1385, 674], NAVY, False),
    ("tC_leg2r", "Executed trajectory", [1481, 631, 1614, 647], NAVY, False),
    ("tC_leg2g", "Reference trajectory", [1481, 657, 1619, 674], NAVY, False),
    ("tC_c1a", "Same", [1255, 739, 1291, 751], NAVY, False),
    ("tC_c1b", "instruction", [1255, 760, 1323, 773], NAVY, False),
    ("tC_c1q", "“Locate the bottle”", [1202, 806, 1327, 819], SUB, False),
    ("tC_c2a", "Same", [1403, 739, 1439, 751], NAVY, False),
    ("tC_c2b", "start", [1403, 762, 1433, 773], NAVY, False),
    ("tC_c2d1", "Identical pose", [1361, 797, 1458, 815], SUB, False),
    ("tC_c2d2", "and episode ID", [1356, 822, 1462, 839], SUB, False),
    ("tC_c3a", "Paired", [1545, 738, 1586, 751], NAVY, False),
    ("tC_c3b", "episode outcome", [1544, 761, 1641, 776], NAVY, False),
    ("tC_c3d1", "Same task,", [1528, 797, 1606, 821], SUB, False),
    ("tC_c3d2", "different result", [1511, 821, 1619, 836], SUB, False),
]

# paste order for raster slots (after native layer). Photos last among overlaps.
IMAGE_ORDER = [
    "icon_cube", "icon_crosshair", "icon_barchart",
    "icon_doc", "icon_gear", "icon_molecule",
    "icon_layers", "icon_axes", "icon_camera", "icon_palette",
    "icon_region_readout", "icon_region_probes",
    "icon_speech", "icon_pin", "icon_share",
    "arrow_A_photos", "arrow_A_pipe1", "arrow_A_pipe2",
    "arrow_B_g1", "arrow_B_g2", "arrow_B_g3", "arrow_B_r1", "arrow_B_r2",
    "bubble", "vlm_chip",
    "check_badge", "cross_badge", "circle1", "circle2", "circle3",
    "cap3b_baked",
    "A_orig_photo", "A_conv_photo",
    "B_thumb_orig", "B_thumb_swap", "B_thumb_pred",
    "B_align_composite", "B_score_photo",
    "B_probe1", "B_probe2", "B_probe3", "B_probe4",
    "C_end_orig", "C_end_conv", "C_map_orig", "C_map_conv",
]
