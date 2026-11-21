#!/usr/bin/env python3
"""Build REAL replacement raster assets for the fig1-0922 rebuild.

Every photo slot is filled from a repository evidence/library image with a
cover-fit crop into the locked slot box. Overlays (green target box, green
prediction dot, dashed context box, coordinate axes, Start pill, Goal star)
are drawn natively on top of the real pixels at positions derived from the
evidence manifest (recorded Qwen3-VL-2B prediction points and the projected
target bbox) or calibrated off baked trajectory endpoints (navigation maps).

Slots are rendered at 3x supersample and Lanczos-downscaled so overlay edges
are antialiased. Outputs: assets/real/<slot>.png + crops.json (locked paste
boxes, unchanged) + provenance.json (source path, crop rect, overlays, sha256).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]  # repo root
OUT = HERE / "assets" / "real"
SS = 3

GROUND = ROOT / "paper/shared/figures/iclr_system_hero/data/grounding"
NAV = ROOT / "paper/shared/figures/iclr_system_hero/data/navigation"
ZOOM = ROOT / "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADA8_usd/c27086f557d316584264/zoom_018"

# evidence-manifest values (iclr_system_hero/evidence_manifest.json)
BBOX = (230.385, 89.121, 369.378, 372.696)  # target bbox in the 1216x450 image
POINT_ORIG = (304.0, 180.0)   # qwen3vl2b hit on two_view_category_original

GREEN_BOX = "#31EFBA"
GREEN_DOT = "#4EF864"
DASH_ORANGE = "#FF9216"
AXIS_BLUE = "#0066FB"
STAR_YELLOW = "#FFFE03"
NAVY = "#00003A"

FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Bold.ttf"


def cover_crop(img: Image.Image, box_w: int, box_h: int, focus=(0.5, 0.5), zoom=1.0):
    """Crop `img` to the slot aspect around focus, resize to box*SS."""
    W, H = img.size
    aspect = box_w / box_h
    cw = min(W, H * aspect) / zoom
    ch = cw / aspect
    if ch > H / zoom:
        ch = H / zoom
        cw = ch * aspect
    cx, cy = focus[0] * W, focus[1] * H
    x0 = min(max(cx - cw / 2, 0), W - cw)
    y0 = min(max(cy - ch / 2, 0), H - ch)
    rect = (int(x0), int(y0), int(x0 + cw), int(y0 + ch))
    crop = img.crop(rect)
    return crop.resize((box_w * SS, box_h * SS), Image.LANCZOS), rect


def to_slot3(pt, rect, box_w, box_h):
    x0, y0, x1, y1 = rect
    sx, sy = box_w * SS / (x1 - x0), box_h * SS / (y1 - y0)
    return ((pt[0] - x0) * sx, (pt[1] - y0) * sy)


def rect_to_slot3(r, rect, box_w, box_h):
    x0, y0, x1, y1 = rect
    sx, sy = box_w * SS / (x1 - x0), box_h * SS / (y1 - y0)
    return ((r[0] - x0) * sx, (r[1] - y0) * sy, (r[2] - x0) * sx, (r[3] - y0) * sy)


def draw_box(d, rect, color, w=3, dash=None):
    x0, y0, x1, y1 = rect
    w3 = w * SS
    if dash is None:
        d.rectangle([x0, y0, x1, y1], outline=color, width=w3)
        return
    on, off = dash[0] * SS, dash[1] * SS
    period = on + off
    for (ax, ay), (bx, by) in zip(
        [(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
        [(x1, y0), (x1, y1), (x0, y1), (x0, y0)],
    ):
        seg = max(1.0, ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5)
        t = 0.0
        while t < seg:
            t2 = min(t + on, seg)
            if (t % period) < on:
                f1, f2 = t / seg, t2 / seg
                d.line([(ax + (bx - ax) * f1, ay + (by - ay) * f1),
                        (ax + (bx - ax) * f2, ay + (by - ay) * f2)], fill=color, width=w3)
            t = t2


def draw_dot(d, center, r, color=GREEN_DOT):
    cx, cy = center
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)


def draw_axes(d, photo_rect, color=AXIS_BLUE):
    """Blue x/y axes hugging the photo's left/bottom edges (geometry measured
    from the source figure: axis extent abs x792..906, y497..621 around photo
    (800,517,906,605)). All coords 3x."""
    x0, y0, x1, y1 = [v for v in photo_rect]
    lw = 4 * SS
    # y axis: vertical from photo bottom to above photo top
    d.line([(x0 - 5 * SS, y1 + 3 * SS), (x0 - 5 * SS, y0 - 18 * SS)], fill=color, width=lw)
    d.polygon([(x0 - 10 * SS, y0 - 12 * SS), (x0, y0 - 12 * SS), (x0 - 5 * SS, y0 - 22 * SS)], fill=color)
    # x axis: horizontal from photo left to just past photo right
    d.line([(x0 - 5 * SS, y1 + 5 * SS), (x1 + 7 * SS, y1 + 5 * SS)], fill=color, width=lw)
    d.polygon([(x1 + 1 * SS, y1), (x1 + 1 * SS, y1 + 10 * SS), (x1 + 11 * SS, y1 + 5 * SS)], fill=color)
    f = ImageFont.truetype(FONT_BOLD, 17 * SS)
    d.text((x0 - 1 * SS, y0 - 20 * SS), "y", font=f, fill=color)
    d.text((x1 + 2 * SS, y1 + 8 * SS), "x", font=f, fill=color)


def draw_start_goal(img3: Image.Image, start_xy, goal_xy):
    """Start pill (white rounded pill + navy ring + 'Start') and Goal (yellow
    star + navy 'Goal'). Coordinates in 1x slot pixels; img3 is 3x."""
    d = ImageDraw.Draw(img3)
    sx, sy = start_xy[0] * SS, start_xy[1] * SS
    pw, ph = 64 * SS, 26 * SS
    d.rounded_rectangle([sx - 2 * SS, sy - ph // 2, sx + pw, sy + ph // 2 + 2 * SS],
                        radius=ph // 2, fill="white", outline="#D8D8D8", width=SS)
    d.ellipse([sx + 4 * SS, sy - 8 * SS, sx + 20 * SS, sy + 8 * SS], outline=NAVY, width=4 * SS)
    f = ImageFont.truetype(FONT_BOLD, 17 * SS)
    d.text((sx + 26 * SS, sy - 9 * SS), "Start", font=f, fill=NAVY)
    gx, gy = goal_xy[0] * SS, goal_xy[1] * SS
    r_out, r_in = 12 * SS, 5 * SS
    pts = []
    for i in range(10):
        ang = -np.pi / 2 + i * np.pi / 5
        r = r_out if i % 2 == 0 else r_in
        pts.append((gx + r * np.cos(ang), gy + r * np.sin(ang)))
    d.polygon(pts, fill=STAR_YELLOW, outline="black")
    if goal_xy[0] > img3.width / SS - 70:
        d.text((gx - 52 * SS, gy - 9 * SS), "Goal", font=f, fill=NAVY)
    else:
        d.text((gx + 15 * SS, gy - 9 * SS), "Goal", font=f, fill=NAVY)
    return img3


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    meta = json.loads((HERE / "assets" / "crops.json").read_text())
    prov: dict[str, dict] = {}

    def save(name, img3, box, record):
        img = img3.resize(((box[2] - box[0]), (box[3] - box[1])), Image.LANCZOS)
        img.convert("RGB").save(OUT / f"{name}.png")
        meta[name] = {"box": box, "size": [box[2] - box[0], box[3] - box[1]]}
        record["sha256"] = sha256(OUT / f"{name}.png")
        prov[name] = record

    # ---- panel A: paired zoom_018 single views (600x450)
    for name, rel, box, focus in [
        ("A_orig_photo", "original/original_0000.png", [25, 203, 237, 487], (0.48, 0.50)),
        ("A_conv_photo", "converted/converted_0000.png", [272, 203, 476, 487], (0.48, 0.50)),
    ]:
        img = Image.open(ZOOM / rel)
        w, h = box[2] - box[0], box[3] - box[1]
        crop, rect = cover_crop(img, w, h, focus)
        save(name, crop, box, {"source": str(img.filename), "crop_rect": rect,
                               "fit": "cover", "focus": focus})

    # ---- panel B grounding row (two_view 1216x450; shelf view = left half)
    tv_orig = Image.open(GROUND / "two_view_category_original.png")
    tv_conv = Image.open(GROUND / "two_view_category_converted.png")

    # thumb_orig: shelf view + green target box
    box = [683, 189, 795, 306]
    w, h = box[2] - box[0], box[3] - box[1]
    crop, rect = cover_crop(tv_orig, w, h, focus=(0.247, 0.513), zoom=1.45)
    d = ImageDraw.Draw(crop)
    draw_box(d, rect_to_slot3(BBOX, rect, w, h), GREEN_BOX, 3)
    save("B_thumb_orig", crop, box, {"source": str(tv_orig.filename), "crop_rect": rect,
                                     "overlays": [{"type": "bbox", "value": BBOX, "color": GREEN_BOX}]})

    # thumb_swap: REAL side1 recording (clock view left, shelf view right —
    # target bottle in the right view). Explicit crop spanning the seam.
    SIDE1 = ROOT / "paper/shared/evidence/raw/iclr_model_behavior/interventions_clean_v2/images/board02.q0.side1.two_view_category.original.png"
    BBOX_SIDE1 = (885, 85, 955, 350)  # bottle bbox measured on the side1 image
    box = [806, 189, 919, 306]
    w, h = box[2] - box[0], box[3] - box[1]
    side1 = Image.open(SIDE1)
    rect = (615, 15, 965, 385)  # shelf view from side1; bottle right-of-center
    crop = side1.crop(rect).resize((w * SS, h * SS), Image.LANCZOS)
    d = ImageDraw.Draw(crop)
    draw_box(d, rect_to_slot3(BBOX_SIDE1, rect, w, h), GREEN_BOX, 3)
    save("B_thumb_swap", crop, box, {"source": str(SIDE1),
                                     "sample_id": "board02.q0.side1.two_view_category.original",
                                     "crop_rect": rect,
                                     "overlays": [{"type": "bbox", "value": BBOX_SIDE1,
                                                   "color": GREEN_BOX,
                                                   "note": "bottle bbox measured on side1 image"}]})

    # thumb_pred: shelf view + green dot at the recorded hit point
    box = [1045, 190, 1158, 306]
    w, h = box[2] - box[0], box[3] - box[1]
    crop, rect = cover_crop(tv_orig, w, h, focus=(0.247, 0.51), zoom=1.55)
    d = ImageDraw.Draw(crop)
    draw_dot(d, to_slot3(POINT_ORIG, rect, w, h), 7 * SS)
    save("B_thumb_pred", crop, box, {"source": str(tv_orig.filename), "crop_rect": rect,
                                     "overlays": [{"type": "point", "value": POINT_ORIG,
                                                   "color": GREEN_DOT, "hit": True}]})

    # ---- align composite: photo + axes + dot (composite box includes axes)
    box = [793, 496, 912, 622]
    W, H = (box[2] - box[0]) * SS, (box[3] - box[1]) * SS
    canvas = Image.new("RGB", (W, H), "white")
    photo_box = tuple((v - o) * SS for v, o in
                      zip((800, 517, 906, 605), (box[0], box[1], box[0], box[1])))
    pw, ph = photo_box[2] - photo_box[0], photo_box[3] - photo_box[1]
    crop, rect = cover_crop(tv_orig, pw // SS, ph // SS, focus=(0.247, 0.48), zoom=2.0)
    canvas.paste(crop, photo_box[:2])
    d = ImageDraw.Draw(canvas)
    draw_dot(d, tuple(a + b for a, b in
                      zip(photo_box[:2], to_slot3(POINT_ORIG, rect, pw // SS, ph // SS))), 6 * SS)
    draw_axes(d, photo_box)
    save("B_align_composite", canvas, box, {"source": str(tv_orig.filename), "crop_rect": rect,
                                            "overlays": [{"type": "point", "value": POINT_ORIG},
                                                         {"type": "axes", "color": AXIS_BLUE}]})

    # ---- score photo: shelf crop + green box + dot (recorded hit)
    box = [981, 509, 1087, 611]
    w, h = box[2] - box[0], box[3] - box[1]
    crop, rect = cover_crop(tv_orig, w, h, focus=(0.247, 0.513), zoom=1.5)
    d = ImageDraw.Draw(crop)
    draw_box(d, rect_to_slot3(BBOX, rect, w, h), GREEN_BOX, 3)
    draw_dot(d, to_slot3(POINT_ORIG, rect, w, h), 7 * SS)
    save("B_score_photo", crop, box, {"source": str(tv_orig.filename), "crop_rect": rect,
                                      "overlays": [{"type": "bbox", "value": BBOX},
                                                   {"type": "point", "value": POINT_ORIG}]})

    # ---- probes row
    probe_specs = [
        ("B_probe1", [516, 731, 668, 867], tv_orig, None),
        ("B_probe2", [680, 731, 829, 867], Image.open(GROUND / "target_window_converted.png"),
         {"color": GREEN_BOX, "dash": None}),
        ("B_probe3", [841, 731, 991, 867], Image.open(GROUND / "context_window_converted.png"),
         {"color": DASH_ORANGE, "dash": (8, 6)}),
        ("B_probe4", [1003, 731, 1152, 867], tv_conv, None),
    ]
    for name, box, img, overlay in probe_specs:
        w, h = box[2] - box[0], box[3] - box[1]
        crop, rect = cover_crop(img, w, h, focus=(0.247, 0.50), zoom=1.4)
        rec = {"source": str(img.filename), "crop_rect": rect}
        if overlay:
            d = ImageDraw.Draw(crop)
            draw_box(d, rect_to_slot3(BBOX, rect, w, h), overlay["color"], 3, overlay["dash"])
            rec["overlays"] = [{"type": "bbox", "value": BBOX, **overlay}]
        save(name, crop, box, rec)

    # ---- panel C end views (left half of end composite, cover-fit wide slot)
    for name, path, box in [
        ("C_end_orig", NAV / "original_end_composite.png", [1203, 236, 1404, 377]),
        ("C_end_conv", NAV / "nomdl_end_composite.png", [1435, 236, 1640, 377]),
    ]:
        img = Image.open(path).crop((0, 0, 512, 512))
        w, h = box[2] - box[0], box[3] - box[1]
        crop, rect = cover_crop(img, w, h, focus=(0.5, 0.42))
        save(name, crop, box, {"source": str(path), "crop_rect": rect, "fit": "cover"})

    # ---- panel C maps (trajectories baked) + Start pill / Goal star
    # Start = bottom-most green-path centroid; Goal = right/top green terminus.
    def green_endpoints(img):
        a = np.asarray(img.convert("RGB")).astype(int)
        R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
        g = (G > 120) & (R < 120) & (B < 140) & (G > R + 50)
        ys, xs = np.where(g)
        bot = ys > ys.max() - 30
        start = (float(xs[bot].mean()), float(ys[bot].mean()))
        # goal: the green terminus nearest the top-right area
        cand = (ys < ys.min() + 40) | (xs > xs.max() - 20)
        goal = (float(xs[cand].mean()), float(ys[cand].mean()))
        return start, goal

    for name, path, box, focus, zoom in [
        ("C_map_orig", NAV / "original_map.png", [1205, 419, 1403, 614], (0.60, 0.72), 1.2),
        ("C_map_conv", NAV / "nomdl_map.png", [1435, 419, 1639, 614], (0.50, 0.35), 1.3),
    ]:
        img = Image.open(path)
        w, h = box[2] - box[0], box[3] - box[1]
        crop, rect = cover_crop(img, w, h, focus=focus, zoom=zoom)
        start_src, goal_src = green_endpoints(img)
        start_xy = tuple(v / SS for v in to_slot3(start_src, rect, w, h))
        goal_xy = tuple(v / SS for v in to_slot3(goal_src, rect, w, h))
        # keep markers inside the slot
        goal_xy = (min(goal_xy[0], w - 30), max(goal_xy[1], 16))
        start_xy = (max(start_xy[0], 2), min(start_xy[1], h - 16))
        crop = draw_start_goal(crop, start_xy, goal_xy)
        save(name, crop, box, {"source": str(path), "crop_rect": rect,
                               "overlays": [{"type": "start_pill", "at": start_xy,
                                             "source_xy": start_src},
                                            {"type": "goal_star", "at": goal_xy,
                                             "source_xy": goal_src}],
                               "note": "trajectories baked by habitat TopDownMap; "
                                       "start/goal markers at green path endpoints"})

    (OUT / "crops.json").write_text(json.dumps(meta, indent=1))
    (OUT / "provenance.json").write_text(json.dumps(prov, indent=1))
    print(f"wrote {len(prov)} real assets to {OUT}")


if __name__ == "__main__":
    build()
