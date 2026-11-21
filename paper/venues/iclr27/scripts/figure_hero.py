"""Rebuild the system hero (Figure 1) from the fig1-0922 real-evidence pipeline.

Figure 1 is the three-panel real-evidence hero (Material Intervention /
Paired Visual Grounding / Closed-loop Navigation) built by
`paper/shared/figures/fig1-0922/rebuild/`:
- `build_real_assets.py` fills the 15 photo slots with library evidence
  (paired renders, recorded VLM inputs/predictions, recorded navigation).
- `build_fig.py --assets-dir assets/real` renders PNG/SVG/PPTX from the
  locked layout; the PDF is produced from the PPTX via LibreOffice.

The previous glass hero pipeline (`iclr_system_hero/build_hero.py`) is left
untouched and can still reproduce that figure independently.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'CLAUDE.md').exists())
BUNDLE = ROOT / 'paper/shared/figures/fig1-0922/rebuild'
OUTPUT = Path(__file__).resolve().parents[1] / 'figures'


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _evidence_sources() -> list[Path]:
    """Real source files recorded in assets/real/provenance.json."""
    provenance = json.loads((BUNDLE / 'assets/real/provenance.json').read_text())
    paths = []
    for row in provenance.values():
        src = row.get('source')
        if src:
            paths.append(Path(src))
    return sorted(set(paths))


def source_paths() -> list[Path]:
    """Inputs included in the parent asset build's source-digest manifest."""
    paths = [
        Path(__file__),
        BUNDLE / 'layout.py',
        BUNDLE / 'build_fig.py',
        BUNDLE / 'build_real_assets.py',
        BUNDLE / 'assets/crops.json',
        BUNDLE / 'assets/real/crops.json',
        BUNDLE / 'assets/real/provenance.json',
        ROOT / 'paper/shared/figures/iclr_system_hero/evidence_manifest.json',
        *_evidence_sources(),
    ]
    return sorted(set(paths))


def render_hero(output_dir: Path | None = None) -> list[Path]:
    """Export system_hero.{svg,pptx,pdf,png}; return reproducibility input Paths."""
    output_dir = Path(output_dir) if output_dir is not None else OUTPUT
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. (Re)build the real-evidence slots and verify output digests.
    real_assets = _load('_fig1_real_assets', BUNDLE / 'build_real_assets.py')
    real_assets.build()
    provenance = json.loads((real_assets.OUT / 'provenance.json').read_text())
    for name, row in provenance.items():
        if sha(real_assets.OUT / f'{name}.png') != row['sha256']:
            raise ValueError(f'Real-asset slot digest mismatch: {name}')

    # 2. Render the locked figure from those slots.
    sys.path.insert(0, str(BUNDLE))
    try:
        build_fig = _load('_fig1_build_fig', BUNDLE / 'build_fig.py')
    finally:
        sys.path.remove(str(BUNDLE))
    assets_dir = real_assets.OUT
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        png_tmp, svg_tmp, pptx_tmp = (tmp / f'system_hero.{ext}' for ext in ('png', 'svg', 'pptx'))
        build_fig.render_png(png_tmp, assets_dir)
        build_fig.render_svg(svg_tmp, assets_dir)
        build_fig.render_pptx(pptx_tmp, assets_dir)
        subprocess.run(
            ['soffice', '--headless', '--convert-to', 'pdf', '--outdir', str(tmp), str(pptx_tmp)],
            check=True, capture_output=True, timeout=300,
        )
        stem = output_dir / 'system_hero'
        for ext in ('svg', 'png', 'pptx', 'pdf'):
            shutil.copyfile(tmp / f'system_hero.{ext}', stem.with_suffix(f'.{ext}'))

    # 3. Tie the native parse readout to the recorded prediction evidence.
    evidence = json.loads(
        (ROOT / 'paper/shared/figures/iclr_system_hero/evidence_manifest.json').read_text()
    )
    point = evidence['grounding']['two_view_category_original']['point_pixels']
    layout = _load('_fig1_layout', BUNDLE / 'layout.py')
    code = next(text for key, text, _ink, _color, _bold in layout.TEXTS if key == 'tB_code1')
    if f'[{int(point[0])}, {int(point[1])}]' not in code:
        raise ValueError(f'Native parse readout "{code}" does not match recorded point {point}')
    return source_paths()


if __name__ == '__main__':
    for source in render_hero():
        print(source.relative_to(ROOT))
