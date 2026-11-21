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


def picture(fig, path, box, border=None):
    data = read_image(path)
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
                              fill=False, edgecolor=border, lw=1.2, clip_on=False))
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
    out=VENUE/'figures'
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


def build_overview(data, mf):
    fig=plt.figure(figsize=(5.5,4.18))
    text(fig,.04,.025,'Same scene, different decisions',12,weight='bold')
    text(fig,5.46,.055,'Material intervention',8,color=MUTED,ha='right')
    src='c27086f557d316584264.zoom_018'
    for i,(v,label,color) in enumerate([('original','Original · MDL',O),('converted','Converted · UsdPreviewSurface',C)]):
        x=.05+i*2.78
        text(fig,x,.31,label,9,color=color,weight='bold')
        picture(fig,mf['sources'][f'{src}.{v}']['path'],(x,.52,2.62,1.60),color)
    text(fig,2.75,2.17,'Geometry and camera held fixed; surface appearance changes',8,color=MUTED,ha='center')
    # A research-design branch, not an assertion that the GRScenes images feed InternNav.
    # One intervention protocol branches into two separate evaluation settings.
    branch_routes=[[(2.75,2.30),(2.75,2.41)],
                   [(2.75,2.41),(.15,2.41),(.15,2.49)],
                   [(2.75,2.41),(3.15,2.41),(3.15,2.49)]]
    for i,route in enumerate(branch_routes):
        points=[(x/5.5,1-y/4.18) for x,y in route]
        fig.add_artist(FancyArrowPatch(path=MplPath(points),transform=fig.transFigure,
                        arrowstyle='-' if i==0 else '-|>',mutation_scale=6,
                        lw=.75,color=MUTED))
    text(fig,.05,2.52,'a  Language-conditioned pointing',9,weight='bold')
    text(fig,3.02,2.52,'b  Episode-level navigation',9,weight='bold')
    text(fig,.05,2.75,'“Locate the bottle” · Qwen3-VL-2B',8,color=MUTED)
    run=next(r for r in data['runs'] if r['model']=='Qwen3-VL-2B' and r['pool']=='two_view_category')
    pred_path=ROOT/run['source'];SOURCES.add(pred_path)
    preds=[json.loads(line) for line in pred_path.read_text().splitlines()]
    pair=[r for r in preds if r['pair_id']=='board02.q0.side0.two_view_category']
    original=next(r for r in pair if r['version']=='original')
    ax=picture(fig,original['image']['path'],(.05,2.94,2.65,.89))
    bb=original['target']['bbox_xyxy']
    ax.add_patch(Rectangle((bb[0],bb[1]),bb[2]-bb[0],bb[3]-bb[1],fill=False,ec='#46CC9E',lw=.9))
    for version,marker,color in [('original','o',O),('converted','D',C)]:
        r=next(record for record in pair if record['version']==version)
        p=r['prediction']['point_xy']; w=r['image']['width'];h=r['image']['height']
        ax.plot(p[0]*w/1000,p[1]*h/1000,marker=marker,ms=5,mec='white',mew=.8,color=color)
    score=run['score']
    hits=([score[c]['hit_n'] for c in ('original','converted')])
    totals=f"{hits[0]}/{score['n_pairs']} hits in both" if hits[0]==hits[1] else f"{hits[0]}→{hits[1]} hits / {score['n_pairs']}"
    text(fig,.05,3.87,f"{totals}; {score['flip_n']} queries change status",7.7,weight='bold')
    text(fig,.05,4.06,'● Original point',7,color=O)
    text(fig,1.22,4.06,'◆ Converted point',7,color=C)
    nav=data['navigation']
    text(fig,3.03,2.78,f"{nav['success_to_fail']} lost",7.4,color=LOSS)
    text(fig,3.69,2.78,f"{nav['fail_to_success']} gained",7.4,color=GAIN)
    text(fig,4.54,2.78,f"{nav['unchanged']} same",7.4,color=MUTED)
    ax=axes_at(fig,3.05,3.00,2.34,.62)
    ax.set_xlim(-.5,16.5);ax.set_ylim(5.5,-.5);ax.set_axis_off()
    # Each mark is one observed pair, grouped by transition (not episode order).
    colors=[LOSS]*nav['success_to_fail']+[GAIN]*nav['fail_to_success']+[LINE]*nav['unchanged']
    for i,color in enumerate(colors):
        ax.add_patch(Rectangle((i%17-.31,i//17-.28),.62,.56,facecolor=color,edgecolor='none'))
    text(fig,3.03,3.71,f"{nav['flips']}/{nav['n']}",19,weight='bold')
    text(fig,4.03,3.73,'episodes change\nsuccess status',8)
    delta=100*nav['metrics']['SR']['mean_delta_modified_minus_original']
    text(fig,3.03,4.06,f"{delta:+.1f} pp net change · {nav['success_to_fail']} lost / {nav['fail_to_success']} gained",7.3,color=MUTED)
    save(fig,'overview')
    # The source specification records scientific semantics and exact panel positions.
    spec={'version':'1.0','mode':'inspired','title':'Same scene, different decisions',
      'canvas':{'width':550,'height':418,'background':'#FFFFFF'},
      'theme':{'font_family':'Liberation Sans','palette':{'original':O,'converted':C,'ink':INK}},
      'panels':[{'id':'material','x':5,'y':30,'width':540,'height':202,'title':'Paired material intervention','semantic_role':'shared-study-design'},
                {'id':'grounding','x':5,'y':250,'width':265,'height':167,'title':'Language-conditioned pointing','semantic_role':'GRScenes-evidence'},
                {'id':'navigation','x':302,'y':250,'width':243,'height':167,'title':'Episode-level navigation','semantic_role':'KuJiaLe-evidence'}],
      'ports':[{'id':'protocol.out','owner':'material','x':275,'y':230,'scope':'external'},
               {'id':'protocol.split','x':275,'y':241,'scope':'junction'},
               {'id':'grounding.in','owner':'grounding','x':15,'y':249,'scope':'external'},
               {'id':'navigation.in','owner':'navigation','x':315,'y':249,'scope':'external'}],
      'edges':[{'id':name,'from':a,'to':b,'scope':'external','meaning':meaning,
                'arrowhead':'none' if i==0 else 'end','route':'explicit',
                'points':[{'x':round(x*100,4),'y':round(y*100,4)} for x,y in branch_routes[i]],
                'color':MUTED,'width':.75,'dash':'solid'}
               for i,(name,a,b,meaning) in enumerate([
                 ('protocol-branch','protocol.out','protocol.split','The shared material intervention design is evaluated in two separate settings.'),
                 ('grounding-branch','protocol.split','grounding.in','GRScenes point-level evaluation of the material intervention.'),
                 ('navigation-branch','protocol.split','navigation.in','Separate KuJiaLe episode-level evaluation of the material intervention.')])],
      'assets':[{'id':v,'path':os.path.relpath(mf['sources'][f'{src}.{v}']['path'],VENUE/'figures/specs'),
          'x':5+i*278,'y':52,'width':262,'height':160,'fit':'contain','alt':f'{v} registered bottle scene','owner':'material'} for i,v in enumerate(('original','converted'))],
      'outputs':{'formats':['svg','pdf','png'],'basename':'overview'},
      'review':{'semantic_graph_approved':True,'approved_by':'user-approved implementation plan; lead checked against saved records',
          'approved_at':'2026-09-15','notes':'Two parallel evidence panels share a material intervention protocol, not raster inputs. No directed causal edge between grounding and navigation. Points plotted in a common original-image coordinate reference; all raw scene pixels preserved.'},
      'provenance':[{'id':'measurements','source':'paper/shared/evidence/raw/iclr_model_behavior/analysis_v1/results.json','status':'verified','applies_to':['grounding','navigation']},
         {'id':'scenes','source':'paper/shared/evidence/raw/iclr_model_behavior/interventions_clean_v2/manifest.json','status':'verified','applies_to':['material']}]}
    (VENUE/'figures/specs').mkdir(exist_ok=True)
    (VENUE/'figures/specs/overview.spec.json').write_text(json.dumps(spec,indent=2)+'\n')


def build_interventions(data,mf):
    fig=plt.figure(figsize=(5.5,3.1))
    text(fig,.03,.015,'a  Which image region changes the decision?',10,weight='bold')
    families=['two_view_category','target_window','context_window','two_view_category']
    versions=['original','converted','converted','converted']
    labels=['Original','Target window','Context window','Full conversion']
    for i,(family,version,label) in enumerate(zip(families,versions,labels)):
        r=next(r for r in mf['scoring_records'] if r['pair_id']==f'board02.q0.side0.{family}' and r['version']==version)
        text(fig,.04+i*1.38,.27,label,8,weight='bold',color=O if i==0 else C)
        ax=picture(fig,r['image']['path'],(.04+i*1.38,.46,1.29,.49))
        bb=r['target']['bbox_xyxy']
        ax.add_patch(Rectangle((bb[0],bb[1]),bb[2]-bb[0],bb[3]-bb[1],fill=False,ec='#46CC9E',lw=.75))
    text(fig,.04,1.0,'One registered canvas · same query and target location',7.5,color=MUTED)
    rule(fig,.04,5.46,1.20)
    text(fig,.04,1.30,'b  Paired point hits',10,weight='bold')
    text(fig,3.85,1.32,'● Original',8,color=O)
    text(fig,4.75,1.32,'◆ Changed',8,color=C)
    models=['Gemma4-E4B','Qwen3-VL-2B','Qwen3-VL-8B']; rr=score_rows(data)
    for j,model in enumerate(models):
        ax=axes_at(fig,.94+j*1.55,1.91,1.22,.86)
        text(fig,.94+j*1.55,1.66,model.replace('-E4B',''),8.3,weight='bold')
        fams=['two_view_category','two_view_action','target_window','context_window']
        for i,fam in enumerate(fams):
            s=rr[model,fam]['score']; a=s['original']['hit_n'];b=s['converted']['hit_n']
            ax.plot([a,b],[i,i],color=LINE,lw=2,zorder=1)
            ax.plot(a,i,marker='o',ms=5,color=O,zorder=2)
            ax.plot(b,i,marker='D',ms=4,color=C,zorder=3)
            ax.text(17.25,i,f'{a}→{b}',va='center',fontsize=7.5)
        ax.set_xlim(8.3,19.8);ax.set_ylim(3.5,-.5)
        ax.set_xticks([8,12,16]);ax.tick_params(labelsize=7)
        ax.set_yticks(range(4),['Full · category','Full · action','Target window','Context window'] if j==0 else ['']*4)
        ax.tick_params(axis='y',labelsize=7.5)
        for v in [8,12,16]:ax.axvline(v,color='#EDF0F4',lw=.6,zorder=0)
    text(fig,2.75,2.94,'Successful queries / 16 paired queries per intervention',8,color=MUTED,ha='center')
    save(fig,'interventions')


def protocol_scores(data):
    runs=data['runs']; canon={r['model']:r for r in runs if r['pool']=='extended80' and r['prompt']=='s1_point'}
    protocols=[('normalized_1000','structured_text'),('normalized_1000','json'),('pixel','structured_text'),('pixel','json')]
    return [[canon[m]['current_stress30_slice'] if j==0 else next(r['score'] for r in runs if r['model']==m and r['pool']=='stress30' and r['prompt']=='s1_point' and r['frame']==frame and r['format']==fmt)
             for j,(frame,fmt) in enumerate(protocols)] for m in MODEL_ORDER]


def build_protocol(data):
    ss=protocol_scores(data)
    delta=np.array([[100*s['delta'] for s in row] for row in ss])
    fig=plt.figure(figsize=(5.5,2.72))
    text(fig,.04,.02,'a  Material effect depends on the readout',9.5,weight='bold')
    text(fig,3.78,.02,'b  Numeric outputs',9.5,weight='bold')
    ax=axes_at(fig,.94,.49,2.50,1.75)
    cmap=LinearSegmentedColormap.from_list('paired_delta',[O,'#FAFBFC',C])
    limit=max(10,float(np.ceil(np.max(abs(delta))/5)*5))
    ax.imshow(delta,cmap=cmap,vmin=-limit,vmax=limit,aspect='auto')
    for i in range(6):
        for j in range(4):
            ax.text(j,i,f'{delta[i,j]:+.1f}',ha='center',va='center',fontsize=8,
                    color='white' if abs(delta[i,j])>limit*.62 else INK)
    ax.set_xticks(range(4),['Norm.\nText','Norm.\nJSON','Pixels\nText','Pixels\nJSON'])
    ax.xaxis.tick_top();ax.tick_params(axis='x',labelsize=7.5,pad=4)
    ax.set_yticks(range(6),SHORT);ax.tick_params(axis='y',labelsize=8,pad=6)
    ax.set_xticks(np.arange(-.5,4,1),minor=True);ax.set_yticks(np.arange(-.5,6,1),minor=True)
    ax.grid(which='minor',color='white',lw=2);ax.tick_params(which='minor',length=0)
    # Exact original→converted counts expose parsing differences without a second color map.
    cov=axes_at(fig,3.72,.49,1.70,1.75);cov.set_xlim(-.5,3.5);cov.set_ylim(5.5,-.5)
    cov.set_xticks(range(4),['N/T','N/J','P/T','P/J']);cov.xaxis.tick_top();cov.tick_params(labelsize=7.5)
    cov.set_yticks([])
    for i in range(6):
        if i%2==0:cov.axhspan(i-.5,i+.5,color='#F3F5F8',zorder=0)
        for j in range(4):
            s=ss[i][j]
            cov.text(j,i,f"{s['original']['valid_point_n']}→{s['converted']['valid_point_n']}",ha='center',va='center',fontsize=6.8)
    cax=axes_at(fig,1.06,2.42,1.50,.08)
    cb=fig.colorbar(plt.cm.ScalarMappable(norm=Normalize(-limit,limit),cmap=cmap),cax=cax,orientation='horizontal',ticks=[-limit,0,limit])
    cb.ax.tick_params(labelsize=7,pad=2);cb.outline.set_visible(False)
    text(fig,2.69,2.38,'Δ hit rate (pp)',7.5,color=MUTED)
    text(fig,3.75,2.37,'Original → converted, /30\nN: normalized; P: pixels\nT: text; J: JSON',6.8,color=MUTED)
    save(fig,'protocol')


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


def build_navigation(data):
    rows=navigation_rows();nav=data['navigation']
    fig=plt.figure(figsize=(5.5,2.23))
    text(fig,.04,.02,'a  Opposing changes cancel',9.5,weight='bold')
    text(fig,3.12,.02,'b  Outcomes by scene',9.5,weight='bold')
    ax=axes_at(fig,.15,.38,2.62,1.13);ax.set_xlim(-18,18);ax.set_ylim(-.8,3.8);ax.set_axis_off()
    ax.axvline(0,color=LINE,lw=.8)
    vals=[-nav['success_to_fail'],nav['fail_to_success'],nav['fail_to_success']-nav['success_to_fail']]
    labels=['Success → failure','Failure → success','Net successful episodes']
    for y,(value,label,color) in enumerate(zip(vals,labels,[LOSS,GAIN,INK])):
        yy=2.5-y*1.2
        ax.barh(yy,value,height=.40,color=color)
        ax.text(0,yy+.30,label,ha='center',va='bottom',fontsize=8)
        ax.text(value/2,yy,f'{value:+d}',va='center',ha='center',fontsize=8,weight='bold',color='white')
    text(fig,.15,1.74,f"{nav['flips']} changed  ·  {nav['unchanged']} unchanged",9,weight='bold')
    text(fig,.15,2.00,f"{nav['n']} paired episodes; each contributes once",7.5,color=MUTED)
    ax=axes_at(fig,3.56,.38,1.68,1.23)
    groups=sorted({r['scene_id'] for r in rows})
    for i,s in enumerate(groups):
        rr=[r for r in rows if r['scene_id']==s]
        a=100*sum(float(r['original_SR']) for r in rr)/len(rr);b=100*sum(float(r['nomdl_SR']) for r in rr)/len(rr)
        ax.plot([a,b],[i,i],color=LINE,lw=2)
        ax.plot(a,i,'o',color=O,ms=5);ax.plot(b,i,'D',color=C,ms=4)
        for v,dy,color in [(a,-.33,O),(b,.33,C)]:ax.text(v,i+dy,f'{v:.1f}',ha='center',va='center',fontsize=7.5,color=color)
    ax.set_xlim(10,93);ax.set_ylim(2.65,-.65);ax.set_yticks(range(3),[s.replace('kujiale_','') for s in groups])
    ax.set_xticks([20,40,60,80]);ax.tick_params(labelsize=8);ax.xaxis.grid(True,color='#EDF0F4',lw=.6)
    text(fig,4.36,1.84,'Success rate (%)',8,color=MUTED,ha='center')
    text(fig,3.47,2.07,'● Original',7.5,color=O)
    text(fig,4.40,2.07,'◆ Converted',7.5,color=C)
    save(fig,'navigation')


def build_trajectories():
    root=RAW/'internnav_vln_downstream/official_selected_qualitative_videos'
    read_json(root/'manifests/kujiale0036_0066_video_case_manifest.json')
    fig=plt.figure(figsize=(5.5,4.32))
    text(fig,.04,.02,'Where the agent stops',10,weight='bold')
    text(fig,1.10,.30,'Original',9,color=O,weight='bold')
    text(fig,3.57,.30,'Converted',9,color=C,weight='bold')
    for i,case in enumerate(['597_597','898_898','919_919']):
        y=.54+i*1.16
        text(fig,.04,y+.20,f'Episode\n{case.split("_")[0]}',7.5,color=MUTED)
        for j,(v,color) in enumerate([('original',O),('nomdl',C)]):
            paths=sorted((root/'stills/kujiale0036_0066').glob(f'kujiale0036_0066_{case}_{v}_end_*.png'))
            if len(paths)!=1:raise ValueError(f'Expected one exact end still: {case} {v}: {paths}')
            picture(fig,paths[0],(.59+j*2.47,y,2.35,1.10),color)
    text(fig,.04,4.10,'Recorded endings · map excerpts',7.5,color=MUTED)
    text(fig,3.17,4.10,'━ Executed',7.5,color='#CC2525')
    text(fig,4.40,4.10,'━ Reference',7.5,color='#168A45')
    save(fig,'trajectories')


def render_all(data):
    SOURCES.clear();QA.clear();style()
    mf=read_json(RAW/'iclr_model_behavior/interventions_clean_v2/manifest.json')
    build_overview(data,mf);build_interventions(data,mf);build_protocol(data)
    build_navigation(data);build_trajectories();build_grounding(data)
    (VENUE/'figures/geometry_checks.json').write_text(json.dumps(QA,indent=2)+'\n')
    return sorted(SOURCES)
