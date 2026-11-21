"""Rebuild appendix evidence from registered component images; raw inputs are read-only."""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

HERE=Path(__file__).resolve(); VENUE=HERE.parents[1]; ROOT=VENUE.parents[2]
SHARED=ROOT/'paper/shared'; RAW=SHARED/'evidence/raw'; OUT=VENUE/'figures/supplement'
SPECS={}
SOURCE_CLOSURE=set()

def load_module(name):
    import sys
    spec=importlib.util.spec_from_file_location(name,SHARED/'figures'/f'{name}.py')
    SOURCE_CLOSURE.add(Path(spec.origin))
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return str(Path(p).resolve().relative_to(ROOT))

def image(c,fig,path,box,assets,*,crop=None,bbox=None):
    path=Path(path); a=c.picture(fig,path,box,crop=crop)
    if bbox:
        x,y,x1,y1=bbox;a.add_patch(Rectangle((x,y),x1-x,y1-y,fill=False,ec='#168A65',lw=.8))
    entry={'source':rel(path),'source_sha256':sha(path),'crop_xyxy':crop,'box_inches':list(box),'target_bbox_xyxy':bbox,'raster_role':'recorded evidence'}
    if crop:
        im=c.read_image(path);x,y,x1,y1=crop;entry['crop_rgb_sha256']=hashlib.sha256(im[y:y1,x:x1].tobytes()).hexdigest()
    assets.append(entry)

def finish(c,fig,name,assets,cases,claim):
    c.save(fig,name)
    SPECS[name]={'version':'1.0','mode':'inspired','figure':name,'communication_job':claim,'case_ids':cases,'assets':assets,'edges':([{'from':'parse','to':'align','meaning':'Parsed point mapped to declared frame.'},{'from':'align','to':'score','meaning':'Mapped point checked against target box.'}] if name=='appendix_readout' else []),'semantics':'Evidence panels compare recorded images; readout arrows encode parse-align-score processing.','approval':'User-approved appendix migration; source manifests govern image identity.','qa':c.QA[name]}

def pair_plate(c,name,title,rows,subtitle='Matched cameras · Original / converted'):
    # One row per real case with two full-frame image slots, no cropping.
    height=.64+len(rows)*1.67
    fig=plt.figure(figsize=(5.5,height));assets=[]
    c.text(fig,.04,.02,title,10,weight='bold');c.text(fig,.04,.27,subtitle,7.5,color=c.MUTED)
    for i,row in enumerate(rows):
        y=.62+i*1.67
        c.text(fig,.04,y,row['label'],8,weight='bold')
        for j,(key,col,label) in enumerate([('original',c.O,'Original'),('converted',c.C,'Converted')]):
            x=.72+j*2.41;c.text(fig,x,y,label,7.5,color=col,weight='bold')
            image(c,fig,row[key],(x,y+.21,2.30,1.38),assets,bbox=row.get('bbox'))
    finish(c,fig,name,assets,[r['id'] for r in rows],title)

def build_proxy(c):
    # These ten object/view pairs are the union of all active ACL empirical plates.
    views=[('0004','front'),('0004','top_front_left'),('0004','top_front_right'),('0011','front'),('0011','top_front_left'),('0011','top_front_right'),('0023','front'),('0023','top_front_right'),('0029','front'),('0029','top_front_right')]
    for page,subset in enumerate([views[:5],views[5:]],1):
        fig=plt.figure(figsize=(5.5,.64+len(subset)*1.30));assets=[]
        c.text(fig,.04,.02,'Controlled object views',10,weight='bold')
        for j,(lab,col) in enumerate([('Original',c.O),('Converted',c.C)]):c.text(fig,.91+j*2.34,.32,lab,8,col,weight='bold')
        for i,(obj,view) in enumerate(subset):
            y=.62+i*1.30;c.text(fig,.04,y+.28,f'#{obj}',8,weight='bold');c.text(fig,.04,y+.49,view.replace('top_front_','top\n').replace('_',' '),7,color=c.MUTED)
            for j,v in enumerate(['A','B']):image(c,fig,RAW/f'renders/chestofdrawers_{obj}/{v}_{view}.png',(.86+j*2.34,y,2.24,1.21),assets)
        finish(c,fig,f'appendix_render_pairs_{page:02}',assets,[f'{o}/{v}' for o,v in subset],'Matched proxy appearances from existing asset views.')
    rows=[]
    for v in ['01','03','05','07']:
        rows.append({'id':f'orbit_{v}','label':f'View {v}','original':SHARED/f'figures/out_tmp/mdl_images/orbit_mdl_{v}.png','converted':SHARED/f'figures/out_tmp/nomdl_images/orbit_{v}.png'})
    pair_plate(c,'appendix_scene_pairs','Material changes in scene context',rows)

def build_grounding(c):
    clean=load_module('gen_supplement_vlm_clean_rerender_panel')
    SOURCE_CLOSURE.update(clean.REPORTS);SOURCE_CLOSURE.add(clean.PROJECTION_QA)
    pairs=clean.load_pairs();rows=[]
    for p in pairs:rows.append({'id':p.pair_id,'label':p.target_category.capitalize(),'original':p.original.image_path,'converted':p.converted.image_path,'bbox':p.original.bbox_xyxy})
    pair_plate(c,'appendix_clean_grounding','Four clean target-view pairs',rows,'Green outline: projected target box')
    from appendix_render_sources import MANIFEST, load_repaired_pairs
    SOURCE_CLOSURE.update({MANIFEST, HERE.with_name('appendix_render_sources.py')})
    rows=load_repaired_pairs()
    pair_plate(c,'appendix_grounding_diagnostics_01','Additional target-view diagnostics',rows[:3],'Re-rendered after MDL dependency repair')
    pair_plate(c,'appendix_grounding_diagnostics_02','Additional camera views',rows[3:],'Re-rendered after MDL dependency repair')
    for name in ('appendix_grounding_diagnostics_01','appendix_grounding_diagnostics_02'):
        SPECS[name].update(
            evidence_role='qualitative_rerender_not_historical_inference',
            source_manifest=rel(MANIFEST), source_manifest_sha256=sha(MANIFEST),
            communication_job='Compare original and converted appearances at matched saved viewpoints after MDL dependency repair.',
            semantics='New paired renders carry no historical prediction overlays and do not replace historical inference inputs or scores.')

def build_material(c):
    for filename,name,title in [('qualitative_render_manifest.json','appendix_material_comparison','Material conversion across three conditions'),('supplemental_qualitative_render_manifest.json','appendix_material_failures','Clearcoat and procedural-texture fixtures')]:
        mf=c.read_json(RAW/'material_effect_baseline'/filename);cases=mf['selected_cases'];records={(r['sample_id'],r['condition']):r for r in mf['records']}
        fig=plt.figure(figsize=(5.5,.60+len(cases)*1.35));assets=[]
        c.text(fig,.04,.02,title,10,weight='bold')
        for j,(label,col) in enumerate([('Original',c.O),('ConvertAsset',c.C),('NVIDIA','#6B7280')]):c.text(fig,.67+j*1.62,.32,label,8,color=col,weight='bold')
        for i,case in enumerate(cases):
            y=.62+i*1.35;label=case['target_category'] if filename.startswith('qualitative') else case['covered_effects'][0].replace('_','\n')
            c.text(fig,.04,y+.30,label.capitalize(),7.5,weight='bold')
            for j,condition in enumerate(mf['condition_order']):
                r=records[case['sample_id'],condition];p=Path(r['image']['path'])
                if r['image'].get('hash_sha256') and sha(p)!=r['image']['hash_sha256']:raise ValueError(f'Raw hash mismatch: {p}')
                image(c,fig,p,(.68+j*1.62,y,1.54,1.22),assets)
        finish(c,fig,name,assets,[r['sample_id'] for r in cases],title)

def build_navigation(c):
    base=RAW/'internnav_vln_downstream/official_selected_qualitative_videos';page=0
    for group in ['kujiale0031','kujiale0036_0066']:
        if group=='kujiale0031':
            q=c.read_json(base/'manifests/kujiale0031_video_basic_qa.json');cases=list(dict.fromkeys(r['path_key'] for r in q['video_records']));scene_by_case={case:'0031' for case in cases}
        else:
            case_rows=c.read_json(base/'manifests/kujiale0036_0066_video_case_manifest.json')['selected_cases'];cases=[r['path_key'] for r in case_rows];scene_by_case={r['path_key']:r['scene_id'].split('_')[-1] for r in case_rows}
        for offset in range(0,len(cases),2):
            page+=1;selected=cases[offset:offset+2];fig=plt.figure(figsize=(5.5,5.30));assets=[]
            page_scenes=sorted({scene_by_case[case] for case in selected});heading=('Scene ' if len(page_scenes)==1 else 'Scenes ')+' / '.join(page_scenes)
            c.text(fig,.04,.02,'Navigation through time',10,weight='bold');c.text(fig,5.46,.05,heading,7.5,color=c.MUTED,ha='right')
            for k,case in enumerate(selected):
                y=.40+k*2.38;scene=scene_by_case[case];c.text(fig,.04,y,f'Episode {case.split("_")[0]} · scene {scene}',9,weight='bold')
                for j,label in enumerate(['Start','Middle','End']):c.text(fig,.59+j*1.64,y+.24,label,7.5,weight='bold')
                for v,version in enumerate(['original','nomdl']):
                    yy=y+.46+v*.90;c.text(fig,.03,yy+.28,'Original' if v==0 else 'Converted',7,color=c.O if v==0 else c.C,rotation=90)
                    for j,label in enumerate(['start','mid','end']):
                        paths=list((base/'stills'/group).glob(f'{group}_{case}_{version}_{label}_*.png'))
                        if len(paths)!=1:raise ValueError(f'Expected one still: {group} {case} {version} {label}')
                        image(c,fig,paths[0],(.48+j*1.64,yy,1.58,.79),assets)
            c.text(fig,.48,5.13,'Red: executed trajectory',7.5,color='#CC2525');c.text(fig,3.04,5.13,'Green: reference trajectory',7.5,color='#168A45')
            finish(c,fig,f'appendix_navigation_cases_{page:02}',assets,[f'{group}/{x}' for x in selected],'Start, middle and end frames from selected qualitative reruns.')


def build_readout(c):
    from matplotlib.patches import FancyArrowPatch
    data=c.read_json(RAW/'iclr_model_behavior/analysis_v1/results.json')
    run=next(r for r in data['runs'] if r['model']=='Qwen3-VL-2B' and r['pool']=='two_view_category')
    predpath=ROOT/run['source'];SOURCE_CLOSURE.add(predpath)
    records=[json.loads(line) for line in predpath.read_text().splitlines() if line.strip()]
    r=next(r for r in records if r['pair_id']=='board02.q0.side0.two_view_category' and r['version']=='original')
    point=r['prediction']['point_xy'];w=r['image']['width'];h=r['image']['height'];bb=r['target']['bbox_xyxy']
    fig=plt.figure(figsize=(5.5,3.23));assets=[]
    c.text(fig,.04,.02,'From a model response to a spatial decision',10,weight='bold')
    c.text(fig,.04,.32,'Decoded response',8,weight='bold')
    c.text(fig,.04,.55,f"Qwen3-VL-2B · bottle\nPoint: ({point[0]:g}, {point[1]:g})\nNormalized coordinates [0, 1000]",7.8,color=c.MUTED)
    c.text(fig,3.02,.32,'Two-view input',8,weight='bold')
    image(c,fig,r['image']['path'],(3.02,.56,2.42,.90),assets,bbox=bb)
    a=fig.axes[-1];a.plot(point[0]*w/1000,point[1]*h/1000,'o',ms=4,color=c.O,mec='white',mew=.7)
    c.rule(fig,.04,5.46,1.56)
    steps=[('1  Parse','Read numeric x, y'),('2  Align','Convert to image pixels'),('3  Score','Test point inside target')]
    for i,(title,note) in enumerate(steps):
        x=.08+i*1.84;c.text(fig,x,1.73,title,8.5,weight='bold');c.text(fig,x,1.98,note,7.2,color=c.MUTED)
        if i<2:fig.add_artist(FancyArrowPatch(((x+1.49)/5.5,1-1.85/3.23),((x+1.76)/5.5,1-1.85/3.23),transform=fig.transFigure,arrowstyle='-|>',mutation_scale=7,color=c.MUTED,lw=.8))
    c.text(fig,.08,2.26,'Text or JSON',7.6,color=c.O)
    c.text(fig,1.92,2.26,'x_px = x × width / 1000\ny_px = y × height / 1000',7.3,color=c.O)
    c.text(fig,3.76,2.26,'Fixed query denominator\nUnusable output = no hit',7.3,color=c.O)
    c.rule(fig,.04,5.46,2.79)
    c.text(fig,.08,2.91,'Coordinate baselines: image center · projected target-box center',7.5,color=c.MUTED)
    finish(c,fig,'appendix_readout',assets,[r['pair_id']],'Numeric outputs are parsed, aligned to the image coordinate frame, and scored using a fixed query denominator.')

def audit_migration():
    acl=ROOT/'paper/venues/acl27';seen=set();figures=[]
    def walk(path):
        path=path.resolve();SOURCE_CLOSURE.add(path)
        if path in seen:return
        seen.add(path);content=re.sub(r'(?m)(?<!\\)%.*$','',path.read_text())
        for match in re.finditer(r'\\(?:input|include)\{([^}]+)\}',content):
            s=match.group(1);candidates=[acl/(s+'.tex'),acl/s,SHARED/(s+'.tex')]
            p=next((p for p in candidates if p.is_file()),None)
            if p:walk(p)
        for match in re.finditer(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}|\\suppcasepair\{([^}]+)\}\{[^}]*\}\{([^}]+)\}',content):
            for s in match.groups():
                if s and not s.startswith('#'):figures.append({'source_tex':rel(path),'old_figure':s})
    walk(acl/'main.tex');walk(acl/'supplement.tex')
    for f in figures:
        n=f['old_figure'];dest=[];disposition='rebuild empirical content; merge repeated explanation'
        if 'method_chain' in n:dest=['main overview']
        elif any(s in n for s in ['review_packet','upload_gate','source_boundary']):disposition='internal reproducibility/submission display retired; metadata retained in migration record';dest=['appendix reproducibility text']
        elif any(s in n for s in ['internnav','navigation']):dest=[x for x in SPECS if 'navigation' in x]+['appendix full paired navigation metrics']
        elif 'material' in n:dest=['appendix_material_comparison','appendix_material_failures','appendix material inventory']
        elif any(s in n for s in ['render_atlas','render_scene','grscene_qualitative']):dest=['appendix_render_pairs_01','appendix_render_pairs_02','appendix_scene_pairs']
        elif 'clean_rerender' in n:dest=['appendix_clean_grounding']
        elif any(s in n for s in ['grscenes','vlm','grounding','theory']):dest=['appendix_clean_grounding','appendix_grounding_diagnostics_01','appendix_grounding_diagnostics_02','appendix corrected protocol/tables']
        else:dest=['appendix metric definitions','appendix_render_pairs_01','appendix_material_comparison','appendix_clean_grounding'];disposition='merge recurring teaching schematic and its repeated evidence into definitions and canonical plates'
        f.update(disposition=disposition,replacement=dest,distinct_cases=sorted({case for d in dest for case in SPECS.get(d,{}).get('case_ids',[])}))
    SOURCE_CLOSURE.update((SHARED/'figures').glob('gen_*.py'))
    result={'active_tex_files':sorted(rel(p) for p in seen),'active_figure_occurrences':len(figures),'unique_old_figures':len({f['old_figure'] for f in figures}),'inventory':figures,'new_figures':{k:{'case_ids':v['case_ids'],'asset_count':len(v['assets'])} for k,v in SPECS.items()},'case_inventory_verification':'Independent prose-author source audit additionally found and restored proxy0004/top_front_right; remaining distinct active empirical cases checked against source generators and records. Broad schematic replacements list canonical evidence families rather than implying every case appears in every original schematic.','statistics_policy':'No old parser-conditional or raw-pixel scores copied. Corrected fixed-denominator analysis_v1 and numeric tables are integrated by prose author.','source_policy':'Direct raw/component image reads; original images immutable. No new experiments. No old-page wrapper reuse.','validation':'All exports geometry-checked; render review recorded separately.'}
    (VENUE/'FIGURE_MIGRATION.json').write_text(json.dumps(result,indent=2)+'\n')
    lines=['# ACL → ICLR appendix figure migration','',f"Audited {len(seen)} active TeX files and {len(figures)} figure occurrences ({result['unique_old_figures']} distinct figure references), recursively including `suppcasepair`.",'','Each distinct real case is retained in the canonical plates below. Repeated schematics move to concise metric/protocol definitions. Numeric results use corrected fixed-denominator analyses; qualitative reruns remain separate from the 99-episode metrics.','','## New plates','']
    lines += [f"- **{k}**: {', '.join(v['case_ids'])}." for k,v in SPECS.items()]
    lines+=['','## Source figure disposition','','| Previous figure | Replacement |','|---|---|']+[f"| {f['old_figure']} | {', '.join(f['replacement'])} |" for f in figures]
    lines+=['','## Validation and handoff','','Python/Matplotlib exports SVG, PDF and 360-dpi PNG. Every source raster and any explicit crop is hash-recorded in `figures/supplement/figure-spec.json`. All text uses at least 7 pt. Final manuscript-scale visual inspection remains required after integration.','']
    (VENUE/'FIGURE_MIGRATION.md').write_text('\n'.join(lines))

def render_supplement(ctx):
    previous=ctx.OUTPUT_DIR;ctx.OUTPUT_DIR=OUT;OUT.mkdir(parents=True,exist_ok=True);SPECS.clear()
    try:
        build_proxy(ctx);build_grounding(ctx);build_material(ctx);build_navigation(ctx);build_readout(ctx)
        (OUT/'figure-spec.json').write_text(json.dumps(SPECS,indent=2)+'\n');audit_migration()
    finally:ctx.OUTPUT_DIR=previous
    return sorted({ROOT/a['source'] for s in SPECS.values() for a in s['assets']} | SOURCE_CLOSURE | set(ctx.SOURCES) | {HERE})

if __name__=='__main__':
    import figure_style as c
    c.style();render_supplement(c)
