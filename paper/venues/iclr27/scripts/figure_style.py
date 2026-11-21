"""Reproducible, image-led ICLR figures from the registered experiment outputs.

All scene pixels and predicted coordinates come from saved records. Matplotlib
owns typography, connectors, and PDF/SVG/PNG export; source images stay read-only.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, FancyArrowPatch
from matplotlib.path import Path as MplPath
from matplotlib.text import Text
from matplotlib import font_manager
import numpy as np
from PIL import Image

VENUE = Path(__file__).resolve().parents[1]
ROOT = VENUE.parents[2]
RAW = ROOT / 'paper/shared/evidence/raw'
MODEL_ORDER = ['Gemma4-E4B', 'Qwen2.5-VL-7B', 'Qwen3-VL-2B', 'Qwen3-VL-8B', 'InternVL3-8B', 'Molmo-7B-D']
SHORT = ['Gemma4', 'Qwen2.5', 'Qwen3-2B', 'Qwen3-8B', 'InternVL3', 'Molmo']
O, C = '#0F4D92', '#E67E22'
INK, MUTED, LINE = '#202A38', '#647184', '#D7DEE7'
GAIN, LOSS = '#168A65', '#A35B78'
SOURCES: set[Path] = set()
QA = {}
OUTPUT_DIR = VENUE / "figures"
CROP_RECORDS = []


def read_json(path):
    path = Path(path)
    SOURCES.add(path)
    return json.loads(path.read_text())


def read_image(path):
    path = Path(path)
    SOURCES.add(path)
    with Image.open(path) as im:
        return np.asarray(im.convert('RGB'))


def style():
    for font in Path('/usr/share/fonts/truetype/liberation').glob('LiberationSans-*.ttf'):
        font_manager.fontManager.addfont(str(font))
    plt.rcParams.update({'font.family': ['Liberation Sans', 'DejaVu Sans'], 'font.sans-serif': ['Liberation Sans', 'DejaVu Sans'],
        'font.size': 8, 'text.color': INK, 'axes.labelcolor': INK, 'xtick.color': MUTED,
        'ytick.color': INK, 'axes.edgecolor': LINE, 'axes.linewidth': .6,
        'axes.spines.top': False, 'axes.spines.right': False, 'axes.spines.left': False,
        'axes.spines.bottom': False, 'xtick.major.size': 0, 'ytick.major.size': 0,
        'legend.frameon': False, 'pdf.fonttype': 42, 'svg.fonttype': 'none',
        'svg.hashsalt': 'iclr27-quality-v2', 'savefig.facecolor': 'white'})


def text(fig, x, y, s, size=8, color=INK, weight='normal', ha='left', **kw):
    """Inch coordinates from the top-left corner; makes shared baselines explicit."""
    w, h = fig.get_size_inches()
    return fig.text(x/w, 1-y/h, s, fontsize=size, color=color, weight=weight,
                    ha=ha, va='top', **kw)


def axes_at(fig, x, y, w, h):
    fw, fh = fig.get_size_inches()
    return fig.add_axes([x/fw, 1-(y+h)/fh, w/fw, h/fh])


def picture(fig, path, box, border=None, crop=None):
    data = read_image(path)
    if crop is not None:
        x0,y0,x1,y1=map(int,crop)
        if not (0<=x0<x1<=data.shape[1] and 0<=y0<y1<=data.shape[0]):
            raise ValueError(f"Crop outside source image: {crop}")
        CROP_RECORDS.append({'source':str(Path(path).relative_to(ROOT)), 'crop_xyxy':[x0,y0,x1,y1], 'purpose':'explicit detail or semantic panel extraction'})
        data=data[y0:y1,x0:x1]
    x, y, w, h = box
    # Fit to the slot without trimming source pixels or distorting aspect ratio.
    ratio = min(w/data.shape[1], h/data.shape[0])
    iw, ih = data.shape[1]*ratio, data.shape[0]*ratio
    ax = axes_at(fig, x+(w-iw)/2, y+(h-ih)/2, iw, ih)
    ax.imshow(data, interpolation='none')
    ax.set_xlim(-.5, data.shape[1]-.5)
    ax.set_ylim(data.shape[0]-.5, -.5)
    ax.set_axis_off()
    if border:
        ax.add_patch(Rectangle((0, 0), 1, 1, transform=ax.transAxes,
                              fill=False, edgecolor=border, lw=.8, clip_on=False))
    return ax


def rule(fig, x0, x1, y, color=LINE, lw=.6):
    w,h=fig.get_size_inches()
    fig.add_artist(Line2D([x0/w,x1/w], [1-y/h]*2, transform=fig.transFigure, color=color, lw=lw))


def save(fig, name):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    outside = []
    labels = []
    bounds = fig.bbox
    for artist in fig.findobj(Text):
        if not artist.get_visible() or not artist.get_text().strip():
            continue
        # Unused axis labels/ticks on image axes are not drawn by Matplotlib.
        ax = artist.axes
        if ax is not None and not ax.axison:
            continue
        box = artist.get_window_extent(renderer)
        if box.width == 0 or box.height == 0:
            continue
        if box.x0 < bounds.x0-1 or box.y0 < bounds.y0-1 or box.x1 > bounds.x1+1 or box.y1 > bounds.y1+1:
            outside.append(artist.get_text())
        labels.append({'text': artist.get_text(), 'font_pt': artist.get_fontsize()})
    data_outside = []
    for ai, ax in enumerate(fig.axes):
        for line in ax.lines:
            if line.get_transform() != ax.transData:
                continue
            xx, yy = np.asarray(line.get_xdata(),dtype=float), np.asarray(line.get_ydata(),dtype=float)
            xmin,xmax=sorted(ax.get_xlim()); ymin,ymax=sorted(ax.get_ylim())
            if np.any((xx<xmin-1e-8)|(xx>xmax+1e-8)) or np.any((yy<ymin-1e-8)|(yy>ymax+1e-8)):
                data_outside.append({'axis':ai,'x':xx.tolist(),'y':yy.tolist()})
    if data_outside:
        raise ValueError(f'{name}: plotted observations outside axes: {data_outside}')
    if outside:
        raise ValueError(f'{name}: text outside canvas: {outside}')
    out=OUTPUT_DIR
    out.mkdir(parents=True,exist_ok=True)
    for suffix in ('svg','pdf','png'):
        meta={'Date': None} if suffix=='svg' else ({'CreationDate': None, 'ModDate': None} if suffix=='pdf' else {})
        fig.savefig(out/f'{name}.{suffix}', dpi=360, metadata=meta)
    QA[name]={'canvas_inches': fig.get_size_inches().tolist(), 'png_dpi': 360,
              'text_outside_canvas': outside, 'data_outside_axes': data_outside, 'minimum_font_pt': min(x['font_pt'] for x in labels),
              'labels': labels, 'renderer':'Matplotlib Agg / SVG / PDF',
              'visual_review': 'see ../VISUAL_REVIEW.json for hash-bound visual inspection'}
    plt.close(fig)


def score_rows(data):
    return {(r['model'],r['pool']):r for r in data['runs'] if r['pool'] in
            {'two_view_category','two_view_action','target_window','context_window'}}


def protocol_scores(data):
    runs=data['runs']; canon={r['model']:r for r in runs if r['pool']=='extended80' and r['prompt']=='s1_point'}
    protocols=[('normalized_1000','structured_text'),('normalized_1000','json'),('pixel','structured_text'),('pixel','json')]
    return [[canon[m]['current_stress30_slice'] if j==0 else next(r['score'] for r in runs if r['model']==m and r['pool']=='stress30' and r['prompt']=='s1_point' and r['frame']==frame and r['format']==fmt)
             for j,(frame,fmt) in enumerate(protocols)] for m in MODEL_ORDER]


def build_grounding(data):
    canon={r['model']:r for r in data['runs'] if r['pool']=='extended80' and r['prompt']=='s1_point'}
    fig=plt.figure(figsize=(5.5,2.6))
    text(fig,.03,.02,'Spatial readout across six model configurations',10,weight='bold')
    ax=axes_at(fig,1.00,.43,3.5,1.74)
    for i,m in enumerate(MODEL_ORDER):
        s=canon[m]['score'];a=100*s['original']['success_rate'];b=100*s['converted']['success_rate']
        ax.plot([a,b],[i,i],color=LINE,lw=2)
        ax.plot(a,i,'o',color=O,ms=5);ax.plot(b,i,'D',color=C,ms=4)
        ax.text(104,i,f"{s['flip_n']}/{s['n_pairs']}",va='center',fontsize=8)
    ax.set_xlim(-2,114);ax.set_ylim(5.5,-.5);ax.set_yticks(range(6),SHORT)
    ax.set_xticks([0,25,50,75,100]);ax.xaxis.grid(True,color='#EDF0F4')
    text(fig,4.42,.25,'Flips',8,weight='bold')
    text(fig,.5,2.4,'End-to-end point hits (%)',8,color=MUTED)
    text(fig,3.2,2.4,'● Original',8,color=O)
    text(fig,4.25,2.4,'◆ Converted',8,color=C)
    save(fig,'grounding')


def navigation_rows():
    p=RAW/'internnav_vln_downstream/official_val_unseen_99/paired_episode_transitions.csv';SOURCES.add(p)
    return list(csv.DictReader(p.open()))


def render_all(data):
    import sys
    from figure_overview import render_overview
    from figure_panels import render_panels
    SOURCES.clear();QA.clear();CROP_RECORDS.clear();style()
    mf=read_json(RAW/'iclr_model_behavior/interventions_clean_v2/manifest.json')
    render_overview(data,mf,sys.modules[__name__])
    render_panels(data,mf,sys.modules[__name__])
    build_grounding(data)
    (VENUE/'figures/geometry_checks.json').write_text(json.dumps(QA,indent=2)+'\n')
    (VENUE/'figures/crop_manifest.json').write_text(json.dumps({'schema_version':1,'crops':CROP_RECORDS},indent=2)+'\n')
    return sorted(SOURCES)
