"""Reference-led hero layouts; source pixels and decisions remain registered data."""
from __future__ import annotations
import json
import os
from pathlib import Path
import numpy as np
from matplotlib.patches import Rectangle, FancyArrowPatch
from matplotlib.lines import Line2D

LAYOUTS = {
    'balanced': {'top_height':1.78,'lower_y':2.49,'height':4.35,'ground_width':2.92},
    'detail': {'top_height':1.39,'lower_y':2.00,'height':3.86,'ground_width':3.16},
    'compact': {'top_height':1.58,'lower_y':2.19,'height':4.03,'ground_width':3.02},
}
CROP = (190,50,455,405)


def draw(fig, data, mf, c, layout):
    p=LAYOUTS[layout]; y=p['lower_y']; gh=p['ground_width']
    c.text(fig,.07,.02,'a  Material intervention',9.3,weight='bold')
    c.text(fig,5.43,.045,'Same geometry · same camera',7.5,color=c.MUTED,ha='right')
    iw=p['top_height']*4/3
    boxes=[]
    for i,(v,name,color) in enumerate([('original','Original',c.O),('converted','Converted',c.C)]):
        x=.10 if i==0 else 5.40-iw
        c.text(fig,x,.25,name,8.3,color=color,weight='bold')
        box=(x,.45,iw,p['top_height']); boxes.append(box)
        c.picture(fig,mf['sources'][f'c27086f557d316584264.zoom_018.{v}']['path'],box,color)
    left=boxes[0][0]+iw; right=boxes[1][0]
    mid=.45+p['top_height']*.47
    fig.add_artist(FancyArrowPatch((left/5.5+.016,1-mid/p['height']),
                     (right/5.5-.016,1-mid/p['height']),transform=fig.transFigure,
                     arrowstyle='-|>',mutation_scale=8,lw=.85,color=c.MUTED))
    if right-left>.65:
        c.text(fig,2.75,mid+.10,'Material\nrewrite',7.3,color=c.MUTED,ha='center')
    # Fine ruled branches express one protocol with separate evaluation settings.
    by=y-.10; top=.45+p['top_height']+.035
    for points in [[(2.75,top),(2.75,by)],[(2.75,by),(.15,by),(.15,y-.015)],[(2.75,by),(gh+.20,by),(gh+.20,y-.015)]]:
        xx,yy=zip(*points)
        fig.add_artist(Line2D(np.array(xx)/5.5,1-np.array(yy)/p['height'],transform=fig.transFigure,color='#ACB8C5',lw=.65))
    c.text(fig,.07,y,'b  Pointing decisions',9.3,weight='bold')
    nx=gh+.12
    c.text(fig,nx,y,'c  Navigation outcomes',9.3,weight='bold')
    c.text(fig,.07,y+.23,'“Locate the bottle”',8.0,weight='bold')
    c.text(fig,gh-.10,y+.25,'Qwen3-VL-2B',7.3,color=c.MUTED,ha='right')
    run=next(r for r in data['runs'] if r['model']=='Qwen3-VL-2B' and r['pool']=='two_view_category')
    path=c.ROOT/run['source'];c.SOURCES.add(path)
    pair=[json.loads(z) for z in path.read_text().splitlines() if json.loads(z)['pair_id']=='board02.q0.side0.two_view_category']
    original=next(r for r in pair if r['version']=='original'); bb=original['target']['bbox_xyxy']
    thumb=(.07,y+.54,gh-1.02,(gh-1.02)*450/1216)
    detail=(gh-.87,y+.43,.72,.965)
    full=c.picture(fig,original['image']['path'],thumb)
    full.add_patch(Rectangle((CROP[0],CROP[1]),CROP[2]-CROP[0],CROP[3]-CROP[1],fill=False,ec='white',lw=.7,ls='--'))
    zoom=c.picture(fig,original['image']['path'],detail,border=c.LINE,crop=CROP)
    for ax,offset in [(full,(0,0)),(zoom,CROP[:2])]:
        x0,y0=offset
        ax.add_patch(Rectangle((bb[0]-x0,bb[1]-y0),bb[2]-bb[0],bb[3]-bb[1],fill=False,ec='#30B394',lw=.8))
        for v,marker,color in [('original','o',c.O),('converted','D',c.C)]:
            r=next(r for r in pair if r['version']==v); pt=r['prediction']['point_xy']
            xx=pt[0]*r['image']['width']/1000-x0;yy=pt[1]*r['image']['height']/1000-y0
            ax.plot(xx,yy,marker=marker,ms=4.3 if ax==full else 5.8,mec='white',mew=.85,color=color)
    # Explicit enlargement connector, not a model/data-flow arrow.
    fx=thumb[0]+thumb[2]; fy=thumb[1]+thumb[3]*.50
    zx=detail[0];zy=detail[1]+detail[3]*.5
    fig.add_artist(Line2D([fx/5.5,(zx-.025)/5.5],[1-fy/p['height'],1-zy/p['height']],transform=fig.transFigure,color='#8B98A8',lw=.6))
    c.text(fig,.07,thumb[1]+thumb[3]+.05,'Shared original-image reference',7,color=c.MUTED)
    score=run['score']; n=score['n_pairs'];a=score['original']['hit_n'];b=score['converted']['hit_n']
    tail=y+1.47
    c.text(fig,.07,tail,f'{a}/{n} → {b}/{n} hits',8.7,weight='bold')
    c.text(fig,1.54,tail+.01,f"{score['flip_n']} decisions flip",8.0,color=c.INK)
    c.text(fig,.07,tail+.22,'● Original',7.3,color=c.O)
    c.text(fig,.98,tail+.22,'◆ Converted',7.3,color=c.C)
    c.text(fig,gh-.1,tail+.22,'□ Target',7.3,color='#168A75',ha='right')
    nav=data['navigation']
    c.text(fig,nx,y+.29,f"{nav['flips']}/{nav['n']}",22,weight='bold')
    c.text(fig,nx+1.05,y+.33,'episodes change\nsuccess status',7.8)
    # True unit chart: all99 paired episodes, fixed order by transition category.
    ax=c.axes_at(fig,nx,y+.81,5.36-nx,.50)
    ax.set_xlim(-.5,16.5);ax.set_ylim(5.6,-.6);ax.set_axis_off()
    colors=[c.LOSS]*nav['success_to_fail']+[c.GAIN]*nav['fail_to_success']+[c.LINE]*nav['unchanged']
    for i,col in enumerate(colors):ax.scatter(i%17,i//17,s=16,color=col,marker='s',linewidths=0)
    c.text(fig,nx,y+1.38,f"{nav['success_to_fail']} lost",7.4,color=c.LOSS)
    c.text(fig,nx+.68,y+1.38,f"{nav['fail_to_success']} gained",7.4,color=c.GAIN)
    c.text(fig,5.38,y+1.38,f"{nav['unchanged']} same",7.4,color=c.MUTED,ha='right')
    delta=100*nav['metrics']['SR']['mean_delta_modified_minus_original']
    c.text(fig,nx,tail+.22,f'{delta:+.1f} pp net success-rate change',7.5,color=c.INK)
    return boxes,original,path


def render_overview(data,mf,c,layout='balanced',name='overview',write_spec=True):
    p=LAYOUTS[layout];fig=c.plt.figure(figsize=(5.5,p['height']))
    boxes,original,predpath=draw(fig,data,mf,c,layout)
    c.save(fig,name)
    if not write_spec:return
    sy=p['lower_y']*100;by=sy-10;ty=(.45+p['top_height']+.035)*100;gx=(p['ground_width']+.20)*100
    routes=[[(275,ty),(275,by)],[(275,by),(15,by),(15,sy-1.5)],[(275,by),(gx,by),(gx,sy-1.5)]]
    spec={'version':'1.0','mode':'inspired','title':'Material intervention and paired decisions',
      'canvas':{'width':550,'height':p['height']*100,'background':'#FFFFFF'},
      'theme':{'font_family':'Liberation Sans','palette':{'original':c.O,'converted':c.C,'ink':c.INK}},
      'panels':[{'id':'material','x':5,'y':0,'width':540,'height':sy-12,'title':'Material intervention'},
        {'id':'grounding','x':5,'y':sy,'width':p['ground_width']*100-5,'height':p['height']*100-sy,'title':'Pointing decisions'},
        {'id':'navigation','x':p['ground_width']*100+12,'y':sy,'width':538-p['ground_width']*100-12,'height':p['height']*100-sy,'title':'Navigation outcomes'}],
      'ports':[{'id':'protocol.out','owner':'material','x':275,'y':ty,'scope':'external'},
        {'id':'protocol.split','x':275,'y':by,'scope':'junction'},
        {'id':'grounding.in','owner':'grounding','x':15,'y':sy-1.5,'scope':'external'},
        {'id':'navigation.in','owner':'navigation','x':gx,'y':sy-1.5,'scope':'external'}],
      'edges':[{'id':eid,'from':a,'to':b,'scope':'external','meaning':meaning,'arrowhead':'none','route':'explicit',
        'points':[{'x':x,'y':y} for x,y in routes[i]],'color':'#ACB8C5','width':.65,'dash':'solid'}
        for i,(eid,a,b,meaning) in enumerate([('protocol-branch','protocol.out','protocol.split','Common material intervention protocol'),
          ('grounding-branch','protocol.split','grounding.in','Separate GRScenes pointing evaluation'),
          ('navigation-branch','protocol.split','navigation.in','Separate KuJiaLe navigation evaluation')])],
      'assets':[{'id':v,'path':os.path.relpath(mf['sources'][f'c27086f557d316584264.zoom_018.{v}']['path'],c.VENUE/'figures/specs'),
        'x':boxes[i][0]*100,'y':boxes[i][1]*100,'width':boxes[i][2]*100,'height':boxes[i][3]*100,'fit':'contain','alt':f'Full {v} material view','owner':'material'} for i,v in enumerate(('original','converted'))],
      'outputs':{'formats':['svg','pdf','png'],'basename':'overview'},
      'review':{'semantic_graph_approved':True,'approved_by':'user-approved reference-led plan; lead source validation','approved_at':'2026-09-15',
        'notes':'Branches denote common intervention protocol, not shared raster inputs or causal mediation. Detail crop is explicitly linked to full original image; both conditions predictions are projected into that reference.'},
      'provenance':[{'id':'measured','source':'paper/shared/evidence/raw/iclr_model_behavior/analysis_v1/results.json','status':'verified'},
        {'id':'scene','source':'paper/shared/evidence/raw/iclr_model_behavior/interventions_clean_v2/manifest.json','status':'verified'},
        {'id':'prediction','source':str(predpath.relative_to(c.ROOT)),'status':'verified'}]}
    iw=p['top_height']*4/3; mid=(.45+p['top_height']*.47)*100
    left=(boxes[0][0]+iw+.088)*100; right=(boxes[1][0]-.088)*100
    spec['ports'] += [{'id':'original.out','owner':'material','x':left,'y':mid,'scope':'external'},
                      {'id':'converted.in','owner':'material','x':right,'y':mid,'scope':'external'}]
    spec['edges'].append({'id':'material-rewrite','from':'original.out','to':'converted.in','scope':'external',
             'meaning':'MDL is converted to UsdPreviewSurface while geometry is retained.','arrowhead':'end',
             'route':'explicit','points':[{'x':left,'y':mid},{'x':right,'y':mid}],
             'color':c.MUTED,'width':.85,'dash':'solid'})
    (c.VENUE/'figures/specs/overview.spec.json').write_text(json.dumps(spec,indent=2)+'\n')
