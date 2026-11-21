"""Task09 r4 near-full bottle: unchanged compact shell, shoulder-fitted high tray.

Ordinary Python (stdlib): --out DIR [--insert-top .084] writes geometry.json.
Blender: -b -t 8 --python-exit-code 1 --python this_file.py -- --out DIR --render
Copy this file AND model_compact_powder_bottle.py into source_scripts for replay.
All lengths are metres. Powder heights are integration targets, not settled evidence.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sys


# 正常模块导入，同时兼容 pytest/importlib、Blender 和独立 source_scripts。
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import model_compact_powder_bottle as compact  # noqa: E402


INSERT_TOP = .084


def _clip(mesh, height, keep_above):
    """Clip an outward closed mesh to a horizontal halfspace and cap its cut.

    The sections used here are convex, so polar ordering gives the boundary.
    Retain triangle-diagonal intersections: dropping them would change the
    authored shoulder surface or leave T-junctions along the cap.
    """
    points, faces, indices = [], [], {}

    def vertex(point):
        key = tuple(round(v, 14) for v in point)
        if key not in indices:
            indices[key] = len(points)
            points.append(key)
        return indices[key]

    for face in mesh['faces']:
        polygon = [mesh['points'][i] for i in face]
        cut = []
        for a, b in zip(polygon, polygon[1:] + polygon[:1]):
            a_in = a[2] >= height - 1e-13 if keep_above else a[2] <= height + 1e-13
            b_in = b[2] >= height - 1e-13 if keep_above else b[2] <= height + 1e-13
            if a_in:
                cut.append(a)
            if a_in != b_in:
                t = (height - a[2]) / (b[2] - a[2])
                cut.append((a[0] + t * (b[0] - a[0]),
                            a[1] + t * (b[1] - a[1]), height))
        ids = list(dict.fromkeys(vertex(p) for p in cut))
        if len(ids) >= 3:
            faces.append(ids)
    edges = Counter(tuple(sorted((a, b))) for f in faces
                    for a, b in zip(f, f[1:] + f[:1]))
    boundary = {i for edge, count in edges.items() if count == 1 for i in edge}
    if boundary:
        cx = sum(points[i][0] for i in boundary) / len(boundary)
        cy = sum(points[i][1] for i in boundary) / len(boundary)
        cap = sorted(boundary, key=lambda i: math.atan2(points[i][1] - cy, points[i][0] - cx),
                     reverse=keep_above)
        faces.append(cap)
    used = sorted({i for f in faces for i in f})
    remap = {old: new for new, old in enumerate(used)}
    return dict(name=mesh['name'], points=[points[i] for i in used],
                faces=[[remap[i] for i in f] for f in faces])


def _slice(mesh, bottom, top):
    return _clip(_clip(mesh, bottom, True), top, False)


def _overlap(point):
    x, y, z = point
    radius = math.hypot(x, y)
    scale = 1 + compact.INSERT_OVERLAP / radius if radius else 1
    return (x * scale, y * scale, z)


def _tray_colliders(inner, bottom, top):
    """Convex radial sectors fit the existing wall-LOD rings, with sealed seams.

    Hull each six-point sector BEFORE clipping. This contains both possible
    diagonals of the nonplanar inner quad and meets the unmodified wall hull.
    Shared radial faces meet exactly; the outer ring has 0.15 mm radial overlap.
    """
    profile = [row for row in inner if row[0] in compact.COLLISION_HEIGHTS]
    pieces = []
    for layer, (low, high) in enumerate(zip(profile, profile[1:])):
        if high[0] <= bottom + 1e-13 or low[0] >= top - 1e-13:
            continue
        rings = [[_overlap(p) for p in compact._ring(*row, compact.SEGMENTS)]
                 for row in [low, high]]
        for i in range(compact.SEGMENTS):
            j = (i + 1) % compact.SEGMENTS
            points = [(0., 0., low[0]), (0., 0., high[0])]
            points += [ring[k] for ring in rings for k in [i, j]]
            hull = compact._wall_hull(f'Insert_{layer:02d}_{i:02d}', points)
            pieces.append(_slice(hull, bottom, top))
    return pieces


def build_geometry(insert_top=.084):
    """Return r3-compatible SI geometry with a 2 mm tray at 83–85 mm (84 default).

    Mass integrates the unchanged shell plus the EXACT clipped triangulated
    visual cavity; the 0.15 mm seam is excluded. Collision sector convex hulls
    are geometric approximations and are not used for mass. No SDK is imported.
    """
    if not math.isfinite(insert_top) or not .083 <= insert_top <= .085:
        raise ValueError('insert_top must be finite and within .083..085 metres')
    bottom = insert_top - compact.INSERT_THICKNESS
    data = compact.build_geometry()
    _, inner = compact._profiles()
    cavity = compact._loft('EffectiveInsert', inner, compact.VISUAL_SEGMENTS)
    effective = _slice(cavity, bottom, insert_top)
    insert = dict(name='FalseBottom', points=[_overlap(p) for p in effective['points']],
                  faces=effective['faces'], material='insert')
    data['visual_meshes'][1] = insert
    data['colliders'] = [p for p in data['colliders'] if p['name'] != 'Insert']
    trays = _tray_colliders(inner, bottom, insert_top)
    data['colliders'].extend(trays)
    moments = [compact._moments(p) for p in [data['visual_meshes'][0], effective]]
    volume = sum(m[0] for m in moments)
    first = [sum(m[1][k] for m in moments) for k in range(3)]
    second = [sum(m[2][k] for m in moments) for k in range(3)]
    com = [v / volume for v in first]
    mass = compact.DENSITY * volume
    inertia = [compact.DENSITY * sum(second[j] for j in range(3) if j != k)
               - mass * sum(com[j]**2 for j in range(3) if j != k) for k in range(3)]
    data.update(producer='ConvertAsset task09 r4 near-full powder bottle model_r1',
                volume_m3=volume, mass_kg=mass, center_of_mass_m=com,
                diagonal_inertia_kg_m2=inertia)
    data['metadata'].update(
        insert_top_m=insert_top, insert_bottom_m=bottom,
        suggested_powder_surface_m=insert_top + .011, suggested_powder_depth_m=.011,
        target_headspace_m=.1 - insert_top - .011,
        powder_surface_semantics='target actual settled powder surface; no particles authored or measured here',
        insert_fit_method='visual: clipped triangulated inner loft + radial 0.15 mm seam; collision: clipped convex sectors of unchanged wall LOD inner rings + radial 0.15 mm seam',
        insert_collider_count=len(trays), collider_count=len(data['colliders']),
        insert_effective_volume_m3=moments[1][0],
        mass_method='signed tetrahedral integration: unchanged shell plus exact triangulated visual cavity clipped at tray bottom/top; seam excluded, no double count (exact authored solid union to floating-point clipping tolerance)',
        collision_mass_semantics='convex LOD sectors approximate contact only; mass is not integrated from colliders',
        validation_scope='static geometry and Blender CPU previews; no runtime or particle qualification',
    )
    return data


def _create_blender(data, out, render, samples):
    # 复用实际新几何切面和 CPU 渲染；旧 helper 唯一读取旧 INSERT_TOP 的属性在此修正。
    compact._create_blender(data, out, render, samples)
    import bpy

    root = bpy.data.objects['Bottle']
    root['insert_top_m'] = data['metadata']['insert_top_m']
    root['suggested_powder_surface_m'] = data['metadata']['suggested_powder_surface_m']
    root['center_of_mass_m'] = data['center_of_mass_m']
    root['diagonal_inertia_kg_m2'] = data['diagonal_inertia_kg_m2']
    bpy.ops.wm.save_as_mainfile(filepath=str(out / 'bottle.blend'))


def main(argv=None):
    """Write JSON in ordinary Python; additionally save/render when in Blender."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--insert-top', type=float, default=INSERT_TOP)
    parser.add_argument('--render', action='store_true')
    parser.add_argument('--samples', type=int, default=40)
    parser.add_argument('--json-only', action='store_true')
    args = parser.parse_args(argv)
    if args.samples < 1:
        parser.error('--samples must be positive')
    try:
        data = build_geometry(args.insert_top)
    except ValueError as exc:
        parser.error(str(exc))
    in_blender = 'bpy' in sys.modules
    if args.render and (args.json_only or not in_blender):
        parser.error('--render requires Blender and cannot be used with --json-only')
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / 'geometry.json').write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')
    if in_blender and not args.json_only:
        _create_blender(data, out, args.render, args.samples)
    print(json.dumps(dict(out=str(out), mass_kg=data['mass_kg'], volume_m3=data['volume_m3'],
                         center_of_mass_m=data['center_of_mass_m'],
                         diagonal_inertia_kg_m2=data['diagonal_inertia_kg_m2'],
                         insert_top_m=args.insert_top, colliders=len(data['colliders'])), indent=2))


if __name__ == '__main__':
    main(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
