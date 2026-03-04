#!/usr/bin/env python3
"""Generate all paper figures for SynData4CV submission."""

import os
import csv
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.lines import Line2D
from sklearn.manifold import TSNE

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, 'raw')
FIG_DIR = os.path.join(BASE, 'figures')
os.makedirs(FIG_DIR, exist_ok=True)

# Publication-quality defaults
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 9,
    'axes.labelsize': 10,
    'axes.titlesize': 11,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 8,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
})

SCENES = ['chestofdrawers_0004', 'chestofdrawers_0011',
          'chestofdrawers_0023', 'chestofdrawers_0029']
SCENE_SHORT = {s: s.replace('chestofdrawers_', '#') for s in SCENES}

# Colorblind-friendly palette (Wong 2011)
C_PSNR  = '#0072B2'
C_SSIM  = '#009E73'
C_LPIPS = '#D55E00'
C_CLIP  = '#0072B2'
C_DINO  = '#E69F00'
C_A     = '#0072B2'
C_B     = '#E69F00'


def load_csv(fname):
    with open(os.path.join(RAW, fname)) as f:
        return list(csv.DictReader(f))


# ============================================================
# Fig 2: Render pair comparison
# ============================================================
def fig_render_pairs():
    selected = [
        ('chestofdrawers_0011', 'front'),
        ('chestofdrawers_0023', 'front'),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(5.5, 4.5))

    for i, (scene, angle) in enumerate(selected):
        rdir = os.path.join(RAW, 'renders', scene)
        img_a = mpimg.imread(os.path.join(rdir, f'A_{angle}.png'))
        img_b = mpimg.imread(os.path.join(rdir, f'B_{angle}.png'))

        axes[i, 0].imshow(img_a)
        axes[i, 0].set_xticks([]); axes[i, 0].set_yticks([])
        axes[i, 1].imshow(img_b)
        axes[i, 1].set_xticks([]); axes[i, 1].set_yticks([])

        # Row label
        axes[i, 0].set_ylabel(SCENE_SHORT[scene], fontsize=10, fontweight='bold')

    # Column headers
    axes[0, 0].set_title('MDL', fontsize=11, fontweight='bold')
    axes[0, 1].set_title('UsdPreviewSurface', fontsize=11, fontweight='bold')

    # Remove spines
    for ax in axes.flat:
        for spine in ax.spines.values():
            spine.set_linewidth(0.3)

    plt.subplots_adjust(wspace=0.04, hspace=0.08)
    fig.savefig(os.path.join(FIG_DIR, 'fig_render_pairs.pdf'))
    fig.savefig(os.path.join(FIG_DIR, 'fig_render_pairs.png'))
    plt.close(fig)
    print('[OK] fig_render_pairs')


# ============================================================
# Fig 3: Image quality metrics bar chart
# ============================================================
def fig_image_quality():
    rows = load_csv('image_quality.csv')

    # Group by scene
    data = {s: {'psnr': [], 'ssim': [], 'lpips': []} for s in SCENES}
    for r in rows:
        s = r['scene_id']
        data[s]['psnr'].append(float(r['psnr']))
        data[s]['ssim'].append(float(r['ssim']))
        data[s]['lpips'].append(float(r['lpips']))

    fig, axes = plt.subplots(1, 3, figsize=(7, 2.5))
    x = np.arange(len(SCENES))
    labels = [SCENE_SHORT[s] for s in SCENES]

    metrics = [
        ('PSNR (dB)', 'psnr', C_PSNR, r'$\uparrow$'),
        ('SSIM', 'ssim', C_SSIM, r'$\uparrow$'),
        ('LPIPS', 'lpips', C_LPIPS, r'$\downarrow$'),
    ]
    for ax, (title, key, color, arrow) in zip(axes, metrics):
        means = [np.mean(data[s][key]) for s in SCENES]
        stds  = [np.std(data[s][key]) for s in SCENES]
        ax.bar(x, means, yerr=stds, width=0.55, color=color, alpha=0.85,
               capsize=3, edgecolor='white', linewidth=0.5)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=0)
        ax.set_title(f'{title} {arrow}', fontsize=10)
        if key == 'ssim':
            ax.set_ylim(0.97, 1.001)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, 'fig_image_quality.pdf'))
    fig.savefig(os.path.join(FIG_DIR, 'fig_image_quality.png'))
    plt.close(fig)
    print('[OK] fig_image_quality')


# ============================================================
# Fig 4: Feature similarity summary
# ============================================================
def fig_feature_similarity():
    rows = load_csv('feature_similarity.csv')

    data = {s: {'clip': [], 'dino': []} for s in SCENES}
    for r in rows:
        s = r['scene_id']
        data[s]['clip'].append(float(r['clip_cosine']))
        data[s]['dino'].append(float(r['dino_cosine']))

    fig, ax = plt.subplots(figsize=(5, 3))
    x = np.arange(len(SCENES))
    w = 0.32
    labels = [SCENE_SHORT[s] for s in SCENES]

    clip_means = [np.mean(data[s]['clip']) for s in SCENES]
    clip_stds  = [np.std(data[s]['clip']) for s in SCENES]
    dino_means = [np.mean(data[s]['dino']) for s in SCENES]
    dino_stds  = [np.std(data[s]['dino']) for s in SCENES]

    ax.bar(x - w/2, clip_means, w, yerr=clip_stds, label='CLIP',
           color=C_CLIP, alpha=0.85, capsize=3, edgecolor='white', linewidth=0.5)
    ax.bar(x + w/2, dino_means, w, yerr=dino_stds, label='DINOv2',
           color=C_DINO, alpha=0.85, capsize=3, edgecolor='white', linewidth=0.5)

    ax.axhline(0.95, color='gray', ls='--', lw=0.8, label='0.95 threshold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel('Cosine Similarity')
    ax.set_ylim(0.5, 1.05)
    ax.legend(loc='lower right', framealpha=0.9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, 'fig_feature_similarity.pdf'))
    fig.savefig(os.path.join(FIG_DIR, 'fig_feature_similarity.png'))
    plt.close(fig)
    print('[OK] fig_feature_similarity')


# ============================================================
# Fig 5: t-SNE of DINOv2 embeddings
# ============================================================
def fig_tsne_dino():
    npz = np.load(os.path.join(RAW, 'dino_embeddings.npz'))
    emb_a = npz['A']   # (24, 384)
    emb_b = npz['B']   # (24, 384)
    pairs = npz['pairs']  # (24, 2): scene_id, angle

    all_emb = np.vstack([emb_a, emb_b])  # (48, 384)
    version = ['MDL'] * 24 + ['UsdPreviewSurface'] * 24
    scene_labels = list(pairs[:, 0]) + list(pairs[:, 0])

    tsne = TSNE(n_components=2, perplexity=12, random_state=42,
                learning_rate='auto', init='pca')
    proj = tsne.fit_transform(all_emb)

    fig, ax = plt.subplots(figsize=(4.5, 3.5))

    markers = {'chestofdrawers_0004': 'o', 'chestofdrawers_0011': 's',
               'chestofdrawers_0023': '^', 'chestofdrawers_0029': 'D'}

    for i in range(48):
        v = version[i]
        s = scene_labels[i]
        c = C_A if v == 'MDL' else C_B
        ax.scatter(proj[i, 0], proj[i, 1], c=c, marker=markers[s],
                   s=40, alpha=0.8, edgecolors='white', linewidths=0.3)

    # Legend: versions
    ver_handles = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor=C_A,
               markersize=7, label='MDL'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=C_B,
               markersize=7, label='UsdPreviewSurface'),
    ]
    # Legend: scenes
    scene_handles = [
        Line2D([0], [0], marker=markers[s], color='gray', linestyle='',
               markersize=6, label=SCENE_SHORT[s])
        for s in SCENES
    ]
    leg1 = ax.legend(handles=ver_handles, loc='upper left', framealpha=0.9,
                     title='Version', title_fontsize=8)
    ax.add_artist(leg1)
    ax.legend(handles=scene_handles, loc='lower right', framealpha=0.9,
              title='Scene', title_fontsize=8)

    ax.set_xlabel('t-SNE dim 1')
    ax.set_ylabel('t-SNE dim 2')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, 'fig_tsne_dino.pdf'))
    fig.savefig(os.path.join(FIG_DIR, 'fig_tsne_dino.png'))
    plt.close(fig)
    print('[OK] fig_tsne_dino')


if __name__ == '__main__':
    fig_render_pairs()
    fig_image_quality()
    fig_feature_similarity()
    fig_tsne_dino()
    print('\nAll figures saved to:', FIG_DIR)
