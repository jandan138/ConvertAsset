"""Reference-informed evidence panels; all observations remain record-derived."""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Rectangle


def interventions(data, mf, c):
    fig=plt.figure(figsize=(5.5,3.92))
    c.text(fig,.04,.02,'a  Local changes, different decisions',10,weight='bold')
    c.text(fig,5.46,.055,'Query: “Locate the bottle”',7.5,color=c.MUTED,ha='right')
    crop=(120,25,480,415)
    families=['two_view_category','target_window','context_window','two_view_category']
    versions=['original','converted','converted','converted']
    for i,(fam,ver,label) in enumerate(zip(families,versions,['Original','Target window','Context window','Full conversion'])):
        x=.04+i*1.375; color=c.O if i==0 else c.C
        r=next(r for r in mf['scoring_records'] if r['pair_id']==f'board02.q0.side0.{fam}' and r['version']==ver)
        c.text(fig,x,.29,label,8.3,weight='bold',color=color)
        a=c.picture(fig,r['image']['path'],(x,.52,1.29,.477))
        a.add_patch(Rectangle((crop[0],crop[1]),crop[2]-crop[0],crop[3]-crop[1],fill=False,ec='white',lw=1.6))
        a.add_patch(Rectangle((crop[0],crop[1]),crop[2]-crop[0],crop[3]-crop[1],fill=False,ec=c.INK,lw=.65))
        a=c.picture(fig,r['image']['path'],(x,1.07,1.29,1.06),crop=crop)
        bb=r['target']['bbox_xyxy']
        a.add_patch(Rectangle((bb[0]-crop[0],bb[1]-crop[1]),bb[2]-bb[0],bb[3]-bb[1],fill=False,ec='#46CC9E',lw=.85))
    c.text(fig,.04,2.20,'White outline: enlargement · green outline: target window',7.3,color=c.MUTED)
    c.rule(fig,.04,5.46,2.43)
    c.text(fig,.04,2.52,'b  Paired point hits',9.5,weight='bold')
    c.text(fig,3.6,2.55,'● Original',7.8,color=c.O);c.text(fig,4.60,2.55,'◆ Changed',7.8,color=c.C)
    rr=c.score_rows(data)
    for j,model in enumerate(['Gemma4-E4B','Qwen3-VL-2B','Qwen3-VL-8B']):
        x=1.03+j*1.49
        c.text(fig,x,2.83,model.replace('-E4B',''),8.2,weight='bold')
        a=c.axes_at(fig,x,3.09,1.27,.57)
        for i,fam in enumerate(['two_view_category','two_view_action','target_window','context_window']):
            s=rr[model,fam]['score'];o=s['original']['hit_n'];v=s['converted']['hit_n']
            a.plot([o,v],[i,i],color=c.LINE,lw=2)
            a.plot(o,i,'o',ms=4.4,color=c.O);a.plot(v,i,'D',ms=3.8,color=c.C)
            a.text(17.1,i,f'{o}→{v}',va='center',fontsize=7.2)
        a.set_xlim(7.5,20.7);a.set_ylim(3.5,-.5)
        a.set_xticks([8,12,16]);a.tick_params(axis='x',labelsize=7,pad=3)
        a.set_yticks(range(4),['Full · category','Full · action','Target window','Context window'] if j==0 else ['']*4)
        a.tick_params(axis='y',labelsize=7,pad=5)
        a.xaxis.grid(True,color='#EDF0F4',lw=.6);a.set_axisbelow(True)
    c.text(fig,2.75,3.81,'Successful queries / 16 paired queries per intervention',7.5,color=c.MUTED,ha='center')
    c.save(fig,'interventions')


def protocol(data,c):
    ss=c.protocol_scores(data); delta=np.array([[100*s['delta'] for s in row] for row in ss])
    fig=plt.figure(figsize=(5.5,2.90))
    c.text(fig,.04,.02,'a  Material effect by readout',9.5,weight='bold')
    c.text(fig,3.47,.02,'b  Parsed points',9.5,weight='bold')
    cmap=LinearSegmentedColormap.from_list('material_delta',[c.O,'#FAFBFC',c.C])
    limit=max(10,float(np.ceil(abs(delta).max()/5)*5))
    x0=.79; heatw=2.45; covx=3.46;covw=1.99
    for x,w in [(x0,heatw),(covx,covw)]:
        for j,label in enumerate(['Normalized','Pixels']):
            c.text(fig,x+w*(.25+.5*j),.31,label,7.6,ha='center',weight='bold')
            c.rule(fig,x+w*.5*j+.02,x+w*.5*(j+1)-.02,.50)
        for j,label in enumerate(['Text','JSON','Text','JSON']):c.text(fig,x+w*(j+.5)/4,.55,label,7.3,ha='center')
    a=c.axes_at(fig,x0,.81,heatw,1.59)
    a.imshow(delta,cmap=cmap,vmin=-limit,vmax=limit,aspect='auto')
    a.set_xticks([]);a.set_yticks(range(6),c.SHORT);a.tick_params(axis='y',labelsize=7.6,pad=5)
    a.set_xticks(np.arange(-.5,4),minor=True);a.set_yticks(np.arange(-.5,6),minor=True)
    a.grid(which='minor',color='white',lw=2);a.tick_params(which='minor',length=0)
    for i in range(6):
        for j in range(4):a.text(j,i,f'{delta[i,j]:+.1f}',ha='center',va='center',fontsize=8.2,color='white' if abs(delta[i,j])>.6*limit else c.INK)
    a=c.axes_at(fig,covx,.81,covw,1.59);a.set_xlim(-.5,3.5);a.set_ylim(5.5,-.5);a.set_axis_off()
    for i in range(6):
        if i%2==0:a.axhspan(i-.5,i+.5,color='#F3F5F8')
        for j in range(4):
            s=ss[i][j];a.text(j,i,f"{s['original']['valid_point_n']}→{s['converted']['valid_point_n']}",ha='center',va='center',fontsize=7.2)
    cb=fig.colorbar(plt.cm.ScalarMappable(norm=Normalize(-limit,limit),cmap=cmap),cax=c.axes_at(fig,.84,2.57,1.30,.065),orientation='horizontal',ticks=[-limit,0,limit]);cb.outline.set_visible(False);cb.ax.tick_params(labelsize=7,pad=3)
    c.text(fig,2.25,2.54,'Δ hit rate\n(pp)',7.2,color=c.MUTED)
    c.text(fig,3.48,2.56,'Original → converted\nNumeric points / 30 queries',7.2,color=c.MUTED)
    c.save(fig,'protocol')


def navigation(data,c):
    nav=data['navigation'];rows=c.navigation_rows()
    fig=plt.figure(figsize=(5.5,2.34))
    c.text(fig,.04,.02,'a  Success transitions',9.5,weight='bold');c.text(fig,3.14,.02,'b  Outcomes by scene',9.5,weight='bold')
    lost,gained=nav['success_to_fail'],nav['fail_to_success']
    a=c.axes_at(fig,.12,.48,2.57,.62);a.set_xlim(-20,20);a.set_ylim(-.7,1.7);a.set_axis_off()
    a.axvline(0,color=c.LINE,lw=.8)
    a.barh(1,-lost,color=c.LOSS,height=.65);a.barh(0,gained,color=c.GAIN,height=.65)
    a.text(-lost/2,1,f'{lost} lost',color='white',fontsize=9,weight='bold',ha='center',va='center')
    a.text(gained/2,0,f'{gained} gained',color='white',fontsize=9,weight='bold',ha='center',va='center')
    delta=100*nav['metrics']['SR']['mean_delta_modified_minus_original']
    c.text(fig,.12,1.24,f'{delta:+.1f}',17,weight='bold')
    c.text(fig,.98,1.25,'pp net change\nin success rate',8,color=c.MUTED)
    c.rule(fig,.12,2.75,1.78)
    c.text(fig,.12,1.89,f"{nav['flips']}/{nav['n']} changed",16,weight='bold')
    c.text(fig,1.88,1.94,f"{nav['unchanged']} unchanged",7.8,color=c.MUTED)
    a=c.axes_at(fig,3.67,.43,1.65,1.27)
    groups=sorted({r['scene_id'] for r in rows})
    for i,s in enumerate(groups):
        rr=[r for r in rows if r['scene_id']==s];o=100*sum(float(r['original_SR']) for r in rr)/len(rr);v=100*sum(float(r['nomdl_SR']) for r in rr)/len(rr)
        a.plot([o,v],[i,i],color=c.LINE,lw=2);a.plot(o,i,'o',color=c.O,ms=5);a.plot(v,i,'D',color=c.C,ms=4)
        for q,dy,col in [(o,-.30,c.O),(v,.30,c.C)]:a.text(q,i+dy,f'{q:.1f}',ha='center',va='center',fontsize=7.5,color=col)
    a.set_xlim(10,93);a.set_ylim(2.66,-.66);a.set_yticks(range(3),[s.replace('kujiale_','') for s in groups]);a.set_xticks([20,40,60,80]);a.tick_params(labelsize=7.5);a.xaxis.grid(True,color='#EDF0F4',lw=.6);a.set_axisbelow(True)
    c.text(fig,4.49,1.94,'Success rate (%)',7.5,ha='center',color=c.MUTED)
    c.text(fig,3.52,2.18,'● Original',7.5,color=c.O);c.text(fig,4.45,2.18,'◆ Converted',7.5,color=c.C)
    c.save(fig,'navigation')


def trajectories(c):
    root=c.RAW/'internnav_vln_downstream/official_selected_qualitative_videos'
    c.read_json(root/'manifests/kujiale0036_0066_video_case_manifest.json')
    fig=plt.figure(figsize=(5.5,4.45))
    c.text(fig,.04,.02,'Where the agent stops',10,weight='bold')
    c.text(fig,5.45,.045,'Recorded endings',7.5,color=c.MUTED,ha='right')
    for x,col,label in [(.60,c.O,'Original'),(3.06,c.C,'Converted')]:
        c.text(fig,x+1.17,.28,label,9,color=col,weight='bold',ha='center');c.rule(fig,x,x+2.35,.50,color=col,lw=1.1)
        c.text(fig,x+.56,.58,'End view',7.5,ha='center',color=c.MUTED);c.text(fig,x+1.77,.58,'Map excerpt',7.5,ha='center',color=c.MUTED)
    for i,case in enumerate(['597_597','898_898','919_919']):
        y=.83+i*1.15
        c.text(fig,.04,y+.36,'Episode',7,color=c.MUTED);c.text(fig,.04,y+.54,case.split('_')[0],9,weight='bold')
        for j,v in enumerate(['original','nomdl']):
            paths=sorted((root/'stills/kujiale0036_0066').glob(f'kujiale0036_0066_{case}_{v}_end_*.png'))
            if len(paths)!=1:raise ValueError(f'Expected one end still: {case} {v}')
            im=c.read_image(paths[0]);h,w=im.shape[:2]
            if w!=2*h:raise ValueError('Expected equal square observation/map halves')
            for k,crop in enumerate([(0,0,w//2,h),(w//2,0,w,h)]):c.picture(fig,paths[0],(.60+j*2.46+k*1.20,y,1.12,1.12),crop=crop)
    c.text(fig,.60,4.32,'━ Executed trajectory',7.5,color='#CC2525');c.text(fig,3.06,4.32,'━ Reference trajectory',7.5,color='#168A45')
    c.save(fig,'trajectories')


def render_panels(data,mf,ctx):
    interventions(data,mf,ctx);protocol(data,ctx);navigation(data,ctx);trajectories(ctx)
